import type { 
  PatientCase, ResourceItem, DecisionPlanResponse, 
  ScenarioEventItem, EvaluationResult, AuditLogItem 
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  // System
  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/system/status`);
    if (!res.ok) throw new Error('Failed to fetch system status');
    return res.json();
  },

  async seedDatabase(force = false) {
    const res = await fetch(`${API_BASE}/system/seed?force_reset=${force}`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to seed database');
    return res.json();
  },

  // Cases
  async getCases(status?: string): Promise<PatientCase[]> {
    const url = status ? `${API_BASE}/cases?status=${status}` : `${API_BASE}/cases`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch cases');
    return res.json();
  },

  async createCase(data: any): Promise<PatientCase> {
    const res = await fetch(`${API_BASE}/cases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create case');
    return res.json();
  },

  // Resources
  async getResources(type?: string): Promise<ResourceItem[]> {
    const url = type ? `${API_BASE}/resources?resource_type=${type}` : `${API_BASE}/resources`;
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to fetch resources');
    return res.json();
  },

  async updateResourceStatus(id: string, status: string, reason?: string): Promise<ResourceItem> {
    const res = await fetch(`${API_BASE}/resources/${id}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, reason }),
    });
    if (!res.ok) throw new Error('Failed to update resource');
    return res.json();
  },

  // Decisions
  async runPlanningCycle(triggerReason = 'MANUAL_OPTIMIZATION', apply = true): Promise<DecisionPlanResponse> {
    const res = await fetch(`${API_BASE}/decisions/plan?trigger_reason=${encodeURIComponent(triggerReason)}&apply_allocations=${apply}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to execute planning cycle');
    return res.json();
  },

  async getDecisionHistory(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/decisions/history`);
    if (!res.ok) throw new Error('Failed to fetch decision history');
    return res.json();
  },

  // Simulation
  async injectScenarioEvent(event_type: string, target_id?: string, description = '', payload?: any): Promise<ScenarioEventItem> {
    const res = await fetch(`${API_BASE}/simulation/event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type, target_id, description, payload }),
    });
    if (!res.ok) throw new Error('Failed to inject scenario event');
    return res.json();
  },

  async getScenarioEvents(): Promise<ScenarioEventItem[]> {
    const res = await fetch(`${API_BASE}/simulation/events`);
    if (!res.ok) throw new Error('Failed to fetch scenario events');
    return res.json();
  },

  // Evaluation
  async runEvaluation(scenario_type: string, ticks = 15): Promise<EvaluationResult> {
    const res = await fetch(`${API_BASE}/evaluation/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_type, simulation_ticks: ticks }),
    });
    if (!res.ok) throw new Error('Failed to run evaluation');
    return res.json();
  },

  async getEvaluationHistory(): Promise<EvaluationResult[]> {
    const res = await fetch(`${API_BASE}/evaluation/history`);
    if (!res.ok) throw new Error('Failed to fetch evaluation history');
    return res.json();
  },

  // Audit
  async getAuditTrail(): Promise<AuditLogItem[]> {
    const res = await fetch(`${API_BASE}/audit`);
    if (!res.ok) throw new Error('Failed to fetch audit trail');
    return res.json();
  },

  // RAG
  async explainDecision(query: string, decisionId?: string) {
    const res = await fetch(`${API_BASE}/explain`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, decision_id: decisionId }),
    });
    if (!res.ok) throw new Error('Failed to generate explanation');
    return res.json();
  }
};
