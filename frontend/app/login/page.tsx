"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/ui/Toast";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";

export default function LoginPage() {
  const { login } = useAuth();
  const toast = useToast();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Sesión iniciada");
      router.push("/catalog");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : "No se pudo iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <div className="panel">
        <h1 className="font-display text-3xl text-ink-900">Entrar a UNTrade</h1>
        <p className="mt-2 text-sm text-ink-700/65">
          Usa tu correo institucional registrado.
        </p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <Label htmlFor="email">Correo estudiantil</Label>
            <Input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="nombre@unal.edu.co"
            />
          </div>
          <div>
            <Label htmlFor="password">Contraseña</Label>
            <Input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "Entrando…" : "Iniciar sesión"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-700/60">
          ¿Sin cuenta?{" "}
          <Link href="/register" className="font-semibold text-campus-700 hover:underline">
            Regístrate
          </Link>
        </p>
      </div>
    </div>
  );
}
