import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .database import Base, engine, SessionLocal
from .seed import seed
from .routers import auth, activities, targets, dashboard, admin

BASE = os.path.dirname(os.path.dirname(__file__))


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    yield


app = FastAPI(title="Clarity - Carbon Emissions Calculator & Regulator", version="1.0.0", lifespan=lifespan)
for r in (auth, activities, targets, dashboard, admin):
    app.include_router(r.router)
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(os.path.join(BASE, "static", "index.html"))


@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok"}
