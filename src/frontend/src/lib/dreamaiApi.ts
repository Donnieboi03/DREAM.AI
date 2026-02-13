import { getDreamAiApiUrl } from "./dreamaiConfig";

export interface TaskSpec {
  description: string;
  goal: string;
  success_criteria: string[];
  max_steps: number;
  subtasks: unknown[];
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
