from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Parcel, Tracking
from app.routers.auth import get_current_user

router = APIRouter(prefix="/tracking", tags=["Tracking"])


class TrackingCreate(BaseModel):
    status: str
    location: str
    description: Optional[str] = None


class TrackingResponse(BaseModel):
    id: int
    parcel_id: int
    status: str
    location: str
    description: Optional[str]
    created_at: datetime


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/parcel/{parcel_id}/create")
def add_tracking(db: db_dependency, user: user_dependency, parcel_id: int, data: TrackingCreate):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    if user.get("role") != "admin" and parcel.sender_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Not allowed")

    parcel.status = data.status
    tracking_item = Tracking(parcel_id=parcel_id, sender_id=parcel.sender_id, **data.model_dump())
    db.add(tracking_item)
    db.commit()
    db.refresh(tracking_item)
    return tracking_item


@router.get("/parcel/{parcel_id}/get")
def get_tracking_by_parcel(db: db_dependency, user: user_dependency, parcel_id: int):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")

    if user.get("role") != "admin" and parcel.sender_id != user.get("id"):
        raise HTTPException(status_code=403, detail="Not allowed")

    return db.query(Tracking).filter(Tracking.parcel_id == parcel_id).all()


@router.get("/item/{tracking_id}/get")
def get_tracking_by_id(db: db_dependency, tracking_id: int):
    tracking = db.query(Tracking).filter(Tracking.id == tracking_id).first()
    if tracking is None:
        raise HTTPException(status_code=404, detail="Tracking not found")
    return tracking
