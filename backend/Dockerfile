# Build from the repo root (context needs backend/, scripts/, and two ml/
# subpaths):
#   docker build -f backend/Dockerfile -t salary-prediction-api .
#   docker run -p 8000:8000 salary-prediction-api
#
# Deliberately does NOT install requirements-dev.txt or copy ml/src or
# frontend/ -- /health, /model/info, /predict only need backend/app plus
# the trained model artifact (architecture.md invariant #8: independent
# of the training pipeline). /narrate additionally needs scripts/ (context
# building + both narrator clients) and the cleaned dataset, which is why
# those are copied too -- see backend/app/services/narrator.py.
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY ml/artifacts/model/ ./ml/artifacts/model/
COPY ml/data/processed/ ./ml/data/processed/

ENV BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
