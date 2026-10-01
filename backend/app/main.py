from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.media import MEDIA_URL_PREFIX, get_media_root
from app.routers import ankieta, auth, kursy, nauka, uzytkownicy

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

app.include_router(auth.router)
app.include_router(uzytkownicy.router)
app.include_router(ankieta.router)
app.include_router(kursy.router)
app.include_router(nauka.router)

# Uploaded images / recordings
_media_root = get_media_root()
_media_root.mkdir(parents=True, exist_ok=True)
app.mount(MEDIA_URL_PREFIX, StaticFiles(directory=_media_root), name="media")


@app.get("/")
def powitanie():
    return {
        "status": "success",
        "wiadomosc": "Serwer działa."
    }
