from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.seed import seed_database_demo_data
from app.api.routes import router

# Create DB tables
Base.metadata.create_all(bind=engine)

# Auto seed if brand new
db = SessionLocal()
try:
    seed_database_demo_data(db, force_reset=False)
finally:
    db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FLOWGUARD: An Explainable AI Agent for Dynamic Hospital Emergency Resource Coordination",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "app": "FLOWGUARD",
        "description": "Hospital Emergency Resource Coordination Platform",
        "team": "Team Trauma",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
