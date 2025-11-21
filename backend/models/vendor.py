from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class VendorBase(BaseModel):
    business_name: str
    email: EmailStr
    phone: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    woo_vendor_id: Optional[str] = Field(default=None, description="WooCommerce vendor identifier")

class VendorCreate(VendorBase):
    password: str
    user_id: Optional[str] = None

class Vendor(VendorBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    is_active: bool = True
    driver_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VendorResponse(VendorBase):
    id: str
    user_id: str
    is_active: bool
    created_at: datetime