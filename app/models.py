from app.database import Base
from sqlalchemy import Column,Integer,String,Boolean,DateTime,Float, ForeignKey
from datetime import datetime,timezone
from pydantic import EmailStr

class Users(Base):

    __tablename__ = 'users'

    id = Column(Integer,primary_key= True, index= True)
    email = Column(String,unique= True, index= True)
    username = Column(String,unique= True, index= True)
    fastname = Column(String)
    lastname = Column(String)
    phone = Column(String, nullable= True)
    hash_password = Column(String)
    is_active = Column(Boolean, default= True)
    role = Column(String, default= 'user')           
    reset_token_expiry = Column(DateTime, nullable= True)
    create_at = Column(DateTime, default= datetime.now)


class Parcel(Base):

    __tablename__ = "parcels"

    id = Column(Integer, primary_key=True, index=True)
    tracking_number = Column(String(40), unique=True, nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_name = Column(String(100), nullable=False)
    receiver_phone = Column(String(30), nullable=False)
    pickup_address = Column(String(255), nullable=False)
    delivery_address = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    weight = Column(Float, nullable=False)
    delivery_fee = Column(Float, nullable=False)
    status = Column(String(30), default="pending", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Tracking(Base):

    __tablename__ = "trackings"

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("parcels.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    location = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

