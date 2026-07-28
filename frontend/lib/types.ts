export type UserRole = "comprador" | "vendedor" | "administrador";

export interface Universidad {
  id_universidad: number;
  nombre: string;
  pais: string;
  dominio_correo: string;
}

export interface UserPublic {
  id_usuario: number;
  id_universidad: number;
  nombre_completo: string;
  correo_estudiantil: string;
  fecha_registro: string;
  roles: UserRole[];
  universidad_nombre?: string | null;
  dominio_correo?: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthResponse {
  user: UserPublic;
  token: TokenResponse;
}

export interface Categoria {
  id_categoria: number;
  nombre: string;
}

export interface ProductoOut {
  id_producto: number;
  precio: number | string;
  calificacion?: number | string | null;
  estado_fisico: "NUEVO" | "USADO";
  stock: number;
}

export interface ServicioOut {
  id_servicio: number;
  modalidad: "Presencial" | "Virtual";
  tarifa_por_hora: number | string;
  disponibilidad_horaria: string;
  calificacion?: number | string | null;
}

export interface Publicacion {
  id_publicacion: number;
  id_vendedor: number;
  id_administrador_moderador?: number | null;
  tipo_item: "Producto" | "Servicio";
  titulo: string;
  descripcion?: string | null;
  fecha_publicacion: string;
  estado_publicacion: string;
  producto?: ProductoOut | null;
  servicio?: ServicioOut | null;
  vendedor_nombre?: string | null;
  universidad_nombre?: string | null;
  id_universidad?: number | null;
  categorias?: string[];
  precio_efectivo?: number | string | null;
}

export interface PublicacionList {
  items: Publicacion[];
  total: number;
  limit: number;
  offset: number;
}

export interface ChebyshevRow {
  id_producto: number;
  proba: number | string;
  media_del_catalogo: number | string;
  desviacion_del_catalogo: number | string;
  limite_superior_chebyshev: number | string;
  diagnostico_chebyshev: string;
}

export interface RankingVendedor {
  id_vendedor: number;
  calificacion_actual?: number | string | null;
  ventas_completadas?: number | null;
  fiabilidad?: number | string | null;
  ranking_fiabilidad?: number | null;
  posicion_fila?: number | null;
  diferencia_con_puesto_anterior?: number | string | null;
  vendedor_nombre?: string | null;
}

export interface PrestamoRiesgo {
  id_prestamo: number;
  deudor: string;
  item_prestado: string;
  fecha_devolucion_pactada: string;
  dias_retraso: number;
  ranking_mora: number;
}

export interface IngresoAcumulado {
  fecha_transaccion: string;
  monto_total: number;
  ingreso_acumulado: number;
}

export interface Auditoria {
  id_auditoria: number;
  id_compra?: number | null;
  id_trueque?: number | null;
  id_prestamo?: number | null;
  id_administrador?: number | null;
  tipo_evento: string;
  detalle_evento: string;
  fecha_registro: string;
  usuario_auditor: string;
}
