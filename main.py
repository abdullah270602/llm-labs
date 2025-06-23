import logging
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.constants import ALLOWED_ORIGINS
from app.routes.chats import router as chat_router
from app.routes.models import router as model_router
from app.routes.workspaces import router as workspaces_router
from app.routes.movements import router as movements_router
from app.routes.folders import router as folders_router
from app.routes.auth import router as auth_router
from dotenv import load_dotenv
from starlette.middleware.sessions import SessionMiddleware
import os

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv(override=True)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET_KEY")  # TODO change keys
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )


@app.get("/")
def read_root():
    return {"Labmise Backend V1": "Online 👍"}

app.include_router(model_router)
app.include_router(chat_router)
app.include_router(workspaces_router)
app.include_router(folders_router)
app.include_router(movements_router)
app.include_router(auth_router)

