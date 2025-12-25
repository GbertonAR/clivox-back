import smtplib
from email.message import EmailMessage

def enviar_mail_validacion(destinatario_email: str, nombre: str, token: str):
    remitente = "gbertonnft@gmail.com"
    clave_app = "sezs ksmi nucy gowi"

    msg = EmailMessage()
    msg['Subject'] = "Confirmación de cuenta - ANSV"
    msg['From'] = remitente
    msg['To'] = destinatario_email

    enlace = f"http://127.0.0.1:8000/validar?token={token}"
    msg.set_content(f"""
        Hola {nombre},

        Gracias por registrarte en el sistema de ANSV.

        Por favor confirmá tu cuenta haciendo clic en el siguiente enlace:
        {enlace}

        Si no realizaste este registro, ignorá este mensaje.
        """, charset='utf-8')

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(remitente, clave_app)
            smtp.send_message(msg)
        print("📬 Correo de validación enviado.")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")
