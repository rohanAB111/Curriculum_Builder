# CurriculumAI Studio

> **Production-Grade, Deployable Web Application for Engineering Faculty to Generate NBA/AICTE-Compliant, Industry-Ready Course Curricula Formatted Strictly in Standard LaTeX Templates.**

---

## 1. Architectural Overview

```
                                      ┌─────────────────────────────────────────────────────────┐
                                      │              CurriculumAI Studio Frontend               │
                                      │    Next.js 14 (App Router) + Tailwind + shadcn/ui       │
                                      └────────────────────────────┬────────────────────────────┘
                                                                   │ REST / JWT Auth
                                                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Backend Application                                 │
│                                                                                               │
│  ┌──────────────────────┐   ┌───────────────────────────────┐   ┌──────────────────────────┐  │
│  │   Auth & RBAC Core   │   │     Advanced RAG Pipeline     │   │ Multi-Model Inference    │  │
│  │   - PBKDF2 Password  │   │     - Hierarchical Chunking   │   │ - Ollama Local (Qwen2.5) │  │
│  │   - JWT Bearer Token │   │     - BM25 + Cosine Semantic  │   │ - OpenAI / Gemini        │  │
│  │   - Admin / HOD / Fac│   │     - Cross-Encoder Re-rank   │   │ - Anthropic / Groq       │  │
│  └──────────────────────┘   └───────────────────────────────┘   └──────────────────────────┘  │
│                                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                              LaTeX Jinja2 Engine & Subprocess                           │  │
│  │                              - Strict Sanitizer (% _ & # \ { })                         │  │
│  │                              - Automated 2-Pass Compilation (pdflatex / latexmk)        │  │
│  │                              - PDF & ZIP Packager                                       │  │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────────────────────────────┬────────────────────────┘
                            │                                          │
                            ▼                                          ▼
             ┌─────────────────────────────┐            ┌─────────────────────────────┐
             │    PostgreSQL + pgvector    │            │     TeXLive-Full Worker     │
             │     Relational & Vectors    │            │   Subprocess Compilation    │
             └─────────────────────────────┘            └─────────────────────────────┘
```

---

## 2. Accreditation & Pedagogical Compliance

CurriculumAI Studio is engineered from the ground up to satisfy the stringent requirements of the **National Board of Accreditation (NBA)** and the **All India Council for Technical Education (AICTE) Model Curriculum / NEP 2020**:

| Accreditation Layer | Institutional Specification | Application Enforcement |
|---|---|---|
| **Course Outcomes (COs)** | 6 measurable statements per course mapped to cognitive domains | Formulates CO1 to CO6 strictly paired with Revised Bloom's Taxonomy cognitive verbs (L1: Remember to L6: Create). |
| **Graduate Attributes (POs)** | 12 NBA Program Outcomes (PO1 to PO12) + 3 PSOs | Automatically generates justifiable correlation weights (`3`: Substantial, `2`: Moderate, `1`: Slight, `-`: No correlation) with attainment averages. |
| **Contact Hour Balance** | Theory, Lab, Tutorial, Self-Study breakdown | Enforces mathematical hour distribution so module hours strictly equal `Total Contact Hours`. |
| **Industry 4.0 Integration** | Mandate for cutting-edge technologies in modern computing | Theory established in Modules 1–3; trending tools (Edge AI, vLLM, TensorRT-LLM, Kafka Streams, TinyML, LangGraph) injected in Modules 4–6. |
| **Academic Citations** | Standard IEEE textbook and reference formatting | Enforces publication-grade IEEE format with authors, titles, editions, publishers, years, and ISBNs. |

---

## 3. Directory Layout

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & middleware
│   │   ├── core/
│   │   │   ├── config.py               # Settings, environment variables, API keys
│   │   │   ├── security.py             # PBKDF2 hashing, JWT signing, RBAC checkers
│   │   │   └── database.py             # SQLAlchemy session & SQLite standalone fallback
│   │   ├── models/                     # SQLAlchemy schemas (User, Role, Department, Curriculum)
│   │   ├── schemas/                    # Pydantic v2 validation models
│   │   ├── rag/
│   │   │   ├── engine.py               # Hierarchical chunker, BM25 + dense RAG store
│   │   │   └── generator.py            # Multi-model LLM inference & balancing logic
│   │   ├── latex/
│   │   │   ├── sanitizer.py            # Strict LaTeX reserved character escaping
│   │   │   └── compiler.py             # Jinja2 renderer, two-pass pdflatex compiler, ZIP packager
│   │   ├── templates/
│   │   │   └── curriculum_nba_aicte.tex.j2 # Publication-grade LaTeX Jinja2 template
│   │   └── api/v1/                     # Auth, Curriculum, RAG, Templates, Admin routers
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                        # Next.js 14 App Router layout & page
│   │   └── components/                 # CourseMeta, Bloom COs, Articulation Matrix, Editor
│   ├── public/index.html               # Responsive standalone web UI
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml                  # Multi-container orchestration (FastAPI + Next.js + DB + TeXLive)
├── storage/                            # Exported PDFs, ZIP bundles, and uploaded syllabus docs
└── tests/
    └── test_compile.py                 # End-to-end curriculum generation & compilation verification
```

---

## 4. Multi-Model Inference Engine

CurriculumAI Studio supports dynamic switching between local offline execution and cloud providers:

- **Local Ollama**: Connects to `http://localhost:11434` supporting `qwen2.5:32b`, `deepseek-r1:14b`, `llama3.1:8b`, and `mistral-nemo`.
- **Cloud Providers**: Native support for **OpenAI** (`gpt-4o`, `o3-mini`), **Anthropic** (`claude-3-5-sonnet`), **Google Gemini** (`gemini-2.5-pro`, `gemini-1.5-flash`), and **Groq** (`llama-3.3-70b-versatile`).
- **Dynamic Credential Manager**: Faculty and Admins can supply session API keys through the frontend UI drawer without restarting services.
- **Offline Deterministic Fallback**: Built-in pedagogical synthesizer guarantees valid, compile-ready curricula even when disconnected from external networks.

---

## 5. Deployment Guide

### Option A: Quickstart with Docker Compose

Launch the full stack (FastAPI Backend, Next.js Frontend, PostgreSQL with pgvector, and TeXLive-full):

```bash
docker-compose up --build -d
```

- **Frontend Application**: `http://localhost:3000`
- **Backend API & Swagger Docs**: `http://localhost:8000/api/v1/docs`
- **Alternative Standalone UI**: `http://localhost:8000/`

### Option B: Local Standalone Execution (Zero External Dependencies)

Run directly using Python 3 and system `pdflatex`:

```bash
# 1. Verify compilation and generate sample NBA document
python3 tests/test_compile.py

# 2. Launch FastAPI Server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Seed Accounts for Role-Based Access Control (RBAC)

The application initializes with standard pre-configured role accounts:

| Role | Email | Default Password | Permissions |
|---|---|---|---|
| **Administrator** | `admin@curriculumai.edu` | `Admin@123` | System config, user management, departments, global templates. |
| **HOD / Reviewer** | `hod.cse@curriculumai.edu` | `Hod@123` | Department curricula review, approval/rejection, Board of Studies sign-off. |
| **Faculty Member** | `faculty@curriculumai.edu` | `Faculty@123` | Create, edit, regenerate, and export course curricula. |

---

## 7. Sample Compiled Deliverables

The test suite automatically compiles a complete 3-page NBA curriculum document:
- **Compiled PDF**: `artifacts/file_generation/ttl=63d/output/curriculum_22cs501_nba_aicte.pdf`
- **Complete ZIP Archive**: `artifacts/file_generation/ttl=63d/output/curriculum_22cs501_bundle.zip`
