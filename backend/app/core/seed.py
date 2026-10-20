from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.entities import (
    PatientCase, Resource, UrgencyLevel, CaseStatus, ResourceType, 
    ResourceStatus, BedCategory, StaffCapability, EquipmentType, AuditLog
)

INITIAL_RESOURCES = [
    # Beds
    {"id": "BED-RESUS-01", "name": "Resuscitation Bay 1", "resource_type": ResourceType.BED, "subtype": BedCategory.RESUSCITATION_BAY.value, "status": ResourceStatus.AVAILABLE, "location": "Red Zone / Bay 1"},
    {"id": "BED-RESUS-02", "name": "Resuscitation Bay 2", "resource_type": ResourceType.BED, "subtype": BedCategory.RESUSCITATION_BAY.value, "status": ResourceStatus.AVAILABLE, "location": "Red Zone / Bay 2"},
    {"id": "BED-ACUTE-01", "name": "Acute Monitored Bed 1", "resource_type": ResourceType.BED, "subtype": BedCategory.ACUTE_MONITORED.value, "status": ResourceStatus.AVAILABLE, "location": "Yellow Zone / Cubicle 1"},
    {"id": "BED-ACUTE-02", "name": "Acute Monitored Bed 2", "resource_type": ResourceType.BED, "subtype": BedCategory.ACUTE_MONITORED.value, "status": ResourceStatus.AVAILABLE, "location": "Yellow Zone / Cubicle 2"},
    {"id": "BED-STEPDOWN-01", "name": "Stepdown Care Bay 1", "resource_type": ResourceType.BED, "subtype": BedCategory.STEPDOWN.value, "status": ResourceStatus.AVAILABLE, "location": "Green Zone / Unit 1"},
    {"id": "BED-STEPDOWN-02", "name": "Stepdown Care Bay 2", "resource_type": ResourceType.BED, "subtype": BedCategory.STEPDOWN.value, "status": ResourceStatus.AVAILABLE, "location": "Green Zone / Unit 2"},
    {"id": "BED-ISOL-01", "name": "Negative Pressure Isolation 1", "resource_type": ResourceType.BED, "subtype": BedCategory.ISOLATION.value, "status": ResourceStatus.AVAILABLE, "location": "Isolation Wing / Iso 1"},

    # Staff
    {"id": "STAFF-SURG-01", "name": "Dr. Sarah Lin, MD", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.TRAUMA_SURGEON.value, "status": ResourceStatus.AVAILABLE, "location": "Trauma Suite"},
    {"id": "STAFF-SURG-02", "name": "Dr. Tariq Al-Mansoor, MD", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.TRAUMA_SURGEON.value, "status": ResourceStatus.AVAILABLE, "location": "Trauma Suite"},
    {"id": "STAFF-PHYS-01", "name": "Dr. Elena Rostova, MD", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.EMERGENCY_PHYSICIAN.value, "status": ResourceStatus.AVAILABLE, "location": "Acute Observation"},
    {"id": "STAFF-PHYS-02", "name": "Dr. Marcus Vance, DO", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.EMERGENCY_PHYSICIAN.value, "status": ResourceStatus.AVAILABLE, "location": "Acute Observation"},
    {"id": "STAFF-NURSE-01", "name": "Nurse Priya Nair, BSN (ICU)", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.ICU_NURSE.value, "status": ResourceStatus.AVAILABLE, "location": "Central Nursing Station"},
    {"id": "STAFF-NURSE-02", "name": "Nurse Liam Gallagher, RN", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.TRIAGE_NURSE.value, "status": ResourceStatus.AVAILABLE, "location": "Intake Triage"},
    {"id": "STAFF-RESP-01", "name": "Carlos Gomez, RRT", "resource_type": ResourceType.STAFF, "subtype": StaffCapability.RESPIRATORY_THERAPIST.value, "status": ResourceStatus.AVAILABLE, "location": "Respiratory Therapy Pod"},

    # Equipment
    {"id": "EQ-VENT-01", "name": "Servo-u Intensive Ventilator 1", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.VENTILATOR.value, "status": ResourceStatus.AVAILABLE, "location": "Equipment Storage Pod A"},
    {"id": "EQ-VENT-02", "name": "Hamilton T1 Transport Ventilator", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.VENTILATOR.value, "status": ResourceStatus.AVAILABLE, "location": "Resuscitation Pod"},
    {"id": "EQ-CARD-01", "name": "Philips IntelliVue MX750 Monitor", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.CARDIAC_MONITOR.value, "status": ResourceStatus.AVAILABLE, "location": "Bay 1 Rack"},
    {"id": "EQ-CARD-02", "name": "Philips IntelliVue MX750 Monitor", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.CARDIAC_MONITOR.value, "status": ResourceStatus.AVAILABLE, "location": "Bay 2 Rack"},
    {"id": "EQ-DEFIB-01", "name": "Zoll R-Series Defibrillator", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.DEFIBRILLATOR.value, "status": ResourceStatus.AVAILABLE, "location": "Crash Cart Alpha"},
    {"id": "EQ-US-01", "name": "Sonosite Point-of-Care Ultrasound", "resource_type": ResourceType.EQUIPMENT, "subtype": EquipmentType.PORTABLE_ULTRASOUND.value, "status": ResourceStatus.AVAILABLE, "location": "Fast-Track Cart"}
]

INITIAL_CASES = [
    {
        "id": "CASE-101",
        "name": "Simulated Case #101",
        "age": 42,
        "chief_complaint": "Severe polytrauma following high-speed motor vehicle collision with airway compromise",
        "urgency_level": UrgencyLevel.CRITICAL_RESUSCITATION,
        "status": CaseStatus.WAITING,
        "required_bed_category": BedCategory.RESUSCITATION_BAY,
        "required_staff_capability": StaffCapability.TRAUMA_SURGEON,
        "required_equipment": EquipmentType.VENTILATOR,
        "waiting_minutes": 8.0
    },
    {
        "id": "CASE-102",
        "name": "Simulated Case #102",
        "age": 67,
        "chief_complaint": "Acute ST-elevation myocardial infarction (STEMI) symptoms with diaphoresis",
        "urgency_level": UrgencyLevel.EMERGENT,
        "status": CaseStatus.WAITING,
        "required_bed_category": BedCategory.ACUTE_MONITORED,
        "required_staff_capability": StaffCapability.EMERGENCY_PHYSICIAN,
        "required_equipment": EquipmentType.CARDIAC_MONITOR,
        "waiting_minutes": 15.0
    },
    {
        "id": "CASE-103",
        "name": "Simulated Case #103",
        "age": 28,
        "chief_complaint": "Severe exacerbation of chronic bronchial asthma with wheezing and hypoxemia",
        "urgency_level": UrgencyLevel.URGENT,
        "status": CaseStatus.WAITING,
        "required_bed_category": BedCategory.ACUTE_MONITORED,
        "required_staff_capability": StaffCapability.RESPIRATORY_THERAPIST,
        "required_equipment": None,
        "waiting_minutes": 22.0
    },
    {
        "id": "CASE-104",
        "name": "Simulated Case #104",
        "age": 55,
        "chief_complaint": "Suspected closed colles wrist fracture with stable neurovascular examination",
        "urgency_level": UrgencyLevel.LESS_URGENT,
        "status": CaseStatus.WAITING,
        "required_bed_category": BedCategory.STEPDOWN,
        "required_staff_capability": StaffCapability.TRIAGE_NURSE,
        "required_equipment": None,
        "waiting_minutes": 38.0
    },
    {
        "id": "CASE-105",
        "name": "Simulated Case #105",
        "age": 73,
        "chief_complaint": "Sudden onset focal neurological deficit with aphasia and right hemiparesis",
        "urgency_level": UrgencyLevel.CRITICAL_RESUSCITATION,
        "status": CaseStatus.WAITING,
        "required_bed_category": BedCategory.RESUSCITATION_BAY,
        "required_staff_capability": StaffCapability.TRAUMA_SURGEON,
        "required_equipment": EquipmentType.VENTILATOR,
        "waiting_minutes": 12.0
    }
]

def seed_database_demo_data(db: Session, force_reset: bool = False):
    """
    Safely seeds initial realistic demonstration resources and patient cases.
    Does NOT overwrite existing data unless explicitly requested.
    """
    existing_resource_count = db.query(Resource).count()
    if existing_resource_count > 0 and not force_reset:
        return {"status": "skipped", "message": f"Database already contains {existing_resource_count} resources."}

    if force_reset:
        db.query(AuditLog).delete()
        db.query(PatientCase).delete()
        db.query(Resource).delete()
        db.commit()

    # Seed Resources
    for r in INITIAL_RESOURCES:
        db_res = Resource(
            id=r["id"],
            name=r["name"],
            resource_type=r["resource_type"],
            subtype=r["subtype"],
            status=r["status"],
            location=r["location"],
            is_active=True
        )
        db.add(db_res)

    now = datetime.utcnow()
    # Seed Cases
    for c in INITIAL_CASES:
        db_case = PatientCase(
            id=c["id"],
            name=c["name"],
            age=c["age"],
            chief_complaint=c["chief_complaint"],
            urgency_level=c["urgency_level"],
            status=c["status"],
            required_bed_category=c["required_bed_category"],
            required_staff_capability=c["required_staff_capability"],
            required_equipment=c["required_equipment"],
            arrival_time=now - timedelta(minutes=c["waiting_minutes"]),
            waiting_time_minutes=c["waiting_minutes"],
            simulated_priority_score=0.0
        )
        db.add(db_case)

    # Initial Audit Log
    db.add(AuditLog(
        id="AUDIT-INIT-01",
        action_type="DATABASE_SEEDED",
        entity_type="SYSTEM",
        entity_id="SEED-INIT",
        details={"resources_seeded": len(INITIAL_RESOURCES), "cases_seeded": len(INITIAL_CASES)}
    ))

    db.commit()
    return {"status": "success", "message": f"Seeded {len(INITIAL_RESOURCES)} resources and {len(INITIAL_CASES)} synthetic cases."}
