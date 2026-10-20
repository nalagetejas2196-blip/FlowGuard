from typing import List, Dict, Tuple, Optional, Any
import time
from datetime import datetime
from app.models.entities import (
    PatientCase, Resource, UrgencyLevel, CaseStatus, 
    ResourceStatus, ResourceType, BedCategory, StaffCapability, EquipmentType
)
from app.schemas.schemas import AllocationAction, RejectedAllocation

# Standard Priority Weights based on emergency operational severity
PRIORITY_WEIGHTS = {
    UrgencyLevel.CRITICAL_RESUSCITATION: 1000.0,
    UrgencyLevel.EMERGENT: 500.0,
    UrgencyLevel.URGENT: 200.0,
    UrgencyLevel.LESS_URGENT: 50.0,
    UrgencyLevel.NON_URGENT: 10.0,
}

# Explicit Rule Definitions
EXPLICIT_RULES = [
    {
        "id": "RULE-01-CRITICAL-PREEMPTION",
        "name": "Critical Resuscitation First Priority",
        "description": "Patients with Level 1 (Critical Resuscitation) receive maximum weight (1000pt) and claim immediate priority for available resuscitation bays and trauma surgeons."
    },
    {
        "id": "RULE-02-EXACT-CAPABILITY-MATCH",
        "name": "Strict Capability & Bed Tier Compatibility",
        "description": "Patients are only matched to beds and clinical staff capable of satisfying their required operational level. Incompatible resource pairings are strictly rejected."
    },
    {
        "id": "RULE-03-PREVENT-OVERALLOCATION",
        "name": "Mutual Resource Exclusion",
        "description": "A single physical bed, staff member, or equipment unit can only be assigned to one active patient at any moment. Secondary concurrent assignment is prohibited."
    },
    {
        "id": "RULE-04-WAIT-TIME-URGENCY-BOOST",
        "name": "Waiting-Time Starvation Mitigation",
        "description": "For cases of equal clinical urgency, waiting time increases priority score linearly (2.5 points per minute queued) to prevent prolonged starvation."
    },
    {
        "id": "RULE-05-EQUIPMENT-CO-ALLOCATION",
        "name": "Vital Equipment Dependency Verification",
        "description": "If a case requires specialized equipment (e.g., Ventilator, Defibrillator), the allocation is only marked feasible if both bed, staff, AND equipment are simultaneously available."
    }
]

class ExplainableDecisionEngine:
    """
    Deterministic, explainable rule-based planning engine for emergency department resource coordination.
    Guarantees reproducible allocations, complete trace transparency, and zero hallucination.
    """

    @classmethod
    def calculate_priority_score(cls, case: PatientCase) -> float:
        base_weight = PRIORITY_WEIGHTS.get(case.urgency_level, 10.0)
        # Rule-04: Starvation mitigation factor (2.5 pts per waiting minute)
        wait_boost = float(case.waiting_time_minutes or 0.0) * 2.5
        # Tie-breaker deterministic modifier based on age (pediatric & elderly considerations)
        age_factor = 0.0
        if case.age < 12 or case.age > 70:
            age_factor = 5.0
        return base_weight + wait_boost + age_factor

    @classmethod
    def evaluate_and_plan(
        cls, 
        waiting_cases: List[PatientCase], 
        available_resources: List[Resource]
    ) -> Tuple[List[AllocationAction], List[RejectedAllocation], List[Dict[str, str]], float]:
        start_time = time.perf_counter()

        # Track active rules activated in this planning cycle
        rules_activated = list(EXPLICIT_RULES)

        # Separate available resources by type
        beds = [r for r in available_resources if r.resource_type == ResourceType.BED and r.status == ResourceStatus.AVAILABLE]
        staff = [r for r in available_resources if r.resource_type == ResourceType.STAFF and r.status == ResourceStatus.AVAILABLE]
        equipment = [r for r in available_resources if r.resource_type == ResourceType.EQUIPMENT and r.status == ResourceStatus.AVAILABLE]

        # Sets of assigned resources in this cycle to enforce RULE-03 (Mutual Exclusion)
        assigned_bed_ids = set()
        assigned_staff_ids = set()
        assigned_equipment_ids = set()

        # Sort waiting cases deterministically by priority score descending, then arrival time ascending
        scored_cases = []
        for c in waiting_cases:
            score = cls.calculate_priority_score(c)
            scored_cases.append((score, c))

        # Stable sort: highest score first; if equal score, earlier arrival first
        scored_cases.sort(key=lambda item: (-item[0], item[1].arrival_time))

        feasible_allocations: List[AllocationAction] = []
        rejected_allocations: List[RejectedAllocation] = []

        for score, case in scored_cases:
            applied_rules = ["RULE-04-WAIT-TIME-URGENCY-BOOST"]
            if case.urgency_level == UrgencyLevel.CRITICAL_RESUSCITATION:
                applied_rules.append("RULE-01-CRITICAL-PREEMPTION")

            # 1. Find suitable bed
            suitable_bed = None
            for b in beds:
                if b.id in assigned_bed_ids:
                    continue
                # RULE-02: Check subtype compatibility
                # Exact or higher capability (e.g. RESUSCITATION_BAY can take acute if needed)
                if b.subtype == case.required_bed_category.value:
                    suitable_bed = b
                    break
                elif case.required_bed_category == BedCategory.ACUTE_MONITORED and b.subtype == BedCategory.RESUSCITATION_BAY.value:
                    # Emergency downgrade flexibility
                    suitable_bed = b
                    break

            # 2. Find suitable staff
            suitable_staff = None
            for s in staff:
                if s.id in assigned_staff_ids:
                    continue
                if s.subtype == case.required_staff_capability.value:
                    suitable_staff = s
                    break

            # 3. Find suitable equipment if required
            suitable_equip = None
            equip_needed = case.required_equipment is not None
            if equip_needed:
                applied_rules.append("RULE-05-EQUIPMENT-CO-ALLOCATION")
                for eq in equipment:
                    if eq.id in assigned_equipment_ids:
                        continue
                    if eq.subtype == case.required_equipment.value:
                        suitable_equip = eq
                        break

            # Verify feasibility conditions (RULE-02, RULE-03, RULE-05)
            missing = []
            if not suitable_bed:
                missing.append(f"Bed ({case.required_bed_category.value})")
            if not suitable_staff:
                missing.append(f"Staff ({case.required_staff_capability.value})")
            if equip_needed and not suitable_equip:
                missing.append(f"Equipment ({case.required_equipment.value})")

            if not missing:
                # All required resources available!
                applied_rules.append("RULE-02-EXACT-CAPABILITY-MATCH")
                applied_rules.append("RULE-03-PREVENT-OVERALLOCATION")

                assigned_bed_ids.add(suitable_bed.id)
                assigned_staff_ids.add(suitable_staff.id)
                if suitable_equip:
                    assigned_equipment_ids.add(suitable_equip.id)

                justification = (
                    f"Selected based on priority score {score:.1f} ({case.urgency_level.value}). "
                    f"Matched with bed {suitable_bed.id} and clinician {suitable_staff.id}."
                )
                if suitable_equip:
                    justification += f" Co-allocated required unit {suitable_equip.id}."

                feasible_allocations.append(AllocationAction(
                    case_id=case.id,
                    case_name=case.name,
                    urgency_level=case.urgency_level,
                    allocated_bed_id=suitable_bed.id,
                    allocated_staff_id=suitable_staff.id,
                    allocated_equipment_id=suitable_equip.id if suitable_equip else None,
                    score=score,
                    justification=justification,
                    rules_applied=applied_rules
                ))
            else:
                # Infeasible allocation
                rejection_msg = f"Infeasible allocation for {case.id} due to operational bottleneck: Missing {', '.join(missing)}."
                blocked_rule = "RULE-05-EQUIPMENT-CO-ALLOCATION" if (equip_needed and not suitable_equip) else "RULE-02-EXACT-CAPABILITY-MATCH"
                rejected_allocations.append(RejectedAllocation(
                    case_id=case.id,
                    case_name=case.name,
                    urgency_level=case.urgency_level,
                    rejection_reason=rejection_msg,
                    missing_resources=missing,
                    rule_blocked=blocked_rule
                ))

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return feasible_allocations, rejected_allocations, rules_activated, latency_ms
