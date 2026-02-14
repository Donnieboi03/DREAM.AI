import { useState, useEffect, memo } from "react";
import { ChevronDown, ChevronUp, LayoutDashboard, Play, RotateCcw, Square } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { cn } from "@/lib/utils";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { rlAgentStatus, rlAgentStart, rlAgentStop } from "@/lib/dreamaiApi";
import type { GameMetrics } from "@/types/game";

interface ControlPanelProps {
  metrics?: GameMetrics | null;
  rewardHistory?: { value: number }[];
  aboveOverlay?: boolean;
  onReset?: () => void;
  onControlModeChange?: (mode: "user" | "agent") => void;
}

const ControlPanel = memo(function ControlPanel({
  metrics,
  rewardHistory = [],
  aboveOverlay = false,
  onReset,
  onControlModeChange,
}: ControlPanelProps) {
  const [collapsed, setCollapsed] = useState(true);
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentLoading, setAgentLoading] = useState(false);

  useEffect(() => {
    const poll = () => rlAgentStatus().then((r) => setAgentRunning(r.running)).catch(() => {});
    poll();
    const id = setInterval(poll, 3000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    onControlModeChange?.(agentRunning ? "agent" : "user");
  }, [agentRunning, onControlModeChange]);

  const handleAgentToggle = async () => {
    if (agentLoading) return;
    setAgentLoading(true);
    try {
      if (agentRunning) {
        await rlAgentStop();
        onControlModeChange?.("user");
        setAgentRunning(false);
      } else {
        await rlAgentStart();
        onControlModeChange?.("agent");
        setAgentRunning(true);
      }
    } catch {
      // Keep current state on error
    } finally {
      setAgentLoading(false);
    }
  };

  const handleReset = async () => {
    onReset?.();
    if (agentRunning) {
      try {
        await rlAgentStop();
        const res = await rlAgentStart();
        setAgentRunning(res.running);
      } catch {
        setAgentRunning(false);
      }
    }
  };

  const episodeReward = metrics?.episode_reward ?? 0;
  const stepCount = metrics?.step_count ?? 0;
  const pos = metrics?.agent_position;
  const actionSuccess = metrics?.last_action_success ?? true;
  const taskAdvancement = metrics?.task_advancement ?? null;
  const maxTaskAdvancement = metrics?.max_task_advancement ?? null;
  const isSuccess = metrics?.is_success ?? null;
  const taskType = metrics?.task_type ?? null;

  const chartData =
    rewardHistory.length > 0 ? rewardHistory : [{ value: episodeReward }];

  const MiniChart = ({ data, color }: { data: { value: number }[]; color: string }) => (
    <ResponsiveContainer width="100%" height={32}>
      <LineChart data={data}>
        <YAxis hide domain={["dataMin", "dataMax"]} padding={{ top: 4, bottom: 4 }} />
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );

  const zClass = aboveOverlay ? "z-[60]" : "z-40";

  if (collapsed) {
    return (
      <button
        onClick={() => setCollapsed(false)}
        className={cn("fixed top-4 right-4 glass-panel rounded-lg p-2 text-primary hover:neon-glow-cyan transition-all", zClass)}
        title="Control Panel"
      >
        <LayoutDashboard className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div className={cn("fixed top-4 right-4 w-64 glass-panel rounded-xl p-3 space-y-2 neon-glow-cyan", zClass)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LayoutDashboard className="h-4 w-4 text-primary" />
          <span className="text-xs font-semibold text-primary tracking-wider">
            CONTROL PANEL
          </span>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="text-muted-foreground hover:text-foreground"
          title="Collapse"
        >
          <ChevronUp className="h-4 w-4" />
        </button>
      </div>

      <Collapsible className="space-y-1">
        <CollapsibleTrigger className="group flex w-full items-center justify-between py-2 text-[10px] font-medium uppercase tracking-wider text-neon-cyan hover:text-neon-cyan/80">
          Metrics
          <ChevronDown className="h-3 w-3 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-2 pt-1">
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-neon-cyan uppercase tracking-wider">Reward</span>
              <span className="text-[10px] font-mono text-neon-green">{episodeReward.toFixed(2)}</span>
            </div>
            <MiniChart data={chartData} color="hsl(160, 100%, 45%)" />
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-neon-cyan uppercase tracking-wider">Steps</span>
              <span className="text-[10px] font-mono text-foreground">{stepCount}</span>
            </div>
          </div>
          {pos && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-neon-cyan uppercase tracking-wider">Position</span>
                <span className="text-[10px] font-mono text-neon-cyan">
                  ({pos.x.toFixed(1)}, {pos.z.toFixed(1)})
                </span>
              </div>
            </div>
          )}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-neon-cyan uppercase tracking-wider">Last Action</span>
              <span
                className={cn(
                  "text-[10px] font-mono",
                  actionSuccess ? "text-emerald-500" : "text-destructive"
                )}
              >
                {actionSuccess ? "Success" : "Failed"}
              </span>
            </div>
          </div>
          {(taskAdvancement != null && maxTaskAdvancement != null && maxTaskAdvancement > 0) && (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-neon-cyan uppercase tracking-wider">Task Progress</span>
                <span className="text-[10px] font-mono text-neon-cyan">
                  {taskType ?? "—"} {Math.round((taskAdvancement / maxTaskAdvancement) * 100)}%
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-neon-cyan transition-all duration-200"
                  style={{ width: `${Math.min(100, (taskAdvancement / maxTaskAdvancement) * 100)}%` }}
                />
              </div>
            </div>
          )}
          {isSuccess === true && (
            <div className="text-[10px] font-semibold text-emerald-400 text-center">
              Task completed!
            </div>
          )}
        </CollapsibleContent>
      </Collapsible>

      <Collapsible className="space-y-1">
        <CollapsibleTrigger className="group flex w-full items-center justify-between py-2 text-[10px] font-medium uppercase tracking-wider text-neon-cyan hover:text-neon-cyan/80">
          Configurations
          <ChevronDown className="h-3 w-3 shrink-0 transition-transform duration-200 group-data-[state=open]:rotate-180" />
        </CollapsibleTrigger>
        <CollapsibleContent className="space-y-2 pt-1">
          <button
            onClick={handleAgentToggle}
            disabled={agentLoading}
            className={cn(
              "w-full flex items-center justify-center gap-2 py-1.5 text-[10px] font-medium uppercase tracking-wider rounded transition-colors",
              agentRunning ? "text-destructive hover:bg-destructive/10" : "text-neon-cyan hover:bg-neon-cyan/10",
              agentLoading && "opacity-60 cursor-not-allowed"
            )}
          >
            {agentRunning ? (
              <>
                <Square className="h-3 w-3" />
                Stop Agent
              </>
            ) : (
              <>
                <Play className="h-3 w-3" />
                Run Agent
              </>
            )}
          </button>
          {onReset && (
            <button
              onClick={handleReset}
              className="w-full flex items-center justify-center gap-2 py-1.5 text-[10px] font-medium uppercase tracking-wider text-neon-cyan hover:text-neon-cyan/80 hover:bg-white/5 rounded transition-colors"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </button>
          )}
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
});

export default ControlPanel;
