import React, { useState, useRef, useCallback } from "react";
import GameViewport from "./components/GameViewport";
import {
  PromptBox,
  MetricsDisplay,
  ActionPanel,
} from "./components/UIOverlays";

interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

function App() {
  const [metrics, setMetrics] = useState<GameMetrics>({
    agent_position: null,
    agent_rotation: null,
    episode_reward: 0,
    step_count: 0,
    last_action_success: true,
  });
  const [isProcessingTask, setIsProcessingTask] = useState(false);
  const gameViewportRef = useRef<any>(null);

  const handleMetricsUpdate = useCallback((newMetrics: GameMetrics) => {
    setMetrics(newMetrics);
  }, []);

  const handlePromptSubmit = async (prompt: string) => {
    setIsProcessingTask(true);
    try {
      // Send prompt to backend orchestrator
      const response = await fetch("/api/orchestrator/generate_task", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Task generated:", data);
        // Task has been processed, metrics will update via WebSocket
      } else {
        console.error("Failed to generate task");
      }
    } catch (error) {
      console.error("Error submitting prompt:", error);
    } finally {
      setIsProcessingTask(false);
    }
  };

  const handleAction = (actionIndex: number) => {
    // This is handled by GameViewport's WebSocket connection
    console.log("Action sent:", actionIndex);
  };

  return (
    <div style={styles.app}>
      {/* Header */}
      <header style={styles.header}>
        <h1>DREAM.AI - ProcTHOR Control Panel</h1>
        <p style={styles.subtitle}>
          Real-time environment streaming and control
        </p>
      </header>

      {/* Main layout */}
      <div style={styles.mainContainer}>
        {/* Left sidebar - UI controls */}
        <div style={styles.sidebar}>
          {/* Prompt box */}
          <PromptBox
            onSubmit={handlePromptSubmit}
            isLoading={isProcessingTask}
          />

          {/* Metrics display */}
          <MetricsDisplay
            episodeReward={metrics.episode_reward}
            stepCount={metrics.step_count}
            agentPosition={metrics.agent_position}
            agentRotation={metrics.agent_rotation}
            actionSuccess={metrics.last_action_success}
          />

          {/* Action control panel */}
          <ActionPanel onAction={handleAction} />
        </div>

        {/* Right side - Game viewport */}
        <div style={styles.gameContainer}>
          <GameViewport
            ref={gameViewportRef}
            onMetricsUpdate={handleMetricsUpdate}
          />
        </div>
      </div>
    </div>
  );
}

const styles = {
  app: {
    display: "flex",
    flexDirection: "column" as const,
    minHeight: "100vh",
    backgroundColor: "#0a0e27",
    color: "#e0e0e0",
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
  },
  header: {
    backgroundColor: "#1a1f3a",
    padding: "20px",
    borderBottom: "2px solid #4a90e2",
    textAlign: "center" as const,
  },
  subtitle: {
    margin: "5px 0 0 0",
    fontSize: "14px",
    color: "#b0b0b0",
  },
  mainContainer: {
    display: "flex",
    gap: "20px",
    padding: "20px",
    flex: 1,
    maxWidth: "1400px",
    margin: "0 auto",
    width: "100%",
  },
  sidebar: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "15px",
    flex: "0 0 350px",
    maxHeight: "calc(100vh - 140px)",
    overflowY: "auto" as const,
  },
  gameContainer: {
    flex: 1,
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
};

export default App;
