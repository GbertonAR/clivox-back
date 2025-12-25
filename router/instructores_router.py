from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel
import sqlite3
from typing import Optional

router = APIRouter(prefix="/instructores", tags=["Instructores"])

DB_PATH = "clivox.db"  # Ajustar si es necesario


# --- Modelos ---
class InstructorPerfil(BaseModel):
    id: int
    nombre: str
    apellido: str
    dni: str
    email: str
    telefono: Optional[str]
    id_provincia: Optional[int]
    id_municipio: Optional[int]

class InstructorPerfilUpdate(BaseModel):
    nombre: str
    apellido: str
    telefono: Optional[str]
    id_provincia: Optional[int]
    id_municipio: Optional[int]


# --- Dependencia simple para obtener usuario actual ---
def get_current_user(request: Request) -> dict:
    """
    Esta función debería extraer al usuario actual desde la sesión o encabezados.
    En este ejemplo simple, asumimos que viene en `request.state.usuario`.
    """
    if not hasattr(request.state, "usuario"):
        raise HTTPException(status_code=401, detail="No autenticado")
    return request.state.usuario


# --- GET /instructores/mi-perfil ---
@router.get("/mi-perfil", response_model=InstructorPerfil)
def obtener_mi_perfil(usuario: dict = Depends(get_current_user)):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nombre, apellido, dni, email, telefono, id_provincia, id_municipio
            FROM instructores
            WHERE id = ?
        """, (usuario["id"],))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Perfil no encontrado")

        return dict(row)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener perfil: {e}")


# --- PUT /instructores/mi-perfil ---
@router.put("/mi-perfil")
def actualizar_mi_perfil(
    datos_actualizados: InstructorPerfilUpdate = Body(...),
    usuario: dict = Depends(get_current_user)
):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE instructores
            SET nombre = ?, apellido = ?, telefono = ?, id_provincia = ?, id_municipio = ?
            WHERE id = ?
        """, (
            datos_actualizados.nombre,
            datos_actualizados.apellido,
            datos_actualizados.telefono,
            datos_actualizados.id_provincia,
            datos_actualizados.id_municipio,
            usuario["id"]
        ))

        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="No se encontró el perfil para actualizar")

        conn.commit()
        conn.close()

        return {"mensaje": "Perfil actualizado correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar perfil: {e}")
