"""Admin moderation: overdue loans, sanctions, audit log, revenue."""

from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from database import BusinessRuleError, call_procedure, execute, raise_http_from_business_rule
from deps import require_roles
from schemas.admin import (
    AuditoriaOut,
    IngresoAcumuladoOut,
    PrestamoRiesgoOut,
    SancionAppliedOut,
    SancionCreate,
)
from schemas.user import UserPublic, UserRole

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/loans/overdue",
    response_model=list[PrestamoRiesgoOut],
    summary="Active overdue loans from vw_prestamos_riesgo",
)
async def overdue_loans(
    _admin: Annotated[
        UserPublic, Depends(require_roles(UserRole.ADMINISTRADOR))
    ],
) -> list[PrestamoRiesgoOut]:
    rows = await execute(
        "SELECT * FROM vw_prestamos_riesgo ORDER BY ranking_mora",
        fetch="all",
        commit=False,
    )
    return [PrestamoRiesgoOut(**row) for row in (rows or [])]


@router.post(
    "/sanctions",
    response_model=SancionAppliedOut,
    status_code=status.HTTP_201_CREATED,
    summary="Apply sanction via CALL aplicar_sancion(...)",
)
async def apply_sanction(
    payload: SancionCreate,
    current_user: Annotated[
        UserPublic, Depends(require_roles(UserRole.ADMINISTRADOR))
    ],
) -> SancionAppliedOut:
    """
    Executes `CALL aplicar_sancion(p_id_prestamo, p_id_administrador, p_motivo, p_monto_incremento)`.
    Trigger/procedure SIGNAL 45000 → HTTP 400.
    """
    admin_id = payload.p_id_administrador
    if admin_id != current_user.id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="p_id_administrador must match the authenticated administrator",
        )

    try:
        await call_procedure(
            "aplicar_sancion",
            (
                payload.p_id_prestamo,
                admin_id,
                payload.p_motivo,
                float(payload.p_monto_incremento),
            ),
        )
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    return SancionAppliedOut(
        detail="Sanction applied successfully",
        p_id_prestamo=payload.p_id_prestamo,
        p_id_administrador=admin_id,
    )


@router.get(
    "/audit",
    response_model=list[AuditoriaOut],
    summary="Fetch transaction logs from AUDITORIA_TRANSACCIONES",
)
async def audit_log(
    _admin: Annotated[
        UserPublic, Depends(require_roles(UserRole.ADMINISTRADOR))
    ],
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    tipo_evento: Annotated[Optional[str], Query(max_length=50)] = None,
) -> list[AuditoriaOut]:
    where = "1=1"
    params: list[object] = []
    if tipo_evento:
        where = "tipo_evento = %s"
        params.append(tipo_evento)

    rows = await execute(
        f"""
        SELECT
            id_auditoria, id_compra, id_trueque, id_prestamo, id_administrador,
            tipo_evento, detalle_evento, fecha_registro, usuario_auditor
        FROM AUDITORIA_TRANSACCIONES
        WHERE {where}
        ORDER BY fecha_registro DESC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
        fetch="all",
        commit=False,
    )
    return [AuditoriaOut(**row) for row in (rows or [])]


@router.get(
    "/revenue",
    response_model=list[IngresoAcumuladoOut],
    summary="Cumulative platform revenue from vw_ingresos_acumulados",
)
async def revenue(
    _admin: Annotated[
        UserPublic, Depends(require_roles(UserRole.ADMINISTRADOR))
    ],
    limit: Annotated[int, Query(ge=1, le=1000)] = 200,
) -> list[IngresoAcumuladoOut]:
    rows = await execute(
        """
        SELECT fecha_transaccion, monto_total, ingreso_acumulado
        FROM vw_ingresos_acumulados
        ORDER BY fecha_transaccion
        LIMIT %s
        """,
        (limit,),
        fetch="all",
        commit=False,
    )
    return [IngresoAcumuladoOut(**row) for row in (rows or [])]
