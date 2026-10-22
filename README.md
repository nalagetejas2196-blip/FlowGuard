# FLOWGUARD
### Explainable AI Agent for Dynamic Hospital Emergency Resource Coordination

> **Team Name:** Team Trauma  
> **Tagline:** *When every resource matters, every decision counts.*  
> **Classification:** Non-Clinical Educational Engineering Simulation Prototype. Not for real diagnostic or clinical triage use.

---

## 📌 Executive Summary

**FLOWGUARD** is a competition-ready, full-stack operational intelligence platform engineered to simulate, coordinate, and dynamically optimize resource allocations in hospital Emergency Departments (EDs). 

Hospital emergency rooms are complex, constrained environments where beds, clinical personnel, and life-critical equipment must be co-allocated under severe uncertainty, sudden arrival surges, and unannounced operational disruptions (e.g., bay decontamination, staff absenteeism, equipment breakdown). Naive FIFO (First-In, First-Out) queuing delays resuscitation patients, while opaque black-box deep learning models fail healthcare transparency standards.

FLOWGUARD solves this through:
1. **A Deterministic, Explainable Rule Engine** with sub-5ms latency, explicit invariants, and starvation mitigation.
2. **Mutual Resource Co-Allocation** enforcing simultaneous availability of compatible beds, clinician capabilities, and required medical devices.
3. **Dynamic Re-planning** that triggers immediate reallocation when operational disruptions occur.
4. **Reproducible Evaluation Laboratory** providing side-by-side empirical benchmarks against unweighted FIFO baselines.
5. **Local RAG & Local LLM Explainer** using an operational knowledge base with Ollama (`llama3.2:3b`), paired with an automatic deterministic fallback.
6. **A Bespoke Visual Identity** designed around Warm Ivory (`#F4F0E8`), Graphite (`#292A28`), and Signal Vermilion (`#C84A35`).

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────┐
                               │       FLOWGUARD Frontend Console       │
                               │  (React 19, TypeScript, Tailwind CSS)  │
                               └───────────────────┬────────────────────┘
                                                   │ HTTP / REST API
                                                   ▼
                               ┌────────────────────────────────────────┐
                               │           FastAPI Backend              │
                               │        (Python 3.11, Pydantic)         │
                               └───────┬───────────────────┬────────────┘
                                       │                   │
                  ┌────────────────────┴──────┐   ┌────────┴───────────────────┐
                  ▼                           ▼   ▼                            ▼
      ┌───────────────────────┐   ┌───────────────────────┐    ┌────────────────────────┐
      │ Deterministic Engine  │   │   Evaluation Lab      │    │  Local RAG & LLM       │
      │ • Priority Scoring    │   │ • Synthetic Cohorts   │    │ • Curated ED Ops KB    │
      │ • 5 Invariant Rules   │   │ • Side-by-Side FIFO   │    │ • Ollama (llama3.2:3b) │
      │ • Starvation Guard    │   │ • Comparative Metrics │    │ • Deterministic Fallbk │
      └───────────┬───────────┘   └───────────┬───────────┘    └───────────┬────────────┘
                  │                           │                            │
                  └───────────────────────────┼────────────────────────────┘
                                              ▼
                               ┌─────────────────────────┐
                               │  Persistent SQLite DB   │
                               │  (SQLAlchemy Relational)│
                               │ • Cases, Resources      │
                               │ • Decision Traces       │
                               │ • Immutable Audit Logs  │
                               └─────────────────────────┘
```

---

## ⚙️ Core Technical Capabilities

### 1. Transparent 5-Invariant Rule Engine
Every decision is governed by explicit operational invariants, completely eliminating hallucinations:
- **`RULE-01-CRITICAL-PREEMPTION`**: Level 1 Resuscitation cases receive maximum weight (1000 pts) and immediately claim available resuscitation bays and trauma surgeons.
- **`RULE-02-EXACT-CAPABILITY-MATCH`**: Enforces strict operational compatibility (e.g., Trauma Surgeon vs. Emergency Physician vs. ICU Nurse; Resuscitation Bay vs. Acute Monitored vs. Stepdown).
- **`RULE-03-PREVENT-OVERALLOCATION`**: Strict mutual exclusion preventing concurrent double-booking of any bed, staff member, or equipment unit.
- **`RULE-04-WAIT-TIME-URGENCY-BOOST`**: Linear starvation mitigation (+$2.5\text{ pts/min}$) ensuring prolonged wait times elevate priority among equal clinical severities.
- **`RULE-05-EQUIPMENT-CO-ALLOCATION`**: Simultaneous dependency verification (e.g., Ventilator, Defibrillator) before confirming allocation feasibility.

### 2. Live Explainability & Rejection Rationale
When an allocation cannot be made, FLOWGUARD does not fail silently. It provides an honest bottleneck report detailing the exact missing requirement (e.g., *Blocked by RULE-05: Missing Equipment [VENTILATOR]*).

### 3. Local Retrieval-Augmented Generation (RAG)
- Curated operational knowledge base covering triage queue disciplines, bed-bay facility logistics, staffing ratios, and safety boundaries.
- Native integration with local Ollama (`llama3.2:3b`).
- **Guaranteed Fallback**: If Ollama is offline or times out, the platform serves structured deterministic explanations with ground-truth citations.

### 4. Reproducible Evaluation Laboratory
Empirically benchmarks FLOWGUARD against an unweighted FIFO baseline across identical synthetic cohorts under standard arrivals, bed outage storms, and sudden multi-casualty surges.

---

## 🎨 Visual Identity & UI Design

FLOWGUARD rejects generic blue/cyan SaaS templates in favor of a specialized clinical operations aesthetic:

| Element | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Warm Ivory** | `#F4F0E8` | Primary background reducing eye fatigue |
| **Graphite** | `#292A28` | High-contrast structural typography and borders |
| **Signal Vermilion** | `#C84A35` | High-urgency alerts, critical indicators, primary actions |
| **Warm Limestone** | `#EAE5DA` | Secondary card surfaces and structural dividers |
| **Limestone Light** | `#F0ECE2` | Primary card panels and operational tables |

---

## 📂 Repository Structure

```
FlowGuard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # REST endpoints for cases, resources, decisions, eval, rag
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic application settings
│   │   │   ├── database.py       # SQLAlchemy engine & session factory
│   │   │   └── seed.py           # Safe, non-destructive demo data seeder
│   │   ├── engine/
│   │   │   └── decision_engine.py# Deterministic rule engine (5 invariants + scoring)
│   │   ├── evaluation/
│   │   │   └── evaluator.py      # Reproducible simulation & FIFO comparator
│   │   ├── models/
│   │   │   └── entities.py       # Relational models (Cases, Resources, Audits)
│   │   ├── rag/
│   │   │   └── rag_service.py    # Local RAG knowledge base & Ollama connector
│   │   ├── schemas/
│   │   │   └── schemas.py        # Typed Pydantic request/response schemas
│   │   └── main.py               # FastAPI entrypoint with CORS & auto-seed
│   ├── tests/
│   │   ├── test_engine.py        # Invariant rules, scoring, and conflict tests
│   │   ├── test_api.py           # REST endpoints and end-to-end integration tests
│   │   └── test_persistence.py   # SQLite persistence test across backend restarts
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api.ts                # Strongly-typed API client
│   │   ├── types.ts              # TypeScript schemas mirroring backend entities
│   │   ├── App.tsx               # Primary ops console with 7 integrated workspaces
│   │   └── index.css             # Tailwind styles & custom limestone scrollbars
│   ├── package.json
│   ├── tailwind.config.js        # Custom warm ivory / graphite / vermilion theme
│   └── vite.config.ts
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python:** 3.11+
- **Node.js:** v18+ & npm
- *(Optional)* **Ollama:** with `llama3.2:3b` installed for local LLM summaries

---

### 1. Backend Setup & Startup

```powershell
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Launch FastAPI server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- **Backend API:** `http://127.0.0.1:8000`
- **Interactive Swagger Documentation:** `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup & Startup

```powershell
# Open a new terminal and navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Launch Vite development server
npm run dev -- --host 127.0.0.1 --port 5173
```

- **Frontend Console:** `http://127.0.0.1:5173`

---

### 3. Optional: Local Ollama LLM Integration

FLOWGUARD functions completely offline in deterministic mode. To enable local AI summaries:
```powershell
# Ensure Ollama is running and pull the lightweight model
ollama pull llama3.2:3b
```
The application automatically detects the running Ollama model on `http://localhost:11434`.

---

## 🧪 Automated Testing & Verification

All automated test suites pass with 100% success rate:

```powershell
cd backend
python -m pytest tests
```

### Verified Test Suites:
- `tests/test_engine.py`: Verifies priority scoring arithmetic, starvation mitigation, all 5 rule invariants, and mutual exclusion under resource contention.
- `tests/test_api.py`: Validates REST endpoints, synthetic case generation, status updates, evaluation executions, and audit log retrieval.
- `tests/test_persistence.py`: Validates that database entities, assignments, and audit logs persist intact across database disconnects and server restarts.

---

## 💻 7 Integrated Workspaces in the Console

1. **Operations Overview**: Real-time KPI summary (queue length, bay capacity, clinician readiness, equipment counts) and live waiting queue.
2. **Emergency Cases**: Filterable table of all synthetic patients with computed urgency scores, wait times, and required resources.
3. **Resource Fleet**: Management view for treatment bays, clinical staff, and equipment with one-click outage simulation.
4. **Decision Intelligence**: Full explainable decision trace with latency indicators, rule activation lists, and LLM/deterministic explainers.
5. **Scenario Simulator**: Inject real-world disruptions (Mass-Casualty Surge, Bay Decontamination Outage, Fleet Restorations) and watch instantaneous agent replanning.
6. **Evaluation Laboratory**: Run reproducible experiments comparing FLOWGUARD against standard FIFO queuing across configurable simulation ticks.
7. **Audit Trail**: Searchable, immutable chronological log of every operational event and allocation decision.

---

## ⚖️ Safety & Non-Clinical Disclaimer

FLOWGUARD is an educational and engineering prototype designed to demonstrate deterministic resource allocation and operational logistics in a simulated healthcare setting. **It does not provide clinical diagnoses, medical advice, or treatment plans.** All decisions in clinical environments must be made by qualified healthcare professionals.

---

## 👥 Authors

**Team Trauma**
- Designed, engineered, and verified for hospital operations optimization competitions.
