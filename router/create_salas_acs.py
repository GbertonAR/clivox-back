# routers/salas_acs.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import uuid

from azure.communication.rooms import RoomsClient, RoomJoinPolicy, RoomParticipantRole, CreateRoomOptions
from azure.communication.identity import CommunicationIdentityClient
from azure.core.credentials import AzureKeyCredential

from data.modelos import crear_sala_en_db  # tu función personalizada para guardar la sala

router = APIRouter()

# 🔐 Tu connection string de Azure Communication Services
ACS_CONNECTION_STRING = "endpoint=https://<tu-recurso>.communication.azure.com/;accesskey=<tu-key>"

class SalaData(BaseModel):
    nombre: str
    descripcion: str
    fechaInicio: str
    horaInicio: str
    duracionEstimada: int
    capacidadMaxima: int
    configuracion: str
    permitirChat: bool
    permitirCompartirPantalla: bool
    permitirGrabacion: bool
    modoEspera: bool
    requiereAprobacion: bool
    participantes: list = []

@router.post("/api/crear_sala_acs")
async def crear_sala_acs(sala: SalaData):
    try:
        # 🕒 Calcular fecha/hora de inicio y fin
        inicio = datetime.strptime(f"{sala.fechaInicio} {sala.horaInicio}", "%Y-%m-%d %H:%M")
        fin = inicio + timedelta(minutes=sala.duracionEstimada)

        # 🔑 Inicializar cliente de Azure Rooms
        rooms_client = RoomsClient.from_connection_string(ACS_CONNECTION_STRING)

        # 🆕 Crear sala (Room) en Azure
        response = rooms_client.create_room(
            valid_from=inicio,
            valid_until=fin,
            room_join_policy=RoomJoinPolicy.INVITE_ONLY,
            participants=[]  # Podés agregar CommunicationIdentifiers si los tenés
        )
        room_id = response.id

        # ✅ Guardar en base de datos local
        nueva_sala = {
            "groupCallId": room_id,
            "nombre": sala.nombre,
            "descripcion": sala.descripcion,
            "fechaInicio": sala.fechaInicio,
            "horaInicio": sala.horaInicio,
            "duracionEstimada": sala.duracionEstimada,
            "capacidadMaxima": sala.capacidadMaxima,
            "configuracion": sala.configuracion,
            "permitirChat": sala.permitirChat,
            "permitirCompartirPantalla": sala.permitirCompartirPantalla,
            "permitirGrabacion": sala.permitirGrabacion,
            "modoEspera": sala.modoEspera,
            "requiereAprobacion": sala.requiereAprobacion,
            "participantes": sala.participantes
        }
        crear_sala_en_db(nueva_sala)

        # 📎 Generar Join URL base (manual)
        join_url = f"https://<TU_DOMINIO_WEB>/sala/{room_id}"

        return {
            "success": True,
            "roomId": room_id,
            "joinUrl": join_url,
            "inicio": inicio.isoformat(),
            "fin": fin.isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
