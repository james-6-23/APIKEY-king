export type LogLevel = "info" | "success" | "warning" | "error" | "debug";

export interface LogEntry {
  type: LogLevel | string;
  message: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export interface WsEvent {
  event: "log" | "history" | "stats" | string;
  data: unknown;
}

type Listener = (event: WsEvent) => void;

export class LogsSocket {
  private url: string;
  private ws: WebSocket | null = null;
  private listeners = new Set<Listener>();
  private stopped = false;
  private retry = 0;

  constructor(url: string) {
    this.url = url;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }
    const ws = new WebSocket(this.url);
    this.ws = ws;

    ws.onopen = () => {
      this.retry = 0;
    };
    ws.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data as string) as WsEvent;
        this.listeners.forEach((l) => l(payload));
      } catch {
        // ignore malformed frame
      }
    };
    ws.onerror = () => {
      // onclose will handle reconnection
    };
    ws.onclose = () => {
      this.ws = null;
      if (this.stopped) return;
      const delay = Math.min(15000, 500 * 2 ** this.retry++);
      setTimeout(() => this.connect(), delay);
    };
  }

  disconnect() {
    this.stopped = true;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(listener: Listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export function buildLogsSocketUrl(): string {
  const { protocol, host } = window.location;
  const wsProto = protocol === "https:" ? "wss:" : "ws:";
  return `${wsProto}//${host}/ws/logs`;
}
