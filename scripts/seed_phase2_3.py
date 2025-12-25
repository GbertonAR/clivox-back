import sqlite3
import os
import json

def seed():
    db_path = "clivox.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Seed Organization
    estetica = {
        "primaryColor": "#3b82f6", 
        "secondaryColor": "#8b5cf6", 
        "theme": "dark"
    }
    cursor.execute("""
        INSERT OR REPLACE INTO organizaciones (id, nombre, tipo, logo_url, configuracion_estetica)
        VALUES (1, 'Clivox Defense Academy', 'Empresa', '/pwa-192x192.png', ?)
    """, (json.dumps(estetica),))

    # 2. Seed an AI Exam Definition for training ID 1
    cursor.execute("""
        INSERT OR REPLACE INTO examenes_definiciones (id, id_capacitacion, temas, cantidad_preguntas, nota_minima, intentos_maximos)
        VALUES (1, 1, 'Protocolos de Seguridad ACS y PWA Moderno', 5, 70, 3)
    """)

    conn.commit()
    conn.close()
    print("Seeding completed.")

if __name__ == "__main__":
    seed()
