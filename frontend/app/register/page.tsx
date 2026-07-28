"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Universidad, UserRole } from "@/lib/types";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";

export default function RegisterPage() {
  const { register } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const [universidades, setUniversidades] = useState<Universidad[]>([]);
  const [nombre, setNombre] = useState("");
  const [localPart, setLocalPart] = useState("");
  const [dominio, setDominio] = useState("");
  const [password, setPassword] = useState("");
  const [roleMode, setRoleMode] = useState<"comprador" | "vendedor" | "both">("both");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .universidades()
      .then((rows) => {
        setUniversidades(rows);
        if (rows[0]) setDominio(rows[0].dominio_correo);
      })
      .catch((e) =>
        toast.error(e instanceof ApiError ? e.detail : "No se pudieron cargar universidades"),
      );
  }, [toast]);

  const email = useMemo(() => {
    if (!localPart || !dominio) return "";
    const d = dominio.startsWith("@") ? dominio : `@${dominio}`;
    return `${localPart.trim().toLowerCase()}${d}`;
  }, [localPart, dominio]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const roles: UserRole[] =
      roleMode === "both"
        ? ["comprador", "vendedor"]
        : roleMode === "comprador"
          ? ["comprador"]
          : ["vendedor"];
    setLoading(true);
    try {
      await register({
        nombre_completo: nombre,
        correo_estudiantil: email,
        password,
        roles,
      });
      toast.success("Cuenta creada");
      router.push("/catalog");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo registrar");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-lg">
      <div className="panel">
        <h1 className="font-display text-3xl text-ink-900">Crear cuenta</h1>
        <p className="mt-2 text-sm text-ink-700/65">
          El dominio del correo debe coincidir con una universidad en `UNIVERSIDAD`.
        </p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <Label>Nombre completo</Label>
            <Input
              required
              minLength={2}
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div>
            <Label>Universidad / dominio</Label>
            <Select
              required
              value={dominio}
              onChange={(e) => setDominio(e.target.value)}
            >
              {universidades.map((u) => (
                <option key={u.id_universidad} value={u.dominio_correo}>
                  {u.nombre} ({u.dominio_correo})
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Usuario del correo</Label>
            <div className="flex items-center gap-2">
              <Input
                required
                value={localPart}
                onChange={(e) => setLocalPart(e.target.value)}
                placeholder="estudiante123"
              />
              <span className="shrink-0 text-sm text-ink-700/60">{dominio}</span>
            </div>
            {email && (
              <p className="mt-1 text-xs text-campus-700">{email}</p>
            )}
          </div>
          <div>
            <Label>Contraseña</Label>
            <Input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div>
            <Label>Rol</Label>
            <Select
              value={roleMode}
              onChange={(e) => setRoleMode(e.target.value as typeof roleMode)}
            >
              <option value="comprador">Comprador</option>
              <option value="vendedor">Vendedor</option>
              <option value="both">Ambos (Comprador + Vendedor)</option>
            </Select>
          </div>
          <Button type="submit" className="w-full" disabled={loading || !email}>
            {loading ? "Creando…" : "Registrarme"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-700/60">
          ¿Ya tienes cuenta?{" "}
          <Link href="/login" className="font-semibold text-campus-700 hover:underline">
            Entrar
          </Link>
        </p>
      </div>
    </div>
  );
}
