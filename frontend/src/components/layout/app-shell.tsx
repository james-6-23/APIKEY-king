import type { ReactNode } from "react";
import { TopBar } from "./top-bar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-col">
      <TopBar />
      <main className="mx-auto w-full max-w-[1600px] flex-1 px-4 py-6 sm:px-6">
        {children}
      </main>
      <footer className="border-t py-4 text-center text-xs text-muted-foreground">
        <span className="mono">APIKEY-king</span> · v1.0
      </footer>
    </div>
  );
}
