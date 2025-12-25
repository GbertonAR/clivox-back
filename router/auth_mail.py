# data/auth_mail.py
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
import sqlite3
import secrets
import string
import smtplib
from email.message import EmailMessage
import qrcode
import io
from base64 import b64encode
from email.mime.image import MIMEImage
from datetime import datetime

router = APIRouter(prefix="", tags=["auth-login"])
templates = Jinja2Templates(directory="data/templates")

# === CONFIGURACIÓN DE EMAIL ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "gbertonnft@gmail.com"  # cambiar por variable de entorno en producción
SMTP_PASSWORD = "sezs ksmi nucy gowi"

# === CONSTANTE DE DB ===
DB_PATH = "clivox.db"  # Cambiar según la ubicación de tu base de datos

# === MODELOS ===
class EmailRequest(BaseModel):
    email: EmailStr

class CodigoVerificacion(BaseModel):
    email: EmailStr
    codigo: str

# === UTILS ===
def generar_codigo(longitud=6):
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def enviar_codigo_por_email(destinatario: str, codigo: str):
    # msg = EmailMessage()
    # msg["Subject"] = "Código de verificación - Acceso al stremming"
    # msg["From"] = SMTP_USER
    # msg["To"] = destinatario
    # msg.set_content(f"Tu código de verificación es: {codigo}\n\nIngresalo en el formulario para acceder al asistente.")
    
    # Generar link con email y código
    link_verificacion = f"https://localhost:5174/verificar?email={destinatario}&codigo={codigo}"

    # Crear contenido del QR
    contenido_qr = f"{link_verificacion}"

    # Generar QR en memoria
    qr = qrcode.make(contenido_qr)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_data = buffer.getvalue()
    img_base64 = b64encode(img_data).decode("utf-8")

    # Crear el correo
    msg = EmailMessage()
    msg["Subject"] = "Código de verificación - Acceso al streaming"
    msg["From"] = SMTP_USER
    msg["To"] = destinatario

    # HTML con QR embebido
    html_content = f"""
    <html>
    <body>
        <p>Tu código de verificación es: <strong>{codigo}</strong></p>
        <p>Escaneá este código QR desde tu celular para verificar automáticamente:</p>
        <img src="cid:qr_code">
        <p>O hacé clic directamente en el siguiente enlace:<br>
        <a href="{link_verificacion}">{link_verificacion}</a></p>
    </body>
    </html>
    """
    msg.set_content(f"Tu código de verificación es: {codigo}\n\nIngresalo en el formulario o escaneá el QR.")
    msg.add_alternative(html_content, subtype="html")

    # Adjuntar la imagen QR
    img = MIMEImage(img_data)
    img.add_header("Content-ID", "<qr_code>")
    img.add_header("Content-Disposition", "inline", filename="qr.png")
    msg.get_payload()[1].add_related(img, "image", "png", cid="qr_code")    
    

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
    conn = sqlite3.connect(DB_PATH)
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
def api_enviar_codigo(payload: EmailRequest):
    email = payload.email
    print(f"Recibido email para enviar código: {email}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    usuario = cur.fetchone()

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
        return RedirectResponse(url="/registro", status_code=status.HTTP_302_FOUND)
       #s return JSONResponse(content={"ok": False, "error": "Usuario no encontrado."}, status_code=404)
    
    
    

@router.post("/auth/validar-codigo_acs")
def validar_codigo(datos: CodigoVerificacion):
    print (f"Validando código para email: {datos.email} con código: {datos.codigo}")
    email = datos.email
    codigo = datos.codigo
    print(f"Validando código: {codigo} para email: {email}")
    conn = sqlite3.connect("clivox.db")
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

        cur.execute("SELECT id, id_rol FROM usuarios WHERE email = ?", (email,))
        usuario = cur.fetchone()
        conn.commit()
        conn.close()
        dashboard = "http://localhost:5174/usuarios"

        if usuario:
            usuario_id, id_rol = usuario # Desempaqueta el usuario aquí
            redirect_path = "/dashboard" # Valor por defecto, si no coincide ningún rol específico
            
            print(f"Usuario ID: {usuario_id}") # Log para depuración
            print(f"ID Rol: {id_rol}") # Log para depuración

            if id_rol == 5: # Rol de Instructor
                # CAMBIO: Solo la ruta relativa, y asegúrate de incluir el ID del usuario si la ruta lo espera
                redirect_path = f"/InstructorDashboard/{usuario_id}" 
            elif id_rol == 1: # Rol de Admin/Usuario principal
                # CAMBIO: Solo la ruta relativa, y asegúrate de incluir el ID del usuario si la ruta lo espera
                # Tu frontend en App.tsx tiene <Route path="/usuarios/:id" ... />
                # Entonces necesitas pasar el ID aquí.
                redirect_path = f"/usuarios/{usuario_id}" 
            # Agregá más casos según necesidad para otros roles (ej. if id_rol == X: redirect_path = "/otra_ruta")
            print(f"Redirigiendo a: {redirect_path}") # Log para depuración
            return JSONResponse(
                content={
                "success": True,
                "usuario_id": usuario_id, # Esto ahora será el ID real del usuario
                "id_rol": id_rol,
                "redirect_url": redirect_path # ¡AHORA ES LA RUTA RELATIVA CORRECTA!
                },
                status_code=200
            )
            
            
            
    else:
        conn.close()
        return JSONResponse(
            content={"success": False, "error": "Código incorrecto. Inténtalo nuevamente."},
            status_code=401
        )
      


# ⚠️ Ruta HTML innecesaria si usás React
# @router.get("/validar-codigo_acs", response_class=HTMLResponse)
# def mostrar_validacion(request: Request, email: str):
#     print("ver si pasas por aca {email}")
#     return templates.TemplateResponse("http://localhost:5174/validacodigo.tsx", {"request": request, "email": email})

# @router.post("/auth/validar-codigo_acs")
# def validar_codigo(datos: CodigoVerificacion):
#     print(f"Validando código para email: {datos.email} con código: {datos.codigo}")
#     email = datos.email
#     codigo = datos.codigo

#     conn = sqlite3.connect(DB_PATH)
#     cur = conn.cursor()

#     cur.execute("SELECT * FROM codigos_verificacion WHERE email = ? AND codigo = ?", (email, codigo))
#     resultado = cur.fetchone()

#     if resultado:
#         cur.execute("""
#             UPDATE codigos_verificacion 
#             SET usado = 1, timestamp_validado = CURRENT_TIMESTAMP 
#             WHERE email = ? AND codigo = ?
#         """, (email, codigo))

#         cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
#         usuario = cur.fetchone()
#         conn.commit()
#         conn.close()

#         return JSONResponse(
#             content={"success": True, "usuario_id": usuario[0], "redirect_url": "/"},
#             status_code=200
#         )
#     else:
#         conn.close()
#         return JSONResponse(
#             content={"success": False, "error": "Código incorrecto. Inténtalo nuevamente."},
#             status_code=401
#         )

@router.get("/api/mi-perfil_acs")
def obtener_perfil(request: Request):
    usuario_id = request.cookies.get("usuario_id")
    if not usuario_id:
        return JSONResponse(status_code=401, content={"error": "No autenticado"})

    conn = sqlite3.connect(DB_PATH)
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

#@router.post("/auth/verificar-codigo-desde-qr")
# async def verificar_codigo_qr(request: Request):
#     data = await request.json()
#     email = data.get("email")

#     conn = sqlite3.connect("clivox.db")
#     cur = conn.cursor()
#     cur.execute("SELECT codigo, usado, usuario_id FROM codigos_verificacion WHERE email = ?", (email,))
#     row = cur.fetchone()
#     conn.close()

#     if row and row[1]:  # validado = True
#         return {"success": True, "usuario_id": row[2]}
#     return {"success": False}
@router.post("/auth/verificar-codigo-desde-qr")
def validar_codigo(email: str, codigo_ingresado: str):
    conn = sqlite3.connect("soporte_db.db")
    cur = conn.cursor()
    
    cur.execute("SELECT codigo, usado, timestamp_validado, usuario_id FROM codigos_verificacion WHERE email = ?", (email,))
    row = cur.fetchone()

    if row and row[0] == codigo_ingresado and row[1] == 0:
        # Marcar como usado y guardar fecha de validación
        timestamp_actual = datetime.utcnow().isoformat()
        cur.execute("""
            UPDATE codigos_verificacion
            SET usado = 1,
                timestamp_validado = ?
            WHERE email = ?
        """, (timestamp_actual, email))
        conn.commit()
        conn.close()
        return {"success": True, "usuario_id": row[3]}
    
    conn.close()
    return {"success": False}