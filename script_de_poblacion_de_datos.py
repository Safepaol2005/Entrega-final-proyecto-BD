import random
from faker import Faker
from datetime import timedelta

# Inicializar Faker con localización colombiana
fake = Faker('es_CO')

universidades_data = [
    ('Universidad Nacional de Colombia', 'Colombia', '@unal.edu.co'),
    ('Universidad de los Andes', 'Colombia', '@uniandes.edu.co'),
    ('Universidad Javeriana', 'Colombia', '@javeriana.edu.co'),
    ('Universidad de Antioquia', 'Colombia', '@udea.edu.co'),
    ('Universidad del Valle', 'Colombia', '@univalle.edu.co'),
    ('Universidad Industrial de Santander', 'Colombia', '@uis.edu.co'),
    ('Universidad del Rosario', 'Colombia', '@urosario.edu.co'),
    ('Universidad de la Sabana', 'Colombia', '@unisabana.edu.co'),
    ('Universidad EAFIT', 'Colombia', '@eafit.edu.co'),
    ('Universidad del Norte', 'Colombia', '@uninorte.edu.co')
]

materias_data = [
    (1, 'Bases de Datos I', 3), 
    (1, 'Programación Orientada a Objetos', 4),
    (1, 'Cálculo Diferencial', 4), 
    (1, 'Física Mecánica', 4),
    (1, 'Estructuras de Datos', 3), 
    (2, 'Arquitectura de Software', 3),
    (2, 'Ingeniería de Requisitos', 3), 
    (3, 'Redes de Computadores', 4),
    (4, 'Sistemas Operativos', 4), 
    (5, 'Inteligencia Artificial', 3)
]

categorias_data = [
    'Libros y Textos', 'Calculadoras y Cómputo', 'Material de Laboratorio',
    'Electrónica y Robótica', 'Arquitectura y Diseño', 'Medicina y Salud',
    'Papelería Técnica', 'Software y Licencias', 'Instrumentos de Medición',
    'Herramientas de Taller'
]

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def format_val(val):
    """Formatea valores de Python para sintaxis SQL."""
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    # Escapar comillas simples en cadenas de texto
    return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"

def write_bulk_insert(file, table, columns, values_list):
    """Genera y escribe una sentencia INSERT multifila en el archivo."""
    if not values_list:
        return 
    
    cols_str = ", ".join(columns)
    file.write(f"INSERT INTO {table} ({cols_str}) VALUES\n")
    
    rows = []
    for vals in values_list:
        vals_str = ", ".join(format_val(v) for v in vals)
        rows.append(f"({vals_str})")
    
    file.write(",\n".join(rows) + ";\n\n")


# ---------------------------------------------------------
# GENERACIÓN DE DATOS (EN MEMORIA)
# ---------------------------------------------------------
print("Generando datos en memoria...")

# Universidades, Materias, Categorias
univ_vals = []
universities_ref = [] 
for i, (nombre, pais, dominio) in enumerate(universidades_data, start=1):
    univ_vals.append((nombre, pais, dominio))
    universities_ref.append((i, dominio))

materia_vals = materias_data.copy()
materia_ids = list(range(1, len(materias_data) + 1))

categoria_vals = [(cat,) for cat in categorias_data]
categoria_ids = list(range(1, len(categorias_data) + 1))

# Usuarios, Admin, Vendedor, Comprador
usuario_vals = []
user_ids = []
for i in range(1, 301):
    univ_id, domain = random.choice(universities_ref)
    base_name = fake.unique.user_name()[:25]
    email = f"{base_name}{random.randint(100,999)}{domain}"
    usuario_vals.append((univ_id, fake.name()[:50], email, fake.sha256()))
    user_ids.append(i)

admin_vals = []
areas_soporte_realistas = [
    'Soporte Técnico de Plataforma', 'Moderación de Contenido', 'Seguridad y Cuentas', 
    'Gestión de Préstamos y Multas', 'Atención al Estudiante', 'Verificación de Identidad',
    'Resolución de Disputas', 'Soporte de Pagos', 'Auditoría de Transacciones', 'Administración General'
]
admin_ids = user_ids[:10]
for i in range(10):
    admin_vals.append((admin_ids[i], random.choice(['SuperAdmin', 'Moderador', 'Soporte']), areas_soporte_realistas[i]))

vendedor_vals = []
vendedor_ids = random.sample(user_ids, 150)
for u_id in vendedor_ids:
    calificacion = random.choice([0.0, 10.0, round(random.uniform(3.5, 5.0), 1)])
    ventas = random.randint(0, 50)
    vendedor_vals.append((u_id, calificacion, ventas))

comprador_vals = []
preferencias_academicas = [
    'Libros de cálculo y matemáticas', 'Calculadoras científicas gráficas', 'Implementos de laboratorio de química',
    'Materiales de arquitectura y dibujo', 'Tarjetas de desarrollo Arduino y sensores', 'Apuntes y cuadernos de ingeniería',
    'Libros de física mecánica', 'Kits de electrónica básica', 'Libros de programación y bases de datos', 'Estetoscopios y material médico'
]
comprador_ids = random.sample(user_ids, 250)
for u_id in comprador_ids:
    preferencia = random.choice(preferencias_academicas)
    comprador_vals.append((u_id, preferencia[:255]))


# Publicaciones, Productos y Servicios
banco_productos_academicos = [
    ("Libro de Cálculo de Larson 11Ed", "Libro en excelente estado, pasta original.", 95000),
    ("Calculadora Científica Casio", "Calculadora con funciones matriciales, poco uso.", 75000),
    ("Kit de Laboratorio de Química", "Set completo de cristalería resistente al calor.", 60000),
    ("Multímetro Digital UT33C+", "Medición de temperatura y continuidad.", 45000),
    ("Escalímetro profesional", "Implementos de dibujo técnico seminuevos.", 50000),
    ("Tarjeta Arduino Uno R3", "Kit de desarrollo para sistemas embebidos.", 90000),
    ("Libro de Bases de Datos", "Edición en español, clave para ingeniería.", 110000),
    ("Estetoscopio Littmann Classic III", "Uso exclusivo de área de salud.", 350000),
    ("Prototyping Breadboard", "Placa de pruebas protoboard con juego de cables.", 25000),
    ("Física Universitaria Sears", "Conjunto de ambos volúmenes empastados.", 140000)
]

publicacion_vals = []
producto_vals = []
servicio_vals = []
cat_prod_vals = []
publicacion_ids = []
producto_ids = []

pub_id_counter = 0
prod_id_counter = 0
cat_prod_set = set()

for _ in range(1000):
    v_id = random.choice(vendedor_ids)
    a_id = random.choice(admin_ids) if random.random() > 0.2 else None
    tipo = random.choice(['Producto', 'Servicio'])
    estado = random.choice(['Activa', 'Pausada', 'Bloqueada', 'Finalizada'])
    
    pub_id_counter += 1
    publicacion_ids.append(pub_id_counter)
    
    if tipo == 'Producto':
        prod_base = random.choice(banco_productos_academicos)
        titulo = prod_base[0] + f" (Ref: {random.randint(10,99)})"
        descripcion = prod_base[1] if random.random() > 0.3 else None
        precio = float(prod_base[2] + random.randint(-5000, 10000))
        
        publicacion_vals.append((v_id, a_id, tipo, titulo, descripcion, estado))
        
        prod_id_counter += 1
        producto_ids.append(prod_id_counter)
        stock = random.choice([0, random.randint(1, 10)])
        producto_vals.append((pub_id_counter, precio, round(random.uniform(3.0, 10.0), 1), random.choice(['NUEVO', 'USADO']), stock))
        
        categorias_asignadas = random.sample(categoria_ids, random.randint(1, 2))
        for cat_id in categorias_asignadas:
            if (cat_id, prod_id_counter) not in cat_prod_set:
                cat_prod_vals.append((cat_id, prod_id_counter))
                cat_prod_set.add((cat_id, prod_id_counter))

    else:
        servicios_academicos = [
            ("Tutoría de Cálculo Diferencial", "Clases orientadas a parciales.", 35000),
            ("Asesoría en Programación", "Apoyo en código C++ y Java.", 45000),
            ("Clases de Física Mecánica", "Diagramas de cuerpo libre.", 40000),
            ("Corrección de Artículos", "Revisión de estilo en inglés.", 50000)
        ]
        serv_base = random.choice(servicios_academicos)
        descripcion = serv_base[1] if random.random() > 0.3 else None
        
        publicacion_vals.append((v_id, a_id, tipo, serv_base[0], descripcion, estado))
        servicio_vals.append((pub_id_counter, random.choice(['Presencial', 'Virtual']), float(serv_base[2]), "L-V 2pm a 6pm", round(random.uniform(4.0, 10.0), 1)))

# Auditoría
auditoria_vals = []
usuario_auditor_script = "root@localhost"

# Materia-Producto
mat_prod_vals = []
mat_prod_set = set()
for _ in range(60):
    m_id = random.choice(materia_ids)
    p_id = random.choice(producto_ids)
    if (m_id, p_id) not in mat_prod_set:
        mat_prod_vals.append((m_id, p_id))
        mat_prod_set.add((m_id, p_id))

# Compras y Simulación del Trigger de Compras
compra_vals = []
for i in range(1050):
    compra_id = i + 1
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    monto = round(random.uniform(20000.0, 350000.0), 2)
    metodo_pago = random.choice(['Transferencia Bancaria', 'Nequi', 'Daviplata', 'Efectivo'])
    
    compra_vals.append((c_id, pub_id, monto, metodo_pago))
    
    # Registro de Auditoría (Simulando trg_auditar_nueva_compra)
    detalle_compra = f"El comprador ID {c_id} realizó una compra en la publicación ID {pub_id} por un monto de ${monto} con el método de pago: {metodo_pago}"
    auditoria_vals.append((compra_id, None, None, 'NUEVA_COMPRA', detalle_compra, usuario_auditor_script))

# Ofertas
oferta_vals = []
for _ in range(200):
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    monto_ofertado = round(random.uniform(15000.0, 120000.0), 2)
    estado_oferta = random.choice(['Pendiente', 'Aceptada', 'Rechazada'])
    oferta_vals.append((c_id, pub_id, monto_ofertado, estado_oferta))

# Préstamos y Simulación del Trigger de Préstamos
prestamo_vals = []
prestamos_demorados = []
prestamo_id_counter = 0

for _ in range(200):
    prestamo_id_counter += 1
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    f_solicitud = fake.date_time_between(start_date='-6m', end_date='-1m')
    f_inicio = f_solicitud + timedelta(days=1)
    f_pactada = f_inicio + timedelta(days=random.randint(5, 15))
    
    estado_prestamo = random.choice(['Solicitado', 'Activo', 'Devuelto', 'Demorado'])
    f_real = None
    if estado_prestamo == 'Devuelto':
        f_real = f_pactada - timedelta(days=random.randint(0, 2))
        
    if estado_prestamo == 'Demorado':
        prestamos_demorados.append((prestamo_id_counter, c_id))
        
    prestamo_vals.append((c_id, pub_id, f_solicitud.strftime('%Y-%m-%d %H:%M:%S'), f_inicio.strftime('%Y-%m-%d %H:%M:%S'), 
                          f_pactada.strftime('%Y-%m-%d %H:%M:%S'), f_real.strftime('%Y-%m-%d %H:%M:%S') if f_real else None, estado_prestamo))

    # Registro de Auditoría (Simulando trg_auditar_nuevo_prestamo)
    detalle_prestamo = f"El comprador ID {c_id} solicitó en préstamo la publicación ID {pub_id}. Fecha pactada de devolución: {f_pactada.strftime('%Y-%m-%d %H:%M')}"
    auditoria_vals.append((None, None, prestamo_id_counter, 'NUEVO_PRESTAMO', detalle_prestamo, usuario_auditor_script))

# Sanciones
sancion_vals = []
for p_id, c_id in prestamos_demorados:
    admin_id = random.choice(admin_ids)
    motivo_sancion = "Incumplimiento en la devolucion del material."
    monto_multa = round(random.uniform(15000.0, 50000.0), 2)
    f_inicio_sancion = fake.date_time_between(start_date='-20d', end_date='now')
    f_fin_sancion = f_inicio_sancion + timedelta(days=30)
    
    sancion_vals.append((c_id, p_id, admin_id, motivo_sancion, monto_multa, f_inicio_sancion.strftime('%Y-%m-%d %H:%M:%S'), f_fin_sancion.strftime('%Y-%m-%d %H:%M:%S'), 'Vigente'))

# Trueques y Simulación del Trigger de Trueques
trueque_vals = []
for i in range(80):
    trueque_id = i + 1
    c_id = random.choice(comprador_ids)
    pub_ofrecida, pub_deseada = random.sample(publicacion_ids, 2)
    estado_trueque = random.choice(['Pendiente', 'Aceptado', 'Rechazado'])
    trueque_vals.append((c_id, pub_deseada, pub_ofrecida, estado_trueque))

    # Registro de Auditoría (Simulando trg_auditar_nuevo_trueque)
    detalle_trueque = f"Trueque iniciado por comprador ID {c_id} ofreciendo publicación {pub_ofrecida} por la publicación {pub_deseada}"
    auditoria_vals.append((None, trueque_id, None, 'NUEVO_TRUEQUE', detalle_trueque, usuario_auditor_script))


# ---------------------------------------------------------
# GENERACIÓN DEL SCRIPT SQL (ESCRITURA A ARCHIVO)
# ---------------------------------------------------------
print("Escribiendo datos en 02_dml.sql...")

with open('02_dml.sql', 'w', encoding='utf-8') as sql_file:
    sql_file.write("-- ==========================================\n")
    sql_file.write("-- Script de Población de Datos (DML)\n")
    sql_file.write("-- Generado automáticamente (Inserts Multifila y simulación de triggers)\n")
    sql_file.write("-- ==========================================\n\n")

    sql_file.write("USE UnTrade;\n\n")

    sql_file.write("-- 1. Maestros (Universidades, Materias, Categorías)\n")
    write_bulk_insert(sql_file, "UNIVERSIDAD", ["nombre", "pais", "dominio_correo"], univ_vals)
    write_bulk_insert(sql_file, "MATERIA", ["id_universidad", "nombre_materia", "creditos"], materia_vals)
    write_bulk_insert(sql_file, "CATEGORIA", ["nombre"], categoria_vals)

    sql_file.write("-- 2. Usuarios, Administradores, Vendedores, Compradores\n")
    write_bulk_insert(sql_file, "USUARIO", ["id_universidad", "nombre_completo", "correo_estudiantil", "password_hash"], usuario_vals)
    write_bulk_insert(sql_file, "ADMINISTRADOR", ["id_administrador", "nivel_permiso", "area_soporte"], admin_vals)
    write_bulk_insert(sql_file, "VENDEDOR", ["id_vendedor", "calificacion", "ventas_completadas"], vendedor_vals)
    write_bulk_insert(sql_file, "COMPRADOR", ["id_comprador", "preferencias_busqueda"], comprador_vals)

    sql_file.write("-- 3. Publicaciones, Productos, Servicios y Categorías Asociadas\n")
    write_bulk_insert(sql_file, "PUBLICACION", ["id_vendedor", "id_administrador_moderador", "tipo_item", "titulo", "descripcion", "estado_publicacion"], publicacion_vals)
    write_bulk_insert(sql_file, "PRODUCTO", ["id_publicacion", "precio", "calificacion", "estado_fisico", "stock"], producto_vals)
    write_bulk_insert(sql_file, "CATEGORIA_PRODUCTO", ["id_categoria", "id_producto"], cat_prod_vals)
    write_bulk_insert(sql_file, "SERVICIO", ["id_publicacion", "modalidad", "tarifa_por_hora", "disponibilidad_horaria", "calificacion"], servicio_vals)

    sql_file.write("-- 4. Transacciones y Operaciones (Compras, Ofertas, Trueques, Préstamos)\n")
    write_bulk_insert(sql_file, "MATERIA_PRODUCTO", ["id_materia", "id_producto"], mat_prod_vals)
    write_bulk_insert(sql_file, "COMPRA", ["id_comprador", "id_publicacion", "monto_total", "metodo_pago"], compra_vals)
    write_bulk_insert(sql_file, "OFERTA", ["id_comprador", "id_publicacion", "monto_ofertado", "estado_oferta"], oferta_vals)
    write_bulk_insert(sql_file, "PRESTAMO", ["id_comprador", "id_publicacion", "fecha_solicitud", "fecha_inicio", "fecha_devolucion_pactada", "fecha_devolucion_real", "estado_prestamo"], prestamo_vals)
    write_bulk_insert(sql_file, "SANCION", ["id_usuario", "id_prestamo", "id_administrador", "motivo", "monto_multa", "fecha_inicio", "fecha_fin", "estado_sancion"], sancion_vals)
    write_bulk_insert(sql_file, "TRUEQUE", ["id_comprador_iniciador", "id_publicacion_deseada", "id_publicacion_ofrecida", "estado_trueque"], trueque_vals)

    sql_file.write("-- 5. Tablas de Log y Auditoría (Simulación de Triggers)\n")
    write_bulk_insert(sql_file, "AUDITORIA_TRANSACCIONES", ["id_compra", "id_trueque", "id_prestamo", "tipo_evento", "detalle_evento", "usuario_auditor"], auditoria_vals)

print("Script finalizado exitosamente. Auditoría generada correctamente.")