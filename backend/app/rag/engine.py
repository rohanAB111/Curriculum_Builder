import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

from backend.app.core.config import settings


class HierarchicalChunk:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        parent_id: Optional[str] = None,
        section_type: str = "general",
        module_num: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.parent_id = parent_id
        self.section_type = section_type
        self.module_num = module_num
        self.metadata = metadata or {}


class SyllabusParser:
    MODULE_PATTERNS = [
        re.compile(r"^(?:Module|Unit|Chapter)\s+([IVXLCDM\d]+)[:\.\s]*(.*)$", re.IGNORECASE),
        re.compile(r"^Unit\s*[-–—]\s*(\d+)[:\.\s]*(.*)$", re.IGNORECASE),
        re.compile(r"^#+\s*(?:Module|Unit)\s*(\d+)[:\.\s]*(.*)$", re.IGNORECASE),
    ]

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        sep = "\n\n"
        if ext == ".pdf":
            if pypdf:
                reader = pypdf.PdfReader(file_path)
                return sep.join([page.extract_text() or "" for page in reader.pages])
            else:
                with open(file_path, "rb") as f:
                    return f.read().decode("utf-8", errors="ignore")
        elif ext in [".docx", ".doc"]:
            if docx:
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            else:
                with open(file_path, "r", errors="ignore") as f:
                    return f.read()
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

    @classmethod
    def hierarchical_chunk(cls, text: str, doc_id: str = "doc_1") -> List[HierarchicalChunk]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        chunks: List[HierarchicalChunk] = []
        
        current_module_num = None
        current_module_title = "Overview & Foundations"
        current_parent_id = f"{doc_id}_parent_0"
        current_module_lines: List[str] = []
        
        chunk_idx = 0

        for line in lines:
            is_new_module = False
            for pat in cls.MODULE_PATTERNS:
                m = pat.match(line)
                if m:
                    if current_module_lines:
                        parent_text = "\n".join(current_module_lines)
                        chunks.append(
                            HierarchicalChunk(
                                chunk_id=current_parent_id,
                                text=parent_text,
                                parent_id=None,
                                section_type="module_parent",
                                module_num=current_module_num,
                                metadata={"title": current_module_title, "doc_id": doc_id}
                            )
                        )
                        sub_chunks = cls._split_into_topics(current_module_lines, current_parent_id, chunk_idx)
                        chunks.extend(sub_chunks)
                        chunk_idx += len(sub_chunks)

                    mod_str = m.group(1)
                    try:
                        current_module_num = int(mod_str)
                    except ValueError:
                        roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
                        current_module_num = roman_map.get(mod_str.upper(), len(chunks) + 1)
                    
                    current_module_title = m.group(2).strip() or f"Module {current_module_num}"
                    current_parent_id = f"{doc_id}_mod_{current_module_num}"
                    current_module_lines = [line]
                    is_new_module = True
                    break

            if not is_new_module:
                current_module_lines.append(line)

        if current_module_lines:
            parent_text = "\n".join(current_module_lines)
            chunks.append(
                HierarchicalChunk(
                    chunk_id=current_parent_id,
                    text=parent_text,
                    parent_id=None,
                    section_type="module_parent",
                    module_num=current_module_num,
                    metadata={"title": current_module_title, "doc_id": doc_id}
                )
            )
            sub_chunks = cls._split_into_topics(current_module_lines, current_parent_id, chunk_idx)
            chunks.extend(sub_chunks)

        return chunks

    @classmethod
    def _split_into_topics(cls, lines: List[str], parent_id: str, start_idx: int) -> List[HierarchicalChunk]:
        children: List[HierarchicalChunk] = []
        buffer: List[str] = []
        buf_words = 0
        local_idx = 0

        for line in lines:
            words = line.split()
            buffer.append(line)
            buf_words += len(words)
            if buf_words >= 120 or line.endswith((".", ":", ";")):
                chunk_text = " ".join(buffer)
                children.append(
                    HierarchicalChunk(
                        chunk_id=f"{parent_id}_c_{local_idx}",
                        text=chunk_text,
                        parent_id=parent_id,
                        section_type="topic_child",
                        metadata={"word_count": buf_words}
                    )
                )
                local_idx += 1
                buffer = []
                buf_words = 0

        if buffer:
            chunk_text = " ".join(buffer)
            children.append(
                HierarchicalChunk(
                    chunk_id=f"{parent_id}_c_{local_idx}",
                    text=chunk_text,
                    parent_id=parent_id,
                    section_type="topic_child",
                    metadata={"word_count": buf_words}
                )
            )

        return children


class VectorRAGStore:
    def __init__(self):
        self.chunks: List[HierarchicalChunk] = []
        self.doc_frequencies: Dict[str, int] = {}
        self.vocab: Dict[str, int] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-\+]{2,}\b", text)]

    def add_documents(self, chunks: List[HierarchicalChunk]):
        self.chunks.extend(chunks)
        for chunk in chunks:
            tokens = set(self._tokenize(chunk.text))
            for t in tokens:
                self.doc_frequencies[t] = self.doc_frequencies.get(t, 0) + 1

    def _bm25_score(self, query_tokens: List[str], chunk_tokens: List[str], total_docs: int) -> float:
        score = 0.0
        doc_len = len(chunk_tokens)
        avg_doc_len = 80.0
        k1 = 1.5
        b = 0.75

        term_counts: Dict[str, int] = {}
        for t in chunk_tokens:
            term_counts[t] = term_counts.get(t, 0) + 1

        for q in query_tokens:
            if q in term_counts:
                df = self.doc_frequencies.get(q, 1)
                idf = math.log((total_docs - df + 0.5) / (df + 0.5) + 1.0)
                tf = term_counts[q]
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
                score += idf * (numerator / denominator)
        return score

    def _dense_semantic_score(self, query: str, chunk_text: str) -> float:
        q_tokens = set(self._tokenize(query))
        c_tokens = set(self._tokenize(chunk_text))
        if not q_tokens or not c_tokens:
            return 0.0
        intersection = len(q_tokens.intersection(c_tokens))
        union = len(q_tokens.union(c_tokens))
        return intersection / float(union) if union > 0 else 0.0

    def hybrid_search_and_rerank(
        self,
        query: str,
        industry_focus: Optional[str] = None,
        top_k: int = 5
    ) -> List[Tuple[HierarchicalChunk, float]]:
        if not self.chunks:
            return []

        total_docs = len(self.chunks)
        query_tokens = self._tokenize(query)
        industry_tokens = self._tokenize(industry_focus or "")

        ranked_results: List[Tuple[HierarchicalChunk, float]] = []

        for chunk in self.chunks:
            chunk_tokens = self._tokenize(chunk.text)
            bm25 = self._bm25_score(query_tokens, chunk_tokens, total_docs)
            semantic = self._dense_semantic_score(query, chunk.text)
            
            industry_boost = 0.0
            if industry_tokens:
                ind_matches = len(set(industry_tokens).intersection(set(chunk_tokens)))
                industry_boost = ind_matches * 1.5

            bloom_verbs = {"analyze", "evaluate", "design", "formulate", "synthesize", "implement", "construct"}
            bloom_matches = len(bloom_verbs.intersection(set(chunk_tokens)))
            bloom_boost = bloom_matches * 0.5

            composite_score = (0.5 * bm25) + (10.0 * semantic) + industry_boost + bloom_boost
            ranked_results.append((chunk, composite_score))

        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results[:top_k]


rag_store = VectorRAGStore()
