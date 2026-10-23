FROM python:3.12-slim

# tesseract-ocr/poppler-utils: local OCR + PDF rasterisation (app/documents/ocr.py).
# libmagic1: real-content MIME detection (app/documents/security_scan.py).
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr poppler-utils libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
