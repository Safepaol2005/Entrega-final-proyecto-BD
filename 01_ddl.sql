-- 1. CREACIÓN DEL ESQUEMA
CREATE DATABASE IF NOT EXISTS UnTrade;
USE UnTrade;

-- 2. LIMPIEZA DE TABLAS PREVIAS (Orden Inverso a dependencias)
DROP TABLE IF EXISTS AUDITORIA_TRANSACCIONES CASCADE;
DROP TABLE IF EXISTS SANCION CASCADE;
DROP TABLE IF EXISTS CATEGORIA_PRODUCTO CASCADE; -- Se destruye la dependencia M:N primero
DROP TABLE IF EXISTS MATERIA_PRODUCTO CASCADE;
DROP TABLE IF EXISTS COMPRA CASCADE;
DROP TABLE IF EXISTS PRESTAMO CASCADE;
DROP TABLE IF EXISTS TRUEQUE CASCADE;
DROP TABLE IF EXISTS OFERTA CASCADE;
DROP TABLE IF EXISTS SERVICIO CASCADE;
DROP TABLE IF EXISTS PRODUCTO CASCADE;         
DROP TABLE IF EXISTS CATEGORIA CASCADE;         
DROP TABLE IF EXISTS PUBLICACION CASCADE;
DROP TABLE IF EXISTS MATERIA CASCADE;
DROP TABLE IF EXISTS COMPRADOR CASCADE;
DROP TABLE IF EXISTS VENDEDOR CASCADE;
DROP TABLE IF EXISTS ADMINISTRADOR CASCADE;
DROP TABLE IF EXISTS USUARIO CASCADE;
DROP TABLE IF EXISTS UNIVERSIDAD CASCADE;

-- 3. CREACIÓN DE ENTIDADES FUERTES Y SUPERCLASE
CREATE TABLE UNIVERSIDAD (
    id_universidad INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,
    pais VARCHAR(50) NOT NULL,
    dominio_correo VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (id_universidad),
    CONSTRAINT chk_dominio_correo CHECK (dominio_correo LIKE '%@%.%')
);

CREATE TABLE USUARIO (
    id_usuario INT NOT NULL AUTO_INCREMENT,
    id_universidad INT NOT NULL,
    nombre_completo VARCHAR(50) NOT NULL,
    correo_estudiantil VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario),
    CONSTRAINT fk_usuario_univ FOREIGN KEY (id_universidad)
        REFERENCES UNIVERSIDAD (id_universidad) ON DELETE RESTRICT,
    CONSTRAINT chk_correo_estudiantil CHECK (correo_estudiantil LIKE '%@%')
);

-- 4. CREACIÓN DE SUBCLASES DE USUARIO
CREATE TABLE ADMINISTRADOR (
    id_administrador INT NOT NULL,
    nivel_permiso VARCHAR(20) NOT NULL,
    fecha_asignacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    area_soporte VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_administrador),
    CONSTRAINT fk_admin_usuario FOREIGN KEY (id_administrador)
        REFERENCES USUARIO(id_usuario) ON DELETE CASCADE,
    CONSTRAINT chk_nivel_permiso CHECK (nivel_permiso IN ('SuperAdmin', 'Moderador', 'Soporte'))
);

CREATE TABLE VENDEDOR (
    id_vendedor INT NOT NULL,
    calificacion DECIMAL(3,1) NOT NULL,
    ventas_completadas INT NOT NULL DEFAULT 0,
    PRIMARY KEY (id_vendedor),
    CONSTRAINT fk_vendedor_usuario FOREIGN KEY (id_vendedor)
        REFERENCES USUARIO (id_usuario) ON DELETE CASCADE,
    CONSTRAINT chk_vendedor_calificacion CHECK (calificacion >= 0 AND calificacion <= 10),
    CONSTRAINT chk_ventas_completadas CHECK (ventas_completadas >= 0)
);

CREATE TABLE COMPRADOR (
    id_comprador INT NOT NULL,
    preferencias_busqueda VARCHAR(255) NULL,
    PRIMARY KEY (id_comprador),
    CONSTRAINT fk_comprador_usuario FOREIGN KEY (id_comprador)
        REFERENCES USUARIO(id_usuario) ON DELETE CASCADE
);

-- 5. CREACIÓN DE ENTIDADES DE CATÁLOGO E ÍTEMS
CREATE TABLE MATERIA (
    id_materia INT NOT NULL AUTO_INCREMENT,
    id_universidad INT NOT NULL,
    nombre_materia VARCHAR(50) NOT NULL,
    creditos INT NOT NULL,
    PRIMARY KEY (id_materia),
    CONSTRAINT fk_materia_univ FOREIGN KEY (id_universidad)
        REFERENCES UNIVERSIDAD (id_universidad) ON DELETE RESTRICT,
    CONSTRAINT chk_creditos CHECK (creditos > 0)
);

CREATE TABLE PUBLICACION (
    id_publicacion INT NOT NULL AUTO_INCREMENT,
    id_vendedor INT NOT NULL,
    id_administrador_moderador INT NULL,
    tipo_item VARCHAR(20) NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT NULL,
    fecha_publicacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_publicacion VARCHAR(20) NOT NULL DEFAULT 'Activa',
    PRIMARY KEY (id_publicacion),
    CONSTRAINT fk_pub_vendedor FOREIGN KEY (id_vendedor)
        REFERENCES VENDEDOR (id_vendedor) ON DELETE RESTRICT,
    CONSTRAINT fk_pub_admin FOREIGN KEY (id_administrador_moderador)
        REFERENCES ADMINISTRADOR(id_administrador) ON DELETE SET NULL,
    CONSTRAINT chk_tipo_item CHECK (tipo_item IN ('Producto', 'Servicio')),
    CONSTRAINT chk_estado_pub CHECK (estado_publicacion IN ('Activa', 'Pausada', 'Bloqueada', 'Finalizada'))
);

CREATE TABLE CATEGORIA (
    id_categoria INT NOT NULL AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (id_categoria)
);

CREATE TABLE PRODUCTO (
    id_producto INT NOT NULL AUTO_INCREMENT,
    id_publicacion INT NOT NULL,
    precio DECIMAL(15,2) NOT NULL,
    calificacion DECIMAL(3,1) NULL,
    estado_fisico VARCHAR(10) NOT NULL,
    stock INT NOT NULL,
    PRIMARY KEY (id_producto),
    CONSTRAINT fk_prod_pub FOREIGN KEY (id_publicacion)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE CASCADE,
    CONSTRAINT chk_prod_precio CHECK (precio > 0),
    CONSTRAINT chk_prod_calif CHECK (calificacion >= 0 AND calificacion <= 10),
    CONSTRAINT chk_estado_fisico CHECK (estado_fisico IN ('NUEVO', 'USADO')),
    CONSTRAINT chk_stock CHECK (stock >= 0)
);

CREATE TABLE CATEGORIA_PRODUCTO (
    id_categoria INT NOT NULL,
    id_producto INT NOT NULL,
    PRIMARY KEY (id_categoria, id_producto),
    CONSTRAINT fk_catprod_categoria FOREIGN KEY (id_categoria)
        REFERENCES CATEGORIA (id_categoria) ON DELETE CASCADE,
    CONSTRAINT fk_catprod_producto FOREIGN KEY (id_producto)
        REFERENCES PRODUCTO (id_producto) ON DELETE CASCADE
);

CREATE TABLE SERVICIO (
    id_servicio INT NOT NULL AUTO_INCREMENT,
    id_publicacion INT NOT NULL,
    modalidad VARCHAR(20) NOT NULL,
    tarifa_por_hora DECIMAL(10,2) NOT NULL,
    disponibilidad_horaria VARCHAR(255) NOT NULL,
    calificacion DECIMAL(3,1) NULL,
    PRIMARY KEY (id_servicio),
    CONSTRAINT fk_serv_pub FOREIGN KEY (id_publicacion)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE CASCADE,
    CONSTRAINT chk_modalidad CHECK (modalidad IN ('Presencial', 'Virtual')),
    CONSTRAINT chk_tarifa CHECK (tarifa_por_hora > 0),
    CONSTRAINT chk_serv_calif CHECK (calificacion >= 0 AND calificacion <= 10)
);

-- 6. CREACIÓN DE ENTIDADES TRANSACCIONALES
CREATE TABLE OFERTA (
    id_oferta INT NOT NULL AUTO_INCREMENT,
    id_comprador INT NOT NULL,
    id_publicacion INT NOT NULL,
    monto_ofertado FLOAT NOT NULL,
    fecha_oferta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_oferta VARCHAR(15) NOT NULL DEFAULT 'Pendiente',
    PRIMARY KEY (id_oferta),
    CONSTRAINT fk_oferta_comp FOREIGN KEY (id_comprador)
        REFERENCES COMPRADOR(id_comprador) ON DELETE RESTRICT,
    CONSTRAINT fk_oferta_pub FOREIGN KEY (id_publicacion)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE RESTRICT,
    CONSTRAINT chk_monto_ofertado CHECK (monto_ofertado > 0),
    CONSTRAINT chk_est_oferta CHECK (estado_oferta IN ('Pendiente', 'Aceptada', 'Rechazada'))
);

CREATE TABLE PRESTAMO (
    id_prestamo INT NOT NULL AUTO_INCREMENT,
    id_comprador INT NOT NULL,
    id_publicacion INT NOT NULL,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_inicio DATETIME NULL,
    fecha_devolucion_pactada DATETIME NOT NULL,
    fecha_devolucion_real DATETIME NULL,
    estado_prestamo VARCHAR(15) NOT NULL DEFAULT 'Solicitado',
    PRIMARY KEY (id_prestamo),
    CONSTRAINT fk_prestamo_comp FOREIGN KEY (id_comprador)
        REFERENCES COMPRADOR(id_comprador) ON DELETE RESTRICT,
    CONSTRAINT fk_prestamo_pub FOREIGN KEY (id_publicacion)
        REFERENCES PUBLICACION(id_publicacion) ON DELETE RESTRICT,
    CONSTRAINT chk_f_inicio CHECK (fecha_inicio > fecha_solicitud),
    CONSTRAINT chk_f_pactada CHECK (fecha_devolucion_pactada >= fecha_inicio),
    CONSTRAINT chk_f_real CHECK (fecha_devolucion_real >= fecha_inicio),
    CONSTRAINT chk_est_prestamo CHECK (estado_prestamo IN ('Solicitado', 'Activo', 'Devuelto', 'Demorado'))
);

CREATE TABLE COMPRA (
    id_compra INT NOT NULL AUTO_INCREMENT,
    id_comprador INT NOT NULL,
    id_publicacion INT NOT NULL,
    monto_total FLOAT NOT NULL,
    fecha_transaccion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_compra),
    CONSTRAINT fk_compra_comp FOREIGN KEY (id_comprador)
        REFERENCES COMPRADOR(id_comprador) ON DELETE RESTRICT,
    CONSTRAINT fk_compra_pub FOREIGN KEY (id_publicacion)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE RESTRICT,
    CONSTRAINT chk_monto_compra CHECK (monto_total > 0)
);

CREATE TABLE SANCION (
    id_sancion INT NOT NULL AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    id_prestamo INT NULL,
    id_administrador INT NOT NULL,
    motivo VARCHAR(255) NOT NULL,
    monto_multa DECIMAL(10,2) NULL,
    fecha_inicio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_fin DATETIME NULL,
    estado_sancion VARCHAR(20) NOT NULL DEFAULT 'Vigente',
    PRIMARY KEY (id_sancion),
    CONSTRAINT fk_sancion_usu FOREIGN KEY (id_usuario)
        REFERENCES USUARIO(id_usuario) ON DELETE RESTRICT,
    CONSTRAINT fk_sancion_prest FOREIGN KEY (id_prestamo)
        REFERENCES PRESTAMO (id_prestamo) ON DELETE RESTRICT,
    CONSTRAINT fk_sancion_admin FOREIGN KEY (id_administrador)
        REFERENCES ADMINISTRADOR(id_administrador) ON DELETE RESTRICT,
    CONSTRAINT chk_multa CHECK (monto_multa >= 0),
    CONSTRAINT chk_f_fin CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT chk_est_sancion CHECK (estado_sancion IN ('Vigente', 'Pagada', 'Expirada'))
);

-- 7. CREACIÓN DE TABLAS ASOCIATIVAS (M:N)
CREATE TABLE MATERIA_PRODUCTO (
    id_materia INT NOT NULL,
    id_producto INT NOT NULL,
    PRIMARY KEY (id_materia, id_producto),
    CONSTRAINT fk_mp_materia FOREIGN KEY (id_materia)
        REFERENCES MATERIA (id_materia) ON DELETE CASCADE,
    CONSTRAINT fk_mp_producto FOREIGN KEY (id_producto)
        REFERENCES PRODUCTO (id_producto) ON DELETE CASCADE
);

CREATE TABLE TRUEQUE (
    id_trueque INT NOT NULL AUTO_INCREMENT,
    id_comprador_iniciador INT NOT NULL,
    id_publicacion_deseada INT NOT NULL,
    id_publicacion_ofrecida INT NOT NULL,
    fecha_propuesta DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_trueque VARCHAR(15) NOT NULL DEFAULT 'Pendiente',
    PRIMARY KEY (id_trueque),
    CONSTRAINT fk_trueque_comp FOREIGN KEY (id_comprador_iniciador)
        REFERENCES COMPRADOR(id_comprador) ON DELETE RESTRICT,
    CONSTRAINT fk_trueque_deseada FOREIGN KEY (id_publicacion_deseada)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE RESTRICT,
    CONSTRAINT fk_trueque_ofrecida FOREIGN KEY (id_publicacion_ofrecida)
        REFERENCES PUBLICACION (id_publicacion) ON DELETE RESTRICT,
    CONSTRAINT chk_pub_distintas CHECK (id_publicacion_ofrecida != id_publicacion_deseada),
    CONSTRAINT chk_est_trueque CHECK (estado_trueque IN ('Pendiente', 'Aceptado', 'Rechazado'))
);

-- 8. CREACIÓN DE TABLAS DE LOG Y AUDITORÍA
CREATE TABLE AUDITORIA_TRANSACCIONES (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_compra INT NULL,
    id_trueque INT NULL,
    id_prestamo INT NULL,
    id_administrador INT NULL,
    tipo_evento VARCHAR(50) NOT NULL,
    detalle_evento TEXT NOT NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    usuario_auditor VARCHAR(100) NOT NULL,
    PRIMARY KEY (id_auditoria),
    CONSTRAINT fk_audit_compra FOREIGN KEY (id_compra)
        REFERENCES COMPRA (id_compra) ON DELETE SET NULL,
    CONSTRAINT fk_audit_trueque FOREIGN KEY (id_trueque)
        REFERENCES TRUEQUE(id_trueque) ON DELETE SET NULL,
    CONSTRAINT fk_audit_prest FOREIGN KEY (id_prestamo)
        REFERENCES PRESTAMO (id_prestamo) ON DELETE SET NULL,
    CONSTRAINT fk_audit_admin FOREIGN KEY (id_administrador)
        REFERENCES ADMINISTRADOR(id_administrador) ON DELETE SET NULL
);