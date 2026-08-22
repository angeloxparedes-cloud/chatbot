# ---- Stage 1: build dependencies ----
FROM python:3.11-slim AS builder

WORKDIR /app

# System deps needed to build faiss-cpu / sentence-transformers wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ---- Stage 2: runtime image ----
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from the builder stage (keeps final image smaller)
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Create a non-root user for security
RUN useradd --create-home fitgen
USER fitgen

COPY --chown=fitgen:fitgen . .

# Pre-build the FAISS index at image build time so the container starts
# ready to serve (comment out if you'd rather build it at first run).
RUN python -m src.ingest.pipeline

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "src.bot.telegram_bot"]
