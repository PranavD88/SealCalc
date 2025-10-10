SealCalc is a tiny FastAPI + PostgreSQL project to assemble “seal” images from layered SVG assets, save trait metadata (eyes, mouth, hair, pattern, colors), upload PNGs to S3, and predict a rough worth value.

## Stack
FastAPI (API)
SQLModel + PostgreSQL (AWS RDS)
S3 (image storage from presigned uploads)
Optional static web UI to compose seals

## Quick start
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
uvicorn server.main:app --reload