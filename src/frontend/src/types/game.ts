export interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

export interface RewardHistoryPoint {
  value: number;
}
