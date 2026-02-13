import { useState, useRef, useEffect } from "react";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  isLoading: boolean;
  onSend: (message: string) => void;
  sidebarCollapsed: boolean;
}

const SUGGESTIONS = [
  "Train an agent to navigate a maze",
  "Set up a CartPole balancing environment",
  "Design a multi-agent competitive arena",
  "Create a custom reward function for robotics",
];

const ChatInterface = ({ messages, isLoading, onSend, sidebarCollapsed }: ChatInterfaceProps) => {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");
  };

  const showWelcome = messages.length === 0;

  return (
    <div
      className={cn(
        "flex flex-col h-screen transition-all duration-300",
        sidebarCollapsed ? "ml-14" : "ml-64"
      )}
    >
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin px-4 py-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {showWelcome && (
            <div className="flex flex-col items-center justify-center pt-[20vh] space-y-8">
              <div className="text-center space-y-3">
                <h1 className="text-4xl font-bold text-primary neon-text-cyan tracking-tight">
                  Dream.AI
                </h1>
                <p className="text-muted-foreground text-sm max-w-md">
                  Configure and launch autonomous RL agent training in self-adapting environments. 
                  Describe what you want your agent to learn.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 w-full max-w-lg">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => onSend(s)}
                    className="glass-panel rounded-xl p-3 text-left text-sm text-muted-foreground hover:text-foreground hover:border-primary/30 hover:neon-glow-cyan transition-all"
                  >
                    <Sparkles className="h-3 w-3 text-primary mb-1" />
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={cn(
                "flex",
                msg.role === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[80%] rounded-2xl px-4 py-3 text-sm",
                  msg.role === "user"
                    ? "bg-primary/15 text-foreground border border-primary/20"
                    : "glass-panel text-foreground"
                )}
              >
                {msg.role === "assistant" ? (
                  <div className="prose prose-invert prose-sm max-w-none [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}

          {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
            <div className="flex justify-start">
              <div className="glass-panel rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-pulse [animation-delay:0.2s]" />
                  <span className="h-2 w-2 rounded-full bg-primary animate-pulse [animation-delay:0.4s]" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input bar */}
      <div className="border-t border-border/30 p-4">
        <form onSubmit={handleSubmit} className="mx-auto max-w-2xl">
          <div className="flex items-center gap-2 glass-panel rounded-xl px-4 py-2 neon-glow-cyan">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe your RL training task..."
              className="flex-1 bg-transparent text-sm text-foreground placeholder:text-muted-foreground/50 outline-none"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              variant="ghost"
              disabled={!input.trim() || isLoading}
              className="h-8 w-8 text-primary hover:text-primary hover:bg-primary/10"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
