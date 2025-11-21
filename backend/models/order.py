from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DRIVER_ASSIGNED = "driver_assigned"
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class OrderBase(BaseModel):
    user_id: str
    vendor_id: str
    pickup_address: str
    pickup_latitude: float
    pickup_longitude: float
    delivery_address: str
    delivery_latitude: float
    delivery_longitude: float
    customer_name: str
    customer_phone: str
    items: list = Field(default_factory=list)  # List of items/medicines
    notes: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    # WooCommerce compatibility
    woo_order_id: Optional[str] = Field(default=None, description="Original WooCommerce order ID")
    woo_vendor_id: Optional[str] = Field(default=None, description="WooCommerce vendor ID/author")
    woo_status: Optional[str] = None
    source: str = Field(default="medex", description="medex | woocommerce")

class CustomerLocationUpdate(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"ORD-{str(uuid.uuid4())[:8].upper()}")
    status: OrderStatus = OrderStatus.PENDING
    driver_id: Optional[str] = None
    assignment_id: Optional[str] = None
    tracking_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    estimated_distance_km: Optional[float] = None
    actual_distance_km: Optional[float] = None
    delivery_fee: float = 0.0
    
    # Proof of delivery
    proof_photo_url: Optional[str] = None
    signature_url: Optional[str] = None
    delivered_at: Optional[datetime] = None
    
    # Customer live location
    customer_current_latitude: Optional[float] = None
    customer_current_longitude: Optional[float] = None
    customer_location_accuracy: Optional[float] = None
    customer_location_heading: Optional[float] = None
    customer_location_speed: Optional[float] = None
    customer_last_location_update: Optional[datetime] = None
    
    # Timestamps
    accepted_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    out_for_delivery_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrderResponse(OrderBase):
    id: str
    order_number: str
    status: OrderStatus
    driver_id: Optional[str]
    tracking_token: str
    estimated_distance_km: Optional[float]
    delivery_fee: float
    created_at: datetime
    updated_at: datetime
    customer_current_latitude: Optional[float] = None
    customer_current_longitude: Optional[float] = None
    customer_last_location_update: Optional[datetime] = None