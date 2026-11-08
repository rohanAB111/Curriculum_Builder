import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from backend.app.core.config import settings
from backend.app.schemas.assessment import (
    AssessmentComponentDetail,
    AssessmentPlanRequest,
    AssessmentPlanResponse,
)
from backend.app.rag.sakec_obe_rubrics import SAKEC_OBE_RUBRICS_CATALOG

logger = logging.getLogger(__name__)

# Official SAKEC OBE Manual Version 3.0 - Selectable Assessment Activities
OBE_ASSESSMENT_CATALOG = {
    "CIA": [
        "Reel / Blog / Skit Activity (SAKEC Rubric 25.8)",
        "Case Study Activity (SAKEC Rubric 25.3)",
        "Presentation Activity (SAKEC Rubric 25.4)",
        "Micro-Project Activity (SAKEC Rubric 25.5)",
        "Group Discussion Activity (SAKEC Rubric 25.6)",
        "Scenario-Based Assignment (SAKEC Rubric 25.7)",
        "Open-Book / Inverted Problem-Solving Challenge",
        "Quizzes & Interactive Tutorials",
    ],
    "MSE": [
        "Mid-Semester Examination (MSE) Mapped to COs",
        "Higher-Order Thinking Questions (HOTS - L3 to L5)",
        "Scenario-Based Analytical Question Paper",
        "System Bottleneck & Failure Diagnosis Paper",
    ],
    "CIAP": [
        "Computer-Allied Lab Experiment (SAKEC Rubric 25.1.1)",
        "Circuit-Allied Lab Experiment (SAKEC Rubric 25.1.2)",
        "PARIKSHAK - Test-Case-Based Program Evaluation (SAKEC Rubric 25.1.3)",
        "Continuous Experiment Logbook & Viva Audit",
    ],
    "ESE": [
        "Comprehensive End-Semester Theory Exam (SAKEC 60% University Weightage)",
        "Bloom's Cognitive Distribution Blueprint (L1 to L6)",
        "Scenario-Based Analytical Question Paper Scheme",
    ],
    "ESEP": [
        "Practical / Oral End-Semester Examination",
        "Hands-On System Deployment & Runtime Demonstration",
        "External Examiner Viva-Voce & Problem Diagnosis",
    ],
    "SLA": [
        "Semester Long Self-Learning Activity - Individual (SAKEC Rubric 25.2.1)",
        "Semester Long Self-Learning Activity - Group (SAKEC Rubric 25.2.2)",
        "NPTEL / SWAYAM / MOOC Certification & Portfolio Review",
        "Capstone Prototype / Research Paper Draft",
    ]
}


class AssessmentPlanGenerator:
    """
    Dedicated generator adhering strictly to the SAKEC Outcome-Based Education Manual (Version 3.0)
    and AICTE/NBA guidelines to construct actionable assessment activities,
    question paper blueprints, and official Annexure B 4-level analytic rubrics.
    """

    def __init__(self, request: AssessmentPlanRequest):
        self.request = request
        self.meta = request.course_meta
        self.cos = request.course_outcomes
        self.scheme = request.assessment_scheme
        self.provider = request.model_provider.lower()
        self.model = request.model_name
        self.api_key = request.api_key
        self.ollama_url = request.ollama_url or settings.OLLAMA_BASE_URL

    async def generate_assessment_plan(self) -> AssessmentPlanResponse:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt()

        raw_json = await self._dispatch_llm_call(system_prompt, user_prompt)
        return self._post_process_plan(raw_json)

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert SAKEC Outcome-Based Education (OBE) Assessment Architect. "
            "Your task is to generate a comprehensive institutional Assessment Methodology Document "
            "for engineering faculty covering CIA, MSE, CIAP, ESE, ESEP, and SLA in strict accordance with "
            "Shah & Anchor Kutchhi Engineering College (SAKEC) OBE Manual Version 3.0.\n"
            "Requirements:\n"
            "1. Align activities with Revised Bloom's Taxonomy (Cognitive L1-L6, Psychomotor P1-P5, Affective A1-A5).\n"
            "2. Reference official SAKEC Annexure B 4-level rubrics (Level 4 Exemplary, Level 3 Proficient/Good, Level 2 Developing/Satisfactory, Level 1 Beginning/Needs Improvement) with percentage weights summing to 100%.\n"
            "3. Include SAKEC CO Attainment formulas: Expected Proficiency = 60% marks; Level 3 >=70% students, linear interpolation y = 0.2*(Expected Attainment %) - 11 for 60%-70%, Direct (80%) + Indirect (20%).\n"
            "4. Output MUST be valid JSON only without markdown code fences."
        )

    def _build_user_prompt(self) -> str:
        cos_text = "\n".join([f"- {co.co_id} ({getattr(co, 'domain', 'Cognitive')}, {co.bloom_level}): {co.description}" for co in self.cos])
        return (
            f"Generate a SAKEC OBE Manual Version 3.0 compliant assessment plan for:\n"
            f"Course: {self.meta.course_name} ({self.meta.course_code})\n"
            f"Semester: {self.meta.semester} ({self.meta.academic_year}) | Dept: {self.meta.department}\n"
            f"Total Marks: {getattr(self.scheme, 'total_marks', 150)}\n\n"
            f"Target Course Outcomes:\n{cos_text}\n\n"
            f"Selected Methods:\n"
            f"- CIA ({getattr(self.scheme, 'cia_marks', 20)}M): {', '.join(self.request.cia_methods)}\n"
            f"- MSE ({getattr(self.scheme, 'mse_marks', 30)}M): {', '.join(self.request.mse_methods)}\n"
            f"- CIAP ({getattr(self.scheme, 'ciap_marks', 25)}M): {', '.join(self.request.ciap_methods)}\n"
            f"- ESE ({getattr(self.scheme, 'ese_marks', 50)}M): {', '.join(self.request.ese_methods)}\n"
            f"- ESEP ({getattr(self.scheme, 'esep_marks', 25)}M): {', '.join(self.request.esep_methods)}\n"
            f"- SLA ({getattr(self.scheme, 'sla_marks', 20)}M): {', '.join(self.request.sla_methods)}\n\n"
            f"Faculty Guidance Prompt:\n{self.request.faculty_prompt}\n"
        )

    async def _dispatch_llm_call(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
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
                        content = resp.json().get("response", "")
                        return self._parse_json(content)
            except Exception as e:
                logger.warning(f"Ollama/PARAM Shavak assessment generation failed ({e}); falling back to SAKEC manual synthesis.")

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
                            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": self.request.temperature
                        }
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"]
                        return self._parse_json(content)
            except Exception as e:
                logger.warning(f"Cloud/vLLM call failed ({e}); falling back.")

        return self._generate_deterministic_assessment_payload()

    def _parse_json(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def _convert_sakec_rubric_to_plan_criteria(self, rubric_key: str) -> List[Dict[str, Any]]:
        raw_list = SAKEC_OBE_RUBRICS_CATALOG.get(rubric_key, [])
        converted = []
        for r in raw_list:
            converted.append({
                "criterion": f"{r['criterion']} ({r['weight']}%)",
                "weight": r["weight"],
                "exemplary_4": r["level_4"],
                "proficient_3": r["level_3"],
                "developing_2": r["level_2"],
                "novice_1": r["level_1"],
            })
        return converted

    def _match_rubric_for_methods(self, methods: List[str], default_key: str) -> List[Dict[str, Any]]:
        joined = " ".join(methods).lower()
        if "reel" in joined or "blog" in joined or "skit" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.8 Reel / Blog / Skit Activity Rubric (5 Criteria - MS Teams Standard)")
        elif "case study" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.3 Case Study Activity Rubric")
        elif "presentation" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.4 Presentation Activity Rubric")
        elif "micro-project" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.5 Micro-Project Activity Rubric")
        elif "group discussion" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.6 Group Discussion Activity Rubric")
        elif "scenario" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.7 Scenario-Based Assignment Activity Rubric")
        elif "parikshak" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.1.3 PARIKSHAK - Test-Case-Based Program Evaluation Rubric")
        elif "circuit" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.1.2 Circuit-Allied Lab Experiment Rubric")
        elif "computer-allied" in joined or "lab" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.1.1 Computer-Allied Lab Experiment Rubric")
        elif "group" in joined and "self-learning" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.2.2 Semester Long Self-Learning Activity (SLA) - Group")
        elif "self-learning" in joined or "sla" in joined:
            return self._convert_sakec_rubric_to_plan_criteria("25.2.1 Semester Long Self-Learning Activity (SLA) - Individual")
        return self._convert_sakec_rubric_to_plan_criteria(default_key)

    def _post_process_plan(self, data: Dict[str, Any]) -> AssessmentPlanResponse:
        components = self._generate_default_component_details()

        return AssessmentPlanResponse(
            course_code=self.meta.course_code,
            course_name=self.meta.course_name,
            academic_year=self.meta.academic_year,
            semester=self.meta.semester,
            total_marks=getattr(self.scheme, "total_marks", 170),
            components=components,
            attainment_methodology=(
                "Per SAKEC OBE Manual Version 3.0 (Section 17 & 20): Expected Proficiency threshold is fixed at 60% marks. "
                "Let X = Percentage of students scoring >= 60% marks. "
                "If X >= 70%, Attainment Level = 3.00. If 60% <= X < 70%, linear interpolation applies: "
                "Attainment Level (y) = 0.2 * X - 11. If X < 60%, Attainment Level = X / 60. "
                "Final Course Outcome Attainment = (0.80 * Direct CO Attainment) + (0.20 * Indirect CO Attainment via Exit Survey). "
                "Initial CO Attainment Target for new courses is 1.80."
            )
        )

    def _generate_default_component_details(self) -> List[AssessmentComponentDetail]:
        return [
            AssessmentComponentDetail(
                component_name="Continuous Internal Assessment (Theory)",
                component_code="CIA",
                selected_methods=self.request.cia_methods,
                allocated_marks=getattr(self.scheme, "cia_marks", 20),
                target_cos=["CO1", "CO2", "CO3"],
                bloom_focus="Cognitive: L3 (Apply) & L4 (Analyze)",
                activity_description=(
                    f"Selected OBE Activities: {', '.join(self.request.cia_methods)}. "
                    f"Faculty Scenario Instructions: {self.request.faculty_prompt}"
                ),
                faculty_guidelines=(
                    "Administer according to SAKEC OBE Manual Section 25.3-25.8. Share Microsoft Teams rubric with students prior to submission. "
                    "Evaluate using the 4-level analytic scale (Excellent 4, Good 3, Satisfactory 2, Needs Improvement 1)."
                ),
                student_deliverables="Activity artifact (60-90s technical reel / case study report / presentation deck) uploaded directly to Microsoft Teams Assignment.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.cia_methods,
                    "25.8 Reel / Blog / Skit Activity Rubric (5 Criteria - MS Teams Standard)"
                )
            ),
            AssessmentComponentDetail(
                component_name="Mid-Semester Examination (Theory)",
                component_code="MSE",
                selected_methods=self.request.mse_methods,
                allocated_marks=getattr(self.scheme, "mse_marks", 30),
                target_cos=["CO1", "CO2", "CO3"],
                bloom_focus="Cognitive: L2 (Understand) to L4 (Analyze)",
                activity_description=(
                    "Centralized written examination evaluating foundational modules covered in the first half of the semester. "
                    "Every question is mapped explicitly to target Course Outcomes (COs) and Bloom's cognitive levels (RBT)."
                ),
                faculty_guidelines="Prepare question-wise CO mapping matrix and model answer key. Record question-wise student marks to compute percentage scoring >= 60%.",
                student_deliverables="Written examination script solving analytical and scenario-based engineering problems.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.mse_methods,
                    "25.7 Scenario-Based Assignment Activity Rubric"
                )
            ),
            AssessmentComponentDetail(
                component_name="Continuous Internal Assessment for Practical / Lab",
                component_code="CIAP",
                selected_methods=self.request.ciap_methods,
                allocated_marks=getattr(self.scheme, "ciap_marks", 25),
                target_cos=["CO2", "CO4", "CO5"],
                bloom_focus="Psychomotor (P2-P3), Cognitive (L3-L4) & Affective (A3)",
                activity_description=(
                    f"Weekly laboratory experiment evaluation and automated test-case verification ({', '.join(self.request.ciap_methods)}). "
                    "Assesses Conceptual Understanding (20%), Execution (15%), Debugging (20%), Professional Conduct & Ethics (20%), Output Accuracy (15%), and Documentation (10%)."
                ),
                faculty_guidelines="Evaluate weekly laboratory experiments using SAKEC Annexure B Section 25.1 rubrics (Computer-Allied / Circuit-Allied / PARIKSHAK).",
                student_deliverables="Executed code/circuit, passed test cases, validated output, and structured laboratory report.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.ciap_methods,
                    "25.1.1 Computer-Allied Lab Experiment Rubric"
                )
            ),
            AssessmentComponentDetail(
                component_name="End-Semester Examination (Theory)",
                component_code="ESE",
                selected_methods=self.request.ese_methods,
                allocated_marks=getattr(self.scheme, "ese_marks", 50),
                target_cos=["CO1", "CO2", "CO3", "CO4", "CO5", "CO6"],
                bloom_focus="Comprehensive Cognitive: L2 to L6",
                activity_description=(
                    "Comprehensive end-semester theory examination covering all curriculum modules (SAKEC 60% University Assessment component of Direct Attainment)."
                ),
                faculty_guidelines="Ensure balanced coverage of all Course Outcomes and Bloom's Taxonomy levels across the question paper.",
                student_deliverables="Comprehensive written answer script.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.ese_methods,
                    "25.7 Scenario-Based Assignment Activity Rubric"
                )
            ),
            AssessmentComponentDetail(
                component_name="End-Semester Practical & Oral Examination",
                component_code="ESEP",
                selected_methods=self.request.esep_methods,
                allocated_marks=getattr(self.scheme, "esep_marks", 25),
                target_cos=["CO4", "CO5", "CO6"],
                bloom_focus="Psychomotor (P4 Articulation) & Cognitive (L5-L6)",
                activity_description=(
                    "Practical and oral viva-voce examination conducted at the end of the semester to evaluate practical skills and application of knowledge."
                ),
                faculty_guidelines="Joint evaluation by Internal Examiner and External Examiner using structured laboratory performance and viva criteria.",
                student_deliverables="Live practical execution, system demonstration, and oral defense.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.esep_methods,
                    "25.1.3 PARIKSHAK - Test-Case-Based Program Evaluation Rubric"
                )
            ),
            AssessmentComponentDetail(
                component_name="Self-Learning Assessment (SLA)",
                component_code="SLA",
                selected_methods=self.request.sla_methods,
                allocated_marks=getattr(self.scheme, "sla_marks", 20),
                target_cos=["CO5", "CO6"],
                bloom_focus="Cognitive (L5-L6) & Affective (A3-A4)",
                activity_description=(
                    "Semester-long Self-Learning Activity evaluated across 3 progressive phases: "
                    "Phase 1: Problem Understanding & Design Methodology (25%), Phase 2: Methodology Validation & Implementation (25%), "
                    "Phase 3: Comprehensive Evaluation & Trade-offs (20%), Final Report Quality (15%), Plagiarism & AI Compliance (10%), Defense (5%)."
                ),
                faculty_guidelines="Conduct progressive reviews at Phase 1, Phase 2, and Phase 3 per SAKEC OBE Manual Section 25.2. Verify AI usage disclosure and plagiarism compliance.",
                student_deliverables="Phase I, II, III progressive review artifacts, final comprehensive technical report, and oral defense.",
                rubric_criteria=self._match_rubric_for_methods(
                    self.request.sla_methods,
                    "25.2.1 Semester Long Self-Learning Activity (SLA) - Individual"
                )
            ),
        ]

    def _generate_deterministic_assessment_payload(self) -> Dict[str, Any]:
        return {
            "components": [c.dict() for c in self._generate_default_component_details()]
        }
