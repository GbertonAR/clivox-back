import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

ACS_ENDPOINT = os.getenv("ACS_ENDPOINT", "https://acs-ansv-chat.unitedstates.communication.azure.com")
BOT_TOKEN = os.getenv("BOT_TOKEN")
THREAD_ID = os.getenv("THREAD_ID")
BOT_ID = os.getenv("BOT_ID")
#BACKEND_BOT_URL = "http://127.0.0.1:8000/api/messages"
BACKEND_BOT_URL = os.getenv("BACKEND_BOT_URL", "https://clivox-backend-cea4bzfcahbpf9fw.westus-01.azurewebsites.net/api/messages")

last_message_ids = set()

headers = {
    "Authorization": f"Bearer {BOT_TOKEN}",
    "Content-Type": "application/json"
}

print(f"🤖 Bot ANSV conectado al thread: {THREAD_ID}")

while True:
    try:
        # Obtener mensajes
        url = f"{ACS_ENDPOINT}/chat/threads/{THREAD_ID}/messages?api-version=2021-09-07"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"❌ Error al obtener mensajes: {response.status_code} - {response.text}")
            time.sleep(5)
            continue

        messages = response.json().get("value", [])

        for msg in messages:
            msg_id = msg["id"]
            sender_id = msg["senderCommunicationIdentifier"].get("rawId")

            if msg_id in last_message_ids or sender_id == BOT_ID:
                continue

            user_text = msg["content"]["message"]
            print(f"📨 Mensaje recibido: {user_text}")

            # Enviar mensaje al bot ANSV
            try:
                ansv_response = requests.post(BACKEND_BOT_URL, json={"message": user_text})
                ansv_reply = ansv_response.json().get("response", "No entendí la consulta.")
            except Exception as e:
                ansv_reply = f"[Error al conectar con ANSV]: {str(e)}"

            print(f"🤖 Respondiendo: {ansv_reply}")

            # Enviar respuesta al chat
            send_url = f"{ACS_ENDPOINT}/chat/threads/{THREAD_ID}/messages?api-version=2021-09-07"
            send_body = {
                "content": ansv_reply,
                "senderDisplayName": "Bot ANSV",
                "type": "text"
            }
            send_response = requests.post(send_url, json=send_body, headers=headers)

            if send_response.status_code != 201:
                print(f"⚠️ Error al enviar mensaje: {send_response.status_code} - {send_response.text}")

            last_message_ids.add(msg_id)

        time.sleep(5)

    except Exception as e:
        print(f"🔥 Error general: {str(e)}")
        time.sleep(5)
