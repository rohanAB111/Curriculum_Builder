import asyncio
import importlib.abc
import importlib.util
import os
import sys

BASE_DIR = "/working_dir/c_d8d81eda79d2913e"


class DirectPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not (fullname.startswith("backend") or fullname.startswith("frontend")):
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

from backend.app.schemas.curriculum import CourseMeta, CourseOutcome, AssessmentScheme
from backend.app.schemas.assessment import AssessmentPlanRequest
from backend.app.rag.assessment_generator import AssessmentPlanGenerator
from backend.app.latex.assessment_compiler import AssessmentPlanCompiler


async def test_assessment_flow():
    meta = CourseMeta(
        course_name="Cloud-Native Distributed Systems & Microservices",
        course_code="22CS501",
        academic_year="2025-26",
        semester="V",
        department="Computer Science & Engineering"
    )
    cos = [
        CourseOutcome(co_id="CO1", domain="Cognitive", bloom_level="L2: Understand", description="Explain foundational consensus and replication state machines."),
        CourseOutcome(co_id="CO2", domain="Psychomotor", bloom_level="P2: Manipulation", description="Configure containerized microservices and service meshes in sandbox clusters."),
        CourseOutcome(co_id="CO3", domain="Cognitive", bloom_level="L4: Analyze", description="Diagnose partition recovery bottlenecks and latency anomalies."),
        CourseOutcome(co_id="CO4", domain="Psychomotor", bloom_level="P3: Precision", description="Implement real-time streaming topologies using Kafka Streams."),
        CourseOutcome(co_id="CO5", domain="Affective", bloom_level="A3: Valuing", description="Adhere to zero-trust ethical security policies and team code reviews."),
        CourseOutcome(co_id="CO6", domain="Cognitive", bloom_level="L6: Create", description="Synthesize a scalable edge computing system incorporating AI accelerators.")
    ]
    scheme = AssessmentScheme(
        cia_marks=20, mse_marks=30, ciap_marks=25, ese_marks=50, esep_marks=25, sla_marks=20, total_marks=170
    )

    req = AssessmentPlanRequest(
        course_meta=meta,
        course_outcomes=cos,
        assessment_scheme=scheme,
        cia_methods=["Technical Reel Explainer (60s)", "Cloud Outage Case Study Analysis"],
        mse_methods=["Higher-Order Thinking Questions (HOTS)", "System Bottleneck Scenario Paper"],
        ciap_methods=["Continuous Lab Experiment Audit", "Live Code Debugging Challenge"],
        ese_methods=["Comprehensive Theory Exam Blueprint", "Bloom's Balanced Part A & B Question Paper"],
        esep_methods=["Hands-on System Demonstration", "External Viva-Voce Examination"],
        sla_methods=["NPTEL / MOOC Certification Audit", "Capstone Open-Source Mini-Project"],
        faculty_prompt="Require students to record a 60-second video explaining consensus for CIA 1, and conduct an AWS outage case study for CIA 2.",
        model_provider="offline"
    )

    print("1. Generating Assessment Plan...")
    gen = AssessmentPlanGenerator(req)
    plan = await gen.generate_assessment_plan()
    print(f"Generated {len(plan.components)} assessment components.")

    print("2. Rendering Assessment LaTeX Template...")
    compiler = AssessmentPlanCompiler()
    tex = compiler.render_template(plan, meta)
    print(f"Rendered TeX Length: {len(tex)} chars.")

    print("3. Compiling Assessment LaTeX to PDF via pdflatex...")
    res = compiler.compile(tex, output_prefix="22CS501_Assessment_Methodology_Dossier")
    print(f"Compilation success: {res.success}")
    if res.success:
        print(f"Assessment PDF created: {res.pdf_path} (Size: {os.path.getsize(res.pdf_path)} bytes)")
    else:
        print("Compilation errors:", res.errors)
        print("Log snippet:\n", res.log_output[-1000:])


if __name__ == "__main__":
    asyncio.run(test_assessment_flow())
