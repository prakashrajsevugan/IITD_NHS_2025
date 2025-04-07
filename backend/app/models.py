from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from .database import Base

# Association table for item-container relationship
item_container = Table(
    "item_container",
    Base.metadata,
    Column("item_id", String, ForeignKey("items.id")),
    Column("container_id", String, ForeignKey("containers.id")),
    extend_existing=True
)

class Item(Base):
    """Database model for items in the space station."""
    __tablename__ = "items"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    mass = Column(Float)
    priority = Column(Integer)
    expiry_date = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    preferred_zone = Column(String, nullable=True)
    is_waste = Column(Boolean, default=False)
    
    # Position within container
    container_id = Column(String, ForeignKey("containers.id"), nullable=True)
    position_x = Column(Float, nullable=True)
    position_y = Column(Float, nullable=True)
    position_z = Column(Float, nullable=True)
    orientation = Column(String, nullable=True)  # e.g., "xyz", "xzy", etc.
    
    # New column for waste management
    status = Column(String, default="Active")
    
    # Relationships
    container = relationship("Container", back_populates="items")
    retrieval_logs = relationship("RetrievalLog", back_populates="item")

class Container(Base):
    """Database model for storage containers in the space station."""
    __tablename__ = "containers"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, index=True)
    zone = Column(String, index=True)
    width = Column(Float)
    depth = Column(Float)
    height = Column(Float)
    
    # Relationships
    items = relationship("Item", back_populates="container")

class RetrievalLog(Base):
    """Database model for logging item retrieval operations."""
    __tablename__ = "retrieval_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(String, ForeignKey("items.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    astronaut_id = Column(String)
    steps = Column(Integer)
    
    # Relationships
    item = relationship("Item", back_populates="retrieval_logs")

class ActionLog(Base):
    """Database model for logging all actions in the system."""
    __tablename__ = "action_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String, index=True)  # e.g., "place", "retrieve", "rearrange"
    item_id = Column(String, nullable=True)
    container_id = Column(String, nullable=True)
    astronaut_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(String, nullable=True)

class SystemDate(Base):
    """Database model for tracking the current system date for simulations."""
    __tablename__ = "system_date"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    current_date = Column(DateTime, default=datetime.utcnow)
