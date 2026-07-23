-- 04_consultas.sql

-- ====================
-- N1: Selección y filtrado (2 consultas)
-- ====================
-- N1-01: ¿Qué publicaciones de productos físicos nuevos están activas actualmente?
SELECT id_publicacion, titulo, descripcion, fecha_publicacion 
FROM PUBLICACION 
WHERE estado_publicacion = 'Activa' AND tipo_item = 'Producto' AND titulo LIKE '%Libro%';

-- N1-02: ¿Cuáles compradores tienen preferencias de búsqueda definidas y se registraron este año?
SELECT id_comprador, preferencias_busqueda 
FROM COMPRADOR 
WHERE preferencias_busqueda IS NOT NULL AND id_comprador IN (SELECT id_usuario FROM USUARIO WHERE fecha_registro >= '2026-01-01');

-- ====================
-- N2: JOINs múltiples (3 consultas)
-- ====================
-- N2-01: ¿Cuál es el nombre de la materia, créditos académicos y la universidad que la dicta?
SELECT u.nombre AS universidad, m.nombre_materia, m.creditos 
FROM UNIVERSIDAD u 
INNER JOIN MATERIA m ON u.id_universidad = m.id_universidad;

-- N2-02: ¿Qué servicios ofrece cada vendedor junto con el nombre del administrador que modera la publicación?
SELECT pu.titulo, s.modalidad, v.calificacion AS rating_vendedor, a.area_soporte 
FROM PUBLICACION pu 
JOIN SERVICIO s ON pu.id_publicacion = s.id_publicacion
JOIN VENDEDOR v ON pu.id_vendedor = v.id_vendedor
JOIN ADMINISTRADOR a ON pu.id_administrador_moderador = a.id_administrador;

-- N2-03: (Diferencia significativa) ¿Qué usuarios registrados NUNCA han actuado como vendedores?
-- Un LEFT JOIN dejará nulos los datos de vendedor si el usuario no tiene rol allí.
SELECT us.nombre_completo, us.correo_estudiantil 
FROM USUARIO us 
LEFT JOIN VENDEDOR v ON us.id_usuario = v.id_vendedor 
WHERE v.id_vendedor IS NULL;

-- ====================
-- N3: Agregación (3 consultas)
-- ====================
-- N3-01: (Agrupación de múltiples columnas) ¿Cuál es el inventario total disponible y promedio de precios por categoría y estado físico?
SELECT categoria, estado_fisico, SUM(stock) AS stock_total, AVG(precio) AS precio_promedio 
FROM PRODUCTO 
GROUP BY categoria, estado_fisico 
HAVING SUM(stock) > 0;

-- N3-02: ¿Cuáles universidades tienen más de 10 usuarios registrados en la plataforma?
SELECT un.nombre, COUNT(u.id_usuario) AS total_usuarios 
FROM UNIVERSIDAD un 
JOIN USUARIO u ON un.id_universidad = u.id_universidad 
GROUP BY un.nombre 
HAVING COUNT(u.id_usuario) > 10;

-- N3-03: ¿Cuánto dinero se ha transaccionado por método de pago en el último semestre?
SELECT metodo_pago, SUM(monto_total) AS volumen_transaccional, COUNT(id_compra) AS cantidad_operaciones 
FROM COMPRA 
WHERE fecha_transaccion >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
GROUP BY metodo_pago;

-- ====================
-- N4: Subconsultas (3 consultas)
-- ====================
-- N4-01: (Subconsulta en FROM) ¿Cuál es el gasto promedio de los compradores que pertenecen al top 20% de compradores más activos?
SELECT AVG(volumen) AS gasto_promedio_top 
FROM (SELECT id_comprador, SUM(monto_total) AS volumen FROM COMPRA GROUP BY id_comprador) sub;

-- N4-02: (Subconsulta correlacionada) ¿Qué publicaciones tienen un precio superior al promedio del precio de su misma categoría?
SELECT pu.titulo, pr.precio, pr.categoria 
FROM PRODUCTO pr 
JOIN PUBLICACION pu ON pr.id_publicacion = pu.id_publicacion 
WHERE pr.precio > (SELECT AVG(precio) FROM PRODUCTO pr2 WHERE pr2.categoria = pr.categoria);

-- N4-03: (EXISTS/NOT EXISTS y CTE) ¿Qué vendedores no tienen ninguna publicación activa actualmente?
WITH VendedoresPublicadores AS (
    SELECT id_vendedor FROM PUBLICACION WHERE estado_publicacion = 'Activa'
)
SELECT u.nombre_completo 
FROM USUARIO u JOIN VENDEDOR v ON u.id_usuario = v.id_vendedor
WHERE NOT EXISTS (SELECT 1 FROM VendedoresPublicadores vp WHERE vp.id_vendedor = v.id_vendedor);

-- ====================
-- N5: Funciones de ventana (2 consultas)
-- ====================
-- N5-01: ¿Cuál es el ranking de los servicios más caros divididos según su modalidad (Presencial/Virtual)?
SELECT pu.titulo, s.modalidad, s.tarifa_por_hora, 
       RANK() OVER(PARTITION BY s.modalidad ORDER BY s.tarifa_por_hora DESC) AS ranking_precio 
FROM SERVICIO s 
JOIN PUBLICACION pu ON s.id_publicacion = pu.id_publicacion;

-- N5-02: ¿Cómo ha crecido el acumulado de ingresos financieros diarios de la plataforma históricamente?
SELECT fecha_transaccion, monto_total, 
       SUM(monto_total) OVER (ORDER BY fecha_transaccion ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ingreso_acumulado 
FROM COMPRA;

-- ====================
-- N6: Vistas (2 consultas)
-- ====================
-- N6-01: Vista para simplificar reportes de catálogo (oculta los JOINs).
CREATE VIEW vw_catalogo_completo AS 
SELECT pu.id_publicacion, pu.titulo, u.nombre_completo AS nombre_vendedor, 
       COALESCE(pr.precio, s.tarifa_por_hora) AS costo, pu.tipo_item
FROM PUBLICACION pu 
JOIN USUARIO u ON pu.id_vendedor = u.id_usuario
LEFT JOIN PRODUCTO pr ON pu.id_publicacion = pr.id_publicacion
LEFT JOIN SERVICIO s ON pu.id_publicacion = s.id_publicacion;

-- N6-02: Vista para monitoreo administrativo de préstamos vencidos.
CREATE VIEW vw_prestamos_riesgo AS 
SELECT pr.id_prestamo, uc.nombre_completo AS deudor, pu.titulo AS item_prestado, 
       pr.fecha_devolucion_pactada, DATEDIFF(NOW(), pr.fecha_devolucion_pactada) AS dias_retraso
FROM PRESTAMO pr 
JOIN COMPRADOR c ON pr.id_comprador = c.id_comprador
JOIN USUARIO uc ON c.id_comprador = uc.id_usuario
JOIN PUBLICACION pu ON pr.id_publicacion = pu.id_publicacion
WHERE pr.estado_prestamo = 'Activo' AND pr.fecha_devolucion_pactada < NOW();