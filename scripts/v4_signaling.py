import sqlite3

DB_PATH = "clivox.db"

def migrate_v4():
    print(f"Iniciando migración v4 en {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabla para almacenar el estado compartido de una sala (whiteboard, participantes activos)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sala_estado (
            sala_id TEXT PRIMARY KEY,
            whiteboard_data TEXT DEFAULT '[]',
            participantes_activos TEXT DEFAULT '[]', -- JSON list: [{"uid": "...", "name": "...", "status": "active"}]
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print("Migración v4 completada con éxito.")

if __name__ == "__main__":
    migrate_v4()
