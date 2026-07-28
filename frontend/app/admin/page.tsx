"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ScrollText, TrendingUp } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Auditoria, IngresoAcumulado, PrestamoRiesgo } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { formatCOP } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import Link from "next/link";

type Tab = "loans" | "revenue" | "audit";

export default function AdminPage() {
  const { user, hasRole } = useAuth();
  const toast = useToast();
  const [tab, setTab] = useState<Tab>("loans");
  const [loans, setLoans] = useState<PrestamoRiesgo[]>([]);
  const [revenue, setRevenue] = useState<IngresoAcumulado[]>([]);
  const [audit, setAudit] = useState<Auditoria[]>([]);
  const [auditQ, setAuditQ] = useState("");
  const [loading, setLoading] = useState(false);

  const [sanctionOpen, setSanctionOpen] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<PrestamoRiesgo | null>(null);
  const [motivo, setMotivo] = useState("Mora en devolución de préstamo");
  const [monto, setMonto] = useState("25000");
  const [busy, setBusy] = useState(false);

  const canAdmin = hasRole("administrador");

  const loadTab = async (t: Tab) => {
    if (!canAdmin) return;
    setLoading(true);
    try {
      if (t === "loans") setLoans(await api.overdueLoans());
      if (t === "revenue") setRevenue(await api.revenue(250));
      if (t === "audit") setAudit(await api.audit({ limit: 150 }));
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "Error cargando panel admin");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (canAdmin) loadTab(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, canAdmin]);

  const filteredAudit = useMemo(() => {
    const q = auditQ.trim().toLowerCase();
    if (!q) return audit;
    return audit.filter(
      (a) =>
        a.tipo_evento.toLowerCase().includes(q) ||
        a.detalle_evento.toLowerCase().includes(q) ||
        a.usuario_auditor.toLowerCase().includes(q),
    );
  }, [audit, auditQ]);

  const maxIngreso = useMemo(
    () => Math.max(...revenue.map((r) => Number(r.ingreso_acumulado) || 0), 1),
    [revenue],
  );

  const onSanction = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedLoan || !user) return;
    setBusy(true);
    try {
      await api.applySanction({
        p_id_prestamo: selectedLoan.id_prestamo,
        p_id_administrador: user.id_usuario,
        p_motivo: motivo,
        p_monto_incremento: Number(monto),
      });
      toast.success("Sanción aplicada");
      setSanctionOpen(false);
      await loadTab("loans");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo sancionar");
    } finally {
      setBusy(false);
    }
  };

  if (!user) {
    return (
      <div className="panel text-center">
        <p>Debes iniciar sesión como administrador.</p>
        <Link href="/login" className="mt-3 inline-block text-campus-700 underline">
          Ir a login
        </Link>
      </div>
    );
  }

  if (!canAdmin) {
    return (
      <div className="panel text-center">
        <p className="text-ink-700/70">
          Tu cuenta no tiene rol <strong>administrador</strong>.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl text-ink-900">Admin Console</h1>
        <p className="text-sm text-ink-700/60">
          Moderación de mora, ingresos acumulados y auditoría transaccional.
        </p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            { id: "loans", label: "Préstamos vencidos", icon: AlertTriangle },
            { id: "revenue", label: "Ingresos", icon: TrendingUp },
            { id: "audit", label: "Auditoría", icon: ScrollText },
          ] as const
        ).map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition ${
              tab === id
                ? "bg-ink-900 text-white"
                : "bg-white text-ink-700 border border-ink-800/10 hover:bg-ink-800/5"
            }`}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="panel h-56 animate-pulse" />
      ) : tab === "loans" ? (
        <section className="panel">
          <h2 className="mb-1 font-display text-xl">vw_prestamos_riesgo</h2>
          <p className="mb-4 text-xs text-ink-700/55">
            Préstamos activos con fecha de devolución vencida.
          </p>
          {loans.length === 0 ? (
            <p className="text-sm text-ink-700/60">No hay préstamos en mora ahora.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-ink-700/50">
                  <tr>
                    <th className="px-2 py-2">Rank mora</th>
                    <th className="px-2 py-2">Préstamo</th>
                    <th className="px-2 py-2">Deudor</th>
                    <th className="px-2 py-2">Ítem</th>
                    <th className="px-2 py-2">Días atraso</th>
                    <th className="px-2 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {loans.map((l) => (
                    <tr key={l.id_prestamo} className="border-t border-ink-800/5">
                      <td className="px-2 py-2 font-semibold">#{l.ranking_mora}</td>
                      <td className="px-2 py-2">{l.id_prestamo}</td>
                      <td className="px-2 py-2">{l.deudor}</td>
                      <td className="px-2 py-2">{l.item_prestado}</td>
                      <td className="px-2 py-2 text-red-700">{l.dias_retraso}</td>
                      <td className="px-2 py-2 text-right">
                        <Button
                          size="sm"
                          variant="danger"
                          onClick={() => {
                            setSelectedLoan(l);
                            setSanctionOpen(true);
                          }}
                        >
                          Sancionar
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      ) : tab === "revenue" ? (
        <section className="panel space-y-4">
          <div>
            <h2 className="font-display text-xl">vw_ingresos_acumulados</h2>
            <p className="text-xs text-ink-700/55">
              Progresión acumulada de montos de compra.
            </p>
          </div>
          <div className="flex h-40 items-end gap-1 overflow-x-auto rounded-xl bg-ink-800/[0.03] p-3">
            {revenue.slice(-80).map((r, idx) => {
              const h = (Number(r.ingreso_acumulado) / maxIngreso) * 100;
              return (
                <div
                  key={`${r.fecha_transaccion}-${idx}`}
                  title={`${r.fecha_transaccion}: ${formatCOP(r.ingreso_acumulado)}`}
                  className="min-w-[6px] flex-1 rounded-t bg-gradient-to-t from-campus-700 to-ember-400"
                  style={{ height: `${Math.max(h, 4)}%` }}
                />
              );
            })}
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-ink-700/50">
                <tr>
                  <th className="px-2 py-2">Fecha</th>
                  <th className="px-2 py-2">Monto</th>
                  <th className="px-2 py-2">Acumulado</th>
                </tr>
              </thead>
              <tbody>
                {revenue.slice(-30).reverse().map((r, idx) => (
                  <tr key={`${r.fecha_transaccion}-${idx}`} className="border-t border-ink-800/5">
                    <td className="px-2 py-2">{new Date(r.fecha_transaccion).toLocaleString("es-CO")}</td>
                    <td className="px-2 py-2">{formatCOP(r.monto_total)}</td>
                    <td className="px-2 py-2 font-medium">{formatCOP(r.ingreso_acumulado)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : (
        <section className="panel space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-xl">AUDITORIA_TRANSACCIONES</h2>
              <p className="text-xs text-ink-700/55">Visor de eventos recientes.</p>
            </div>
            <Input
              className="max-w-xs"
              placeholder="Buscar tipo, detalle, usuario…"
              value={auditQ}
              onChange={(e) => setAuditQ(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            {filteredAudit.map((a) => (
              <article
                key={a.id_auditoria}
                className="rounded-xl border border-ink-800/8 bg-white px-3 py-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="rounded-full bg-ink-900 px-2.5 py-0.5 text-xs font-semibold text-white">
                    {a.tipo_evento}
                  </span>
                  <span className="text-xs text-ink-700/50">
                    {new Date(a.fecha_registro).toLocaleString("es-CO")}
                  </span>
                </div>
                <p className="mt-2 text-sm text-ink-800">{a.detalle_evento}</p>
                <p className="mt-1 text-xs text-ink-700/50">auditor: {a.usuario_auditor}</p>
              </article>
            ))}
            {filteredAudit.length === 0 && (
              <p className="text-sm text-ink-700/60">Sin eventos para ese filtro.</p>
            )}
          </div>
        </section>
      )}

      <Modal
        open={sanctionOpen}
        onClose={() => setSanctionOpen(false)}
        title="Aplicar sanción"
      >
        <form onSubmit={onSanction} className="space-y-4">
          <p className="text-sm text-ink-700/70">
            `CALL aplicar_sancion` sobre préstamo{" "}
            <strong>#{selectedLoan?.id_prestamo}</strong> ({selectedLoan?.deudor}).
          </p>
          <div>
            <Label>Motivo</Label>
            <Textarea
              required
              minLength={5}
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
            />
          </div>
          <div>
            <Label>Monto multa (COP)</Label>
            <Input
              type="number"
              min={0}
              required
              value={monto}
              onChange={(e) => setMonto(e.target.value)}
            />
          </div>
          <Button type="submit" variant="danger" className="w-full" disabled={busy}>
            {busy ? "Aplicando…" : "Confirmar sanción"}
          </Button>
        </form>
      </Modal>
    </div>
  );
}
