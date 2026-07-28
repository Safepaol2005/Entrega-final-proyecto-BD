"""FastAPI dependencies: DB access helpers and JWT current-user resolution."""

from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.security import decode_access_token
from database import execute
from schemas.user import UserPublic, UserRole

bearer_scheme = HTTPBearer(auto_error=True)


async def load_user_roles(id_usuario: int) -> list[UserRole]:
    roles: list[UserRole] = []
    comprador = await execute(
        "SELECT 1 AS ok FROM COMPRADOR WHERE id_comprador = %s",
        (id_usuario,),
        fetch="one",
        commit=False,
    )
    if comprador:
        roles.append(UserRole.COMPRADOR)

    vendedor = await execute(
        "SELECT 1 AS ok FROM VENDEDOR WHERE id_vendedor = %s",
        (id_usuario,),
        fetch="one",
        commit=False,
    )
    if vendedor:
        roles.append(UserRole.VENDEDOR)

    admin = await execute(
        "SELECT 1 AS ok FROM ADMINISTRADOR WHERE id_administrador = %s",
        (id_usuario,),
        fetch="one",
        commit=False,
    )
    if admin:
        roles.append(UserRole.ADMINISTRADOR)

    return roles


async def get_user_by_id(id_usuario: int) -> Optional[dict[str, Any]]:
    return await execute(
        """
        SELECT
            u.id_usuario,
            u.id_universidad,
            u.nombre_completo,
            u.correo_estudiantil,
            u.fecha_registro,
            un.nombre AS universidad_nombre,
            un.dominio_correo
        FROM USUARIO u
        INNER JOIN UNIVERSIDAD un ON un.id_universidad = u.id_universidad
        WHERE u.id_usuario = %s
        """,
        (id_usuario,),
        fetch="one",
        commit=False,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> UserPublic:
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")
        if subject is None:
            raise ValueError("missing subject")
        id_usuario = int(subject)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    row = await get_user_by_id(id_usuario)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles = await load_user_roles(id_usuario)
    return UserPublic(**row, roles=roles)


def require_roles(*allowed: UserRole):
    """Dependency factory that enforces one of the given subclass roles."""

    async def _checker(
        current_user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> UserPublic:
        if not any(role in current_user.roles for role in allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {[r.value for r in allowed]}",
            )
        return current_user

    return _checker
