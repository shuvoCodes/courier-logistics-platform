from app.database import SessionLocal
from fastapi import APIRouter,Depends,HTTPException,Query
from fastapi.responses import JSONResponse
from app.models import Users
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated,Optional
from app.routers.auth import get_current_user, require_roles
from sqlalchemy import asc, desc
from math import ceil



route = APIRouter(prefix='/Admin', tags=['Admin'])

bcrypt_context = CryptContext(schemes= ['bcrypt'], deprecated = 'auto')


class CreateUser(BaseModel):
    email : str
    username: str
    fastname: str
    lastname: str
    phone : Optional[str] = Field(default= None)
    password: str
    role : str

class UpdateUser(BaseModel):
    email : Optional[str] = Field(default= None)
    username: Optional[str] = Field(default= None)
    fastname: Optional[str] = Field(default= None)
    lastname: Optional[str] = Field(default= None)
    phone : Optional[str] = Field(default= None)

class UpdateRole(BaseModel):
    role : str

class UpdateStatus(BaseModel):
    is_active : bool

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_current_user)]


@route.post('/users')
def create_user(user : user_dependency, db : db_dependency, new_user : CreateUser):
    require_roles(user, 'admin')

    exist = db.query(Users).filter(
        (Users.email == new_user.email) | (Users.username == new_user.username)
    ).first()
    if exist is not None:
        raise HTTPException(status_code= 400, detail= 'Email or Username already registered.')

    user_model = Users(
        email = new_user.email,
        username = new_user.username,
        fastname = new_user.fastname,
        lastname = new_user.lastname,
        phone = new_user.phone,
        hash_password = bcrypt_context.hash(new_user.password),
        is_active = True,
        role = new_user.role
    )
    db.add(user_model)
    db.commit()
    db.refresh(user_model)

    return JSONResponse(status_code= 201, content= {'message' : 'User Created Sucessfully.'})

@route.get("/users")
def list_users(user: user_dependency,db: db_dependency,search: str = Query(None),role: str = Query(None),
    is_active: bool = Query(None),sort_by: str = Query("create_at"),sort_order: str = Query("desc"),
    page: int = Query(1, ge=1),page_size: int = Query(10, ge=1, le=100)):

    require_roles(user, "admin")

    query = db.query(Users)

    if search:
        query = query.filter(Users.username.contains(search))

    if role:
        query = query.filter(Users.role == role)

    if is_active is not None:
        query = query.filter(Users.is_active == is_active)

    if sort_by == "username":
        column = Users.username

    elif sort_by == "email":
        column = Users.email

    elif sort_by == "create_at":
        column = Users.create_at

    else:
        return JSONResponse(status_code=404,content={"message": f"Invalid sort_by: {sort_by}"})

    if sort_order == "asc":
        query = query.order_by(asc(column))

    elif sort_order == "desc":
        query = query.order_by(desc(column))

    else:
        return JSONResponse(status_code=404,content={"message": f"Invalid sort_order: {sort_order}"})

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

# GET /users?page=1&page_size=20
# GET /users?page=2&page_size=10
# GET /users?search=shuvo&role=admin&is_active=true&page=1&page_size=5&sort_by=username&sort_order=asc


@route.get('/users/{user_id}')
def get_user_by_id(user : user_dependency, db : db_dependency, user_id : int):
    require_roles(user, 'admin')

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')

    return find


@route.put('/users/{user_id}/update')
def update_user(user : user_dependency, db : db_dependency, user_id : int, update_info : UpdateUser):
    require_roles(user, 'admin')

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')

    update = update_info.model_dump(exclude_unset= True)
    for key,value in update.items():
        setattr(find,key,value)

    db.commit()

    return JSONResponse(status_code= 200, content= {'message' : 'User Updated Sucessfully.'})


@route.delete('/users/{user_id}')
def delete_user(user : user_dependency, db : db_dependency, user_id : int):
    require_roles(user, 'admin')

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')

    db.query(Users).filter(Users.id == user_id).delete()
    db.commit()

    return JSONResponse(status_code= 200, content= {'message' : 'User Deleted Sucessfully.'})


@route.patch('/users/{user_id}/role')
def update_user_role(user : user_dependency, db : db_dependency, user_id : int, body : UpdateRole):
    require_roles(user, 'admin')

    find = db.query(Users).filter(Users.id == user_id).first()
    if find is None:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')

    find.role = body.role
    db.commit()

    return JSONResponse(status_code= 200, content= {'message' : 'User Role Updated Sucessfully.'})


@route.patch('/users/{user_id}/status')
def update_user_status(user : user_dependency, db : db_dependency, user_id : int, body : UpdateStatus):
    require_roles(user, 'admin')

    find = db.query(Users).filter(Users.id == user_id).first()

    if find is None:
        raise HTTPException(status_code= 404, detail= 'User Not Found.')

    find.is_active = body.is_active
    db.commit()

    return JSONResponse(status_code= 200, content= {'message' : 'User Status Updated Sucessfully.'})



@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.token)
        if payload.get("type") != "password_reset":
            raise HTTPException(400, "Invalid reset token")
        user = db.query(User).filter(User.id == payload.get("id")).first()
        if not user:
            raise HTTPException(404, "User not found")
        user.hashed_password = hash_password(data.new_password)
        db.commit()
        return {"message": "Password reset successful"}
    except JWTError:
        raise HTTPException(status_code=400, detail={"Invalid or expired reset token"})
