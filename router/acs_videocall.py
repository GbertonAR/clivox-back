from fastapi import APIRouter, Body
from azure.communication.identity import CommunicationIdentityClient
import os
import sqlite3
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

router = APIRouter()
DB_PATH = "clivox.db"

class SalaEstado(BaseModel):
    sala_id: str
    whiteboard_data: Optional[str] = None
    participantes_activos: Optional[str] = None

@router.get("/api/videocall-info")
def get_videocall_info():
    connection_str = os.getenv("ACS_CONNECTION_STRING")
    endpoint = os.getenv("ACS_ENDPOINT")

    if not connection_str or not endpoint:
        return {"error": "ACS config missing"}

    identity_client = CommunicationIdentityClient.from_connection_string(connection_str)
    user = identity_client.create_user()
    token_response = identity_client.get_token(user, scopes=["voip"])

    return {
        "user_id": user.properties["id"],
        "display_name": "Instructor CLIVOX",
        "token": token_response.token,
        "thread_id": "00000000-0000-0000-0000-000000000000"
    }

@router.post("/api/videocall/state/sync")
def sync_videocall_state(estado: SalaEstado):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Asegurar que la sala existe en la tabla de estado
    cursor.execute("INSERT OR IGNORE INTO sala_estado (sala_id) VALUES (?)", (estado.sala_id,))
    
    if estado.whiteboard_data is not None:
        cursor.execute("UPDATE sala_estado SET whiteboard_data = ?, last_updated = ? WHERE sala_id = ?", 
                       (estado.whiteboard_data, datetime.utcnow(), estado.sala_id))
                       
    if estado.participantes_activos is not None:
        cursor.execute("UPDATE sala_estado SET participantes_activos = ?, last_updated = ? WHERE sala_id = ?", 
                       (estado.participantes_activos, datetime.utcnow(), estado.sala_id))
    
    conn.commit()
    conn.close()
    return {"status": "synced"}

@router.get("/api/videocall/state/{sala_id}")
def get_videocall_state(sala_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM sala_estado WHERE sala_id = ?", (sala_id,))
    res = cursor.fetchone()
    conn.close()
    
    if res:
        return dict(res)
    return {"sala_id": sala_id, "whiteboard_data": "[]", "participantes_activos": "[]"}
