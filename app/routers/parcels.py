from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import asc,desc
from pydantic import Field,BaseModel
from typing import Optional,Annotated
from app.models import Parcel
from app.routers.auth import get_current_user
from app.database import SessionLocal
from math import ceil
import secrets


router = APIRouter(prefix="/parcels", tags=["Parcels"])


class ParcelCreate(BaseModel):
    receiver_name: str = Field("jone")
    receiver_phone: str = Field("01XXXXXXXXXX")
    pickup_address: str = Field("Dhaka")
    delivery_address: str = Field("Janata Branch")
    category: str = Field("Books")
    weight: float = Field(gt=0)


class ParcelUpdate(BaseModel):
    receiver_name: Optional[str] = Field(default=None)
    receiver_phone: Optional[str] = Field(default=None)
    pickup_address: Optional[str] = Field(default=None)
    delivery_address: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    weight: Optional[float] = Field(default=None, gt=0)
    delivery_fee: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependancy = Annotated[Session,Depends(get_db)]
user_dependancy = Annotated[dict,Depends(get_current_user)]


@router.post("/")
def create_parcel(db: db_dependancy, user: user_dependancy, data: ParcelCreate):
    parcel = Parcel(
        **data.model_dump(),
        delivery_fee = data.weight * 60,
        tracking_number = f"CR-{secrets.token_hex(5).upper()}",
        sender_id=user.get('id')
    )
    db.add(parcel)
    db.commit()
    db.refresh(parcel)
    return JSONResponse(status_code=201 ,content={"message": 'Parcel Create Sucessfully'})

@router.get("/search")
def list_parcels(db: db_dependancy,user: user_dependancy,search: str = Query(None),status: str = Query(None),category: str = Query(None),
    date_from: datetime = Query(None),date_to: datetime = Query(None),sort: str = Query("newest",description="Sort based on newest, oldest, alphabetical and price"),
    page: int = Query(1, ge=1),page_size: int = Query(10, ge=1, le=100)):

    query = db.query(Parcel)

    if user.get('role') != "admin":
        query = query.filter(Parcel.sender_id == user.get('id'))

    if search:
        query = query.filter(Parcel.tracking_number == search)

    if status:
        query = query.filter(Parcel.status == status)

    if category:
        query = query.filter(Parcel.category == category)

    if date_from:
        query = query.filter(Parcel.created_at >= date_from)

    if date_to:
        query = query.filter(Parcel.created_at <= date_to)

    if sort == "newest":
        column = Parcel.created_at
        order = "desc"

    elif sort == "oldest":
        column = Parcel.created_at
        order = "asc"

    elif sort == "alphabetical":
        column = Parcel.receiver_name
        order = "asc"

    elif sort == "price":
        column = Parcel.delivery_fee
        order = "desc"

    else:
        return JSONResponse(status_code=404,content={"message": f"Invalid Request of {sort}"})

    if order == "asc":
        query = query.order_by(asc(column))

    else:
        query = query.order_by(desc(column))

    total_items = query.count()

    total_pages = ceil(total_items / page_size)

    skip = (page - 1) * page_size

    items = query.offset(skip).limit(page_size).all()

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "items": items
    }

@router.get("/{parcel_id}")
def get_parcel(parcel_id: int,db: db_dependancy,user: user_dependancy):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()

    if parcel is None:
        raise HTTPException(status_code=404,detail="Parcel not found")

    # Normal user can only see own parcel
    if (user.get("role") != "admin"and parcel.sender_id != user.get("id")):
        raise HTTPException(status_code=403,detail="Not allowed")

    return parcel

@router.put("/update/{parcel_id}")
def update_parcel(parcel_id: int, data: ParcelUpdate, db: db_dependancy, user: user_dependancy):

    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    if user.get('role') != "admin" and parcel.sender_id != user.get('id'):
        raise HTTPException(status_code=403, detail="Not allowed")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(parcel, key, value)

    db.commit()
    db.refresh(parcel)
    return parcel

@router.delete("/delete/{parcel_id}")
def delete_parcel(db: db_dependancy, user:user_dependancy,parcel_id: int):

    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    if user.get('role') != "admin" and parcel.sender_id != user.get('id'):
        raise HTTPException(status_code=403, detail="Not allowed")
    
    db.delete(parcel)
    db.commit()
    return JSONResponse(status_code=200, content={ "message": "Parcel deleted successfully"})
