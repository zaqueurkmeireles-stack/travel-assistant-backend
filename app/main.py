from dotenv import load_dotenv
# O load_dotenv() PRECISA vir antes de importar o supabase_client
load_dotenv()

import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.auth import AuthContext, get_auth_context

app = FastAPI(title="Travel Assistant Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/webhook/message")
async def webhook_message(payload: dict, auth: AuthContext = Depends(get_auth_context)) -> dict:
    return {
        "status": "received",
        "user_id": auth.user_id,
        "trip_id": auth.trip_id,
        "role": (auth.trip_context or {}).get("user_role"),
    }
