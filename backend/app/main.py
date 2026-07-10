from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.hcps import router as hcps_router, materials_router
from .api.interactions import router as interactions_router
from .api.agent import router as agent_router
from .database import async_engine, Base
from . import models  # noqa: F401 – ensures all models are registered with SQLAlchemy


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="CRM HCP Module API",
    version="1.0.0",
    description="AI-First CRM for pharmaceutical field representatives",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcps_router)
app.include_router(materials_router)
app.include_router(interactions_router)
app.include_router(agent_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "CRM HCP Module API is running"}
