from fastapi import APIRouter
import os
from azure.communication.identity import CommunicationIdentityClient
from azure.communication.chat import ChatClient, ChatParticipant
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING")
ACS_ENDPOINT = "https://acs-ansv-chat.unitedstates.communication.azure.com"

@router.post("/acs/create-thread-bot")
def create_thread_with_bot():
    try:
        identity_client = CommunicationIdentityClient.from_connection_string(ACS_CONNECTION_STRING)
        bot_user = identity_client.create_user()
        bot_token = identity_client.get_token(bot_user, scopes=["chat"])

        chat_client = ChatClient(
            endpoint=ACS_ENDPOINT,
            credential=CommunicationTokenCredential(bot_token.token)
        )

        bot_participant = ChatParticipant(
            identifier=bot_user,
            display_name="Bot ANSV",
            share_history_time=None
        )

        create_thread_result = chat_client.create_chat_thread(
            topic="Clase en línea - ANSV",
            participants=[bot_participant]
        )

        thread_id = create_thread_result.chat_thread.id

        return {
            "thread_id": thread_id,
            "bot_user_id": bot_user.properties["id"],
            "bot_token": bot_token.token,
            "bot_expires_on": bot_token.expires_on
        }

    except Exception as e:
        return {"error": str(e)}
