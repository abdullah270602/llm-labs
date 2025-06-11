import os
from jose import jwt
from datetime import datetime, timedelta

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
    except Exception:
        return None
