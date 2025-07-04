from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import Generator
from .ws_signaling import router as signaling_router

app = FastAPI()

app.include_router(signaling_router)

DATABASE = "clivox.db"

def get_db() -> Generator:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

class Parametro(BaseModel):
    clave: str
    valor: str

@app.get("/parametros/{clave}", response_model=Parametro)
def leer_parametro(clave: str, db=Depends(get_db)):
    cursor = db.execute("SELECT clave, valor FROM parametros_clivox WHERE clave = ?", (clave,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Parámetro no encontrado")
    return {"clave": row["clave"], "valor": row["valor"]}

@app.get("/salas/{sala_id}")
def obtener_sala(sala_id: str):
    # Por ahora mock simple, luego DB real
    return {"sala_id": sala_id, "nombre": f"Sala {sala_id}"}
