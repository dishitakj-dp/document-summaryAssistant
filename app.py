import os
import re
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Document Summary Assistant", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class SummaryRequest(BaseModel):
    text: str
    length: str = "medium"


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text


def extract_pdf_text(data: bytes) -> str:
    try:
        document = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text("text") for page in document]
        document.close()
        return clean_text("\n".join(pages))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {exc}")


def extract_image_text(data: bytes) -> str:
    try:
        from io import BytesIO
        image = Image.open(BytesIO(data))
        return clean_text(pytesseract.image_to_string(image))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not OCR the image. Make sure Tesseract is installed: {exc}",
        )


def split_sentences(text: str):
    text = clean_text(text)
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 25]


def score_sentences(sentences):
    if not sentences:
        return []

    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", " ".join(sentences).lower())
    stop_words = {
        "the", "and", "that", "this", "with", "from", "were", "have", "has",
        "are", "for", "was", "but", "not", "you", "your", "they", "their",
        "its", "into", "than", "then", "also", "about", "which", "will",
        "would", "there", "these", "those", "been", "being", "can", "could",
        "should", "more", "some", "such", "other", "only", "very", "each",
        "using", "used", "use", "our", "who", "what", "when", "where", "how",
    }
    freq = {}
    for word in words:
        if word not in stop_words:
            freq[word] = freq.get(word, 0) + 1

    scored = []
    for idx, sentence in enumerate(sentences):
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", sentence.lower())
        score = sum(freq.get(t, 0) for t in tokens)
        # Slightly favor earlier sentences while avoiding an overly positional summary.
        score += max(0, 3 - idx * 0.05)
        scored.append((score, idx, sentence))

    return sorted(scored, reverse=True)


def generate_summary(text: str, length: str):
    sentences = split_sentences(text)
    if not sentences:
        return "Not enough readable text was found to generate a summary."

    limits = {"short": 3, "medium": 6, "long": 10}
    target = min(limits.get(length, 6), len(sentences))

    ranked = score_sentences(sentences)[:target]
    selected = sorted(ranked, key=lambda item: item[1])
    summary = " ".join(item[2] for item in selected)

    if len(summary) > 2500:
        summary = summary[:2500].rsplit(" ", 1)[0] + "..."
    return summary


def key_points(text: str, count: int = 5):
    sentences = split_sentences(text)
    ranked = score_sentences(sentences)
    selected = sorted(ranked[:count], key=lambda item: item[1])
    return [item[2] for item in selected]


@app.get("/")
async def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/extract")
async def extract_document(file: UploadFile = File(...)):
    filename = file.filename or "document"
    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a PDF, PNG, JPG, JPEG, or WEBP file.",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File is too large. Maximum size is 10 MB.")

    if suffix == ".pdf":
        text = extract_pdf_text(data)
        extraction_method = "PDF text extraction"
    else:
        text = extract_image_text(data)
        extraction_method = "OCR (Tesseract)"

    if len(text) < 20:
        raise HTTPException(
            status_code=422,
            detail="Very little readable text was found. Try a clearer document or scanned image.",
        )

    return {
        "filename": filename,
        "text": text,
        "characters": len(text),
        "extraction_method": extraction_method,
    }


@app.post("/api/summarize")
async def summarize_document(request: SummaryRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="No document text was provided.")

    if request.length not in {"short", "medium", "long"}:
        raise HTTPException(status_code=400, detail="Length must be short, medium, or long.")

    summary = generate_summary(request.text, request.length)
    points = key_points(request.text, 5)

    return {
        "summary": summary,
        "key_points": points,
        "length": request.length,
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}
