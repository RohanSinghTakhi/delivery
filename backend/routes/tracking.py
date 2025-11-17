from fastapi import APIRouter, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime
from utils import calculate_eta

router = APIRouter(prefix="/tracking", tags=["Tracking"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.get("/{tracking_token}")
async def track_order(tracking_token: str):
    """
    Public endpoint to track order by token
    No authentication required
    """
    order = await db.orders.find_one({"tracking_token": tracking_token}, {"_id": 0})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid tracking token"
        )
    
    # Get driver location if assigned
    driver_location = None
    eta_minutes = None
    
    if order.get("driver_id"):
        driver = await db.drivers.find_one({"id": order["driver_id"]}, {"_id": 0})
        if driver and driver.get("current_latitude") and driver.get("current_longitude"):
            driver_location = {
                "latitude": driver["current_latitude"],
                "longitude": driver["current_longitude"],
                "last_update": driver.get("last_location_update")
            }
            
            # Calculate ETA
            eta_minutes = calculate_eta(
                (driver["current_latitude"], driver["current_longitude"]),
                (order["delivery_latitude"], order["delivery_longitude"])
            )
    
    # Parse datetime strings
    if isinstance(order.get('created_at'), str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order.get('updated_at'), str):
        order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return {
        "order": {
            "order_number": order["order_number"],
            "status": order["status"],
            "customer_name": order["customer_name"],
            "delivery_address": order["delivery_address"],
            "delivery_latitude": order["delivery_latitude"],
            "delivery_longitude": order["delivery_longitude"],
            "estimated_delivery_time": order.get("estimated_delivery_time"),
            "created_at": order["created_at"].isoformat() if isinstance(order["created_at"], datetime) else order["created_at"]
        },
        "driver_location": driver_location,
        "eta_minutes": eta_minutes
    }