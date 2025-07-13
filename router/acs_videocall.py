from fastapi import APIRouter
from azure.communication.identity import CommunicationIdentityClient
import os

router = APIRouter()

@router.get("/api/videocall-info")
def get_videocall_info():
    connection_str = os.getenv("ACS_CONNECTION_STRING")
    endpoint = os.getenv("ACS_ENDPOINT")

    if not connection_str or not endpoint:
        return {"error": "ACS config missing"}

    identity_client = CommunicationIdentityClient.from_connection_string(connection_str)
    user = identity_client.create_user()
    token_response = identity_client.get_token(user, scopes=["voip"])

    return {
        "user_id": user.properties["id"],
        "display_name": "Instructor CLIVOX",
        "token": token_response.token,
        "thread_id": "00000000-0000-0000-0000-000000000000"  # ¡lo cambiamos más adelante!
    }
