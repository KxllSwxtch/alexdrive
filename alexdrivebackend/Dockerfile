# ── Builder ──────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# ── Runtime ──────────────────────────────────────────────
FROM python:3.13-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ app/

# Non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE ${PORT:-3001}

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-3001}/api/health')" || exit 1

# Single worker to preserve module-level caches (session, filters)
# Shell form so $PORT is expanded at runtime (Render sets PORT dynamically)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-3001} --workers 1
