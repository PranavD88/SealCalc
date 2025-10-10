import os, uuid
from fastapi import UploadFile

UPLOAD_DIR = "server/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_png(file: UploadFile) -> str:
    if file.content_type != "image/png":
        raise ValueError("PNG required")
    name = f"{uuid.uuid4().hex}.png"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(file.file.read())
    return f"/uploads/{name}"
