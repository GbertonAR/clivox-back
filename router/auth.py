from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import sqlite3
import random
import string

router = APIRouter()

DB_PATH = "clivox.db"

# Modelo del request
class EmailRequest(BaseModel):
    email: EmailStr

# Utilidad: generar código alfanumérico
def generar_codigo(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class CodigoRequest(BaseModel):
    email: EmailStr
    codigo: str

@router.post("/api/verificar-codigo")
def verificar_codigo(data: CodigoRequest):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT codigo FROM codigos_verificacion
            WHERE email = ?
        """, (data.email,))
        row = cursor.fetchone()

        if row is None or row[0] != data.codigo:
            raise HTTPException(status_code=401, detail="Código inválido")

        # Eliminar código si es válido (opcional)
        cursor.execute("DELETE FROM codigos_verificacion WHERE email = ?", (data.email,))
        conn.commit()
        conn.close()

        return {"mensaje": "Código verificado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/api/verificar-email")
def verificar_email(data: EmailRequest):
    email = data.email

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si el usuario existe
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        resultado = cursor.fetchone()

        if resultado is None:
            raise HTTPException(status_code=404, detail="Usuario no registrado")

        # Generar y guardar código temporal
        codigo = generar_codigo()

        # Reemplazá esto por envío real de email si querés
        print(f"[DEBUG] Enviar código {codigo} a {email}")

        # Guardar en tabla de verificación (creala si no existe)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS codigos_verificacion (
                email TEXT PRIMARY KEY,
                codigo TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            INSERT OR REPLACE INTO codigos_verificacion (email, codigo)
            VALUES (?, ?)
        """, (email, codigo))

        conn.commit()
        conn.close()

        return {"mensaje": "Código enviado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/api/registrar-usuario", status_code=status.HTTP_201_CREATED)
# def registrar_usuario(data: RegistroRequest):
#     try:
#         conn = sqlite3.connect(DB_PATH)
#         cursor = conn.cursor()

#         # Verificar si el email ya existe
#         cursor.execute("SELECT id FROM usuarios WHERE email = ?", (data.email,))
#         if cursor.fetchone() is not None:
#             return {"detail": "El email ya está registrado"}

#         # Insertar usuario nuevo
#         cursor.execute(
#             "INSERT INTO usuarios (nombre, email) VALUES (?, ?)",
#             (data.nombre, data.email),
#         )
#         conn.commit()
#         conn.close()

#         return {"mensaje": "Usuario registrado con éxito"}

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/validar-mail-post-registro")
def enviar_codigo_validacion_post_registro(data: EmailRequest):
    email = data.email

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Verificar si usuario existe (por registro recién hecho)
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        resultado = cursor.fetchone()

        if resultado is None:
            raise HTTPException(status_code=404, detail="Usuario no registrado")

        # Generar código de validación
        codigo = generar_codigo()

        # Guardar código en tabla códigos de validación (misma tabla codigos_verificacion)
        cursor.execute("""
            INSERT OR REPLACE INTO codigos_verificacion (email, codigo)
            VALUES (?, ?)
        """, (email, codigo))

        conn.commit()
        conn.close()

        # Aquí enviar email real con el código (o solo log/debug)
        print(f"[DEBUG] Código validación registro: {codigo} para {email}")

        return {"mensaje": "Código de validación enviado por correo"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
