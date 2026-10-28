# ==========================================
# Stage 1: Build & Python Dependencies
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir .

# ==========================================
# Stage 2: Runtime Production Image
# ==========================================
FROM python:3.10-slim AS runner

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV MOCK_LLM_MODE=true
ENV DEMO_MODE=true
ENV ENVIRONMENT=production

# Copy application source code and configurations
COPY pyproject.toml .
COPY src/ ./src/
COPY docs/knowledge_base/ ./docs/knowledge_base/
COPY data/sample/ ./data/sample/
COPY evals/ ./evals/
COPY models/ ./models/
COPY scripts/docker_entrypoint.sh ./scripts/docker_entrypoint.sh

RUN chmod +x ./scripts/docker_entrypoint.sh

# Expose FastAPI port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["./scripts/docker_entrypoint.sh"]
