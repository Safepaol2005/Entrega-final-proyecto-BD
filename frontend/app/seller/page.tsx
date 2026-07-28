"use client";

import { useEffect, useState } from "react";
import { RefreshCw, Trophy } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Publicacion, RankingVendedor } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { formatCOP } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import Link from "next/link";

export default function SellerHubPage() {
  const { user, hasRole } = useAuth();
  const toast = useToast();
  const [ranking, setRanking] = useState<RankingVendedor[]>([]);
  const [listings, setListings] = useState<Publicacion[]>([]);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const [rank, pubs] = await Promise.all([
        api.sellerRanking(),
        api.publications({ limit: 50 }),
      ]);
      setRanking(rank);
      if (user) {
        setListings(pubs.items.filter((p) => p.id_vendedor === user.id_usuario));
      } else {
        setListings([]);
      }
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "No se pudo cargar Seller Hub");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id_usuario]);

  const onRate = async () => {
    if (!user) {
      toast.info("Inicia sesión");
      return;
    }
    if (!hasRole("vendedor")) {
      toast.error("Necesitas rol Vendedor");
      return;
    }
    setBusy(true);
    try {
      const res = await api.rateSeller(user.id_usuario);
      toast.success(`Calificación actualizada: ${res.calificacion}`);
      await load();
    } catch (e) {
      toast.error(e instanceof ApiError ? e.detail : "No se pudo recalcular");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-ink-900">Seller Hub</h1>
          <p className="text-sm text-ink-700/60">
            Listings activos, recalculo de rating y ranking de fiabilidad.
          </p>
        </div>
        <Button onClick={onRate} disabled={busy || !hasRole("vendedor")}>
          <RefreshCw className={`h-4 w-4 ${busy ? "animate-spin" : ""}`} />
          Recalcular mi rating
        </Button>
      </div>

      <section className="panel">
        <h2 className="mb-3 font-display text-xl">Mis publicaciones</h2>
        {!user ? (
          <p className="text-sm text-ink-700/60">
            <Link href="/login" className="text-campus-700 underline">
              Inicia sesión
            </Link>{" "}
            como vendedor para ver tus listings.
          </p>
        ) : loading ? (
          <div className="h-24 animate-pulse rounded-xl bg-ink-800/5" />
        ) : listings.length === 0 ? (
          <p className="text-sm text-ink-700/60">Aún no tienes publicaciones activas visibles.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-ink-700/50">
                <tr>
                  <th className="px-2 py-2">ID</th>
                  <th className="px-2 py-2">Título</th>
                  <th className="px-2 py-2">Tipo</th>
                  <th className="px-2 py-2">Precio</th>
                  <th className="px-2 py-2">Estado</th>
                </tr>
              </thead>
              <tbody>
                {listings.map((l) => (
                  <tr key={l.id_publicacion} className="border-t border-ink-800/5">
                    <td className="px-2 py-2">{l.id_publicacion}</td>
                    <td className="px-2 py-2">
                      <Link
                        href={`/publication/${l.id_publicacion}`}
                        className="font-medium text-campus-700 hover:underline"
                      >
                        {l.titulo}
                      </Link>
                    </td>
                    <td className="px-2 py-2">
                      <Badge tone={l.tipo_item === "Producto" ? "campus" : "ember"}>
                        {l.tipo_item}
                      </Badge>
                    </td>
                    <td className="px-2 py-2">{formatCOP(l.precio_efectivo)}</td>
                    <td className="px-2 py-2">{l.estado_publicacion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel">
        <div className="mb-3 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-ember-500" />
          <h2 className="font-display text-xl">Leaderboard de fiabilidad</h2>
        </div>
        <p className="mb-4 text-xs text-ink-700/55">
          Fuente: `vista_ranking_vendedores` (ventas_completadas ≥ 10).
        </p>
        {loading ? (
          <div className="h-40 animate-pulse rounded-xl bg-ink-800/5" />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-ink-700/50">
                <tr>
                  <th className="px-2 py-2">Rank</th>
                  <th className="px-2 py-2">Vendedor</th>
                  <th className="px-2 py-2">Fiabilidad</th>
                  <th className="px-2 py-2">Δ puesto</th>
                  <th className="px-2 py-2">Ventas</th>
                  <th className="px-2 py-2">Rating</th>
                </tr>
              </thead>
              <tbody>
                {ranking.slice(0, 40).map((r) => (
                  <tr
                    key={r.id_vendedor}
                    className={`border-t border-ink-800/5 ${
                      user?.id_usuario === r.id_vendedor ? "bg-campus-50" : ""
                    }`}
                  >
                    <td className="px-2 py-2 font-semibold">#{r.ranking_fiabilidad}</td>
                    <td className="px-2 py-2">
                      {r.vendedor_nombre || `Vendedor ${r.id_vendedor}`}
                    </td>
                    <td className="px-2 py-2">{r.fiabilidad}</td>
                    <td className="px-2 py-2">{r.diferencia_con_puesto_anterior ?? 0}</td>
                    <td className="px-2 py-2">{r.ventas_completadas}</td>
                    <td className="px-2 py-2">{r.calificacion_actual}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
