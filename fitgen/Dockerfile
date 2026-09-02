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
# Create a non-root user for security
RUN useradd --create-home fitgen
# Copy only the installed packages from the builder stage (keeps final image
# smaller). They must land under the fitgen user's home directory, not
# root's, since `pip install --user` resolves the target path from the
# current user's HOME at import time -- copying into /root/.local would be
# invisible once we switch to running as the fitgen user below.
COPY --from=builder --chown=fitgen:fitgen /root/.local /home/fitgen/.local
ENV PATH=/home/fitgen/.local/bin:$PATH
USER fitgen
COPY --chown=fitgen:fitgen . .
# Pre-build the FAISS index at image build time so the container starts
# ready to serve (comment out if you'd rather build it at first run).
RUN python -m src.ingest.pipeline
ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "src.bot.telegram_bot"]
