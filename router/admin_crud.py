from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
import sqlite3

router = APIRouter()
DB_PATH = "clivox.db"  # Asegurate de que esta ruta sea correcta


# 🔹 1. Obtener lista de tablas
@router.get("/api/admin_crud/tables")
def get_tables() -> List[str]:
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    rows = cursor.fetchall()
    print("Tablas obtenidas, procesando...")
    tables = []
    for row in rows:
        if row[0] and row[0] != 'sqlite_sequence':
            tables.append(row[0])  # Para depuración
    conn.close()
    return tables

# 🔹 2. Obtener columnas de una tabla
@router.get("/api/admin_crud/schema/{table_name}")
def get_table_schema(table_name: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    schema = [
        {"name": row[1], "type": row[2], "pk": bool(row[5])}
        for row in cursor.fetchall()
    ]
    conn.close()
    return schema

# 🔹 3. Obtener todos los registros
@router.get("/api/admin_crud/data/{table_name}")
def get_table_data(table_name: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = [dict(row) for row in cursor.fetchall()]
        return rows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# 🔹 4. Crear nuevo registro
@router.post("/api/admin_crud/data/{table_name}")
async def create_record(table_name: str, data: Dict[str, Any]):
    keys = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    values = list(data.values())

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO {table_name} ({keys}) VALUES ({placeholders})",
            values,
        )
        conn.commit()
        return {"message": "Registro creado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# 🔹 5. Editar registro
@router.put("/api/admin_crud/data/{table_name}/{row_id}")
async def update_record(table_name: str, row_id: int, data: Dict[str, Any]):
    set_clause = ", ".join([f"{key}=?" for key in data])
    values = list(data.values()) + [row_id]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"UPDATE {table_name} SET {set_clause} WHERE rowid=?",
            values,
        )
        conn.commit()
        return {"message": "Registro actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

# 🔹 6. Eliminar registro
@router.delete("/api/admin_crud/data/{table_name}/{row_id}")
def delete_record(table_name: str, row_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table_name} WHERE rowid=?", (row_id,))
        conn.commit()
        return {"message": "Registro eliminado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()
