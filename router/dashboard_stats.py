from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Union
import sqlite3

router = APIRouter()

DB_PATH = "clivox.db"  # Asegurate de que la ruta sea correcta según tu estructura


# ✅ Modelos Pydantic para validar la respuesta
class Evento(BaseModel):
    evento: str
    cantidad: int

class Llamada(BaseModel):
    sala_id: str
    cantidad: int

class DashboardStats(BaseModel):
    eventos: List[Evento]
    llamadas: List[Llamada]


@router.get("/dashboard/stats", response_model=Union[DashboardStats, dict])
def get_dashboard_stats():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Eventos por tipo (ej: mute, screen_share_start, call_start, etc)
        cursor.execute("SELECT evento, COUNT(*) FROM llamada_eventos GROUP BY evento")
        eventos = [{"evento": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

        # Cantidad de eventos por sala
        cursor.execute("SELECT sala_id, COUNT(*) FROM llamada_eventos GROUP BY sala_id")
        llamadas = [{"sala_id": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            "eventos": eventos,
            "llamadas": llamadas
        }

    except Exception as e:
        return {
            "error": f"Ocurrió un error al acceder a la base de datos: {str(e)}"
        }
