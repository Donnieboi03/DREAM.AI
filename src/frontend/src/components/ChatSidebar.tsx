import { Plus, MessageSquare, PanelLeftClose, PanelLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export interface ChatSession {
  id: string;
  title: string;
  timestamp: Date;
}

interface ChatSidebarProps {
  sessions: ChatSession[];
  activeSessionId: string;
  collapsed: boolean;
  onToggle: () => void;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
}

const ChatSidebar = ({
  sessions,
  activeSessionId,
  collapsed,
  onToggle,
  onNewChat,
  onSelectSession,
}: ChatSidebarProps) => {
  return (
    <div
      className={cn(
        "fixed left-0 top-0 z-30 flex h-full flex-col transition-all duration-300 glass-panel",
        collapsed ? "w-14" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3">
        {!collapsed && (
          <span className="text-sm font-semibold text-primary neon-text-cyan tracking-wider">
            DREAM.AI
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-muted-foreground hover:text-primary"
          onClick={onToggle}
        >
          {collapsed ? <PanelLeft className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
        </Button>
      </div>

      {/* New Chat */}
      <div className="px-2 pb-2">
        <Button
          variant="outline"
          className={cn(
            "w-full border-border/50 bg-transparent hover:bg-muted hover:text-primary transition-all",
            collapsed ? "px-2" : "justify-start gap-2"
          )}
          onClick={onNewChat}
        >
          <Plus className="h-4 w-4 shrink-0" />
          {!collapsed && <span className="text-sm">New Chat</span>}
        </Button>
      </div>

      {/* Sessions */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-2 space-y-1">
        {sessions.map((session) => (
          <button
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm transition-all",
              session.id === activeSessionId
                ? "bg-primary/10 text-primary neon-glow-cyan"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            {!collapsed && (
              <span className="truncate">{session.title}</span>
            )}
          </button>
        ))}
      </div>

      {/* Footer */}
      {!collapsed && (
        <div className="border-t border-border/30 p-3">
          <p className="text-[10px] text-muted-foreground/50 text-center">
            Autonomous RL Training Platform
          </p>
        </div>
      )}
    </div>
  );
};

export default ChatSidebar;
