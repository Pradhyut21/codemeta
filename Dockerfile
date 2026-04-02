FROM python:3.11-slim

LABEL maintainer="codesentinel-team"
LABEL org.opencontainers.image.title="CodeSentinel"
LABEL org.opencontainers.image.description="OpenEnv environment for AI code review agents"
LABEL space_sdk="docker"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV HOST=0.0.0.0
ENV PORT=7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/validate')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
