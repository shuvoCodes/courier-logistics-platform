from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional ,Annotated 
from datetime import datetime
from app.models import Tracking,Parcel
from app.database import SessionLocal
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

db_dependancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict,Depends(get_current_user)]



@router.post("/{parcel_id}")
def add_tracking(db: db_dependancy, user: user_dependancy,parcel_id: int, data: TrackingCreate):

    if user.get('role') != "admin" :
        raise HTTPException(403, "Not allowed")
    
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(404, "Parcel not found")
    
    
    parcel.status = data.status
    item = Tracking(parcel_id=parcel_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.get("/{parcel_id}")
def get_tracking(db: db_dependancy, user: user_dependancy,parcel_id: int):

    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if not parcel:
        raise HTTPException(404, "Parcel not found")
    
    if user.get('role') != "admin" and parcel.sender_id != user.get('id'):
        raise HTTPException(403, "Not allowed")

    if user.get('role') == 'admin':
        return db.query(Tracking).filter(Tracking.parcel_id == parcel_id).all()
    else:
        return db.query(Tracking).join(Parcel, Tracking.parcel_id == Parcel.id).filter(
            Tracking.parcel_id == parcel_id,Parcel.sender_id == user.get('id')).all()


@router.get("/{tracking_number}/get")
def get_tracking(db: db_dependancy,tracking_number: str):

    parcel = db.query(Parcel).filter(Parcel.tracking_number == tracking_id).first()

    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    return db.query(Tracking).filter(Tracking.parcel_id == parcel.id).first()
