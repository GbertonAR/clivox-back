from fastapi import APIRouter, HTTPException
import sqlite3
import uuid
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "clivox.db"

class QRAuthRequest(BaseModel):
    token: str
    user_id: str
    org_id: int

@router.post("/api/auth/qr/generate")
def generate_qr_session():
    """Genera un token de sesión para mostrar como QR en pantalla."""
    token = str(uuid.uuid4())
    expires = datetime.now() + timedelta(minutes=5)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sesiones_qr (token_sesion, estado, fecha_expiracion)
            VALUES (?, 'PENDIENTE', ?)
        """, (token, expires))
        conn.commit()
        conn.close()
        return {"token": token, "expires": expires}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/auth/qr/status/{token}")
def check_qr_status(token: str):
    """El frontend polea este endpoint para saber si el QR fue escaneado/autorizado."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT estado, id_usuario, id_organizacion FROM sesiones_qr
            WHERE token_sesion = ?
        """, (token,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Token no encontrado")
            
        return {
            "estado": row[0],
            "user_id": row[1],
            "org_id": row[2]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/auth/qr/authorize")
def authorize_qr_session(data: QRAuthRequest):
    """El dispositivo móvil llama a este endpoint después de escanear el QR."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sesiones_qr
            SET estado = 'AUTORIZADO', id_usuario = ?, id_organizacion = ?
            WHERE token_sesion = ? AND estado = 'PENDIENTE'
        """, (data.user_id, data.org_id, data.token))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="Token inválido o ya procesado")
            
        conn.commit()
        conn.close()
        return {"mensaje": "Sesión autorizada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
