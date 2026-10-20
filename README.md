# FLOWGUARD — Master Engineering Documentation
**An Explainable AI Agent for Dynamic Hospital Emergency Resource Coordination**

> **Team Name:** Team Trauma  
> **Tagline:** *When every resource matters, every decision counts.*  
> **Classification:** Non-clinical Educational Engineering Simulation Prototype. Not for real diagnostic or clinical triage use.

---

## 1. Project Overview & Architectural Vision
FLOWGUARD addresses the critical logistical challenge in hospital emergency departments: allocating constrained, interdependent clinical resources (resuscitation bays, acute beds, trauma surgeons, emergency physicians, ventilators, cardiac monitors) under fluctuating patient arrival rates and sudden operational disruptions (e.g. bay decontamination outages, equipment failures, mass-casualty surges).

Unlike opaque black-box deep learning or naive FIFO queues, FLOWGUARD provides:
1. **Deterministic Rule-Based Decision Engine**: Completely reproducible, sub-10ms latency, zero hallucination, and mathematically bounded priority scoring with starvation mitigation.
2. **Dynamic Replanning**: Immediate recalculation of queue assignments when resources go offline or surge events occur.
3. **Multi-Resource Mutual Exclusion**: Enforces simultaneous co-allocation of physical beds, clinician specialties, and specialized equipment units.
4. **Transparent Auditability**: Every decision records applied rules, candidate considerations, rejected alternatives, and bottleneck rationale to SQLite.
5. **Local RAG & Optional LLM Explainer**: Seamlessly integrates with local Ollama (`llama3.2:3b`), gracefully falling back to deterministic explanation if the model is absent or offline.
6. **Reproducible Evaluation Laboratory**: Side-by-side empirical benchmark comparing the FLOWGUARD Agent against an unweighted FIFO baseline under identical synthetic cohorts.

---

## 2. Visual Identity & Design System
FLOWGUARD strictly avoids generic SaaS and blue/cyan "AI templates":
- **Primary Background**: Warm Ivory (`#F4F0E8`)
- **Primary Text & Structure**: Graphite (`#292A28`)
- **Primary Accent**: Restrained Vermilion (`#C84A35`)
- **Secondary Surfaces**: Warm Limestone (`#EAE5DA`) & Limestone Light (`#F0ECE2`)
- **Borders**: Stone Border (`#DCD6C8`)
- **Emergency Indicators**: Semantically distinct, high-contrast badges for Resuscitation (Vermilion), Emergent (Amber-Orange), and Stable/Discharged (Forest-Stone).

---

## 3. Technology Stack & Directory Structure
```
flowguard/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py         # REST endpoints for cases, resources, decisions, eval, rag
│   │   ├── core/
│   │   │   ├── config.py         # Pydantic v2 application settings
│   │   │   ├── database.py       # SQLite engine, sessions, declarative base
│   │   │   └── seed.py           # Safe, idempotent demonstration data seeder
│   │   ├── engine/
│   │   │   └── decision_engine.py# Deterministic explainable rule engine (5 invariants)
│   │   ├── evaluation/
│   │   │   └── evaluator.py      # Reproducible simulation & FIFO baseline comparator
│   │   ├── models/
│   │   │   └── entities.py       # SQLAlchemy relational models (Cases, Resources, Audits)
│   │   ├── rag/
│   │   │   └── rag_service.py    # Local operational RAG & Ollama llama3.2:3b connector
│   │   ├── schemas/
│   │   │   └── schemas.py        # Pydantic request/response schemas
│   │   └── main.py               # FastAPI application entrypoint with CORS
│   ├── tests/
│   │   ├── test_engine.py        # Unit tests for scoring, rules, and mutual exclusion
│   │   ├── test_api.py           # End-to-end API integration tests
│   │   └── test_persistence.py   # SQLite roundtrip persistence test across restarts
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api.ts                # Typed client for backend REST API
    │   ├── types.ts              # TypeScript interfaces mirroring backend schemas
    │   ├── App.tsx               # Primary single-page operations console & 7 workspaces
    │   └── index.css             # Tailwind CSS & Limestone custom scrollbars
    ├── package.json
    ├── tailwind.config.js        # Warm Ivory, Graphite & Vermilion palette
    └── vite.config.ts
```

---

## 4. Setup, Installation & Startup Guide

### Prerequisites
- Python 3.11+
- Node.js v18+ & npm
- (Optional) Local Ollama running `llama3.2:3b`

### Backend Setup & Launch
```powershell
cd C:\Users\nalag\.gemini\antigravity\scratch\flowguard\backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
- **Backend URL:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`

### Frontend Setup & Launch
```powershell
cd C:\Users\nalag\.gemini\antigravity\scratch\flowguard\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```
- **Frontend URL:** `http://127.0.0.1:5173`

---

## 5. Verification & Test Suite Results
All automated tests pass with 100% success rate:
- **`tests/test_engine.py`**:
  - `test_explicit_rules_defined`: Verified all 5 invariant rules are registered.
  - `test_priority_score_calculation`: Verified Level 1 preemption and Rule-04 wait boost.
  - `test_mutual_exclusion_and_capacity`: Verified two critical patients competing for 1 bay triggers honest conflict rejection on the second.
  - `test_evaluation_benchmark_execution`: Verified evaluation metrics computation.
- **`tests/test_api.py`**:
  - `test_health_endpoint`, `test_system_status`, `test_create_case_and_plan`, `test_resource_status_update`, `test_evaluation_lab_endpoint`, `test_audit_log_endpoint`.
- **`tests/test_persistence.py`**:
  - Verifies roundtrip persistence to SQLite surviving session closures and backend re-initializations.

---

## 6. Competition Demonstration Script
1. **Explore Operations Overview**: Observe live counts of queue length, bay capacity, clinician readiness, and equipment stock.
2. **Inspect Emergency Cases**: View simulated cases with calculated wait times and urgency tiers. Click "+ Create Case" to add a new acute presentation.
3. **Execute Agent Planning Cycle**: Click **Run Agent Planning Cycle**. Observe sub-millisecond execution, rule activations, and dynamic resource binding into treatment bays.
4. **Trigger Resource Disruption**: Go to **Resource Fleet** or **Scenario Simulator**. Click **Trigger Resus Bay 1 Outage**.
5. **Observe Dynamic Replanning**: Notice how FLOWGUARD immediately replans, shifting eligible cases or honestly reporting resource deficits with explicit bottleneck explanations.
6. **Run Evaluation Benchmark**: Open the **Evaluation Lab** and click **Run Surge Benchmark**. Observe how FLOWGUARD cuts critical delay to 0 compared to standard FIFO queuing.
7. **Inspect RAG Explanations**: In **Decision Intelligence**, ask: *"Why was Resuscitation Bay prioritized over Stepdown?"* to view citations from the operational knowledge base and Ollama generation.
