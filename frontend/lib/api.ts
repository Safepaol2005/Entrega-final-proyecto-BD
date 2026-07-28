import type {
  AuthResponse,
  Auditoria,
  Categoria,
  ChebyshevRow,
  IngresoAcumulado,
  PrestamoRiesgo,
  Publicacion,
  PublicacionList,
  RankingVendedor,
  Universidad,
  UserPublic,
  UserRole,
} from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001/api/v1";

const TOKEN_KEY = "untrade_token";
const USER_KEY = "untrade_user";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): UserPublic | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserPublic;
  } catch {
    return null;
  }
}

export function persistAuth(auth: AuthResponse) {
  localStorage.setItem(TOKEN_KEY, auth.token.access_token);
  localStorage.setItem(USER_KEY, JSON.stringify(auth.user));
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function parseError(res: Response): Promise<ApiError> {
  let detail = res.statusText || "Request failed";
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") {
      detail = data.detail;
    } else if (Array.isArray(data?.detail)) {
      detail = data.detail
        .map((e: { msg?: string; loc?: unknown }) => e.msg || JSON.stringify(e))
        .join("; ");
    } else if (data?.detail != null) {
      detail = JSON.stringify(data.detail);
    }
  } catch {
    // keep statusText
  }
  return new ApiError(res.status, detail);
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  auth?: boolean;
  query?: Record<string, string | number | boolean | null | undefined>;
};

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, auth = false, query } = options;
  const token = options.token ?? (auth ? getStoredToken() : null);

  const url = new URL(`${API_BASE}${path.startsWith("/") ? path : `/${path}`}`);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== "") {
        url.searchParams.set(k, String(v));
      }
    });
  }

  const headers: HeadersInit = {
    Accept: "application/json",
  };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(url.toString(), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    throw await parseError(res);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  universidades: () => apiRequest<Universidad[]>("/auth/universidades"),

  register: (payload: {
    nombre_completo: string;
    correo_estudiantil: string;
    password: string;
    roles: UserRole[];
    preferencias_busqueda?: string;
  }) =>
    apiRequest<AuthResponse>("/auth/register", {
      method: "POST",
      body: payload,
    }),

  login: (payload: { correo_estudiantil: string; password: string }) =>
    apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: payload,
    }),

  me: () => apiRequest<UserPublic>("/auth/me", { auth: true }),

  categories: () => apiRequest<Categoria[]>("/catalog/categories"),

  publications: (query?: Record<string, string | number | boolean | null | undefined>) =>
    apiRequest<PublicacionList>("/catalog/publications", { query }),

  publication: (id: number) =>
    apiRequest<Publicacion>(`/catalog/publications/${id}`),

  chebyshev: () =>
    apiRequest<ChebyshevRow[]>("/catalog/analytics/chebyshev"),

  buy: (payload: {
    id_publicacion: number;
    monto_total: number;
    metodo_pago: string;
  }) =>
    apiRequest("/transactions/buy", {
      method: "POST",
      body: payload,
      auth: true,
    }),

  offer: (payload: { id_publicacion: number; monto_ofertado: number }) =>
    apiRequest("/transactions/offers", {
      method: "POST",
      body: payload,
      auth: true,
    }),

  updateOffer: (id: number, estado_oferta: "Aceptada" | "Rechazada") =>
    apiRequest(`/transactions/offers/${id}`, {
      method: "PATCH",
      body: { estado_oferta },
      auth: true,
    }),

  barter: (payload: {
    id_publicacion_deseada: number;
    id_publicacion_ofrecida: number;
  }) =>
    apiRequest("/transactions/barter", {
      method: "POST",
      body: payload,
      auth: true,
    }),

  loan: (payload: {
    id_publicacion: number;
    fecha_devolucion_pactada: string;
    fecha_inicio?: string | null;
  }) =>
    apiRequest("/transactions/loans", {
      method: "POST",
      body: payload,
      auth: true,
    }),

  rateSeller: (id: number) =>
    apiRequest<{ id_vendedor: number; calificacion: number; detail: string }>(
      `/seller/${id}/rate`,
      { method: "POST", auth: true },
    ),

  sellerRanking: () => apiRequest<RankingVendedor[]>("/seller/ranking"),

  overdueLoans: () =>
    apiRequest<PrestamoRiesgo[]>("/admin/loans/overdue", { auth: true }),

  applySanction: (payload: {
    p_id_prestamo: number;
    p_id_administrador: number;
    p_motivo: string;
    p_monto_incremento: number;
  }) =>
    apiRequest("/admin/sanctions", {
      method: "POST",
      body: payload,
      auth: true,
    }),

  audit: (query?: { limit?: number; offset?: number; tipo_evento?: string }) =>
    apiRequest<Auditoria[]>("/admin/audit", { auth: true, query }),

  revenue: (limit = 200) =>
    apiRequest<IngresoAcumulado[]>("/admin/revenue", {
      auth: true,
      query: { limit },
    }),
};
