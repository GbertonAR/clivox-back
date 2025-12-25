import sqlite3
import os

DB_PATH = "clivox.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Iniciando migración v2...")

    # 1. Crear tabla Organizaciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS organizaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT, -- 'Empresa', 'Colegio', 'Academia'
        logo_url TEXT,
        configuracion_estetica TEXT -- JSON string
    )
    """)

    # 2. Agregar id_organizacion a usuarios (si no existe)
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN id_organizacion INTEGER REFERENCES organizaciones(id)")
        print("Columna id_organizacion añadida a usuarios.")
    except sqlite3.OperationalError:
        print("La columna id_organizacion ya existe en usuarios.")

    # 3. Agregar columnas a capacitaciones
    try:
        cursor.execute("ALTER TABLE capacitaciones ADD COLUMN id_organizacion INTEGER REFERENCES organizaciones(id)")
        print("Columna id_organizacion añadida a capacitaciones.")
    except sqlite3.OperationalError:
        print("La columna id_organizacion ya existe en capacitaciones.")

    try:
        cursor.execute("ALTER TABLE capacitaciones ADD COLUMN categoria TEXT")
        print("Columna categoria añadida a capacitaciones.")
    except sqlite3.OperationalError:
        print("La columna categoria ya existe en capacitaciones.")

    try:
        cursor.execute("ALTER TABLE capacitaciones ADD COLUMN es_asincronica BOOLEAN DEFAULT 0")
        print("Columna es_asincronica añadida a capacitaciones.")
    except sqlite3.OperationalError:
        print("La columna es_asincronica ya existe en capacitaciones.")

    # 4. Crear tablas de Exámenes (Preguntas y Opciones)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS examenes_preguntas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_capacitacion INTEGER NOT NULL REFERENCES capacitaciones(id),
        enunciado TEXT NOT NULL,
        tipo TEXT -- 'multiple_choice', 'verdadero_falso'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS examenes_opciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_pregunta INTEGER NOT NULL REFERENCES examenes_preguntas(id),
        texto TEXT NOT NULL,
        es_correcta BOOLEAN NOT NULL
    )
    """)

    # 5. Crear tabla de respuestas de usuarios (para auditoría y calificación)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS examenes_respuestas_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario TEXT NOT NULL REFERENCES usuarios(id),
        id_pregunta INTEGER NOT NULL REFERENCES examenes_preguntas(id),
        id_opcion_seleccionada INTEGER REFERENCES examenes_opciones(id),
        es_correcta BOOLEAN,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    print("Migración v2 completada exitosamente.")

if __name__ == "__main__":
    migrate()
