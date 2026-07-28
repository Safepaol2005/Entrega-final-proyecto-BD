"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  Handshake,
  CalendarClock,
  ShoppingBag,
  Tag,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Publicacion } from "@/lib/types";
import { formatCOP } from "@/lib/utils";
import { Button } from "@/components/ui/Button";
import { Badge, ChebyshevBadge } from "@/components/ui/Badge";
import { Input, Label, Select } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { useToast } from "@/components/ui/Toast";

export default function PublicationDetailPage() {
  const params = useParams();
  const id = Number(params.id);
  const { user, hasRole } = useAuth();
  const toast = useToast();
  const router = useRouter();

  const [item, setItem] = useState<Publicacion | null>(null);
  const [demand, setDemand] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [myListings, setMyListings] = useState<Publicacion[]>([]);

  const [buyOpen, setBuyOpen] = useState(false);
  const [offerOpen, setOfferOpen] = useState(false);
  const [barterOpen, setBarterOpen] = useState(false);
  const [loanOpen, setLoanOpen] = useState(false);

  const [metodoPago, setMetodoPago] = useState("Transferencia");
  const [montoOferta, setMontoOferta] = useState("");
  const [offeredId, setOfferedId] = useState("");
  const [fechaDev, setFechaDev] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!Number.isFinite(id)) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const pub = await api.publication(id);
        if (cancelled) return;
        setItem(pub);
        const defaultPrice = Number(pub.precio_efectivo || 0);
        setMontoOferta(String(Math.round(defaultPrice * 0.9) || ""));
        if (pub.producto?.id_producto) {
          const rows = await api.chebyshev();
          const row = rows.find((r) => r.id_producto === pub.producto!.id_producto);
          setDemand(row?.diagnostico_chebyshev ?? null);
        }
      } catch (e) {
        toast.error(e instanceof ApiError ? e.detail : "Publicación no encontrada");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, toast]);

  useEffect(() => {
    if (!user || !hasRole("vendedor")) return;
    api
      .publications({ limit: 50 })
      .then((data) => {
        setMyListings(
          data.items.filter(
            (p) => p.id_vendedor === user.id_usuario && p.id_publicacion !== id,
          ),
        );
      })
      .catch(() => undefined);
  }, [user, hasRole, id]);

  const priceLabel = useMemo(() => {
    if (!item) return "";
    if (item.tipo_item === "Servicio") {
      return `${formatCOP(item.servicio?.tarifa_por_hora ?? item.precio_efectivo)} / hora`;
    }
    return formatCOP(item.producto?.precio ?? item.precio_efectivo);
  }, [item]);

  const requireBuyer = () => {
    if (!user) {
      toast.info("Inicia sesión para continuar");
      router.push("/login");
      return false;
    }
    if (!hasRole("comprador")) {
      toast.error("Necesitas rol Comprador para esta acción");
      return false;
    }
    return true;
  };

  const onBuy = async (e: FormEvent) => {
    e.preventDefault();
    if (!item || !requireBuyer()) return;
    setBusy(true);
    try {
      await api.buy({
        id_publicacion: item.id_publicacion,
        monto_total: Number(item.precio_efectivo || 0),
        metodo_pago: metodoPago,
      });
      toast.success("Compra registrada");
      setBuyOpen(false);
      const refreshed = await api.publication(item.id_publicacion);
      setItem(refreshed);
    } catch (err) {
      // Surface exact MySQL trigger MESSAGE_TEXT (HTTP 400)
      toast.error(err instanceof ApiError ? err.detail : "Compra rechazada");
    } finally {
      setBusy(false);
    }
  };

  const onOffer = async (e: FormEvent) => {
    e.preventDefault();
    if (!item || !requireBuyer()) return;
    setBusy(true);
    try {
      await api.offer({
        id_publicacion: item.id_publicacion,
        monto_ofertado: Number(montoOferta),
      });
      toast.success("Oferta enviada");
      setOfferOpen(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo crear la oferta");
    } finally {
      setBusy(false);
    }
  };

  const onBarter = async (e: FormEvent) => {
    e.preventDefault();
    if (!item || !requireBuyer()) return;
    if (!offeredId) {
      toast.error("Selecciona una publicación propia para ofrecer");
      return;
    }
    setBusy(true);
    try {
      await api.barter({
        id_publicacion_deseada: item.id_publicacion,
        id_publicacion_ofrecida: Number(offeredId),
      });
      toast.success("Trueque propuesto");
      setBarterOpen(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo proponer el trueque");
    } finally {
      setBusy(false);
    }
  };

  const onLoan = async (e: FormEvent) => {
    e.preventDefault();
    if (!item || !requireBuyer()) return;
    setBusy(true);
    try {
      await api.loan({
        id_publicacion: item.id_publicacion,
        fecha_devolucion_pactada: new Date(fechaDev).toISOString().slice(0, 19).replace("T", " "),
      });
      toast.success("Préstamo solicitado");
      setLoanOpen(false);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo solicitar el préstamo");
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="panel h-80 animate-pulse" />;
  }
  if (!item) {
    return (
      <div className="panel text-center">
        <p>Publicación no encontrada.</p>
        <Link href="/catalog" className="mt-3 inline-block text-campus-700">
          Volver al catálogo
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link
        href="/catalog"
        className="inline-flex items-center gap-2 text-sm font-medium text-ink-700/70 hover:text-campus-700"
      >
        <ArrowLeft className="h-4 w-4" /> Volver al marketplace
      </Link>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
        <section className="panel space-y-5">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={item.tipo_item === "Producto" ? "campus" : "ember"}>
              {item.tipo_item}
            </Badge>
            <Badge>{item.estado_publicacion}</Badge>
            <ChebyshevBadge diagnostico={demand} />
          </div>
          <h1 className="font-display text-3xl text-ink-900 md:text-4xl">{item.titulo}</h1>
          <p className="text-base leading-relaxed text-ink-700/75">
            {item.descripcion || "Sin descripción disponible."}
          </p>

          {item.tipo_item === "Producto" && item.producto && (
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat label="Precio" value={formatCOP(item.producto.precio)} />
              <Stat label="Estado" value={item.producto.estado_fisico} />
              <Stat label="Stock" value={String(item.producto.stock)} />
            </div>
          )}
          {item.tipo_item === "Servicio" && item.servicio && (
            <div className="grid gap-3 sm:grid-cols-3">
              <Stat label="Tarifa" value={`${formatCOP(item.servicio.tarifa_por_hora)}/h`} />
              <Stat label="Modalidad" value={item.servicio.modalidad} />
              <Stat label="Horario" value={item.servicio.disponibilidad_horaria} />
            </div>
          )}

          {(item.categorias?.length ?? 0) > 0 && (
            <div className="flex flex-wrap gap-2">
              {item.categorias!.map((c) => (
                <Badge key={c} tone="neutral">
                  {c}
                </Badge>
              ))}
            </div>
          )}
        </section>

        <aside className="panel h-fit space-y-4 lg:sticky lg:top-24">
          <div>
            <div className="text-sm text-ink-700/55">Precio</div>
            <div className="font-display text-3xl text-ink-900">{priceLabel}</div>
          </div>
          <div className="rounded-xl bg-campus-50 px-3 py-2 text-sm text-campus-800">
            Vendedor: <strong>{item.vendedor_nombre || `#${item.id_vendedor}`}</strong>
            {item.universidad_nombre ? ` · ${item.universidad_nombre}` : ""}
          </div>

          <div className="grid gap-2">
            <Button onClick={() => (requireBuyer() ? setBuyOpen(true) : null)}>
              <ShoppingBag className="h-4 w-4" /> Comprar ahora
            </Button>
            <Button variant="secondary" onClick={() => (requireBuyer() ? setOfferOpen(true) : null)}>
              <Tag className="h-4 w-4" /> Hacer oferta
            </Button>
            <Button variant="secondary" onClick={() => (requireBuyer() ? setBarterOpen(true) : null)}>
              <Handshake className="h-4 w-4" /> Proponer trueque
            </Button>
            <Button variant="secondary" onClick={() => (requireBuyer() ? setLoanOpen(true) : null)}>
              <CalendarClock className="h-4 w-4" /> Solicitar préstamo
            </Button>
          </div>
        </aside>
      </div>

      <Modal open={buyOpen} onClose={() => setBuyOpen(false)} title="Confirmar compra">
        <form onSubmit={onBuy} className="space-y-4">
          <p className="text-sm text-ink-700/70">
            Se insertará en `COMPRA`. Si el trigger rechaza stock/horario, verás el mensaje exacto de MySQL.
          </p>
          <div>
            <Label>Método de pago</Label>
            <Select value={metodoPago} onChange={(e) => setMetodoPago(e.target.value)}>
              <option>Transferencia</option>
              <option>Efectivo</option>
              <option>Nequi</option>
              <option>Tarjeta</option>
            </Select>
          </div>
          <div className="rounded-xl bg-ink-800/5 px-3 py-2 text-sm">
            Total: <strong>{formatCOP(item.precio_efectivo)}</strong>
          </div>
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Procesando…" : "Confirmar compra"}
          </Button>
        </form>
      </Modal>

      <Modal open={offerOpen} onClose={() => setOfferOpen(false)} title="Hacer oferta">
        <form onSubmit={onOffer} className="space-y-4">
          <div>
            <Label>Monto ofertado (COP)</Label>
            <Input
              type="number"
              min={1}
              required
              value={montoOferta}
              onChange={(e) => setMontoOferta(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Enviando…" : "Enviar oferta"}
          </Button>
        </form>
      </Modal>

      <Modal open={barterOpen} onClose={() => setBarterOpen(false)} title="Proponer trueque" wide>
        <form onSubmit={onBarter} className="space-y-4">
          <p className="text-sm text-ink-700/70">
            Ofrece una de tus publicaciones activas a cambio de <strong>{item.titulo}</strong>.
          </p>
          <div>
            <Label>Tu publicación ofrecida</Label>
            <Select
              required
              value={offeredId}
              onChange={(e) => setOfferedId(e.target.value)}
            >
              <option value="">Selecciona…</option>
              {myListings.map((p) => (
                <option key={p.id_publicacion} value={p.id_publicacion}>
                  #{p.id_publicacion} · {p.titulo}
                </option>
              ))}
            </Select>
            {myListings.length === 0 && (
              <p className="mt-2 text-xs text-ember-600">
                No aparecen listings propios en el catálogo activo. Necesitas rol vendedor con publicaciones.
              </p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={busy || myListings.length === 0}>
            {busy ? "Enviando…" : "Proponer trueque"}
          </Button>
        </form>
      </Modal>

      <Modal open={loanOpen} onClose={() => setLoanOpen(false)} title="Solicitar préstamo">
        <form onSubmit={onLoan} className="space-y-4">
          <div>
            <Label>Fecha de devolución pactada</Label>
            <Input
              type="datetime-local"
              required
              value={fechaDev}
              onChange={(e) => setFechaDev(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Solicitando…" : "Solicitar préstamo"}
          </Button>
        </form>
      </Modal>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-ink-800/8 bg-campus-50/60 px-3 py-3">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-ink-700/50">
        {label}
      </div>
      <div className="mt-1 text-sm font-semibold text-ink-900">{value}</div>
    </div>
  );
}
