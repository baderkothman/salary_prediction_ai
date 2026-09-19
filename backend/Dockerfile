# Build from the repo root (context needs both backend/ and the model
# artifact under ml/):
#   docker build -f backend/Dockerfile -t salary-prediction-api .
#   docker run -p 8000:8000 salary-prediction-api
#
# Deliberately does NOT install requirements-dev.txt or copy ml/src,
# scripts/, or frontend/ -- the deployed service only needs backend/app
# plus the trained model artifact (architecture.md invariant #8: the
# deployed API is independent of the training/generation pipeline).
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY ml/artifacts/model/ ./ml/artifacts/model/

ENV BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
