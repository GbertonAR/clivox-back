from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

router = APIRouter(prefix="/organizaciones", tags=["Organizaciones"])
DB_PATH = "clivox.db"

class Organizacion(BaseModel):
    id: Optional[int] = None
    nombre: str
    tipo: str
    logo_url: Optional[str] = None
    configuracion_estetica: Optional[str] = None

@router.get("/", response_model=List[Organizacion])
def listar_organizaciones():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizaciones")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/", response_model=Organizacion)
def crear_organizacion(org: Organizacion):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO organizaciones (nombre, tipo, logo_url, configuracion_estetica)
            VALUES (?, ?, ?, ?)
        """, (org.nombre, org.tipo, org.logo_url, org.configuracion_estetica))
        conn.commit()
        org.id = cursor.lastrowid
        return org
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/{org_id}", response_model=Organizacion)
def obtener_organizacion(org_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM organizaciones WHERE id = ?", (org_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Organización no encontrada")
    return dict(row)
