import sqlite3
import os

DB_PATH = "clivox.db"

def migrate_v3():
    print(f"Iniciando migración v3 en {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Tabla para las definiciones de exámenes (configuración de IA)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examenes_definiciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_capacitacion INTEGER,
            temas TEXT,
            cantidad_preguntas INTEGER DEFAULT 10,
            nota_minima INTEGER DEFAULT 60,
            intentos_maximos INTEGER DEFAULT 5,
            ruta_documento_resguardo TEXT,
            FOREIGN KEY (id_capacitacion) REFERENCES capacitaciones(id)
        )
    """)

    # 2. Tabla para las preguntas generadas por IA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examenes_preguntas_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_definicion INTEGER,
            enunciado TEXT,
            tipo TEXT, -- 'multiple_choice', 'verdadero_falso'
            nivel_complejidad INTEGER DEFAULT 1,
            FOREIGN KEY (id_definicion) REFERENCES examenes_definiciones(id)
        )
    """)

    # 3. Tabla para las opciones de las preguntas generadas por IA
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examenes_opciones_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_pregunta INTEGER,
            texto TEXT,
            es_correcta BOOLEAN,
            FOREIGN KEY (id_pregunta) REFERENCES examenes_preguntas_ia(id)
        )
    """)

    # 4. Tabla para registrar los intentos de los alumnos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS examenes_intentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario TEXT,
            id_definicion INTEGER,
            numero_intento INTEGER,
            puntaje INTEGER,
            aprobado BOOLEAN,
            fecha TIMESTAMP,
            preguntas_json TEXT, -- Almacena el set específico de preguntas (IDs) usado en este intento
            FOREIGN KEY (id_definicion) REFERENCES examenes_definiciones(id)
        )
    """)

    # 5. Tabla para los documentos de resguardo (opcionalmente vinculados a la definición)
    # Ya está en examenes_definiciones, pero podríamos tener una tabla aparte si hay múltiples docs
    
    conn.commit()
    conn.close()
    print("Migración v3 completada con éxito.")

if __name__ == "__main__":
    migrate_v3()
