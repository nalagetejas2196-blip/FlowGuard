import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class UrgencyLevel(str, enum.Enum):
    CRITICAL_RESUSCITATION = "CRITICAL_RESUSCITATION" # Level 1
    EMERGENT = "EMERGENT"                           # Level 2
    URGENT = "URGENT"                               # Level 3
    LESS_URGENT = "LESS_URGENT"                     # Level 4
    NON_URGENT = "NON_URGENT"                       # Level 5

class CaseStatus(str, enum.Enum):
    WAITING = "WAITING"
    ALLOCATING = "ALLOCATING"
    ASSIGNED = "ASSIGNED"
    IN_TREATMENT = "IN_TREATMENT"
    DISCHARGED = "DISCHARGED"
    TRANSFERRED = "TRANSFERRED"

class ResourceType(str, enum.Enum):
    BED = "BED"
    STAFF = "STAFF"
    EQUIPMENT = "EQUIPMENT"

class ResourceStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    SHORTAGE_MAINTENANCE = "SHORTAGE_MAINTENANCE"
    OFFLINE = "OFFLINE"

class BedCategory(str, enum.Enum):
    RESUSCITATION_BAY = "RESUSCITATION_BAY"
    ACUTE_MONITORED = "ACUTE_MONITORED"
    STEPDOWN = "STEPDOWN"
    FAST_TRACK = "FAST_TRACK"
    ISOLATION = "ISOLATION"

class StaffCapability(str, enum.Enum):
    TRAUMA_SURGEON = "TRAUMA_SURGEON"
    EMERGENCY_PHYSICIAN = "EMERGENCY_PHYSICIAN"
    TRIAGE_NURSE = "TRIAGE_NURSE"
    ICU_NURSE = "ICU_NURSE"
    RESPIRATORY_THERAPIST = "RESPIRATORY_THERAPIST"

class EquipmentType(str, enum.Enum):
    VENTILATOR = "VENTILATOR"
    CARDIAC_MONITOR = "CARDIAC_MONITOR"
    PORTABLE_ULTRASOUND = "PORTABLE_ULTRASOUND"
    DEFIBRILLATOR = "DEFIBRILLATOR"
    INFUSION_PUMP = "INFUSION_PUMP"

class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(String, primary_key=True, index=True) # e.g. "CASE-101"
    name = Column(String, nullable=False) # Synthetic anonymized demo name
    age = Column(Integer, nullable=False)
    chief_complaint = Column(String, nullable=False)
    urgency_level = Column(Enum(UrgencyLevel), nullable=False, index=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.WAITING, nullable=False, index=True)
    
    # Required resource profile
    required_bed_category = Column(Enum(BedCategory), nullable=False)
    required_staff_capability = Column(Enum(StaffCapability), nullable=False)
    required_equipment = Column(Enum(EquipmentType), nullable=True)
    
    arrival_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    waiting_time_minutes = Column(Float, default=0.0)
    simulated_priority_score = Column(Float, default=0.0)

    # Operational assignments
    assigned_bed_id = Column(String, ForeignKey("resources.id"), nullable=True)
    assigned_staff_id = Column(String, ForeignKey("resources.id"), nullable=True)
    assigned_equipment_id = Column(String, ForeignKey("resources.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("ResourceAssignment", back_populates="case", cascade="all, delete-orphan")


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String, primary_key=True, index=True) # e.g. "BED-01", "STAFF-DR-1"
    name = Column(String, nullable=False)
    resource_type = Column(Enum(ResourceType), nullable=False, index=True)
    subtype = Column(String, nullable=False) # e.g. "RESUSCITATION_BAY", "TRAUMA_SURGEON"
    status = Column(Enum(ResourceStatus), default=ResourceStatus.AVAILABLE, nullable=False, index=True)
    location = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Operational attributes
    current_case_id = Column(String, ForeignKey("patient_cases.id"), nullable=True)
    last_status_change = Column(DateTime, default=datetime.utcnow)
    metadata_info = Column(JSON, nullable=True) # Capabilities, shifts, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("ResourceAssignment", back_populates="resource")


class ResourceAssignment(Base):
    __tablename__ = "resource_assignments"

    id = Column(String, primary_key=True, index=True)
    case_id = Column(String, ForeignKey("patient_cases.id"), nullable=False)
    resource_id = Column(String, ForeignKey("resources.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    allocation_notes = Column(Text, nullable=True)

    case = relationship("PatientCase", back_populates="assignments")
    resource = relationship("Resource", back_populates="assignments")


class DecisionRun(Base):
    __tablename__ = "decision_runs"

    id = Column(String, primary_key=True, index=True) # e.g. "DEC-109238"
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    trigger_reason = Column(String, nullable=False) # e.g. "NEW_ARRIVAL", "RESOURCE_DISRUPTION", "MANUAL_REPLAN"
    operational_state_summary = Column(JSON, nullable=False)
    total_waiting_cases = Column(Integer, default=0)
    feasible_allocations_count = Column(Integer, default=0)
    unallocated_cases_count = Column(Integer, default=0)
    conflict_detected = Column(Boolean, default=False)
    
    # Detailed reasoning trace
    rules_activated = Column(JSON, nullable=False) # List of rule IDs and names
    candidate_actions_count = Column(Integer, default=0)
    rejected_actions_count = Column(Integer, default=0)
    decisions_trace = Column(JSON, nullable=False) # Structured trace of selected & rejected actions
    planning_latency_ms = Column(Float, default=0.0)
    
    # LLM summary if generated
    llm_summary = Column(Text, nullable=True)
    llm_model_used = Column(String, nullable=True)


class ScenarioEvent(Base):
    __tablename__ = "scenario_events"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    simulated_time_tick = Column(Integer, default=0)
    event_type = Column(String, nullable=False) # "SURGE_ARRIVAL", "BED_OUTAGE", "STAFF_SICK_LEAVE", "RESTORE_RESOURCE"
    target_id = Column(String, nullable=True)
    description = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    scenario_name = Column(String, nullable=False)
    scenario_description = Column(String, nullable=False)
    simulation_ticks = Column(Integer, default=10)
    
    # Comparative Results: Agent vs Baseline (FIFO/Greedy)
    agent_metrics = Column(JSON, nullable=False)
    baseline_metrics = Column(JSON, nullable=False)
    comparison_summary = Column(JSON, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    action_type = Column(String, nullable=False) # "CASE_CREATED", "STATUS_CHANGED", "RESOURCE_UPDATED", "DECISION_EXECUTED"
    entity_type = Column(String, nullable=False) # "CASE", "RESOURCE", "DECISION", "SYSTEM"
    entity_id = Column(String, nullable=True)
    details = Column(JSON, nullable=False)
