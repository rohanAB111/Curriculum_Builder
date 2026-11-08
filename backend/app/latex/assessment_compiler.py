import os
import re
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

import jinja2

from backend.app.core.config import settings
from backend.app.latex.compiler import CompilationResult
from backend.app.latex.sanitizer import sanitize_latex
from backend.app.schemas.assessment import AssessmentPlanResponse


class AssessmentPlanCompiler:
    def __init__(self):
        self.template_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "templates"
        )
        self.template_name = "assessment_plan_nba.tex.j2"
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

    def render_template(self, plan: AssessmentPlanResponse, meta: Any) -> str:
        template = self.env.get_template(self.template_name)
        
        raw_context = {
            "meta": meta.dict() if hasattr(meta, "dict") else meta.__dict__,
            "components": [c.dict() if hasattr(c, "dict") else c.__dict__ for c in plan.components],
            "total_marks": plan.total_marks,
            "attainment_methodology": plan.attainment_methodology,
        }
        context = self._sanitize_data_recursively(raw_context)
        return template.render(**context)

    def compile(
        self,
        tex_source: str,
        output_prefix: str = "assessment_plan",
        output_dir: Optional[str] = None
    ) -> CompilationResult:
        build_dir = tempfile.mkdtemp(prefix="assess_tex_")
        target_dir = output_dir or settings.EXPORT_DIR
        os.makedirs(target_dir, exist_ok=True)

        safe_prefix = re.sub(r"[^a-zA-Z0-9_\-]", "_", output_prefix)
        tex_filename = f"{safe_prefix}.tex"
        pdf_filename = f"{safe_prefix}.pdf"

        tex_file_path = os.path.join(build_dir, tex_filename)
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_source)

        compiler_bin = settings.LATEX_COMPILER_BIN
        cmd = [compiler_bin, "-interaction=nonstopmode", "-halt-on-error", tex_filename]

        try:
            # 2 passes
            subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, timeout=60)
            proc2 = subprocess.run(cmd, cwd=build_dir, capture_output=True, text=True, timeout=60)

            log_output = ""
            log_file_path = os.path.join(build_dir, f"{safe_prefix}.log")
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    log_output = f.read()

            built_pdf = os.path.join(build_dir, pdf_filename)
            if proc2.returncode == 0 and os.path.exists(built_pdf):
                final_pdf_path = os.path.join(target_dir, pdf_filename)
                final_tex_path = os.path.join(target_dir, tex_filename)
                shutil.copyfile(built_pdf, final_pdf_path)
                shutil.copyfile(tex_file_path, final_tex_path)

                with open(final_pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                return CompilationResult(
                    success=True,
                    pdf_path=final_pdf_path,
                    pdf_bytes=pdf_bytes,
                    tex_path=final_tex_path,
                    tex_source=tex_source,
                    log_output=log_output[-2000:]
                )
            else:
                return CompilationResult(
                    success=False,
                    tex_source=tex_source,
                    errors=["LaTeX compilation failed."],
                    log_output=log_output[-3000:]
                )
        finally:
            shutil.rmtree(build_dir, ignore_errors=True)
