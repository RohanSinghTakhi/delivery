from fastapi import WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from utils import verify_token, calculate_eta
from .manager import manager
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def websocket_auth(token: str) -> dict:
    """
    Authenticate WebSocket connection via JWT token
    """
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    user_id = payload.get("sub")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user or not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user

async def handle_driver_location(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket handler for driver location updates
    
    Driver sends location every 3-5 seconds
    Server broadcasts to:
    - Vendor room (vendor_{vendor_id})
    - Order room (order_{order_id}) if driver has active order
    """
    try:
        # Authenticate
        user = await websocket_auth(token)
        
        if user["role"] != "driver":
            await websocket.close(code=1008, reason="Not a driver")
            return
        
        # Get driver
        driver = await db.drivers.find_one({"user_id": user["id"]}, {"_id": 0})
        if not driver:
            await websocket.close(code=1008, reason="Driver profile not found")
            return
        
        driver_id = driver["id"]
        vendor_id = driver["vendor_id"]
        
        # Connect
        await manager.connect(websocket, driver_id)
        
        # Join vendor room
        manager.join_room(f"vendor_{vendor_id}", driver_id)
        
        # Send connection success
        await manager.send_personal_message({
            "type": "connected",
            "message": "Driver connected successfully",
            "driver_id": driver_id
        }, driver_id)
        
        while True:
            # Receive location update
            data = await websocket.receive_json()
            
            if data.get("type") == "location":
                latitude = data.get("latitude")
                longitude = data.get("longitude")
                speed = data.get("speed", 0)
                heading = data.get("heading", 0)
                
                # Update driver location in DB
                await db.drivers.update_one(
                    {"id": driver_id},
                    {
                        "$set": {
                            "current_latitude": latitude,
                            "current_longitude": longitude,
                            "last_location_update": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                # Store location event
                from models import LocationEvent
                location_event = LocationEvent(
                    driver_id=driver_id,
                    latitude=latitude,
                    longitude=longitude,
                    speed=speed,
                    heading=heading
                )
                
                location_dict = location_event.model_dump()
                location_dict['timestamp'] = location_dict['timestamp'].isoformat()
                
                await db.location_events.insert_one(location_dict)
                
                # Broadcast to vendor room
                await manager.broadcast_to_room(f"vendor_{vendor_id}", {
                    "type": "driver_location",
                    "driver_id": driver_id,
                    "latitude": latitude,
                    "longitude": longitude,
                    "speed": speed,
                    "heading": heading,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # If driver has active order, broadcast to order room
                active_order = await db.orders.find_one({
                    "driver_id": driver_id,
                    "status": {"$in": ["driver_assigned", "picked_up", "out_for_delivery"]}
                }, {"_id": 0})
                
                if active_order:
                    order_id = active_order["id"]
                    
                    # Calculate ETA
                    eta_minutes = calculate_eta(
                        (latitude, longitude),
                        (active_order["delivery_latitude"], active_order["delivery_longitude"])
                    )
                    
                    # Broadcast to order tracking room
                    await manager.broadcast_to_room(f"order_{order_id}", {
                        "type": "driver_location",
                        "order_id": order_id,
                        "driver_id": driver_id,
                        "latitude": latitude,
                        "longitude": longitude,
                        "eta_minutes": eta_minutes,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
    
    except WebSocketDisconnect:
        manager.disconnect(driver_id)
        logger.info(f"Driver {driver_id} disconnected")
    except Exception as e:
        logger.error(f"Error in driver WebSocket: {e}")
        if driver_id:
            manager.disconnect(driver_id)

async def handle_vendor_tracking(websocket: WebSocket, vendor_id: str, token: str = Query(...)):
    """
    WebSocket handler for vendor to track all drivers
    """
    try:
        # Authenticate
        user = await websocket_auth(token)
        
        if user["role"] not in ["vendor", "admin"]:
            await websocket.close(code=1008, reason="Access denied")
            return
        
        # Connect
        await manager.connect(websocket, f"vendor_user_{user['id']}")
        
        # Join vendor room
        manager.join_room(f"vendor_{vendor_id}", f"vendor_user_{user['id']}")
        
        # Send initial driver locations
        drivers = await db.drivers.find({"vendor_id": vendor_id}, {"_id": 0}).to_list(1000)
        
        await manager.send_personal_message({
            "type": "initial_state",
            "drivers": [
                {
                    "driver_id": d["id"],
                    "driver_name": d["full_name"],
                    "status": d["status"],
                    "latitude": d.get("current_latitude"),
                    "longitude": d.get("current_longitude"),
                    "last_update": d.get("last_location_update")
                }
                for d in drivers
            ]
        }, f"vendor_user_{user['id']}")
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        manager.disconnect(f"vendor_user_{user['id']}")
        logger.info(f"Vendor user {user['id']} disconnected")
    except Exception as e:
        logger.error(f"Error in vendor WebSocket: {e}")
        manager.disconnect(f"vendor_user_{user['id']}")

async def handle_order_tracking(websocket: WebSocket, tracking_token: str):
    """
    WebSocket handler for public order tracking
    No authentication required - uses tracking token
    """
    order = None
    user_id = None
    
    try:
        # Verify tracking token
        order = await db.orders.find_one({"tracking_token": tracking_token}, {"_id": 0})
        if not order:
            await websocket.close(code=1008, reason="Invalid tracking token")
            return
        
        user_id = f"tracking_{tracking_token}"
        order_id = order["id"]
        
        # Connect
        await manager.connect(websocket, user_id)
        
        # Join order room
        manager.join_room(f"order_{order_id}", user_id)
        
        # Send initial state
        driver_location = None
        if order.get("driver_id"):
            driver = await db.drivers.find_one({"id": order["driver_id"]}, {"_id": 0})
            if driver:
                driver_location = {
                    "latitude": driver.get("current_latitude"),
                    "longitude": driver.get("current_longitude"),
                    "last_update": driver.get("last_location_update")
                }
        
        await manager.send_personal_message({
            "type": "initial_state",
            "order": {
                "order_number": order["order_number"],
                "status": order["status"],
                "delivery_address": order["delivery_address"]
            },
            "driver_location": driver_location
        }, user_id)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
        logger.info(f"Tracking user disconnected: {tracking_token}")
    except Exception as e:
        logger.error(f"Error in tracking WebSocket: {e}")
        if user_id:
            manager.disconnect(user_id)