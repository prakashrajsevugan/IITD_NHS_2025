from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Tuple, Any
from datetime import datetime

# Item Schemas
class ItemBase(BaseModel):
    name: str
    width_cm: float
    depth_cm: float
    height_cm: float
    mass_kg: float
    priority: int = Field(..., ge=1, le=10)
    expiry_date: Optional[str] = None
    usage_limit: Optional[int] = None
    preferred_zone: Optional[str] = None

class ItemCreate(ItemBase):
    id: str

class Coordinates(BaseModel):
    width: float
    depth: float
    height: float

class Position(BaseModel):
    startCoordinates: Coordinates
    endCoordinates: Coordinates

class Item(ItemBase):
    id: str
    container_id: Optional[str] = None
    position: Optional[str] = None
    is_waste: bool = False

    class Config:
        from_attributes = True

# Container Schemas
class ContainerBase(BaseModel):
    zone: str
    width_cm: float
    depth_cm: float
    height_cm: float

class ContainerCreate(ContainerBase):
    id: str

class Container(ContainerBase):
    id: str

    class Config:
        from_attributes = True

# Placement Schemas
class PlacementRequest(BaseModel):
    itemId: str
    userId: str
    containerId: str
    timestamp: str
    position: Position

class PlacementResponse(BaseModel):
    success: bool
    message: Optional[str] = None

# Search and Retrieval Schemas
class SearchRequest(BaseModel):
    item_id: Optional[str] = None
    name: Optional[str] = None
    zone: Optional[str] = None
    priority_min: Optional[int] = None

class SearchResult(BaseModel):
    items: List[Item]
    retrieval_difficulty: Dict[str, int]
    total_count: int = 0
    search_time_ms: Optional[float] = None

class RetrievalRequest(BaseModel):
    itemId: str
    userId: str
    timestamp: str
    notes: Optional[str] = None

class RetrievalStep(BaseModel):
    step_number: int
    action: str
    item_id: str
    item_name: Optional[str] = None
    temporary_position: Optional[Dict[str, float]] = None
    notes: Optional[str] = None

class RetrievalResult(BaseModel):
    item_id: str
    item_name: Optional[str] = None
    container_id: str
    container_zone: Optional[str] = None
    steps: List[RetrievalStep]
    total_steps: int
    estimated_time_seconds: Optional[int] = None
    retrieval_timestamp: datetime = Field(default_factory=datetime.utcnow)

# Waste Management Schemas
class WasteItem(BaseModel):
    item: Item
    reason: str

class ReturnPlanRequest(BaseModel):
    undockingContainerId: str
    undockingDate: str
    maxWeight: float

class ReturnPlanItem(BaseModel):
    item_id: str
    name: str
    mass: float
    priority: int
    reason: str

class ReturnPlan(BaseModel):
    items: List[ReturnPlanItem]
    total_mass: float
    remaining_capacity: float
    space_reclaimed: Dict[str, float]

class UndockingRequest(BaseModel):
    undockingContainerId: str
    timestamp: str

# Time Simulation schemas
class ItemUsage(BaseModel):
    item_id: str
    uses: int = 1

class SimulationRequest(BaseModel):
    numOfDays: int = 1
    itemsToBeUsedPerDay: Optional[List[Dict[str, Any]]] = None

class SimulationResult(BaseModel):
    message: str
    current_date: str
    waste_items: List[Item]
    waste_items_count: int

# Log Schemas
class Log(BaseModel):
    id: int
    action_type: str
    item_id: Optional[str] = None
    container_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime
    details: Optional[str] = None

    class Config:
        from_attributes = True

class LogCreate(BaseModel):
    action_type: str
    item_id: Optional[str] = None
    container_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
