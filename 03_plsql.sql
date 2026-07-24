USE UnTrade;

DROP PROCEDURE IF EXISTS aplicar_sancion;
DROP PROCEDURE IF EXISTS calificar_vendedor;
DROP FUNCTION IF EXISTS promedio;

DELIMITER $$

CREATE PROCEDURE aplicar_sancion(
    IN p_id_prestamo INT,
    IN p_id_administrador INT,
    IN p_motivo VARCHAR(255),
    IN p_monto_incremento DECIMAL(10,2)
)
BEGIN
    DECLARE v_existe_prestamo INT DEFAULT 0;
    DECLARE v_existe_administrador INT DEFAULT 0;
    DECLARE v_id_usuario INT;
    DECLARE v_fecha_pago_oportuno DATETIME;
    DECLARE v_fecha_devolucion_real DATETIME;
    DECLARE v_nuevo_monto DECIMAL(10,2);

    START TRANSACTION;

    SELECT COUNT(*)
    INTO v_existe_administrador
    FROM ADMINISTRADOR
    WHERE id_administrador = p_id_administrador;

    IF v_existe_administrador = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El administrador no existe.';
    END IF;

    SELECT COUNT(*)
    INTO v_existe_prestamo
    FROM PRESTAMO
    WHERE id_prestamo = p_id_prestamo;

    IF v_existe_prestamo = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El préstamo no existe.';
    END IF;

    SELECT
        id_comprador,
        fecha_devolucion_pactada,
        fecha_devolucion_real
    INTO
        v_id_usuario,
        v_fecha_pago_oportuno,
        v_fecha_devolucion_real
    FROM PRESTAMO
    WHERE id_prestamo = p_id_prestamo;

    IF NOW() <= v_fecha_pago_oportuno THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'La sanción no es válida: todavía no ha vencido la fecha de devolución pactada.';
    END IF;

    SET v_nuevo_monto = p_monto_incremento;

    INSERT INTO SANCION (
        id_usuario,
        id_prestamo,
        id_administrador,
        motivo,
        monto_multa,
        fecha_inicio,
        fecha_fin,
        estado_sancion
    )
    VALUES (
        v_id_usuario,
        p_id_prestamo,
        p_id_administrador,
        p_motivo,
        v_nuevo_monto,
        NOW(),
        NULL,
        'Vigente'
    );

    UPDATE PRESTAMO
    SET estado_prestamo = 'Demorado'
    WHERE id_prestamo = p_id_prestamo;

    COMMIT;
END$$

CREATE FUNCTION promedio(
    p_total DECIMAL(20,2),
    p_cantidad BIGINT
)
RETURNS DECIMAL(2,1)
BEGIN
    IF p_cantidad = 0 THEN
        RETURN 0.0;
    END IF;

    RETURN ROUND(p_total / p_cantidad, 1);
END$$
    
CREATE PROCEDURE calificar_vendedor(
    IN p_id_vendedor INT
)

BEGIN
    DECLARE v_existe_vendedor INT DEFAULT 0;
    DECLARE v_suma DECIMAL(20,2);
    DECLARE v_cantidad BIGINT;
    DECLARE v_promedio DECIMAL(2,1);

    SELECT COUNT(*)
    INTO v_existe_vendedor
    FROM VENDEDOR
    WHERE id_vendedor = p_id_vendedor;

    IF v_existe_vendedor = 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'El vendedor indicado no existe';
    END IF;
    
    SELECT
        COALESCE(SUM(publicacion.calificacion), 0.0),
        COUNT(publicacion.calificacion)
    INTO
        v_suma,
        v_cantidad
    FROM PUBLICACION AS publicacion
    INNER JOIN PRODUCTO AS producto
        ON producto.id_publicacion = publicacion.id_publicacion
    WHERE publicacion.id_vendedor = p_id_vendedor;

    SET v_promedio = promedio(v_suma, v_cantidad);

    UPDATE VENDEDOR
    SET calificacion = v_promedio
    WHERE id_vendedor = p_id_vendedor;
END$$

-- ======================
-- Triggers
-- ================

-- 1. Triggers que generan automaticamente la auditoria para las transacciones
CREATE TRIGGER trg_auditar_nueva_compra
AFTER INSERT ON COMPRA
FOR EACH ROW
BEGIN
    INSERT INTO AUDITORIA_TRANSACCIONES (id_compra, tipo_evento, detalle_evento, usuario_auditor) VALUES 
        (NEW.id_compra, 'NUEVA_COMPRA', CONCAT('El comprador ID ', NEW.id_comprador, ' realizó una compra en la publicación ID ', NEW.id_publicacion, ' por un monto de $', NEW.monto_total, ' con el método de pago: ', NEW.metodo_pago), CURRENT_USER());
END //

CREATE TRIGGER trg_auditar_nuevo_trueque
AFTER INSERT ON TRUEQUE
FOR EACH ROW
BEGIN
    INSERT INTO AUDITORIA_TRANSACCIONES (id_trueque, tipo_evento, detalle_evento, usuario_auditor) VALUES 
        (NEW.id_trueque, 'NUEVO_TRUEQUE', CONCAT('Trueque iniciado por comprador ID ', NEW.id_comprador_iniciador, ' ofreciendo publicación ', NEW.id_publicacion_ofrecida, ' por la publicación ', NEW.id_publicacion_deseada), CURRENT_USER());
END //

CREATE TRIGGER trg_auditar_nuevo_prestamo
AFTER INSERT ON PRESTAMO
FOR EACH ROW
BEGIN
    INSERT INTO AUDITORIA_TRANSACCIONES (id_prestamo, tipo_evento, detalle_evento, usuario_auditor) VALUES 
        (NEW.id_prestamo, 'NUEVO_PRESTAMO', CONCAT('El comprador ID ', NEW.id_comprador, ' solicitó en préstamo la publicación ID ', NEW.id_publicacion, '. Fecha pactada de devolución: ', DATE_FORMAT(NEW.fecha_devolucion_pactada, '%Y-%m-%d %H:%i')), CURRENT_USER());
END //

-- 2. Trigger para validar las disponibilidad de una compra, mirando que tanto comprador como publicacion existen y verificando si hay stock para el caso de productos y disponibilidad horaria en el caso de servicio

CREATE TRIGGER trg_validar_disponibilidad_compra
BEFORE INSERT ON COMPRA
FOR EACH ROW
BEGIN

    DECLARE v_existe_comprador INT DEFAULT 0;
    DECLARE v_existe_publicacion INT DEFAULT 0;
    DECLARE v_tipo_item VARCHAR(20);
    DECLARE v_stock_producto INT;
    DECLARE v_disp_servicio VARCHAR(255);

    SELECT COUNT(*) INTO v_existe_comprador 
    FROM COMPRADOR WHERE id_comprador = NEW.id_comprador;
    
    IF v_existe_comprador = 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Excepción: El comprador indicado no existe en el sistema.';
    END IF;

    SELECT COUNT(*) INTO v_existe_publicacion 
    FROM PUBLICACION WHERE id_publicacion = NEW.id_publicacion;
    
    IF v_existe_publicacion = 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'Excepción: La publicación indicada no existe en el sistema.';
    END IF;

    SELECT tipo_item INTO v_tipo_item 
    FROM PUBLICACION WHERE id_publicacion = NEW.id_publicacion;

    IF v_tipo_item = 'Producto' THEN
        SELECT stock INTO v_stock_producto 
        FROM PRODUCTO WHERE id_publicacion = NEW.id_publicacion;

        IF v_stock_producto IS NULL OR v_stock_producto <= 0 THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Excepción: El producto no cuenta con stock disponible (> 0) o no existe el detalle del producto.';
        END IF;
        
    ELSEIF v_tipo_item = 'Servicio' THEN
        SELECT disponibilidad_horaria INTO v_disp_servicio 
        FROM SERVICIO WHERE id_publicacion = NEW.id_publicacion;
        
        IF v_disp_servicio IS NULL OR TRIM(v_disp_servicio) = '' THEN
            SIGNAL SQLSTATE '45000' 
            SET MESSAGE_TEXT = 'Excepción: El servicio tiene una disponibilidad horaria vacía o no existe el detalle del servicio.';
        END IF;
        
    END IF;

END //
    
DELIMITER ;
