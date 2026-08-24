# Document Summary Assistant

# Document Summary Assistant

**Live Application:** https://document-summaryassistant.onrender.com/

An AI-style document summarization web application that accepts PDF and image documents, extracts readable text, and generates short, medium, or long summaries with key points.

## Features

- PDF upload with text extraction using PyMuPDF
- Image upload with OCR using Tesseract
- Drag-and-drop and file-picker upload
- Short, medium, and long summary options
- Key points / main ideas
- Loading states and basic error handling
- Responsive interface for desktop and mobile
- 10 MB upload limit
- Copy-summary action
- Health-check endpoint for deployment

## Tech Stack

- **Backend:** Python, FastAPI
- **PDF parsing:** PyMuPDF
- **OCR:** Tesseract + pytesseract
- **Image handling:** Pillow
- **Frontend:** HTML, CSS, JavaScript

## Project Structure

```text
document-summary-assistant/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```

## Run locally

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract

On macOS with Homebrew:

```bash
brew install tesseract
```

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

### 4. Start the application

```bash
uvicorn app:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

## How it works

1. The user uploads a PDF or image.
2. The backend validates file type and size.
3. PDFs are parsed with PyMuPDF.
4. Images are processed through Tesseract OCR.
5. Extracted text is cleaned and split into sentences.
6. Sentences are ranked using word-frequency scoring.
7. The highest-ranked sentences are selected according to the requested summary length.
8. The same ranking is used to identify key points.

The summarization fallback is intentionally local and API-key-free so the project can be demonstrated without paid services.

## API

### `POST /api/extract`

Multipart form field:

```text
file=<PDF or image>
```

Returns extracted text and extraction metadata.

### `POST /api/summarize`

JSON:

```json
{
  "text": "Document text...",
  "length": "medium"
}
```

### `GET /api/health`

Returns:

```json
{
  "status": "ok"
}
```

## Brief approach write-up

The application follows a simple document-processing pipeline. Users upload a PDF or scanned image through a responsive drag-and-drop interface. The backend validates the file and extracts text using PyMuPDF for PDFs or Tesseract OCR for images. The extracted text is normalized and split into sentences. A frequency-based scoring approach ranks sentences according to important words and selects the highest-scoring sentences while preserving their original order. Users can choose short, medium, or long summaries, and the interface also presents key points and document metadata. Basic validation, upload limits, loading states, and readable error messages are included to improve reliability and user experience. The project is intentionally API-key-free so it can be run locally and demonstrated easily; the summarization layer can later be replaced by an external LLM service without changing the upload/extraction pipeline.

## Assignment alignment

This project is designed around the assessment requirements:

- Document upload for PDFs and images
- PDF parsing
- OCR for scanned documents
- Summary length options
- Key points and main ideas
- Simple responsive UI
- Error handling
- Loading states
- Documentation

For the final submission, add the deployed application URL near the top of this README.
