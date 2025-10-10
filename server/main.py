import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from sqlmodel import select
from server.db import init_db, get_session
from server.models import Seal

USE_S3 = os.getenv("USE_S3", "0") == "1"

app = FastAPI()

app.mount("/assets", StaticFiles(directory="server/seal_assets"), name="assets")
app.mount("/uploads", StaticFiles(directory="server/uploads"), name="uploads")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/upload-local")
def upload_local(file: UploadFile = File(...)):
    from server.local_storage import save_png
    url = save_png(file)
    return {"image_path": url}

@app.post("/submit-seal")
def submit_seal(payload: dict):
    if not (1 <= payload["eyes"] <= 12): raise HTTPException(422, "eyes 1..12")
    if not (1 <= payload["mouth"] <= 4): raise HTTPException(422, "mouth 1..4")
    if not (0 <= payload["hair"] <= 3): raise HTTPException(422, "hair 0..3")
    if not (2 <= payload["pattern"] <= 5): raise HTTPException(422, "pattern 2..5")
    if not (1 <= payload["base_color"] <= 20): raise HTTPException(422, "base_color 1..20")
    if not (1 <= payload["pattern_color"] <= 20): raise HTTPException(422, "pattern_color 1..20")

    seal = Seal(**payload)
    with get_session() as s:
        s.add(seal)
        s.commit()
        s.refresh(seal)
    return {"id": seal.id}

@app.get("/seals")
def list_seals(limit: int = 50, offset: int = 0):
    with get_session() as s:
        q = select(Seal).order_by(Seal.id.desc()).limit(limit).offset(offset)
        return s.exec(q).all()

@app.post("/predict")
def predict(body: dict):
    base = 10000 + body["eyes"]*500 + body["mouth"]*400 + body["hair"]*250 + (body["pattern"]-1)*700
    color_bonus = (body["base_color"] + body["pattern_color"]) * 10
    return {"predicted_value": float(base + color_bonus)}
