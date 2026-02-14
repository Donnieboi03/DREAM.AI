import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Minimize2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { getDreamAiWsGameUrl } from "@/lib/dreamaiConfig";
import type { GameMetrics } from "@/types/game";

export type { GameMetrics };

interface GameViewportProps {
  onMetricsUpdate?: (metrics: GameMetrics) => void;
  onEnlargedChange?: (enlarged: boolean) => void;
  className?: string;
}

export interface GameViewportHandle {
  loadScene: (sceneName: string, taskDescriptionDict?: Record<string, unknown>) => void;
  sendAction: (actionIndex: number) => void;
  /** Reset scene. randomize=false (default): restore to default. randomize=true: random agent/object positions (for agent on timeout/completion). */
  reset: (randomize?: boolean) => void;
}

const GameViewport = forwardRef<GameViewportHandle, GameViewportProps>(
  ({ onMetricsUpdate, onEnlargedChange, className }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wsRef = useRef<WebSocket | null>(null);
    const lastMetricsKeyRef = useRef("");
    const [isEnlarged, setIsEnlarged] = useState(false);

    const setEnlarged = (v: boolean) => {
      setIsEnlarged(v);
      onEnlargedChange?.(v);
    };
    const [connectionStatus, setConnectionStatus] = useState<"connecting" | "connected" | "disconnected" | "error">("connecting");
    const [currentMetrics, setCurrentMetrics] = useState<GameMetrics>({
      agent_position: null,
      agent_rotation: null,
      episode_reward: 0,
      step_count: 0,
      last_action_success: true,
    });

    useImperativeHandle(ref, () => ({
      loadScene: (sceneName: string, taskDescriptionDict?: Record<string, unknown>) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          const msg: Record<string, unknown> = { type: "load_scene", scene: sceneName };
          if (taskDescriptionDict != null) {
            msg.task_description_dict = taskDescriptionDict;
          }
          wsRef.current.send(JSON.stringify(msg));
        }
      },
      sendAction: (actionIndex: number) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "action", action: actionIndex }));
        }
      },
      reset: (randomize = false) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: "reset", randomize }));
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
                  const m = message.metrics;
                  const key = `${m.episode_reward}|${m.step_count}|${m.last_action_success}|${m.agent_position?.x ?? ""}|${m.agent_position?.z ?? ""}`;
                  if (key !== lastMetricsKeyRef.current) {
                    lastMetricsKeyRef.current = key;
                    onMetricsUpdate?.(message.metrics);
                  }
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

        // Don't capture keys when user is typing in chat/input
        const target = e.target as HTMLElement;
        const tag = target?.tagName?.toLowerCase();
        if (tag === "input" || tag === "textarea" || target?.isContentEditable) return;

        const keyMap: Record<string, number> = {
          w: 0, s: 1, a: 2, d: 3, q: 4, e: 5, p: 6, l: 7, t: 8,
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

    const viewportContent = (
      <Card
        className={cn(
          "relative overflow-hidden bg-black w-full aspect-[16/9] shrink-0 cursor-pointer",
          isEnlarged && "max-w-7xl",
          className
        )}
        onDoubleClick={() => !isEnlarged && setEnlarged(true)}
      >
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          className="w-full h-full block"
        />
        <div
          className={cn(
            "absolute bottom-2 left-2 px-2 py-1 rounded text-xs font-medium bg-black/60",
            statusColor
          )}
        >
          {connectionStatus === "connecting" && "Connecting…"}
          {connectionStatus === "connected" && "● Connected"}
          {connectionStatus === "disconnected" && "Disconnected"}
          {connectionStatus === "error" && "Error"}
        </div>
        {isEnlarged && (
          <Button
            variant="secondary"
            size="icon"
            className="absolute top-2 left-2 h-8 w-8 bg-black/60 hover:bg-black/80"
            onClick={(e) => {
              e.stopPropagation();
              setEnlarged(false);
            }}
            title="Minimize"
          >
            <Minimize2 className="h-4 w-4" />
          </Button>
        )}
        {!isEnlarged && (
          <div className="absolute bottom-2 right-2 px-2 py-1 rounded text-[10px] text-muted-foreground bg-black/40">
            Double-click to enlarge
          </div>
        )}
      </Card>
    );

    if (isEnlarged) {
      return (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          onClick={() => setEnlarged(false)}
        >
          <div
            className="w-full max-w-7xl"
            onClick={(e) => e.stopPropagation()}
          >
            {viewportContent}
          </div>
        </div>
      );
    }

    return viewportContent;
  }
);

GameViewport.displayName = "GameViewport";
export default GameViewport;
