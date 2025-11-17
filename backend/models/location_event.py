from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid

class LocationEventBase(BaseModel):
    driver_id: str
    latitude: float
    longitude: float
    speed: float = 0.0  # km/h
    heading: float = 0.0  # degrees
    accuracy: float = 0.0  # meters

class LocationEventCreate(LocationEventBase):
    pass

class LocationEvent(LocationEventBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))