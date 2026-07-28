"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Package, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Categoria, ChebyshevRow, Publicacion } from "@/lib/types";
import { Button } from "@/components/ui/Button";
import { Input, Select, Label } from "@/components/ui/Input";
import { Badge, ChebyshevBadge } from "@/components/ui/Badge";
import { formatCOP, shortDiagnostico } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";

type Filters = {
  id_categoria: string;
  tipo_item: string;
  precio_min: string;
  precio_max: string;
  q: string;
};

function PublicationCard({
  item,
  demand,
}: {
  item: Publicacion;
  demand?: string | null;
}) {
  const price =
    item.tipo_item === "Servicio"
      ? `${formatCOP(item.servicio?.tarifa_por_hora ?? item.precio_efectivo)}/h`
      : formatCOP(item.producto?.precio ?? item.precio_efectivo);
  const stock = item.producto?.stock;
  const rating =
    item.producto?.calificacion ?? item.servicio?.calificacion ?? null;

  return (
    <Link
      href={`/publication/${item.id_publicacion}`}
      className="group panel flex h-full flex-col transition hover:-translate-y-0.5 hover:border-campus-400/50"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <Badge tone={item.tipo_item === "Producto" ? "campus" : "ember"}>
          {item.tipo_item}
        </Badge>
        <ChebyshevBadge diagnostico={demand} />
      </div>
      <h3 className="font-display text-lg leading-snug text-ink-900 group-hover:text-campus-700">
        {item.titulo}
      </h3>
      <p className="mt-2 line-clamp-2 flex-1 text-sm text-ink-700/65">
        {item.descripcion || "Sin descripción"}
      </p>
      <div className="mt-4 flex items-end justify-between gap-3 border-t border-ink-800/5 pt-3">
        <div>
          <div className="text-lg font-semibold text-ink-900">{price}</div>
          <div className="text-xs text-ink-700/55">
            {item.vendedor_nombre || "Vendedor"}
            {rating != null ? ` · ★ ${Number(rating).toFixed(1)}` : ""}
          </div>
        </div>
        {item.tipo_item === "Producto" && (
          <div
            className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
              (stock ?? 0) > 0
                ? "bg-campus-100 text-campus-700"
                : "bg-red-100 text-red-700"
            }`}
          >
            Stock {stock ?? 0}
          </div>
        )}
      </div>
    </Link>
  );
}

export function CatalogView({
  initialQ = "",
  showHero = false,
}: {
  initialQ?: string;
  showHero?: boolean;
}) {
  const toast = useToast();
  const [categories, setCategories] = useState<Categoria[]>([]);
  const [items, setItems] = useState<Publicacion[]>([]);
  const [total, setTotal] = useState(0);
  const [cheby, setCheby] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<Filters>({
    id_categoria: "",
    tipo_item: "",
    precio_min: "",
    precio_max: "",
    q: initialQ,
  });

  useEffect(() => {
    setFilters((f) => ({ ...f, q: initialQ }));
  }, [initialQ]);

  useEffect(() => {
    api.categories().then(setCategories).catch(() => undefined);
    api
      .chebyshev()
      .then((rows: ChebyshevRow[]) => {
        const map: Record<number, string> = {};
        rows.forEach((r) => {
          map[r.id_producto] = r.diagnostico_chebyshev;
        });
        setCheby(map);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const data = await api.publications({
          id_categoria: filters.id_categoria || null,
          tipo_item: filters.tipo_item || null,
          precio_min: filters.precio_min || null,
          precio_max: filters.precio_max || null,
          q: filters.q || null,
          limit: 24,
          offset: 0,
        });
        if (!cancelled) {
          setItems(data.items);
          setTotal(data.total);
        }
      } catch (e) {
        if (!cancelled) {
          toast.error(e instanceof ApiError ? e.detail : "No se pudo cargar el catálogo");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  const demandStats = useMemo(() => {
    let atipico = 0;
    let bajas = 0;
    let normal = 0;
    items.forEach((it) => {
      const id = it.producto?.id_producto;
      if (!id) return;
      const k = shortDiagnostico(cheby[id]);
      if (k === "atipico") atipico += 1;
      else if (k === "bajas") bajas += 1;
      else if (k === "normal") normal += 1;
    });
    return { atipico, bajas, normal };
  }, [items, cheby]);

  return (
    <div className="space-y-6">
      {showHero && (
        <section className="relative overflow-hidden rounded-[1.75rem] border border-ink-800/10 bg-ink-900 text-white">
          <div
            className="absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "radial-gradient(circle at 20% 20%, rgba(58,168,130,0.55), transparent 40%), radial-gradient(circle at 80% 0%, rgba(240,180,41,0.35), transparent 35%)",
            }}
          />
          <div className="relative grid gap-8 px-6 py-10 md:grid-cols-[1.2fr_0.8fr] md:px-10 md:py-14">
            <div>
              <p className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-campus-200">
                <Sparkles className="h-3.5 w-3.5" /> Marketplace universitario
              </p>
              <h1 className="font-display text-4xl leading-[1.05] tracking-tight md:text-5xl">
                UNTrade
              </h1>
              <p className="mt-4 max-w-xl text-base text-white/75 md:text-lg">
                Compra, ofrece, intercambia y presta entre campus. Catálogo vivo
                conectado a MySQL UnTrade.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link href="/catalog">
                  <Button variant="ember">
                    Explorar marketplace <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link href="/register">
                  <Button variant="secondary" className="border-white/20 bg-white/10 text-white hover:bg-white/20">
                    Crear cuenta
                  </Button>
                </Link>
              </div>
            </div>
            <div className="grid content-end gap-3 sm:grid-cols-3 md:grid-cols-1 lg:grid-cols-3">
              {[
                { label: "Listings", value: total },
                { label: "Éxito atípico", value: demandStats.atipico },
                { label: "Demanda normal", value: demandStats.normal },
              ].map((s) => (
                <div key={s.label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="text-2xl font-semibold">{s.value}</div>
                  <div className="text-xs uppercase tracking-wide text-white/55">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className="panel h-fit space-y-4 lg:sticky lg:top-24">
          <div className="flex items-center gap-2">
            <Package className="h-4 w-4 text-campus-600" />
            <h2 className="font-display text-lg">Filtros</h2>
          </div>

          <div>
            <Label>Búsqueda</Label>
            <Input
              value={filters.q}
              onChange={(e) => setFilters((f) => ({ ...f, q: e.target.value }))}
              placeholder="Título o descripción"
            />
          </div>
          <div>
            <Label>Categoría</Label>
            <Select
              value={filters.id_categoria}
              onChange={(e) => setFilters((f) => ({ ...f, id_categoria: e.target.value }))}
            >
              <option value="">Todas</option>
              {categories.map((c) => (
                <option key={c.id_categoria} value={c.id_categoria}>
                  {c.nombre}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Tipo</Label>
            <Select
              value={filters.tipo_item}
              onChange={(e) => setFilters((f) => ({ ...f, tipo_item: e.target.value }))}
            >
              <option value="">Producto y Servicio</option>
              <option value="Producto">Producto</option>
              <option value="Servicio">Servicio</option>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label>Precio min</Label>
              <Input
                type="number"
                min={0}
                value={filters.precio_min}
                onChange={(e) => setFilters((f) => ({ ...f, precio_min: e.target.value }))}
              />
            </div>
            <div>
              <Label>Precio max</Label>
              <Input
                type="number"
                min={0}
                value={filters.precio_max}
                onChange={(e) => setFilters((f) => ({ ...f, precio_max: e.target.value }))}
              />
            </div>
          </div>
          <Button
            variant="secondary"
            className="w-full"
            onClick={() =>
              setFilters({
                id_categoria: "",
                tipo_item: "",
                precio_min: "",
                precio_max: "",
                q: "",
              })
            }
          >
            Limpiar filtros
          </Button>
        </aside>

        <section>
          <div className="mb-4 flex items-end justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl text-ink-900">Catálogo</h2>
              <p className="text-sm text-ink-700/60">{total} publicaciones activas</p>
            </div>
          </div>

          {loading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="panel h-52 animate-pulse bg-ink-800/5" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="panel text-center text-ink-700/60">No hay resultados con estos filtros.</div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {items.map((item) => (
                <PublicationCard
                  key={item.id_publicacion}
                  item={item}
                  demand={
                    item.producto?.id_producto
                      ? cheby[item.producto.id_producto]
                      : null
                  }
                />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
