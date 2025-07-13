# data/routers/communication.py

from fastapi import APIRouter
from azure.communication.identity import CommunicationIdentityClient
import os

router = APIRouter()

# Cargar el connection string desde variables de entorno
ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")

@router.get("/acs/token")
def generate_acs_token():
    try:
        client = CommunicationIdentityClient.from_connection_string(ACS_CONNECTION_STRING)
        user = client.create_user()
        token_response = client.get_token(user, scopes=["chat"])
        return {
            "user_id": user.properties["id"],
            "token": token_response.token,
            "expires_on": token_response.expires_on  # Ya es string
        }
    except Exception as e:
        return {"error": str(e)}
