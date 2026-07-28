"""Pydantic schemas for publications, products, and services."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TipoItem(str, Enum):
    PRODUCTO = "Producto"
    SERVICIO = "Servicio"


class EstadoPublicacion(str, Enum):
    ACTIVA = "Activa"
    PAUSADA = "Pausada"
    BLOQUEADA = "Bloqueada"
    FINALIZADA = "Finalizada"


class EstadoFisico(str, Enum):
    NUEVO = "NUEVO"
    USADO = "USADO"


class ModalidadServicio(str, Enum):
    PRESENCIAL = "Presencial"
    VIRTUAL = "Virtual"


class ProductoCreate(BaseModel):
    precio: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2)
    estado_fisico: EstadoFisico
    stock: int = Field(..., ge=0)
    calificacion: Optional[Decimal] = Field(default=None, ge=0, le=10)
    categorias: list[int] = Field(default_factory=list)
    materias: list[int] = Field(default_factory=list)


class ServicioCreate(BaseModel):
    modalidad: ModalidadServicio
    tarifa_por_hora: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    disponibilidad_horaria: str = Field(..., min_length=1, max_length=255)
    calificacion: Optional[Decimal] = Field(default=None, ge=0, le=10)


class PublicacionCreate(BaseModel):
    titulo: str = Field(..., min_length=3, max_length=150)
    descripcion: Optional[str] = None
    tipo_item: TipoItem
    producto: Optional[ProductoCreate] = None
    servicio: Optional[ServicioCreate] = None

    @field_validator("titulo")
    @classmethod
    def strip_titulo(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def require_typed_payload(self) -> "PublicacionCreate":
        if self.tipo_item == TipoItem.PRODUCTO and self.producto is None:
            raise ValueError("producto payload is required when tipo_item is Producto")
        if self.tipo_item == TipoItem.SERVICIO and self.servicio is None:
            raise ValueError("servicio payload is required when tipo_item is Servicio")
        return self


class PublicacionUpdate(BaseModel):
    titulo: Optional[str] = Field(default=None, min_length=3, max_length=150)
    descripcion: Optional[str] = None
    estado_publicacion: Optional[EstadoPublicacion] = None


class CatalogFilters(BaseModel):
    q: Optional[str] = Field(default=None, description="Full-text search on title/description")
    tipo_item: Optional[TipoItem] = None
    estado_publicacion: Optional[EstadoPublicacion] = EstadoPublicacion.ACTIVA
    id_categoria: Optional[int] = None
    id_universidad: Optional[int] = None
    precio_min: Optional[Decimal] = Field(default=None, ge=0)
    precio_max: Optional[Decimal] = Field(default=None, ge=0)
    modalidad: Optional[ModalidadServicio] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ProductoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    precio: Decimal
    calificacion: Optional[Decimal] = None
    estado_fisico: EstadoFisico
    stock: int


class ServicioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_servicio: int
    modalidad: ModalidadServicio
    tarifa_por_hora: Decimal
    disponibilidad_horaria: str
    calificacion: Optional[Decimal] = None


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_categoria: int
    nombre: str


class PublicacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_publicacion: int
    id_vendedor: int
    id_administrador_moderador: Optional[int] = None
    tipo_item: TipoItem
    titulo: str
    descripcion: Optional[str] = None
    fecha_publicacion: datetime
    estado_publicacion: EstadoPublicacion
    producto: Optional[ProductoOut] = None
    servicio: Optional[ServicioOut] = None
    vendedor_nombre: Optional[str] = None
    universidad_nombre: Optional[str] = None
    id_universidad: Optional[int] = None
    categorias: list[str] = Field(default_factory=list)
    precio_efectivo: Optional[Decimal] = Field(
        default=None,
        description="PRODUCTO.precio or SERVICIO.tarifa_por_hora",
    )


class PublicacionListOut(BaseModel):
    items: list[PublicacionOut]
    total: int
    limit: int
    offset: int


class ChebyshevDiagnosticoOut(BaseModel):
    """Row shape from the N5-03 Chebyshev demand diagnostic query."""

    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    proba: Decimal
    media_del_catalogo: Decimal
    desviacion_del_catalogo: Decimal
    limite_superior_chebyshev: Decimal
    diagnostico_chebyshev: str
