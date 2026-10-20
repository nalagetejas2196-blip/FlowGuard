import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.entities import UrgencyLevel, BedCategory, StaffCapability

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "FLOWGUARD" in data["service"]

def test_system_status():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_cases"] >= 0
    assert data["total_resources"] >= 0
    assert "ollama_layer" in data

def test_create_case_and_plan():
    # 1. Create a synthetic patient case
    case_payload = {
        "name": "Integration Test Patient",
        "age": 52,
        "chief_complaint": "Acute unstable angina",
        "urgency_level": "EMERGENT",
        "required_bed_category": "ACUTE_MONITORED",
        "required_staff_capability": "EMERGENCY_PHYSICIAN",
        "required_equipment": "CARDIAC_MONITOR"
    }
    create_res = client.post("/api/v1/cases", json=case_payload)
    assert create_res.status_code == 200
    created_case = create_res.json()
    assert created_case["id"].startswith("CASE-")
    assert created_case["status"] == "WAITING"

    # 2. Run planning cycle
    plan_res = client.post("/api/v1/decisions/plan?trigger_reason=INTEGRATION_TEST")
    assert plan_res.status_code == 200
    plan_data = plan_res.json()
    assert "decision_id" in plan_data
    assert plan_data["planning_latency_ms"] >= 0

def test_resource_status_update():
    # Fetch resources
    res = client.get("/api/v1/resources")
    assert res.status_code == 200
    resources = res.json()
    assert len(resources) > 0
    target_id = resources[0]["id"]

    # Toggle status to SHORTAGE_MAINTENANCE
    update_res = client.patch(
        f"/api/v1/resources/{target_id}/status",
        json={"status": "SHORTAGE_MAINTENANCE", "reason": "Sterilization protocol"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "SHORTAGE_MAINTENANCE"

    # Restore status to AVAILABLE
    restore_res = client.patch(
        f"/api/v1/resources/{target_id}/status",
        json={"status": "AVAILABLE", "reason": "Sanitation complete"}
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["status"] == "AVAILABLE"

def test_evaluation_lab_endpoint():
    eval_payload = {
        "scenario_type": "STANDARD_ARRIVAL",
        "simulation_ticks": 10
    }
    eval_res = client.post("/api/v1/evaluation/run", json=eval_payload)
    assert eval_res.status_code == 200
    data = eval_res.json()
    assert "agent_metrics" in data
    assert "baseline_metrics" in data
    assert "comparison_summary" in data

def test_audit_log_endpoint():
    audit_res = client.get("/api/v1/audit")
    assert audit_res.status_code == 200
    assert isinstance(audit_res.json(), list)
