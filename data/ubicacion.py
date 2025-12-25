from fastapi import APIRouter, HTTPException, Query
import sqlite3

router = APIRouter()
DB_PATH = "clivox.db"  # Asegúrate de que esta ruta sea correcta

@router.get("/api/provincias")
def get_provincias():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM provincias")
    provincias = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
    conn.close()
    return provincias

@router.get("/api/municipios")
def get_municipios(provincia_id: int = Query(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre FROM municipios WHERE id_provincia = ?", (provincia_id,))
    municipios = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
    conn.close()
    return municipios
