import React, { useState } from "react";

interface PromptBoxProps {
  onSubmit: (prompt: string) => void;
  isLoading?: boolean;
}

export const PromptBox: React.FC<PromptBoxProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [promptText, setPromptText] = useState("");

  const handleSubmit = () => {
    if (promptText.trim()) {
      onSubmit(promptText);
      setPromptText("");
    }
  };

  return (
    <div style={styles.container}>
      <label style={styles.label}>Task Prompt:</label>
      <textarea
        value={promptText}
        onChange={(e) => setPromptText(e.target.value)}
        placeholder="Describe the task for the agent..."
        style={styles.textarea}
        disabled={isLoading}
      />
      <button
        onClick={handleSubmit}
        style={{
          ...styles.button,
          opacity: isLoading ? 0.6 : 1,
        }}
        disabled={isLoading}
      >
        {isLoading ? "Processing..." : "Submit Task"}
      </button>
    </div>
  );
};

interface MetricsDisplayProps {
  episodeReward: number;
  stepCount: number;
  agentPosition?: { x: number; y: number; z: number } | null;
  agentRotation?: number | null;
  actionSuccess: boolean;
}

export const MetricsDisplay: React.FC<MetricsDisplayProps> = ({
  episodeReward,
  stepCount,
  agentPosition,
  agentRotation,
  actionSuccess,
}) => {
  return (
    <div style={styles.metricsContainer}>
      <div style={styles.metricRow}>
        <span style={styles.metricLabel}>Episode Reward:</span>
        <span style={styles.metricValue}>{episodeReward.toFixed(2)}</span>
      </div>
      <div style={styles.metricRow}>
        <span style={styles.metricLabel}>Steps:</span>
        <span style={styles.metricValue}>{stepCount}</span>
      </div>
      {agentPosition && (
        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>Position:</span>
          <span style={styles.metricValue}>
            ({agentPosition.x.toFixed(2)}, {agentPosition.z.toFixed(2)})
          </span>
        </div>
      )}
      {agentRotation !== null && agentRotation !== undefined && (
        <div style={styles.metricRow}>
          <span style={styles.metricLabel}>Rotation:</span>
          <span style={styles.metricValue}>{agentRotation.toFixed(1)}°</span>
        </div>
      )}
      <div style={styles.metricRow}>
        <span style={styles.metricLabel}>Last Action:</span>
        <span
          style={{
            ...styles.metricValue,
            color: actionSuccess ? "#4ade80" : "#f87171",
          }}
        >
          {actionSuccess ? "✓ Success" : "✗ Failed"}
        </span>
      </div>
    </div>
  );
};

interface ActionButtonProps {
  label: string;
  actionIndex: number;
  onAction: (index: number) => void;
}

const ActionButton: React.FC<ActionButtonProps> = ({
  label,
  actionIndex,
  onAction,
}) => {
  return (
    <button
      onClick={() => onAction(actionIndex)}
      style={styles.actionButton}
      onMouseEnter={(e) => {
        (e.target as HTMLButtonElement).style.backgroundColor = "#3b82f6";
      }}
      onMouseLeave={(e) => {
        (e.target as HTMLButtonElement).style.backgroundColor = "#4a90e2";
      }}
    >
      {label}
    </button>
  );
};

interface ActionPanelProps {
  onAction: (actionIndex: number) => void;
}

export const ActionPanel: React.FC<ActionPanelProps> = ({ onAction }) => {
  const actions = [
    { label: "↑ Move Ahead", index: 0 },
    { label: "↓ Move Back", index: 1 },
    { label: "← Rotate Left", index: 2 },
    { label: "→ Rotate Right", index: 3 },
    { label: "⬆ Look Up", index: 4 },
    { label: "⬇ Look Down", index: 5 },
    { label: "🖐 Pickup", index: 6 },
    { label: "📥 Drop", index: 7 },
    { label: "⚡ Toggle", index: 8 },
  ];

  return (
    <div style={styles.actionPanelContainer}>
      <div style={styles.actionPanelTitle}>Controls</div>
      <div style={styles.actionPanelGrid}>
        {actions.map((action) => (
          <ActionButton
            key={action.index}
            label={action.label}
            actionIndex={action.index}
            onAction={onAction}
          />
        ))}
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "10px",
    padding: "15px",
    backgroundColor: "#1a1f3a",
    borderRadius: "8px",
    border: "1px solid #4a90e2",
  },
  label: {
    fontSize: "14px",
    fontWeight: "bold" as const,
    color: "#e0e0e0",
  },
  textarea: {
    padding: "10px",
    backgroundColor: "#0a0e27",
    color: "#e0e0e0",
    border: "1px solid #4a90e2",
    borderRadius: "4px",
    fontSize: "13px",
    fontFamily: "monospace",
    minHeight: "80px",
    resize: "vertical" as const,
    outline: "none",
  },
  button: {
    padding: "10px 20px",
    backgroundColor: "#4a90e2",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold" as const,
    transition: "background-color 0.2s",
  },
  metricsContainer: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
    padding: "15px",
    backgroundColor: "rgba(74, 144, 226, 0.1)",
    borderRadius: "8px",
    border: "1px solid #4a90e2",
  },
  metricRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "13px",
  },
  metricLabel: {
    color: "#b0b0b0",
  },
  metricValue: {
    color: "#4ade80",
    fontWeight: "bold" as const,
    fontFamily: "monospace",
  },
  actionPanelContainer: {
    padding: "15px",
    backgroundColor: "#1a1f3a",
    borderRadius: "8px",
    border: "1px solid #4a90e2",
  },
  actionPanelTitle: {
    fontSize: "14px",
    fontWeight: "bold" as const,
    marginBottom: "12px",
    color: "#e0e0e0",
  },
  actionPanelGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "8px",
  },
  actionButton: {
    padding: "10px",
    backgroundColor: "#4a90e2",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "12px",
    fontWeight: "bold" as const,
    transition: "background-color 0.2s",
  },
};

export default {
  PromptBox,
  MetricsDisplay,
  ActionPanel,
};
