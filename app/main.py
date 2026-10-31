from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import engine
from app.routers import admin, auth, parcels, tracking

app = FastAPI(title="Courier & Logistics Management Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

for router in (auth.route, admin.route, parcels.router, tracking.router):
    app.include_router(router)


@app.get("/")
def hello():
    return "Welcome \"Courier & Logistics Management Platform\""


@app.get("/health")
def health():
    return {"status": "ok"}
