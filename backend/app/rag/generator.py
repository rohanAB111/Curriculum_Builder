import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import httpx

from backend.app.core.config import settings
from backend.app.rag.engine import rag_store
from backend.app.schemas.curriculum import (
    ArticulationCell,
    AssessmentScheme,
    BookCitation,
    CourseMeta,
    CourseOutcome,
    CurriculumCreate,
    GenerationRequest,
    ModuleTopic,
    ProgramSpecificOutcome,
)

logger = logging.getLogger(__name__)

NBA_PROGRAM_OUTCOMES = [
    ("PO1", "Engineering Knowledge: Apply knowledge of mathematics, science, engineering fundamentals to solve complex engineering problems."),
    ("PO2", "Problem Analysis: Identify, formulate, review research literature, and analyze complex engineering problems reaching substantiated conclusions."),
    ("PO3", "Design/Development of Solutions: Design solutions for complex engineering problems and design system components or processes that meet specified needs."),
    ("PO4", "Conduct Investigations of Complex Problems: Use research-based knowledge and research methods including design of experiments, analysis and interpretation of data."),
    ("PO5", "Modern Tool Usage: Create, select, and apply appropriate techniques, resources, and modern engineering and IT tools."),
    ("PO6", "The Engineer and Society: Apply reasoning informed by contextual knowledge to assess societal, health, safety, legal, and cultural issues."),
    ("PO7", "Environment and Sustainability: Understand the impact of professional engineering solutions in societal and environmental contexts."),
    ("PO8", "Ethics: Apply ethical principles and commit to professional ethics and responsibilities and norms of engineering practice."),
    ("PO9", "Individual and Team Work: Function effectively as an individual, and as a member or leader in diverse teams, and in multidisciplinary settings."),
    ("PO10", "Communication: Communicate effectively on complex engineering activities with the engineering community and with society at large."),
    ("PO11", "Project Management and Finance: Demonstrate knowledge and understanding of engineering and management principles and apply these to one's own work."),
    ("PO12", "Life-long Learning: Recognize the need for, and have the preparation and ability to engage in independent and life-long learning in the broadest context of technological change."),
]

DEFAULT_PSOS = [
    ProgramSpecificOutcome(pso_id="PSO1", statement="Professional Skills: Ability to design, develop, and deploy scalable software systems, algorithms, and cloud/edge infrastructure."),
    ProgramSpecificOutcome(pso_id="PSO2", statement="Industrial Competence: Ability to apply modern frameworks, AI accelerators, real-time data pipelines, and security protocols in enterprise settings."),
    ProgramSpecificOutcome(pso_id="PSO3", statement="Innovation and Entrepreneurship: Ability to formulate innovative technical solutions addressing societal and interdisciplinary challenges."),
]

BLOOM_LEVELS_THEORY = [
    ("CO1", "Cognitive", "L2: Understand", "Understand and explain foundational concepts, formal representations, and system invariants."),
    ("CO2", "Cognitive", "L3: Apply", "Apply algorithmic techniques, mathematical models, and architectural patterns to solve domain problems."),
    ("CO3", "Cognitive", "L4: Analyze", "Analyze system performance, bottlenecks, failure modes, and trade-offs under varying operational constraints."),
    ("CO4", "Cognitive", "L4: Analyze", "Formulate and analyze modern data workflows, streaming architectures, and distributed coordination."),
    ("CO5", "Cognitive", "L5: Evaluate", "Evaluate enterprise integration strategies, security postures, and cost-performance trade-offs."),
    ("CO6", "Cognitive", "L6: Create", "Design and synthesize an end-to-end, production-grade industry-aligned system integrating cutting-edge tooling."),
]

BLOOM_LEVELS_LAB_INTEGRATED = [
    ("CO1", "Cognitive", "L2: Understand", "Explain the theoretical principles and protocol state machines governing the technology domain."),
    ("CO2", "Psychomotor", "P2: Manipulation", "Configure, instrument, and operate development toolchains, container runtimes, and local clusters according to technical specifications."),
    ("CO3", "Cognitive", "L4: Analyze", "Diagnose system failures, benchmark operational bottlenecks, and profile latency profiles under stress."),
    ("CO4", "Psychomotor", "P3: Precision", "Implement and execute end-to-end automated pipelines, real-time streaming topologies, and API contracts with measurable accuracy."),
    ("CO5", "Affective", "A3: Valuing", "Adhere to professional engineering standards, open-source compliance, ethical zero-trust postures, and collaborative peer code review."),
    ("CO6", "Cognitive", "L6: Create", "Synthesize a functional capstone engineering solution incorporating hardware acceleration or production-grade cloud architectures."),
]


class CurriculumGenerator:
    def __init__(self, request: GenerationRequest):
        self.request = request
        self.meta = request.course_meta
        self.provider = request.model_provider.lower()
        self.model = request.model_name
        self.api_key = request.api_key
        self.ollama_url = request.ollama_url or settings.OLLAMA_BASE_URL

    async def generate_curriculum(self) -> CurriculumCreate:
        retrieved_context = ""
        if rag_store.chunks or self.request.reference_syllabus_text:
            query = f"{self.meta.course_name} {self.meta.department} syllabus modules course outcomes"
            top_chunks = rag_store.hybrid_search_and_rerank(
                query=query,
                industry_focus=self.request.industry_topics,
                top_k=4
            )
            retrieved_context = "\n---\n".join([f"[{c[0].section_type}] {c[0].text}" for c in top_chunks])
            if self.request.reference_syllabus_text:
                retrieved_context += f"\n\n[USER REFERENCE SYLLABUS]:\n{self.request.reference_syllabus_text[:2000]}"

        raw_llm_json = await self._dispatch_llm_call(retrieved_context)
        curriculum = self._post_process_and_balance(raw_llm_json)
        return curriculum

    async def _dispatch_llm_call(self, rag_context: str) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(rag_context)

        # 0. Zero-Auth Auto-Discovery for PARAM Shavak / On-Prem Qwen when model is "auto" or provider is "param_shavak_auto"
        if self.provider in ["param_shavak_auto", "ollama", "param_shavak", "qwen", "vllm"] and (
            not self.model or self.model.startswith("auto") or self.provider == "param_shavak_auto"
        ):
            try:
                from backend.app.llm.param_shavak_discovery import auto_discover_param_shavak_async
                disc = await auto_discover_param_shavak_async(self.ollama_url, preferred_model="qwen")
                if disc.get("connected"):
                    self.provider = disc["protocol"]
                    self.ollama_url = disc["base_url"]
                    self.model = disc["selected_model"]
            except Exception as e:
                logger.debug(f"Auto-discovery skipped: {e}")

        # 1. Ollama or PARAM Shavak Qwen endpoint (Zero-Auth REST /api/generate)
        if self.provider in ["ollama", "param_shavak", "qwen"]:
            try:
                target_model = self.model if (self.model and not self.model.startswith("auto")) else "qwen2.5:14b"
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{self.ollama_url}/api/generate",
                        json={
                            "model": target_model,
                            "system": system_prompt,
                            "prompt": user_prompt,
                            "format": "json",
                            "stream": False,
                            "options": {"temperature": self.request.temperature}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        response_text = data.get("response", "")
                        return self._parse_json_safely(response_text)
            except Exception as e:
                logger.warning(f"Ollama/PARAM Shavak call failed ({e}); falling back to deterministic generation.")

        # 2. OpenAI or vLLM (PARAM Shavak vLLM on port 8000)
        elif self.provider in ["openai", "vllm"] and (self.api_key or settings.OPENAI_API_KEY or "vllm" in self.provider):
            try:
                key = self.api_key or settings.OPENAI_API_KEY or "none"
                target_model = self.model or "qwen2.5-32b-instruct"
                base_url = self.ollama_url if "vllm" in self.provider else "https://api.openai.com/v1"
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                        json={
                            "model": target_model,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": self.request.temperature
                        }
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return self._parse_json_safely(content)
            except Exception as e:
                logger.warning(f"OpenAI/vLLM call failed ({e}); falling back to deterministic generation.")

        # 3. Google Gemini
        elif self.provider in ["gemini", "google"] and (self.api_key or settings.GEMINI_API_KEY):
            try:
                key = self.api_key or settings.GEMINI_API_KEY
                target_model = self.model or settings.GEMINI_MODEL
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                    "generationConfig": {"response_mime_type": "application/json", "temperature": self.request.temperature}
                }
                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        content = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                        return self._parse_json_safely(content)
            except Exception as e:
                logger.warning(f"Gemini call failed ({e}); falling back to deterministic generation.")

        return self._generate_high_fidelity_academic_payload()

    def _build_system_prompt(self) -> str:
        course_type = getattr(self.meta, "course_type", "Integrated")
        return (
            "You are an expert academic curriculum architect and NBA/AICTE Accreditation Reviewer. "
            "Generate an outcome-based course syllabus compliant with Indian engineering standards. "
            f"Course Type: {course_type}.\n"
            "Constraints:\n"
            "1. Multi-Domain Bloom's Taxonomy: If the course has practical/lab components, include both Cognitive (L1-L6) and Psychomotor (P1-P5) outcomes, and optionally Affective (A1-A5).\n"
            "2. Theory vs Industry progression: Modules 1-3 MUST establish fundamental theory and algorithms. Modules 4-6 MUST integrate trending industry tools.\n"
            "3. Enforce hour balance: Total contact hours across modules must equal exactly the specified Total Contact Hours.\n"
            "4. Output MUST be valid JSON only without markdown code ticks."
        )

    def _build_user_prompt(self, rag_context: str) -> str:
        num_cos = getattr(self.request, "num_cos", 6)
        num_mods = getattr(self.request, "num_modules", 5)
        return (
            f"Generate curriculum for:\n"
            f"Course Name: {self.meta.course_name} ({self.meta.course_code})\n"
            f"Course Type: {getattr(self.meta, 'course_type', 'Theory + Lab')}\n"
            f"Credits (L-T-P-C): {self.meta.credits_l}-{self.meta.credits_t}-{self.meta.credits_p}-{self.meta.credits_c}\n"
            f"Total Contact Hours: {self.meta.total_contact_hours}\n"
            f"Number of Modules: {num_mods}\n"
            f"Number of Course Outcomes: {num_cos}\n"
            f"Industry Topics: {self.request.industry_topics}\n\n"
            f"Reference Context:\n{rag_context}\n"
        )

    def _parse_json_safely(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def _balance_module_hours(self, num_modules: int, total_hours: int) -> List[int]:
        base = total_hours // num_modules
        remainder = total_hours % num_modules
        hours = [base] * num_modules
        for i in range(remainder):
            hours[i] += 1
        return hours

    def _post_process_and_balance(self, data: Dict[str, Any]) -> CurriculumCreate:
        num_mods = getattr(self.request, "num_modules", 5)
        num_cos = getattr(self.request, "num_cos", 6)
        total_hours = self.meta.total_contact_hours
        balanced_hours = self._balance_module_hours(num_mods, total_hours)
        is_lab = "lab" in getattr(self.meta, "course_type", "").lower() or "practical" in getattr(self.meta, "course_type", "").lower()

        # 1. Course Outcomes (Cognitive, Psychomotor, Affective)
        cos: List[CourseOutcome] = []
        raw_cos = data.get("course_outcomes", [])
        
        template_levels = BLOOM_LEVELS_LAB_INTEGRATED if is_lab else BLOOM_LEVELS_THEORY

        for idx in range(num_cos):
            co_id = f"CO{idx + 1}"
            if idx < len(raw_cos):
                item = raw_cos[idx]
                cos.append(CourseOutcome(
                    co_id=co_id,
                    description=item.get("description", f"Demonstrate mastery in {self.meta.course_name}"),
                    domain=item.get("domain", template_levels[idx % len(template_levels)][1]),
                    bloom_level=item.get("bloom_level", template_levels[idx % len(template_levels)][2]),
                    target_attainment_pct=float(item.get("target_attainment_pct", 70.0))
                ))
            else:
                tmpl = template_levels[idx % len(template_levels)]
                cos.append(CourseOutcome(
                    co_id=co_id,
                    description=f"{tmpl[3]} in the context of {self.meta.course_name}.",
                    domain=tmpl[1],
                    bloom_level=tmpl[2],
                    target_attainment_pct=70.0
                ))

        # 2. Modules
        modules: List[ModuleTopic] = []
        raw_mods = data.get("modules", [])
        ind_tags = [t.strip() for t in (self.request.industry_topics or "").split(",") if t.strip()]

        for i in range(num_mods):
            mod_num = i + 1
            allocated_h = balanced_hours[i]
            weightage = round((allocated_h / float(total_hours)) * 100.0, 1)

            if i < len(raw_mods):
                m_item = raw_mods[i]
                title = m_item.get("title", f"Module {mod_num}: In-Depth Domain Study")
                topics = m_item.get("topics", [f"Core syllabus topics for Unit {mod_num}"])
                cog = m_item.get("cognitive_level", "L2-L3" if mod_num <= 3 else "L4-L6")
            else:
                title, topics, cog = self._get_default_module_topics(mod_num, self.meta.course_name, ind_tags)

            mod_ind_tags = []
            if mod_num >= 4 and ind_tags:
                sub_tags = ind_tags[(mod_num - 4) * 2 : (mod_num - 3) * 2]
                mod_ind_tags = sub_tags if sub_tags else ind_tags[:2]

            modules.append(ModuleTopic(
                module_number=mod_num,
                title=title,
                contact_hours=allocated_h,
                weightage_pct=weightage,
                cognitive_level=cog,
                topics=topics,
                industry_integration_tags=mod_ind_tags
            ))

        # 3. PSOs & Articulation Matrix
        active_psos = self.meta.psos if self.meta.psos else DEFAULT_PSOS
        articulation_matrix: List[ArticulationCell] = []
        
        for co in cos:
            co_num = int(re.sub(r"\D", "", co.co_id) or "1")
            for po_id, _ in NBA_PROGRAM_OUTCOMES:
                po_num = int(po_id.replace("PO", ""))
                corr = 0
                if po_num == 1: corr = 3
                elif po_num == 2 and co_num >= 2: corr = 3 if co_num >= 3 else 2
                elif po_num == 3 and co_num >= 3: corr = 3 if co_num >= 5 else 2
                elif po_num == 4 and (co.domain == "Psychomotor" or co_num in [3, 4]): corr = 3 if is_lab else 2
                elif po_num == 5 and (co_num >= 3 or co.domain == "Psychomotor"): corr = 3  # Modern tools
                elif po_num == 8 and co.domain == "Affective": corr = 3  # Ethics
                elif po_num in [9, 10] and (co.domain == "Affective" or co_num == num_cos): corr = 2  # Teamwork
                elif po_num == 12: corr = 2
                articulation_matrix.append(ArticulationCell(co_id=co.co_id, target_id=po_id, correlation_level=corr))

            for pso in active_psos:
                pso_corr = 3 if co_num >= 3 else 2
                articulation_matrix.append(ArticulationCell(co_id=co.co_id, target_id=pso.pso_id, correlation_level=pso_corr))

        # 4. Textbooks & References
        textbooks = [
            BookCitation(
                book_type="Textbook",
                authors="Martin Kleppmann",
                title="Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems",
                edition="1st Edition",
                publisher="O'Reilly Media",
                year=2023,
                isbn="978-1449373320"
            ),
            BookCitation(
                book_type="Textbook",
                authors="Andrew S. Tanenbaum and Maarten van Steen",
                title="Distributed Systems: Principles and Paradigms",
                edition="4th Edition",
                publisher="Pearson Education",
                year=2024,
                isbn="978-1543057386"
            )
        ]

        reference_books = [
            BookCitation(
                book_type="Reference",
                authors="Brendan Burns",
                title="Designing Distributed Systems: Patterns and Paradigms for Scalable, Reliable Services",
                edition="2nd Edition",
                publisher="O'Reilly Media",
                year=2024,
                isbn="978-1492031772"
            ),
            BookCitation(
                book_type="Reference",
                authors="IEEE / ACM Joint Curriculum Committee",
                title="Computer Science Curricula 2023: Guidelines for Associate and Baccalaureate Programs in Computing",
                edition="Final Edition",
                publisher="IEEE-CS & ACM Press",
                year=2024
            )
        ]

        # 5. Assessment Scheme Breakdown (CIA, MSE, CIAP, ESE, ESEP, SLA)
        assessment = AssessmentScheme(
            cia_marks=20,
            mse_marks=30,
            ciap_marks=25,
            ese_marks=50,
            esep_marks=25,
            sla_marks=20,
            total_marks=170,
            passing_threshold_pct=40.0,
            rubrics_summary=(
                "Evaluation adheres to NBA/AICTE accreditation guidelines: Theory continuous evaluation consists of CIA (20 Marks) "
                "and MSE (30 Marks). Practical lab competence is evaluated via CIAP (25 Marks) and ESEP (25 Marks). Comprehensive "
                "end-semester written examination ESE carries 50 Marks, and Self-Learning Assessment (SLA / Capstone Mini-project) carries 20 Marks."
            )
        )

        return CurriculumCreate(
            course_meta=self.meta,
            course_outcomes=cos,
            industry_topics=self.request.industry_topics,
            modules=modules,
            articulation_matrix=articulation_matrix,
            textbooks=textbooks,
            reference_books=reference_books,
            assessment_scheme=assessment,
            department_id=1
        )

    def _get_default_module_topics(self, mod_num: int, course_name: str, ind_tags: List[str]) -> Tuple[str, List[str], str]:
        if mod_num == 1:
            return (
                "Foundational Concepts and Theoretical Framework",
                [
                    f"Introduction to {course_name} and core domain principles",
                    "Formal models, architectural taxonomies, and invariant properties",
                    "Mathematical foundations, complexity bounds, and state representation",
                    "Design space trade-offs, consistency criteria, and boundary conditions",
                ],
                "L1-L2"
            )
        elif mod_num == 2:
            return (
                "Core Algorithms and Design Patterns",
                [
                    "Fundamental algorithms, control flows, and scheduling mechanisms",
                    "Component interactions, interface contracts, and encapsulation",
                    "State synchronization, resource management, and partition recovery",
                    "Analytical verification and baseline validation benchmarks",
                ],
                "L2-L3"
            )
        elif mod_num == 3:
            return (
                "System Architecture and Optimization",
                [
                    "Modular decomposition, layering, and concurrency abstractions",
                    "High-performance caching, replication, and data partitioning",
                    "Fault-tolerant consensus, failure detectors, and self-healing topologies",
                    "Empirical profiling, bottleneck detection, and latency mitigation",
                ],
                "L3-L4"
            )
        elif mod_num == 4:
            tech_1 = ind_tags[0] if len(ind_tags) > 0 else "Cloud-Native Microservices"
            tech_2 = ind_tags[1] if len(ind_tags) > 1 else "Kafka Event Streaming"
            return (
                f"Modern Engineering Workflows & {tech_1}",
                [
                    f"Integration of {tech_1} into modern operational pipelines",
                    f"Asynchronous event processing using {tech_2} and message brokers",
                    "Distributed telemetry, observability, and structured logging",
                    "Zero-trust security, containerized deployment, and CI/CD pipelines",
                ],
                "L4-L5"
            )
        elif mod_num == 5:
            tech_3 = ind_tags[2] if len(ind_tags) > 2 else "Edge AI Accelerators"
            tech_4 = ind_tags[3] if len(ind_tags) > 3 else "TensorRT-LLM / vLLM Inference"
            return (
                f"Advanced Industry Applications & {tech_3}",
                [
                    f"Edge computing architectures, TinyML, and hardware acceleration with {tech_3}",
                    f"High-throughput LLM serving and model optimization utilizing {tech_4}",
                    "Fault injection testing, chaos engineering, and resilience metrics",
                    "Scalability benchmarking and compliance with modern enterprise standards",
                ],
                "L5-L6"
            )
        else:
            return (
                "Case Studies, Capstone System Synthesis & Emerging Horizons",
                [
                    "Real-world enterprise case studies and multi-cloud architectural patterns",
                    "Autonomous agent orchestration (LangGraph) and reactive state machines",
                    "Cost engineering, green computing, and environmental sustainability",
                    "Synthesis capstone: End-to-end design, audit, and deployment blueprint",
                ],
                "L6"
            )

    def _generate_high_fidelity_academic_payload(self) -> Dict[str, Any]:
        num_mods = getattr(self.request, "num_modules", 5)
        num_cos = getattr(self.request, "num_cos", 6)
        balanced_hours = self._balance_module_hours(num_mods, self.meta.total_contact_hours)
        ind_tags = [t.strip() for t in (self.request.industry_topics or "").split(",") if t.strip()]
        is_lab = "lab" in getattr(self.meta, "course_type", "").lower() or "practical" in getattr(self.meta, "course_type", "").lower()

        modules_data = []
        for i in range(num_mods):
            mod_num = i + 1
            title, topics, cog = self._get_default_module_topics(mod_num, self.meta.course_name, ind_tags)
            modules_data.append({
                "module_number": mod_num,
                "title": title,
                "contact_hours": balanced_hours[i],
                "cognitive_level": cog,
                "topics": topics
            })

        template_levels = BLOOM_LEVELS_LAB_INTEGRATED if is_lab else BLOOM_LEVELS_THEORY
        cos_data = []
        for i in range(num_cos):
            tmpl = template_levels[i % len(template_levels)]
            cos_data.append({
                "co_id": f"CO{i+1}",
                "domain": tmpl[1],
                "bloom_level": tmpl[2],
                "description": f"{tmpl[3]} for {self.meta.course_name}."
            })

        return {
            "course_outcomes": cos_data,
            "modules": modules_data
        }
