import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";

interface GameViewportProps {
  onMetricsUpdate?: (metrics: any) => void;
}

interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

const GameViewport = forwardRef<any, GameViewportProps>(
  ({ onMetricsUpdate }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [connectionStatus, setConnectionStatus] = useState("Disconnecting...");
    const [currentMetrics, setCurrentMetrics] = useState<GameMetrics>({
      agent_position: null,
      agent_rotation: null,
      episode_reward: 0,
      step_count: 0,
      last_action_success: true,
    });

    // Exposed methods via ref
    useImperativeHandle(ref, () => ({
      loadScene: (sceneName: string) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: "load_scene",
              scene: sceneName,
            })
          );
          console.log("[GameViewport] Scene name sent to backend:", sceneName);
        }
      },
      sendAction: (actionIndex: number) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(
            JSON.stringify({
              type: "action",
              action: actionIndex,
            })
          );
        }
      },
      reset: () => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "reset" }));
        }
      },
    }));

    useEffect(() => {
      const connectWebSocket = () => {
        try {
          wsRef.current = new WebSocket("ws://localhost:8000/ws/game");

          wsRef.current.onopen = () => {
            console.log("[GameViewport] Connected to backend");
            setConnectionStatus("Connected");

            // Start streaming frames
            wsRef.current?.send(JSON.stringify({ type: "start_streaming" }));
          };

          wsRef.current.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);

              if (message.type === "frame" && message.jpeg_base64) {
                // Decode and render JPEG frame
                const img = new Image();
                img.onload = () => {
                  const canvas = canvasRef.current;
                  if (canvas) {
                    const ctx = canvas.getContext("2d");
                    if (ctx) {
                      ctx.drawImage(img, 0, 0);
                    }
                  }
                };
                img.src = `data:image/jpeg;base64,${message.jpeg_base64}`;

                // Update metrics
                if (message.metrics) {
                  setCurrentMetrics(message.metrics);
                  onMetricsUpdate?.(message.metrics);
                }
              }
            } catch (e) {
              console.error("[GameViewport] Error processing message:", e);
            }
          };

          wsRef.current.onerror = (error) => {
            console.error("[GameViewport] WebSocket error:", error);
            setConnectionStatus("Error");
          };

          wsRef.current.onclose = () => {
            console.log("[GameViewport] Disconnected from backend");
            setConnectionStatus("Disconnected");
            // Attempt to reconnect after 3 seconds
            setTimeout(connectWebSocket, 3000);
          };
        } catch (e) {
          console.error("[GameViewport] Failed to connect:", e);
          setConnectionStatus("Failed to connect");
        }
      };

      connectWebSocket();

      // Keyboard controls
      const handleKeyDown = (e: KeyboardEvent) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          return;
        }

        let action: number | null = null;

        switch (e.key.toLowerCase()) {
          case "w":
            action = 0; // Move forward
            break;
          case "s":
            action = 1; // Move backward
            break;
          case "a":
            action = 2; // Turn left
            break;
          case "d":
            action = 3; // Turn right
            break;
          case "q":
            action = 4; // Look up
            break;
          case "e":
            action = 5; // Look down
            break;
          case "f":
            action = 6; // Pickup
            break;
          case "g":
            action = 7; // Drop
            break;
          case "t":
            action = 8; // Toggle
            break;
          default:
            break;
        }

        if (action !== null) {
          e.preventDefault();
          wsRef.current.send(
            JSON.stringify({
              type: "action",
              action,
            })
          );
        }
      };

      window.addEventListener("keydown", handleKeyDown);

      return () => {
        window.removeEventListener("keydown", handleKeyDown);
        if (wsRef.current) {
          wsRef.current.close();
        }
      };
    }, [onMetricsUpdate]);

    return (
      <div style={styles.container}>
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          style={styles.canvas}
        />
        <div style={styles.status}>{connectionStatus}</div>
      </div>
    );
  }
);

GameViewport.displayName = "GameViewport";

const styles = {
  container: {
    position: "relative" as const,
    width: "100%",
    maxWidth: "1280px",
    aspectRatio: "16 / 9",
    backgroundColor: "#000",
    borderRadius: "8px",
    overflow: "hidden",
    boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
  },
  canvas: {
    width: "100%",
    height: "100%",
    display: "block",
  },
  status: {
    position: "absolute" as const,
    top: "10px",
    right: "10px",
    backgroundColor: "rgba(0, 0, 0, 0.6)",
    color: "#4ade80",
    padding: "5px 10px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "bold" as const,
  },
};

export default GameViewport;
