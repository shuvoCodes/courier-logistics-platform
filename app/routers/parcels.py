from datetime import datetime
from math import ceil
import secrets
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Parcel
from app.routers.auth import get_current_user

router = APIRouter(prefix="/parcels", tags=["Parcels"])


class ParcelCreate(BaseModel):
    receiver_name: str = Field(default="jone")
    receiver_phone: str = Field(default="01XXXXXXXXXX")
    pickup_address: str = Field(default="Dhaka")
    delivery_address: str = Field(default="Janata Branch")
    category: str = Field(default="Books")
    weight: float = Field(gt=0)
    delivery_fee: float = Field(ge=0)


class ParcelUpdate(BaseModel):
    receiver_name: Optional[str] = Field(default=None)
    receiver_phone: Optional[str] = Field(default=None)
    pickup_address: Optional[str] = Field(default=None)
    delivery_address: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    weight: Optional[float] = Field(default=None, gt=0)
    delivery_fee: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None)


SORT_OPTIONS = {
    "newest": (Parcel.created_at, "desc"),
    "oldest": (Parcel.created_at, "asc"),
    "alphabetical": (Parcel.receiver_name, "asc"),
    "price": (Parcel.delivery_fee, "desc"),
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.post("/create")
def create_parcel(db: db_dependency, user: user_dependency, data: ParcelCreate):
    parcel = Parcel(
        **data.model_dump(),
        tracking_number=f"CR-{secrets.token_hex(5).upper()}",
        sender_id=user["id"],
    )
    db.add(parcel)
    db.commit()
    db.refresh(parcel)
    return parcel


@router.get("/find")
def list_parcels(
    db: db_dependency,
    user: user_dependency,
    search: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    date_from: Optional[datetime] = Query(default=None),
    date_to: Optional[datetime] = Query(default=None),
    sort: str = Query(default="newest", description="Sort based on newest, oldest, alphabetical and price"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    query = db.query(Parcel)

    if user["role"] != "admin":
        query = query.filter(Parcel.sender_id == user["id"])

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

    sort_config = SORT_OPTIONS.get(sort)
    if sort_config is None:
        raise HTTPException(status_code=400, detail=f"Invalid Request of {sort}")

    column, direction = sort_config
    query = query.order_by(desc(column) if direction == "desc" else asc(column))

    total_items = query.count()
    total_pages = ceil(total_items / page_size)
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "items": items,
    }


@router.get("/{parcel_id}/get")
def get_parcel(parcel_id: int, db: db_dependency, user: user_dependency):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    if user["role"] != "admin" and parcel.sender_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    return parcel


@router.put("/{parcel_id}/update")
def update_parcel(parcel_id: int, data: ParcelUpdate, db: db_dependency, user: user_dependency):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    if user["role"] != "admin" and parcel.sender_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(parcel, key, value)

    db.commit()
    db.refresh(parcel)
    return parcel


@router.delete("/{parcel_id}/delete")
def delete_parcel(db: db_dependency, user: user_dependency, parcel_id: int):
    parcel = db.query(Parcel).filter(Parcel.id == parcel_id).first()
    if parcel is None:
        raise HTTPException(status_code=404, detail="Parcel not found")

    if user["role"] != "admin" and parcel.sender_id != user["id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    db.delete(parcel)
    db.commit()
    return JSONResponse(status_code=200, content={"message": "Parcel deleted successfully"})
