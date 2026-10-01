from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import kursy

app = FastAPI(title="StylNauki API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kursy.router)


@app.get("/")
def powitanie():
    return {
        "status": "success",
        "wiadomosc": "Serwer działa."
    }
