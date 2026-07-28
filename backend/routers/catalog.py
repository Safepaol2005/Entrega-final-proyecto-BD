"""Catalog search, publication detail, categories, and Chebyshev analytics."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any, Optional

from fastapi import APIRouter, HTTPException, Query, status

from database import execute
from schemas.publication import (
    CategoriaOut,
    ChebyshevDiagnosticoOut,
    EstadoPublicacion,
    ModalidadServicio,
    ProductoOut,
    PublicacionListOut,
    PublicacionOut,
    ServicioOut,
    TipoItem,
)

router = APIRouter(prefix="/catalog", tags=["catalog"])

CHEBYSHEV_SQL = """
WITH TablaProbabilidades AS (
    SELECT
        id_producto,
        id_publicacion,
        precio,
        calcular_probabilidad_producto(id_producto) AS proba
    FROM PRODUCTO
),
MetricasChebyshev AS (
    SELECT
        AVG(proba) AS media_mu,
        STDDEV(proba) AS desviacion_sigma
    FROM TablaProbabilidades
)
SELECT
    t.id_producto,
    t.proba,
    ROUND(m.media_mu, 6) AS media_del_catalogo,
    ROUND(m.desviacion_sigma, 6) AS desviacion_del_catalogo,
    ROUND(m.media_mu + (2 * m.desviacion_sigma), 6) AS limite_superior_chebyshev,
    CASE
        WHEN t.proba > (m.media_mu + (2 * m.desviacion_sigma))
            THEN 'Exito Atipico (Fuera del limite Chebyshev)'
        WHEN t.proba < (m.media_mu - (2 * m.desviacion_sigma))
            THEN 'Ventas Muy Bajas'
        ELSE 'Comportamiento Normal (Dentro del 75 por ciento esperado)'
    END AS diagnostico_chebyshev
FROM TablaProbabilidades t
CROSS JOIN MetricasChebyshev m
ORDER BY t.proba DESC
"""


def _row_to_publicacion(row: dict[str, Any], categorias: Optional[list[str]] = None) -> PublicacionOut:
    producto = None
    servicio = None
    precio_efectivo: Optional[Decimal] = None

    if row.get("id_producto") is not None:
        producto = ProductoOut(
            id_producto=row["id_producto"],
            precio=row["precio"],
            calificacion=row.get("prod_calificacion"),
            estado_fisico=row["estado_fisico"],
            stock=row["stock"],
        )
        precio_efectivo = row["precio"]

    if row.get("id_servicio") is not None:
        servicio = ServicioOut(
            id_servicio=row["id_servicio"],
            modalidad=row["modalidad"],
            tarifa_por_hora=row["tarifa_por_hora"],
            disponibilidad_horaria=row["disponibilidad_horaria"],
            calificacion=row.get("serv_calificacion"),
        )
        precio_efectivo = row["tarifa_por_hora"]

    return PublicacionOut(
        id_publicacion=row["id_publicacion"],
        id_vendedor=row["id_vendedor"],
        id_administrador_moderador=row.get("id_administrador_moderador"),
        tipo_item=row["tipo_item"],
        titulo=row["titulo"],
        descripcion=row.get("descripcion"),
        fecha_publicacion=row["fecha_publicacion"],
        estado_publicacion=row["estado_publicacion"],
        producto=producto,
        servicio=servicio,
        vendedor_nombre=row.get("vendedor_nombre"),
        universidad_nombre=row.get("universidad_nombre"),
        id_universidad=row.get("id_universidad"),
        categorias=categorias or [],
        precio_efectivo=precio_efectivo,
    )


async def _categorias_for_producto(id_producto: int) -> list[str]:
    rows = await execute(
        """
        SELECT c.nombre
        FROM CATEGORIA_PRODUCTO cp
        INNER JOIN CATEGORIA c ON c.id_categoria = cp.id_categoria
        WHERE cp.id_producto = %s
        ORDER BY c.nombre
        """,
        (id_producto,),
        fetch="all",
        commit=False,
    )
    return [r["nombre"] for r in (rows or [])]


@router.get(
    "/publications",
    response_model=PublicacionListOut,
    summary="List publications with optional catalog filters",
)
async def list_publications(
    id_categoria: Annotated[Optional[int], Query(gt=0)] = None,
    id_universidad: Annotated[Optional[int], Query(gt=0)] = None,
    precio_min: Annotated[Optional[Decimal], Query(ge=0)] = None,
    precio_max: Annotated[Optional[Decimal], Query(ge=0)] = None,
    tipo_item: Annotated[Optional[TipoItem], Query()] = None,
    estado_publicacion: Annotated[
        Optional[EstadoPublicacion], Query()
    ] = EstadoPublicacion.ACTIVA,
    modalidad: Annotated[Optional[ModalidadServicio], Query()] = None,
    q: Annotated[Optional[str], Query(max_length=150)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PublicacionListOut:
    where: list[str] = ["1=1"]
    params: list[Any] = []

    if estado_publicacion is not None:
        where.append("pu.estado_publicacion = %s")
        params.append(estado_publicacion.value)

    if tipo_item is not None:
        where.append("pu.tipo_item = %s")
        params.append(tipo_item.value)

    if id_universidad is not None:
        where.append("u.id_universidad = %s")
        params.append(id_universidad)

    if id_categoria is not None:
        where.append(
            """
            EXISTS (
                SELECT 1
                FROM CATEGORIA_PRODUCTO cp
                WHERE cp.id_producto = pr.id_producto
                  AND cp.id_categoria = %s
            )
            """
        )
        params.append(id_categoria)

    if modalidad is not None:
        where.append("s.modalidad = %s")
        params.append(modalidad.value)

    if q:
        where.append("(pu.titulo LIKE %s OR pu.descripcion LIKE %s)")
        like = f"%{q}%"
        params.extend([like, like])

    # Effective price: product price or service hourly rate
    price_expr = "COALESCE(pr.precio, s.tarifa_por_hora)"
    if precio_min is not None:
        where.append(f"{price_expr} >= %s")
        params.append(precio_min)
    if precio_max is not None:
        where.append(f"{price_expr} <= %s")
        params.append(precio_max)

    where_sql = " AND ".join(where)

    count_row = await execute(
        f"""
        SELECT COUNT(DISTINCT pu.id_publicacion) AS total
        FROM PUBLICACION pu
        INNER JOIN VENDEDOR v ON v.id_vendedor = pu.id_vendedor
        INNER JOIN USUARIO u ON u.id_usuario = v.id_vendedor
        INNER JOIN UNIVERSIDAD un ON un.id_universidad = u.id_universidad
        LEFT JOIN PRODUCTO pr ON pr.id_publicacion = pu.id_publicacion
        LEFT JOIN SERVICIO s ON s.id_publicacion = pu.id_publicacion
        WHERE {where_sql}
        """,
        params,
        fetch="one",
        commit=False,
    )
    total = int((count_row or {}).get("total") or 0)

    rows = await execute(
        f"""
        SELECT
            pu.id_publicacion,
            pu.id_vendedor,
            pu.id_administrador_moderador,
            pu.tipo_item,
            pu.titulo,
            pu.descripcion,
            pu.fecha_publicacion,
            pu.estado_publicacion,
            u.nombre_completo AS vendedor_nombre,
            u.id_universidad,
            un.nombre AS universidad_nombre,
            pr.id_producto,
            pr.precio,
            pr.calificacion AS prod_calificacion,
            pr.estado_fisico,
            pr.stock,
            s.id_servicio,
            s.modalidad,
            s.tarifa_por_hora,
            s.disponibilidad_horaria,
            s.calificacion AS serv_calificacion
        FROM PUBLICACION pu
        INNER JOIN VENDEDOR v ON v.id_vendedor = pu.id_vendedor
        INNER JOIN USUARIO u ON u.id_usuario = v.id_vendedor
        INNER JOIN UNIVERSIDAD un ON un.id_universidad = u.id_universidad
        LEFT JOIN PRODUCTO pr ON pr.id_publicacion = pu.id_publicacion
        LEFT JOIN SERVICIO s ON s.id_publicacion = pu.id_publicacion
        WHERE {where_sql}
        ORDER BY pu.fecha_publicacion DESC
        LIMIT %s OFFSET %s
        """,
        [*params, limit, offset],
        fetch="all",
        commit=False,
    )

    items: list[PublicacionOut] = []
    for row in rows or []:
        cats: list[str] = []
        if row.get("id_producto") is not None:
            cats = await _categorias_for_producto(row["id_producto"])
        items.append(_row_to_publicacion(row, cats))

    return PublicacionListOut(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/publications/{id_publicacion}",
    response_model=PublicacionOut,
    summary="Detailed view of a single publication",
)
async def get_publication(id_publicacion: int) -> PublicacionOut:
    row = await execute(
        """
        SELECT
            pu.id_publicacion,
            pu.id_vendedor,
            pu.id_administrador_moderador,
            pu.tipo_item,
            pu.titulo,
            pu.descripcion,
            pu.fecha_publicacion,
            pu.estado_publicacion,
            u.nombre_completo AS vendedor_nombre,
            u.id_universidad,
            un.nombre AS universidad_nombre,
            pr.id_producto,
            pr.precio,
            pr.calificacion AS prod_calificacion,
            pr.estado_fisico,
            pr.stock,
            s.id_servicio,
            s.modalidad,
            s.tarifa_por_hora,
            s.disponibilidad_horaria,
            s.calificacion AS serv_calificacion
        FROM PUBLICACION pu
        INNER JOIN VENDEDOR v ON v.id_vendedor = pu.id_vendedor
        INNER JOIN USUARIO u ON u.id_usuario = v.id_vendedor
        INNER JOIN UNIVERSIDAD un ON un.id_universidad = u.id_universidad
        LEFT JOIN PRODUCTO pr ON pr.id_publicacion = pu.id_publicacion
        LEFT JOIN SERVICIO s ON s.id_publicacion = pu.id_publicacion
        WHERE pu.id_publicacion = %s
        """,
        (id_publicacion,),
        fetch="one",
        commit=False,
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publication {id_publicacion} not found",
        )

    cats: list[str] = []
    if row.get("id_producto") is not None:
        cats = await _categorias_for_producto(row["id_producto"])
    return _row_to_publicacion(row, cats)


@router.get(
    "/categories",
    response_model=list[CategoriaOut],
    summary="List all CATEGORIA items",
)
async def list_categories() -> list[CategoriaOut]:
    rows = await execute(
        "SELECT id_categoria, nombre FROM CATEGORIA ORDER BY nombre",
        fetch="all",
        commit=False,
    )
    return [CategoriaOut(**r) for r in (rows or [])]


@router.get(
    "/analytics/chebyshev",
    response_model=list[ChebyshevDiagnosticoOut],
    summary="Chebyshev outlier diagnostic via calcular_probabilidad_producto",
)
async def chebyshev_analytics() -> list[ChebyshevDiagnosticoOut]:
    """
    Classifies product demand using Chebyshev (k=2, ≥75% confidence):
    Exito Atipico / Ventas Muy Bajas / Comportamiento Normal.
    """
    rows = await execute(CHEBYSHEV_SQL, fetch="all", commit=False)
    return [ChebyshevDiagnosticoOut(**r) for r in (rows or [])]
