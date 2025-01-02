from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from app.constants import ALLOWED_ORIGINS
from app.routes.chats import router as chat_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Labmise Backend V1": "Online 👍"}


app.include_router(chat_router)


