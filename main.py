from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
from router import acs, communication, acs_bot, acs_tokens, acs_videocall
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


#  # Asegúrate de que estos módulos existan y estén correctamente definidos
 # importar el nuevo módulo





allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
#endpoint = os.getenv("AZURE_COMMUNICATION_ENDPOINT")

app = FastAPI()



# Permitir CORS (ajustar orígenes según frontend)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost",
#         "http://localhost:5173",
#         "http://127.0.0.1:5173"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(acs.router)  # incluir el router de ACS
app.include_router(communication.router)  # incluir el router de comunicación
app.include_router(acs_bot.router)  # incluir el router del bot de ACS
app.include_router(acs_tokens.router, prefix="/acs")
app.include_router(acs_videocall.router)  # incluir el router de videollamadas de ACS



# Estructura para guardar conexiones: { sala_id: { user_id: websocket } }
rooms: Dict[str, Dict[str, WebSocket]] = {}

@app.websocket("/ws/{role}/{sala_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, role: str, sala_id: str, user_id: str):
    await websocket.accept()
    if sala_id not in rooms:
        rooms[sala_id] = {}
    rooms[sala_id][user_id] = websocket

    print(f"[WS] Usuario '{user_id}' ({role}) conectado a sala '{sala_id}'")

    # Avisar a otros usuarios que llegó uno nuevo
    for uid, ws in rooms[sala_id].items():
        if uid != user_id:
            await ws.send_text(f"NEW_USER::{user_id}")

    try:
        while True:
            data = await websocket.receive_text()
            # Formato esperado: tipo::destino_id::mensaje
            parts = data.split("::", 2)
            if len(parts) != 3:
                continue
            tipo, destino_id, mensaje = parts

            # Reenviar al destinatario si está conectado
            if destino_id in rooms[sala_id]:
                await rooms[sala_id][destino_id].send_text(f"{tipo}::{user_id}::{mensaje}")

    except WebSocketDisconnect:
        print(f"[WS] Usuario '{user_id}' desconectado de sala '{sala_id}'")
        del rooms[sala_id][user_id]
        for uid, ws in rooms[sala_id].items():
            await ws.send_text(f"USER_LEFT::{user_id}")

        if not rooms[sala_id]:
            del rooms[sala_id]

@app.get("/", response_class=HTMLResponse)
async def clivox_status():
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"""
    <html>
        <head>
            <title>Clivox</title>
            <style>
                body {{
                    background: linear-gradient(to right, #6a11cb, #2575fc);
                    color: white;
                    font-family: sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .card {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 2rem;
                    border-radius: 1rem;
                    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                    text-align: center;
                }}
                h1 {{
                    margin-bottom: 1rem;
                }}
                p {{
                    font-size: 1.2rem;
                }}
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Clivox activo y funcionando</h1>
                <p>🕒 {now}</p>
            </div>
        </body>
    </html>
    """

@app.post("/acs/token")
def generate_acs_token():
    conn_str = os.getenv("ACS_CONNECTION_STRING")
    if not conn_str:
        return {"error": "ACS_CONNECTION_STRING not configured."}

    client = CommunicationIdentityClient.from_connection_string(conn_str)

    # Crear nuevo usuario + token con permiso VOIP (llamadas)
    token_response = client.create_user_and_token(scopes=["voip"])
    identity = token_response[0]
    token = token_response[1]

    return {
        "user_id": identity.properties["id"],
        "token": token.token,
        "expires_on": token.expires_on.isoformat()
    }