from fastapi import APIRouter, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderStatus
import os
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("/wc/order-created")
async def woocommerce_order_created(request: Request):
    """
    WooCommerce webhook for new orders
    Expects order data in WooCommerce format
    """
    try:
        data = await request.json()
        logger.info(f"Received WooCommerce order webhook: {data.get('id')}")
        
        # Extract relevant data from WooCommerce payload
        wc_order_id = data.get("id")
        billing = data.get("billing", {})
        shipping = data.get("shipping", {})
        
        # Create order in our system
        order = Order(
            user_id="woocommerce",  # Placeholder, map to actual user if needed
            vendor_id=data.get("vendor_id", "default_vendor"),
            pickup_address=shipping.get("address_1", ""),
            pickup_latitude=0.0,  # Would need geocoding
            pickup_longitude=0.0,
            delivery_address=f"{shipping.get('address_1', '')}, {shipping.get('city', '')}",
            delivery_latitude=0.0,  # Would need geocoding
            delivery_longitude=0.0,
            customer_name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}",
            customer_phone=billing.get("phone", ""),
            items=data.get("line_items", []),
            notes=data.get("customer_note", "")
        )
        
        order_dict = order.model_dump()
        order_dict['created_at'] = order_dict['created_at'].isoformat()
        order_dict['updated_at'] = order_dict['updated_at'].isoformat()
        order_dict['wc_order_id'] = wc_order_id  # Store WC reference
        
        await db.orders.insert_one(order_dict)
        
        return {
            "success": True,
            "message": "Order created",
            "order_id": order.id,
            "wc_order_id": wc_order_id
        }
        
    except Exception as e:
        logger.error(f"Error processing WooCommerce webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/wc/order-updated")
async def woocommerce_order_updated(request: Request):
    """
    WooCommerce webhook for order updates
    """
    try:
        data = await request.json()
        logger.info(f"Received WooCommerce order update webhook: {data.get('id')}")
        
        wc_order_id = data.get("id")
        wc_status = data.get("status")
        
        # Find order by WC ID
        order = await db.orders.find_one({"wc_order_id": wc_order_id}, {"_id": 0})
        
        if not order:
            logger.warning(f"Order not found for WC ID: {wc_order_id}")
            return {"success": False, "message": "Order not found"}
        
        # Map WC status to our status
        status_map = {
            "pending": OrderStatus.PENDING,
            "processing": OrderStatus.ACCEPTED,
            "completed": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED
        }
        
        new_status = status_map.get(wc_status, OrderStatus.PENDING)
        
        await db.orders.update_one(
            {"id": order["id"]},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "success": True,
            "message": "Order status updated",
            "order_id": order["id"],
            "new_status": new_status
        }
        
    except Exception as e:
        logger.error(f"Error processing WooCommerce update webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )