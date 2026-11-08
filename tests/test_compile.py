import asyncio
import importlib.abc
import importlib.util
import os
import sys

BASE_DIR = "/working_dir/c_d8d81eda79d2913e"


class DirectPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith("backend"):
            return None
        parts = fullname.split(".")
        rel_path = os.path.join(*parts)
        
        pkg_init = os.path.join(BASE_DIR, rel_path, "__init__.py")
        if os.path.exists(pkg_init):
            return importlib.util.spec_from_file_location(
                fullname, pkg_init, submodule_search_locations=[os.path.join(BASE_DIR, rel_path)]
            )
            
        mod_py = os.path.join(BASE_DIR, rel_path + ".py")
        if os.path.exists(mod_py):
            return importlib.util.spec_from_file_location(fullname, mod_py)
            
        return None


sys.meta_path.insert(0, DirectPathFinder())

from backend.app.schemas.curriculum import CourseMeta, GenerationRequest
from backend.app.rag.generator import CurriculumGenerator
from backend.app.latex.compiler import LatexCompiler


async def test_generation_and_compilation():
    meta = CourseMeta(
        course_name="Cloud-Native Distributed Systems and Microservices",
        course_code="22CS501",
        academic_year="2025-26",
        semester="V",
        department="Computer Science & Engineering",
        department_code="CSE",
        scheme="NEP 2020 / AICTE Model Curriculum",
        credits_l=3,
        credits_t=0,
        credits_p=2,
        credits_c=4,
        total_contact_hours=45,
        theory_hours=45,
        lab_hours=30,
        self_study_hours=15
    )

    request = GenerationRequest(
        course_meta=meta,
        industry_topics="Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph",
        num_modules=5,
        model_provider="offline"
    )

    print("1. Generating curriculum via CurriculumGenerator...")
    generator = CurriculumGenerator(request)
    curriculum = await generator.generate_curriculum()
    print(f"Generated {len(curriculum.modules)} modules and {len(curriculum.course_outcomes)} COs.")

    print("2. Rendering LaTeX template...")
    compiler = LatexCompiler()
    rendered_tex = compiler.render_template(curriculum)
    print(f"Rendered LaTeX length: {len(rendered_tex)} characters.")

    print("3. Compiling LaTeX to PDF via pdflatex...")
    result = compiler.compile(rendered_tex, output_prefix="22CS501_Cloud_Native_Distributed_Systems")

    print(f"Compilation success: {result.success}")
    if result.success:
        print(f"PDF successfully created: {result.pdf_path} (Size: {os.path.getsize(result.pdf_path)} bytes)")
        print(f"ZIP archive created: {result.zip_path} (Size: {os.path.getsize(result.zip_path)} bytes)")
    else:
        print("Compilation errors:")
        for err in (result.errors or []):
            print("  ", err)
        print("Log snippet:\n", result.log_output[-1000:])


if __name__ == "__main__":
    asyncio.run(test_generation_and_compilation())
