/**
 * DREAM.AI backend configuration.
 * In dev with Vite proxy: uses relative URLs so /api and /ws proxy to backend.
 * In prod: uses VITE_DREAMAI_API_URL and VITE_DREAMAI_WS_URL.
 */
const isDev = import.meta.env.DEV;

export const dreamaiConfig = {
  apiUrl: isDev
    ? ""
    : (import.meta.env.VITE_DREAMAI_API_URL ?? "http://localhost:8000").replace(
        /\/$/,
        ""
      ),
  wsUrl: isDev
    ? (typeof window !== "undefined"
        ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
        : "ws://localhost:8080")
    : (import.meta.env.VITE_DREAMAI_WS_URL ?? "ws://localhost:8000").replace(
        /\/$/,
        ""
      ),
} as const;

export function getDreamAiApiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return dreamaiConfig.apiUrl ? `${dreamaiConfig.apiUrl}${p}` : p;
}

export function getDreamAiWsGameUrl(): string {
  const base = dreamaiConfig.wsUrl;
  return base.endsWith("/ws/game") ? base : `${base}/ws/game`;
}
