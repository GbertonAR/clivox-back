
# auth_routes.py
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import secrets
import string
import smtplib
from email.message import EmailMessage
from pydantic import BaseModel, EmailStr

class EmailRequest(BaseModel):
    email: EmailStr
    
    
class CodigoVerificacion(BaseModel):
    email: EmailStr
    codigo: str    

router = APIRouter(prefix="", tags=["auth-login"])
templates = Jinja2Templates(directory="data/templates")

# === CONFIGURACIÓN DE EMAIL ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "gbertonnft@gmail.com"  # cambiar a una cuenta válida
SMTP_PASSWORD = "sezs ksmi nucy gowi"  # usar contraseña de app segura o variable de entorno

# === UTILS ===
def generar_codigo(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def enviar_codigo_por_email(destinatario: str, codigo: str):
    msg = EmailMessage()
    msg["Subject"] = "Código de verificación - ANSV Bot"
    msg["From"] = SMTP_USER
    msg["To"] = destinatario
    msg.set_content(f"Tu código de verificación es: {codigo}\n\nIngresalo en el formulario para acceder al asistente.")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

# === RUTAS ===
@router.get("/login", response_class=HTMLResponse)
def mostrar_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def procesar_login(request: Request, email: EmailStr = Form(...)):
    conn = sqlite3.connect("../clivox.db")
    cur = conn.cursor()

    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    usuario = cur.fetchone()

    if usuario:
        codigo = generar_codigo()
        cur.execute("INSERT INTO codigos_verificacion (email, codigo) VALUES (?, ?)", (email, codigo))
        conn.commit()
        enviar_codigo_por_email(email, codigo)
        conn.close()
        return RedirectResponse(url=f"/validar-codigo?email={email}", status_code=status.HTTP_302_FOUND)
    else:
        conn.close()
        return RedirectResponse(url="/registro", status_code=status.HTTP_302_FOUND)

@router.post("/auth/enviar-codigo_acs")
#def api_enviar_codigo(email: EmailStr = Form(...)):
def api_enviar_codigo(payload: EmailRequest):
    email = payload.email
    print(f"Recibido email para enviar código: {email}")    

    conn = sqlite3.connect("../clivox.db")
    cur = conn.cursor()

    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    usuario = cur.fetchone()

    print(f"Usuario encontrado: {usuario}")
    if usuario:
        codigo = generar_codigo()
        print(f"Generado código: {codigo} para email: {email}")
        cur.execute("INSERT INTO codigos_verificacion (email, codigo) VALUES (?, ?)", (email, codigo))
        conn.commit()
        enviar_codigo_por_email(email, codigo)
        conn.close()
        return JSONResponse(content={"ok": True, "mensaje": "Código enviado correctamente."})
    else:
        conn.close()
        return JSONResponse(content={"ok": False, "error": "Usuario no encontrado."}, status_code=404)

@router.get("/validar-codigo_acs", response_class=HTMLResponse)
def mostrar_validacion(request: Request, email: str):
    return templates.TemplateResponse("validacodigo.tsx", {"request": request, "email": email})

# @router.post("/auth/validar-codigo")
# #def validar_codigo(request: Request, email: str = Form(...), codigo: str = Form(...)):
# def validar_codigo(request: Request, datos: CodigoVerificacion):
#     print (f"Validando código para email: {datos.email} con código: {datos.codigo}")
#     email = datos.email
#     codigo = datos.codigo
        
#     conn = sqlite3.connect("data/soporte_db.db")
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM codigos_verificacion WHERE email = ? AND codigo = ?", (email, codigo))
#     resultado = cur.fetchone()

#     if resultado:
#         cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
#         usuario = cur.fetchone()
#         conn.close()

#         response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
#         response.set_cookie("usuario_id", str(usuario[0]), max_age=86400)  # 1 día
#         return response
#     else:
#         conn.close()
#         return templates.TemplateResponse("validar_codigo.html", {
#             "request": request,
#             "email": email,
#             "error": "❌ Código incorrecto. Intentalo nuevamente."
#         })

@router.post("/auth/validar-codigo_acs")
def validar_codigo(datos: CodigoVerificacion):
    print (f"Validando código para email: {datos.email} con código: {datos.codigo}")
    email = datos.email
    codigo = datos.codigo
        
    conn = sqlite3.connect("../clivox.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM codigos_verificacion WHERE email = ? AND codigo = ?", (email, codigo))
    resultado = cur.fetchone()

    if resultado:
        # OPCIONAL: marcar el código como usado
        cur.execute("""
            UPDATE codigos_verificacion 
            SET usado = 1, timestamp_validado = CURRENT_TIMESTAMP 
            WHERE email = ? AND codigo = ?
        """, (email, codigo))

        cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario = cur.fetchone()
        conn.commit()
        conn.close()

        return JSONResponse(
            content={"success": True, "usuario_id": usuario[0], "redirect_url": "/"},
            status_code=200
        )
    else:
        conn.close()
        return JSONResponse(
            content={"success": False, "error": "Código incorrecto. Inténtalo nuevamente."},
            status_code=401
        )
        
# data/auth_routes.py
@router.get("/api/mi-perfil_acs")
def obtener_perfil(request: Request):
    usuario_id = request.cookies.get("usuario_id")
    if not usuario_id:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})

    conn = sqlite3.connect("../clivox.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT u.nombre, p.Nombre AS provincia, m.Nombre AS municipio
        FROM usuarios u
        LEFT JOIN Municipios m ON u.id_municipio = m.ID
        LEFT JOIN Provincias p ON m.Id_Provincia = p.ID
        WHERE u.id = ?
    """, (usuario_id,))
    usuario = cur.fetchone()
    conn.close()

    if usuario:
        return {
            "nombre": usuario[0],
            "provincia": usuario[1] or "Sin asignar",
            "municipio": usuario[2] or "Sin asignar",
        }
    return JSONResponse(status_code=404, content={"error": "Usuario no encontrado"})
        