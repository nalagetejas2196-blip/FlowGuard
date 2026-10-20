import React, { useState, useEffect } from 'react';
import { 
  Activity, Users, Bed, ShieldAlert, Cpu, 
  RotateCw, Plus, AlertTriangle, CheckCircle2, 
  ChevronRight, Clock, FileText, Sparkles, Play, BookOpen, Check
} from 'lucide-react';
import { api } from './api';
import type { 
  PatientCase, ResourceItem, DecisionPlanResponse, 
  ScenarioEventItem, EvaluationResult, AuditLogItem 
} from './types';

export function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'cases' | 'resources' | 'decision' | 'simulation' | 'evaluation' | 'audit'>('overview');
  
  // App State
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [cases, setCases] = useState<PatientCase[]>([]);
  const [resources, setResources] = useState<ResourceItem[]>([]);
  const [latestPlan, setLatestPlan] = useState<DecisionPlanResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [scenarioEvents, setScenarioEvents] = useState<ScenarioEventItem[]>([]);
  const [evaluationHistory, setEvaluationHistory] = useState<EvaluationResult[]>([]);
  
  // UI states
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successToast, setSuccessToast] = useState<string | null>(null);

  // New Case Modal / Form
  const [newCaseModal, setNewCaseModal] = useState(false);
  const [newCaseForm, setNewCaseForm] = useState({
    name: 'Patient #' + Math.floor(100 + Math.random() * 900),
    age: 48,
    chief_complaint: 'Severe retrosternal chest pain with diaphoresis',
    urgency_level: 'EMERGENT',
    required_bed_category: 'ACUTE_MONITORED',
    required_staff_capability: 'EMERGENCY_PHYSICIAN',
    required_equipment: 'CARDIAC_MONITOR'
  });

  // RAG Query
  const [ragQuery, setRagQuery] = useState('Why was Resuscitation Bay prioritized over Stepdown?');
  const [ragResult, setRagResult] = useState<any>(null);
  const [ragLoading, setRagLoading] = useState(false);

  const showNotification = (msg: string) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  const loadData = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const [status, cList, rList, audits, events, evals] = await Promise.all([
        api.getSystemStatus(),
        api.getCases(),
        api.getResources(),
        api.getAuditTrail(),
        api.getScenarioEvents(),
        api.getEvaluationHistory()
      ]);
      setSystemStatus(status);
      setCases(cList);
      setResources(rList);
      setAuditLogs(audits);
      setScenarioEvents(events);
      setEvaluationHistory(evals);
    } catch (err: any) {
      setErrorMsg(err.message || 'Error connecting to FLOWGUARD backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      // Background non-disruptive refresh
      api.getSystemStatus().then(setSystemStatus).catch(() => {});
      api.getCases().then(setCases).catch(() => {});
      api.getResources().then(setResources).catch(() => {});
    }, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleRunPlanning = async () => {
    try {
      setLoading(true);
      const plan = await api.runPlanningCycle('MANUAL_OPTIMIZATION_TRIGGER', true);
      setLatestPlan(plan);
      setActiveTab('decision');
      showNotification(`Optimization completed: ${plan.feasible_allocations.length} allocated, ${plan.rejected_allocations.length} rejected in ${plan.planning_latency_ms.toFixed(1)}ms`);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await api.createCase(newCaseForm);
      setNewCaseModal(false);
      showNotification(`Case "${newCaseForm.name}" created and queued successfully.`);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleResourceStatus = async (resourceId: string, currentStatus: string) => {
    const nextStatus = currentStatus === 'AVAILABLE' ? 'SHORTAGE_MAINTENANCE' : 'AVAILABLE';
    const reason = nextStatus === 'AVAILABLE' ? 'Restored by operations team' : 'Simulated emergency maintenance outage';
    try {
      await api.updateResourceStatus(resourceId, nextStatus, reason);
      showNotification(`Resource ${resourceId} status transitioned to ${nextStatus}.`);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    }
  };

  const handleScenarioInject = async (type: string, desc: string, targetId?: string) => {
    try {
      setLoading(true);
      await api.injectScenarioEvent(type, targetId, desc);
      showNotification(`Scenario Event "${type}" executed.`);
      // Run planning cycle automatically to demonstrate immediate agent replanning
      const plan = await api.runPlanningCycle(`REPLAN_FOLLOWING_${type}`, true);
      setLatestPlan(plan);
      await loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async (scenarioType: string) => {
    try {
      setLoading(true);
      const evalRes = await api.runEvaluation(scenarioType, 15);
      setEvaluationHistory(prev => [evalRes, ...prev]);
      showNotification(`Evaluation complete for ${scenarioType}. Comparative metrics calculated.`);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAskRAG = async () => {
    if (!ragQuery.trim()) return;
    try {
      setRagLoading(true);
      const res = await api.explainDecision(ragQuery, latestPlan?.decision_id);
      setRagResult(res);
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setRagLoading(false);
    }
  };

  const getUrgencyBadge = (level: string) => {
    switch (level) {
      case 'CRITICAL_RESUSCITATION':
        return <span className="px-2 py-0.5 text-xs font-semibold bg-vermilion text-ivory rounded uppercase tracking-wider">Level 1 - Critical</span>;
      case 'EMERGENT':
        return <span className="px-2 py-0.5 text-xs font-medium bg-[#D97736] text-ivory rounded uppercase tracking-wider">Level 2 - Emergent</span>;
      case 'URGENT':
        return <span className="px-2 py-0.5 text-xs font-medium bg-[#A07C2E] text-ivory rounded uppercase tracking-wider">Level 3 - Urgent</span>;
      case 'LESS_URGENT':
        return <span className="px-2 py-0.5 text-xs font-medium bg-[#607D62] text-ivory rounded uppercase tracking-wider">Level 4 - Less Urgent</span>;
      default:
        return <span className="px-2 py-0.5 text-xs font-medium bg-stone-dim text-ivory rounded uppercase tracking-wider">Level 5 - Non-Urgent</span>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return <span className="inline-flex items-center gap-1 text-xs text-[#2E6B34] font-medium bg-[#E3EFE3] px-2 py-0.5 rounded border border-[#C5DEC5]"><Check className="w-3 h-3" /> Available</span>;
      case 'OCCUPIED':
        return <span className="inline-flex items-center gap-1 text-xs text-[#8A5210] font-medium bg-[#FBF0DC] px-2 py-0.5 rounded border border-[#EDDCB6]"><Clock className="w-3 h-3" /> Occupied</span>;
      case 'SHORTAGE_MAINTENANCE':
        return <span className="inline-flex items-center gap-1 text-xs text-vermilion font-medium bg-[#F7E5E2] px-2 py-0.5 rounded border border-[#E9C0B9]"><AlertTriangle className="w-3 h-3" /> Outage / Maint</span>;
      default:
        return <span className="inline-flex items-center gap-1 text-xs text-stone-dim font-medium bg-limestone px-2 py-0.5 rounded">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-ivory text-graphite flex flex-col font-sans">
      {/* Top Banner Disclaimer */}
      <div className="bg-graphite text-ivory px-4 py-1.5 text-xs flex justify-between items-center border-b border-stone-dim">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-vermilion" />
          <span className="font-semibold tracking-wide">FLOWGUARD v1.0 [Team Trauma]</span>
          <span className="text-stone-subtle hidden sm:inline">| Non-Clinical Educational Engineering Simulation — Not for Diagnostic Use</span>
        </div>
        <div className="flex items-center gap-4 text-stone-subtle font-mono text-[11px]">
          <span>LLM Layer: {systemStatus?.ollama_layer?.available ? 'Ollama Online' : 'Deterministic Mode'}</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Engine Ready</span>
        </div>
      </div>

      {/* Primary Header */}
      <header className="bg-limestone-light border-b border-stone-border px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-graphite font-sans">FLOWGUARD</h1>
            <span className="text-xs px-2 py-0.5 rounded bg-limestone font-mono border border-stone-border text-graphite">
              OPS-CONSOLE
            </span>
          </div>
          <p className="text-xs text-stone-dim mt-0.5 font-sans">
            Explainable Emergency Resource Coordination & Dynamic Constraint Solver
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setNewCaseModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-medium bg-limestone hover:bg-limestone-light border border-stone-border text-graphite rounded shadow-sm transition"
          >
            <Plus className="w-4 h-4 text-vermilion" />
            New Simulated Case
          </button>
          
          <button
            onClick={handleRunPlanning}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-vermilion hover:bg-vermilion-hover text-ivory rounded shadow-sm transition disabled:opacity-50"
          >
            <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Run Agent Planning Cycle
          </button>
        </div>
      </header>

      {/* Toast Notification */}
      {successToast && (
        <div className="bg-[#E4ECE3] border-b border-[#BFD5BE] text-[#224A26] px-6 py-2 text-xs flex items-center justify-between">
          <span className="font-medium flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-[#2E6B34]" />
            {successToast}
          </span>
          <button onClick={() => setSuccessToast(null)} className="text-stone-dim hover:text-graphite font-bold">✕</button>
        </div>
      )}

      {/* Error Message */}
      {errorMsg && (
        <div className="bg-[#FBEBE8] border-b border-[#F0BCB4] text-vermilion px-6 py-2 text-xs flex items-center justify-between">
          <span className="font-medium flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {errorMsg}
          </span>
          <button onClick={() => setErrorMsg(null)} className="text-stone-dim hover:text-graphite font-bold">✕</button>
        </div>
      )}

      {/* Main Navigation Tabs */}
      <nav className="bg-ivory border-b border-stone-border px-6 flex gap-6 text-sm font-medium overflow-x-auto">
        {[
          { id: 'overview', label: 'Operations Overview', icon: Activity },
          { id: 'cases', label: `Emergency Cases (${cases.length})`, icon: Users },
          { id: 'resources', label: `Resource Fleet (${resources.length})`, icon: Bed },
          { id: 'decision', label: 'Decision Intelligence', icon: Cpu },
          { id: 'simulation', label: 'Scenario Simulator', icon: Play },
          { id: 'evaluation', label: 'Evaluation Lab', icon: BookOpen },
          { id: 'audit', label: 'Audit Trail', icon: FileText },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-3 flex items-center gap-2 border-b-2 transition text-xs uppercase tracking-wider font-semibold ${
                isActive 
                  ? 'border-vermilion text-vermilion' 
                  : 'border-transparent text-stone-dim hover:text-graphite'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Main Content Body */}
      <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
        {/* ================= SECTION A: OVERVIEW ================= */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* KPI Summary Tiles */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-limestone-light p-4 rounded border border-stone-border">
                <span className="text-xs uppercase tracking-wider text-stone-dim font-medium">Waiting Queue</span>
                <div className="text-3xl font-bold font-mono text-graphite mt-1">
                  {cases.filter(c => c.status === 'WAITING').length}
                </div>
                <span className="text-[11px] text-vermilion font-medium mt-1 inline-block">
                  {cases.filter(c => c.urgency_level === 'CRITICAL_RESUSCITATION' && c.status === 'WAITING').length} critical unallocated
                </span>
              </div>

              <div className="bg-limestone-light p-4 rounded border border-stone-border">
                <span className="text-xs uppercase tracking-wider text-stone-dim font-medium">Available Beds</span>
                <div className="text-3xl font-bold font-mono text-graphite mt-1">
                  {resources.filter(r => r.resource_type === 'BED' && r.status === 'AVAILABLE').length} / {resources.filter(r => r.resource_type === 'BED').length}
                </div>
                <span className="text-[11px] text-stone-dim mt-1 inline-block">Treatment capacity</span>
              </div>

              <div className="bg-limestone-light p-4 rounded border border-stone-border">
                <span className="text-xs uppercase tracking-wider text-stone-dim font-medium">Clinician Fleet</span>
                <div className="text-3xl font-bold font-mono text-graphite mt-1">
                  {resources.filter(r => r.resource_type === 'STAFF' && r.status === 'AVAILABLE').length} / {resources.filter(r => r.resource_type === 'STAFF').length}
                </div>
                <span className="text-[11px] text-stone-dim mt-1 inline-block">Surgeons, MDs & Nurses</span>
              </div>

              <div className="bg-limestone-light p-4 rounded border border-stone-border">
                <span className="text-xs uppercase tracking-wider text-stone-dim font-medium">Equipment Ready</span>
                <div className="text-3xl font-bold font-mono text-graphite mt-1">
                  {resources.filter(r => r.resource_type === 'EQUIPMENT' && r.status === 'AVAILABLE').length} / {resources.filter(r => r.resource_type === 'EQUIPMENT').length}
                </div>
                <span className="text-[11px] text-stone-dim mt-1 inline-block">Ventilators & Monitors</span>
              </div>
            </div>

            {/* Live Queue and Operational Snapshot */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Waiting Queue List */}
              <div className="lg:col-span-2 bg-limestone-light border border-stone-border rounded p-4">
                <div className="flex items-center justify-between pb-3 border-b border-stone-border">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-graphite">High-Priority Waiting Patients</h2>
                  <button onClick={() => setActiveTab('cases')} className="text-xs text-vermilion hover:underline flex items-center gap-1 font-semibold">
                    View All <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
                
                <div className="divide-y divide-stone-border mt-2">
                  {cases.filter(c => c.status === 'WAITING').slice(0, 5).map(c => (
                    <div key={c.id} className="py-3 flex items-start justify-between gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-graphite">{c.id}</span>
                          <span className="text-sm font-semibold text-graphite">{c.name}</span>
                          <span className="text-xs text-stone-dim">({c.age} yrs)</span>
                        </div>
                        <p className="text-xs text-stone-dim line-clamp-1">{c.chief_complaint}</p>
                        <div className="text-[11px] text-stone-dim flex items-center gap-3">
                          <span>Req Bed: <strong className="text-graphite">{c.required_bed_category}</strong></span>
                          <span>Staff: <strong className="text-graphite">{c.required_staff_capability}</strong></span>
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <div>{getUrgencyBadge(c.urgency_level)}</div>
                        <div className="font-mono text-xs text-stone-dim flex items-center justify-end gap-1">
                          <Clock className="w-3 h-3 text-vermilion" /> {c.waiting_time_minutes.toFixed(0)}m waiting
                        </div>
                      </div>
                    </div>
                  ))}
                  {cases.filter(c => c.status === 'WAITING').length === 0 && (
                    <div className="py-8 text-center text-xs text-stone-dim">
                      No cases queued in waiting status.
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Actions & System Info */}
              <div className="space-y-4">
                <div className="bg-limestone-light border border-stone-border rounded p-4">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite mb-3">Quick Scenario Controls</h3>
                  <div className="space-y-2">
                    <button 
                      onClick={() => handleScenarioInject('SURGE_ARRIVAL', 'Sudden influx of 3 mass-casualty victims')}
                      className="w-full text-left px-3 py-2 text-xs bg-ivory hover:bg-limestone border border-stone-border rounded font-medium flex items-center justify-between"
                    >
                      <span>🚨 Inject Surge (3 Critical Cases)</span>
                      <ChevronRight className="w-3 h-3 text-stone-dim" />
                    </button>
                    <button 
                      onClick={() => handleScenarioInject('BED_OUTAGE', 'Bay 1 decontamination alert', 'BED-RESUS-01')}
                      className="w-full text-left px-3 py-2 text-xs bg-ivory hover:bg-limestone border border-stone-border rounded font-medium flex items-center justify-between"
                    >
                      <span>⚠️ Trigger Resus Bay 1 Outage</span>
                      <ChevronRight className="w-3 h-3 text-stone-dim" />
                    </button>
                    <button 
                      onClick={() => handleScenarioInject('RESTORE_RESOURCE', 'Sanitation completed', 'BED-RESUS-01')}
                      className="w-full text-left px-3 py-2 text-xs bg-ivory hover:bg-limestone border border-stone-border rounded font-medium flex items-center justify-between"
                    >
                      <span>✅ Restore Resus Bay 1</span>
                      <ChevronRight className="w-3 h-3 text-stone-dim" />
                    </button>
                  </div>
                </div>

                <div className="bg-limestone-light border border-stone-border rounded p-4 font-mono text-xs space-y-2">
                  <h3 className="font-bold uppercase tracking-wider text-graphite font-sans">Agent Status</h3>
                  <div className="flex justify-between border-b border-stone-border pb-1">
                    <span className="text-stone-dim">Algorithm:</span>
                    <span className="font-semibold text-graphite">Deterministic Rule Engine</span>
                  </div>
                  <div className="flex justify-between border-b border-stone-border pb-1">
                    <span className="text-stone-dim">Rules Loaded:</span>
                    <span className="font-semibold text-graphite">5 Formal Invariants</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-dim">Database:</span>
                    <span className="font-semibold text-emerald-700">SQLite (Persistent)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ================= SECTION B: CASES ================= */}
        {activeTab === 'cases' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-bold text-graphite">Simulated Patient Cases</h2>
                <p className="text-xs text-stone-dim">Synthetic emergency cohort queue with priority rankings</p>
              </div>
              <button
                onClick={() => setNewCaseModal(true)}
                className="px-3 py-1.5 text-xs font-semibold bg-vermilion text-ivory rounded hover:bg-vermilion-hover flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" /> Create Case
              </button>
            </div>

            <div className="bg-limestone-light border border-stone-border rounded overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-limestone border-b border-stone-border text-stone-dim uppercase tracking-wider">
                    <th className="p-3">Case ID</th>
                    <th className="p-3">Presentation</th>
                    <th className="p-3">Urgency Tier</th>
                    <th className="p-3">Required Resources</th>
                    <th className="p-3">Wait Time</th>
                    <th className="p-3">Status</th>
                    <th className="p-3">Assigned Units</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-border">
                  {cases.map(c => (
                    <tr key={c.id} className="hover:bg-ivory/50 transition">
                      <td className="p-3 font-mono font-bold text-graphite">{c.id}</td>
                      <td className="p-3">
                        <div className="font-semibold text-graphite">{c.name} ({c.age}y)</div>
                        <div className="text-stone-dim text-[11px] max-w-xs truncate">{c.chief_complaint}</div>
                      </td>
                      <td className="p-3">{getUrgencyBadge(c.urgency_level)}</td>
                      <td className="p-3 space-y-0.5 text-[11px]">
                        <div>Bed: <span className="font-mono">{c.required_bed_category}</span></div>
                        <div>Staff: <span className="font-mono">{c.required_staff_capability}</span></div>
                        {c.required_equipment && <div>Equip: <span className="font-mono text-vermilion">{c.required_equipment}</span></div>}
                      </td>
                      <td className="p-3 font-mono text-graphite">{c.waiting_time_minutes.toFixed(0)} min</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          c.status === 'ASSIGNED' ? 'bg-[#D3E8D5] text-[#1E5224]' : 'bg-limestone text-graphite'
                        }`}>
                          {c.status}
                        </span>
                      </td>
                      <td className="p-3 font-mono text-[11px] text-stone-dim">
                        {c.assigned_bed_id ? (
                          <div className="text-graphite font-semibold">
                            {c.assigned_bed_id} | {c.assigned_staff_id}
                          </div>
                        ) : (
                          <span>Unassigned</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ================= SECTION C: RESOURCES ================= */}
        {activeTab === 'resources' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-bold text-graphite">Resource Fleets & Fleet Controls</h2>
                <p className="text-xs text-stone-dim">Beds, Clinical Specialists, and Specialized Monitoring Units</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {['BED', 'STAFF', 'EQUIPMENT'].map(type => (
                <div key={type} className="bg-limestone-light border border-stone-border rounded p-4 flex flex-col">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite pb-2 border-b border-stone-border mb-3">
                    {type === 'BED' ? 'Treatment Bays & Beds' : type === 'STAFF' ? 'Clinical Staff' : 'Specialized Equipment'}
                  </h3>
                  <div className="space-y-3 flex-1">
                    {resources.filter(r => r.resource_type === type).map(r => (
                      <div key={r.id} className="p-3 bg-ivory border border-stone-border rounded space-y-2">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-mono text-xs font-bold text-graphite">{r.id}</div>
                            <div className="text-xs font-semibold text-graphite">{r.name}</div>
                            <div className="text-[11px] text-stone-dim font-mono">{r.subtype}</div>
                          </div>
                          <div>{getStatusBadge(r.status)}</div>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-stone-border text-[11px]">
                          <span className="text-stone-dim">{r.location || 'Central Floor'}</span>
                          <button
                            onClick={() => handleToggleResourceStatus(r.id, r.status)}
                            className="text-xs text-vermilion hover:underline font-medium"
                          >
                            {r.status === 'AVAILABLE' ? 'Simulate Outage' : 'Restore'}
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================= SECTION D: DECISION INTELLIGENCE ================= */}
        {activeTab === 'decision' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-bold text-graphite">Explainable Decision Trace</h2>
                <p className="text-xs text-stone-dim">Deterministic rule activations, conflict evaluations, and justification audits</p>
              </div>
              <button
                onClick={handleRunPlanning}
                disabled={loading}
                className="px-3.5 py-1.5 text-xs font-semibold bg-vermilion text-ivory rounded hover:bg-vermilion-hover flex items-center gap-1.5"
              >
                <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                Re-evaluate State
              </button>
            </div>

            {latestPlan ? (
              <div className="space-y-6">
                {/* Latency and Meta Header */}
                <div className="bg-limestone-light border border-stone-border rounded p-4 font-mono text-xs grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div>
                    <span className="text-stone-dim block">Decision ID:</span>
                    <span className="font-bold text-graphite">{latestPlan.decision_id}</span>
                  </div>
                  <div>
                    <span className="text-stone-dim block">Latency:</span>
                    <span className="font-bold text-graphite">{latestPlan.planning_latency_ms.toFixed(2)} ms</span>
                  </div>
                  <div>
                    <span className="text-stone-dim block">Feasible Allocations:</span>
                    <span className="font-bold text-emerald-700">{latestPlan.feasible_allocations.length}</span>
                  </div>
                  <div>
                    <span className="text-stone-dim block">Rejected / Conflicts:</span>
                    <span className="font-bold text-vermilion">{latestPlan.rejected_allocations.length}</span>
                  </div>
                </div>

                {/* Feasible Allocations */}
                <div className="space-y-3">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">Feasible Action Plan</h3>
                  <div className="space-y-3">
                    {latestPlan.feasible_allocations.map((action, idx) => (
                      <div key={idx} className="bg-limestone-light border border-stone-border rounded p-4">
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-bold text-graphite">{action.case_id}</span>
                              <span className="text-sm font-bold text-graphite">{action.case_name}</span>
                              {getUrgencyBadge(action.urgency_level)}
                            </div>
                            <p className="text-xs text-graphite font-sans mt-1">{action.justification}</p>
                          </div>
                          <span className="font-mono text-xs font-bold text-vermilion bg-ivory px-2 py-1 rounded border border-stone-border">
                            Priority Score: {action.score.toFixed(1)}
                          </span>
                        </div>

                        <div className="mt-3 pt-2 border-t border-stone-border flex flex-wrap gap-2 items-center text-[11px] font-mono">
                          <span className="text-stone-dim">Resource Bindings:</span>
                          <span className="bg-ivory px-2 py-0.5 rounded border border-stone-border font-semibold text-graphite">
                            Bed: {action.allocated_bed_id}
                          </span>
                          <span className="bg-ivory px-2 py-0.5 rounded border border-stone-border font-semibold text-graphite">
                            Staff: {action.allocated_staff_id}
                          </span>
                          {action.allocated_equipment_id && (
                            <span className="bg-ivory px-2 py-0.5 rounded border border-stone-border font-semibold text-vermilion">
                              Equip: {action.allocated_equipment_id}
                            </span>
                          )}
                        </div>

                        <div className="mt-2 flex flex-wrap gap-1">
                          {action.rules_applied.map((rule, rIdx) => (
                            <span key={rIdx} className="text-[10px] font-mono bg-limestone text-graphite px-1.5 py-0.5 rounded border border-stone-border">
                              {rule}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                    {latestPlan.feasible_allocations.length === 0 && (
                      <div className="p-4 bg-limestone-light border border-stone-border rounded text-xs text-stone-dim text-center">
                        No feasible allocations identified for current state.
                      </div>
                    )}
                  </div>
                </div>

                {/* Rejected Allocations / Honest Bottlenecks */}
                {latestPlan.rejected_allocations.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-vermilion flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4" /> Operational Bottlenecks & Rejections
                    </h3>
                    <div className="space-y-3">
                      {latestPlan.rejected_allocations.map((rej, idx) => (
                        <div key={idx} className="bg-[#FBF4F3] border border-[#ECD1CD] rounded p-4 text-xs">
                          <div className="flex items-center justify-between">
                            <div className="font-mono font-bold text-graphite flex items-center gap-2">
                              <span>{rej.case_id}</span>
                              <span className="text-graphite font-sans font-semibold">{rej.case_name}</span>
                              {getUrgencyBadge(rej.urgency_level)}
                            </div>
                            <span className="font-mono text-[11px] text-vermilion font-semibold">
                              Blocked by {rej.rule_blocked}
                            </span>
                          </div>
                          <p className="mt-1.5 text-graphite font-sans">{rej.rejection_reason}</p>
                          <div className="mt-2 text-[11px] font-mono text-vermilion">
                            Missing Requirements: {rej.missing_resources.join(', ')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* RAG & Natural Language Operational Explanations */}
                <div className="bg-limestone-light border border-stone-border rounded p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-vermilion" />
                    <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">
                      Operations Knowledge & LLM Explainer
                    </h3>
                  </div>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={ragQuery}
                      onChange={(e) => setRagQuery(e.target.value)}
                      placeholder="Ask why a specific decision or constraint was enforced..."
                      className="flex-1 px-3 py-2 text-xs bg-ivory border border-stone-border rounded focus:outline-none focus:border-vermilion"
                    />
                    <button
                      onClick={handleAskRAG}
                      disabled={ragLoading}
                      className="px-4 py-2 text-xs font-semibold bg-graphite text-ivory rounded hover:bg-stone-dim transition flex items-center gap-1.5"
                    >
                      {ragLoading ? 'Generating...' : 'Explain Decision'}
                    </button>
                  </div>

                  {ragResult && (
                    <div className="mt-4 p-4 bg-ivory border border-stone-border rounded space-y-3">
                      <div className="flex justify-between items-center text-xs font-mono text-stone-dim border-b border-stone-border pb-1">
                        <span>Source Engine: <strong>{ragResult.model_used}</strong></span>
                        <span className="text-vermilion font-sans font-semibold">{ragResult.ollama_status}</span>
                      </div>
                      <p className="text-xs leading-relaxed text-graphite font-sans whitespace-pre-line">
                        {ragResult.explanation}
                      </p>
                      {ragResult.sources && (
                        <div className="pt-2 border-t border-stone-border text-[11px] font-mono text-stone-dim">
                          <span>Grounding Citations:</span>
                          <ul className="list-disc list-inside mt-1 space-y-0.5">
                            {ragResult.sources.map((src: any) => (
                              <li key={src.id}>
                                <strong>{src.id}</strong> — {src.title} ({src.category})
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-12 text-center bg-limestone-light border border-stone-border rounded space-y-3">
                <Cpu className="w-8 h-8 text-stone-dim mx-auto" />
                <p className="text-xs text-stone-dim">No decision trace loaded yet.</p>
                <button
                  onClick={handleRunPlanning}
                  className="px-4 py-2 text-xs font-semibold bg-vermilion text-ivory rounded hover:bg-vermilion-hover"
                >
                  Run Agent Planning Cycle
                </button>
              </div>
            )}
          </div>
        )}

        {/* ================= SECTION E: SIMULATION ================= */}
        {activeTab === 'simulation' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-graphite">Interactive Scenario Simulator</h2>
              <p className="text-xs text-stone-dim">Inject operational perturbations to evaluate dynamic system replanning</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-limestone-light border border-stone-border rounded p-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">Mass-Casualty Influx</h3>
                  <p className="text-xs text-stone-dim mt-1">Introduces 3 high-acuity multi-trauma presentations simultaneously.</p>
                </div>
                <button
                  onClick={() => handleScenarioInject('SURGE_ARRIVAL', 'Sudden influx of 3 mass-casualty victims')}
                  className="mt-4 px-3 py-1.5 text-xs font-semibold bg-vermilion text-ivory rounded hover:bg-vermilion-hover"
                >
                  Trigger Surge
                </button>
              </div>

              <div className="bg-limestone-light border border-stone-border rounded p-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">Resuscitation Bay Outage</h3>
                  <p className="text-xs text-stone-dim mt-1">Takes Bay 1 offline due to urgent contamination sanitation.</p>
                </div>
                <button
                  onClick={() => handleScenarioInject('BED_OUTAGE', 'Bay 1 emergency decontamination', 'BED-RESUS-01')}
                  className="mt-4 px-3 py-1.5 text-xs font-semibold bg-graphite text-ivory rounded hover:bg-stone-dim"
                >
                  Trigger Bay 1 Outage
                </button>
              </div>

              <div className="bg-limestone-light border border-stone-border rounded p-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">Resource Fleet Restoration</h3>
                  <p className="text-xs text-stone-dim mt-1">Returns all offline bays and personnel back to active status.</p>
                </div>
                <button
                  onClick={() => handleScenarioInject('RESTORE_RESOURCE', 'Emergency maintenance completed', 'BED-RESUS-01')}
                  className="mt-4 px-3 py-1.5 text-xs font-semibold bg-[#2E6B34] text-ivory rounded hover:bg-[#25572A]"
                >
                  Restore Fleet
                </button>
              </div>
            </div>

            {/* Event Timeline */}
            <div className="bg-limestone-light border border-stone-border rounded p-4 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-graphite">Simulation Event Log</h3>
              <div className="divide-y divide-stone-border font-mono text-xs">
                {scenarioEvents.map(evt => (
                  <div key={evt.id} className="py-2.5 flex items-center justify-between">
                    <div>
                      <span className="font-bold text-graphite">{evt.event_type}</span>
                      <span className="text-stone-dim ml-2 font-sans">{evt.description}</span>
                    </div>
                    <span className="text-[11px] text-stone-dim">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= SECTION F: EVALUATION LAB ================= */}
        {activeTab === 'evaluation' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-base font-bold text-graphite">Evaluation Laboratory & Benchmarks</h2>
                <p className="text-xs text-stone-dim">Reproducible side-by-side comparison between FLOWGUARD and FIFO Baseline</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleRunEvaluation('STANDARD_ARRIVAL')}
                  className="px-3 py-1.5 text-xs font-semibold bg-limestone hover:bg-ivory border border-stone-border text-graphite rounded"
                >
                  Run Standard
                </button>
                <button
                  onClick={() => handleRunEvaluation('SUDDEN_SURGE')}
                  className="px-3 py-1.5 text-xs font-semibold bg-vermilion text-ivory rounded hover:bg-vermilion-hover"
                >
                  Run Surge Benchmark
                </button>
              </div>
            </div>

            {evaluationHistory.length > 0 ? (
              <div className="space-y-6">
                {evaluationHistory.slice(0, 3).map(ev => (
                  <div key={ev.id} className="bg-limestone-light border border-stone-border rounded p-5 space-y-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-graphite">{ev.id}</span>
                          <span className="font-bold text-sm text-graphite">{ev.scenario_name}</span>
                        </div>
                        <p className="text-xs text-stone-dim font-sans mt-0.5">{ev.scenario_description}</p>
                      </div>
                      <span className="text-[11px] font-mono text-stone-dim">
                        {new Date(ev.created_at).toLocaleTimeString()}
                      </span>
                    </div>

                    {/* Comparison Columns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* FlowGuard Agent */}
                      <div className="bg-ivory border border-stone-border rounded p-4 space-y-3">
                        <div className="flex justify-between items-center border-b border-stone-border pb-1.5">
                          <span className="text-xs font-bold uppercase tracking-wider text-vermilion">
                            FLOWGUARD Agent
                          </span>
                          <span className="text-[10px] font-mono bg-vermilion/10 text-vermilion px-1.5 py-0.5 rounded font-bold">
                            Active
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                          <div>
                            <span className="text-stone-dim block text-[11px]">Allocated Rate:</span>
                            <span className="text-base font-bold text-graphite">{ev.agent_metrics.feasible_allocation_rate_pct}%</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Critical Guarantee:</span>
                            <span className="text-base font-bold text-emerald-700">{ev.agent_metrics.critical_allocation_guarantee_pct}%</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Critical Delayed:</span>
                            <span className="text-base font-bold text-graphite">{ev.agent_metrics.critical_cases_delayed}</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Mean Latency:</span>
                            <span className="text-base font-bold text-graphite">{ev.agent_metrics.mean_decision_latency_ms} ms</span>
                          </div>
                        </div>
                      </div>

                      {/* Baseline FIFO */}
                      <div className="bg-ivory border border-stone-border rounded p-4 space-y-3">
                        <div className="flex justify-between items-center border-b border-stone-border pb-1.5">
                          <span className="text-xs font-bold uppercase tracking-wider text-stone-dim">
                            Baseline (Unweighted FIFO)
                          </span>
                          <span className="text-[10px] font-mono bg-limestone text-graphite px-1.5 py-0.5 rounded">
                            Standard
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                          <div>
                            <span className="text-stone-dim block text-[11px]">Allocated Rate:</span>
                            <span className="text-base font-bold text-graphite">{ev.baseline_metrics.feasible_allocation_rate_pct}%</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Avg Wait Time:</span>
                            <span className="text-base font-bold text-graphite">{ev.baseline_metrics.avg_waiting_minutes}m</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Critical Delayed:</span>
                            <span className="text-base font-bold text-vermilion">{ev.baseline_metrics.critical_cases_delayed}</span>
                          </div>
                          <div>
                            <span className="text-stone-dim block text-[11px]">Unallocated Count:</span>
                            <span className="text-base font-bold text-graphite">{ev.baseline_metrics.unallocated_count}</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Verdict */}
                    <div className="p-3 bg-limestone rounded border border-stone-border text-xs flex items-center justify-between">
                      <span className="text-graphite font-medium">
                        <strong>Outcome:</strong> {ev.comparison_summary.verdict}
                      </span>
                      <span className="font-mono text-emerald-800 text-[11px] font-bold">
                        Safety Constraints Verified ✓
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-12 text-center bg-limestone-light border border-stone-border rounded text-xs text-stone-dim">
                No evaluation experiments executed yet. Click a benchmark scenario above.
              </div>
            )}
          </div>
        )}

        {/* ================= SECTION G: AUDIT TRAIL ================= */}
        {activeTab === 'audit' && (
          <div className="space-y-4">
            <div>
              <h2 className="text-base font-bold text-graphite">Immutable Operational Audit Log</h2>
              <p className="text-xs text-stone-dim">Full operational traceability and decision history recorded to persistent SQLite</p>
            </div>

            <div className="bg-limestone-light border border-stone-border rounded overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-limestone border-b border-stone-border text-stone-dim uppercase tracking-wider font-mono">
                    <th className="p-3">Log ID</th>
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Action Type</th>
                    <th className="p-3">Entity Type</th>
                    <th className="p-3">Entity ID</th>
                    <th className="p-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-border font-mono">
                  {auditLogs.map(log => (
                    <tr key={log.id} className="hover:bg-ivory/50">
                      <td className="p-3 font-bold text-graphite">{log.id}</td>
                      <td className="p-3 text-stone-dim">{new Date(log.timestamp).toLocaleTimeString()}</td>
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-limestone text-graphite border border-stone-border">
                          {log.action_type}
                        </span>
                      </td>
                      <td className="p-3 text-stone-dim">{log.entity_type}</td>
                      <td className="p-3 text-graphite font-semibold">{log.entity_id || '-'}</td>
                      <td className="p-3 font-sans text-stone-dim text-[11px] max-w-xs truncate">
                        {JSON.stringify(log.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* New Case Creation Modal */}
      {newCaseModal && (
        <div className="fixed inset-0 bg-graphite/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-ivory border border-stone-border rounded max-w-md w-full p-6 shadow-xl space-y-4">
            <div className="flex justify-between items-center border-b border-stone-border pb-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-graphite font-sans">
                Create Synthetic Patient Presentation
              </h3>
              <button onClick={() => setNewCaseModal(false)} className="text-stone-dim hover:text-graphite font-bold">✕</button>
            </div>

            <form onSubmit={handleCreateCase} className="space-y-3 text-xs">
              <div>
                <label className="block text-stone-dim font-medium mb-1">Patient Identifier Name</label>
                <input
                  type="text"
                  required
                  value={newCaseForm.name}
                  onChange={e => setNewCaseForm({ ...newCaseForm, name: e.target.value })}
                  className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-stone-dim font-medium mb-1">Age</label>
                  <input
                    type="number"
                    min="1"
                    max="110"
                    value={newCaseForm.age}
                    onChange={e => setNewCaseForm({ ...newCaseForm, age: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                  />
                </div>
                <div>
                  <label className="block text-stone-dim font-medium mb-1">Urgency Tier</label>
                  <select
                    value={newCaseForm.urgency_level}
                    onChange={e => setNewCaseForm({ ...newCaseForm, urgency_level: e.target.value })}
                    className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                  >
                    <option value="CRITICAL_RESUSCITATION">Level 1 - Critical</option>
                    <option value="EMERGENT">Level 2 - Emergent</option>
                    <option value="URGENT">Level 3 - Urgent</option>
                    <option value="LESS_URGENT">Level 4 - Less Urgent</option>
                    <option value="NON_URGENT">Level 5 - Non-Urgent</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-stone-dim font-medium mb-1">Chief Presentation Complaint</label>
                <textarea
                  rows={2}
                  required
                  value={newCaseForm.chief_complaint}
                  onChange={e => setNewCaseForm({ ...newCaseForm, chief_complaint: e.target.value })}
                  className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-stone-dim font-medium mb-1">Required Bed Category</label>
                  <select
                    value={newCaseForm.required_bed_category}
                    onChange={e => setNewCaseForm({ ...newCaseForm, required_bed_category: e.target.value })}
                    className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                  >
                    <option value="RESUSCITATION_BAY">Resuscitation Bay</option>
                    <option value="ACUTE_MONITORED">Acute Monitored</option>
                    <option value="STEPDOWN">Stepdown Care</option>
                    <option value="ISOLATION">Isolation Bay</option>
                  </select>
                </div>
                <div>
                  <label className="block text-stone-dim font-medium mb-1">Required Clinician</label>
                  <select
                    value={newCaseForm.required_staff_capability}
                    onChange={e => setNewCaseForm({ ...newCaseForm, required_staff_capability: e.target.value })}
                    className="w-full px-3 py-1.5 bg-limestone-light border border-stone-border rounded focus:outline-none focus:border-vermilion"
                  >
                    <option value="TRAUMA_SURGEON">Trauma Surgeon</option>
                    <option value="EMERGENCY_PHYSICIAN">Emergency Physician</option>
                    <option value="TRIAGE_NURSE">Triage Nurse</option>
                    <option value="RESPIRATORY_THERAPIST">Respiratory Therapist</option>
                  </select>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-border flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setNewCaseModal(false)}
                  className="px-3 py-1.5 bg-limestone hover:bg-stone-border rounded text-graphite font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-vermilion hover:bg-vermilion-hover text-ivory rounded font-semibold"
                >
                  Save & Queue Case
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
export default App;
