from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sqlite3
import uuid

router = APIRouter()
DB_PATH = "clivox.db"

class ConfiguracionSala(BaseModel):
    permitirChat: bool
    permitirGrabacion: bool
    permitirCompartirPantalla: bool
    modoEspera: bool

class SalaData(BaseModel):
    id: Optional[str] = None
    nombre: str
    descripcion: Optional[str]
    fechaInicio: str
    horaInicio: str
    duracionEstimada: str
    capacidadMaxima: int
    groupCallId: Optional[str]
    requiereAprobacion: bool
    participantes: List[str] = Field(default_factory=list)
    configuracion: ConfiguracionSala

@router.post("/sala_crear")
async def crear_sala(sala: SalaData):
    print("Datos recibidos:", sala)
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        sala_id = sala.id or str(uuid.uuid4())
        group_call_id = sala.groupCallId or str(uuid.uuid4())

        cursor.execute("""
            INSERT INTO nueva_sala (
                nombre, descripcion, fecha_inicio, hora_inicio, duracion_estimada,
                capacidad_maxima, group_call_id, requiere_aprobacion,
                permitir_chat, permitir_grabacion, permitir_compartir_pantalla,
                modo_espera
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sala.nombre,
            sala.descripcion,
            sala.fechaInicio,
            sala.horaInicio,
            sala.duracionEstimada,
            sala.capacidadMaxima,
            group_call_id,
            sala.requiereAprobacion,
            sala.configuracion.permitirChat,
            sala.configuracion.permitirGrabacion,
            sala.configuracion.permitirCompartirPantalla,
            sala.configuracion.modoEspera
        ))

        for participante in sala.participantes:
            cursor.execute("""
                INSERT INTO sala_participantes (group_call_id, email)
                VALUES (?, ?)
            """, (group_call_id, participante))

        conn.commit()
        return { "mensaje": "Sala creada exitosamente", "groupCallId": group_call_id }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear la sala: {str(e)}")

    finally:
        if conn:
            conn.close()
