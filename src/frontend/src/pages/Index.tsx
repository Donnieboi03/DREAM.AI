import { useState, useCallback, useRef } from "react";
import { toast } from "sonner";
import ParticleBackground from "@/components/ParticleBackground";
import ChatSidebar, { type ChatSession } from "@/components/ChatSidebar";
import ChatInterface, { type Message } from "@/components/ChatInterface";
import ControlPanel from "@/components/ControlPanel";
import GameViewport, { type GameViewportHandle } from "@/components/GameViewport";
import ActionPanel from "@/components/ActionPanel";
import TaskDisplay from "@/components/TaskDisplay";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { generateTask, type TaskSpec } from "@/lib/dreamaiApi";
import { useMetrics } from "@/hooks/useMetrics";

const Index = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([
    { id: "1", title: "Maze Navigation Agent", timestamp: new Date() },
  ]);
  const [activeSessionId, setActiveSessionId] = useState("1");
  const [chatHistories, setChatHistories] = useState<Record<string, Message[]>>(
    {}
  );
  const [isLoading, setIsLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskSpec | null>(null);
  const [isViewportEnlarged, setIsViewportEnlarged] = useState(false);
  const [controlMode, setControlMode] = useState<"user" | "agent">("user");
  const gameViewportRef = useRef<GameViewportHandle>(null);
  const { metrics, rewardHistory, updateMetrics, clearMetrics } = useMetrics();

  const activeMessages = chatHistories[activeSessionId] || [];

  const setActiveMessages = useCallback(
    (updater: (prev: Message[]) => Message[]) => {
      setChatHistories((prev) => ({
        ...prev,
        [activeSessionId]: updater(prev[activeSessionId] || []),
      }));
    },
    [activeSessionId]
  );

  const handleNewChat = () => {
    const id = Date.now().toString();
    setSessions((prev) => [
      { id, title: "New Chat", timestamp: new Date() },
      ...prev,
    ]);
    setActiveSessionId(id);
  };

  const handleSend = async (input: string) => {
    const userMsg: Message = { role: "user", content: input };
    setActiveMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    if ((chatHistories[activeSessionId] || []).length === 0) {
      setSessions((prev) =>
        prev.map((s) =>
          s.id === activeSessionId
            ? {
                ...s,
                title: input.slice(0, 40) + (input.length > 40 ? "…" : ""),
              }
            : s
        )
      );
    }

    try {
      const res = await generateTask(input, 500);
      setCurrentTask(res.task);

      setActiveMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `**Task generated.**\n\nGoal: ${res.task.goal}\n\nLoading scene: ${res.scene_id}`,
        },
      ]);

      gameViewportRef.current?.loadScene(
        res.scene_id,
        res.task?.extra?.task_description_dict as Record<string, unknown> | undefined
      );
      toast.success("Task loaded. Scene is loading.");
    } catch (e) {
      console.error(e);
      const errMsg = e instanceof Error ? e.message : "Failed to generate task";
      toast.error(errMsg);
      setActiveMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${errMsg}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAction = (index: number) => {
    gameViewportRef.current?.sendAction(index);
  };

  const handleReset = () => {
    gameViewportRef.current?.reset();
    setCurrentTask(null);
    clearMetrics();
  };

  const handleControlModeChange = useCallback((mode: "user" | "agent") => {
    setControlMode(mode);
    gameViewportRef.current?.setControlMode(mode);
  }, []);

  return (
    <div className="relative h-screen w-full overflow-hidden flex">
      <ParticleBackground />
      <ChatSidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((p) => !p)}
        onNewChat={handleNewChat}
        onSelectSession={setActiveSessionId}
      />

      {/* Left: Chat */}
      <div
        className={cn(
          "flex flex-col flex-1 min-w-0 transition-all duration-300 border-r border-border/30",
          sidebarCollapsed ? "ml-14" : "ml-64"
        )}
      >
        <ChatInterface
          messages={activeMessages}
          isLoading={isLoading}
          onSend={handleSend}
          sidebarCollapsed={sidebarCollapsed}
        />
      </div>

      {/* Right: Game viewport + controls */}
      <div className="flex flex-col w-[480px] shrink-0 gap-3 p-4 overflow-y-auto">
        <GameViewport
          ref={gameViewportRef}
          onMetricsUpdate={updateMetrics}
          onEnlargedChange={setIsViewportEnlarged}
          userControlEnabled={controlMode === "user"}
        />
        {currentTask && <TaskDisplay task={currentTask} />}
        <div className="flex gap-2">
          <Button variant="destructive" size="sm" onClick={handleReset}>
            Reset Scene
          </Button>
        </div>
        <ActionPanel onAction={handleAction} />
      </div>

      <ControlPanel
        metrics={metrics}
        rewardHistory={rewardHistory}
        aboveOverlay={isViewportEnlarged}
        onReset={handleReset}
        onControlModeChange={handleControlModeChange}
      />
    </div>
  );
};

export default Index;
