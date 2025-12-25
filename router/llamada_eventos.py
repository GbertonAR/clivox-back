from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import sqlite3

router = APIRouter()

class EventoLlamada(BaseModel):
    user_id: str
    sala_id: str
    evento: str

@router.post("/llamada/evento")
def registrar_evento(evento: EventoLlamada):
    conn = sqlite3.connect("clivox.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO llamada_eventos (user_id, sala_id, evento, timestamp)
        VALUES (?, ?, ?, ?)
    """, (evento.user_id, evento.sala_id, evento.evento, datetime.utcnow()))
    conn.commit()
    conn.close()
    return {"status": "ok"}
