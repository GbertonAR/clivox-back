from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import uuid

router = APIRouter()

class Sala:
    def __init__(self, sala_id: str):
        self.sala_id = sala_id
        self.instructor: WebSocket | None = None
        self.clientes: Dict[str, WebSocket] = {}

salas: Dict[str, Sala] = {}  # sala_id -> Sala

@router.websocket("/ws/{rol}/{sala_id}")
async def websocket_handler(websocket: WebSocket, rol: str, sala_id: str):
    await websocket.accept()
    client_id = str(uuid.uuid4())

    if sala_id not in salas:
        salas[sala_id] = Sala(sala_id)

    sala = salas[sala_id]

    if rol == "instructor":
        sala.instructor = websocket
        print(f"Instructor conectado en sala {sala_id}")
    elif rol == "cliente":
        sala.clientes[client_id] = websocket
        print(f"Cliente {client_id} conectado en sala {sala_id}")
        # Avisar al instructor que hay un nuevo cliente
        if sala.instructor:
            await sala.instructor.send_text(f'NEW_CLIENT::{client_id}')
    else:
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_text()

            # Mensajes señalización tipo: OFFER::<id>::<payload>
            if "::" in data:
                parts = data.split("::", 2)
                if len(parts) == 3:
                    tipo, target_id, payload = parts
                    if rol == "instructor" and target_id in sala.clientes:
                        await sala.clientes[target_id].send_text(f'{tipo.upper()}::{client_id}::{payload}')
                    elif rol == "cliente" and sala.instructor:
                        await sala.instructor.send_text(f'{tipo.upper()}::{client_id}::{payload}')
    except WebSocketDisconnect:
        if rol == "instructor":
            sala.instructor = None
        elif rol == "cliente":
            sala.clientes.pop(client_id, None)
        print(f"Desconectado: {rol} {client_id} de sala {sala_id}")
