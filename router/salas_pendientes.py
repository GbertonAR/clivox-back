from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, date
import sqlite3

router = APIRouter()

# Define el modelo Pydantic para los datos de la sala que se recuperarán de la DB
class SalaDB(BaseModel):
    id: int
    nombre: str
    descripcion: str
    fecha_inicio: str
    hora_inicio: str
    duracion_estimada: int  # Asumiendo que es int para cálculos
    capacidad_maxima: int
    group_call_id: str | None = None # Puede ser None si aún no se generó
    requiere_aprobacion: bool
    permitir_chat: bool
    permitir_grabacion: bool
    permitir_compartir_pantalla: bool
    modo_espera: bool
    configuracion: str | None = None # Asumiendo que 'configuracion' es un TEXT en DB

# Conexión a la base de datos (asegúrate de que la ruta sea correcta)
DATABASE_URL = "clivox.db" # <-- ACTUALIZA ESTA RUTA A TU ARCHIVO .db

def get_db_connection():
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row # Esto permite acceder a las columnas por nombre
    return conn

@router.get("/api/salas_pendientes", response_model=list[SalaDB])
async def get_pending_salas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = date.today().isoformat() # Formato YYYY-MM-DD

        # Consulta para obtener registros donde fecha_inicio es posterior a hoy
        # Usamos DATE() para comparar solo la parte de la fecha
        cursor.execute(
            """
            SELECT id, nombre, descripcion, fecha_inicio, hora_inicio, 
                   duracion_estimada, capacidad_maxima, group_call_id,
                   requiere_aprobacion, permitir_chat, permitir_grabacion,
                   permitir_compartir_pantalla, modo_espera, configuracion
            FROM nueva_sala
            WHERE DATE(fecha_inicio) > DATE(?)
            ORDER BY fecha_inicio, hora_inicio
            """,
            (today,)
        )
        salas = cursor.fetchall()
        conn.close()

        # Convertir Rows a diccionarios para Pydantic
        return [dict(sala) for sala in salas]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener salas pendientes: {str(e)}")