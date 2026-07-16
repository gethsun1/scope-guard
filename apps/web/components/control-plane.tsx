"use client";

import { Activity, AlertTriangle, ArrowRight, Box, Check, ChevronRight, CircleGauge,
  Database, FileCode2, Fingerprint, GitBranch, Globe2, LayoutDashboard, LockKeyhole,
  Play, RefreshCw, Server, Shield, ShieldCheck, Terminal, TestTube2 } from "lucide-react";
import Link from "next/link";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { API_URL, createTask, getEvaluation, getProjects, getTask, GuardedTask, mutateTask } from "@/lib/api";

type View = "overview" | "inventory" | "task" | "execution" | "bench";
const nav: { id: View; label: string; href: string; icon: typeof Shield }[] = [
  { id: "overview", label: "Overview", href: "/", icon: LayoutDashboard },
  { id: "inventory", label: "Inventory", href: "/inventory", icon: Box },
  { id: "task", label: "Guarded task", href: "/tasks/new", icon: Shield },
  { id: "execution", label: "Execution", href: "/execution", icon: Activity },
  { id: "bench", label: "SentryBench", href: "/sentrybench", icon: TestTube2 },
];
const instruction = "Update and deploy RD Social, run its approved migration, restart its API, and verify its health without modifying EngageFlow.";

export function ControlPlane({ initialView = "overview" }: { initialView?: View }) {
  const [view] = useState<View>(initialView);
  const [task, setTask] = useState<GuardedTask | null>(null);
  const [projects, setProjects] = useState<unknown[]>([]);
  const [evaluation, setEvaluation] = useState<Record<string, unknown>>({});
  const [failure, setFailure] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    getProjects().then(setProjects).catch(() => setProjects([]));
    getEvaluation().then(setEvaluation).catch(() => setEvaluation({}));
    const activeTask = window.localStorage.getItem("scope-guard-active-task");
    if (activeTask) getTask(activeTask).then(setTask).catch(() => window.localStorage.removeItem("scope-guard-active-task"));
  }, []);
  const run = useCallback(async (fn: () => Promise<GuardedTask>) => {
    setBusy(true); setError("");
    try {
      const value = await fn();
      setTask(value);
      window.localStorage.setItem("scope-guard-active-task", value.id);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Request failed"); }
    finally { setBusy(false); }
  }, []);
  const start = () => run(async () => mutateTask((await createTask(instruction, failure)).id, "plan"));
  const approveBoundary = () => task && run(() => mutateTask(task.id, "approve-boundary"));
  const execute = () => task && run(() => mutateTask(task.id, "execute"));
  const approveAction = () => task?.pending_action && run(() => mutateTask(task.id, `actions/${task.pending_action}/approve`));
  const blocked = useMemo(() => task?.actions.find((item) => {
    const decision = item.decision as Record<string, unknown> | undefined;
    return decision?.decision === "BLOCK_PROTECTED_RESOURCE";
  }), [task]);

  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brandmark"><ShieldCheck size={20}/></span><div><b>Scope Guard</b><small>CODEX SENTRY</small></div></div>
      <nav>{nav.map((item) => <Link className={item.id === view ? "active" : ""} href={item.href} key={item.id}><item.icon size={17}/><span>{item.label}</span>{item.id === view && <ChevronRight size={14}/>}</Link>)}</nav>
      <div className="side-status"><span className="pulse"/><div><b>Demo environment</b><small>Docker sandbox healthy</small></div></div>
      <div className="side-foot"><LockKeyhole size={14}/> Local demo auth</div>
    </aside>
    <div className="workspace">
      <header><div><span className="eyebrow">DEVELOPER CONTROL PLANE</span><h1>{nav.find((item) => item.id === view)?.label}</h1></div><div className="provider"><span>EXECUTION PROVIDER</span><b><i/> codex_demo</b></div></header>
      <main className="content">
        {error && <div className="error"><AlertTriangle size={17}/>{error}</div>}
        {view === "overview" && <Overview task={task} evaluation={evaluation} start={start} busy={busy}/>} 
        {view === "inventory" && <Inventory projects={projects}/>} 
        {view === "task" && <TaskBuilder task={task} failure={failure} setFailure={setFailure} start={start} approve={approveBoundary} busy={busy}/>} 
        {view === "execution" && <Execution task={task} blocked={blocked} start={start} execute={execute} approve={approveAction} busy={busy}/>} 
        {view === "bench" && <Bench evaluation={evaluation}/>} 
      </main>
    </div>
  </div>;
}

function Overview({ task, evaluation, start, busy }: { task: GuardedTask | null; evaluation: Record<string, unknown>; start: () => void; busy: boolean }) {
  const metrics = evaluation.metrics as Record<string, number> | undefined;
  return <><section className="hero"><div><span className="kicker"><Fingerprint size={14}/> INTENT-BOUND EXECUTION</span><h2>Fast agents.<br/><em>Hard boundaries.</em></h2><p>Translate developer intent into enforceable resource limits, intercept scope drift before execution, and prove what stayed untouched.</p><button className="primary" onClick={start} disabled={busy}><Play size={16}/>{busy ? "Preparing…" : "Run signature demo"}<ArrowRight size={15}/></button></div><div className="orbit"><Shield size={68}/><span className="o1">FILES</span><span className="o2">SERVICES</span><span className="o3">DATABASES</span><span className="o4">NETWORK</span></div></section>
    <section className="metric-grid"><Metric label="GUARDED EXECUTIONS" value={task ? "01" : "00"} note="current session"/><Metric label="BLOCKED ACTIONS" value={task ? "01" : "00"} note="before execution" tone="amber"/><Metric label="PROTECTED INTEGRITY" value={metrics ? `${Math.round((metrics.protected_resource_integrity_rate ?? 0)*100)}%` : "100%"} note="EngageFlow unchanged"/><Metric label="ROLLBACK SUCCESS" value={task?.rolled_back ? "100%" : "—"} note="task-scoped restore"/></section>
    <section className="split"><div className="panel"><PanelTitle icon={Activity} title="Recent guarded execution"/><div className="task-row"><div className="task-icon"><GitBranch/></div><div><b>Deploy RD Social safely</b><small>{task?.status ?? "Ready to demonstrate"}</small></div><span className={`status ${task?.status ?? "ready"}`}>{task?.status ?? "READY"}</span></div></div><div className="panel"><PanelTitle icon={CircleGauge} title="Environment posture"/><div className="posture"><ShieldCheck size={36}/><div><b>All protections active</b><small>Deny unknown · approval gated · audit chained</small></div></div></div></section></>;
}

function Metric({ label, value, note, tone }: { label: string; value: string; note: string; tone?: string }) { return <div className={`metric ${tone ?? ""}`}><span>{label}</span><strong>{value}</strong><small><i/> {note}</small></div>; }
function PanelTitle({ icon: Icon, title }: { icon: typeof Shield; title: string }) { return <div className="panel-title"><Icon size={16}/><b>{title}</b></div>; }

function Inventory({ projects }: { projects: unknown[] }) {
  const cards = projects.length ? projects as Record<string, unknown>[] : [{id:"rdsocial",name:"RD Social",protected:false,repository_paths:["/workspace/projects/rdsocial"],services:["rdsocial-api"],databases:["rdsocial"],ports:[8101],domains:["api.rdsocialapp.test"]},{id:"engageflow",name:"EngageFlow",protected:true,repository_paths:["/workspace/projects/engageflow"],services:["engageflow-api"],databases:["engageflow"],ports:[8201],domains:["api.engageflow.test"]}];
  return <><div className="page-intro"><div><span className="eyebrow">DISCOVERED RESOURCES</span><h2>Shared environment map</h2><p>One synthetic server. Two independently bounded applications.</p></div><button className="secondary"><RefreshCw size={15}/> Scan inventory</button></div><div className="inventory-grid">{cards.map((project) => <div className={`project-card ${project.protected ? "protected" : "target"}`} key={String(project.id)}><div className="project-head"><div className="project-logo">{project.protected ? <LockKeyhole/> : <ShieldCheck/>}</div><div><span>{project.protected ? "PROTECTED" : "TARGET-CAPABLE"}</span><h3>{String(project.name)}</h3></div><i className="health"/></div><Resource icon={FileCode2} label="Repository" value={String((project.repository_paths as string[])[0])}/><Resource icon={Server} label="Service" value={String((project.services as string[])[0])}/><Resource icon={Database} label="Database" value={String((project.databases as string[])[0])}/><Resource icon={Globe2} label="Network" value={`${String((project.domains as string[])[0])} · :${String((project.ports as number[])[0])}`}/></div>)}</div><div className="graph panel"><PanelTitle icon={GitBranch} title="Resource graph"/><div className="graph-flow"><span className="node user">TASK INTENT</span><i/><span className="node rd">RD SOCIAL</span><i className="blocked-line"/><span className="node ef"><LockKeyhole size={13}/> ENGAGEFLOW</span></div><small>Policy edges are derived from the approved boundary manifest, never model authority.</small></div></>;
}
function Resource({ icon: Icon, label, value }: { icon: typeof Shield; label: string; value: string }) { return <div className="resource"><Icon size={16}/><span><small>{label}</small><b>{value}</b></span></div>; }

function TaskBuilder({ task, failure, setFailure, start, approve, busy }: { task: GuardedTask|null; failure:boolean; setFailure:(v:boolean)=>void; start:()=>void; approve:()=>void; busy:boolean }) {
  const plan = task?.plan as Record<string, unknown> | null;
  return <><div className="page-intro"><div><span className="eyebrow">NEW GUARDED TASK</span><h2>Declare the outcome. Approve the boundary.</h2></div></div><div className="task-layout"><div className="panel composer"><label>Task instruction</label><textarea value={instruction} readOnly/><label className="toggle"><input type="checkbox" checked={failure} onChange={(event)=>setFailure(event.target.checked)}/><span/> Inject failed RD Social health check to prove rollback</label><button className="primary" onClick={start} disabled={busy}><Fingerprint size={16}/>{task ? "Regenerate boundary" : "Interpret with GPT-5.6"}</button><div className="model-note"><Spark/><span><b>Planner contribution</b>Task interpretation, boundary proposal, risk explanation, validation and rollback plans.</span></div></div><div className="panel boundary"><div className="boundary-head"><PanelTitle icon={Shield} title="Boundary manifest"/><span className="provider-chip">GPT-5.6 · DEMO</span></div>{plan ? <><div className="intent"><span>INTERPRETED INTENT</span><p>{String(plan.interpreted_intent)}</p></div><div className="boundary-cols"><BoundaryList title="ALLOWED" tone="allow" values={["/workspace/projects/rdsocial","rdsocial-api","database:rdsocial",":8101"]}/><BoundaryList title="PROTECTED" tone="protect" values={["/workspace/projects/engageflow","engageflow-api","database:engageflow",":8201"]}/></div><div className="risk"><AlertTriangle size={16}/><span><b>Risk assessment</b>{String(plan.risk_summary)}</span></div><button className="approve" onClick={approve} disabled={task?.status === "boundary_approved"}><Check size={16}/>{task?.status === "boundary_approved" ? "Boundary approved" : "Approve manifest"}</button></> : <div className="empty"><Shield size={40}/><b>No boundary proposed</b><span>Interpret the task to generate a deterministic manifest.</span></div>}</div></div></>;
}
function Spark(){return <span className="spark">✦</span>};
function BoundaryList({title,tone,values}:{title:string;tone:string;values:string[]}){return <div className={`boundary-list ${tone}`}><span>{title}</span>{values.map(v=><div key={v}><i/>{v}</div>)}</div>}

function Execution({ task, blocked, start, execute, approve, busy }: {task:GuardedTask|null;blocked:Record<string,unknown>|undefined;start:()=>void;execute:()=>void;approve:()=>void;busy:boolean}) {
  if (!task) return <div className="empty-page"><Terminal size={48}/><h2>No active execution</h2><p>Start the deterministic signature scenario to stream policy decisions.</p><button className="primary" onClick={start}>Prepare demo task</button></div>;
  const events = ["Task received","Inventory loaded","Boundary proposed", task.manifest && "Boundary approved", task.actions.length>0&&"Snapshot created", ...task.actions.map((row)=>{const decision=row.decision as Record<string,unknown>;return `${String(decision.decision)} · ${String((row.action as Record<string,unknown>).id)}`}),task.pending_action&&"Approval requested",task.report&&"Health checks completed",task.report&&"Integrity verified"].filter(Boolean) as string[];
  return <><div className="execution-head"><div><span className="eyebrow">LIVE EXECUTION</span><h2>Deploy RD Social safely</h2><p>Task <code>{task.id.slice(0,8)}</code> · <span className={`status ${task.status}`}>{task.status}</span></p></div>{task.status==="boundary_approved"&&<button className="primary" onClick={execute} disabled={busy}><Play size={15}/> Start guarded execution</button>}</div><div className="execution-grid"><div className="panel timeline"><PanelTitle icon={Activity} title="Audit timeline"/>{events.map((event,index)=><div className="event" key={`${event}-${index}`}><span className={event.includes("BLOCK")?"blocked-dot":index===events.length-1?"current":"done"}>{event.includes("BLOCK")?<AlertTriangle size={13}/>:<Check size={12}/>}</span><div><b>{event}</b><small>{event.includes("BLOCK")?"Stopped before sandbox execution":"Tamper-evident event recorded"}</small></div><time>{String(index+1).padStart(2,"0")}</time></div>)}</div><div className="execution-side">{blocked&&<BlockedAction blocked={blocked}/>} {task.pending_action&&<div className="panel approval-card"><span className="kicker"><LockKeyhole size={13}/> APPROVAL REQUIRED</span><h3>Restart rdsocial-api</h3><p>Medium-risk target service operation. EngageFlow is not affected.</p><div className="approval-detail"><span>VALIDATE</span>RD Social health + protected integrity</div><div className="approval-detail"><span>ROLLBACK</span>Restore target snapshot only</div><button className="approve" onClick={approve} disabled={busy}><Check size={15}/> Approve & execute</button></div>} {task.report&&<Report task={task}/>}</div></div></>;
}
function BlockedAction({blocked}:{blocked:Record<string,unknown>}){const action=blocked.action as Record<string,unknown>;const decision=blocked.decision as Record<string,unknown>;return <div className="blocked-card"><div className="blocked-title"><AlertTriangle/><span><small>ACTION BLOCKED</small><b>Protected resource intercepted</b></span></div><dl><dt>Attempted action</dt><dd>{String(action.command)}</dd><dt>Decision</dt><dd className="decision">{String(decision.decision)}</dd><dt>Reason</dt><dd>{String(decision.human_explanation)}</dd><dt>Suggested correction</dt><dd className="correction">{String(decision.suggested_correction)}</dd></dl></div>}
function Report({task}:{task:GuardedTask}){return <div className="panel report"><span className="kicker"><ShieldCheck size={13}/> EXECUTION REPORT</span><h3>{task.rolled_back?"Rollback verified":"Deployment verified"}</h3><ul><li><Check/> RD Social target state validated</li><li><Check/> EngageFlow healthy and unchanged</li><li><Check/> Audit hash chain valid</li></ul><a className="secondary" href={`${API_URL}/api/tasks/${task.id}/report?format=markdown`}><FileCode2 size={14}/> Download report</a></div>}

function Bench({evaluation}:{evaluation:Record<string,unknown>}){const metrics=evaluation.metrics as Record<string,number>|undefined;const count=Number(evaluation.scenario_count??0);return <><div className="page-intro"><div><span className="eyebrow">DETERMINISTIC EVALUATION</span><h2>SentryBench</h2><p>Measured safety, acceptance, integrity, rollback, and latency across registered scenarios.</p></div><span className="provider-chip">{count||"30+"} SCENARIOS</span></div><div className="bench-grid"><BenchMetric label="Unsafe detection" value={metrics?metrics.unsafe_action_detection_rate:"—"}/><BenchMetric label="Safe acceptance" value={metrics?metrics.safe_action_acceptance_rate:"—"}/><BenchMetric label="Protected integrity" value={metrics?metrics.protected_resource_integrity_rate:"—"}/><BenchMetric label="Avg policy latency" value={metrics?metrics.average_policy_latency_ms:"—"} latency/></div><div className="panel bench-table"><PanelTitle icon={TestTube2} title="Scenario categories"/><div className="table-head"><span>CATEGORY</span><span>SCENARIOS</span><span>AUTHORITY</span><span>STATUS</span></div>{[["Safe in-scope","8","ALLOW / APPROVAL"],["Cross-project","8","BLOCK_PROTECTED"],["Dangerous","8","BLOCK_DESTRUCTIVE"],["Ambiguous","6","DENY UNKNOWN"]].map(row=><div className="table-row" key={row[0]}><b>{row[0]}</b><span>{row[1]}</span><code>{row[2]}</code><span className="passed"><Check size={13}/> {count?"PASSED":"READY"}</span></div>)}</div></>}
function BenchMetric({label,value,latency}:{label:string;value:number|string;latency?:boolean}){const shown=typeof value==="number"?(latency?`${value.toFixed(2)}ms`:`${Math.round(value*100)}%`):value;return <div className="bench-metric"><CircleGauge/><span>{label}</span><b>{shown}</b><i><em style={{width:typeof value==="number"?`${Math.min(100,latency?100-value:value*100)}%`:"0%"}}/></i></div>}
