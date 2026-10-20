import pytest
from app.models.entities import PatientCase, Resource, UrgencyLevel, CaseStatus, ResourceStatus, ResourceType, BedCategory, StaffCapability, EquipmentType
from app.engine.decision_engine import ExplainableDecisionEngine, EXPLICIT_RULES
from app.evaluation.evaluator import ScenarioEvaluator, BaselineGreedyAllocator

def test_explicit_rules_defined():
    assert len(EXPLICIT_RULES) >= 5
    rule_ids = [r["id"] for r in EXPLICIT_RULES]
    assert "RULE-01-CRITICAL-PREEMPTION" in rule_ids
    assert "RULE-02-EXACT-CAPABILITY-MATCH" in rule_ids
    assert "RULE-03-PREVENT-OVERALLOCATION" in rule_ids
    assert "RULE-04-WAIT-TIME-URGENCY-BOOST" in rule_ids
    assert "RULE-05-EQUIPMENT-CO-ALLOCATION" in rule_ids

def test_priority_score_calculation():
    crit_case = PatientCase(
        id="C1", name="Test Crit", age=45, chief_complaint="Arrest",
        urgency_level=UrgencyLevel.CRITICAL_RESUSCITATION, waiting_time_minutes=10.0
    )
    score_crit = ExplainableDecisionEngine.calculate_priority_score(crit_case)
    
    non_crit = PatientCase(
        id="C2", name="Test NonCrit", age=45, chief_complaint="Minor sprain",
        urgency_level=UrgencyLevel.NON_URGENT, waiting_time_minutes=10.0
    )
    score_non_crit = ExplainableDecisionEngine.calculate_priority_score(non_crit)

    assert score_crit > score_non_crit
    # Rule-04 wait boost: 10 mins * 2.5 = 25 pts boost
    assert score_crit >= 1025.0

def test_mutual_exclusion_and_capacity():
    # Only 1 resuscitation bay available, but 2 critical cases waiting
    cases = [
        PatientCase(id="C1", name="Crit 1", age=30, chief_complaint="Polytrauma",
                    urgency_level=UrgencyLevel.CRITICAL_RESUSCITATION, waiting_time_minutes=5.0,
                    required_bed_category=BedCategory.RESUSCITATION_BAY, required_staff_capability=StaffCapability.TRAUMA_SURGEON),
        PatientCase(id="C2", name="Crit 2", age=35, chief_complaint="Cardiac Arrest",
                    urgency_level=UrgencyLevel.CRITICAL_RESUSCITATION, waiting_time_minutes=15.0,
                    required_bed_category=BedCategory.RESUSCITATION_BAY, required_staff_capability=StaffCapability.TRAUMA_SURGEON)
    ]
    resources = [
        Resource(id="B1", name="Bay 1", resource_type=ResourceType.BED, subtype=BedCategory.RESUSCITATION_BAY.value, status=ResourceStatus.AVAILABLE),
        Resource(id="S1", name="Surgeon 1", resource_type=ResourceType.STAFF, subtype=StaffCapability.TRAUMA_SURGEON.value, status=ResourceStatus.AVAILABLE)
    ]

    feasible, rejected, rules, latency = ExplainableDecisionEngine.evaluate_and_plan(cases, resources)
    
    # Exactly one should be allocated, the other rejected with clear conflict explanation
    assert len(feasible) == 1
    assert len(rejected) == 1
    # C2 had 15m wait time, so higher score => C2 allocated
    assert feasible[0].case_id == "C2"
    assert rejected[0].case_id == "C1"
    assert "Missing Bed" in rejected[0].rejection_reason or "Missing Staff" in rejected[0].rejection_reason

def test_evaluation_benchmark_execution():
    eval_res = ScenarioEvaluator.execute_evaluation("SUDDEN_SURGE", ticks=5)
    assert eval_res["agent_metrics"]["feasible_allocation_rate_pct"] >= 0
    assert "critical_delay_reduction" in eval_res["comparison_summary"]
    assert eval_res["comparison_summary"]["safety_boundary_compliance"] is True
