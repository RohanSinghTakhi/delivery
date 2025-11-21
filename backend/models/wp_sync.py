from pydantic import BaseModel, Field
from typing import List, Optional


class WooOrderItem(BaseModel):
    sku: Optional[str] = None
    name: str
    quantity: int = 1
    price: Optional[float] = None


class WooOrderPayload(BaseModel):
    woo_order_id: str = Field(..., description="WooCommerce order ID")
    woo_vendor_id: Optional[str] = Field(default=None, description="WooCommerce vendor/author ID")
    status: Optional[str] = None
    total: Optional[float] = 0.0
    customer_name: str
    customer_phone: Optional[str] = None
    pickup_address: Optional[str] = Field(default=None, description="Vendor/store pickup address (defaults to delivery address if not provided)")
    pickup_latitude: Optional[float] = None
    pickup_longitude: Optional[float] = None
    delivery_address: str
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    items: List[WooOrderItem] = Field(default_factory=list)
    notes: Optional[str] = None
    vendor_id: Optional[str] = Field(default=None, description="Internal MedEx vendor ID override")
    user_id: Optional[str] = Field(default=None, description="Internal MedEx user ID")

