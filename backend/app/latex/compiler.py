import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import jinja2

from backend.app.core.config import settings
from backend.app.latex.sanitizer import sanitize_latex
from backend.app.schemas.curriculum import CurriculumCreate


@dataclass
class CompilationResult:
    success: bool
    pdf_path: Optional[str] = None
    pdf_bytes: Optional[bytes] = None
    tex_path: Optional[str] = None
    tex_source: str = ""
    zip_path: Optional[str] = None
    errors: Optional[List[str]] = None
    log_output: str = ""


class LatexCompiler:
    def __init__(self, template_path: Optional[str] = None):
        self.template_dir = os.path.dirname(template_path) if template_path else os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        self.template_name = os.path.basename(template_path) if template_path else "curriculum_nba_aicte.tex.j2"
        
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            block_start_string=r"\BLOCK{",
            block_end_string=r"}",
            variable_start_string=r"\VAR{",
            variable_end_string=r"}",
            comment_start_string=r"\#{",
            comment_end_string=r"}",
            line_statement_prefix="%%",
            line_comment_prefix="%#",
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["latex_escape"] = sanitize_latex

    def _sanitize_data_recursively(self, obj: Any) -> Any:
        if isinstance(obj, str):
            return sanitize_latex(obj)
        elif isinstance(obj, dict):
            return {k: self._sanitize_data_recursively(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_data_recursively(i) for i in obj]
        return obj

    def render_template(self, curriculum: CurriculumCreate) -> str:
        template = self.env.get_template(self.template_name)
        
        matrix_lookup: Dict[str, str] = {}
        target_totals: Dict[str, List[int]] = {}

        for cell in curriculum.articulation_matrix:
            key = f"{cell.co_id}_{cell.target_id}"
            val_str = str(cell.correlation_level) if cell.correlation_level > 0 else "-"
            matrix_lookup[key] = val_str
            if cell.correlation_level > 0:
                target_totals.setdefault(cell.target_id, []).append(cell.correlation_level)

        averages: Dict[str, str] = {}
        for target, vals in target_totals.items():
            if vals:
                averages[target] = f"{sum(vals) / len(vals):.1f}"
            else:
                averages[target] = "-"

        raw_context = {
            "meta": curriculum.course_meta.dict(),
            "course_outcomes": [co.dict() for co in curriculum.course_outcomes],
            "modules": [mod.dict() for mod in curriculum.modules],
            "matrix_lookup": matrix_lookup,
            "averages": averages,
            "textbooks": [b.dict() for b in curriculum.textbooks],
            "reference_books": [r.dict() for r in curriculum.reference_books],
            "assessment": curriculum.assessment_scheme.dict(),
        }

        context = self._sanitize_data_recursively(raw_context)
        rendered_tex = template.render(**context)
        return rendered_tex

    def compile(
        self,
        tex_source: str,
        output_prefix: str = "curriculum",
        output_dir: Optional[str] = None
    ) -> CompilationResult:
        build_dir = tempfile.mkdtemp(prefix="curriculum_tex_")
        target_dir = output_dir or settings.EXPORT_DIR
        os.makedirs(target_dir, exist_ok=True)

        safe_prefix = re.sub(r"[^a-zA-Z0-9_\-]", "_", output_prefix)
        tex_filename = f"{safe_prefix}.tex"
        pdf_filename = f"{safe_prefix}.pdf"
        zip_filename = f"{safe_prefix}_export.zip"

        tex_file_path = os.path.join(build_dir, tex_filename)
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_source)

        compiler_bin = settings.LATEX_COMPILER_BIN
        cmd = [
            compiler_bin,
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_filename
        ]

        errors: List[str] = []
        log_output = ""

        try:
            proc1 = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, timeout=settings.LATEX_TIMEOUT_SECONDS)
            proc2 = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, timeout=settings.LATEX_TIMEOUT_SECONDS)

            log_file_path = os.path.join(build_dir, f"{safe_prefix}.log")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    log_output = f.read()

            built_pdf = os.path.join(build_dir, pdf_filename)
            if proc2.returncode == 0 and os.path.exists(built_pdf):
                final_pdf_path = os.path.join(target_dir, pdf_filename)
                final_tex_path = os.path.join(target_dir, tex_filename)
                final_zip_path = os.path.join(target_dir, zip_filename)

                shutil.copyfile(built_pdf, final_pdf_path)
                shutil.copyfile(tex_file_path, final_tex_path)

                with open(final_pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                with zipfile.ZipFile(final_zip_path, "w", zipfile.ZIP_DEFLATED) as zip_out:
                    zip_out.write(final_tex_path, arcname=tex_filename)
                    zip_out.write(final_pdf_path, arcname=pdf_filename)
                    readme_content = (
                        f"CurriculumAI Studio - NBA/AICTE Accreditation Export\n"
                        f"Course: {safe_prefix}\n"
                        f"Compiler: {compiler_bin}\n"
                        f"Status: Compiled Successfully\n"
                    )
                    zip_out.writestr("README.txt", readme_content)

                return CompilationResult(
                    success=True,
                    pdf_path=final_pdf_path,
                    pdf_bytes=pdf_bytes,
                    tex_path=final_tex_path,
                    tex_source=tex_source,
                    zip_path=final_zip_path,
                    log_output=log_output[-2000:]
                )
            else:
                errors = self._extract_latex_errors(log_output)
                return CompilationResult(
                    success=False,
                    tex_source=tex_source,
                    errors=errors,
                    log_output=log_output[-3000:]
                )

        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                tex_source=tex_source,
                errors=["LaTeX compilation process timed out after 60 seconds."],
                log_output="Process timed out."
            )
        except Exception as e:
            return CompilationResult(
                success=False,
                tex_source=tex_source,
                errors=[f"Compilation worker exception: {str(e)}"],
                log_output=str(e)
            )
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)

    def _extract_latex_errors(self, log_text: str) -> List[str]:
        errors = []
        for line in log_text.splitlines():
            if line.startswith("!"):
                errors.append(line)
            elif "Error:" in line or "Fatal error" in line:
                errors.append(line)
        return errors[:10] if errors else ["LaTeX compilation failed. Inspect log output."]
