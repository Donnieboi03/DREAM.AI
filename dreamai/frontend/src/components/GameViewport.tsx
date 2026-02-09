import React, { useEffect, useRef, useState } from "react";

interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

interface GameViewportProps {
  onMetricsUpdate?: (metrics: GameMetrics) => void;
}

const GameViewport: React.FC<GameViewportProps> = ({ onMetricsUpdate }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState<GameMetrics>({
    agent_position: null,
    agent_rotation: null,
    episode_reward: 0,
    step_count: 0,
    last_action_success: true,
  });
  const [isStreaming, setIsStreaming] = useState(false);

  // Initialize WebSocket connection
  useEffect(() => {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/game`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to backend");
      setIsConnected(true);
      // Send start streaming signal
      ws.send(JSON.stringify({ type: "start_streaming" }));
      setIsStreaming(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);

        if (message.type === "frame") {
          // Decode and render JPEG frame
          const canvas = canvasRef.current;
          if (canvas) {
            const ctx = canvas.getContext("2d");
            if (ctx) {
              const img = new Image();
              img.onload = () => {
                ctx.drawImage(img, 0, 0);
              };
              img.src = `data:image/jpeg;base64,${message.jpeg_base64}`;
            }
          }

          // Update metrics
          if (message.metrics) {
            setMetrics(message.metrics);
            onMetricsUpdate?.(message.metrics);
          }
        }
      } catch (e) {
        console.error("Error parsing WebSocket message:", e);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log("Disconnected from backend");
      setIsConnected(false);
      setIsStreaming(false);
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "stop_streaming" }));
        ws.close();
      }
    };
  }, [onMetricsUpdate]);

  // Send action to backend
  const sendAction = (actionIndex: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "action", action: actionIndex }));
    }
  };

  // Reset environment
  const resetEnvironment = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "reset" }));
    }
  };

  return (
    <div style={styles.container}>
      {/* Connection status */}
      <div style={styles.statusBar}>
        <span style={{ color: isConnected ? "green" : "red" }}>
          {isConnected ? "● Connected" : "● Disconnected"}
        </span>
        <span style={{ marginLeft: "20px" }}>
          {isStreaming ? "Streaming" : "Not streaming"}
        </span>
        <button onClick={resetEnvironment} style={styles.resetButton}>
          Reset
        </button>
      </div>

      {/* Main game canvas */}
      <canvas
        ref={canvasRef}
        width={800}
        height={600}
        style={styles.canvas}
      />

      {/* Debug metrics display (temporary) */}
      <div style={styles.debugMetrics}>
        <p>Episode Reward: {metrics.episode_reward.toFixed(2)}</p>
        <p>Steps: {metrics.step_count}</p>
        {metrics.agent_position && (
          <p>
            Agent Pos: ({metrics.agent_position.x.toFixed(2)},
            {metrics.agent_position.z.toFixed(2)})
          </p>
        )}
      </div>

      {/* Temporary action buttons for testing */}
      <div style={styles.controlPanel}>
        <button onClick={() => sendAction(0)} style={styles.button}>
          Move Ahead
        </button>
        <button onClick={() => sendAction(1)} style={styles.button}>
          Move Back
        </button>
        <button onClick={() => sendAction(2)} style={styles.button}>
          Rotate Left
        </button>
        <button onClick={() => sendAction(3)} style={styles.button}>
          Rotate Right
        </button>
        <button onClick={() => sendAction(4)} style={styles.button}>
          Look Up
        </button>
        <button onClick={() => sendAction(5)} style={styles.button}>
          Look Down
        </button>
        <button onClick={() => sendAction(6)} style={styles.button}>
          Pickup
        </button>
        <button onClick={() => sendAction(7)} style={styles.button}>
          Drop
        </button>
        <button onClick={() => sendAction(8)} style={styles.button}>
          Toggle
        </button>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    flexDirection: "column" as const,
    alignItems: "center",
    padding: "20px",
    backgroundColor: "#0a0e27",
    minHeight: "100vh",
    color: "#fff",
    fontFamily: "monospace",
  },
  statusBar: {
    display: "flex",
    alignItems: "center",
    marginBottom: "20px",
    padding: "10px 20px",
    backgroundColor: "#1a1f3a",
    borderRadius: "5px",
    width: "100%",
    maxWidth: "800px",
  },
  resetButton: {
    marginLeft: "auto",
    padding: "8px 16px",
    backgroundColor: "#ff6b6b",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
  },
  canvas: {
    border: "2px solid #4a90e2",
    borderRadius: "8px",
    backgroundColor: "#000",
    maxWidth: "100%",
    height: "auto",
    marginBottom: "20px",
  },
  debugMetrics: {
    padding: "10px 20px",
    backgroundColor: "#1a1f3a",
    borderRadius: "5px",
    marginBottom: "20px",
    fontSize: "12px",
    textAlign: "left" as const,
    width: "100%",
    maxWidth: "800px",
  },
  controlPanel: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "10px",
    width: "100%",
    maxWidth: "800px",
  },
  button: {
    padding: "12px",
    backgroundColor: "#4a90e2",
    color: "#fff",
    border: "none",
    borderRadius: "4px",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "bold",
    transition: "background-color 0.2s",
  },
};

export default GameViewport;
