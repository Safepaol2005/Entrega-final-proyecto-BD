"""JWT authentication router: register / login against USUARIO + UNIVERSIDAD."""

from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import create_access_token, hash_password, verify_password
from database import BusinessRuleError, execute, raise_http_from_business_rule, transaction
from deps import get_current_user, load_user_roles
from schemas.user import (
    AuthResponse,
    TokenResponse,
    UserLogin,
    UserPublic,
    UserRegister,
    UserRole,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _email_domain(email: str) -> str:
    """Return '@domain.tld' from a full email address."""
    local, _, domain = email.partition("@")
    if not local or not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid student email format",
        )
    return f"@{domain.lower()}"


async def _resolve_universidad(email: str) -> dict[str, Any]:
    """
    Match correo_estudiantil against UNIVERSIDAD.dominio_correo
    (e.g. student@unal.edu.co ↔ '@unal.edu.co').
    """
    dominio = _email_domain(email)
    row = await execute(
        """
        SELECT id_universidad, nombre, pais, dominio_correo
        FROM UNIVERSIDAD
        WHERE LOWER(dominio_correo) = %s
        """,
        (dominio,),
        fetch="one",
        commit=False,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Email domain '{dominio}' is not registered in UNIVERSIDAD. "
                "Institutional affiliation required (chk_dominio_correo)."
            ),
        )
    return row


async def _get_user_by_email(email: str) -> Optional[dict[str, Any]]:
    return await execute(
        """
        SELECT
            u.id_usuario,
            u.id_universidad,
            u.nombre_completo,
            u.correo_estudiantil,
            u.password_hash,
            u.fecha_registro,
            un.nombre AS universidad_nombre,
            un.dominio_correo
        FROM USUARIO u
        INNER JOIN UNIVERSIDAD un ON un.id_universidad = u.id_universidad
        WHERE LOWER(u.correo_estudiantil) = %s
        """,
        (email.lower(),),
        fetch="one",
        commit=False,
    )


async def _create_role_rows(conn: Any, user_id: int, payload: UserRegister) -> None:
    if UserRole.COMPRADOR in payload.roles:
        await execute(
            """
            INSERT INTO COMPRADOR (id_comprador, preferencias_busqueda)
            VALUES (%s, %s)
            """,
            (user_id, payload.preferencias_busqueda),
            connection=conn,
        )

    if UserRole.VENDEDOR in payload.roles:
        await execute(
            """
            INSERT INTO VENDEDOR (id_vendedor, calificacion, ventas_completadas)
            VALUES (%s, %s, %s)
            """,
            (user_id, 0.0, 0),
            connection=conn,
        )

    if UserRole.ADMINISTRADOR in payload.roles:
        await execute(
            """
            INSERT INTO ADMINISTRADOR (id_administrador, nivel_permiso, area_soporte)
            VALUES (%s, %s, %s)
            """,
            (
                user_id,
                payload.nivel_permiso or "Moderador",
                payload.area_soporte or "Atención al Estudiante",
            ),
            connection=conn,
        )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a student user linked to UNIVERSIDAD by email domain",
)
async def register(payload: UserRegister) -> AuthResponse:
    universidad = await _resolve_universidad(payload.correo_estudiantil)

    existing = await _get_user_by_email(payload.correo_estudiantil)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this student email already exists",
        )

    password_hash = hash_password(payload.password)
    email = payload.correo_estudiantil.lower()

    try:
        async with transaction() as conn:
            insert_result = await execute(
                """
                INSERT INTO USUARIO (
                    id_universidad, nombre_completo, correo_estudiantil, password_hash
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    universidad["id_universidad"],
                    payload.nombre_completo.strip(),
                    email,
                    password_hash,
                ),
                connection=conn,
            )
            user_id = insert_result["lastrowid"]
            await _create_role_rows(conn, user_id, payload)
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    created = await _get_user_by_email(email)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User was created but could not be reloaded",
        )

    roles = await load_user_roles(user_id)
    token_str, expires_in = create_access_token(
        user_id,
        extra_claims={"email": email, "roles": [r.value for r in roles]},
    )

    user = UserPublic(
        id_usuario=created["id_usuario"],
        id_universidad=created["id_universidad"],
        nombre_completo=created["nombre_completo"],
        correo_estudiantil=created["correo_estudiantil"],
        fecha_registro=created["fecha_registro"],
        roles=roles,
        universidad_nombre=created["universidad_nombre"],
        dominio_correo=created["dominio_correo"],
    )
    return AuthResponse(
        user=user,
        token=TokenResponse(access_token=token_str, expires_in=expires_in),
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate against USUARIO.password_hash and issue JWT",
)
async def login(payload: UserLogin) -> AuthResponse:
    row = await _get_user_by_email(payload.correo_estudiantil)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stored_hash: str = row["password_hash"]
    if not stored_hash.startswith("$2"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "This account uses a legacy seed password hash (SHA-256). "
                "Register a new account or reset password_hash to bcrypt."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = await load_user_roles(row["id_usuario"])
    token_str, expires_in = create_access_token(
        row["id_usuario"],
        extra_claims={
            "email": row["correo_estudiantil"],
            "roles": [r.value for r in roles],
        },
    )

    user = UserPublic(
        id_usuario=row["id_usuario"],
        id_universidad=row["id_universidad"],
        nombre_completo=row["nombre_completo"],
        correo_estudiantil=row["correo_estudiantil"],
        fecha_registro=row["fecha_registro"],
        roles=roles,
        universidad_nombre=row["universidad_nombre"],
        dominio_correo=row["dominio_correo"],
    )
    return AuthResponse(
        user=user,
        token=TokenResponse(access_token=token_str, expires_in=expires_in),
    )


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Return the authenticated USUARIO profile and subclass roles",
)
async def me(
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> UserPublic:
    return current_user


@router.get(
    "/universidades",
    summary="List UNIVERSIDAD rows (allowed email domains for registration)",
)
async def list_universidades() -> list[dict[str, Any]]:
    rows = await execute(
        """
        SELECT id_universidad, nombre, pais, dominio_correo
        FROM UNIVERSIDAD
        ORDER BY nombre
        """,
        fetch="all",
        commit=False,
    )
    return list(rows or [])
