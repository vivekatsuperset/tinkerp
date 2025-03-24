import os

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from google.auth.transport import requests
from google.oauth2 import id_token

from symmetri.api.domain.users import User
from symmetri.api.server.models import TokenExchangeRequest
from symmetri.api.services.user_management import UserManagementService
from symmetri.symmetri_logger import logger

router = APIRouter()


@router.post("/v1/auth/google-token")
async def google_token_exchange(request: TokenExchangeRequest):
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    try:
        id_info = id_token.verify_oauth2_token(
            id_token=request.id_token,
            request=requests.Request(),
            audience=google_client_id,
        )
        logger.info(id_info)
        logger.info(id_info["aud"])
        logger.info(google_client_id)

        if id_info["aud"] != google_client_id:
            raise ValueError("Could not verify audience.")

        user = UserManagementService().create_user(User.from_google_user_data(id_info))
        logger.info("Token is valid. User info:", id_info)
        return {
            'email': user.email,
            'name': user.name,
            'db_id': user.user_id,
            'partner_user_id': user.partner_user_id,
            'is_admin': user.is_admin
        }
    except ValueError as e:
        print("Invalid token:", e)
        return None


@router.options("/v1/auth/google-token")
async def google_auth_options(request: TokenExchangeRequest):
    logger.info(request)
    allowed_methods = ["POST", "OPTIONS"]
    headers = {
        "Allow": ", ".join(allowed_methods)
    }
    return JSONResponse(content=None, headers=headers)
