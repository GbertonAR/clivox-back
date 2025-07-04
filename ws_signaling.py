from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict

router = APIRouter()

rooms: Dict[str, Dict[str, WebSocket]] = {}

async def notify_users_in_room(sala_id: str, message: str, exclude_user: str = None):
    if sala_id not in rooms:
        return
    for user_id, ws in rooms[sala_id].items():
        if user_id != exclude_user:
            try:
                await ws.send_text(message)
            except:
                pass

@router.websocket("/ws/{role}/{sala_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, role: str, sala_id: str, user_id: str):
    await websocket.accept()
    if sala_id not in rooms:
        rooms[sala_id] = {}
    rooms[sala_id][user_id] = websocket

    # Avisar a todos que un nuevo usuario se unió
    await notify_users_in_room(sala_id, f"NEW_USER::{user_id}", exclude_user=user_id)

    try:
        while True:
            data = await websocket.receive_text()
            parts = data.split("::", 2)
            if len(parts) != 3:
                continue
            tipo, destino_id, payload = parts

            if sala_id in rooms and destino_id in rooms[sala_id]:
                await rooms[sala_id][destino_id].send_text(f"{tipo}::{user_id}::{payload}")

    except WebSocketDisconnect:
        del rooms[sala_id][user_id]
        await notify_users_in_room(sala_id, f"USER_LEFT::{user_id}", exclude_user=user_id)
        if not rooms[sala_id]:
            del rooms[sala_id]
