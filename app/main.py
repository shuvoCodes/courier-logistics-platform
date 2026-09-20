from fastapi import FastAPI
from app import models
from app.database import engine
from app.routers import auth,admin,parcels,tracking
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Courier & Logistics Management Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind = engine)
app.include_router(auth.route)
app.include_router(admin.route)
app.include_router(parcels.router)
app.include_router(tracking.router)


@app.get('/')
def hello():
    return 'Welcome "Courier & Logistics Management Platform"'

@app.get('/health')
def health():
    return {'status' : 'Ok'}





