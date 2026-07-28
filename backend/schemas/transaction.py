"""Pydantic schemas for purchases, offers, barters, and loans."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EstadoOferta(str, Enum):
    PENDIENTE = "Pendiente"
    ACEPTADA = "Aceptada"
    RECHAZADA = "Rechazada"


class EstadoPrestamo(str, Enum):
    SOLICITADO = "Solicitado"
    ACTIVO = "Activo"
    DEVUELTO = "Devuelto"
    DEMORADO = "Demorado"


class EstadoTrueque(str, Enum):
    PENDIENTE = "Pendiente"
    ACEPTADO = "Aceptado"
    RECHAZADO = "Rechazado"


class CompraCreate(BaseModel):
    id_publicacion: int = Field(..., gt=0)
    monto_total: float = Field(..., gt=0)
    metodo_pago: str = Field(..., min_length=2, max_length=50)


class CompraOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_compra: int
    id_comprador: int
    id_publicacion: int
    monto_total: float
    fecha_transaccion: datetime
    metodo_pago: str


class OfertaCreate(BaseModel):
    id_publicacion: int = Field(..., gt=0)
    monto_ofertado: float = Field(..., gt=0)


class OfertaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_oferta: int
    id_comprador: int
    id_publicacion: int
    monto_ofertado: float
    fecha_oferta: datetime
    estado_oferta: EstadoOferta


class OfertaEstadoUpdate(BaseModel):
    estado_oferta: EstadoOferta

    @model_validator(mode="after")
    def only_accept_or_reject(self) -> "OfertaEstadoUpdate":
        if self.estado_oferta == EstadoOferta.PENDIENTE:
            raise ValueError("estado_oferta must be Aceptada or Rechazada")
        return self


class CalificarVendedorOut(BaseModel):
    id_vendedor: int
    calificacion: Decimal
    detail: str = "Seller rating recalculated via calificar_vendedor"


class TruequeCreate(BaseModel):
    id_publicacion_deseada: int = Field(..., gt=0)
    id_publicacion_ofrecida: int = Field(..., gt=0)

    @model_validator(mode="after")
    def distinct_publications(self) -> "TruequeCreate":
        if self.id_publicacion_deseada == self.id_publicacion_ofrecida:
            raise ValueError("id_publicacion_ofrecida must differ from id_publicacion_deseada")
        return self


class TruequeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_trueque: int
    id_comprador_iniciador: int
    id_publicacion_deseada: int
    id_publicacion_ofrecida: int
    fecha_propuesta: datetime
    estado_trueque: EstadoTrueque


class PrestamoCreate(BaseModel):
    id_publicacion: int = Field(..., gt=0)
    fecha_devolucion_pactada: datetime
    fecha_inicio: Optional[datetime] = None


class PrestamoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_prestamo: int
    id_comprador: int
    id_publicacion: int
    fecha_solicitud: datetime
    fecha_inicio: Optional[datetime] = None
    fecha_devolucion_pactada: datetime
    fecha_devolucion_real: Optional[datetime] = None
    estado_prestamo: EstadoPrestamo


class CalificarVendedorRequest(BaseModel):
    """Wrapper around CALL calificar_vendedor(p_id_vendedor)."""

    id_vendedor: int = Field(..., gt=0)
