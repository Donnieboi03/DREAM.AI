import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface TaskSpec {
  description: string;
  goal: string;
  success_criteria: string[];
  max_steps: number;
  subtasks?: unknown[];
}

interface TaskDisplayProps {
  task: TaskSpec;
  className?: string;
}

export default function TaskDisplay({ task, className }: TaskDisplayProps) {
  return (
    <Card className={cn("border-primary/30 bg-primary/5", className)}>
      <CardHeader className="py-3">
        <div className="text-sm font-semibold text-primary">Current Task</div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">Goal</div>
          <div className="text-sm text-foreground">{task.goal}</div>
        </div>
        {task.success_criteria?.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
              Success Criteria
            </div>
            <ul className="list-disc list-inside text-sm text-foreground space-y-0.5">
              {task.success_criteria.map((c, i) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </div>
        )}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-0.5">
            Max Steps
          </div>
          <div className="text-sm font-mono text-foreground">{task.max_steps}</div>
        </div>
      </CardContent>
    </Card>
  );
}
