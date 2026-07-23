# 02_dml_generator.py
# Script generador para poblar volumen realista (Mínimo 1000 filas)
import mysql.connector
from faker import Faker
import random

fake = Faker('es_CO')
db = mysql.connector.connect(host="localhost", user="root", password="", database="UnTrade")
cursor = db.cursor()

# 1. Generate 150 Users
for _ in range(150):
    univ = random.randint(1, 10)
    cursor.execute("INSERT INTO USUARIO (id_universidad, nombre_completo, correo_estudiantil, password_hash) VALUES (%s, %s, %s, %s)",
                   (univ, fake.name(), fake.email(), fake.sha256()))
db.commit()

# 2. Assign Subclasses (20 Admins, 80 Sellers, 100 Buyers - overlapping allowed)
for i in range(1, 21):
    cursor.execute("INSERT INTO ADMINISTRADOR (id_administrador, nivel_permiso, area_soporte) VALUES (%s, %s, %s)",
                   (i, random.choice(['SuperAdmin', 'Moderador', 'Soporte']), fake.job()))
for i in range(21, 101):
    cursor.execute("INSERT INTO VENDEDOR (id_vendedor, calificacion, ventas_completadas) VALUES (%s, %s, %s)",
                   (i, round(random.uniform(3.0, 5.0), 1), random.randint(0, 50)))
for i in range(50, 150):
    cursor.execute("INSERT INTO COMPRADOR (id_comprador, preferencias_busqueda) VALUES (%s, %s)",
                   (i, fake.word()))
db.commit()

# 3. Generate 300 Publications & Products/Services
for _ in range(300):
    vendedor = random.randint(21, 100)
    admin = random.randint(1, 20)
    tipo = random.choice(['Producto', 'Servicio'])
    cursor.execute("INSERT INTO PUBLICACION (id_vendedor, id_administrador_moderador, tipo_item, titulo, descripcion, estado_publicacion) VALUES (%s, %s, %s, %s, %s, %s)",
                   (vendedor, admin, tipo, fake.catch_phrase(), fake.text(), 'Activa'))
    pub_id = cursor.lastrowid
    if tipo == 'Producto':
        cursor.execute("INSERT INTO PRODUCTO (id_publicacion, precio, categoria, estado_fisico, stock) VALUES (%s, %s, %s, %s, %s)",
                       (pub_id, round(random.uniform(10.0, 500.0), 2), fake.word(), random.choice(['NUEVO', 'USADO']), random.randint(1, 20)))
    else:
        cursor.execute("INSERT INTO SERVICIO (id_publicacion, modalidad, tarifa_por_hora, disponibilidad_horaria) VALUES (%s, %s, %s, %s)",
                       (pub_id, random.choice(['Presencial', 'Virtual']), round(random.uniform(15.0, 100.0), 2), "L-V 8am-5pm"))
db.commit()

# 4. Generate 1000+ Transactions (COMPRA) to meet volume constraint
for _ in range(1050):
    comprador = random.randint(50, 149)
    publicacion = random.randint(1, 300)
    monto = round(random.uniform(10.0, 500.0), 2)
    cursor.execute("INSERT INTO COMPRA (id_comprador, id_publicacion, monto_total, metodo_pago) VALUES (%s, %s, %s, %s)",
                   (comprador, publicacion, monto, random.choice(['Tarjeta', 'Transferencia', 'Efectivo'])))
db.commit()
cursor.close()
db.close()