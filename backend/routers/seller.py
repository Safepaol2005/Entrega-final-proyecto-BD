"""Seller metrics: calificar_vendedor procedure and ranking view."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from database import BusinessRuleError, call_procedure, execute, raise_http_from_business_rule
from deps import get_current_user
from schemas.admin import RankingVendedorOut
from schemas.transaction import CalificarVendedorOut
from schemas.user import UserPublic

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post(
    "/{id_vendedor}/rate",
    response_model=CalificarVendedorOut,
    summary="Recalculate seller rating via CALL calificar_vendedor",
)
async def rate_seller(
    id_vendedor: int,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> CalificarVendedorOut:
    """
    Executes `CALL calificar_vendedor(p_id_vendedor)`.
    SIGNAL 45000 (unknown seller) → HTTP 400.
    """
    _ = current_user  # authenticated callers only
    try:
        await call_procedure("calificar_vendedor", (id_vendedor,))
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    row = await execute(
        "SELECT id_vendedor, calificacion FROM VENDEDOR WHERE id_vendedor = %s",
        (id_vendedor,),
        fetch="one",
        commit=False,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seller {id_vendedor} not found",
        )
    return CalificarVendedorOut(
        id_vendedor=row["id_vendedor"],
        calificacion=row["calificacion"],
    )


@router.get(
    "/ranking",
    response_model=list[RankingVendedorOut],
    summary="Seller reliability ranking from vista_ranking_vendedores",
)
async def seller_ranking() -> list[RankingVendedorOut]:
    rows = await execute(
        """
        SELECT
            r.id_vendedor,
            r.calificacion_actual,
            r.ventas_completadas,
            r.fiabilidad,
            r.ranking_fiabilidad,
            r.posicion_fila,
            r.diferencia_con_puesto_anterior,
            u.nombre_completo AS vendedor_nombre
        FROM vista_ranking_vendedores r
        LEFT JOIN USUARIO u ON u.id_usuario = r.id_vendedor
        ORDER BY r.ranking_fiabilidad
        """,
        fetch="all",
        commit=False,
    )
    return [RankingVendedorOut(**row) for row in (rows or [])]
