import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getDreamAiWsGameUrl } from "@/lib/dreamaiConfig";

export interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

interface GameViewportProps {
  onMetricsUpdate?: (metrics: GameMetrics) => void;
  className?: string;
}

export interface GameViewportHandle {
  loadScene: (sceneName: string) => void;
  sendAction: (actionIndex: number) => void;
  reset: () => void;
}

const GameViewport = forwardRef<GameViewportHandle, GameViewportProps>(
  ({ onMetricsUpdate, className }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected" | "error">("connecting");
    const [currentMetrics, setCurrentMetrics] = useState<GameMetrics>({
      agent_position: null,
      agent_rotation: null,
      episode_reward: 0,
      step_count: 0,
      last_action_success: true,
    });

    useImperativeHandle(ref, () => ({
      loadScene: (sceneName: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "load_scene", scene: sceneName }));
        }
      },
      sendAction: (actionIndex: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "action", action: actionIndex }));
        }
      },
      reset: () => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "reset" }));
        }
      },
    }));

    useEffect(() => {
      const connectWebSocket = () => {
        try {
          const wsUrl = getDreamAiWsGameUrl();
          wsRef.current = new WebSocket(wsUrl);

          wsRef.current.onopen = () => {
            setConnectionStatus("connected");
            wsRef.current?.send(JSON.stringify({ type: "start_streaming" }));
          };

          wsRef.current.onmessage = (event) => {
            try {
              const message = JSON.parse(event.data);

              if (message.type === "frame" && message.jpeg_base64) {
                const img = new Image();
                img.onload = () => {
                  const canvas = canvasRef.current;
                  if (canvas) {
                    const ctx = canvas.getContext("2d");
                    if (ctx) ctx.drawImage(img, 0, 0);
                  }
                };
                img.src = `data:image/jpeg;base64,${message.jpeg_base64}`;

                if (message.metrics) {
                  setCurrentMetrics(message.metrics);
                  onMetricsUpdate?.(message.metrics);
                }
              }
            } catch (e) {
              console.error("[GameViewport] Error processing message:", e);
            }
          };

          wsRef.current.onerror = () => setConnectionStatus("error");
          wsRef.current.onclose = () => {
            setConnectionStatus("disconnected");
            setTimeout(connectWebSocket, 3000);
          };
        } catch (e) {
          console.error("[GameViewport] Failed to connect:", e);
          setConnectionStatus("error");
          setTimeout(connectWebSocket, 3000);
        }
      };

      connectWebSocket();

      const handleKeyDown = (e: KeyboardEvent) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

        const keyMap: Record<string, number> = {
          w: 0, s: 1, a: 2, d: 3, q: 4, e: 5, f: 6, g: 7, t: 8,
        };
        const action = keyMap[e.key.toLowerCase()];
        if (action !== undefined) {
          e.preventDefault();
          wsRef.current.send(JSON.stringify({ type: "action", action }));
        }
      };

      window.addEventListener("keydown", handleKeyDown);
      return () => {
        window.removeEventListener("keydown", handleKeyDown);
        wsRef.current?.close();
      };
    }, [onMetricsUpdate]);

    const statusColor = {
      connecting: "text-muted-foreground",
      connected: "text-emerald-500",
      disconnected: "text-amber-500",
      error: "text-destructive",
    }[connectionStatus];

    return (
      <Card className={cn("relative overflow-hidden bg-black", className)}>
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          className="w-full h-auto block"
        />
        <div
          className={cn(
            "absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium bg-black/60",
            statusColor
          )}
        >
          {connectionStatus === "connecting" && "Connecting…"}
          {connectionStatus === "connected" && "● Connected"}
          {connectionStatus === "disconnected" && "Disconnected"}
          {connectionStatus === "error" && "Error"}
        </div>
      </Card>
    );
  }
);

GameViewport.displayName = "GameViewport";
export default GameViewport;
