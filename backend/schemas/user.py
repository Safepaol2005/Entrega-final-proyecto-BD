"""Pydantic schemas for authentication and user profiles."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    COMPRADOR = "comprador"
    VENDEDOR = "vendedor"
    ADMINISTRADOR = "administrador"


class UserRegister(BaseModel):
    """Registration payload. Email domain must match a UNIVERSIDAD.dominio_correo."""

    nombre_completo: str = Field(..., min_length=2, max_length=50)
    correo_estudiantil: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    roles: list[UserRole] = Field(
        default_factory=lambda: [UserRole.COMPRADOR],
        min_length=1,
        description="At least one subclass role to create (COMPRADOR / VENDEDOR / ADMINISTRADOR).",
    )
    preferencias_busqueda: Optional[str] = Field(default=None, max_length=255)
    # Admin-only fields (ignored unless administrador role is requested)
    nivel_permiso: Optional[str] = Field(default="Moderador", max_length=20)
    area_soporte: Optional[str] = Field(default="Atención al Estudiante", max_length=50)

    @field_validator("correo_estudiantil")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("roles")
    @classmethod
    def unique_roles(cls, value: list[UserRole]) -> list[UserRole]:
        return list(dict.fromkeys(value))

    @field_validator("nivel_permiso")
    @classmethod
    def validate_nivel(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"SuperAdmin", "Moderador", "Soporte"}
        if value not in allowed:
            raise ValueError(f"nivel_permiso must be one of {sorted(allowed)}")
        return value


class UserLogin(BaseModel):
    correo_estudiantil: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("correo_estudiantil")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    id_universidad: int
    nombre_completo: str
    correo_estudiantil: EmailStr
    fecha_registro: datetime
    roles: list[UserRole] = Field(default_factory=list)
    universidad_nombre: Optional[str] = None
    dominio_correo: Optional[str] = None


class AuthResponse(BaseModel):
    user: UserPublic
    token: TokenResponse
