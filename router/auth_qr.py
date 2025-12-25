from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import sqlite3
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import qrcode
import io

router = APIRouter()
DB_PATH = "clivox.db"

# 📦 Leer parámetros desde la tabla parametros_seteos
def get_param(nombre: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM parametros_seteos WHERE clave = ?", (nombre,))
    result = cursor.fetchone()
    conn.close()
    if not result:
        raise HTTPException(status_code=500, detail=f"Parámetro '{nombre}' no encontrado en la base")
    return result[0]

# 📩 Solicita código de verificación (envía QR y mail)
class SolicitudCodigo(BaseModel):
    email: str

@router.post("/auth/solicitar-codigo")
def solicitar_codigo(data: SolicitudCodigo):
    codigo = str(uuid4())[:6].upper()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO codigos_verificacion (email, codigo, timestamp, usado)
        VALUES (?, ?, ?, 0)
    """, (data.email, codigo, datetime.now()))
    conn.commit()
    conn.close()

    # 🔗 URL de verificación para el QR
    qr_url = f"https://clivox-admin.vercel.app/verificar-qr?codigo={codigo}"

    # 🖼️ Generar imagen QR
    qr = qrcode.make(qr_url)
    img_buffer = io.BytesIO()
    qr.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # ✉️ Armar email con imagen QR
    msg = MIMEMultipart("related")
    msg["Subject"] = "Código de validación - Clivox Admin"
    msg["From"] = get_param("EMAIL_USERNAME")
    msg["To"] = data.email

    html = f"""
    <html>
        <body>
            <p>Hola,<br><br>
            Tu código de validación es: <b>{codigo}</b><br><br>
            También podés escanear este código QR:<br><br>
            <img src="cid:qrimage"><br><br>
            O hacé clic en este <a href="{qr_url}">enlace</a> desde tu celular.<br><br>
            Gracias,<br>
            Equipo Clivox
            </p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    image = MIMEImage(img_buffer.read(), name="qr.png")
    image.add_header("Content-ID", "<qrimage>")
    msg.attach(image)

    # 📤 Enviar email real con configuración desde la base
    try:
        smtp_host = get_param("EMAIL_SENDER")
        smtp_port = int(get_param("EMAIL_PORT"))
        smtp_user = get_param("EMAIL_USERNAME")
        smtp_pass = get_param("EMAIL_PASSWORD")

        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando correo: {e}")

    return {"mensaje": "Código enviado correctamente", "codigo": codigo}

# 🔍 Verifica si el código es válido (desde QR o link)
@router.get("/auth/verificar-qr")
def verificar_qr(codigo: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email, usado FROM codigos_verificacion WHERE codigo = ?", (codigo,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Código inválido")

    email, usado = row
    if usado:
        raise HTTPException(status_code=400, detail="Código ya utilizado")

    return {"email": email}

# 📲 Completa la verificación registrando el celular y bloqueando el código
class ConfirmacionQR(BaseModel):
    codigo: str
    celular: str

@router.post("/auth/completar-verificacion")
def completar_verificacion(data: ConfirmacionQR):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM codigos_verificacion WHERE codigo = ? AND usado = 0", (data.codigo,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Código inválido o ya utilizado")

    email = result[0]

    # Asegurarse de que el usuario exista
    cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (email) VALUES (?)", (email,))

    # Guardar celular y marcar código como usado
    cursor.execute("UPDATE usuarios SET celular = ? WHERE email = ?", (data.celular, email))
    cursor.execute("UPDATE codigos_verificacion SET usado = 1, timestamp_validado = ? WHERE codigo = ?",
                   (datetime.now(), data.codigo))

    conn.commit()
    conn.close()

    return {"mensaje": "Verificación completada con éxito"}
