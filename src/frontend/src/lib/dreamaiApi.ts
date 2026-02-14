import { getDreamAiApiUrl } from "./dreamaiConfig";

export interface TaskSpec {
  description: string;
  goal: string;
  success_criteria: string[];
  max_steps: number;
  subtasks: unknown[];
  /** Provider-specific fields, e.g. task_description_dict for rl_thor Graph Tasks */
  extra?: Record<string, unknown>;
}

export interface GenerateTaskResponse {
  task: TaskSpec;
  scene_id: string;
  message: string;
  scene_dict?: Record<string, unknown>;
}

export async function generateTask(
  prompt: string,
  maxSteps = 500,
  sceneId?: string
): Promise<GenerateTaskResponse> {
  const url = getDreamAiApiUrl("/api/orchestrator/generate_task");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      max_steps: maxSteps,
      scene_id: sceneId ?? null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `generate_task failed: ${res.status}`);
  }
  return res.json();
}

export interface EvaluateEpisodeRequest {
  total_reward: number;
  steps: number;
  max_steps?: number;
  success: boolean;
}

export async function evaluateEpisode(
  data: EvaluateEpisodeRequest
): Promise<Record<string, unknown>> {
  const url = getDreamAiApiUrl("/api/orchestrator/evaluate_episode");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `evaluate_episode failed: ${res.status}`);
  }
  return res.json();
}

export async function healthCheck(): Promise<{
  status: string;
  environment_initialized?: boolean;
  connected_clients?: number;
}> {
  const url = getDreamAiApiUrl("/health");
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function rlAgentStatus(): Promise<{ running: boolean }> {
  const url = getDreamAiApiUrl("/api/rl/status");
  const res = await fetch(url);
  if (!res.ok) throw new Error(`RL status failed: ${res.status}`);
  return res.json();
}

export interface RLStartOptions {
  policy_mode?: string;
  network_size?: string;
}

export async function rlAgentStart(options?: RLStartOptions): Promise<{ running: boolean }> {
  const url = getDreamAiApiUrl("/api/rl/start");
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(options ?? {}),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `RL start failed: ${res.status}`);
  }
  return res.json();
}

export async function rlModelImport(file: File): Promise<{ ok: boolean }> {
  const url = getDreamAiApiUrl("/api/rl/model/import");
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(url, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Invalid file type");
  }
  return res.json();
}

export async function rlModelExport(): Promise<Blob> {
  const url = getDreamAiApiUrl("/api/rl/model/export");
  const res = await fetch(url);
  if (!res.ok) {
    if (res.status === 404) throw new Error("No model to export");
    throw new Error(`Export failed: ${res.status}`);
  }
  return res.blob();
}

export async function rlAgentStop(): Promise<{ running: boolean }> {
  const url = getDreamAiApiUrl("/api/rl/stop");
  const res = await fetch(url, { method: "POST" });
  if (!res.ok) throw new Error(`RL stop failed: ${res.status}`);
  return res.json();
}
