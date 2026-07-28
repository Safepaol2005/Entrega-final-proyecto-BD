import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCOP(value: number | string | null | undefined) {
  const n = typeof value === "string" ? Number(value) : value ?? 0;
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(n) ? n : 0);
}

export function shortDiagnostico(raw: string | undefined | null): "atipico" | "bajas" | "normal" | null {
  if (!raw) return null;
  const t = raw.toLowerCase();
  if (t.includes("exito") || t.includes("atipico") || t.includes("atípico")) return "atipico";
  if (t.includes("bajas")) return "bajas";
  if (t.includes("normal")) return "normal";
  return null;
}
