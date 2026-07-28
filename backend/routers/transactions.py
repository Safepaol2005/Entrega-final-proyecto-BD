"""Transactional endpoints: COMPRA, OFERTA, TRUEQUE, PRESTAMO."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from database import BusinessRuleError, execute, raise_http_from_business_rule
from deps import get_current_user, require_roles
from schemas.transaction import (
    CompraCreate,
    CompraOut,
    EstadoOferta,
    OfertaCreate,
    OfertaEstadoUpdate,
    OfertaOut,
    PrestamoCreate,
    PrestamoOut,
    TruequeCreate,
    TruequeOut,
)
from schemas.user import UserPublic, UserRole

router = APIRouter(prefix="/transactions", tags=["transactions"])


async def _fetch_one(sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    return await execute(sql, params, fetch="one", commit=False)


@router.post(
    "/buy",
    response_model=CompraOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a purchase (COMPRA); trigger validates stock/schedule",
)
async def buy(
    payload: CompraCreate,
    current_user: Annotated[
        UserPublic, Depends(require_roles(UserRole.COMPRADOR))
    ],
) -> CompraOut:
    """
    INSERT INTO COMPRA. Trigger `trg_validar_disponibilidad_compra` raises
    SQLSTATE 45000 when stock <= 0 or service availability is empty — mapped to HTTP 400.
    """
    try:
        result = await execute(
            """
            INSERT INTO COMPRA (id_comprador, id_publicacion, monto_total, metodo_pago)
            VALUES (%s, %s, %s, %s)
            """,
            (
                current_user.id_usuario,
                payload.id_publicacion,
                payload.monto_total,
                payload.metodo_pago,
            ),
        )
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    row = await _fetch_one(
        """
        SELECT id_compra, id_comprador, id_publicacion, monto_total,
               fecha_transaccion, metodo_pago
        FROM COMPRA WHERE id_compra = %s
        """,
        (result["lastrowid"],),
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Purchase created but could not be reloaded",
        )
    return CompraOut(**row)


@router.post(
    "/offers",
    response_model=OfertaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a price offer (OFERTA)",
)
async def create_offer(
    payload: OfertaCreate,
    current_user: Annotated[
        UserPublic, Depends(require_roles(UserRole.COMPRADOR))
    ],
) -> OfertaOut:
    pub = await _fetch_one(
        "SELECT id_publicacion FROM PUBLICACION WHERE id_publicacion = %s",
        (payload.id_publicacion,),
    )
    if pub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication {payload.id_publicacion} not found",
        )

    try:
        result = await execute(
            """
            INSERT INTO OFERTA (id_comprador, id_publicacion, monto_ofertado)
            VALUES (%s, %s, %s)
            """,
            (current_user.id_usuario, payload.id_publicacion, payload.monto_ofertado),
        )
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    row = await _fetch_one(
        """
        SELECT id_oferta, id_comprador, id_publicacion, monto_ofertado,
               fecha_oferta, estado_oferta
        FROM OFERTA WHERE id_oferta = %s
        """,
        (result["lastrowid"],),
    )
    assert row is not None
    return OfertaOut(**row)


@router.patch(
    "/offers/{id_oferta}",
    response_model=OfertaOut,
    summary="Accept or reject an offer (Aceptada / Rechazada)",
)
async def update_offer(
    id_oferta: int,
    payload: OfertaEstadoUpdate,
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> OfertaOut:
    oferta = await _fetch_one(
        """
        SELECT o.id_oferta, o.id_comprador, o.id_publicacion, o.monto_ofertado,
               o.fecha_oferta, o.estado_oferta, pu.id_vendedor
        FROM OFERTA o
        INNER JOIN PUBLICACION pu ON pu.id_publicacion = o.id_publicacion
        WHERE o.id_oferta = %s
        """,
        (id_oferta,),
    )
    if oferta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Offer {id_oferta} not found",
        )

    is_seller = (
        UserRole.VENDEDOR in current_user.roles
        and oferta["id_vendedor"] == current_user.id_usuario
    )
    is_admin = UserRole.ADMINISTRADOR in current_user.roles
    if not (is_seller or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the publication seller or an admin can accept/reject offers",
        )

    if oferta["estado_oferta"] != EstadoOferta.PENDIENTE.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Offer is already {oferta['estado_oferta']}",
        )

    await execute(
        "UPDATE OFERTA SET estado_oferta = %s WHERE id_oferta = %s",
        (payload.estado_oferta.value, id_oferta),
    )

    row = await _fetch_one(
        """
        SELECT id_oferta, id_comprador, id_publicacion, monto_ofertado,
               fecha_oferta, estado_oferta
        FROM OFERTA WHERE id_oferta = %s
        """,
        (id_oferta,),
    )
    assert row is not None
    return OfertaOut(**row)


@router.post(
    "/barter",
    response_model=TruequeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Propose a trade (TRUEQUE)",
)
async def create_barter(
    payload: TruequeCreate,
    current_user: Annotated[
        UserPublic, Depends(require_roles(UserRole.COMPRADOR))
    ],
) -> TruequeOut:
    for pub_id, label in (
        (payload.id_publicacion_deseada, "desired"),
        (payload.id_publicacion_ofrecida, "offered"),
    ):
        exists = await _fetch_one(
            "SELECT id_publicacion FROM PUBLICACION WHERE id_publicacion = %s",
            (pub_id,),
        )
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Publication {pub_id} ({label}) not found",
            )

    try:
        result = await execute(
            """
            INSERT INTO TRUEQUE (
                id_comprador_iniciador,
                id_publicacion_deseada,
                id_publicacion_ofrecida
            )
            VALUES (%s, %s, %s)
            """,
            (
                current_user.id_usuario,
                payload.id_publicacion_deseada,
                payload.id_publicacion_ofrecida,
            ),
        )
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    row = await _fetch_one(
        """
        SELECT id_trueque, id_comprador_iniciador, id_publicacion_deseada,
               id_publicacion_ofrecida, fecha_propuesta, estado_trueque
        FROM TRUEQUE WHERE id_trueque = %s
        """,
        (result["lastrowid"],),
    )
    assert row is not None
    return TruequeOut(**row)


@router.post(
    "/loans",
    response_model=PrestamoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Request an item loan (PRESTAMO)",
)
async def create_loan(
    payload: PrestamoCreate,
    current_user: Annotated[
        UserPublic, Depends(require_roles(UserRole.COMPRADOR))
    ],
) -> PrestamoOut:
    pub = await _fetch_one(
        "SELECT id_publicacion FROM PUBLICACION WHERE id_publicacion = %s",
        (payload.id_publicacion,),
    )
    if pub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication {payload.id_publicacion} not found",
        )

    try:
        result = await execute(
            """
            INSERT INTO PRESTAMO (
                id_comprador,
                id_publicacion,
                fecha_inicio,
                fecha_devolucion_pactada
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                current_user.id_usuario,
                payload.id_publicacion,
                payload.fecha_inicio,
                payload.fecha_devolucion_pactada,
            ),
        )
    except BusinessRuleError as exc:
        raise_http_from_business_rule(exc)

    row = await _fetch_one(
        """
        SELECT id_prestamo, id_comprador, id_publicacion, fecha_solicitud,
               fecha_inicio, fecha_devolucion_pactada, fecha_devolucion_real,
               estado_prestamo
        FROM PRESTAMO WHERE id_prestamo = %s
        """,
        (result["lastrowid"],),
    )
    assert row is not None
    return PrestamoOut(**row)
