# app/auth/dependencies.py
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.auth.utils import decode_access_token
from psycopg2.extensions import connection as PGConnection

from app.database.auth_queries import create_user, get_user_by_email


security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


def get_or_create_user(conn: PGConnection, email: str, name: str):
    user = get_user_by_email(conn, email)
    if user:
        return user
    return create_user(conn, email, name)