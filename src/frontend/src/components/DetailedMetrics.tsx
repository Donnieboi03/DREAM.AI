import React, { useState, useEffect } from "react";

interface MetricsHistory {
  timestamps: number[];
  rewards: number[];
  steps: number[];
}

interface MetricsGraphProps {
  rewardHistory: number[];
  maxHistory?: number;
}

export const RewardGraph: React.FC<MetricsGraphProps> = ({
  rewardHistory,
  maxHistory = 100,
}) => {
  // Normalize rewards for display (0-100 range)
  const maxReward = Math.max(...rewardHistory, 1);
  const normalizedData = rewardHistory.map((r) => (r / maxReward) * 100);

  // Only show last maxHistory items
  const displayData = normalizedData.slice(-maxHistory);

  const height = 150;
  const width = 300;
  const padding = 20;
  const graphHeight = height - padding * 2;
  const pointSpacing = (width - padding * 2) / Math.max(displayData.length - 1, 1);

  let pathData = "";
  displayData.forEach((value, index) => {
    const x = padding + index * pointSpacing;
    const y = height - padding - (value / 100) * graphHeight;
    pathData += `${index === 0 ? "M" : "L"} ${x} ${y} `;
  });

  return (
    <div style={styles.graphContainer}>
      <h4 style={styles.graphTitle}>Reward Trend</h4>
      <svg width={width} height={height} style={styles.svg}>
        {/* Grid lines */}
        {[25, 50, 75].map((line) => (
          <line
            key={line}
            x1={padding}
            y1={height - padding - (line / 100) * graphHeight}
            x2={width - padding}
            y2={height - padding - (line / 100) * graphHeight}
            stroke="#4a90e2"
            strokeDasharray="4"
            opacity="0.3"
          />
        ))}

        {/* Path */}
        <path
          d={pathData}
          stroke="#4ade80"
          strokeWidth="2"
          fill="none"
          vectorEffect="non-scaling-stroke"
        />

        {/* Axes */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={height - padding}
          stroke="#4a90e2"
          strokeWidth="1"
        />
        <line
          x1={padding}
          y1={height - padding}
          x2={width - padding}
          y2={height - padding}
          stroke="#4a90e2"
          strokeWidth="1"
        />
      </svg>
      {displayData.length > 0 && (
        <div style={styles.graphStats}>
          <span>Min: {Math.min(...rewardHistory).toFixed(2)}</span>
          <span>
            Avg:{" "}
            {(
              rewardHistory.reduce((a, b) => a + b, 0) / rewardHistory.length
            ).toFixed(2)}
          </span>
          <span>Max: {Math.max(...rewardHistory).toFixed(2)}</span>
        </div>
      )}
    </div>
  );
};

interface DetailedMetricsProps {
  episodeReward: number;
  stepCount: number;
  rewardHistory: number[];
  agentPosition?: { x: number; y: number; z: number } | null;
  agentRotation?: number | null;
  actionSuccess: boolean;
}

export const DetailedMetrics: React.FC<DetailedMetricsProps> = ({
  episodeReward,
  stepCount,
  rewardHistory,
  agentPosition,
  agentRotation,
  actionSuccess,
}) => {
  return (
    <div style={styles.container}>
      {/* Stats grid */}
      <div style={styles.statsGrid}>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>Episode Reward</div>
          <div style={styles.statValue}>{episodeReward.toFixed(2)}</div>
        </div>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>Steps Taken</div>
          <div style={styles.statValue}>{stepCount}</div>
        </div>
        <div style={styles.statBox}>
          <div style={styles.statLabel}>Avg Reward/Step</div>
          <div style={styles.statValue}>
            {stepCount > 0 ? (episodeReward / stepCount).toFixed(3) : "0.000"}
          </div>
        </div>
        <div style={styles.statBox}>
          <div
            style={{
              ...styles.statLabel,
              color: actionSuccess ? "#4ade80" : "#f87171",
            }}
          >
            Last Action
          </div>
          <div
            style={{
              ...styles.statValue,
              color: actionSuccess ? "#4ade80" : "#f87171",
            }}
          >
            {actionSuccess ? "✓ Success" : "✗ Failed"}
          </div>
        </div>
      </div>

      {/* Position info */}
      {agentPosition && (
        <div style={styles.positionInfo}>
          <h4 style={styles.infoTitle}>Agent Position</h4>
          <div style={styles.positionGrid}>
            <div>
              <span style={styles.label}>X:</span>
              <span style={styles.value}>{agentPosition.x.toFixed(2)}</span>
            </div>
            <div>
              <span style={styles.label}>Z:</span>
              <span style={styles.value}>{agentPosition.z.toFixed(2)}</span>
            </div>
            {agentRotation !== null && agentRotation !== undefined && (
              <div>
                <span style={styles.label}>Rotation:</span>
                <span style={styles.value}>{agentRotation.toFixed(1)}°</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reward graph */}
      {rewardHistory.length > 0 && (
        <RewardGraph rewardHistory={rewardHistory} />
      )}
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "12px",
    padding: "15px",
    backgroundColor: "#1a1f3a",
    borderRadius: "8px",
    border: "1px solid #4a90e2",
  },
  statsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "10px",
  },
  statBox: {
    padding: "10px",
    backgroundColor: "rgba(74, 144, 226, 0.1)",
    borderRadius: "4px",
    border: "1px solid rgba(74, 144, 226, 0.3)",
  },
  statLabel: {
    fontSize: "12px",
    color: "#b0b0b0",
    marginBottom: "4px",
  },
  statValue: {
    fontSize: "18px",
    fontWeight: "bold" as const,
    color: "#4ade80",
    fontFamily: "monospace",
  },
  positionInfo: {
    padding: "10px",
    backgroundColor: "rgba(74, 144, 226, 0.1)",
    borderRadius: "4px",
    border: "1px solid rgba(74, 144, 226, 0.3)",
  },
  infoTitle: {
    margin: "0 0 8px 0",
    fontSize: "13px",
    color: "#e0e0e0",
  },
  positionGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "8px",
  },
  label: {
    color: "#b0b0b0",
    marginRight: "4px",
    fontSize: "12px",
  },
  value: {
    color: "#4ade80",
    fontFamily: "monospace",
    fontSize: "13px",
  },
  graphContainer: {
    padding: "10px",
    backgroundColor: "rgba(74, 144, 226, 0.05)",
    borderRadius: "4px",
    border: "1px solid rgba(74, 144, 226, 0.2)",
  },
  graphTitle: {
    margin: "0 0 10px 0",
    fontSize: "13px",
    color: "#e0e0e0",
  },
  svg: {
    width: "100%",
    height: "auto",
  },
  graphStats: {
    display: "flex",
    justifyContent: "space-around",
    marginTop: "8px",
    fontSize: "11px",
    color: "#b0b0b0",
    fontFamily: "monospace",
  },
};

export default {
  RewardGraph,
  DetailedMetrics,
};
