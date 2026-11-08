"""
CurriculumAI Studio - Streamlit Web Application
Production-grade NBA/AICTE-Compliant Curriculum Generation & LaTeX Compilation Studio.
"""

import asyncio
import os
import sys
import tempfile
import base64
from typing import Dict, List, Any

# Ensure backend modules can be imported
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import streamlit as st

# Direct import fallback helper for sandbox environments
import importlib.abc
import importlib.util

class DirectPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if not (fullname.startswith("backend") or fullname.startswith("frontend")):
            return None
        parts = fullname.split(".")
        rel_path = os.path.join(*parts)
        pkg_init = os.path.join(CURRENT_DIR, rel_path, "__init__.py")
        if os.path.exists(pkg_init):
            return importlib.util.spec_from_file_location(
                fullname, pkg_init, submodule_search_locations=[os.path.join(CURRENT_DIR, rel_path)]
            )
        mod_py = os.path.join(CURRENT_DIR, rel_path + ".py")
        if os.path.exists(mod_py):
            return importlib.util.spec_from_file_location(fullname, mod_py)
        return None

sys.meta_path.insert(0, DirectPathFinder())

from backend.app.schemas.curriculum import (
    CourseMeta,
    CourseOutcome,
    ModuleTopic,
    ArticulationCell,
    BookCitation,
    AssessmentScheme,
    CurriculumCreate,
    GenerationRequest,
)
from backend.app.rag.generator import CurriculumGenerator
from backend.app.rag.engine import SyllabusParser, rag_store
from backend.app.latex.compiler import LatexCompiler


# Page Configuration
st.set_page_config(
    page_title="CurriculumAI Studio | NBA/AICTE Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        color: #163669;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #46505f;
        font-size: 14px;
        margin-bottom: 20px;
    }
    .badge-nba {
        background-color: #d1fae5;
        color: #065f46;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid #a7f3d0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 6px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #163669 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "curriculum" not in st.session_state:
    st.session_state.curriculum = None
if "tex_source" not in st.session_state:
    st.session_state.tex_source = ""
if "compilation_result" not in st.session_state:
    st.session_state.compilation_result = None
if "curriculum_status" not in st.session_state:
    st.session_state.curriculum_status = "DRAFT"


# Sidebar Configuration
st.sidebar.markdown("### ⚙️ Inference & Accreditation Settings")

role = st.sidebar.selectbox(
    "Active Role:",
    ["Faculty", "HOD / Reviewer", "Administrator"],
    index=0,
    help="HODs and Admins have permission to audit, approve, and sign off curricula."
)

provider = st.sidebar.selectbox(
    "LLM Provider:",
    ["Ollama (Local)", "OpenAI", "Google Gemini", "Anthropic Claude", "Groq", "Deterministic Academic (Offline)"],
    index=5,
    help="Select local Ollama for zero-cost on-prem execution or cloud API."
)

api_key = ""
ollama_url = "http://localhost:11434"
model_name = ""

if provider == "Ollama (Local)":
    ollama_url = st.sidebar.text_input("Ollama Endpoint:", value="http://localhost:11434")
    model_name = st.sidebar.selectbox("Ollama Model:", ["qwen2.5:32b", "deepseek-r1:14b", "llama3.1:8b", "mistral-nemo"])
elif provider != "Deterministic Academic (Offline)":
    secret_key_name = f"{provider.split()[0].upper()}_API_KEY"
    default_key = st.secrets.get(secret_key_name, "") if hasattr(st, "secrets") else ""
    api_key = st.sidebar.text_input(f"{provider} API Key:", value=default_key, type="password")
    if provider == "OpenAI":
        model_name = st.sidebar.text_input("Model Variant:", value="gpt-4o")
    elif provider == "Google Gemini":
        model_name = st.sidebar.text_input("Model Variant:", value="gemini-2.5-pro")
    elif provider == "Anthropic Claude":
        model_name = st.sidebar.text_input("Model Variant:", value="claude-3-5-sonnet-20241022")
    elif provider == "Groq":
        model_name = st.sidebar.text_input("Model Variant:", value="llama-3.3-70b-versatile")

temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.2, step=0.05,
                               help="Lower temperatures enforce strict adherence to NBA accreditation guidelines.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Curriculum Status:** `{st.session_state.curriculum_status}`")
if st.session_state.curriculum_status == "APPROVED":
    st.sidebar.success("✅ Curriculum Board of Studies Approved")
elif st.session_state.curriculum_status == "UNDER_REVIEW":
    st.sidebar.warning("⏳ Pending Department HOD Audit")


# Main Dashboard Header
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown('<h1 class="main-header">CurriculumAI Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">AI-Powered Outcome-Based Curriculum Designer & LaTeX Compiler for Engineering Faculty</p>', unsafe_allow_html=True)
with col_badge:
    st.markdown('<div style="text-align: right; padding-top: 15px;"><span class="badge-nba">NBA / AICTE Ready</span></div>', unsafe_allow_html=True)


# Tabs Interface
tabs = st.tabs([
    "1. Course Metadata",
    "2. Course Outcomes (COs)",
    "3. Industry Integration & RAG",
    "4. Articulation Matrix",
    "5. Curriculum Modules",
    "6. Live LaTeX Editor",
    "7. PDF Preview & Review",
])


# TAB 1: COURSE METADATA
with tabs[0]:
    st.markdown("### Course Metadata & Credit Structure (L-T-P-C)")
    st.caption("Specify course identification, semester, regulatory scheme, and contact hours.")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        course_name = st.text_input("Course / Subject Name:", value="Cloud-Native Distributed Systems & Microservices")
    with col2:
        course_code = st.text_input("Course Code:", value="22CS501")
    with col3:
        dept = st.text_input("Department / Branch:", value="Computer Science & Engineering")

    col4, col5, col6 = st.columns(3)
    with col4:
        scheme = st.selectbox("Curriculum Scheme / Regulation:", [
            "NEP 2020 / AICTE Model Curriculum",
            "Choice Based Credit System (CBCS)",
            "Autonomous Institute 2025 Regulations"
        ])
    with col5:
        academic_year = st.text_input("Academic Year:", value="2025-26")
    with col6:
        semester = st.selectbox("Semester:", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"], index=4)

    st.markdown("#### Credit Allocation & Contact Hours")
    c_l, c_t, c_p, c_c = st.columns(4)
    with c_l:
        credits_l = st.number_input("Lecture (L) hrs/week:", min_value=0, max_value=6, value=3)
    with c_t:
        credits_t = st.number_input("Tutorial (T) hrs/week:", min_value=0, max_value=4, value=0)
    with c_p:
        credits_p = st.number_input("Practical (P) hrs/week:", min_value=0, max_value=6, value=2)
    with c_c:
        credits_c = st.number_input("Total Credits (C):", min_value=1, max_value=10, value=4)

    h_tot, h_th, h_lab, h_ss = st.columns(4)
    with h_tot:
        total_hours = st.number_input("Total Theory Contact Hours:", min_value=20, max_value=120, value=45)
    with h_th:
        theory_hours = st.number_input("Theory Hours:", min_value=0, value=45)
    with h_lab:
        lab_hours = st.number_input("Practical / Lab Hours:", min_value=0, value=30)
    with h_ss:
        self_study = st.number_input("Self-Study / Project Hours:", min_value=0, value=15)


# TAB 2: COURSE OUTCOMES (COs)
with tabs[1]:
    st.markdown("### Course Outcomes (COs) & Revised Bloom's Taxonomy")
    st.caption("Formulate 6 measurable Course Outcomes mapped strictly to cognitive levels (L1 Remember to L6 Create).")

    default_cos = [
        {"id": "CO1", "level": "L2: Understand", "desc": "Understand foundational principles, consensus models, and state invariants in distributed architectures.", "target": 70},
        {"id": "CO2", "level": "L3: Apply", "desc": "Apply algorithmic synchronization, failure detectors, and caching strategies to resilient backends.", "target": 70},
        {"id": "CO3", "level": "L4: Analyze", "desc": "Analyze partition recovery mechanisms, latency tail distributions, and zero-trust perimeter contracts.", "target": 75},
        {"id": "CO4", "level": "L4: Analyze", "desc": "Formulate event-driven data streaming workflows leveraging Kafka Streams and reactive pipelines.", "target": 70},
        {"id": "CO5", "level": "L5: Evaluate", "desc": "Evaluate cloud-native container orchestrations, cost-performance trade-offs, and observability standards.", "target": 70},
        {"id": "CO6", "level": "L6: Create", "desc": "Design and synthesize an end-to-end production microservice system integrating Edge AI accelerators.", "target": 80},
    ]

    co_inputs = []
    for co in default_cos:
        c1, c2, c3, c4 = st.columns([1, 2, 5, 1.5])
        with c1:
            st.markdown(f"**{co['id']}**")
        with c2:
            level = st.selectbox(
                f"Level ({co['id']}):",
                ["L1: Remember", "L2: Understand", "L3: Apply", "L4: Analyze", "L5: Evaluate", "L6: Create"],
                index=["L1: Remember", "L2: Understand", "L3: Apply", "L4: Analyze", "L5: Evaluate", "L6: Create"].index(co["level"]),
                key=f"bloom_{co['id']}",
                label_visibility="collapsed"
            )
        with c3:
            desc = st.text_input(f"Desc ({co['id']}):", value=co["desc"], key=f"desc_{co['id']}", label_visibility="collapsed")
        with c4:
            target = st.number_input(f"Target % ({co['id']}):", min_value=50, max_value=100, value=co["target"], key=f"target_{co['id']}", label_visibility="collapsed")
        co_inputs.append({"id": co["id"], "level": level, "desc": desc, "target": target})


# TAB 3: INDUSTRY INTEGRATION & RAG
with tabs[2]:
    st.markdown("### Novel Industry Topics & Context Ingestion (RAG)")
    st.caption("Specify emerging tools and upload existing reference curricula. Theory is preserved in Modules 1–3; industry tech is injected into Modules 4–6.")

    industry_topics = st.text_area(
        "Emerging Technologies / Industry 4.0 Tools (comma-separated):",
        value="Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph, Ray Distributed, OpenTelemetry",
        help="These frameworks will be automatically incorporated into Modules 4, 5, and 6."
    )

    st.markdown("#### Upload Reference Syllabi (PDF / DOCX / TXT)")
    uploaded_file = st.file_uploader(
        "Drag and drop past syllabus documents or AICTE guidelines for hierarchical indexing:",
        type=["pdf", "docx", "txt", "md"]
    )
    if uploaded_file is not None:
        if st.button("📥 Parse & Ingest into RAG Vector Store"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                text = SyllabusParser.extract_text_from_file(tmp_path)
                chunks = SyllabusParser.hierarchical_chunk(text, doc_id=uploaded_file.name)
                rag_store.add_documents(chunks)
                st.success(f"Indexed {len(chunks)} hierarchical chunks ({len(text)} characters) from {uploaded_file.name}!")
            finally:
                os.unlink(tmp_path)


# TAB 4: ARTICULATION MATRIX
with tabs[3]:
    st.markdown("### CO-PO & CO-PSO Articulation Matrix (NBA Criterion 3)")
    st.caption("Correlation Weights: 3 = Substantial (High), 2 = Moderate (Medium), 1 = Slight (Low), - = No Correlation.")

    po_cols = [f"PO{i}" for i in range(1, 13)] + ["PSO1", "PSO2", "PSO3"]
    matrix_data = []

    for idx, co in enumerate(co_inputs):
        co_num = idx + 1
        row = {"CO ID": co["id"]}
        for po_idx in range(1, 13):
            val = "-"
            if po_idx == 1: val = "3"
            elif po_idx == 2 and co_num >= 2: val = "3" if co_num >= 3 else "2"
            elif po_idx == 3 and co_num >= 4: val = "3" if co_num == 6 else "2"
            elif po_idx == 5 and co_num >= 3: val = "3"
            elif po_idx == 12: val = "2"
            row[f"PO{po_idx}"] = val
        for pso_idx in range(1, 4):
            row[f"PSO{pso_idx}"] = "3" if co_num >= 4 else "2"
        matrix_data.append(row)

    st.dataframe(matrix_data, use_container_width=True, hide_index=True)


# TAB 5: CURRICULUM GENERATION & MODULES
with tabs[4]:
    st.markdown("### AI Generation & Mathematical Hour Balancing")
    st.caption("Generate complete module breakdown, balanced hours, textbooks, and assessment rubrics.")

    col_btn, col_info = st.columns([2, 4])
    with col_btn:
        generate_clicked = st.button("✨ Synthesize Curriculum with AI", use_container_width=True, type="primary")

    if generate_clicked:
        with st.spinner("Executing RAG retrieval and multi-model synthesis..."):
            meta_obj = CourseMeta(
                course_name=course_name,
                course_code=course_code,
                academic_year=academic_year,
                semester=semester,
                department=dept,
                scheme=scheme,
                credits_l=credits_l,
                credits_t=credits_t,
                credits_p=credits_p,
                credits_c=credits_c,
                total_contact_hours=total_hours,
                theory_hours=theory_hours,
                lab_hours=lab_hours,
                self_study_hours=self_study
            )
            provider_code = provider.split()[0].lower()
            if "offline" in provider.lower():
                provider_code = "offline"

            gen_req = GenerationRequest(
                course_meta=meta_obj,
                industry_topics=industry_topics,
                num_modules=5,
                model_provider=provider_code,
                model_name=model_name or None,
                api_key=api_key or None,
                ollama_url=ollama_url or None,
                temperature=temperature
            )
            generator = CurriculumGenerator(gen_req)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            curr = loop.run_until_complete(generator.generate_curriculum())
            loop.close()

            compiler = LatexCompiler()
            tex = compiler.render_template(curr)

            st.session_state.curriculum = curr
            st.session_state.tex_source = tex
            st.session_state.curriculum_status = "DRAFT"
            st.success("Curriculum synthesized successfully! Proceed to Tab 6 to compile or edit.")

    if st.session_state.curriculum:
        st.markdown("---")
        curr = st.session_state.curriculum
        st.markdown(f"#### Generated Modules (Total Hours: {sum(m.contact_hours for m in curr.modules)} / {curr.course_meta.total_contact_hours})")
        for mod in curr.modules:
            with st.expander(f"Module {mod.module_number}: {mod.title} ({mod.contact_hours} Hours - {mod.weightage_pct}%)", expanded=(mod.module_number == 1)):
                st.markdown(f"**Cognitive Level:** `{mod.cognitive_level}`")
                if mod.industry_integration_tags:
                    st.markdown(f"**Industry Integration:** `{', '.join(mod.industry_integration_tags)}`")
                st.markdown("**Itemized Topics:**")
                for t in mod.topics:
                    st.markdown(f"- {t}")


# TAB 6: LIVE LATEX EDITOR & COMPILER
with tabs[5]:
    st.markdown("### Live LaTeX Source Editor & Subprocess pdflatex Compiler")
    st.caption("Inspect and refine the Jinja2 LaTeX source before compiling to PDF.")

    tex_input = st.text_area(
        "LaTeX Source Code (.tex):",
        value=st.session_state.tex_source or "% Click 'Synthesize Curriculum' in Tab 5 to generate LaTeX...",
        height=450
    )
    st.session_state.tex_source = tex_input

    col_comp, col_clear = st.columns([2, 1])
    with col_comp:
        if st.button("🔨 Compile LaTeX to PDF (2-Pass)", type="primary", use_container_width=True):
            if not st.session_state.tex_source.strip():
                st.error("LaTeX source is empty.")
            else:
                with st.spinner("Executing two-pass pdflatex subprocess worker..."):
                    compiler = LatexCompiler()
                    res = compiler.compile(st.session_state.tex_source, output_prefix=f"{course_code}_{course_name}")
                    st.session_state.compilation_result = res
                    if res.success:
                        st.success(f"Compilation succeeded! PDF created: {os.path.basename(res.pdf_path)} ({os.path.getsize(res.pdf_path)} bytes)")
                    else:
                        st.error("LaTeX compilation error encountered.")

    if st.session_state.compilation_result:
        res = st.session_state.compilation_result
        if not res.success:
            st.markdown("#### Errors Detected:")
            for err in (res.errors or []):
                st.code(err, language="text")
        with st.expander("Show Compiler Output Log", expanded=not res.success):
            st.code(res.log_output, language="text")


# TAB 7: PDF PREVIEW & REVIEW WORKFLOW
with tabs[6]:
    st.markdown("### Accreditation Review & Deliverables Export")
    st.caption("Download the compiled PDF, LaTeX source, or complete ZIP package, and perform HOD sign-off.")

    res = st.session_state.compilation_result

    # Top action bar
    if res and res.success and res.pdf_path and os.path.exists(res.pdf_path):
        with open(res.pdf_path, "rb") as f:
            pdf_bytes = f.read()

        zip_bytes = None
        if res.zip_path and os.path.exists(res.zip_path):
            with open(res.zip_path, "rb") as f:
                zip_bytes = f.read()

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                "📥 Download Compiled PDF",
                data=pdf_bytes,
                file_name=f"{course_code}_NBA_Curriculum.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with d2:
            st.download_button(
                "📄 Download LaTeX Source (.tex)",
                data=st.session_state.tex_source,
                file_name=f"{course_code}_Curriculum.tex",
                mime="text/x-tex",
                use_container_width=True
            )
        with d3:
            if zip_bytes:
                st.download_button(
                    "📦 Download Full ZIP Bundle",
                    data=zip_bytes,
                    file_name=f"{course_code}_Curriculum_Bundle.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        # HOD Review Approval Workflow
        st.markdown("---")
        st.markdown("#### Institutional Review & Sign-Off Workflow")
        if role in ["HOD / Reviewer", "Administrator"]:
            r_col1, r_col2 = st.columns([1, 2])
            with r_col1:
                decision = st.selectbox("Accreditation Decision:", ["APPROVED", "CHANGES_REQUESTED", "REJECTED"])
            with r_col2:
                review_notes = st.text_input("Reviewer Comments:", value="Approved for Board of Studies. Complies with AICTE model curriculum.")
            if st.button("Submit Official Review"):
                st.session_state.curriculum_status = decision
                st.success(f"Curriculum status updated to: {decision}")
        else:
            st.info("Log in as HOD or Administrator in the sidebar to review and approve this curriculum.")

        # PDF Preview via iframe
        st.markdown("---")
        st.markdown("#### Document Preview:")
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("No compiled PDF available yet. Synthesize curriculum in Tab 5 and click 'Compile to PDF' in Tab 6.")
