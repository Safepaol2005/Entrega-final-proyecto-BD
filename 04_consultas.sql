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