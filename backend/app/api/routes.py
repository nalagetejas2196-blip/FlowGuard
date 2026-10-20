from datetime import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.seed import seed_database_demo_data
from app.models.entities import (
    PatientCase, Resource, ResourceAssignment, DecisionRun, 
    ScenarioEvent, EvaluationRun, AuditLog, CaseStatus, ResourceStatus, UrgencyLevel
)
from app.schemas.schemas import (
    PatientCaseCreate, PatientCaseUpdate, PatientCaseOut,
    ResourceCreate, ResourceStatusUpdate, ResourceOut,
    DecisionPlanResponse, ScenarioEventCreate, ScenarioEventOut,
    EvaluationRunRequest, EvaluationResultOut, AuditLogOut, ExplainQuery
)
from app.engine.decision_engine import ExplainableDecisionEngine
from app.evaluation.evaluator import ScenarioEvaluator
from app.rag.rag_service import LocalRAGService

router = APIRouter()

# ----------------- SYSTEM & SEED -----------------

@router.get("/health")
def get_health():
    return {
        "status": "healthy",
        "service": "FLOWGUARD Emergency Resource Coordination Agent",
        "version": "1.0.0",
        "mode": "Simulation / Educational Prototype"
    }

@router.post("/system/seed")
def seed_data(force_reset: bool = False, db: Session = Depends(get_db)):
    result = seed_database_demo_data(db, force_reset=force_reset)
    return result

@router.get("/system/status")
async def get_system_status(db: Session = Depends(get_db)):
    total_cases = db.query(PatientCase).count()
    waiting_cases = db.query(PatientCase).filter(PatientCase.status == CaseStatus.WAITING).count()
    total_resources = db.query(Resource).count()
    available_resources = db.query(Resource).filter(Resource.status == ResourceStatus.AVAILABLE).count()
    total_decisions = db.query(DecisionRun).count()
    ollama_info = await LocalRAGService.check_ollama_health()

    return {
        "total_cases": total_cases,
        "waiting_cases": waiting_cases,
        "total_resources": total_resources,
        "available_resources": available_resources,
        "total_decisions_executed": total_decisions,
        "ollama_layer": ollama_info
    }

# ----------------- PATIENT CASES -----------------

@router.get("/cases", response_model=List[PatientCaseOut])
def list_cases(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PatientCase)
    if status:
        query = query.filter(PatientCase.status == status)
    return query.order_by(PatientCase.created_at.desc()).all()

@router.post("/cases", response_model=PatientCaseOut)
def create_case(case_in: PatientCaseCreate, db: Session = Depends(get_db)):
    case_id = f"CASE-{uuid.uuid4().hex[:6].upper()}"
    new_case = PatientCase(
        id=case_id,
        name=case_in.name,
        age=case_in.age,
        chief_complaint=case_in.chief_complaint,
        urgency_level=case_in.urgency_level,
        status=CaseStatus.WAITING,
        required_bed_category=case_in.required_bed_category,
        required_staff_capability=case_in.required_staff_capability,
        required_equipment=case_in.required_equipment,
        waiting_time_minutes=0.0,
        simulated_priority_score=ExplainableDecisionEngine.calculate_priority_score(
            PatientCase(
                id=case_id,
                name=case_in.name,
                age=case_in.age,
                chief_complaint=case_in.chief_complaint,
                urgency_level=case_in.urgency_level,
                waiting_time_minutes=0.0
            )
        )
    )
    db.add(new_case)
    
    # Audit log
    db.add(AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        action_type="CASE_CREATED",
        entity_type="CASE",
        entity_id=case_id,
        details={"name": new_case.name, "urgency": new_case.urgency_level.value}
    ))
    db.commit()
    db.refresh(new_case)
    return new_case

@router.patch("/cases/{case_id}", response_model=PatientCaseOut)
def update_case(case_id: str, case_in: PatientCaseUpdate, db: Session = Depends(get_db)):
    case = db.query(PatientCase).filter(PatientCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    update_data = case_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(case, field, val)
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case

# ----------------- RESOURCES -----------------

@router.get("/resources", response_model=List[ResourceOut])
def list_resources(resource_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Resource)
    if resource_type:
        query = query.filter(Resource.resource_type == resource_type)
    return query.all()

@router.patch("/resources/{resource_id}/status", response_model=ResourceOut)
def update_resource_status(resource_id: str, payload: ResourceStatusUpdate, db: Session = Depends(get_db)):
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    old_status = resource.status
    resource.status = payload.status
    resource.last_status_change = datetime.utcnow()

    # Record scenario event & audit
    event_id = f"EVT-{uuid.uuid4().hex[:6].upper()}"
    db.add(ScenarioEvent(
        id=event_id,
        simulated_time_tick=0,
        event_type="RESOURCE_STATUS_CHANGE",
        target_id=resource_id,
        description=f"Resource {resource.name} ({resource_id}) changed status from {old_status.value} to {payload.status.value}. Reason: {payload.reason or 'Operational update'}",
        payload={"previous_status": old_status.value, "new_status": payload.status.value, "reason": payload.reason}
    ))

    db.add(AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        action_type="RESOURCE_STATUS_CHANGE",
        entity_type="RESOURCE",
        entity_id=resource_id,
        details={"from": old_status.value, "to": payload.status.value, "reason": payload.reason}
    ))

    db.commit()
    db.refresh(resource)
    return resource

# ----------------- DECISION INTELLIGENCE -----------------

@router.post("/decisions/plan", response_model=DecisionPlanResponse)
async def execute_planning_cycle(
    trigger_reason: str = Query("MANUAL_OPTIMIZATION", description="Reason for running plan"),
    apply_allocations: bool = Query(True, description="Whether to commit assignments into DB"),
    db: Session = Depends(get_db)
):
    waiting_cases = db.query(PatientCase).filter(PatientCase.status == CaseStatus.WAITING).all()
    available_resources = db.query(Resource).filter(Resource.status == ResourceStatus.AVAILABLE).all()

    feasible, rejected, rules, latency_ms = ExplainableDecisionEngine.evaluate_and_plan(
        waiting_cases, available_resources
    )

    decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
    conflict_detected = len(rejected) > 0

    # If apply_allocations is True, commit assignments to database
    if apply_allocations:
        for alloc in feasible:
            case = db.query(PatientCase).filter(PatientCase.id == alloc.case_id).first()
            if case:
                case.status = CaseStatus.ASSIGNED
                case.assigned_bed_id = alloc.allocated_bed_id
                case.assigned_staff_id = alloc.allocated_staff_id
                case.assigned_equipment_id = alloc.allocated_equipment_id

                # Update resources
                if alloc.allocated_bed_id:
                    bed = db.query(Resource).filter(Resource.id == alloc.allocated_bed_id).first()
                    if bed:
                        bed.status = ResourceStatus.OCCUPIED
                        bed.current_case_id = case.id
                if alloc.allocated_staff_id:
                    staff = db.query(Resource).filter(Resource.id == alloc.allocated_staff_id).first()
                    if staff:
                        staff.status = ResourceStatus.OCCUPIED
                        staff.current_case_id = case.id
                if alloc.allocated_equipment_id:
                    eq = db.query(Resource).filter(Resource.id == alloc.allocated_equipment_id).first()
                    if eq:
                        eq.status = ResourceStatus.OCCUPIED
                        eq.current_case_id = case.id

    # Persist Decision Run
    run_record = DecisionRun(
        id=decision_id,
        trigger_reason=trigger_reason,
        operational_state_summary={
            "total_waiting": len(waiting_cases),
            "available_resources": len(available_resources)
        },
        total_waiting_cases=len(waiting_cases),
        feasible_allocations_count=len(feasible),
        unallocated_cases_count=len(rejected),
        conflict_detected=conflict_detected,
        rules_activated=rules,
        candidate_actions_count=len(waiting_cases),
        rejected_actions_count=len(rejected),
        decisions_trace={
            "feasible": [a.dict() for a in feasible],
            "rejected": [r.dict() for r in rejected]
        },
        planning_latency_ms=latency_ms
    )
    db.add(run_record)

    db.add(AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        action_type="PLANNING_CYCLE_EXECUTED",
        entity_type="DECISION",
        entity_id=decision_id,
        details={
            "feasible_count": len(feasible),
            "rejected_count": len(rejected),
            "latency_ms": latency_ms,
            "trigger": trigger_reason
        }
    ))
    db.commit()

    return DecisionPlanResponse(
        decision_id=decision_id,
        timestamp=run_record.timestamp,
        trigger_reason=trigger_reason,
        total_waiting=len(waiting_cases),
        feasible_allocations=feasible,
        rejected_allocations=rejected,
        rules_activated=rules,
        planning_latency_ms=latency_ms,
        conflict_detected=conflict_detected
    )

@router.get("/decisions/history")
def get_decision_history(limit: int = 10, db: Session = Depends(get_db)):
    runs = db.query(DecisionRun).order_by(DecisionRun.timestamp.desc()).limit(limit).all()
    return runs

# ----------------- SCENARIO SIMULATION -----------------

@router.post("/simulation/event", response_model=ScenarioEventOut)
def inject_scenario_event(evt_in: ScenarioEventCreate, db: Session = Depends(get_db)):
    event_id = f"EVT-{uuid.uuid4().hex[:6].upper()}"
    new_evt = ScenarioEvent(
        id=event_id,
        event_type=evt_in.event_type,
        target_id=evt_in.target_id,
        description=evt_in.description,
        payload=evt_in.payload
    )
    db.add(new_evt)

    # If the event modifies a resource status directly
    if evt_in.event_type in ["BED_OUTAGE", "STAFF_UNAVAILABLE", "EQUIPMENT_FAILURE"] and evt_in.target_id:
        res = db.query(Resource).filter(Resource.id == evt_in.target_id).first()
        if res:
            res.status = ResourceStatus.SHORTAGE_MAINTENANCE
            res.last_status_change = datetime.utcnow()
    elif evt_in.event_type == "RESTORE_RESOURCE" and evt_in.target_id:
        res = db.query(Resource).filter(Resource.id == evt_in.target_id).first()
        if res:
            res.status = ResourceStatus.AVAILABLE
            res.last_status_change = datetime.utcnow()

    # If it's a surge arrival event, inject synthetic emergent cases
    if evt_in.event_type == "SURGE_ARRIVAL":
        now = datetime.utcnow()
        for idx in range(3):
            cid = f"SURGE-{uuid.uuid4().hex[:4].upper()}"
            s_case = PatientCase(
                id=cid,
                name=f"Surge Victim #{idx+1}",
                age=35 + idx * 5,
                chief_complaint="Multi-trauma presentation from incident scene",
                urgency_level=UrgencyLevel.CRITICAL_RESUSCITATION if idx == 0 else UrgencyLevel.EMERGENT,
                status=CaseStatus.WAITING,
                required_bed_category=BedCategory.RESUSCITATION_BAY if idx == 0 else BedCategory.ACUTE_MONITORED,
                required_staff_capability=StaffCapability.TRAUMA_SURGEON if idx == 0 else StaffCapability.EMERGENCY_PHYSICIAN,
                required_equipment=None,
                waiting_time_minutes=2.0
            )
            db.add(s_case)

    db.add(AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8]}",
        action_type="SCENARIO_EVENT_INJECTED",
        entity_type="SYSTEM",
        entity_id=event_id,
        details={"type": evt_in.event_type, "desc": evt_in.description}
    ))

    db.commit()
    db.refresh(new_evt)
    return new_evt

@router.get("/simulation/events", response_model=List[ScenarioEventOut])
def get_scenario_events(limit: int = 20, db: Session = Depends(get_db)):
    return db.query(ScenarioEvent).order_by(ScenarioEvent.timestamp.desc()).limit(limit).all()

# ----------------- EVALUATION LAB -----------------

@router.post("/evaluation/run", response_model=EvaluationResultOut)
def run_evaluation(payload: EvaluationRunRequest, db: Session = Depends(get_db)):
    result = ScenarioEvaluator.execute_evaluation(payload.scenario_type, ticks=payload.simulation_ticks)
    
    run_id = f"EVAL-{uuid.uuid4().hex[:6].upper()}"
    eval_record = EvaluationRun(
        id=run_id,
        scenario_name=result["scenario_name"],
        scenario_description=result["scenario_description"],
        simulation_ticks=result["simulation_ticks"],
        agent_metrics=result["agent_metrics"],
        baseline_metrics=result["baseline_metrics"],
        comparison_summary=result["comparison_summary"]
    )
    db.add(eval_record)
    db.commit()
    db.refresh(eval_record)
    return eval_record

@router.get("/evaluation/history", response_model=List[EvaluationResultOut])
def list_evaluations(db: Session = Depends(get_db)):
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(15).all()

# ----------------- RAG & EXPLAINABILITY -----------------

@router.post("/explain")
async def explain_decision(query_in: ExplainQuery):
    explanation = await LocalRAGService.generate_explanation(query_in.query)
    return explanation

# ----------------- AUDIT TRAIL -----------------

@router.get("/audit", response_model=List[AuditLogOut])
def get_audit_trail(limit: int = 30, db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
