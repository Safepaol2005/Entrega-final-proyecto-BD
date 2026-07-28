"""Pydantic schemas for admin moderation and sanctions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EstadoSancion(str, Enum):
    VIGENTE = "Vigente"
    PAGADA = "Pagada"
    EXPIRADA = "Expirada"


class SancionCreate(BaseModel):
    """Payload mapped to CALL aplicar_sancion(...)."""

    p_id_prestamo: int = Field(..., gt=0)
    p_id_administrador: int = Field(..., gt=0)
    p_motivo: str = Field(..., min_length=5, max_length=255)
    p_monto_incremento: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)


class SancionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_sancion: int
    id_usuario: int
    id_prestamo: Optional[int] = None
    id_administrador: int
    motivo: str
    monto_multa: Optional[Decimal] = None
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    estado_sancion: EstadoSancion


class PrestamoRiesgoOut(BaseModel):
    """Row shape from vw_prestamos_riesgo."""

    model_config = ConfigDict(from_attributes=True)

    id_prestamo: int
    deudor: str
    item_prestado: str
    fecha_devolucion_pactada: datetime
    dias_retraso: int
    ranking_mora: int


class AuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_auditoria: int
    id_compra: Optional[int] = None
    id_trueque: Optional[int] = None
    id_prestamo: Optional[int] = None
    id_administrador: Optional[int] = None
    tipo_evento: str
    detalle_evento: str
    fecha_registro: datetime
    usuario_auditor: str


class RankingVendedorOut(BaseModel):
    """Row shape from vista_ranking_vendedores."""

    model_config = ConfigDict(from_attributes=True)

    id_vendedor: int
    calificacion_actual: Optional[Decimal] = None
    ventas_completadas: Optional[int] = None
    fiabilidad: Optional[Decimal] = None
    ranking_fiabilidad: Optional[int] = None
    posicion_fila: Optional[int] = None
    diferencia_con_puesto_anterior: Optional[Decimal] = None
    vendedor_nombre: Optional[str] = None


class SancionAppliedOut(BaseModel):
    detail: str
    p_id_prestamo: int
    p_id_administrador: int


class IngresoAcumuladoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    fecha_transaccion: datetime
    monto_total: float
    ingreso_acumulado: float
