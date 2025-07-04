from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

# Diccionario: sala_id -> { user_id: WebSocket }
rooms: Dict[str, Dict[str, WebSocket]] = {}

# Función para enviar mensaje a todos en la sala, menos a quien se indica
async def notify_users_in_room(sala_id: str, message: str, exclude_user: str = None):
    if sala_id not in rooms:
        return

    for user_id, ws in rooms[sala_id].items():
        if user_id != exclude_user:
            try:
                await ws.send_text(message)
            except Exception as e:
                print(f"[ERROR] No se pudo notificar a {user_id}: {e}")

# WebSocket principal para signaling entre usuarios
@router.websocket("/ws/{role}/{sala_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, role: str, sala_id: str, user_id: str):
    print(f"[WS] Conexión entrante: role={role}, sala={sala_id}, user={user_id}")

    # Aceptar WebSocket con CORS permisivo (solo para testing local)
    await websocket.accept(headers=[(b"Access-Control-Allow-Origin", b"*")])

    if sala_id not in rooms:
        rooms[sala_id] = {}
    rooms[sala_id][user_id] = websocket

    print(f"[WS] Usuario '{user_id}' ({role}) conectado a sala '{sala_id}'")

    await notify_users_in_room(sala_id, f"NEW_USER::{user_id}", exclude_user=user_id)

    try:
        while True:
            data = await websocket.receive_text()
            parts = data.split("::", 2)  # tipo, destino_id, payload

            if len(parts) != 3:
                print(f"[WARN] Mensaje mal formado: {data}")
                continue

            tipo, destino_id, payload = parts

            if sala_id in rooms and destino_id in rooms[sala_id]:
                try:
                    await rooms[sala_id][destino_id].send_text(f"{tipo}::{user_id}::{payload}")
                except Exception as e:
                    print(f"[ERROR] Error enviando a {destino_id}: {e}")

    except WebSocketDisconnect:
        print(f"[WS] Usuario '{user_id}' desconectado de sala '{sala_id}'")
        del rooms[sala_id][user_id]
        await notify_users_in_room(sala_id, f"USER_LEFT::{user_id}", exclude_user=user_id)
        if not rooms[sala_id]:
            del rooms[sala_id]

# Ruta simple para testeo de WebSocket
@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("✅ Test WS conectado")
    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"Eco: {msg}")
    except WebSocketDisconnect:
        print("[WS TEST] Cliente desconectado")
