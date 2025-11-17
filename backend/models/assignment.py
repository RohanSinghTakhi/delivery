from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

class AssignmentStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    COMPLETED = "completed"

class AssignmentBase(BaseModel):
    order_id: str
    driver_id: str
    vendor_id: str

class AssignmentCreate(AssignmentBase):
    pass

class Assignment(AssignmentBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: AssignmentStatus = AssignmentStatus.PENDING
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accepted_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AssignmentResponse(AssignmentBase):
    id: str
    status: AssignmentStatus
    assigned_at: datetime
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]