import { useEffect, useRef, useState } from "react";
import { LogsSocket, buildLogsSocketUrl, type LogEntry, type WsEvent } from "@/lib/ws";

const MAX_LOGS = 800;

interface State {
  logs: LogEntry[];
  connected: boolean;
}

export function useLogsSocket() {
  const [state, setState] = useState<State>({ logs: [], connected: false });
  const socketRef = useRef<LogsSocket | null>(null);

  useEffect(() => {
    const socket = new LogsSocket(buildLogsSocketUrl());
    socketRef.current = socket;

    const unsub = socket.subscribe((event: WsEvent) => {
      setState((prev) => {
        if (event.event === "history" && Array.isArray(event.data)) {
          return { ...prev, logs: event.data as LogEntry[], connected: true };
        }
        if (event.event === "log" && event.data) {
          const next = [...prev.logs, event.data as LogEntry];
          if (next.length > MAX_LOGS) next.splice(0, next.length - MAX_LOGS);
          return { ...prev, logs: next, connected: true };
        }
        return prev;
      });
    });

    const ws = socket as unknown as { ws: WebSocket | null };
    const connectionPoll = window.setInterval(() => {
      setState((prev) => ({
        ...prev,
        connected: ws.ws?.readyState === WebSocket.OPEN,
      }));
    }, 2000);

    socket.connect();
    return () => {
      unsub();
      window.clearInterval(connectionPoll);
      socket.disconnect();
    };
  }, []);

  return state;
}
