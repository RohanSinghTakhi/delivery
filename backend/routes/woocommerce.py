from fastapi import APIRouter, Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from pydantic import BaseModel
import os
from datetime import datetime, timezone

from models import Order, OrderResponse, OrderStatus, WooOrderPayload

router = APIRouter(prefix="/woocommerce", tags=["WooCommerce"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

WC_SYNC_SECRET = os.environ.get("WOOCOMMERCE_SYNC_SECRET")


def translate_status(woo_status: Optional[str]) -> OrderStatus:
    if not woo_status:
        return OrderStatus.PENDING
    mapping = {
        "pending": OrderStatus.PENDING,
        "processing": OrderStatus.ACCEPTED,
        "driver_assigned": OrderStatus.DRIVER_ASSIGNED,
        "driver-assigned": OrderStatus.DRIVER_ASSIGNED,
        "picked_up": OrderStatus.PICKED_UP,
        "picked-up": OrderStatus.PICKED_UP,
        "out_for_delivery": OrderStatus.OUT_FOR_DELIVERY,
        "out-for-delivery": OrderStatus.OUT_FOR_DELIVERY,
        "completed": OrderStatus.DELIVERED,
        "delivered": OrderStatus.DELIVERED,
        "cancelled": OrderStatus.CANCELLED,
        "failed": OrderStatus.CANCELLED
    }
    return mapping.get(woo_status.lower(), OrderStatus.PENDING)


async def verify_wc_secret(x_wc_secret: Optional[str] = Header(default=None, alias="X-WC-Secret")):
    if WC_SYNC_SECRET:
        if not x_wc_secret or x_wc_secret != WC_SYNC_SECRET:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid WooCommerce secret")


async def resolve_vendor_id(payload: WooOrderPayload) -> Optional[str]:
    if payload.vendor_id:
        return payload.vendor_id
    if not payload.woo_vendor_id:
        return None
    vendor = await db.vendors.find_one({"woo_vendor_id": payload.woo_vendor_id}, {"_id": 0, "id": 1})
    if vendor:
        return vendor["id"]
    return None


def serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


@router.post("/orders/sync", response_model=OrderResponse)
async def sync_order(payload: WooOrderPayload, _: None = Depends(verify_wc_secret)):
    vendor_id = await resolve_vendor_id(payload)
    if not vendor_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown vendor for WooCommerce sync")

    status_value = translate_status(payload.status)
    # Fallback pickup_address to delivery_address if not provided
    pickup_addr = payload.pickup_address or payload.delivery_address or "Address not provided"
    order_doc = {
        "user_id": payload.user_id or vendor_id,
        "vendor_id": vendor_id,
        "pickup_address": pickup_addr,
        "pickup_latitude": payload.pickup_latitude or 0.0,
        "pickup_longitude": payload.pickup_longitude or 0.0,
        "delivery_address": payload.delivery_address,
        "delivery_latitude": payload.delivery_latitude or 0.0,
        "delivery_longitude": payload.delivery_longitude or 0.0,
        "customer_name": payload.customer_name,
        "customer_phone": payload.customer_phone or "",
        "items": [item.model_dump() for item in payload.items],
        "notes": payload.notes,
        "status": status_value,
        "source": "woocommerce",
        "woo_order_id": payload.woo_order_id,
        "woo_vendor_id": payload.woo_vendor_id,
        "woo_status": payload.status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

    existing = await db.orders.find_one({"woo_order_id": payload.woo_order_id}, {"_id": 0})
    if existing:
        await db.orders.update_one({"woo_order_id": payload.woo_order_id}, {"$set": order_doc})
        updated = await db.orders.find_one({"woo_order_id": payload.woo_order_id}, {"_id": 0})
        return OrderResponse(**updated)

    order = Order(
        user_id=order_doc["user_id"],
        vendor_id=vendor_id,
        pickup_address=order_doc["pickup_address"],
        pickup_latitude=order_doc["pickup_latitude"],
        pickup_longitude=order_doc["pickup_longitude"],
        delivery_address=order_doc["delivery_address"],
        delivery_latitude=order_doc["delivery_latitude"],
        delivery_longitude=order_doc["delivery_longitude"],
        customer_name=order_doc["customer_name"],
        customer_phone=order_doc["customer_phone"],
        items=order_doc["items"],
        notes=order_doc["notes"],
        status=status_value,
        source="woocommerce",
        woo_order_id=payload.woo_order_id,
        woo_vendor_id=payload.woo_vendor_id,
        woo_status=payload.status
    )
    order_dict = order.model_dump()
    order_dict["created_at"] = serialize_datetime(order_dict["created_at"])
    order_dict["updated_at"] = serialize_datetime(order_dict["updated_at"])
    await db.orders.insert_one(order_dict)
    return OrderResponse(**order.model_dump())


class WooStatusUpdate(BaseModel):
    status: str


@router.patch("/orders/{woo_order_id}/status")
async def update_order_status(woo_order_id: str, payload: WooStatusUpdate, _: None = Depends(verify_wc_secret)):
    order = await db.orders.find_one({"woo_order_id": woo_order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    medex_status = translate_status(payload.status)
    await db.orders.update_one(
        {"woo_order_id": woo_order_id},
        {
            "$set": {
                "status": medex_status,
                "woo_status": payload.status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    return {"message": "Status updated", "status": medex_status}

