# ---------- stage 1: build ----------
FROM python:3.13-slim AS builder

ARG DEBIAN_FRONTEND=noninteractive
# venv bin first in PATH = venv "activated"
ENV PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/venv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- stage 2: run ----------
FROM python:3.13-slim AS runner

RUN useradd --system --uid 10001 --no-create-home ipcalc

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY app/ .

USER ipcalc
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "main:app"]
