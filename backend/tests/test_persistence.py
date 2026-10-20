import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.entities import PatientCase, Resource, UrgencyLevel, CaseStatus, ResourceStatus, BedCategory, StaffCapability
from app.engine.decision_engine import ExplainableDecisionEngine

def test_sqlite_persistence_roundtrip():
    # 1. Create unique test case in DB
    db = SessionLocal()
    test_id = "PERSIST-TEST-001"
    
    # Clean if exists
    existing = db.query(PatientCase).filter(PatientCase.id == test_id).first()
    if existing:
        db.delete(existing)
        db.commit()

    case = PatientCase(
        id=test_id,
        name="Persistence Test Case",
        age=39,
        chief_complaint="Severe trauma roundtrip validation",
        urgency_level=UrgencyLevel.CRITICAL_RESUSCITATION,
        status=CaseStatus.WAITING,
        required_bed_category=BedCategory.RESUSCITATION_BAY,
        required_staff_capability=StaffCapability.TRAUMA_SURGEON
    )
    db.add(case)
    db.commit()
    db.close()

    # 2. Re-open independent database session to emulate backend restart
    fresh_db = SessionLocal()
    retrieved = fresh_db.query(PatientCase).filter(PatientCase.id == test_id).first()
    assert retrieved is not None
    assert retrieved.name == "Persistence Test Case"
    assert retrieved.urgency_level == UrgencyLevel.CRITICAL_RESUSCITATION

    # Clean up test artifact
    fresh_db.delete(retrieved)
    fresh_db.commit()
    fresh_db.close()
