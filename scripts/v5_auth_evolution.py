import sqlite3
import os

def migrate():
    # Use absolute or relative path correctly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "..", "clivox.db")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"Running migration v5_auth_evolution.py at {db_path}...")

    # Table for WebAuthn (Biometric) Credentials
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios_biometria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario TEXT NOT NULL,
        credential_id BLOB NOT NULL,
        public_key BLOB NOT NULL,
        sign_count INTEGER DEFAULT 0,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
    )
    """)

    # Table for QR Session Tokens (Screen Login)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sesiones_qr (
        token_sesion TEXT PRIMARY KEY,
        estado TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, ESCANEADO, AUTORIZADO, EXPIRADO
        id_usuario TEXT,
        id_organizacion INTEGER,
        fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_expiracion DATETIME
    )
    """)

    conn.commit()
    conn.close()
    print("Migration v5_auth_evolution.py completed successfully.")

if __name__ == "__main__":
    migrate()
