from fastapi import APIRouter
from azure.communication.identity import CommunicationIdentityClient
import os

router = APIRouter()

@router.post("/token")
def generate_acs_token():
    try:
        conn_str = os.getenv("ACS_CONNECTION_STRING")
        if not conn_str:
            return {"error": "ACS_CONNECTION_STRING not configured."}

        client = CommunicationIdentityClient.from_connection_string(conn_str)

        token_response = client.create_user_and_token(scopes=["voip"])
        identity = token_response[0]
        token = token_response[1]

        return {
            "user_id": identity.properties["id"],
            "token": token.token,
            "expires_on": str(token.expires_on)  # ✅ corregido
        }
        
    except Exception as e:
        print("❌ Error generando token:", str(e))
        return {"error": str(e)}
