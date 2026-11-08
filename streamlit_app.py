"""
CurriculumAI Studio - Streamlit Web Application
Production-grade NBA/AICTE-Compliant Curriculum Generation & LaTeX Compilation Studio.
Features:
- Multi-Domain Bloom's (Cognitive, Psychomotor for Lab, Affective)
- Comprehensive Assessment Scheme (CIA, MSE, CIAP, ESE, ESEP, SLA)
- Official SAKEC OBE Manual Version 3.0 Departmental PSOs & Annexure B Rubrics
- Microsoft Teams Rubric CSV Builder & 1-Click Exporter (v.11p Schema)
- Reference LaTeX Template Upload & 2-Pass pdflatex Compiler
- Dedicated C-DAC PARAM Shavak Qwen HPC Integration
"""

import asyncio
import os
import sys
import tempfile
import base64
import re
from typing import Dict, List, Any

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import streamlit as st
import httpx

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
try:
    from backend.app.schemas.curriculum import ProgramSpecificOutcome
except ImportError:
    from pydantic import BaseModel, Field
    class ProgramSpecificOutcome(BaseModel):  # type: ignore
        pso_id: str = Field(default="PSO1")
        statement: str = Field(default="")
from backend.app.schemas.assessment import (
    AssessmentComponentDetail,
    AssessmentPlanRequest,
    AssessmentPlanResponse,
)
from backend.app.rag.generator import CurriculumGenerator
from backend.app.rag.assessment_generator import AssessmentPlanGenerator, OBE_ASSESSMENT_CATALOG
from backend.app.rag.sakec_obe_rubrics import SAKEC_OBE_RUBRICS_CATALOG, generate_ms_teams_rubric_csv
from backend.app.rag.engine import SyllabusParser, rag_store
from backend.app.latex.compiler import LatexCompiler
from backend.app.latex.assessment_compiler import AssessmentPlanCompiler


# Official SAKEC OBE Manual Version 3.0 - Department PSOs
SAKEC_DEPARTMENT_PSOS = {
    "Computer Engineering": [
        {"id": "PSO1", "statement": "Develop innovative solutions by leveraging specialized knowledge in Networking, Cloud Computing, Artificial Intelligence, Data Science, and Cyber Security to solve complex engineering problems."},
        {"id": "PSO2", "statement": "Design and develop intelligent software systems by fostering creativity, analytical thinking, problem-solving ability, and adaptability to emerging technologies."},
    ],
    "Information Technology": [
        {"id": "PSO1", "statement": "Analyze, design, develop, test, and manage Information Technology-based solutions by applying engineering principles, mathematical foundations, and modern computing technologies to solve real-world and open-ended problems."},
        {"id": "PSO2", "statement": "Perform diverse professional roles as software engineers, system architects, entrepreneurs, researchers, or higher education aspirants while upholding ethical values, professionalism, and social responsibility."},
    ],
    "Artificial Intelligence and Data Science": [
        {"id": "PSO1", "statement": "Demonstrate proficiency in Machine Learning, Deep Learning, Natural Language Processing and related AI technologies for innovative multidisciplinary solutions."},
        {"id": "PSO2", "statement": "Engineer robust and scalable AI/Data Science pipelines using modern computing infrastructures while ensuring ethical and sustainable practices."},
        {"id": "PSO3", "statement": "Exhibit research capabilities in emerging AI domains, integrating entrepreneurship, sustainability, and ethics into impactful industrial and societal solutions."},
    ],
    "Cyber Security": [
        {"id": "PSO1", "statement": "Analyze evolving software and hardware security threats, identify system vulnerabilities, and apply appropriate cybersecurity principles to safeguard digital infrastructure."},
        {"id": "PSO2", "statement": "Apply ethical hacking techniques, modern cybersecurity tools, and emerging technologies to develop innovative security solutions while balancing security, privacy, legal, and law-enforcement requirements."},
    ],
    "Electronics & Computer Science": [
        {"id": "PSO1", "statement": "Develop technically sound, economically viable, and ethically responsible solutions to real-world engineering problems by integrating the principles of Electronics Engineering with Computer Science techniques."},
        {"id": "PSO2", "statement": "Apply emerging technologies in areas such as Internet of Things (IoT), Communication Networks, Cloud Computing, Artificial Intelligence, Database Systems, and Information Management to develop innovative solutions that contribute to societal and industrial advancement."},
    ],
    "Electronics & Telecommunication Engineering": [
        {"id": "PSO1", "statement": "Design technically sound, economically feasible, and sustainable solutions in the areas of analog and digital electronics, signal processing, embedded systems, and VLSI applications."},
        {"id": "PSO2", "statement": "Apply modern modelling, simulation, and computational techniques for the analysis, design, and implementation of communication, networking, and data management systems."},
        {"id": "PSO3", "statement": "Develop interdisciplinary solutions in emerging application domains such as Agriculture, Telemetry, Healthcare, Multimedia, Internet of Things (IoT), Artificial Intelligence (AI), and other engineering management fields."},
    ],
    "Advanced Communication Technology": [
        {"id": "PSO1", "statement": "Demonstrate knowledge in advanced communication engineering including next-generation telecommunication networks, satellite communication and allied technologies to provide scalable industrial solutions."},
        {"id": "PSO2", "statement": "Develop innovative and sustainable solutions in hardware systems, communication and networking, IT security, AI&ML and signal processing using modern design tools."},
        {"id": "PSO3", "statement": "Design, develop and test embedded systems for solving societal problems."},
    ],
    "VLSI Design & Technology": [
        {"id": "PSO1", "statement": "Pursue higher education, research, and innovation by adapting to emerging trends and advanced technologies in the VLSI and semiconductor domains."},
        {"id": "PSO2", "statement": "Demonstrate enhanced employability through technical competence, teamwork, leadership qualities, and effective use of modern VLSI design tools and methodologies."},
    ],
}


# Page Configuration
st.set_page_config(
    page_title="CurriculumAI Studio | SAKEC NBA/AICTE Platform",
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
    .badge-param {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid #fde68a;
    }
    .badge-teams {
        background-color: #e0e7ff;
        color: #3730a3;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid #c7d2fe;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #163669 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)



# Official SAKEC Institutional Metadata (from https://www.sakec.ac.in/)
SAKEC_INSTITUTE_INFO = {
    "trust": "Mahavir Education Trust's",
    "name": "SHAH & ANCHOR KUTCHHI ENGINEERING COLLEGE",
    "autonomous_status": "An Autonomous Institute Affiliated to University of Mumbai (UGC Autonomy: AY 2024-25 to 2033-34)",
    "approvals": "Approved by AICTE, New Delhi & Govt. of Maharashtra | Established in 1985 | ISO 9001:2015 Certified",
    "accreditations": (
        "NAAC Accredited 'A' Grade (3.16 CGPA) | NBA Accredited UG Programs: Computer Engg. & IT (up to 30/06/2028), "
        "EXTC (up to 30/06/2027) | NIRF Ranked (251-300 Band) | University of Mumbai's Best College Honor (2024-25)"
    ),
    "dte_code": "3148",
    "address": "Mahavir Education Trust's Chowk, W. T. Patil Marg, D P Road, Next to Duke's Company, Chembur, Mumbai – 400 088, Maharashtra, India",
    "phone": "022-25580854 / 022-67978100",
    "fax": "022-25568100",
    "email": "info@sakec.ac.in | registrar@sakec.ac.in | examcell@sakec.ac.in",
    "website": "https://www.sakec.ac.in/",
    "principal": "Dr. Bhavesh Patel (Ph.D. in Computer Engineering)",
    "developer": "Dr. Rohan Borgalli",
    "dte_course_codes": [
        {"dept": "Computer Engineering", "dte_code": "314824510", "ug_intake": 180, "wp_intake": 30, "pg_intake": 9, "phd_intake": 10, "nba": "Accredited (2025-2028)"},
        {"dept": "Information Technology", "dte_code": "314824610", "ug_intake": 180, "wp_intake": 30, "pg_intake": 9, "phd_intake": 10, "nba": "Accredited (2025-2028)"},
        {"dept": "Electronics & Computer Science", "dte_code": "314890010", "ug_intake": 120, "wp_intake": 0, "pg_intake": 9, "phd_intake": 0, "nba": "Autonomous OBE Scheme"},
        {"dept": "Electronics & Telecommunication Engineering", "dte_code": "314837210", "ug_intake": 60, "wp_intake": 0, "pg_intake": 0, "phd_intake": 0, "nba": "Accredited (2024-2027)"},
        {"dept": "Artificial Intelligence and Data Science", "dte_code": "314899510", "ug_intake": 120, "wp_intake": 0, "pg_intake": 0, "phd_intake": 0, "nba": "Autonomous OBE Scheme"},
        {"dept": "Cyber Security", "dte_code": "314825210", "ug_intake": 60, "wp_intake": 0, "pg_intake": 0, "phd_intake": 0, "nba": "Autonomous OBE Scheme"},
        {"dept": "VLSI Design & Technology", "dte_code": "314837810", "ug_intake": 60, "wp_intake": 0, "pg_intake": 0, "phd_intake": 0, "nba": "Autonomous OBE Scheme"},
        {"dept": "Advanced Communication Technology", "dte_code": "314892810", "ug_intake": 60, "wp_intake": 0, "pg_intake": 0, "phd_intake": 0, "nba": "Autonomous OBE Scheme"},
    ],
}

# Hierarchical Role Access Matrix:
# - Faculty: All 10 Authoring, Compilation & MS Teams Rubric Tabs (Tabs 1-10)
# - HOD: Inherits ALL Faculty Access (Tabs 1-10) + HOD Department Governance & BoS Approval (Tab 11)
# - Principal: Inherits ALL Faculty + HOD + Principal & Admin Access (Tabs 1-12) across all departments
# - Admin: Full System, User Directory, HPC & Institutional Access (Tabs 1-12)
ROLE_PERMISSIONS = {
    "Faculty": {
        "inherited_roles": ["Faculty"],
        "badge_color": "#0284c7",
        "description": "Full Course Authoring, Multi-Domain COs, LaTeX/PDF Compilation & MS Teams Rubric Export (Tabs 1–10).",
    },
    "HOD": {
        "inherited_roles": ["Faculty", "HOD"],
        "badge_color": "#d97706",
        "description": "Inherits ALL Faculty Access (Tabs 1–10) + Department HOD Review, BoS Sign-Off & PSO Lock (Tab 11).",
    },
    "Principal": {
        "inherited_roles": ["Faculty", "HOD", "Principal", "Admin"],
        "badge_color": "#7c3aed",
        "description": "Inherits ALL Faculty + HOD + Principal & Admin Access (Tabs 1–12) across all 8 SAKEC Departments & Final Seal.",
    },
    "Admin": {
        "inherited_roles": ["Faculty", "HOD", "Principal", "Admin"],
        "badge_color": "#059669",
        "description": "Full System Administration, User & Role Provisioning, PARAM Shavak HPC Config & All Tabs (Tabs 1–12).",
    },
}

DEFAULT_SAKEC_USERS = {
    "faculty@sakec.ac.in": {
        "email": "faculty@sakec.ac.in",
        "password": "sakec@123",
        "name": "Dr. Rohan Borgalli",
        "designation": "Assistant Professor & Incubator In-Charge (SAKEC TBI)",
        "role": "Faculty",
        "department": "Electronics & Telecommunication Engineering",
    },
    "hod@sakec.ac.in": {
        "email": "hod@sakec.ac.in",
        "password": "sakec@123",
        "name": "Head of Department (HOD)",
        "designation": "Head of Department & Chairman, Board of Studies (BoS)",
        "role": "HOD",
        "department": "Computer Engineering",
    },
    "principal@sakec.ac.in": {
        "email": "principal@sakec.ac.in",
        "password": "sakec@123",
        "name": "Dr. Bhavesh Patel",
        "designation": "Principal, Shah & Anchor Kutchhi Engineering College",
        "role": "Principal",
        "department": "All SAKEC Departments (Institute-Wide)",
    },
    "admin@sakec.ac.in": {
        "email": "admin@sakec.ac.in",
        "password": "sakec@123",
        "name": "SAKEC ERP & System Administrator",
        "designation": "Institutional ERP, Samarth & PARAM Shavak HPC Admin",
        "role": "Admin",
        "department": "All SAKEC Departments (System-Wide)",
    },
}


def render_sakec_institutional_header():
    """Renders the official Shah & Anchor Kutchhi Engineering College (https://www.sakec.ac.in/) header banner."""
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #0f2547 0%, #163669 60%, #1e4682 100%); color: white; padding: 16px 22px; border-radius: 12px; border-bottom: 4px solid #f59e0b; margin-bottom: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.12);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="flex: 1; min-width: 280px;">
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1.4px; color: #fde68a; font-weight: 700;">
                        Mahavir Education Trust's
                    </div>
                    <div style="font-size: 24px; font-weight: 900; letter-spacing: 0.4px; color: #ffffff; line-height: 1.2; margin: 2px 0;">
                        SHAH &amp; ANCHOR KUTCHHI ENGINEERING COLLEGE
                    </div>
                    <div style="font-size: 13px; color: #e0f2fe; font-weight: 600; margin-top: 2px;">
                        An Autonomous Institute Affiliated to University of Mumbai (UGC 10-Year Autonomy: AY 2024–25 to 2033–34) &bull; Approved by AICTE, New Delhi &amp; Govt. of Maharashtra
                    </div>
                    <div style="font-size: 11.5px; color: #cbd5e1; margin-top: 4px;">
                        🏆 <b>NAAC Accredited 'A' Grade (3.16 CGPA)</b> &bull; <b>NBA Accredited UG Programs</b> (Computer Engg., IT, EXTC) &bull; <b>ISO 9001:2015</b> &bull; <b>NIRF Ranked (251–300)</b> &bull; <b>UoM Best College Award 2024–25</b> &bull; <b>DTE Institute Code: 3148</b>
                    </div>
                    <div style="font-size: 11.5px; color: #e2e8f0; margin-top: 4px;">
                        📍 Mahavir Education Trust's Chowk, W. T. Patil Marg, D P Road, Next to Duke's Company, Chembur, Mumbai – 400 088, Maharashtra &bull; ☎️ 022-25580854 / 022-67978100 &bull; ✉️ <a href="mailto:info@sakec.ac.in" style="color: #93c5fd; text-decoration: underline;">info@sakec.ac.in</a> &bull; 🌐 <a href="https://www.sakec.ac.in/" target="_blank" style="color: #fde68a; font-weight: 700; text-decoration: underline;">www.sakec.ac.in</a>
                    </div>
                </div>
                <div style="text-align: right; min-width: 230px; background: rgba(255,255,255,0.1); padding: 10px 14px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.22);">
                    <div style="font-size: 11px; color: #fde68a; font-weight: 700; text-transform: uppercase;">CurriculumAI Studio &bull; OBE V3.0</div>
                    <div style="font-size: 12px; color: #ffffff; margin-top: 3px;"><b>Principal:</b> Dr. Bhavesh Patel</div>
                    <div style="font-size: 13px; color: #fef08a; font-weight: 800; margin-top: 4px; background: rgba(0,0,0,0.28); padding: 4px 8px; border-radius: 5px;">
                        👨‍💻 Developed by Dr. Rohan Borgalli
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sakec_footer():
    """Renders the official SAKEC footer and developer attribution."""
    st.markdown("---")
    st.markdown(
        """
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #163669; padding: 12px 18px; border-radius: 8px; font-size: 12px; color: #334155; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div>
                <b>© Shah &amp; Anchor Kutchhi Engineering College (Autonomous)</b> &bull; DTE Code: <b>3148</b> &bull; Chembur, Mumbai – 400 088 &bull;
                <a href="https://www.sakec.ac.in/" target="_blank" style="color: #163669; font-weight: 700;">https://www.sakec.ac.in/</a> &bull;
                <a href="https://www.sakec.ac.in/contact/" target="_blank" style="color: #163669;">Contact Us (022-25580854)</a>
            </div>
            <div style="font-weight: 700; color: #163669; background: #e0e7ff; padding: 4px 12px; border-radius: 999px;">
                🚀 Engineered &amp; Developed by Dr. Rohan Borgalli (SAKEC)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_directory" not in st.session_state:
    st.session_state.user_directory = {k: dict(v) for k, v in DEFAULT_SAKEC_USERS.items()}
if "current_user" not in st.session_state:
    st.session_state.current_user = dict(DEFAULT_SAKEC_USERS["faculty@sakec.ac.in"])
if "principal_seal" not in st.session_state:
    st.session_state.principal_seal = "PENDING_ACADEMIC_COUNCIL"
if "curriculum" not in st.session_state:
    st.session_state.curriculum = None
if "tex_source" not in st.session_state:
    st.session_state.tex_source = ""
if "tex_editor_version" not in st.session_state:
    st.session_state.tex_editor_version = 0
if "custom_uploaded_tex" not in st.session_state:
    st.session_state.custom_uploaded_tex = ""
if "last_uploaded_tex_hash" not in st.session_state:
    st.session_state.last_uploaded_tex_hash = ""
if "compilation_result" not in st.session_state:
    st.session_state.compilation_result = None
if "curriculum_status" not in st.session_state:
    st.session_state.curriculum_status = "DRAFT"
if "custom_psos" not in st.session_state:
    st.session_state.custom_psos = [dict(x) for x in SAKEC_DEPARTMENT_PSOS["Computer Engineering"]]
if "assessment_plan" not in st.session_state:
    st.session_state.assessment_plan = None
if "assessment_tex_source" not in st.session_state:
    st.session_state.assessment_tex_source = ""
if "assessment_compilation_result" not in st.session_state:
    st.session_state.assessment_compilation_result = None
if "editable_rubric" not in st.session_state:
    st.session_state.editable_rubric = [
        dict(x) for x in SAKEC_OBE_RUBRICS_CATALOG["25.8 Reel / Blog / Skit Activity Rubric (5 Criteria - MS Teams Standard)"]
    ]


# Render Official SAKEC Header Banner at Top of Page
render_sakec_institutional_header()


# Dedicated Role-Based Authentication Page (Faculty, HOD, Principal, Admin)
if not st.session_state.authenticated:
    st.markdown("### 🔐 SAKEC Institutional Authentication & Role-Based Access Portal")
    st.caption("Sign in with your SAKEC institutional credentials or use the 1-Click Role Access cards below. Hierarchical access is enforced: **HOD** inherits all **Faculty** privileges; **Principal** and **Admin** inherit all **Faculty + HOD + Institutional** privileges.")

    auth_col1, auth_col2 = st.columns([1.2, 1.5])

    with auth_col1:
        st.markdown("#### 🔑 Institutional Sign-In")
        with st.form("sakec_login_form"):
            login_email = st.text_input("SAKEC Email ID:", value="faculty@sakec.ac.in", placeholder="username@sakec.ac.in")
            login_password = st.text_input("Password:", value="sakec@123", type="password")
            submit_login = st.form_submit_button("🔓 Sign In to CurriculumAI Studio", type="primary", use_container_width=True)

            if submit_login:
                email_clean = login_email.strip().lower()
                user_rec = st.session_state.user_directory.get(email_clean)
                if user_rec and user_rec["password"] == login_password:
                    st.session_state.authenticated = True
                    st.session_state.current_user = dict(user_rec)
                    st.rerun()
                else:
                    st.error("Invalid SAKEC email or password. Use default password `sakec@123` or click a Quick Login card on the right.")

        with st.expander("➕ Register New SAKEC Faculty / HOD Account", expanded=False):
            reg_name = st.text_input("Full Name (with Title):", placeholder="e.g., Dr. Rohan Borgalli")
            reg_email = st.text_input("Official SAKEC Email:", placeholder="rohan.borgalli@sakec.ac.in")
            reg_role = st.selectbox("Institutional Role:", ["Faculty", "HOD", "Principal", "Admin"])
            reg_dept = st.selectbox("Department:", list(SAKEC_DEPARTMENT_PSOS.keys()))
            reg_pwd = st.text_input("Set Password:", value="sakec@123", type="password")
            if st.button("✅ Create & Sign In"):
                if reg_name and reg_email:
                    new_u = {
                        "email": reg_email.strip().lower(),
                        "password": reg_pwd,
                        "name": reg_name.strip(),
                        "designation": f"{reg_role}, Dept. of {reg_dept}",
                        "role": reg_role,
                        "department": reg_dept,
                    }
                    st.session_state.user_directory[new_u["email"]] = new_u
                    st.session_state.authenticated = True
                    st.session_state.current_user = new_u
                    st.rerun()

    with auth_col2:
        st.markdown("#### ⚡ 1-Click Role Access & Hierarchical Permission Matrix")
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            st.info(
                "**👨‍🏫 Faculty Access**\n"
                "- **User**: Dr. Rohan Borgalli (`faculty@sakec.ac.in`)\n"
                "- **Scope**: Course Authoring, Multi-Domain COs, LaTeX/PDF & MS Teams Rubrics (`.csv`)"
            )
            if st.button("🚀 Login as Faculty (Dr. Rohan Borgalli)", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.current_user = dict(st.session_state.user_directory["faculty@sakec.ac.in"])
                st.rerun()

            st.success(
                "**🎓 Principal Access (All Access)**\n"
                "- **User**: Dr. Bhavesh Patel (`principal@sakec.ac.in`)\n"
                "- **Scope**: **All Faculty + All HOD + Institute-Wide Principal & Admin Access**"
            )
            if st.button("🚀 Login as Principal (Dr. Bhavesh Patel)", type="primary", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.current_user = dict(st.session_state.user_directory["principal@sakec.ac.in"])
                st.rerun()

        with q_col2:
            st.warning(
                "**🏛️ HOD Access (All Faculty + HOD)**\n"
                "- **User**: Head of Department (`hod@sakec.ac.in`)\n"
                "- **Scope**: **Inherits All Faculty Access** + BoS Approval & Dept. PSO Lock"
            )
            if st.button("🚀 Login as HOD (Dept. Head)", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.current_user = dict(st.session_state.user_directory["hod@sakec.ac.in"])
                st.rerun()

            st.info(
                "**🛡️ Admin Access (System & All)**\n"
                "- **User**: System Admin (`admin@sakec.ac.in`)\n"
                "- **Scope**: **All Access** + User Provisioning & PARAM Shavak HPC Config"
            )
            if st.button("🚀 Login as System Admin", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.current_user = dict(st.session_state.user_directory["admin@sakec.ac.in"])
                st.rerun()

        st.markdown("##### 📊 SAKEC Programs & DTE Codes (`https://www.sakec.ac.in/` — Institute Code: `3148`)")
        st.dataframe(SAKEC_INSTITUTE_INFO["dte_course_codes"], hide_index=True, use_container_width=True)

    render_sakec_footer()
    st.stop()


# Logged-In User Context & Sidebar Profile / Role Switcher
current_user = st.session_state.current_user
role = current_user.get("role", "Faculty")
effective_roles = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["Faculty"])["inherited_roles"]

st.sidebar.markdown("### 👤 SAKEC Authenticated Session")
st.sidebar.markdown(
    f"<div style='background:#f1f5f9; padding:10px 12px; border-radius:8px; border-left:4px solid #163669; font-size:12.5px;'>"
    f"<b>{current_user.get('name')}</b><br>"
    f"<span style='color:#475569;'>{current_user.get('designation')}</span><br>"
    f"<b>Role:</b> <code>{role}</code> &bull; <b>Inherited:</b> <code>{', '.join(effective_roles)}</code><br>"
    f"<span style='color:#0f172a; font-size:11px;'>👨‍💻 Developed by Dr. Rohan Borgalli</span>"
    f"</div>",
    unsafe_allow_html=True,
)

role_switch_options = ["Faculty", "HOD", "Principal", "Admin"]
selected_switch_role = st.sidebar.selectbox(
    "Switch Active Role View:",
    role_switch_options,
    index=role_switch_options.index(role) if role in role_switch_options else 0,
    help="HOD gets all Faculty access; Principal and Admin get all Faculty + HOD + Institutional access."
)
if selected_switch_role != role:
    role_to_default_email = {
        "Faculty": "faculty@sakec.ac.in",
        "HOD": "hod@sakec.ac.in",
        "Principal": "principal@sakec.ac.in",
        "Admin": "admin@sakec.ac.in",
    }
    st.session_state.current_user = dict(st.session_state.user_directory[role_to_default_email[selected_switch_role]])
    st.rerun()

if st.sidebar.button("🚪 Logout to SAKEC Login Page", use_container_width=True):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Inference & Server Settings")

server_mode = st.sidebar.radio(
    "AI Engine Source:",
    ["C-DAC PARAM Shavak (On-Prem)", "Local Workstation (Ollama)", "Cloud API (OpenAI/Gemini/Claude)", "Offline Synthesizer"],
    index=0
)

api_key = ""
ollama_url = "http://localhost:11434"
model_name = "qwen2.5:32b"
provider_code = "ollama"

if server_mode == "C-DAC PARAM Shavak (On-Prem)":
    from backend.app.llm.param_shavak_discovery import auto_discover_param_shavak_sync
    st.sidebar.markdown("#### 🖥️ PARAM Shavak Zero-Auth Auto-Config")
    default_host = os.getenv("PARAM_SHAVAK_HOST", "192.168.1.150")
    param_ip = st.sidebar.text_input(
        "PARAM Shavak Host / IP:",
        value=default_host,
        help="Only the IP/hostname is needed (or localhost if via SSH tunnel). Port, protocol, and installed Qwen model tag are auto-discovered without any API key."
    )
    serving_framework = st.sidebar.selectbox(
        "Model Serving Protocol:",
        [
            "Auto-Detect (Zero-Auth Probe: 11434 / 8000 / 8080)",
            "Ollama (Port 11434 - /api/tags)",
            "vLLM / TGI (Port 8000 - /v1/models)",
        ],
        index=0
    )

    discovered_info = st.session_state.get("param_shavak_discovered", None)
    default_models = [
        "auto (Auto-Detect Deployed Qwen Model)",
        "qwen2.5:32b",
        "qwen2.5:14b",
        "qwen2.5:7b",
        "Qwen/Qwen2.5-14B-Instruct",
        "Qwen/Qwen2.5-32B-Instruct",
        "deepseek-r1:14b",
    ]
    if discovered_info and discovered_info.get("discovered_models"):
        default_models = discovered_info["discovered_models"] + [m for m in default_models if m not in discovered_info["discovered_models"]]

    model_name = st.sidebar.selectbox(
        "Deployed Qwen Model on PARAM Shavak:",
        default_models,
        index=0
    )

    if "Auto-Detect" in serving_framework:
        if discovered_info and discovered_info.get("connected"):
            ollama_url = discovered_info["base_url"]
            provider_code = discovered_info["protocol"]
        else:
            ollama_url = f"http://{param_ip}:11434"
            provider_code = "param_shavak_auto"
    elif "11434" in serving_framework:
        ollama_url = f"http://{param_ip}:11434"
        provider_code = "ollama"
    else:
        ollama_url = f"http://{param_ip}:8000/v1"
        provider_code = "vllm"

    if st.sidebar.button("🔍 Auto-Discover & Configure Qwen (Zero-Auth)"):
        with st.sidebar:
            with st.spinner("Scanning ports 11434, 8000, 8080 without authentication..."):
                disc = auto_discover_param_shavak_sync(param_ip, timeout=2.5, preferred_model="qwen")
                st.session_state["param_shavak_discovered"] = disc
                if disc["connected"]:
                    st.success(
                        f"✅ Auto-Configured!\n"
                        f"- **Protocol**: `{disc.get('protocol', 'ollama').upper()}` (Port `{disc.get('port', 11434)}`)\n"
                        f"- **Selected Model**: `{disc.get('selected_model')}`\n"
                        f"- **Auth**: `{disc.get('auth_mode')}`"
                    )
                else:
                    st.warning(
                        f"⚠️ Could not reach `{param_ip}` on ports 11434/8000/8080 from this network. "
                        f"Runtime auto-fallback (`{disc.get('selected_model')}`) remains active when deployed on campus LAN."
                    )

elif server_mode == "Local Workstation (Ollama)":
    ollama_url = st.sidebar.text_input("Ollama Endpoint:", value="http://localhost:11434")
    model_name = st.sidebar.selectbox("Ollama Model:", ["qwen2.5:32b", "deepseek-r1:14b", "llama3.1:8b", "mistral-nemo"])
    provider_code = "ollama"

elif server_mode == "Cloud API (OpenAI/Gemini/Claude)":
    cloud_provider = st.sidebar.selectbox("Cloud Provider:", ["OpenAI", "Google Gemini", "Anthropic Claude", "Groq"])
    secret_key_name = f"{cloud_provider.split()[0].upper()}_API_KEY"
    default_key = st.secrets.get(secret_key_name, "") if hasattr(st, "secrets") else ""
    api_key = st.sidebar.text_input(f"{cloud_provider} API Key:", value=default_key, type="password")
    if cloud_provider == "OpenAI":
        model_name = st.sidebar.text_input("Model Variant:", value="gpt-4o")
        provider_code = "openai"
    elif cloud_provider == "Google Gemini":
        model_name = st.sidebar.text_input("Model Variant:", value="gemini-2.5-pro")
        provider_code = "gemini"
    elif cloud_provider == "Anthropic Claude":
        model_name = st.sidebar.text_input("Model Variant:", value="claude-3-5-sonnet-20241022")
        provider_code = "anthropic"
    elif cloud_provider == "Groq":
        model_name = st.sidebar.text_input("Model Variant:", value="llama-3.3-70b-versatile")
        provider_code = "groq"

else:
    provider_code = "offline"

temperature = st.sidebar.slider("Temperature:", min_value=0.0, max_value=1.0, value=0.2, step=0.05,
                               help="Lower temperatures enforce strict compliance with NBA syllabus rules.")

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Curriculum Status:** `{st.session_state.curriculum_status}`")
if st.session_state.curriculum_status == "APPROVED":
    st.sidebar.success("✅ Curriculum Board of Studies Approved")
elif st.session_state.curriculum_status == "UNDER_REVIEW":
    st.sidebar.warning("⏳ Pending Department HOD Audit")


# Main Dashboard Header
col_title, col_badge = st.columns([3.5, 2.5])
with col_title:
    st.markdown('<h1 class="main-header">CurriculumAI Studio</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">SAKEC OBE Manual Version 3.0 Compliant Curriculum Architect, Multi-Domain Bloom\'s & MS Teams Rubric Exporter</p>', unsafe_allow_html=True)
with col_badge:
    st.markdown('<div style="text-align: right; padding-top: 15px;"><span class="badge-nba">SAKEC OBE V3.0</span> <span class="badge-teams">MS Teams CSV Ready</span> <span class="badge-param">PARAM Shavak HPC</span></div>', unsafe_allow_html=True)


# Dynamic Hierarchical Tabs Interface
# - Faculty: Tabs 1 to 10
# - HOD: All Faculty Tabs (1 to 10) + Tab 11 (HOD Department Governance & BoS Sign-Off)
# - Principal & Admin: All Faculty Tabs (1 to 10) + Tab 11 (HOD Governance) + Tab 12 (Principal & Admin Institutional Console)
tab_labels = [
    "1. Course Meta",
    "2. Multi-Domain COs",
    "3. Department PSOs",
    "4. Assessment Matrix",
    "5. Industry & RAG",
    "6. Articulation Matrix",
    "7. Curriculum Modules",
    "8. LaTeX Compiler",
    "9. PDF Export & Review",
    "10. OBE Assessment & MS Teams Rubrics (.csv)",
]
if "HOD" in effective_roles:
    tab_labels.append("11. 🏛️ HOD Governance & BoS Approval")
if "Principal" in effective_roles or "Admin" in effective_roles:
    tab_labels.append("12. 🎓 Principal & Admin Institutional Console")

tabs = st.tabs(tab_labels)


# TAB 1: COURSE METADATA
with tabs[0]:
    st.markdown("### Course Metadata & Credit Structure (L-T-P-C)")
    st.caption("Specify course identification, semester, regulatory scheme, course type, and contact hours.")

    col1, col2, col3 = st.columns([2, 1, 1.5])
    with col1:
        course_name = st.text_input("Course / Subject Name:", value="Cloud-Native Distributed Systems & Microservices")
    with col2:
        course_code = st.text_input("Course Code:", value="22CS501")
    with col3:
        dept = st.selectbox("SAKEC Department / Programme:", list(SAKEC_DEPARTMENT_PSOS.keys()), index=0)

    col4, col5, col6, col7 = st.columns(4)
    with col4:
        course_type = st.selectbox("Course Type:", [
            "Integrated Course (Theory + Lab)",
            "Theory Course Only",
            "Laboratory / Practical Course Only",
            "Project / Seminar Course"
        ], index=0)
    with col5:
        scheme = st.selectbox("Curriculum Scheme / Regulation:", [
            "SAKEC Autonomous NEP 2020 Scheme",
            "AICTE Model Curriculum",
            "Choice Based Credit System (CBCS)"
        ])
    with col6:
        academic_year = st.text_input("Academic Year:", value="2025-26")
    with col7:
        semester = st.selectbox("Semester:", ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"], index=4)

    st.markdown("#### Dynamic Structure Control")
    sc1, sc2 = st.columns(2)
    with sc1:
        num_modules_val = st.slider("Number of Units / Modules in Curriculum:", min_value=4, max_value=8, value=5, help="Select standard 5 or 6 modules.")
    with sc2:
        num_cos_val = st.slider("Number of Target Course Outcomes (COs):", min_value=4, max_value=8, value=6, help="NBA recommends 5 to 6 COs per course.")

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


# TAB 2: MULTI-DOMAIN COURSE OUTCOMES
with tabs[1]:
    st.markdown("### Multi-Domain Course Outcomes (Cognitive, Psychomotor, Affective)")
    st.caption("Per SAKEC OBE Manual Section 15 & 16: Each CO statement should incorporate **Performance** (action verb), **Condition** (context/tools), and **Criteria** (accuracy/standard) across Cognitive, Psychomotor, and Affective domains.")

    DOMAIN_LEVEL_MAP = {
        "Cognitive": ["L1: Remember", "L2: Understand", "L3: Apply", "L4: Analyze", "L5: Evaluate", "L6: Create"],
        "Psychomotor (Lab / Practical)": ["P1: Imitation", "P2: Manipulation", "P3: Precision", "P4: Articulation", "P5: Naturalization"],
        "Affective (Ethics / Teamwork)": ["A1: Receiving", "A2: Responding", "A3: Valuing", "A4: Organization", "A5: Characterization"],
    }

    default_multi_cos = [
        {"domain": "Cognitive", "level": "L2: Understand", "desc": "Explain foundational architectural patterns, consensus state machines, and replication invariants.", "target": 70},
        {"domain": "Psychomotor (Lab / Practical)", "level": "P2: Manipulation", "desc": "Configure, instrument, and deploy containerized microservice clusters with runtime telemetry.", "target": 70},
        {"domain": "Cognitive", "level": "L4: Analyze", "desc": "Analyze network partitions, tail latency bottlenecks, and zero-trust perimeter contracts under load.", "target": 75},
        {"domain": "Psychomotor (Lab / Practical)", "level": "P3: Precision", "desc": "Implement fault-tolerant event streaming pipelines leveraging Kafka Streams with verified accuracy.", "target": 70},
        {"domain": "Affective (Ethics / Teamwork)", "level": "A3: Valuing", "desc": "Adhere to professional engineering ethics, open-source compliance, and collaborative team reviews.", "target": 70},
        {"domain": "Cognitive", "level": "L6: Create", "desc": "Design and synthesize an end-to-end production microservice system integrating Edge AI accelerators.", "target": 80},
        {"domain": "Psychomotor (Lab / Practical)", "level": "P4: Articulation", "desc": "Integrate heterogeneous hardware accelerators and test failover topologies in real-time.", "target": 75},
        {"domain": "Affective (Ethics / Teamwork)", "level": "A4: Organization", "desc": "Formulate ethical sustainability roadmaps and lead multidisciplinary agile project milestones.", "target": 75},
    ]

    co_inputs = []
    for idx in range(num_cos_val):
        co_id = f"CO{idx + 1}"
        default_item = default_multi_cos[idx % len(default_multi_cos)]
        
        c_id, c_dom, c_lvl, c_desc, c_tgt = st.columns([1, 2.5, 2.5, 5, 1.5])
        with c_id:
            st.markdown(f"**{co_id}**")
        with c_dom:
            domain_choice = st.selectbox(
                f"Domain ({co_id}):",
                list(DOMAIN_LEVEL_MAP.keys()),
                index=list(DOMAIN_LEVEL_MAP.keys()).index(default_item["domain"]) if default_item["domain"] in DOMAIN_LEVEL_MAP else 0,
                key=f"dom_{co_id}",
                label_visibility="collapsed"
            )
        with c_lvl:
            available_levels = DOMAIN_LEVEL_MAP[domain_choice]
            def_idx = 0
            if default_item["level"] in available_levels:
                def_idx = available_levels.index(default_item["level"])
            level_choice = st.selectbox(
                f"Level ({co_id}):",
                available_levels,
                index=def_idx,
                key=f"lvl_{co_id}",
                label_visibility="collapsed"
            )
        with c_desc:
            desc_val = st.text_input(
                f"Statement ({co_id}):",
                value=default_item["desc"],
                key=f"desc_{co_id}",
                label_visibility="collapsed"
            )
        with c_tgt:
            target_val = st.number_input(
                f"Target % ({co_id}):",
                min_value=50, max_value=100,
                value=default_item["target"],
                key=f"tgt_{co_id}",
                label_visibility="collapsed"
            )
        
        domain_clean = domain_choice.split()[0]
        co_inputs.append({
            "id": co_id,
            "domain": domain_clean,
            "bloom_level": level_choice,
            "desc": desc_val,
            "target": target_val
        })


# TAB 3: DEPARTMENT PSOs (PROGRAM SPECIFIC OUTCOMES)
with tabs[2]:
    st.markdown("### SAKEC Department Program Specific Outcomes (PSOs)")
    st.caption("Load official PSOs directly from SAKEC OBE Manual Version 3.0 (Chapters 2 & 3) or customize statements.")

    col_preset, col_load = st.columns([3, 1.5])
    with col_preset:
        selected_dept_preset = st.selectbox("Select SAKEC Department Preset:", list(SAKEC_DEPARTMENT_PSOS.keys()), index=list(SAKEC_DEPARTMENT_PSOS.keys()).index(dept) if dept in SAKEC_DEPARTMENT_PSOS else 0)
    with col_load:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Load Official SAKEC PSOs", use_container_width=True):
            st.session_state.custom_psos = [dict(x) for x in SAKEC_DEPARTMENT_PSOS[selected_dept_preset]]
            st.rerun()

    pso_items = []
    for idx, pso in enumerate(st.session_state.custom_psos):
        p1, p2, p3 = st.columns([1.5, 7, 1])
        with p1:
            pso_id_val = st.text_input(f"ID #{idx+1}:", value=pso["id"], key=f"pso_id_{idx}")
        with p2:
            pso_stmt_val = st.text_area(f"Statement for {pso_id_val}:", value=pso["statement"], key=f"pso_stmt_{idx}", height=68)
        with p3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_pso_{idx}", help="Delete PSO"):
                if len(st.session_state.custom_psos) > 1:
                    st.session_state.custom_psos.pop(idx)
                    st.rerun()
        pso_items.append({"id": pso_id_val, "statement": pso_stmt_val})

    st.session_state.custom_psos = pso_items

    if st.button("➕ Add Custom PSO"):
        next_num = len(st.session_state.custom_psos) + 1
        st.session_state.custom_psos.append({
            "id": f"PSO{next_num}",
            "statement": f"PSO{next_num}: Specialized domain competence in cutting-edge engineering systems."
        })
        st.rerun()


# TAB 4: COMPREHENSIVE ASSESSMENT SCHEME (CIA, MSE, CIAP, ESE, ESEP, SLA)
with tabs[3]:
    st.markdown("### Comprehensive Examination Scheme & Marks Weightage")
    st.caption("Configure institutional weightages across Continuous Assessment (CIA), Mid-Semester Exam (MSE), Practical Internal (CIAP), End-Semester Theory (ESE), End-Semester Practical (ESEP), and Self-Learning Assessment (SLA).")

    e1, e2, e3 = st.columns(3)
    with e1:
        cia_val = st.number_input("CIA (Continuous Internal Assessment - Theory):", min_value=0, max_value=100, value=20)
    with e2:
        mse_val = st.number_input("MSE (Mid-Semester Examination - Theory):", min_value=0, max_value=100, value=30)
    with e3:
        ciap_val = st.number_input("CIAP (Continuous Assessment - Practical / Lab):", min_value=0, max_value=100, value=25)

    e4, e5, e6 = st.columns(3)
    with e4:
        ese_val = st.number_input("ESE (End-Semester Examination - Theory):", min_value=0, max_value=150, value=50)
    with e5:
        esep_val = st.number_input("ESEP (End-Semester Exam - Practical / Oral / Viva):", min_value=0, max_value=100, value=25)
    with e6:
        sla_val = st.number_input("SLA (Self-Learning Assessment / Mini-Project):", min_value=0, max_value=100, value=20)

    calculated_total = cia_val + mse_val + ciap_val + ese_val + esep_val + sla_val
    pass_thresh = st.slider("Expected Proficiency Threshold (% Marks per SAKEC OBE Manual):", min_value=40.0, max_value=70.0, value=60.0, step=5.0)

    st.markdown(f"""
    <div style="background-color: #ebf2fa; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; margin-top: 10px;">
        <span style="font-size: 14px; font-weight: 700; color: #163669;">Calculated Total Course Marks: {calculated_total} Marks</span> &nbsp;|&nbsp;
        <span style="font-size: 12px; color: #46505f;">Theory Total: {cia_val + mse_val + ese_val} Marks &nbsp;|&nbsp; Practical/Lab Total: {ciap_val + esep_val} Marks &nbsp;|&nbsp; SLA Total: {sla_val} Marks &nbsp;|&nbsp; Expected Proficiency: {pass_thresh}%</span>
    </div>
    """, unsafe_allow_html=True)


# TAB 5: INDUSTRY INTEGRATION & RAG
with tabs[4]:
    st.markdown("### Novel Industry Integration & Reference Syllabus Ingestion (RAG)")
    st.caption("Enter trending technologies. Foundational theory is preserved in Units 1–3 while modern industry tools are infused into Units 4–6.")

    industry_topics = st.text_area(
        "Industry Frameworks & Tools (comma-separated):",
        value="Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph, Ray Distributed, OpenTelemetry, eBPF",
        height=80
    )

    st.markdown("#### Upload Reference Curriculum or SAKEC OBE Manual (PDF / DOCX / TXT)")
    uploaded_file = st.file_uploader(
        "Upload reference syllabus or accreditation manual to populate hierarchical vector store:",
        type=["pdf", "docx", "txt", "md"]
    )
    if uploaded_file is not None:
        if st.button("📥 Ingest Reference Document into Vector Index"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            try:
                text = SyllabusParser.extract_text_from_file(tmp_path)
                chunks = SyllabusParser.hierarchical_chunk(text, doc_id=uploaded_file.name)
                rag_store.add_documents(chunks)
                st.success(f"Successfully indexed {len(chunks)} hierarchical syllabus chunks from {uploaded_file.name}!")
            finally:
                os.unlink(tmp_path)


# TAB 6: ARTICULATION MATRIX
with tabs[5]:
    st.markdown("### Course Articulation Matrix (CO–PO & CO–PSO Mapping)")
    st.caption("Per SAKEC OBE Manual Section 17 & 18: Correlation Levels: 3 = High Correlation, 2 = Medium Correlation, 1 = Low Correlation, - = No Correlation.")

    matrix_data = []
    for idx, co in enumerate(co_inputs):
        co_num = idx + 1
        row = {"CO ID": co["id"], "Domain": co["domain"]}
        for po_idx in range(1, 13):
            val = "-"
            if po_idx == 1: val = "3"
            elif po_idx == 2 and co_num >= 2: val = "3" if co_num >= 3 else "2"
            elif po_idx == 3 and co_num >= 3: val = "3" if co_num >= 4 else "2"
            elif po_idx == 4 and (co["domain"] == "Psychomotor" or co_num in [3, 4]): val = "3"
            elif po_idx == 5 and (co_num >= 3 or co["domain"] == "Psychomotor"): val = "3"
            elif po_idx == 8 and co["domain"] == "Affective": val = "3"
            elif po_idx in [9, 10] and (co["domain"] == "Affective" or co_num == num_cos_val): val = "2"
            elif po_idx == 12: val = "2"
            row[f"PO{po_idx}"] = val
        for pso_item in st.session_state.custom_psos:
            row[pso_item["id"]] = "3" if co_num >= 3 else "2"
        matrix_data.append(row)

    st.dataframe(matrix_data, hide_index=True)


# Helper to synthesize or sync current UI inputs (Tabs 1-6) into CurriculumCreate & LaTeX
def _synthesize_and_render_latex(use_custom_template: bool = False):
    psos_objects = [ProgramSpecificOutcome(pso_id=p["id"], statement=p["statement"]) for p in st.session_state.custom_psos]
    meta_obj = CourseMeta(
        course_name=course_name,
        course_code=course_code,
        academic_year=academic_year,
        semester=semester,
        department=dept,
        scheme=scheme,
        course_type=course_type,
        credits_l=credits_l,
        credits_t=credits_t,
        credits_p=credits_p,
        credits_c=credits_c,
        total_contact_hours=total_hours,
        theory_hours=theory_hours,
        lab_hours=lab_hours,
        self_study_hours=self_study,
        psos=psos_objects,
    )

    gen_req = GenerationRequest(
        course_meta=meta_obj,
        industry_topics=industry_topics,
        num_modules=num_modules_val,
        num_cos=num_cos_val,
        model_provider=provider_code,
        model_name=model_name or None,
        api_key=api_key or None,
        ollama_url=ollama_url or None,
        temperature=temperature,
    )
    generator = CurriculumGenerator(gen_req)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    curr = loop.run_until_complete(generator.generate_curriculum())
    loop.close()

    # Always preserve the faculty's exact edited Multi-Domain COs from Tab 2
    if co_inputs:
        curr.course_outcomes = [
            CourseOutcome(
                co_id=c["id"],
                domain=c["domain"],
                bloom_level=c["bloom_level"],
                description=c["desc"],
                target_attainment_pct=c["target"],
            )
            for c in co_inputs
        ]

    # Always preserve the faculty's exact 6-component Assessment Scheme from Tab 4
    curr.assessment_scheme = AssessmentScheme(
        cia_marks=cia_val,
        mse_marks=mse_val,
        ciap_marks=ciap_val,
        ese_marks=ese_val,
        esep_marks=esep_val,
        sla_marks=sla_val,
        total_marks=calculated_total,
        passing_threshold_pct=pass_thresh,
    )

    compiler = LatexCompiler()
    if use_custom_template and st.session_state.get("custom_uploaded_tex"):
        tex = compiler.render_with_custom_template(curr, st.session_state.custom_uploaded_tex)
    else:
        tex = compiler.render_template(curr)

    st.session_state.curriculum = curr
    st.session_state.tex_source = tex
    st.session_state.tex_editor_version += 1
    st.session_state.curriculum_status = "DRAFT"
    return curr, tex


# TAB 7: CURRICULUM GENERATION & MODULES
with tabs[6]:
    st.markdown("### AI Generation & Mathematical Hour Balancing")
    st.caption(f"Synthesize {num_modules_val} modules mathematically balanced to sum to exactly {total_hours} contact hours.")

    col_btn, col_info = st.columns([2, 4])
    with col_btn:
        generate_clicked = st.button("✨ Synthesize Curriculum", type="primary")

    if generate_clicked:
        with st.spinner(f"Querying {model_name} on {server_mode} and updating LaTeX template..."):
            use_custom = bool(st.session_state.get("custom_uploaded_tex"))
            curr, tex = _synthesize_and_render_latex(use_custom_template=use_custom)
            st.success(f"Generated {num_modules_val} modules and {num_cos_val} multi-domain outcomes, and updated the LaTeX template in Tab 8!")

    if st.session_state.curriculum:
        st.markdown("---")
        curr = st.session_state.curriculum
        st.markdown(f"#### Generated Modules (Hours Sum: {sum(m.contact_hours for m in curr.modules)} / {curr.course_meta.total_contact_hours})")
        for mod in curr.modules:
            with st.expander(f"Module {mod.module_number}: {mod.title} ({mod.contact_hours} Hours - {mod.weightage_pct}%)", expanded=(mod.module_number == 1)):
                st.markdown(f"**Cognitive Level:** `{mod.cognitive_level}`")
                if mod.industry_integration_tags:
                    st.markdown(f"**Industry Integration:** `{', '.join(mod.industry_integration_tags)}`")
                st.markdown("**Detailed Topics:**")
                for t in mod.topics:
                    st.markdown(f"- {t}")


# TAB 8: CUSTOM LATEX TEMPLATE UPLOAD & COMPILER
with tabs[7]:
    from backend.app.latex.compiler import fix_latex_option_clashes
    import hashlib

    st.markdown("### Reference LaTeX Template Upload & pdflatex Compiler")
    st.caption("Upload your institutional `.tex` reference template or use the standard SAKEC NBA/AICTE template. Your created curriculum is automatically injected into the LaTeX source below.")

    template_mode = st.radio(
        "Template Choice:",
        ["Standard Publication-Grade NBA/AICTE Template", "Upload Custom Institutional .tex Template"],
        index=0,
    )

    if template_mode == "Upload Custom Institutional .tex Template":
        custom_tex_file = st.file_uploader("Upload Institutional Reference Template (.tex):", type=["tex"])
        if custom_tex_file is not None:
            raw_bytes = custom_tex_file.getvalue()
            file_hash = hashlib.md5(raw_bytes).hexdigest()
            raw_uploaded_tex = raw_bytes.decode("utf-8", errors="ignore")
            st.session_state.custom_uploaded_tex = raw_uploaded_tex

            # Automatically populate the uploaded .tex template with the created curriculum when uploaded!
            if file_hash != st.session_state.get("last_uploaded_tex_hash"):
                st.session_state.last_uploaded_tex_hash = file_hash
                if st.session_state.curriculum is None:
                    _synthesize_and_render_latex(use_custom_template=True)
                else:
                    compiler_tmp = LatexCompiler()
                    st.session_state.tex_source = compiler_tmp.render_with_custom_template(
                        st.session_state.curriculum, raw_uploaded_tex
                    )
                    st.session_state.tex_editor_version += 1
                st.success("✅ Uploaded reference LaTeX template automatically populated with your created curriculum!")

    # Auto-populate initial curriculum LaTeX if tex_source is still empty
    if not st.session_state.tex_source.strip():
        _synthesize_and_render_latex(
            use_custom_template=(template_mode == "Upload Custom Institutional .tex Template" and bool(st.session_state.get("custom_uploaded_tex")))
        )

    sync_col1, sync_col2 = st.columns([2.2, 2.8])
    with sync_col1:
        if st.button("🔄 Sync / Update Created Curriculum into LaTeX Template", use_container_width=True):
            use_custom = (template_mode == "Upload Custom Institutional .tex Template" and bool(st.session_state.get("custom_uploaded_tex")))
            _synthesize_and_render_latex(use_custom_template=use_custom)
            st.success("✅ LaTeX template updated with all latest Course Metadata, Multi-Domain COs, PSOs, Modules, and Assessment Marks!")
            st.rerun()
    with sync_col2:
        if template_mode == "Upload Custom Institutional .tex Template" and st.session_state.get("custom_uploaded_tex"):
            if st.button("📄 View Raw Unmodified Uploaded .tex File", use_container_width=True):
                st.session_state.tex_source = fix_latex_option_clashes(st.session_state.custom_uploaded_tex)
                st.session_state.tex_editor_version += 1
                st.rerun()

    editor_key = f"latex_editor_v{st.session_state.tex_editor_version}"
    tex_input = st.text_area(
        "LaTeX Source Code (.tex):",
        value=st.session_state.tex_source,
        height=450,
        key=editor_key,
    )
    st.session_state.tex_source = tex_input

    if st.button("🔨 Compile LaTeX to PDF (2-Pass)", type="primary"):
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


# TAB 9: PDF PREVIEW & REVIEW WORKFLOW
with tabs[8]:
    st.markdown("### Accreditation Review & Deliverables Export")
    st.caption("Download the compiled PDF, LaTeX source, or complete ZIP package, and perform HOD sign-off.")

    res = st.session_state.compilation_result

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
                mime="application/pdf"
            )
        with d2:
            st.download_button(
                "📄 Download LaTeX Source (.tex)",
                data=st.session_state.tex_source,
                file_name=f"{course_code}_Curriculum.tex",
                mime="text/x-tex"
            )
        with d3:
            if zip_bytes:
                st.download_button(
                    "📦 Download Full ZIP Bundle",
                    data=zip_bytes,
                    file_name=f"{course_code}_Curriculum_Bundle.zip",
                    mime="application/zip"
                )

        st.markdown("---")
        st.markdown("#### Institutional Review & Sign-Off Workflow")
        if "HOD" in effective_roles:
            r_col1, r_col2 = st.columns([1, 2])
            with r_col1:
                decision = st.selectbox("Accreditation Decision:", ["APPROVED", "CHANGES_REQUESTED", "REJECTED"])
            with r_col2:
                review_notes = st.text_input("Reviewer Comments:", value="Approved for Board of Studies. Multi-domain COs and assessment scheme comply with SAKEC OBE Manual V3.0.")
            if st.button("Submit Official Review"):
                st.session_state.curriculum_status = decision
                st.success(f"Curriculum status updated to: {decision}")
        else:
            st.info("Log in as HOD or Administrator in the sidebar to review and approve this curriculum.")

        st.markdown("---")
        st.markdown("#### Document Preview:")
        base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.info("No compiled PDF available yet. Synthesize curriculum in Tab 7 and click 'Compile to PDF' in Tab 8.")


# TAB 10: DEDICATED OBE ASSESSMENT PLAN & MICROSOFT TEAMS RUBRICS GENERATOR
with tabs[9]:
    st.markdown("### 📋 SAKEC OBE Assessment Methodology & Microsoft Teams Rubric Exporter (`.csv`)")
    st.caption("Aligned with **SAKEC Outcome-Based Education Manual Version 3.0 (Annexure B, Sections 25.1 to 25.8)**. Select official rubrics or customize criteria, generate the full LaTeX/PDF Course File Assessment Dossier, and export ready-to-upload **Microsoft Teams `.csv` Rubric files** (`v.11p` schema).")

    # SECTION A: MICROSOFT TEAMS RUBRIC BUILDER & CSV EXPORTER
    st.markdown("#### A. Microsoft Teams Rubric Builder & 1-Click `.csv` Exporter")
    
    r_col1, r_col2, r_col3 = st.columns([2.5, 2, 1.5])
    with r_col1:
        selected_rubric_template = st.selectbox(
            "Select Official SAKEC OBE Manual Rubric Preset (Annexure B):",
            list(SAKEC_OBE_RUBRICS_CATALOG.keys()),
            index=10  # Default to 25.8 Reel / Blog / Skit
        )
    with r_col2:
        teams_rubric_title = st.text_input(
            "Microsoft Teams Rubric Title:",
            value=f"{course_code} CIAP Reels & Technical Explainer"
        )
    with r_col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Load SAKEC Rubric Preset"):
            st.session_state.editable_rubric = [
                dict(x) for x in SAKEC_OBE_RUBRICS_CATALOG[selected_rubric_template]
            ]
            st.rerun()

    st.markdown("##### Customize Rubric Criteria, Descriptors (4 to 1), and Percentage Weights:")
    updated_rubric_rows = []
    total_weight_sum = 0

    for r_idx, r_item in enumerate(st.session_state.editable_rubric):
        with st.expander(f"Criterion {r_idx + 1}: {r_item['criterion']} (Weight: {r_item['weight']}%)", expanded=(r_idx == 0)):
            rc1, rc2, rc3 = st.columns([4, 1.5, 0.8])
            with rc1:
                crit_name = st.text_input("Evaluating Parameter / Criterion:", value=r_item["criterion"], key=f"r_crit_{r_idx}")
            with rc2:
                crit_weight = st.number_input("Weight (%):", min_value=5, max_value=100, value=int(r_item["weight"]), step=5, key=f"r_w_{r_idx}")
            with rc3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_r_{r_idx}", help="Delete criterion"):
                    if len(st.session_state.editable_rubric) > 1:
                        st.session_state.editable_rubric.pop(r_idx)
                        st.rerun()

            rl4, rl3, rl2, rl1 = st.columns(4)
            with rl4:
                desc_4 = st.text_area("Level 4 - Exemplary / Excellent:", value=r_item["level_4"], key=f"r_l4_{r_idx}", height=90)
            with rl3:
                desc_3 = st.text_area("Level 3 - Proficient / Good:", value=r_item["level_3"], key=f"r_l3_{r_idx}", height=90)
            with rl2:
                desc_2 = st.text_area("Level 2 - Developing / Satisfactory:", value=r_item["level_2"], key=f"r_l2_{r_idx}", height=90)
            with rl1:
                desc_1 = st.text_area("Level 1 - Beginning / Needs Improvement:", value=r_item["level_1"], key=f"r_l1_{r_idx}", height=90)

            updated_rubric_rows.append({
                "criterion": crit_name,
                "weight": crit_weight,
                "level_4": desc_4,
                "level_3": desc_3,
                "level_2": desc_2,
                "level_1": desc_1,
            })
            total_weight_sum += crit_weight

    st.session_state.editable_rubric = updated_rubric_rows

    b_add, b_weight_status, b_dl = st.columns([1.5, 2.5, 2.5])
    with b_add:
        if st.button("➕ Add Custom Criterion"):
            st.session_state.editable_rubric.append({
                "criterion": "New Evaluation Criterion",
                "weight": 10,
                "level_4": "Demonstrates exemplary mastery and complete accuracy.",
                "level_3": "Demonstrates good understanding with minor omissions.",
                "level_2": "Demonstrates basic understanding with limited clarity.",
                "level_1": "Demonstrates minimal understanding or incomplete work.",
            })
            st.rerun()

    with b_weight_status:
        if total_weight_sum == 100:
            st.success(f"✅ Total Rubric Weight: {total_weight_sum}% (Valid for MS Teams)")
        else:
            st.warning(f"⚠️ Total Weight is {total_weight_sum}% (Should sum to 100% for MS Teams)")

    # Generate the exact Microsoft Teams CSV
    ms_teams_csv_content = generate_ms_teams_rubric_csv(
        title=teams_rubric_title,
        criteria_list=st.session_state.editable_rubric,
        total_points=100
    )

    with b_dl:
        safe_csv_filename = re.sub(r"[^a-zA-Z0-9_\-]", "_", teams_rubric_title) + "_MS_Teams_Rubric.csv"
        st.download_button(
            "📥 Download Microsoft Teams Rubric (.csv)",
            data=ms_teams_csv_content,
            file_name=safe_csv_filename,
            mime="text/csv",
            type="primary"
        )

    with st.expander("🔍 Preview Raw Microsoft Teams `.csv` Format (v.11p Schema)", expanded=False):
        st.code(ms_teams_csv_content, language="csv")

    st.markdown("---")

    # SECTION B: FULL COURSE ASSESSMENT DOSSIER GENERATOR (PDF & LaTeX)
    st.markdown("#### B. Complete Course Assessment Methodology Dossier Generator (CIA, MSE, CIAP, ESE, ESEP, SLA)")
    st.caption("Select assessment methodologies across all 6 evaluation components and synthesize the complete 4-page NBA/SAKEC Course File Assessment Dossier.")

    m_col1, m_col2 = st.columns(2)
    with m_col1:
        sel_cia = st.multiselect(
            "CIA Activities (Continuous Internal Assessment - Theory):",
            OBE_ASSESSMENT_CATALOG["CIA"],
            default=["Reel / Blog / Skit Activity (SAKEC Rubric 25.8)", "Case Study Activity (SAKEC Rubric 25.3)"]
        )
        sel_mse = st.multiselect(
            "MSE Methodologies (Mid-Semester Exam):",
            OBE_ASSESSMENT_CATALOG["MSE"],
            default=["Mid-Semester Examination (MSE) Mapped to COs", "Higher-Order Thinking Questions (HOTS - L3 to L5)"]
        )
        sel_ciap = st.multiselect(
            "CIAP Lab Evaluation (Continuous Practical):",
            OBE_ASSESSMENT_CATALOG["CIAP"],
            default=["Computer-Allied Lab Experiment (SAKEC Rubric 25.1.1)", "PARIKSHAK - Test-Case-Based Program Evaluation (SAKEC Rubric 25.1.3)"]
        )

    with m_col2:
        sel_ese = st.multiselect(
            "ESE Theory Blueprint (End-Semester Exam):",
            OBE_ASSESSMENT_CATALOG["ESE"],
            default=["Comprehensive End-Semester Theory Exam (SAKEC 60% University Weightage)", "Bloom's Cognitive Distribution Blueprint (L1 to L6)"]
        )
        sel_esep = st.multiselect(
            "ESEP Practical / Oral Exam:",
            OBE_ASSESSMENT_CATALOG["ESEP"],
            default=["Practical / Oral End-Semester Examination", "Hands-On System Deployment & Runtime Demonstration"]
        )
        sel_sla = st.multiselect(
            "SLA Self-Learning Activities:",
            OBE_ASSESSMENT_CATALOG["SLA"],
            default=["Semester Long Self-Learning Activity - Individual (SAKEC Rubric 25.2.1)", "Semester Long Self-Learning Activity - Group (SAKEC Rubric 25.2.2)"]
        )

    faculty_prompt = st.text_area(
        "Faculty Specific Conduction & Scenario Prompt:",
        value=(
            "For CIA 1, students must create a 60-second technical reel/video explaining distributed state or simulation logic evaluated via SAKEC Rubric 25.8. "
            "For CIA 2, conduct an engineering case study evaluated via SAKEC Rubric 25.3. "
            "For CIAP, evaluate weekly computer-allied lab experiments (25.1.1) and automated test-case pass percentage via PARIKSHAK (25.1.3). "
            "For SLA, conduct progressive 3-phase evaluations across the semester per SAKEC Section 25.2."
        ),
        height=95
    )

    if st.button("🚀 Generate Full SAKEC OBE Assessment Dossier (PDF & LaTeX)", type="primary"):
        with st.spinner(f"Synthesizing complete SAKEC OBE Assessment Dossier using {model_name} on {server_mode}..."):
            psos_objects = [ProgramSpecificOutcome(pso_id=p["id"], statement=p["statement"]) for p in st.session_state.custom_psos]
            meta_obj = CourseMeta(
                course_name=course_name,
                course_code=course_code,
                academic_year=academic_year,
                semester=semester,
                department=dept,
                scheme=scheme,
                course_type=course_type,
                credits_l=credits_l,
                credits_t=credits_t,
                credits_p=credits_p,
                credits_c=credits_c,
                total_contact_hours=total_hours,
                theory_hours=theory_hours,
                lab_hours=lab_hours,
                self_study_hours=self_study,
                psos=psos_objects
            )
            cos_objects = [CourseOutcome(co_id=c["id"], domain=c["domain"], bloom_level=c["bloom_level"], description=c["desc"], target_attainment_pct=c["target"]) for c in co_inputs]
            scheme_obj = AssessmentScheme(
                cia_marks=cia_val, mse_marks=mse_val, ciap_marks=ciap_val, ese_marks=ese_val, esep_marks=esep_val, sla_marks=sla_val, total_marks=calculated_total
            )

            assess_req = AssessmentPlanRequest(
                course_meta=meta_obj,
                course_outcomes=cos_objects,
                assessment_scheme=scheme_obj,
                cia_methods=sel_cia,
                mse_methods=sel_mse,
                ciap_methods=sel_ciap,
                ese_methods=sel_ese,
                esep_methods=sel_esep,
                sla_methods=sel_sla,
                faculty_prompt=faculty_prompt,
                model_provider=provider_code,
                model_name=model_name or None,
                api_key=api_key or None,
                ollama_url=ollama_url or None,
                temperature=temperature
            )
            plan_gen = AssessmentPlanGenerator(assess_req)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            plan = loop.run_until_complete(plan_gen.generate_assessment_plan())
            loop.close()

            compiler = AssessmentPlanCompiler()
            tex = compiler.render_template(plan, meta_obj)

            st.session_state.assessment_plan = plan
            st.session_state.assessment_tex_source = tex

            res = compiler.compile(tex, output_prefix=f"{course_code}_SAKEC_Assessment_Dossier")
            st.session_state.assessment_compilation_result = res

            if res.success:
                st.success(f"SAKEC Assessment Plan & Rubrics Dossier compiled into PDF ({os.path.basename(res.pdf_path)}, {os.path.getsize(res.pdf_path)} bytes)!")
            else:
                st.warning("Assessment plan generated. Inspect LaTeX source below.")

    if st.session_state.assessment_plan:
        plan = st.session_state.assessment_plan
        res = st.session_state.assessment_compilation_result

        st.markdown("---")
        st.markdown(f"#### Generated Assessment Components for {plan.course_code} (Total Marks: {plan.total_marks})")

        if res and res.success and res.pdf_path and os.path.exists(res.pdf_path):
            with open(res.pdf_path, "rb") as f:
                pdf_data = f.read()
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.download_button(
                    "📥 Download Assessment Dossier PDF",
                    data=pdf_data,
                    file_name=f"{plan.course_code}_SAKEC_Assessment_Dossier.pdf",
                    mime="application/pdf"
                )
            with d_col2:
                st.download_button(
                    "📄 Download Assessment LaTeX Source (.tex)",
                    data=st.session_state.assessment_tex_source,
                    file_name=f"{plan.course_code}_SAKEC_Assessment_Dossier.tex",
                    mime="text/x-tex"
                )

        for comp in plan.components:
            with st.expander(f"{comp.component_code}: {comp.component_name} ({comp.allocated_marks} Marks - Target COs: {', '.join(comp.target_cos)})", expanded=(comp.component_code == "CIA")):
                st.markdown(f"**Selected Methods:** `{', '.join(comp.selected_methods)}`")
                st.markdown(f"**Bloom Focus:** `{comp.bloom_focus}`")
                st.markdown(f"**Activity Description:**\n{comp.activity_description}")
                st.markdown(f"**Faculty Guidelines:**\n{comp.faculty_guidelines}")
                st.markdown(f"**Student Deliverables:**\n{comp.student_deliverables}")
                
                if comp.rubric_criteria:
                    st.markdown("**SAKEC Annexure B 4-Level Performance Analytic Rubric:**")
                    rub_table = []
                    for r in comp.rubric_criteria:
                        rub_table.append({
                            "Evaluating Parameter": r.get("criterion", "Criterion"),
                            "Level 4 - Exemplary": r.get("exemplary_4", ""),
                            "Level 3 - Proficient": r.get("proficient_3", ""),
                            "Level 2 - Developing": r.get("developing_2", ""),
                            "Level 1 - Beginning": r.get("novice_1", "")
                        })
                    st.dataframe(rub_table, hide_index=True)

                    # Individual component MS Teams CSV download button
                    comp_csv = generate_ms_teams_rubric_csv(
                        title=f"{plan.course_code} - {comp.component_code} Rubric",
                        criteria_list=[
                            {
                                "criterion": re.sub(r"\s*\(\d+%\)$", "", r.get("criterion", "Criterion")),
                                "weight": r.get("weight", 20),
                                "level_4": r.get("exemplary_4", ""),
                                "level_3": r.get("proficient_3", ""),
                                "level_2": r.get("developing_2", ""),
                                "level_1": r.get("novice_1", ""),
                            }
                            for r in comp.rubric_criteria
                        ],
                        total_points=100
                    )
                    st.download_button(
                        f"📥 Download {comp.component_code} Rubric for Microsoft Teams (.csv)",
                        data=comp_csv,
                        file_name=f"{plan.course_code}_{comp.component_code}_MS_Teams_Rubric.csv",
                        mime="text/csv",
                        key=f"dl_teams_{comp.component_code}"
                    )

        st.markdown("#### SAKEC OBE Manual Version 3.0 Attainment Formulation")
        st.info(plan.attainment_methodology)

        if res and res.success and res.pdf_path and os.path.exists(res.pdf_path):
            st.markdown("#### Assessment Dossier Document Preview:")
            with open(res.pdf_path, "rb") as f:
                base64_assess_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_embed = f'<iframe src="data:application/pdf;base64,{base64_assess_pdf}" width="100%" height="700" type="application/pdf"></iframe>'
            st.markdown(pdf_embed, unsafe_allow_html=True)


# TAB 11: HOD DEPARTMENT GOVERNANCE & BOARD OF STUDIES (BoS) APPROVAL CONSOLE
if "HOD" in effective_roles and len(tabs) >= 11:
    with tabs[10]:
        st.markdown("### 🏛️ Head of Department (HOD) Governance & Board of Studies (BoS) Approval Console")
        st.caption(
            f"Logged in as **{current_user.get('name')}** (`{role}`). "
            "HODs inherit full **Faculty** curriculum and assessment authoring rights (Tabs 1–10) plus departmental Board of Studies audit, PSO management, and curriculum approval."
        )

        h_col1, h_col2, h_col3 = st.columns(3)
        with h_col1:
            st.metric("Active Course Under Review", f"{course_code} ({dept})")
        with h_col2:
            st.metric("Department BoS Status", st.session_state.curriculum_status)
        with h_col3:
            st.metric("SAKEC Proficiency Threshold", "60% Marks (Target 1.80)")

        st.markdown("#### 1. Board of Studies (BoS) Curriculum & OBE Assessment Sign-Off")
        rev_c1, rev_c2 = st.columns([1.2, 2.5])
        with rev_c1:
            hod_decision = st.selectbox(
                "HOD / BoS Accreditation Decision:",
                ["APPROVED", "UNDER_REVIEW", "CHANGES_REQUESTED", "REJECTED"],
                index=0,
                key="hod_tab_decision"
            )
        with rev_c2:
            hod_remarks = st.text_input(
                "HOD BoS Audit Remarks:",
                value="Verified multi-domain COs (Cognitive, Psychomotor, Affective), SAKEC OBE Manual V3.0 Annexure B rubrics, and 6-component assessment weightages.",
                key="hod_tab_remarks"
            )
        if st.button("✅ Record Official HOD & Board of Studies Sign-Off", type="primary"):
            st.session_state.curriculum_status = hod_decision
            st.success(f"HOD Sign-Off recorded by {current_user.get('name')}: Status = `{hod_decision}`")

        st.markdown("---")
        st.markdown("#### 2. Departmental CO-PO & PSO Attainment Readiness Checklist (NBA SAR Criteria 3)")
        st.table([
            {"NBA / SAKEC Audit Parameter": "Multi-Domain CO Mapping (Cognitive + Psychomotor + Affective)", "Requirement": "4 to 8 COs mapped to L1–L6, P1–P5, A1–A5", "Status": "✅ Verified"},
            {"NBA / SAKEC Audit Parameter": "6-Component Examination Scheme (CIA, MSE, CIAP, ESE, ESEP, SLA)", "Requirement": f"Total = {calculated_total} Marks (40% Passing)", "Status": "✅ Verified"},
            {"NBA / SAKEC Audit Parameter": "SAKEC Annexure B 4-Level Analytic Rubrics & MS Teams CSV", "Requirement": "Weights sum to 100% (v.11p schema)", "Status": "✅ Verified"},
            {"NBA / SAKEC Audit Parameter": "Direct (80%) + Indirect (20%) CO Attainment Formula", "Requirement": "60% Expected Proficiency | y = 0.2X - 11", "Status": "✅ Verified"},
        ])


# TAB 12: PRINCIPAL & ADMIN INSTITUTIONAL GOVERNANCE CONSOLE
if ("Principal" in effective_roles or "Admin" in effective_roles) and len(tabs) >= 12:
    with tabs[11]:
        st.markdown("### 🎓 Principal & Institutional Executive Governance Console (SAKEC — DTE Code: 3148)")
        st.caption(
            f"Logged in as **{current_user.get('name')}** (`{role}`). "
            "**Principal** (`Dr. Bhavesh Patel`) and **Admin** inherit **ALL Faculty Access (Tabs 1–10)** + **ALL HOD Access (Tab 11)** + **Institute-Wide Governance across all 8 SAKEC Engineering Departments**."
        )

        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        with p_col1:
            st.metric("Autonomous Status", "UGC 10-Yr (2024–2034)")
        with p_col2:
            st.metric("NAAC Accreditation", "Grade 'A' (3.16 CGPA)")
        with p_col3:
            st.metric("NBA Accredited UG Depts", "Comp, IT, EXTC")
        with p_col4:
            st.metric("Academic Council Seal", st.session_state.principal_seal)

        st.markdown("#### 1. Principal & Academic Council Final Institutional Approval Seal")
        pc1, pc2 = st.columns([1.4, 2.6])
        with pc1:
            principal_decision = st.selectbox(
                "Academic Council Final Seal:",
                [
                    "APPROVED_BY_PRINCIPAL_AND_ACADEMIC_COUNCIL",
                    "CONDITIONAL_APPROVAL_PENDING_MINOR_EDITS",
                    "RETURNED_TO_DEPARTMENT_BOS",
                ],
                index=0,
            )
        with pc2:
            principal_note = st.text_input(
                "Principal's Executive Endorsement Note:",
                value="Approved under SAKEC Autonomous Curriculum Regulations (NEP 2020 / AICTE & SAKEC OBE Manual Version 3.0) by Dr. Bhavesh Patel, Principal, SAKEC.",
            )
        if st.button("🏅 Apply Principal & Academic Council Final Institutional Seal", type="primary"):
            st.session_state.principal_seal = principal_decision
            st.session_state.curriculum_status = "APPROVED"
            st.success(f"Final Institutional Seal applied: `{principal_decision}` — Endorsed by {current_user.get('name')}.")

        st.markdown("---")
        st.markdown("#### 2. SAKEC Institute-Wide Departments, DTE Codes & Intake Matrix (`https://www.sakec.ac.in/`)")
        st.dataframe(SAKEC_INSTITUTE_INFO["dte_course_codes"], hide_index=True, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 3. Institutional Role & User Access Directory (Admin & Principal Control)")
        user_rows = [
            {
                "Email": u["email"],
                "Full Name": u["name"],
                "Role": u["role"],
                "Inherited Access": ", ".join(ROLE_PERMISSIONS.get(u["role"], {"inherited_roles": ["Faculty"]})["inherited_roles"]),
                "Department": u["department"],
                "Designation": u["designation"],
            }
            for u in st.session_state.user_directory.values()
        ]
        st.dataframe(user_rows, hide_index=True, use_container_width=True)


# Render Official SAKEC Footer & Developer Attribution ("Developed by Dr. Rohan Borgalli")
render_sakec_footer()