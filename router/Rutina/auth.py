from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid
import sqlite3

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.requests import Request
from fastapi import Request
from pathlib import Path
from data.mail_utils import enviar_mail_validacion



BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
print(f"📂 Plantillas cargadas desde: {BASE_DIR / 'templates'}")

# Ruta de la base de datos SQLite
DB_PATH = "data/soporte_db.db"

# Inicialización del router
router = APIRouter()

# Función para conectar con la base de datos
def conectar_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Esquema de datos recibidos en el registro
class RegistroUsuario(BaseModel):
    nombre: str
    email: EmailStr
    celular: str
    id_municipio: int

# Endpoint para registrar nuevo usuario
@router.post("/register")
def registrar_usuario(datos: RegistroUsuario):
    conn = conectar_db()
    cur = conn.cursor()

    # Verificar si ya existe un usuario con ese email
    cur.execute("SELECT * FROM usuarios WHERE email = ?", (datos.email,))
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    # Generar ID único y token de validación
    user_id = str(uuid.uuid4())
    token_validacion = str(uuid.uuid4())

    try:
        cur.execute("""
            INSERT INTO usuarios (id, nombre, email, celular, id_municipio, id_rol, token_validacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, datos.nombre, datos.email, datos.celular, datos.id_municipio, 1, token_validacion))
        conn.commit()
        enviar_mail_validacion(datos.email, datos.nombre, token_validacion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar usuario: {str(e)}")
    finally:
        conn.close()

    # Log para desarrollador (reemplazar con envío de email/SMS en el futuro)
    print(f"🟢 Usuario registrado: {datos.email}")
    print(f"🔗 Token de validación: {token_validacion}")

    return {
        "mensaje": "Usuario registrado correctamente. Validación pendiente.",
        "token": token_validacion
    }
    
@router.get("/registro", response_class=HTMLResponse)
def mostrar_formulario_registro(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})    

@router.get("/validar", response_class=HTMLResponse)
def validar_usuario(request: Request, token: str):
    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("SELECT ID FROM usuarios WHERE token_validacion = ?", (token,))
    fila = cur.fetchone()

    if fila:
        # Marcar usuario como validado
        try:
            cur.execute("""
                UPDATE usuarios
                SET token_validacion = NULL
                WHERE id = ?
            """, (fila["id"],))
            conn.commit()
            mensaje = "✅ Cuenta verificada con éxito. ¡Gracias!"
            estado = "success"
        except:
            mensaje = "⚠️ Error al validar. Intente más tarde."
            estado = "error"
    else:
        mensaje = "❌ Token inválido o ya fue utilizado."
        estado = "error"

    conn.close()
    return templates.TemplateResponse("validar.html", {
        "request": request,
        "mensaje": mensaje,
        "status": estado
    })
    
@router.get("/login", response_class=HTMLResponse)
def mostrar_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def procesar_login(datos: dict):
    email = datos.get("email")
    celular = datos.get("celular")

    if not email or not celular:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Faltan datos"})

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre FROM usuarios
        WHERE email = ? AND celular = ? AND token_validacion IS NULL
    """, (email, celular))
    usuario = cur.fetchone()
    conn.close()

    if usuario:
        return {"ok": True, "mensaje": f"Bienvenido {usuario['nombre']} 🎉"}
    else:
        return JSONResponse(status_code=401, content={
            "ok": False,
            "detail": "Credenciales inválidas o cuenta no validada."
        })    
        
@router.post("/login")
def procesar_login(datos: dict):
    email = datos.get("email")
    celular = datos.get("celular")

    if not email or not celular:
        return JSONResponse(status_code=400, content={"ok": False, "detail": "Faltan datos"})

    conn = conectar_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, nombre, id_rol FROM usuarios
        WHERE email = ? AND celular = ? AND token_validacion IS NULL
    """, (email, celular))
    usuario = cur.fetchone()
    conn.close()

    if usuario:
        response = RedirectResponse(url="/perfil", status_code=302)
        response.set_cookie(
            key="usuario_id",
            value=usuario["id"],
            httponly=True,
            max_age=60*60*24,  # 1 día
        )
        return response
    else:
        return JSONResponse(status_code=401, content={
            "ok": False,
            "detail": "Credenciales inválidas o cuenta no validada."
        })
        
@router.get("/perfil", response_class=HTMLResponse)
def ver_perfil(request: Request):
    usuario = request.state.usuario
    if not usuario:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse("perfil.html", {
        "request": request,
        "usuario": usuario
    })
    
@router.get("/logout")
def cerrar_sesion():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("usuario_id")
    return response                  

@router.get("/dashboard", response_class=HTMLResponse)
def ver_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "usuario": {"nombre": "Invitado", "rol": "guest"}  # Datos ficticios si querés mostrar algo
    })