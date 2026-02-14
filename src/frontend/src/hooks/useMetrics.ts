import { useState, useCallback } from "react";
import type { GameMetrics, RewardHistoryPoint } from "@/types/game";

const MAX_REWARD_HISTORY = 60;

export function useMetrics() {
  const [metrics, setMetricsState] = useState<GameMetrics | null>(null);
  const [rewardHistory, setRewardHistory] = useState<RewardHistoryPoint[]>([]);

  const updateMetrics = useCallback((m: GameMetrics) => {
    setMetricsState(m);
    setRewardHistory((prev) => {
      const lastVal = prev[prev.length - 1]?.value;
      if (lastVal === m.episode_reward) return prev;
      return [
        ...prev.slice(-(MAX_REWARD_HISTORY - 1)),
        { value: m.episode_reward },
      ];
    });
  }, []);

  const clearMetrics = useCallback(() => {
    setMetricsState(null);
    setRewardHistory([]);
  }, []);

  const setMetrics = useCallback((m: GameMetrics | null) => {
    setMetricsState(m);
    if (m) {
      setRewardHistory((prev) => [
        ...prev.slice(-(MAX_REWARD_HISTORY - 1)),
        { value: m.episode_reward },
      ]);
    } else {
      setRewardHistory([]);
    }
  }, []);

  const appendReward = useCallback((value: number) => {
    setRewardHistory((prev) => [
      ...prev.slice(-(MAX_REWARD_HISTORY - 1)),
      { value },
    ]);
  }, []);

  return {
    metrics,
    rewardHistory,
    updateMetrics,
    clearMetrics,
    setMetrics,
    appendReward,
  };
}
