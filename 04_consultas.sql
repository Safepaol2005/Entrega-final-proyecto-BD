-- ==========================================
-- NIVEL 1: SELECCIÓN Y FILTRADO
-- ==========================================

-- Consulta N1-01: Identifica los identificadores de los productos asociados a una materia específica.
SELECT id_producto 
FROM MATERIA_PRODUCTO 
WHERE id_materia = 5;

-- Consulta N1-02: Retorna los productos de una categoría específica dentro de un rango de precio.
SELECT cp.id_producto, p.precio, c.nombre
FROM PRODUCTO p
JOIN CATEGORIA_PRODUCTO cp ON p.id_producto = cp.id_producto
JOIN CATEGORIA c ON cp.id_categoria = c.id_categoria
WHERE p.precio BETWEEN 20000 AND 80000
  AND c.nombre = 'Libros y Textos';

-- Consulta N1-03: Muestra las publicaciones de productos físicos que se encuentran activas actualmente.
SELECT id_publicacion, titulo, descripcion, fecha_publicacion 
FROM PUBLICACION 
WHERE estado_publicacion = 'Activa' AND tipo_item = 'Producto';


-- ==========================================
-- NIVEL 2: JOINS MÚLTIPLES
-- ==========================================

-- Consulta N2-01: Muestra los administradores asociados a cada materia, incluyendo materias sin administradores.
SELECT m.nombre_materia, a.id_administrador, a.area_soporte
FROM MATERIA m
LEFT JOIN MATERIA_PRODUCTO mp ON m.id_materia = mp.id_materia
LEFT JOIN PRODUCTO p ON mp.id_producto = p.id_producto
LEFT JOIN PUBLICACION pu ON p.id_publicacion = pu.id_publicacion
LEFT JOIN ADMINISTRADOR a ON pu.id_administrador_moderador = a.id_administrador;

-- Consulta N2-02: Identifica los productos ofrecidos por vendedores para una materia específica.
SELECT v.id_vendedor, u.nombre_completo, pu.titulo AS producto_titulo, m.nombre_materia
FROM VENDEDOR v
JOIN USUARIO u ON v.id_vendedor = u.id_usuario
JOIN PUBLICACION pu ON v.id_vendedor = pu.id_vendedor
JOIN PRODUCTO p ON pu.id_publicacion = p.id_publicacion
JOIN MATERIA_PRODUCTO mp ON p.id_producto = mp.id_producto
JOIN MATERIA m ON mp.id_materia = m.id_materia
WHERE m.id_materia = 1;

-- Consulta N2-03: Vincula los servicios ofrecidos con el nombre del administrador moderador y la calificación del vendedor.
SELECT pu.titulo, s.modalidad, v.calificacion AS rating_vendedor, a.area_soporte 
FROM PUBLICACION pu 
JOIN SERVICIO s ON pu.id_publicacion = s.id_publicacion
JOIN VENDEDOR v ON pu.id_vendedor = v.id_vendedor
JOIN ADMINISTRADOR a ON pu.id_administrador_moderador = a.id_administrador;

-- Consulta N2-04: Filtra los usuarios registrados que nunca han actuado como vendedores.
SELECT us.nombre_completo, us.correo_estudiantil 
FROM USUARIO us 
LEFT JOIN VENDEDOR v ON us.id_usuario = v.id_vendedor 
WHERE v.id_vendedor IS NULL;

-- Consulta N2-05: Busca usuarios que compren y vendan el mismo producto físico.
SELECT DISTINCT u.id_usuario, u.nombre_completo, p.id_producto, pu_compra.titulo
FROM USUARIO u
JOIN COMPRADOR c ON u.id_usuario = c.id_comprador
JOIN COMPRA co ON c.id_comprador = co.id_comprador
JOIN PUBLICACION pu_compra ON co.id_publicacion = pu_compra.id_publicacion
JOIN PRODUCTO p ON pu_compra.id_publicacion = p.id_publicacion
JOIN PUBLICACION pu_venta ON p.id_publicacion = pu_venta.id_publicacion
JOIN VENDEDOR v ON pu_venta.id_vendedor = v.id_vendedor
WHERE v.id_vendedor = u.id_usuario;


-- ==========================================
-- NIVEL 3: AGREGACIÓN
-- ==========================================

-- Consulta N3-01: Calcula el ingreso total generado por cada vendedor en ventas finalizadas superiores a un umbral.
SELECT pu.id_vendedor, u.nombre_completo, SUM(co.monto_total) AS ingreso_total
FROM COMPRA co
JOIN PUBLICACION pu ON co.id_publicacion = pu.id_publicacion
JOIN USUARIO u ON pu.id_vendedor = u.id_usuario
GROUP BY pu.id_vendedor, u.nombre_completo
HAVING SUM(co.monto_total) > 50000;

-- Consulta N3-02: Calcula el mayor precio ofertado para cada publicación.
SELECT id_publicacion, MAX(monto_ofertado) AS mayor_precio_ofertado
FROM OFERTA
GROUP BY id_publicacion;

-- Consulta N3-03: Cuantifica la cantidad de préstamos solicitados por cada comprador, excluyendo esporádicos.
SELECT pr.id_comprador, u.nombre_completo, COUNT(pr.id_prestamo) AS total_prestamos
FROM PRESTAMO pr
JOIN USUARIO u ON pr.id_comprador = u.id_usuario
GROUP BY pr.id_comprador, u.nombre_completo
HAVING COUNT(pr.id_prestamo) > 2;

-- Consulta N3-04: Calcula el volumen transaccional y cantidad de operaciones por método de pago en el último semestre.
SELECT metodo_pago, SUM(monto_total) AS volumen_transaccional, COUNT(id_compra) AS cantidad_operaciones 
FROM COMPRA 
WHERE fecha_transaccion >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY metodo_pago;


-- ==========================================
-- NIVEL 4: SUBCONSULTAS
-- ==========================================

-- Consulta N4-01: Enlista los productos que actualmente no tienen publicaciones de venta activas.
SELECT p.id_producto, pu.titulo
FROM PRODUCTO p INNER JOIN PUBLICACION pu ON p.id_publicacion = pu.id_publicacion
WHERE NOT EXISTS (
    SELECT 1 
    FROM PUBLICACION v 
    WHERE v.id_publicacion = p.id_publicacion
      AND v.estado_publicacion = 'Activa'
);

-- Consulta N4-02: Obtiene el comprador con el mayor gasto acumulado en la plataforma.
SELECT id_comprador, dinero_gastado
FROM (
    SELECT id_comprador, SUM(monto_total) AS dinero_gastado 
    FROM COMPRA 
    GROUP BY id_comprador
) AS totales
WHERE dinero_gastado = (
    SELECT MAX(dinero_gastado)
    FROM (
        SELECT SUM(monto_total) AS dinero_gastado 
        FROM COMPRA 
        GROUP BY id_comprador
    ) AS maximos
);

-- Consulta N4-03: Obtiene los vendedores cuyo catálogo de productos abarca la totalidad de las materias registradas.
SELECT pu.id_vendedor
FROM PUBLICACION pu
JOIN PRODUCTO pr ON pu.id_publicacion = pr.id_publicacion
JOIN MATERIA_PRODUCTO mp ON pr.id_producto = mp.id_producto
GROUP BY pu.id_vendedor
HAVING COUNT(DISTINCT mp.id_materia) = (SELECT COUNT(*) FROM MATERIA);

-- Consulta N4-04: Lista los vendedores que actualmente no tienen ninguna publicación activa.
WITH VendedoresPublicadores AS (
    SELECT id_vendedor FROM PUBLICACION WHERE estado_publicacion = 'Activa'
)
SELECT u.nombre_completo 
FROM USUARIO u JOIN VENDEDOR v ON u.id_usuario = v.id_vendedor
WHERE NOT EXISTS (SELECT 1 FROM VendedoresPublicadores vp WHERE vp.id_vendedor = v.id_vendedor);

-- Consulta N4-05: Retorna las universidades y la cantidad total de usuarios registrados en cada una.
SELECT uni.nombre AS universidad,
       (SELECT COUNT(*) 
        FROM USUARIO u 
        WHERE u.id_universidad = uni.id_universidad) AS total_usuarios
FROM UNIVERSIDAD uni;


-- ==========================================
-- NIVEL 5: FUNCIONES DE VENTANA
-- ==========================================

-- Consulta N5-01: Genera un ranking de los productos más caros dentro de cada estado físico.
SELECT id_producto, estado_fisico, precio,
       RANK() OVER (PARTITION BY estado_fisico ORDER BY precio DESC) AS ranking_precio
FROM PRODUCTO;

-- Consulta N5-02: Calcula el historial acumulado del monto de compras por cada comprador a lo largo del tiempo.
SELECT id_comprador, fecha_transaccion, monto_total,
       SUM(monto_total) OVER (
           PARTITION BY id_comprador 
           ORDER BY fecha_transaccion
       ) AS gasto_acumulado
FROM COMPRA;

-- Consulta N5-03
/* 
  Clasifica los productos identificando éxitos atípicos o ventas muy bajas mediante 
  el Teorema de Chebyshev (k=2, al menos 75% de confianza), evaluando su probabilidad 
  individual frente a la media y desviación estándar del catálogo.
*/
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
        WHEN t.proba > (m.media_mu + (2 * m.desviacion_sigma)) THEN 'Exito Atipico (Fuera del limite Chebyshev)'
        WHEN t.proba < (m.media_mu - (2 * m.desviacion_sigma)) THEN 'Ventas Muy Bajas'
        ELSE 'Comportamiento Normal (Dentro del 75 por ciento esperado)'
    END AS diagnostico_chebyshev
FROM TablaProbabilidades t
CROSS JOIN MetricasChebyshev m
ORDER BY t.proba DESC;

-- ==========================================
-- NIVEL 6: VISTAS
-- ==========================================

-- Consulta N6-01: Crea una vista con el ranking de los servicios más caros divididos por su modalidad.
CREATE OR REPLACE VIEW vw_ranking_servicios_modalidad AS
SELECT pu.titulo, 
       s.modalidad, 
       s.tarifa_por_hora, 
       RANK() OVER (PARTITION BY s.modalidad ORDER BY s.tarifa_por_hora DESC) AS ranking_precio 
FROM SERVICIO s 
JOIN PUBLICACION pu ON s.id_publicacion = pu.id_publicacion;

-- Consulta N6-02: Crea una vista del acumulado histórico de ingresos financieros diarios de la plataforma.
CREATE OR REPLACE VIEW vw_ingresos_acumulados AS
SELECT fecha_transaccion, 
       monto_total, 
       SUM(monto_total) OVER (
           ORDER BY fecha_transaccion 
           ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
       ) AS ingreso_acumulado 
FROM COMPRA;

-- Consulta N6-03: Crea una vista de monitoreo administrativo para préstamos activos vencidos.
CREATE OR REPLACE VIEW vw_prestamos_riesgo AS 
SELECT pr.id_prestamo, 
       uc.nombre_completo AS deudor, 
       pu.titulo AS item_prestado, 
       pr.fecha_devolucion_pactada, 
       DATEDIFF(NOW(), pr.fecha_devolucion_pactada) AS dias_retraso,
       RANK() OVER (ORDER BY DATEDIFF(NOW(), pr.fecha_devolucion_pactada) DESC) AS ranking_mora
FROM PRESTAMO pr 
JOIN COMPRADOR c ON pr.id_comprador = c.id_comprador
JOIN USUARIO uc ON c.id_comprador = uc.id_usuario
JOIN PUBLICACION pu ON pr.id_publicacion = pu.id_publicacion
WHERE pr.estado_prestamo = 'Activo' 
  AND pr.fecha_devolucion_pactada < NOW();

-- Consulta N6-04: Crea una vista de la actividad transaccional de los compradores, rankeados por compras.
CREATE OR REPLACE VIEW vw_actividad_compradores AS
SELECT c.id_comprador, 
       u.nombre_completo,
       (SELECT COUNT(*) FROM COMPRA co WHERE co.id_comprador = c.id_comprador) AS total_compras,
       (SELECT COUNT(*) FROM OFERTA o WHERE o.id_comprador = c.id_comprador) AS total_ofertas,
       DENSE_RANK() OVER (
           ORDER BY (SELECT COUNT(*) FROM COMPRA co WHERE co.id_comprador = c.id_comprador) DESC
       ) AS ranking_comprador
FROM COMPRADOR c
JOIN USUARIO u ON c.id_comprador = u.id_usuario;

-- Consulta N6-05
CREATE OR REPLACE VIEW vista_ranking_vendedores AS
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
        ROUND(puntuacion_fiabilidad, 2) AS fiabilidad,

        DENSE_RANK() OVER (
            ORDER BY puntuacion_fiabilidad DESC
        ) AS ranking_fiabilidad,

        ROW_NUMBER() OVER (
            ORDER BY puntuacion_fiabilidad DESC
        ) AS posicion_fila,

        LAG(puntuacion_fiabilidad) OVER (
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