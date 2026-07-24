/* 
  Clasifica los productos identificando éxitos atípicos o ventas muy bajas mediante 
  el Teorema de Chebyshev (k=2, al menos 75% de confianza), evaluando su probabilidad 
  individual frente a la media y desviación estándar del catálogo.
*/
WITH TablaProbabilidades AS (
    -- Paso 1: Obtenemos la probabilidad (proba) de cada producto usando la nueva función
    SELECT 
        id_producto,
        id_publicacion,
        precio,
        calcular_probabilidad_producto(id_producto) AS proba
    FROM PRODUCTO
),
MetricasChebyshev AS (
    -- Paso 2: Calculamos la media empirica (mu) y la desviacion estandar (sigma) de las probabilidades
    SELECT 
        AVG(proba) AS media_mu,
        STDDEV(proba) AS desviacion_sigma
    FROM TablaProbabilidades
)
-- Paso 3: Evaluamos cada producto con k=2 desviaciones estandar (al menos 75% de confianza)
SELECT 
    t.id_producto,
    t.proba,
    ROUND(m.media_mu, 6) AS media_del_catalogo,
    ROUND(m.desviacion_sigma, 6) AS desviacion_del_catalogo,
    ROUND(m.media_mu + (2 * m.desviacion_sigma), 6) AS limite_superior_chebyshev,
    CASE 
        WHEN t.proba > (m.media_mu + (2 * m.desviacion_sigma)) THEN 'Exito Atipico (Fuera del limite Chebyshev)'
        WHEN t.proba < (m.media_mu - (2 * m.desviacion_sigma)) THEN 'Ventas Muy Bajas'
        ELSE 'Comportamiento Normal (Dentro del 75 por ciento esperado)'
    END AS diagnostico_chebyshev
FROM TablaProbabilidades t
CROSS JOIN MetricasChebyshev ms
ORDER BY t.proba DESC;
/* 
  Genera un ranking de vendedores (con al menos 10 ventas) según su puntaje de 
  fiabilidad, asignando posiciones y calculando la diferencia de puntaje respecto 
  al vendedor en la posición anterior.
*/

WITH VendedoresFiltrados AS (
    SELECT
        id_vendedor,
        calificacion AS calificacion_actual,
        ventas_completadas,
        calcular_fiabilidad_vendedor(id_vendedor) AS puntuacion_fiabilidad
    FROM VENDEDOR
    WHERE ventas_completadas >= 10
),

Ranking AS (
    SELECT
        id_vendedor,
        calificacion_actual,
        ventas_completadas,
        puntuacion_fiabilidad,
        ROUND(puntuacion_fiabilidad,2) AS fiabilidad,

        DENSE_RANK() OVER (
            ORDER BY puntuacion_fiabilidad DESC
        ) AS ranking_fiabilidad,

        ROW_NUMBER() OVER (
            ORDER BY puntuacion_fiabilidad DESC
        ) AS posicion_fila,

        LAG(puntuacion_fiabilidad)
            OVER (
                ORDER BY puntuacion_fiabilidad DESC
            ) AS fiabilidad_anterior

    FROM VendedoresFiltrados
)

SELECT
    id_vendedor,
    calificacion_actual,
    ventas_completadas,
    fiabilidad,
    ranking_fiabilidad,
    posicion_fila,

    ROUND(
        COALESCE(
            puntuacion_fiabilidad - fiabilidad_anterior,
            0
        ),
        2
    ) AS diferencia_con_puesto_anterior

FROM Ranking

ORDER BY ranking_fiabilidad;
