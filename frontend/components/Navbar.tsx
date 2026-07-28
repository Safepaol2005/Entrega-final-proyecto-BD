"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  ChevronDown,
  LayoutDashboard,
  LogOut,
  Search,
  Shield,
  Store,
  UserRound,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { RoleBadges } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

const links = [
  { href: "/catalog", label: "Marketplace", icon: Store },
  { href: "/seller", label: "Seller Hub", icon: LayoutDashboard },
  { href: "/admin", label: "Admin", icon: Shield, adminOnly: true },
];

export function Navbar() {
  const { user, logout, hasRole } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (!menuRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const params = new URLSearchParams();
    if (q.trim()) params.set("q", q.trim());
    router.push(`/catalog?${params.toString()}`);
  };

  return (
    <header className="sticky top-0 z-40 border-b border-ink-800/10 bg-[#f7fbf9]/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="group shrink-0">
          <div className="font-display text-2xl tracking-tight text-ink-900">
            UN<span className="text-campus-600">Trade</span>
          </div>
          <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-ink-700/50 group-hover:text-campus-600">
            Campus exchange
          </div>
        </Link>

        <form onSubmit={onSearch} className="relative mx-auto hidden min-w-0 flex-1 md:block md:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-700/40" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar libros, servicios, materiales…"
            className="h-11 w-full rounded-full border border-ink-800/10 bg-white/80 pl-10 pr-4 text-sm outline-none transition focus:border-campus-500 focus:ring-2 focus:ring-campus-200"
          />
        </form>

        <nav className="hidden items-center gap-1 lg:flex">
          {links.map(({ href, label, icon: Icon, adminOnly }) => {
            if (adminOnly && !hasRole("administrador")) return null;
            const active = pathname === href || pathname.startsWith(`${href}/`);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-full px-3 py-2 text-sm font-medium transition",
                  active
                    ? "bg-ink-900 text-white"
                    : "text-ink-700 hover:bg-ink-800/5",
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="relative ml-auto" ref={menuRef}>
          {user ? (
            <>
              <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center gap-2 rounded-full border border-ink-800/10 bg-white px-2.5 py-1.5 shadow-sm"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-campus-100 text-campus-700">
                  <UserRound className="h-4 w-4" />
                </span>
                <span className="hidden max-w-[9rem] truncate text-left text-sm font-medium text-ink-900 sm:block">
                  {user.nombre_completo.split(" ")[0]}
                </span>
                <ChevronDown className="h-4 w-4 text-ink-700/50" />
              </button>
              {open && (
                <div className="absolute right-0 mt-2 w-72 rounded-2xl border border-ink-800/10 bg-white p-3 shadow-lift">
                  <div className="mb-2 border-b border-ink-800/5 pb-2">
                    <p className="font-medium text-ink-900">{user.nombre_completo}</p>
                    <p className="truncate text-xs text-ink-700/60">{user.correo_estudiantil}</p>
                    <div className="mt-2">
                      <RoleBadges roles={user.roles} />
                    </div>
                  </div>
                  <div className="flex flex-col gap-1 lg:hidden">
                    {links.map(({ href, label, adminOnly }) => {
                      if (adminOnly && !hasRole("administrador")) return null;
                      return (
                        <Link
                          key={href}
                          href={href}
                          onClick={() => setOpen(false)}
                          className="rounded-lg px-2 py-2 text-sm hover:bg-ink-800/5"
                        >
                          {label}
                        </Link>
                      );
                    })}
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      logout();
                      setOpen(false);
                      router.push("/login");
                    }}
                    className="mt-1 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-red-700 hover:bg-red-50"
                  >
                    <LogOut className="h-4 w-4" />
                    Cerrar sesión
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                href="/login"
                className="rounded-full px-3 py-2 text-sm font-medium text-ink-700 hover:bg-ink-800/5"
              >
                Entrar
              </Link>
              <Link
                href="/register"
                className="rounded-full bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-800"
              >
                Registrarse
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
