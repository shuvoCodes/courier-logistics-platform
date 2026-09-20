from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# SQLALCHEMY_DATABASE_URL = 'postgresql://postgres.dqtesnnigaztzjpzbmjw:Admin2026Shuvo@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres'
SQLALCHEMY_DATABASE_URL = 'postgresql://postgres.bhfeugtmloecdzxsrhkb:Admin2026Shuvo@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres'
# SQLALCHEMY_DATABASE_URL = 'sqlite:///./Courier.db'
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autoflush= False, autocommit= False, bind= engine)

Base = declarative_base()