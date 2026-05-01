import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from "lucide-react";
import { cn } from "@/lib/cn";

type ToastVariant = "default" | "success" | "error" | "warning" | "info";

interface ToastItem {
  id: string;
  title?: ReactNode;
  description?: ReactNode;
  variant: ToastVariant;
  duration?: number;
}

interface ToastContextValue {
  toast: (t: Omit<ToastItem, "id" | "variant"> & { variant?: ToastVariant }) => void;
  success: (title: ReactNode, description?: ReactNode) => void;
  error: (title: ReactNode, description?: ReactNode) => void;
  info: (title: ReactNode, description?: ReactNode) => void;
  warning: (title: ReactNode, description?: ReactNode) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const variantIcon: Record<ToastVariant, typeof CheckCircle2> = {
  default: Info,
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const variantClasses: Record<ToastVariant, string> = {
  default: "border-border",
  success: "border-[--color-success]/40",
  error: "border-destructive/40",
  warning: "border-[--color-warning]/40",
  info: "border-[--color-info]/40",
};

const iconClasses: Record<ToastVariant, string> = {
  default: "text-muted-foreground",
  success: "text-[color:var(--color-success)]",
  error: "text-destructive",
  warning: "text-[color:var(--color-warning)]",
  info: "text-[color:var(--color-info)]",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((input: Omit<ToastItem, "id" | "variant"> & { variant?: ToastVariant }) => {
    const id = Math.random().toString(36).slice(2);
    setItems((prev) => [...prev, { id, variant: "default", ...input }]);
  }, []);

  const value = useMemo<ToastContextValue>(
    () => ({
      toast: push,
      success: (title, description) => push({ title, description, variant: "success" }),
      error: (title, description) => push({ title, description, variant: "error" }),
      info: (title, description) => push({ title, description, variant: "info" }),
      warning: (title, description) => push({ title, description, variant: "warning" }),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      <ToastPrimitive.Provider swipeDirection="right" duration={4000}>
        {children}
        {items.map((t) => {
          const Icon = variantIcon[t.variant];
          return (
            <ToastPrimitive.Root
              key={t.id}
              duration={t.duration ?? 4000}
              onOpenChange={(open) => {
                if (!open) dismiss(t.id);
              }}
              className={cn(
                "group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-lg border bg-card p-4 pr-8 text-card-foreground shadow-lg",
                "data-[state=open]:animate-[slide-in-right_180ms_ease-out] data-[state=closed]:animate-[fade-out_150ms_ease-out]",
                variantClasses[t.variant],
              )}
            >
              <Icon className={cn("mt-0.5 h-5 w-5 shrink-0", iconClasses[t.variant])} />
              <div className="flex-1 space-y-1">
                {t.title ? (
                  <ToastPrimitive.Title className="text-sm font-medium leading-none">
                    {t.title}
                  </ToastPrimitive.Title>
                ) : null}
                {t.description ? (
                  <ToastPrimitive.Description className="text-sm text-muted-foreground">
                    {t.description}
                  </ToastPrimitive.Description>
                ) : null}
              </div>
              <ToastPrimitive.Close
                aria-label="Close"
                className="absolute right-2 top-2 rounded-md p-1 text-muted-foreground opacity-70 transition hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X className="h-4 w-4" />
              </ToastPrimitive.Close>
            </ToastPrimitive.Root>
          );
        })}
        <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-[100] flex max-h-screen w-[380px] max-w-[92vw] flex-col gap-2 outline-none" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
