export type UrgencyLevel = 
  | 'CRITICAL_RESUSCITATION'
  | 'EMERGENT'
  | 'URGENT'
  | 'LESS_URGENT'
  | 'NON_URGENT';

export type CaseStatus = 
  | 'WAITING'
  | 'ALLOCATING'
  | 'ASSIGNED'
  | 'IN_TREATMENT'
  | 'DISCHARGED';

export type ResourceType = 'BED' | 'STAFF' | 'EQUIPMENT';
export type ResourceStatus = 'AVAILABLE' | 'OCCUPIED' | 'SHORTAGE_MAINTENANCE' | 'OFFLINE';

export interface PatientCase {
  id: string;
  name: string;
  age: number;
  chief_complaint: string;
  urgency_level: UrgencyLevel;
  status: CaseStatus;
  required_bed_category: string;
  required_staff_capability: string;
  required_equipment: string | null;
  arrival_time: string;
  waiting_time_minutes: number;
  simulated_priority_score: number;
  assigned_bed_id: string | null;
  assigned_staff_id: string | null;
  assigned_equipment_id: string | null;
}

export interface ResourceItem {
  id: string;
  name: string;
  resource_type: ResourceType;
  subtype: string;
  status: ResourceStatus;
  location: string | null;
  is_active: boolean;
  current_case_id: string | null;
  last_status_change: string;
}

export interface AllocationAction {
  case_id: string;
  case_name: string;
  urgency_level: UrgencyLevel;
  allocated_bed_id: string | null;
  allocated_staff_id: string | null;
  allocated_equipment_id: string | null;
  score: number;
  justification: string;
  rules_applied: string[];
}

export interface RejectedAllocation {
  case_id: string;
  case_name: string;
  urgency_level: UrgencyLevel;
  rejection_reason: string;
  missing_resources: string[];
  rule_blocked: string;
}

export interface DecisionPlanResponse {
  decision_id: string;
  timestamp: string;
  trigger_reason: string;
  total_waiting: number;
  feasible_allocations: AllocationAction[];
  rejected_allocations: RejectedAllocation[];
  rules_activated: { id: string; name: string; description: string }[];
  planning_latency_ms: number;
  conflict_detected: boolean;
}

export interface ScenarioEventItem {
  id: string;
  timestamp: string;
  simulated_time_tick: number;
  event_type: string;
  target_id: string | null;
  description: string;
  payload: any;
}

export interface EvaluationResult {
  id: string;
  created_at: string;
  scenario_name: string;
  scenario_description: string;
  simulation_ticks: number;
  agent_metrics: {
    allocated_count: number;
    unallocated_count: number;
    critical_cases_delayed: number;
    critical_allocation_guarantee_pct: number;
    feasible_allocation_rate_pct: number;
    mean_decision_latency_ms: number;
    rules_evaluated_count: number;
  };
  baseline_metrics: {
    allocated_count: number;
    unallocated_count: number;
    critical_cases_delayed: number;
    avg_waiting_minutes: number;
    feasible_allocation_rate_pct: number;
  };
  comparison_summary: {
    scenario: string;
    total_cohort_size: number;
    critical_cases_total: number;
    critical_delay_reduction: number;
    verdict: string;
    safety_boundary_compliance: boolean;
  };
}

export interface AuditLogItem {
  id: string;
  timestamp: string;
  action_type: string;
  entity_type: string;
  entity_id: string | null;
  details: any;
}
