import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Literal, cast
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from sqlalchemy import desc
from server.db import init_db, get_session
from server.models import Seal

USE_S3 = os.getenv("USE_S3", "0") == "1"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME") or os.getenv("S3_BUCKET") or ""
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

def s3_url(key: str) -> str:
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}".replace("//", "/").replace("https:/", "https://")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# CORS
allow_origins = ["*"] if CORS_ORIGINS.strip() == "*" else [o.strip() for o in CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="server/seal_assets"), name="assets")
app.mount("/uploads", StaticFiles(directory="server/uploads"), name="uploads")

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/upload-local")
def upload_local(file: UploadFile = File(...)):
    from server.local_storage import save_png
    url = save_png(file)
    return {"image_path": url}

@app.get("/options")
def options() -> Dict[str, List[int]]:
    return {
        "eyes": list(range(1, 7)),
        "mouth": list(range(1, 5)),
        "hair": [0, 1, 2, 3], # 0 = none
        "pattern": list(range(1, 5)),
        "color": list(range(1, 21)),
    }

@app.post("/preview-urls")
def preview_urls(body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns the ordered layer keys as well as full URLs to SVG assets on S3 for the chosen traits.
    It expects:
      eyes (1 to 6), mouth(1 to 4), hair(0 to 3 - since 0 is no hair), pattern(1 to 4),
      base_color(1 to 20), pattern_color(1 to 20),
      eyes_tint_source: "base" | "pattern"
    """
    required = ["eyes", "mouth", "hair", "pattern", "base_color", "pattern_color"]
    for k in required:
        if k not in body:
            raise HTTPException(422, f"missing field: {k}")

    eyes = int(body["eyes"])
    mouth = int(body["mouth"])
    hair = int(body["hair"])
    pattern = int(body["pattern"])
    base_color = int(body["base_color"])
    pattern_color = int(body["pattern_color"])

    if not (1 <= eyes <= 6): raise HTTPException(422, "eyes 1..6")
    if not (1 <= mouth <= 4): raise HTTPException(422, "mouth 1..4")
    if not (0 <= hair <= 3): raise HTTPException(422, "hair 0..3 (0 = none)")
    if not (1 <= pattern <= 4): raise HTTPException(422, "pattern 1..4")
    if not (1 <= base_color <= 20): raise HTTPException(422, "base_color 1..20")
    if not (1 <= pattern_color <= 20): raise HTTPException(422, "pattern_color 1..20")

    eyes_color = base_color

    layers: List[str] = []
    urls: Dict[str, str] = {}

    body_key = f"seal_assets/SealBody/{base_color}.svg"
    layers.append("body")
    urls["body"] = s3_url(body_key)

    pattern_key = f"seal_assets/SealPattern{pattern}/{pattern_color}.svg"
    layers.append("pattern")
    urls["pattern"] = s3_url(pattern_key)

    mouth_key = f"seal_assets/SealMouth{mouth}/{base_color}.svg"
    layers.append("mouth")
    urls["mouth"] = s3_url(mouth_key)

    eyes_key = f"seal_assets/SealEyes{eyes}/{eyes_color}.svg"
    layers.append("eyes")
    urls["eyes"] = s3_url(eyes_key)

    if hair != 0:
        hair_key = f"seal_assets/SealHair{hair}/{base_color}.svg"
        layers.append("hair")
        urls["hair"] = s3_url(hair_key)

    return {"layers": layers, "urls": urls}

@app.post("/submit-seal")
def submit_seal(payload: Dict[str, Any]):
    if not (1 <= payload["eyes"] <= 6):
        raise HTTPException(422, "eyes 1..6")
    if not (1 <= payload["mouth"] <= 4):
        raise HTTPException(422, "mouth 1..4")
    if not (0 <= payload["hair"] <= 3):
        raise HTTPException(422, "hair 0..3 (0 = no hair)")
    if not (1 <= payload["pattern"] <= 4):
        raise HTTPException(422, "pattern 1..4")
    if not (1 <= payload["base_color"] <= 20):
        raise HTTPException(422, "base_color 1..20")
    if not (1 <= payload["pattern_color"] <= 20):
        raise HTTPException(422, "pattern_color 1..20")

    seal = Seal(**payload)
    with get_session() as s:
        s.add(seal)
        s.commit()
        s.refresh(seal)
    return {"id": seal.id}

@app.get("/seals")
def list_seals(limit: int = 50, offset: int = 0):
    with get_session() as s:
        q = (
            select(Seal)
            .order_by(desc(cast(Any, Seal.id)))
            .limit(limit)
            .offset(offset)
        )
        return s.exec(q).all()

# Dummy Predictor
@app.post("/predict")
def predict(body: Dict[str, Any]):
    base = (
        10000
        + body["eyes"] * 500
        + body["mouth"] * 400
        + body["hair"] * 250
        + (body["pattern"] - 1) * 700
    )
    color_bonus = (body["base_color"] + body["pattern_color"]) * 10
    return {"predicted_value": float(base + color_bonus)}
