export interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
  /** Progress toward goal (0..max_task_advancement). rl_thor-style. */
  task_advancement?: number | null;
  /** Max possible task advancement. rl_thor-style. */
  max_task_advancement?: number | null;
  /** Task completed. rl_thor-style. */
  is_success?: boolean | null;
  /** Task type name, e.g. "PlaceIn", "Pickup". rl_thor-style. */
  task_type?: string | null;
  /** Who controls the agent: "user" or "agent". Derived from process state; kept for display only. */
  control_mode?: "user" | "agent";
}

export interface RewardHistoryPoint {
  value: number;
}
