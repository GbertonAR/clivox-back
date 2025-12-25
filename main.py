from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from fastapi.responses import HTMLResponse
from datetime import datetime
import os
from router import acs, communication, acs_bot, acs_tokens, acs_videocall, llamada_eventos
from router import dashboard_stats, admin_crud, instructores_router, maintenance
from router import auth_mail, auth_qr, auth, auth_qr_logic, salas_routes, salas_pendientes, organizaciones, lms_engine
from data import  ubicacion, perfil  # ✅ tu nuevo archivo
from data.perfil import UsuarioPerfil  # ✅ importar el modelo de perfil
#from data import sala_routes
from sqlite3 import connect
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
    #allow_origins=allowed_origins,
    allow_origins=[
         "http://localhost:8000",
         "http://localhost:5174",
         "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(acs.router)  # incluir el router de ACS
app.include_router(communication.router)  # incluir el router de comunicación
app.include_router(acs_bot.router)  # incluir el router del bot de ACS
app.include_router(acs_tokens.router, prefix="/acs")
app.include_router(acs_videocall.router)  # incluir el router de videollamadas de ACS
app.include_router(llamada_eventos.router)  # incluir el router de eventos de llamadas
app.include_router(dashboard_stats.router) # incluir el router de estadísticas del dashboard
#app.include_router(admin_crud.router, prefix="/api/admin-crud")
app.include_router(admin_crud.router)
app.include_router(auth_mail.router)
app.include_router(auth_qr.router)
app.include_router(auth.router)
app.include_router(auth_qr_logic.router)
app.include_router(instructores_router.router) # incluir el router de instructores
app.include_router(perfil.router)
app.include_router(ubicacion.router)
#app.include_router(salas_routes.router)  # incluir el router de salas
app.include_router(salas_routes.router)  # incluir el router de
app.include_router(salas_pendientes.router)
app.include_router(organizaciones.router)
app.include_router(lms_engine.router)
app.include_router(maintenance.router)  # Hidden maintenance endpoints



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
    
    
@app.get("/dashboard/stats")
def get_dashboard_stats():
    conn = connect("clivox.db")
    cursor = conn.cursor()

    cursor.execute("SELECT evento, COUNT(*) FROM llamada_eventos GROUP BY evento")
    eventos = [{"evento": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

    cursor.execute("SELECT sala_id, COUNT(*) FROM llamada_eventos GROUP BY sala_id")
    llamadas = [{"sala_id": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

    conn.close()
    return {"eventos": eventos, "llamadas": llamadas}               

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)