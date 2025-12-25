import sqlite3
import os

def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "..", "clivox.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("Running migration v6_multimedia_exams.py...")

    # Update examenes_preguntas_ia to support multimedia
    try:
        cursor.execute("ALTER TABLE examenes_preguntas_ia ADD COLUMN audio_url TEXT")
        cursor.execute("ALTER TABLE examenes_preguntas_ia ADD COLUMN video_hint TEXT")
        print("Updated examenes_preguntas_ia with multimedia columns.")
    except sqlite3.OperationalError:
        print("Columns already exist or table doesn't exist.")

    conn.commit()
    conn.close()
    print("Migration v6_multimedia_exams.py completed successfully.")

if __name__ == "__main__":
    migrate()
