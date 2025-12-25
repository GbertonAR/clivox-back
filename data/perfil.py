from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import sqlite3

router = APIRouter()

DB_PATH = "clivox.db"

print("Cargando perfil.py...", DB_PATH)

class UsuarioPerfil(BaseModel):
    nombre: str
    apellido: Optional[str] = None # Asumiendo que 'apellido' puede ser nulo si no es NOT NULL en DB
    email: str
    celular: Optional[str] = None # Asumiendo que 'celular' puede ser nulo
    cuil: Optional[str] = None    # Asumiendo que 'cuil' puede ser nulo

    # Estos son los IDs que usas para la lógica de selección
    id_provincia: int
    id_municipio: int

    # ESTOS SON LOS NUEVOS CAMPOS QUE VIENEN DEL JOIN
    nombre_municipio: str
    nombre_provincia: str

    # Opcional: Si este modelo se usa para las actualizaciones POST/PUT,
    # y no quieres que el frontend envíe 'nombre_municipio'/'nombre_provincia'
    # puedes crear un modelo diferente para la actualización (ej. UsuarioPerfilUpdate)
    # o hacer estos campos opcionales para la entrada, pero requeridos para la salida.
    # Por ahora, los dejamos requeridos si siempre vienen del SELECT.

# Obtener perfil del usuario (simulación sin auth por ahora)
@router.get("/api/usuarios/perfil")
def obtener_perfil():
    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("cursor")

        cursor.execute("""
            SELECT
                u.nombre,
                u.apellido,
                u.email,
                u.celular,
                u.cuil,
                m.ID AS id_municipio,         -- Utiliza 'ID' de la tabla Municipios
                m.Nombre AS nombre_municipio, -- Utiliza 'Nombre' de la tabla Municipios
                p.ID AS id_provincia,         -- Utiliza 'ID' de la tabla Provincias
                p.Nombre AS nombre_provincia  -- Utiliza 'Nombre' de la tabla Provincias
            FROM
                usuarios u
            JOIN
                Municipios m ON u.id_municipio = m.ID -- <-- ¡AHORA CON 'M' MAYÚSCULA EN EL NOMBRE DE LA TABLA Y 'ID' DE LA COLUMNA!
            JOIN
                Provincias p ON m.Id_Provincia = p.ID -- <-- ¡AHORA CON 'P' MAYÚSCULA EN EL NOMBRE DE LA TABLA Y 'ID', 'Id_Provincia' DE LAS COLUMNAS!
            LIMIT 1;
        """)
        user_data = cursor.fetchone()
        print("user_data", user_data)

        if user_data:
            # Actualiza las columnas para que coincidan con el SELECT
            columns = [
                "nombre", "apellido", "email", "celular", "cuil",
                "id_municipio", "nombre_municipio", "id_provincia", "nombre_provincia"
            ]
            profile = dict(zip(columns, user_data))
            return profile
        else:
            return None # O lanza HTTPException si no se encuentra el perfil

    except sqlite3.OperationalError as e:
        print(f"Error de base de datos en obtener_perfil: {e}")
        raise # O maneja el error apropiadamente
    except Exception as e:
        print(f"Error inesperado al obtener perfil: {e}")
        raise
    finally:
        if conn:
            conn.close()
# def obtener_perfil():
#     conn = sqlite3.connect(DB_PATH)
#     cursor = conn.cursor()
#     cursor.execute("SELECT nombre, apellido, email, celular, cuil, id_provincia, id_municipio FROM usuarios LIMIT 1")
#     resultado = cursor.fetchone()
#     conn.close()

#     if resultado:
#         keys = ["nombre", "apellido", "email", "celular", "cuil", "id_provincia", "id_municipio"]
#         return dict(zip(keys, resultado))
#     raise HTTPException(status_code=404, detail="Usuario no encontrado")

# Actualizar perfil del usuario
@router.post("/api/usuarios/actualizar")
def actualizar_perfil(data: UsuarioPerfil):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE usuarios
            SET nombre = ?, apellido = ?, email = ?, celular = ?, cuil = ?, id_provincia = ?, id_municipio = ?
            WHERE email = ?
        """, (data.nombre, data.apellido, data.email, data.celular, data.cuil, data.id_provincia, data.id_municipio, data.email))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    conn.close()
    return {"message": "Datos actualizados correctamente"}
