from fastapi import APIRouter, Request
from app.auth.dependencies import get_or_create_user
from app.auth.google_auth import oauth, get_google_user_info
from app.auth.utils import create_access_token
from app.database.connection import PostgresConnection

router = APIRouter(tags=["auth"])

@router.get("/google/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    user_info = await get_google_user_info(request)
    email = user_info["email"]
    name = user_info.get("name", "")

    with PostgresConnection() as conn:
        user = get_or_create_user(conn, email, name)
    
    
    sanitized_user = {
    "id": str(user["id"]),
    "email": user["email"],
    "username": user["username"],
    }
    
    token = create_access_token(sanitized_user)

    return {"access_token": token, "token_type": "bearer"}

