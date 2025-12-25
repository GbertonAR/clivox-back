import sqlite3

DB_PATH = "clivox.db"

def seed_test_exam():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Asegurar que exista al menos una capacitación
    cursor.execute("INSERT OR IGNORE INTO capacitaciones (id, titulo) VALUES (1, 'Introducción a Clivox v2')")
    
    # 2. Crear preguntas para esa capacitación
    preguntas = [
        (1, "¿Qué herramienta de comunicación utiliza Clivox principalmente?", "multiple_choice"),
        (1, "¿Clivox permite el seguimiento de asistencia automática?", "verdadero_falso")
    ]
    
    for p in preguntas:
        cursor.execute("INSERT INTO examenes_preguntas (id_capacitacion, enunciado, tipo) VALUES (?, ?, ?)", p)
        p_id = cursor.lastrowid
        
        if p[2] == "multiple_choice":
            opciones = [
                (p_id, "MS Teams", True),
                (p_id, "Zoom", False),
                (p_id, "Skype", False)
            ]
        else:
            opciones = [
                (p_id, "Verdadero", True),
                (p_id, "Falso", False)
            ]
        
        cursor.executemany("INSERT INTO examenes_opciones (id_pregunta, texto, es_correcta) VALUES (?, ?, ?)", opciones)

    conn.commit()
    conn.close()
    print("Datos de prueba (examen) cargados exitosamente.")

if __name__ == "__main__":
    seed_test_exam()
