# 02_dml_generator.py
import mysql.connector
from faker import Faker
import random
from datetime import timedelta

# Inicializar Faker con localización colombiana
fake = Faker('es_CO')

# Conexión a la base de datos
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YBMfmx45*", 
    database="UnTrade"
)
cursor = db.cursor()

def get_db_ids(table_name, id_column):
    cursor.execute(f"SELECT {id_column} FROM {table_name}")
    return [row[0] for row in cursor.fetchall()]

# Obtener universidades base
cursor.execute("SELECT id_universidad, dominio_correo FROM UNIVERSIDAD")
universities = cursor.fetchall()

if not universities:
    raise ValueError("La tabla UNIVERSIDAD está vacía. Ejecute primero el script de datos maestros.")

print("Generando usuarios y roles adaptados al contexto académico...")

# 1. Generar 300 Usuarios con correos institucionales reales
for _ in range(300):
    univ_id, domain = random.choice(universities)
    base_name = fake.unique.user_name()[:25]
    email = f"{base_name}{random.randint(100,999)}{domain}" 
    
    cursor.execute(
        "INSERT INTO USUARIO (id_universidad, nombre_completo, correo_estudiantil, password_hash) VALUES (%s, %s, %s, %s)",
        (univ_id, fake.name()[:50], email, fake.sha256())
    )
db.commit()
user_ids = get_db_ids("USUARIO", "id_usuario")

# 2. Asignar Subclases (Exactamente 10 Administradores, 150 Vendedores, 250 Compradores)
# 3. Administradores con áreas de soporte contextuales y realistas
areas_soporte_realistas = [
    'Soporte Técnico de Plataforma', 'Moderación de Contenido', 'Seguridad y Cuentas', 
    'Gestión de Préstamos y Multas', 'Atención al Estudiante', 'Verificación de Identidad',
    'Resolución de Disputas', 'Soporte de Pagos', 'Auditoría de Transacciones', 'Administración General'
]
for i in range(10):
    u_id = user_ids[i]
    area_soporte = areas_soporte_realistas[i]
    cursor.execute(
        "INSERT INTO ADMINISTRADOR (id_administrador, nivel_permiso, area_soporte) VALUES (%s, %s, %s)",
        (u_id, random.choice(['SuperAdmin', 'Moderador', 'Soporte']), area_soporte)
    )

# Vendedores
for u_id in random.sample(user_ids, 150):
    calificacion = random.choice([0.0, 10.0, round(random.uniform(3.5, 5.0), 1)])
    ventas = random.randint(0, 50)
    cursor.execute(
        "INSERT INTO VENDEDOR (id_vendedor, calificacion, ventas_completadas) VALUES (%s, %s, %s)",
        (u_id, calificacion, ventas)
    )

# 2. Compradores con preferencias de búsqueda académicas reales
preferencias_academicas = [
    'Libros de cálculo y matemáticas', 'Calculadoras científicas gráficas', 'Implementos de laboratorio de química',
    'Materiales de arquitectura y dibujo', 'Tarjetas de desarrollo Arduino y sensores', 'Apuntes y cuadernos de ingeniería',
    'Libros de física mecánica', 'Kits de electrónica básica', 'Libros de programación y bases de datos', 'Estetoscopios y material médico'
]
for u_id in random.sample(user_ids, 250):
    preferencia = random.choice(preferencias_academicas)
    cursor.execute(
        "INSERT INTO COMPRADOR (id_comprador, preferencias_busqueda) VALUES (%s, %s)",
        (u_id, preferencia[:255])
    )
db.commit()

admin_ids = get_db_ids("ADMINISTRADOR", "id_administrador")
vendedor_ids = get_db_ids("VENDEDOR", "id_vendedor")
comprador_ids = get_db_ids("COMPRADOR", "id_comprador")
materia_ids = get_db_ids("MATERIA", "id_materia")

print("Generando publicaciones académicas, productos y servicios...")

# 1. & 5. Publicaciones y Productos con títulos, descripciones y categorías realistas del ámbito universitario
banco_productos_academicos = [
    ("Libro de Cálculo de Larson 11Ed", "Libro en excelente estado, pasta original, ideal para estudiantes de ingeniería primer semestre.", "Libros y Textos", 95000),
    ("Calculadora Científica Casio fx-991ES Plus", "Calculadora científica con funciones matriciales y vectoriales, poco uso, se entrega con estuche.", "Calculadoras", 75000),
    ("Kit de Laboratorio de Química (Bagueta, Vasos de Precipitado)", "Set completo de cristalería resistente al calor para prácticas de química orgánica.", "Laboratorio", 60000),
    ("Multímetro Digital UT33C+", "Multímetro con medición de temperatura y continuidad, perfecto para laboratorios de circuitos.", "Electrónica", 45000),
    ("Escalímetro profesional y Tabla paralela A3", "Implementos de dibujo técnico para diseño y arquitectura, seminuevos.", "Arquitectura y Diseño", 50000),
    ("Tarjeta Arduino Uno R3 + Sensor Kit", "Kit de desarrollo para proyectos de sistemas embebidos e internet de las cosas.", "Electrónica", 90000),
    ("Libro de Bases de Datos Elmasri Navathe", "Edición en español, clave para materias de ingeniería de sistemas y gestión de datos.", "Libros y Textos", 110000),
    ("Estetoscopio Littmann Classic III", "Color negro, original, con membrana de repuesto, uso exclusivo de área de salud.", "Medicina y Salud", 350000),
    ("Prototyping Breadboard 830 puntos y cables jumper", "Placa de pruebas protoboard con juego de cables macho-macho para circuitos.", "Electrónica", 25000),
    ("Física Universitaria Sears Zemansky Vol 1 y 2", "Conjunto de ambos volúmenes empastados, ligeras notas a lápiz en capítulos iniciales.", "Libros y Textos", 140000)
]

for _ in range(500):
    v_id = random.choice(vendedor_ids)
    a_id = random.choice(admin_ids) if random.random() > 0.2 else None
    tipo = random.choice(['Producto', 'Servicio'])
    estado = random.choice(['Activa', 'Pausada', 'Bloqueada', 'Finalizada'])
    
    if tipo == 'Producto':
        prod_base = random.choice(banco_productos_academicos)
        titulo = prod_base[0] + f" (Ref: {random.randint(10,99)})"
        descripcion = prod_base[1]
        
        # FIX: Enforce strict slicing to match VARCHAR(20) DDL constraint
        categoria = prod_base[2][:20] 
        
        precio = float(prod_base[3] + random.randint(-5000, 10000))
        
        cursor.execute(
            "INSERT INTO PUBLICACION (id_vendedor, id_administrador_moderador, tipo_item, titulo, descripcion, estado_publicacion) VALUES (%s, %s, %s, %s, %s, %s)",
            (v_id, a_id, tipo, titulo, descripcion, estado)
        )
        pub_id = cursor.lastrowid
        
        stock = random.choice([0, random.randint(1, 10)])
        cursor.execute(
            "INSERT INTO PRODUCTO (id_publicacion, precio, categoria, calificacion, estado_fisico, stock) VALUES (%s, %s, %s, %s, %s, %s)",
            (pub_id, precio, categoria, round(random.uniform(3.0, 10.0), 1), random.choice(['NUEVO', 'USADO']), stock)
        )
    else:
        servicios_academicos = [
            ("Tutoría de Cálculo Diferencial e Integral", "Clases particulares orientadas a la preparación de parciales y solución de talleres.", "Servicios Académicos", 35000),
            ("Asesoría en Estructuras de Datos y Programación", "Apoyo en código C++, Java y depuración de algoritmos complejos.", "Servicios Académicos", 45000),
            ("Clases de Física Mecánica y Estática", "Explicación de diagramas de cuerpo libre y leyes de Newton paso a paso.", "Servicios Académicos", 40000),
            ("Traducción y Corrección de Artículos Científicos", "Revisión de estilo y formato en inglés técnico para proyectos de grado.", "Servicios Académicos", 50000)
        ]
        serv_base = random.choice(servicios_academicos)
        cursor.execute(
            "INSERT INTO PUBLICACION (id_vendedor, id_administrador_moderador, tipo_item, titulo, descripcion, estado_publicacion) VALUES (%s, %s, %s, %s, %s, %s)",
            (v_id, a_id, tipo, serv_base[0], serv_base[1], estado)
        )
        pub_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO SERVICIO (id_publicacion, modalidad, tarifa_por_hora, disponibilidad_horaria, calificacion) VALUES (%s, %s, %s, %s, %s)",
            (pub_id, random.choice(['Presencial', 'Virtual']), float(serv_base[3]), "Lunes a Viernes de 2pm a 6pm", round(random.uniform(4.0, 10.0), 1))
        )
db.commit()

publicacion_ids = get_db_ids("PUBLICACION", "id_publicacion")
producto_ids = get_db_ids("PRODUCTO", "id_producto")

print("Generando asociaciones, transacciones, ofertas y sanciones...")

# Asociaciones Materia-Producto
for _ in range(60):
    m_id = random.choice(materia_ids)
    p_id = random.choice(producto_ids)
    try:
        cursor.execute("INSERT INTO MATERIA_PRODUCTO (id_materia, id_producto) VALUES (%s, %s)", (m_id, p_id))
    except mysql.connector.errors.IntegrityError:
        pass
db.commit()

# Transacciones (COMPRA)
for _ in range(1050):
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    monto = round(random.uniform(20000.0, 350000.0), 2)
    cursor.execute(
        "INSERT INTO COMPRA (id_comprador, id_publicacion, monto_total, metodo_pago) VALUES (%s, %s, %s, %s)",
        (c_id, pub_id, monto, random.choice(['Transferencia Bancaria', 'Nequi', 'Daviplata', 'Efectivo']))
    )

# 4. Datos en la tabla OFERTA (Re-negociación de precios con montos reales)
for _ in range(200):
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    # Generar oferta menor al precio promedio de mercado
    monto_ofertado = round(random.uniform(15000.0, 120000.0), 2)
    estado_oferta = random.choice(['Pendiente', 'Aceptada', 'Rechazada'])
    cursor.execute(
        "INSERT INTO OFERTA (id_comprador, id_publicacion, monto_ofertado, estado_oferta) VALUES (%s, %s, %s, %s)",
        (c_id, pub_id, monto_ofertado, estado_oferta)
    )

# Préstamos de material académico
prestamo_ids = []
for _ in range(200):
    c_id = random.choice(comprador_ids)
    pub_id = random.choice(publicacion_ids)
    f_solicitud = fake.date_time_between(start_date='-6m', end_date='-1m')
    f_inicio = f_solicitud + timedelta(days=1)
    f_pactada = f_inicio + timedelta(days=random.randint(5, 15))
    
    # Determinar si el préstamo está demorado/vencido para activar la regla de sanción
    estado_prestamo = random.choice(['Solicitado', 'Activo', 'Devuelto', 'Demorado'])
    f_real = None
    if estado_prestamo == 'Devuelto':
        f_real = f_pactada - timedelta(days=random.randint(0, 2))
    elif estado_prestamo == 'Demorado':
        f_real = None # Sigue sin devolverse a tiempo
        
    cursor.execute(
        "INSERT INTO PRESTAMO (id_comprador, id_publicacion, fecha_solicitud, fecha_inicio, fecha_devolucion_pactada, fecha_devolucion_real, estado_prestamo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (c_id, pub_id, f_solicitud.strftime('%Y-%m-%d %H:%M:%S'), f_inicio.strftime('%Y-%m-%d %H:%M:%S'), f_pactada.strftime('%Y-%m-%d %H:%M:%S'), f_real.strftime('%Y-%m-%d %H:%M:%S') if f_real else None, estado_prestamo)
    )
    prestamo_ids.append(cursor.lastrowid)

# 6. Sanciones por productos prestados no entregados en el plazo dado
cursor.execute("SELECT id_prestamo, id_comprador FROM PRESTAMO WHERE estado_prestamo = 'Demorado'")
prestamos_demorados = cursor.fetchall()

for p_id, c_id in prestamos_demorados:
    admin_id = random.choice(admin_ids)
    motivo_sancion = "Incumplimiento en la fecha límite de devolución del material bibliográfico/instrumento prestado."
    monto_multa = round(random.uniform(15000.0, 50000.0), 2)
    f_inicio_sancion = fake.date_time_between(start_date='-20d', end_date='now')
    f_fin_sancion = f_inicio_sancion + timedelta(days=30)
    
    cursor.execute(
        "INSERT INTO SANCION (id_usuario, id_prestamo, id_administrador, motivo, monto_multa, fecha_inicio, fecha_fin, estado_sancion) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (c_id, p_id, admin_id, motivo_sancion, monto_multa, f_inicio_sancion.strftime('%Y-%m-%d %H:%M:%S'), f_fin_sancion.strftime('%Y-%m-%d %H:%M:%S'), 'Vigente')
    )

# Trueques académicos
for _ in range(80):
    c_id = random.choice(comprador_ids)
    pub_ofrecida, pub_deseada = random.sample(publicacion_ids, 2)
    cursor.execute(
        "INSERT INTO TRUEQUE (id_comprador_iniciador, id_publicacion_deseada, id_publicacion_ofrecida, estado_trueque) VALUES (%s, %s, %s, %s)",
        (c_id, pub_deseada, pub_ofrecida, random.choice(['Pendiente', 'Aceptado', 'Rechazado']))
    )

db.commit()
cursor.close()
db.close()
print("¡Poblamiento de datos contextualizado y validado completado con éxito!")