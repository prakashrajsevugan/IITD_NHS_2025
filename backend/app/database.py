from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import json
from datetime import datetime

# Create SQLite database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./space_cargo.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define database models
class Container(Base):
    __tablename__ = "containers"

    id = Column(String, primary_key=True, index=True)
    zone = Column(String)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    occupied_volume = Column(Float, default=0)
    
    items = relationship("Item", back_populates="container")

class Item(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    mass = Column(Float)
    priority = Column(Integer)
    expiry_date = Column(String, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    container_id = Column(String, ForeignKey("containers.id"), nullable=True)
    status = Column(String, default="Active")  # New column for waste management
    
    container = relationship("Container", back_populates="items")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    action_type = Column(String)
    astronaut_id = Column(String, nullable=True)
    item_id = Column(String, nullable=True)
    details = Column(String, nullable=True)  # JSON string

# Create tables
Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
