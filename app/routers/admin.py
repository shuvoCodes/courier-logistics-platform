from math import ceil
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Users
from app.routers.auth import get_current_user, require_roles

route = APIRouter(prefix="/Admin", tags=["Admin"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CreateUser(BaseModel):
    email: str
    username: str
    fastname: str
    lastname: str
    phone: Optional[str] = Field(default=None)
    password: str
    role: str


class UpdateUser(BaseModel):
    email: Optional[str] = Field(default=None)
    username: Optional[str] = Field(default=None)
    fastname: Optional[str] = Field(default=None)
    lastname: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)


class UpdateRole(BaseModel):
    role: str


class UpdateStatus(BaseModel):
    is_active: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@route.post("/users/create")
def create_user(user: user_dependency, db: db_dependency, new_user: CreateUser):
    require_roles(user, "admin")

    existing_user = db.query(Users).filter(
        (Users.email == new_user.email) | (Users.username == new_user.username)
    ).first()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Email or Username already registered.")

    user_model = Users(
        email=new_user.email,
        username=new_user.username,
        fastname=new_user.fastname,
        lastname=new_user.lastname,
        phone=new_user.phone,
        hash_password=bcrypt_context.hash(new_user.password),
        is_active=True,
        role=new_user.role,
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return JSONResponse(status_code=201, content={"message": "User Created Successfully."})


@route.get("/users/list")
def list_users(
    user: user_dependency,
    db: db_dependency,
    search: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="create_at"),
    sort_order: str = Query(default="desc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
):
    require_roles(user, "admin")

    query = db.query(Users)

    if search:
        query = query.filter(Users.username.contains(search))

    if role:
        query = query.filter(Users.role == role)

    if is_active is not None:
        query = query.filter(Users.is_active == is_active)

    sort_mapping = {
        "username": Users.username,
        "email": Users.email,
        "create_at": Users.create_at,
    }
    column = sort_mapping.get(sort_by)
    if column is None:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by: {sort_by}")

    if sort_order == "asc":
        query = query.order_by(asc(column))
    elif sort_order == "desc":
        query = query.order_by(desc(column))
    else:
        raise HTTPException(status_code=400, detail=f"Invalid sort_order: {sort_order}")

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


@route.get("/users/{user_id}/get")
def get_user_by_id(user: user_dependency, db: db_dependency, user_id: int):
    require_roles(user, "admin")

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code=404, detail="User Not Found.")

    return find


@route.put("/users/{user_id}/update")
def update_user(user: user_dependency, db: db_dependency, user_id: int, update_info: UpdateUser):
    require_roles(user, "admin")

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code=404, detail="User Not Found.")

    update = update_info.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(find, key, value)

    db.commit()
    return JSONResponse(status_code=200, content={"message": "User Updated Successfully."})


@route.delete("/users/{user_id}/delete")
def delete_user(user: user_dependency, db: db_dependency, user_id: int):
    require_roles(user, "admin")

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code=404, detail="User Not Found.")

    db.query(Users).filter(Users.id == user_id).delete()
    db.commit()
    return JSONResponse(status_code=200, content={"message": "User Deleted Successfully."})


@route.patch("/users/{user_id}/role")
def update_user_role(user: user_dependency, db: db_dependency, user_id: int, body: UpdateRole):
    require_roles(user, "admin")

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code=404, detail="User Not Found.")

    find.role = body.role
    db.commit()
    return JSONResponse(status_code=200, content={"message": "User Role Updated Successfully."})


@route.patch("/users/{user_id}/status")
def update_user_status(user: user_dependency, db: db_dependency, user_id: int, body: UpdateStatus):
    require_roles(user, "admin")

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code=404, detail="User Not Found.")

    find.is_active = body.is_active
    db.commit()
    return JSONResponse(status_code=200, content={"message": "User Status Updated Successfully."})
