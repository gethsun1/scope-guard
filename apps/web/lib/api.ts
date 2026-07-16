import { z } from "zod";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const token = "scope-guard-demo";

export const ResourceSchema = z.object({
  type: z.string(), identifier: z.string(), project_id: z.string().nullable(), protected: z.boolean(),
});

export const TaskSchema = z.object({
  id: z.string(), instruction: z.string(), failure_injection: z.boolean(), status: z.string(),
  provider: z.string(), plan: z.record(z.string(), z.unknown()).nullable(),
  manifest: z.record(z.string(), z.unknown()).nullable(), actions: z.array(z.record(z.string(), z.unknown())),
  pending_action: z.string().nullable(), rolled_back: z.boolean(),
  report: z.record(z.string(), z.unknown()).nullable(),
});
export type GuardedTask = z.infer<typeof TaskSchema>;

async function request(path: string, init: RequestInit = {}): Promise<unknown> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Demo-Token": token, ...init.headers },
  });
  if (!response.ok) throw new Error(`Scope Guard API returned ${response.status}`);
  return response.json();
}

export async function createTask(instruction: string, failure: boolean): Promise<GuardedTask> {
  return TaskSchema.parse(await request("/api/tasks", { method: "POST", body: JSON.stringify({ instruction, failure_injection: failure }) }));
}

export async function mutateTask(taskId: string, operation: string): Promise<GuardedTask> {
  return TaskSchema.parse(await request(`/api/tasks/${taskId}/${operation}`, { method: "POST" }));
}

export async function getTask(taskId: string): Promise<GuardedTask> {
  return TaskSchema.parse(await request(`/api/tasks/${taskId}`));
}

export async function getProjects(): Promise<unknown[]> {
  return z.array(z.record(z.string(), z.unknown())).parse(await request("/api/projects"));
}

export async function scanInventory(): Promise<unknown[]> {
  const result = z.object({ projects: z.array(z.record(z.string(), z.unknown())) })
    .parse(await request("/api/inventory/scan", { method: "POST" }));
  return result.projects;
}

export async function getDemoStatus(): Promise<Record<string, unknown>> {
  return z.record(z.string(), z.unknown()).parse(await request("/api/demo/status"));
}

export async function getEvaluation(): Promise<Record<string, unknown>> {
  return z.record(z.string(), z.unknown()).parse(await request("/api/evaluations/latest"));
}
