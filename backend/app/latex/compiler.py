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


def fix_latex_option_clashes(tex: str) -> str:
    r"""
    Automatically resolves common LaTeX errors in uploaded institutional .tex templates:
    1. '! LaTeX Error: Option clash for package geometry' -> Converts multiple \usepackage[opts]{geometry}
       declarations into a single \usepackage{geometry} followed by \geometry{opts}.
    2. Hoists package options via \PassOptionsToPackage{opts}{pkg} before \documentclass and
       removes duplicate \usepackage calls for the same package.
    3. '! Misplaced \omit. \multispan -> \omit' -> Fixes \multirow{R}{W}{\multicolumn{C}{align}{text}},
       \textbf{\multicolumn{C}{align}{text}}, \centering \multicolumn, and braced {\multicolumn...}.
    """
    if "\\begin{document}" in tex:
        preamble, body = tex.split("\\begin{document}", 1)

        # 1. Resolve geometry option clashes by converting [opts] into \geometry{opts}
        geom_seen = False

        def _repl_geom(match: re.Match) -> str:
            nonlocal geom_seen
            opts = (match.group(1) or "").strip()
            if not geom_seen:
                geom_seen = True
                if opts:
                    return f"\\usepackage{{geometry}}\n\\geometry{{{opts}}}"
                return "\\usepackage{geometry}"
            else:
                if opts:
                    return f"\\geometry{{{opts}}}"
                return "% duplicate \\usepackage{geometry} removed"

        preamble = re.sub(r"\\usepackage\s*(?:\[([^\]]*)\])?\s*\{\s*geometry\s*\}", _repl_geom, preamble)

        # 2. Collect options for all other packages and deduplicate repeated \usepackage calls
        pkg_options: Dict[str, List[str]] = {}
        for m in re.finditer(r"\\usepackage\s*\[([^\]]+)\]\s*\{([^}]+)\}", preamble):
            opts_str, pkgs_str = m.group(1), m.group(2)
            opts_list = [o.strip() for o in opts_str.split(",") if o.strip()]
            for pkg in [p.strip() for p in pkgs_str.split(",") if p.strip()]:
                pkg_options.setdefault(pkg, [])
                for o in opts_list:
                    if o not in pkg_options[pkg]:
                        pkg_options[pkg].append(o)

        seen_pkgs = set()

        def _dedup_usepackage(match: re.Match) -> str:
            opts = (match.group(1) or "").strip()
            pkgs = [p.strip() for p in match.group(2).split(",") if p.strip()]
            remaining = [p for p in pkgs if p not in seen_pkgs]
            for p in remaining:
                seen_pkgs.add(p)
            if not remaining:
                if len(pkgs) == 1 and pkgs[0] == "hyperref" and opts:
                    return f"\\hypersetup{{{opts}}}"
                return f"% duplicate \\usepackage{{{','.join(pkgs)}}} removed"
            return f"\\usepackage{{{','.join(remaining)}}}"

        preamble = re.sub(r"\\usepackage\s*(?:\[([^\]]*)\])?\s*\{([^}]+)\}", _dedup_usepackage, preamble)

        pass_lines = []
        for pkg, opts in pkg_options.items():
            if opts and pkg != "geometry":
                pass_lines.append(f"\\PassOptionsToPackage{{{','.join(opts)}}}{{{pkg}}}")
        if ("xcolor" in seen_pkgs or "colortbl" in seen_pkgs) and "xcolor" not in pkg_options:
            pass_lines.append("\\PassOptionsToPackage{table,dvipsnames}{xcolor}")

        if pass_lines:
            pass_block = "\n".join(pass_lines) + "\n"
            preamble = re.sub(r"(\\documentclass)", lambda m: pass_block + m.group(1), preamble, count=1)

        tex = preamble + "\\begin{document}" + body

    # 3. Fix '! Misplaced \omit' caused by \multicolumn nested inside \multirow, \textbf, or braces
    nested_arg = r"((?:[^{}]|\{[^{}]*\})*)"

    # 3a. \multirow{R}{W}{\multicolumn{C}{align}{text}} -> \multicolumn{C}{align}{\multirow{R}{W}{text}}
    tex = re.sub(
        rf"\\multirow\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\{{\s*\\multicolumn\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\}}",
        r"\\multicolumn{\3}{\4}{\\multirow{\1}{\2}{\5}}",
        tex,
    )

    # 3b. \textbf{\multicolumn{C}{align}{text}} -> \multicolumn{C}{align}{\textbf{text}}
    for macro in ("textbf", "textit", "emph", "underline"):
        tex = re.sub(
            rf"\\{macro}\s*\{{\s*\\multicolumn\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\}}",
            rf"\\multicolumn{{\1}}{{\2}}{{\\{macro}{{\3}}}}",
            tex,
        )

    # 3c. Remove alignment/spacing commands placed immediately before \multicolumn in the same cell
    tex = re.sub(
        r"(?:\\centering|\\raggedright|\\raggedleft|\\noindent|\\leavevmode)\s*(\\multicolumn\s*\{)",
        r"\1",
        tex,
    )

    # 3d. Unwrap {\multicolumn{C}{align}{text}} enclosed in extra braces after & or \\
    tex = re.sub(
        rf"([&\\]\s*)\{{\s*(\\multicolumn\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}}\s*\{{{nested_arg}\}})\s*\}}",
        r"\1\2",
        tex,
    )

    return tex


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

        pso_items = []
        if curriculum.course_meta.psos:
            pso_items = [
                p.dict() if hasattr(p, "dict") else {"pso_id": p.get("pso_id", "PSO1"), "statement": p.get("statement", "")}
                for p in curriculum.course_meta.psos
            ]
        else:
            pso_items = [
                {"pso_id": "PSO1", "statement": "Professional Skills: Design and develop enterprise cloud and edge systems."},
                {"pso_id": "PSO2", "statement": "Industrial Competence: Implement streaming data architectures and real-time AI pipelines."},
                {"pso_id": "PSO3", "statement": "Research & Ethics: Formulate secure, sustainable computing solutions."},
            ]

        po_list = [f"PO{i}" for i in range(1, 13)]

        raw_context = {
            "meta": curriculum.course_meta.dict() if hasattr(curriculum.course_meta, "dict") else curriculum.course_meta.__dict__,
            "course_outcomes": [co.dict() if hasattr(co, "dict") else co.__dict__ for co in curriculum.course_outcomes],
            "modules": [mod.dict() if hasattr(mod, "dict") else mod.__dict__ for mod in curriculum.modules],
            "matrix_lookup": matrix_lookup,
            "averages": averages,
            "po_list": po_list,
            "pso_list": pso_items,
            "textbooks": [b.dict() if hasattr(b, "dict") else b.__dict__ for b in curriculum.textbooks],
            "reference_books": [r.dict() if hasattr(r, "dict") else r.__dict__ for r in curriculum.reference_books],
            "assessment": curriculum.assessment_scheme.dict() if hasattr(curriculum.assessment_scheme, "dict") else curriculum.assessment_scheme.__dict__,
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

        tex_source = fix_latex_option_clashes(tex_source)
        tex_file_path = os.path.join(build_dir, tex_filename)
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_source)

        compiler_bin = settings.LATEX_COMPILER_BIN
        # Run in nonstopmode WITHOUT -halt-on-error so pdflatex recovers from minor table/alignment warnings
        cmd = [
            compiler_bin,
            "-interaction=nonstopmode",
            tex_filename,
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
            if os.path.exists(built_pdf) and os.path.getsize(built_pdf) > 0:
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