"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { cn } from "@/lib/utils";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";

type ToastTone = "success" | "error" | "info";

type ToastItem = {
  id: number;
  message: string;
  tone: ToastTone;
};

type ToastContextValue = {
  push: (message: string, tone?: ToastTone) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);

  const push = useCallback((message: string, tone: ToastTone = "info") => {
    const id = Date.now() + Math.random();
    setItems((prev) => [...prev, { id, message, tone }]);
    window.setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id));
    }, 5200);
  }, []);

  const value = useMemo(
    () => ({
      push,
      success: (m: string) => push(m, "success"),
      error: (m: string) => push(m, "error"),
      info: (m: string) => push(m, "info"),
    }),
    [push],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[min(100%-2rem,24rem)] flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              "pointer-events-auto flex items-start gap-3 rounded-2xl border px-4 py-3 shadow-lift backdrop-blur",
              t.tone === "success" && "border-campus-300 bg-campus-50 text-campus-700",
              t.tone === "error" && "border-red-200 bg-red-50 text-red-800",
              t.tone === "info" && "border-ink-800/10 bg-white text-ink-800",
            )}
          >
            {t.tone === "success" && <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0" />}
            {t.tone === "error" && <XCircle className="mt-0.5 h-5 w-5 shrink-0" />}
            {t.tone === "info" && <Info className="mt-0.5 h-5 w-5 shrink-0" />}
            <p className="flex-1 text-sm leading-snug">{t.message}</p>
            <button
              type="button"
              className="opacity-60 hover:opacity-100"
              onClick={() => setItems((prev) => prev.filter((x) => x.id !== t.id))}
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
