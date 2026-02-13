import { useState } from "react";
import { Activity, ChevronUp } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, YAxis } from "recharts";
import { cn } from "@/lib/utils";

interface GameMetrics {
  agent_position: { x: number; y: number; z: number } | null;
  agent_rotation: number | null;
  episode_reward: number;
  step_count: number;
  last_action_success: boolean;
}

interface MetricsHUDProps {
  metrics?: GameMetrics | null;
  rewardHistory?: { value: number }[];
  aboveOverlay?: boolean;
}

const MetricsHUD = ({
  metrics,
  rewardHistory = [],
  aboveOverlay = false,
}: MetricsHUDProps) => {
  const [collapsed, setCollapsed] = useState(false);

  const episodeReward = metrics?.episode_reward ?? 0;
  const stepCount = metrics?.step_count ?? 0;
  const pos = metrics?.agent_position;
  const actionSuccess = metrics?.last_action_success ?? true;

  const chartData =
    rewardHistory.length > 0 ? rewardHistory : [{ value: episodeReward }];

  const MiniChart = ({ data, color }: { data: { value: number }[]; color: string }) => (
    <ResponsiveContainer width="100%" height={32}>
      <LineChart data={data}>
        <YAxis hide domain={["auto", "auto"]} />
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
      >
        <Activity className="h-5 w-5" />
      </button>
    );
  }

  return (
    <div className={cn("fixed top-4 right-4 w-64 glass-panel rounded-xl p-3 space-y-3 neon-glow-cyan", zClass)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-primary" />
          <span className="text-xs font-semibold text-primary tracking-wider">
            METRICS
          </span>
        </div>
        <button
          onClick={() => setCollapsed(true)}
          className="text-muted-foreground hover:text-foreground"
        >
          <ChevronUp className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-2">
        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Reward
            </span>
            <span className="text-[10px] font-mono text-neon-green">
              {episodeReward.toFixed(2)}
            </span>
          </div>
          <MiniChart data={chartData} color="hsl(160, 100%, 45%)" />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Steps
            </span>
            <span className="text-[10px] font-mono text-foreground">
              {stepCount}
            </span>
          </div>
        </div>

        {pos && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                Position
              </span>
              <span className="text-[10px] font-mono text-neon-cyan">
                ({pos.x.toFixed(1)}, {pos.z.toFixed(1)})
              </span>
            </div>
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Last Action
            </span>
            <span
              className={cn(
                "text-[10px] font-mono",
                actionSuccess ? "text-emerald-500" : "text-destructive"
              )}
            >
              {actionSuccess ? "✓ Success" : "✗ Failed"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MetricsHUD;
