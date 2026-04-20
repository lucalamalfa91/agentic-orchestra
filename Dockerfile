# Stage 1: install dependencies
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# CPU-only PyTorch first — avoids pulling the 2 GB CUDA wheel
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch>=2.0.0"

COPY orchestrator-ui/backend/requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt


# Stage 2: runtime image
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy full repo so both orchestrator-ui/ and AI_agents/ are available
COPY . /app

# Pre-download embedding model at build time (avoids slow cold starts)
# paraphrase-MiniLM-L6-v2 is ~80 MB and fits comfortably in 512 MB RAM
ENV SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence_transformers
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('paraphrase-MiniLM-L6-v2')" || true

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PYTHONPATH=/app

CMD ["python", "-m", "uvicorn", "orchestrator_ui.backend.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
