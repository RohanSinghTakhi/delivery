from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

class DriverStatus(str, Enum):
    OFFLINE = "offline"
    AVAILABLE = "available"
    BUSY = "busy"
    ON_BREAK = "on_break"

class DriverBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    vehicle_type: str  # bike, scooter, car, van
    vehicle_number: str
    license_number: str

class DriverCreate(DriverBase):
    password: str
    vendor_id: str

class DriverLogin(BaseModel):
    email: EmailStr
    password: str
    device_platform: Optional[str] = None
    push_token: Optional[str] = None

class DriverPushTokenUpdate(BaseModel):
    push_token: str
    device_platform: Optional[str] = None

class Driver(DriverBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    vendor_id: str
    status: DriverStatus = DriverStatus.OFFLINE
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    last_location_update: Optional[datetime] = None
    is_active: bool = True
    total_deliveries: int = 0
    total_earnings: float = 0.0
    device_platform: Optional[str] = None
    push_token: Optional[str] = None
    push_token_updated_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DriverResponse(DriverBase):
    id: str
    vendor_id: str
    status: DriverStatus
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    last_location_update: Optional[datetime]
    total_deliveries: int
    total_earnings: float
    device_platform: Optional[str]
    push_token: Optional[str]
    push_token_updated_at: Optional[datetime]
    created_at: datetime