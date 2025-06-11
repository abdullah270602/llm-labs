import os
from jose import jwt
from datetime import datetime, timedelta

ALGORITHM = "HS256"

def create_access_token(user: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = {
        "sub": user["id"],
        "email": user["email"],
        "username": user["username"]
    }

    expire = datetime.utcnow() + expires_delta
        
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, os.getenv("JWT_SECRET_KEY"), algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(str(token), os.getenv("JWT_SECRET_KEY"), algorithms=[ALGORITHM])
        return payload if "exp" in payload and datetime.utcnow() < datetime.fromtimestamp(payload["exp"]) else None
    except Exception as e:
        print(str(e)) #TODO handle exception properly
        return False
