-- 02_dml_master.sql
-- Inserciones de tablas maestras y datos base (Mínimo 10 filas por catálogo)

INSERT INTO UNIVERSIDAD (nombre, pais, dominio_correo) VALUES
('Universidad Nacional de Colombia', 'Colombia', 'unal.edu.co'),
('Universidad de los Andes', 'Colombia', 'uniandes.edu.co'),
('Universidad Javeriana', 'Colombia', 'javeriana.edu.co'),
('Universidad de Antioquia', 'Colombia', 'udea.edu.co'),
('Universidad del Valle', 'Colombia', 'univalle.edu.co'),
('Universidad Industrial de Santander', 'Colombia', 'uis.edu.co'),
('Universidad del Rosario', 'Colombia', 'urosario.edu.co'),
('Universidad de la Sabana', 'Colombia', 'unisabana.edu.co'),
('Universidad EAFIT', 'Colombia', 'eafit.edu.co'),
('Universidad del Norte', 'Colombia', 'uninorte.edu.co');

INSERT INTO MATERIA (id_universidad, nombre_materia, creditos) VALUES
(1, 'Bases de Datos I', 3), (1, 'Programación Orientada a Objetos', 4),
(1, 'Cálculo Diferencial', 4), (1, 'Física Mecánica', 4),
(1, 'Estructuras de Datos', 3), (2, 'Arquitectura de Software', 3),
(2, 'Ingeniería de Requisitos', 3), (3, 'Redes de Computadores', 4),
(4, 'Sistemas Operativos', 4), (5, 'Inteligencia Artificial', 3);