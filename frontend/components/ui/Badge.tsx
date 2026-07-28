"use client";

import { cn, shortDiagnostico } from "@/lib/utils";

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: "neutral" | "campus" | "ember" | "danger" | "ink";
  className?: string;
}) {
  const tones = {
    neutral: "bg-ink-800/8 text-ink-700",
    campus: "bg-campus-100 text-campus-700",
    ember: "bg-ember-400/25 text-ember-600",
    danger: "bg-red-100 text-red-700",
    ink: "bg-ink-900 text-white",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function RoleBadges({ roles }: { roles: string[] }) {
  const map: Record<string, { label: string; tone: "campus" | "ember" | "ink" }> = {
    comprador: { label: "Comprador", tone: "campus" },
    vendedor: { label: "Vendedor", tone: "ember" },
    administrador: { label: "Admin", tone: "ink" },
  };
  return (
    <div className="flex flex-wrap gap-1.5">
      {roles.map((r) => {
        const m = map[r] || { label: r, tone: "campus" as const };
        return (
          <Badge key={r} tone={m.tone}>
            {m.label}
          </Badge>
        );
      })}
    </div>
  );
}

export function ChebyshevBadge({ diagnostico }: { diagnostico?: string | null }) {
  const kind = shortDiagnostico(diagnostico);
  if (!kind) return null;
  if (kind === "atipico") {
    return <Badge tone="ember">Éxito atípico</Badge>;
  }
  if (kind === "bajas") {
    return <Badge tone="danger">Ventas muy bajas</Badge>;
  }
  return <Badge tone="campus">Normal</Badge>;
}
