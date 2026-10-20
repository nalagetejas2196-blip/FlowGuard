from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from app.models.entities import UrgencyLevel, CaseStatus, ResourceType, ResourceStatus, BedCategory, StaffCapability, EquipmentType

# Patient Case Schemas
class PatientCaseCreate(BaseModel):
    name: str = Field(..., example="Patient #842")
    age: int = Field(..., ge=0, le=120, example=45)
    chief_complaint: str = Field(..., example="Acute respiratory distress")
    urgency_level: UrgencyLevel = Field(..., example=UrgencyLevel.CRITICAL_RESUSCITATION)
    required_bed_category: BedCategory = Field(..., example=BedCategory.RESUSCITATION_BAY)
    required_staff_capability: StaffCapability = Field(..., example=StaffCapability.TRAUMA_SURGEON)
    required_equipment: Optional[EquipmentType] = Field(None, example=EquipmentType.VENTILATOR)

class PatientCaseUpdate(BaseModel):
    name: Optional[str] = None
    urgency_level: Optional[UrgencyLevel] = None
    status: Optional[CaseStatus] = None
    required_bed_category: Optional[BedCategory] = None
    required_staff_capability: Optional[StaffCapability] = None
    required_equipment: Optional[EquipmentType] = None
    waiting_time_minutes: Optional[float] = None

class PatientCaseOut(BaseModel):
    id: str
    name: str
    age: int
    chief_complaint: str
    urgency_level: UrgencyLevel
    status: CaseStatus
    required_bed_category: BedCategory
    required_staff_capability: StaffCapability
    required_equipment: Optional[EquipmentType] = None
    arrival_time: datetime
    waiting_time_minutes: float
    simulated_priority_score: float
    assigned_bed_id: Optional[str] = None
    assigned_staff_id: Optional[str] = None
    assigned_equipment_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resource Schemas
class ResourceCreate(BaseModel):
    id: str = Field(..., example="BED-01")
    name: str = Field(..., example="Resuscitation Bay 1")
    resource_type: ResourceType
    subtype: str = Field(..., example="RESUSCITATION_BAY")
    location: Optional[str] = None
    metadata_info: Optional[Dict[str, Any]] = None

class ResourceStatusUpdate(BaseModel):
    status: ResourceStatus
    reason: Optional[str] = None

class ResourceOut(BaseModel):
    id: str
    name: str
    resource_type: ResourceType
    subtype: str
    status: ResourceStatus
    location: Optional[str] = None
    is_active: bool
    current_case_id: Optional[str] = None
    last_status_change: datetime
    metadata_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# Operational Decision Schemas
class AllocationAction(BaseModel):
    case_id: str
    case_name: str
    urgency_level: UrgencyLevel
    allocated_bed_id: Optional[str] = None
    allocated_staff_id: Optional[str] = None
    allocated_equipment_id: Optional[str] = None
    score: float
    justification: str
    rules_applied: List[str]

class RejectedAllocation(BaseModel):
    case_id: str
    case_name: str
    urgency_level: UrgencyLevel
    rejection_reason: str
    missing_resources: List[str]
    rule_blocked: str

class DecisionPlanResponse(BaseModel):
    decision_id: str
    timestamp: datetime
    trigger_reason: str
    total_waiting: int
    feasible_allocations: List[AllocationAction]
    rejected_allocations: List[RejectedAllocation]
    rules_activated: List[Dict[str, str]]
    planning_latency_ms: float
    conflict_detected: bool
    llm_explanation: Optional[str] = None

# Scenario Schemas
class ScenarioEventCreate(BaseModel):
    event_type: str = Field(..., example="BED_OUTAGE") # "BED_OUTAGE", "STAFF_UNAVAILABLE", "SURGE_ARRIVAL", "RESTORE_RESOURCE"
    target_id: Optional[str] = None
    description: str
    payload: Optional[Dict[str, Any]] = None

class ScenarioEventOut(BaseModel):
    id: str
    timestamp: datetime
    simulated_time_tick: int
    event_type: str
    target_id: Optional[str]
    description: str
    payload: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True

# Evaluation Schemas
class EvaluationRunRequest(BaseModel):
    scenario_type: str = Field(..., example="SUDDEN_SURGE") # "STANDARD_ARRIVAL", "SUDDEN_SURGE", "BED_OUTAGE_STORM", "MULTIPLE_RESOURCE_DEFICIT"
    simulation_ticks: int = Field(15, ge=5, le=50)

class EvaluationResultOut(BaseModel):
    id: str
    created_at: datetime
    scenario_name: str
    scenario_description: str
    simulation_ticks: int
    agent_metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    comparison_summary: Dict[str, Any]

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogOut(BaseModel):
    id: str
    timestamp: datetime
    action_type: str
    entity_type: str
    entity_id: Optional[str]
    details: Dict[str, Any]

    class Config:
        from_attributes = True

# RAG / Explainability Query
class ExplainQuery(BaseModel):
    query: str
    decision_id: Optional[str] = None
