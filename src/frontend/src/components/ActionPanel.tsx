import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const ACTIONS = [
  { label: "↑ Ahead", index: 0 },
  { label: "↓ Back", index: 1 },
  { label: "← Left", index: 2 },
  { label: "→ Right", index: 3 },
  { label: "⬆ Look Up", index: 4 },
  { label: "⬇ Look Down", index: 5 },
  { label: "🖐 Pickup", index: 6 },
  { label: "📥 Drop", index: 7 },
  { label: "⚡ Toggle", index: 8 },
] as const;

interface ActionPanelProps {
  onAction: (index: number) => void;
  disabled?: boolean;
  className?: string;
}

export default function ActionPanel({ onAction, disabled, className }: ActionPanelProps) {
  return (
    <div className={cn("space-y-2", className)}>
      <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        Controls
      </div>
      <div className="grid grid-cols-3 gap-2">
        {ACTIONS.map(({ label, index }) => (
          <Button
            key={index}
            variant="outline"
            size="sm"
            disabled={disabled}
            onClick={() => onAction(index)}
            className="font-mono text-xs"
          >
            {label}
          </Button>
        ))}
      </div>
    </div>
  );
}
