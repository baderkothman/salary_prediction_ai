import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import router
from backend.app.core.config import settings
from backend.app.core.errors import register_exception_handlers
from backend.app.services.narrator import narrator_service
from backend.app.services.predictor import predictor_service

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("salary_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        predictor_service.load()
    except Exception:
        # The service still boots so /health can report model_loaded=False
        # rather than crash-looping the whole container over a missing artifact.
        logger.exception("Failed to load model artifact at startup")

    try:
        narrator_service.load()
    except Exception:
        # /narrate degrades to a clean 503 (get_narrator dependency) rather
        # than the app failing to boot -- a deployment without the cleaned
        # dataset or scripts/ still serves /predict, /health, /model/info.
        logger.warning("Narrator service unavailable at startup (dataset missing or scripts/ not present)")

    yield


app = FastAPI(title="Salary Prediction API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["GET"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(router)
