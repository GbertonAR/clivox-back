from fastapi import APIRouter
from azure.communication.identity import CommunicationIdentityClient
from datetime import timedelta
import os
import requests

router = APIRouter()

@router.post("/acs/create-thread-bot")
def create_thread_bot():
    connection_str = os.getenv("ACS_CONNECTION_STRING")
    endpoint = os.getenv("ACS_ENDPOINT")

    # Crear identidad y token
    identity_client = CommunicationIdentityClient.from_connection_string(connection_str)
    identity_token_result = identity_client.create_user_and_token(scopes=["chat"])
    user = identity_token_result[0]
    token = identity_token_result[1].token
    user_id = user.properties["id"]

    # Crear thread usando REST API
    url = f"{endpoint}/chat/threads?api-version=2021-09-07"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    body = {
        "topic": "Clase ANSV",
        "participants": [
            {
                "id": user_id,
                "displayName": "Bot ANSV"
            }
        ]
    }

    resp = requests.post(url, headers=headers, json=body)
    resp.raise_for_status()
    thread_id = resp.json()["chatThread"]["id"]

    return {
        "thread_id": thread_id,
        "bot_user_id": user_id,
        "bot_token": token
    }
