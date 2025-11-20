from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from models import (
    Driver,
    DriverCreate,
    DriverResponse,
    DriverStatus,
    DriverLogin,
    DriverPushTokenUpdate,
    User,
    OrderStatus
)
from middleware import get_current_user, require_role
from utils import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    calculate_eta
)
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict
from socket_handlers.manager import manager

router = APIRouter(prefix="/drivers", tags=["Drivers"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_driver(driver_data: DriverCreate):
    """
    Register a new driver
    """
    # Check if email already exists
    existing_user = await db.users.find_one({"email": driver_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user account
    user = User(
        email=driver_data.email,
        full_name=driver_data.full_name,
        phone=driver_data.phone,
        role="driver",
        hashed_password=get_password_hash(driver_data.password)
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Create driver profile
    driver = Driver(
        full_name=driver_data.full_name,
        email=driver_data.email,
        phone=driver_data.phone,
        vehicle_type=driver_data.vehicle_type,
        vehicle_number=driver_data.vehicle_number,
        license_number=driver_data.license_number,
        user_id=user.id,
        vendor_id=driver_data.vendor_id
    )
    
    driver_dict = driver.model_dump()
    driver_dict['created_at'] = driver_dict['created_at'].isoformat()
    driver_dict['updated_at'] = driver_dict['updated_at'].isoformat()
    
    await db.drivers.insert_one(driver_dict)
    
    # Add driver to vendor's driver list
    await db.vendors.update_one(
        {"id": driver_data.vendor_id},
        {"$push": {"driver_ids": driver.id}}
    )
    
    return {
        "message": "Driver registered successfully",
        "driver_id": driver.id,
        "user_id": user.id
    }

@router.post("/login", response_model=dict)
async def driver_login(credentials: DriverLogin):
    """
    Driver-specific login returning tokens + driver profile
    """
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or user.get("role") != "driver":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    driver = await db.drivers.find_one({"user_id": user["id"]}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver profile not found")
    
    update_payload = {
        "device_platform": credentials.device_platform,
        "push_token": credentials.push_token,
        "push_token_updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.drivers.update_one({"id": driver["id"]}, {"$set": update_payload})
    driver.update({k: v for k, v in update_payload.items() if v is not None})
    
    access_token = create_access_token({"sub": user["id"], "role": "driver"})
    refresh_token = create_refresh_token({"sub": user["id"]})
    
    return {
        "message": "Driver login successful",
        "driver": driver,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    }

@router.get("", response_model=List[DriverResponse])
async def get_drivers(
    vendor_id: str = None,
    status: DriverStatus = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get drivers with filters
    """
    query = {}
    
    if vendor_id:
        query["vendor_id"] = vendor_id
    
    if status:
        query["status"] = status
    
    drivers = await db.drivers.find(query, {"_id": 0}).to_list(1000)
    
    # Parse datetime strings
    for driver in drivers:
        if isinstance(driver.get('created_at'), str):
            driver['created_at'] = datetime.fromisoformat(driver['created_at'])
        if isinstance(driver.get('updated_at'), str):
            driver['updated_at'] = datetime.fromisoformat(driver['updated_at'])
        if driver.get('last_location_update') and isinstance(driver['last_location_update'], str):
            driver['last_location_update'] = datetime.fromisoformat(driver['last_location_update'])
    
    return [DriverResponse(**driver) for driver in drivers]

@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get specific driver by ID
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Parse datetime
    if isinstance(driver.get('created_at'), str):
        driver['created_at'] = datetime.fromisoformat(driver['created_at'])
    if isinstance(driver.get('updated_at'), str):
        driver['updated_at'] = datetime.fromisoformat(driver['updated_at'])
    if driver.get('last_location_update') and isinstance(driver['last_location_update'], str):
        driver['last_location_update'] = datetime.fromisoformat(driver['last_location_update'])
    
    return DriverResponse(**driver)

@router.patch("/{driver_id}/status", response_model=dict)
async def update_driver_status(
    driver_id: str,
    new_status: DriverStatus,
    current_user: dict = Depends(get_current_user)
):
    """
    Update driver status (online/offline/busy)
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Check permission
    if current_user["role"] == "driver" and driver["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    await db.drivers.update_one(
        {"id": driver_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": "Driver status updated",
        "driver_id": driver_id,
        "status": new_status
    }

@router.post("/{driver_id}/location", response_model=dict)
async def update_driver_location(
    driver_id: str,
    latitude: float,
    longitude: float,
    current_user: dict = Depends(get_current_user)
):
    """
    Update driver location (HTTP fallback for WebSocket)
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Check permission
    if current_user["role"] == "driver" and driver["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update driver location
    await db.drivers.update_one(
        {"id": driver_id},
        {
            "$set": {
                "current_latitude": latitude,
                "current_longitude": longitude,
                "last_location_update": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Store location event
    from models import LocationEvent
    location_event = LocationEvent(
        driver_id=driver_id,
        latitude=latitude,
        longitude=longitude
    )
    
    location_dict = location_event.model_dump()
    location_dict['timestamp'] = location_dict['timestamp'].isoformat()
    
    await db.location_events.insert_one(location_dict)
    
    # Broadcast updates to vendor and active order rooms
    await manager.broadcast_to_room(f"vendor_{driver['vendor_id']}", {
        "type": "driver_location",
        "driver_id": driver_id,
        "latitude": latitude,
        "longitude": longitude,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    active_order = await db.orders.find_one({
        "driver_id": driver_id,
        "status": {"$in": [OrderStatus.DRIVER_ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.OUT_FOR_DELIVERY]}
    }, {"_id": 0})
    
    if active_order:
        eta_minutes = calculate_eta(
            (latitude, longitude),
            (active_order["delivery_latitude"], active_order["delivery_longitude"])
        )
        await manager.broadcast_to_room(f"order_{active_order['id']}", {
            "type": "driver_location",
            "order_id": active_order["id"],
            "driver_id": driver_id,
            "latitude": latitude,
            "longitude": longitude,
            "eta_minutes": eta_minutes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "message": "Location updated",
        "driver_id": driver_id,
        "latitude": latitude,
        "longitude": longitude
    }

async def _get_vendor_id_for_user(user_id: str) -> Optional[str]:
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1})
    return vendor["id"] if vendor else None

async def _get_driver_id_for_user(user_id: str) -> Optional[str]:
    driver = await db.drivers.find_one({"user_id": user_id}, {"_id": 0, "id": 1})
    return driver["id"] if driver else None

def _format_dt(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value

async def _ensure_driver_access(driver: dict, current_user: dict):
    role = current_user["role"]
    if role == "driver":
        driver_id = await _get_driver_id_for_user(current_user["id"])
        if driver_id != driver["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "vendor":
        vendor_id = await _get_vendor_id_for_user(current_user["id"])
        if vendor_id != driver["vendor_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

@router.get("/{driver_id}/orders/active", response_model=dict)
async def get_active_orders_for_driver(driver_id: str, current_user: dict = Depends(get_current_user)):
    """
    Driver or vendor can fetch live assignments with customer map data
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    
    await _ensure_driver_access(driver, current_user)
    
    orders = await db.orders.find(
        {
            "driver_id": driver_id,
            "status": {"$nin": [OrderStatus.DELIVERED, OrderStatus.CANCELLED]}
        },
        {
            "_id": 0,
            "id": 1,
            "order_number": 1,
            "status": 1,
            "pickup_address": 1,
            "pickup_latitude": 1,
            "pickup_longitude": 1,
            "delivery_address": 1,
            "delivery_latitude": 1,
            "delivery_longitude": 1,
            "customer_name": 1,
            "customer_phone": 1,
            "customer_current_latitude": 1,
            "customer_current_longitude": 1,
            "customer_last_location_update": 1,
            "notes": 1,
            "created_at": 1,
            "updated_at": 1
        }
    ).sort("created_at", -1).to_list(100)
    
    formatted_orders = []
    for order in orders:
        formatted_orders.append({
            "id": order["id"],
            "order_number": order["order_number"],
            "status": order["status"],
            "pickup": {
                "address": order.get("pickup_address"),
                "latitude": order.get("pickup_latitude"),
                "longitude": order.get("pickup_longitude")
            },
            "dropoff": {
                "address": order.get("delivery_address"),
                "latitude": order.get("delivery_latitude"),
                "longitude": order.get("delivery_longitude")
            },
            "customer": {
                "name": order.get("customer_name"),
                "phone": order.get("customer_phone")
            },
            "customer_live_location": {
                "latitude": order.get("customer_current_latitude"),
                "longitude": order.get("customer_current_longitude"),
                "last_update": order.get("customer_last_location_update")
            } if order.get("customer_current_latitude") and order.get("customer_current_longitude") else None,
            "notes": order.get("notes"),
            "created_at": _format_dt(order.get("created_at")),
            "updated_at": _format_dt(order.get("updated_at"))
        })
    
    return {
        "driver_id": driver_id,
        "orders": formatted_orders
    }

@router.get("/{driver_id}/live", response_model=dict)
async def get_driver_live_state(driver_id: str, current_user: dict = Depends(get_current_user)):
    """
    Returns driver's current location, status, and today's stats
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    
    await _ensure_driver_access(driver, current_user)
    
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    delivered_count = await db.orders.count_documents({
        "driver_id": driver_id,
        "status": OrderStatus.DELIVERED,
        "delivered_at": {"$gte": start_of_day.isoformat(), "$lte": now.isoformat()}
    })
    
    active_orders = await db.orders.find(
        {
            "driver_id": driver_id,
            "status": {"$nin": [OrderStatus.DELIVERED, OrderStatus.CANCELLED]}
        },
        {"_id": 0, "id": 1, "order_number": 1, "status": 1}
    ).to_list(20)
    
    return {
        "driver": {
            "id": driver["id"],
            "name": driver["full_name"],
            "status": driver.get("status"),
            "location": {
                "latitude": driver.get("current_latitude"),
                "longitude": driver.get("current_longitude"),
                "last_update": _format_dt(driver.get("last_location_update"))
            }
        },
        "active_orders": active_orders,
        "today": {
            "completed": delivered_count
        },
        "generated_at": now.isoformat()
    }

@router.post("/{driver_id}/push-token", response_model=dict)
async def update_driver_push_token(
    driver_id: str,
    payload: DriverPushTokenUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Store/update push notification token for driver device
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    
    await _ensure_driver_access(driver, current_user)
    
    update_payload = {
        "push_token": payload.push_token,
        "device_platform": payload.device_platform,
        "push_token_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.drivers.update_one({"id": driver_id}, {"$set": update_payload})
    
    return {
        "message": "Push token updated",
        "driver_id": driver_id
    }

@router.get("/{driver_id}/analytics", response_model=dict)
async def get_driver_analytics(
    driver_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Detailed analytics for driver (distance, deliveries, durations)
    """
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    
    await _ensure_driver_access(driver, current_user)
    
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromisoformat(start_date) if start_date else now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.fromisoformat(end_date) if end_date else now
    
    orders = await db.orders.find(
        {
            "driver_id": driver_id,
            "created_at": {"$gte": start_dt.isoformat(), "$lte": end_dt.isoformat()}
        },
        {
            "_id": 0,
            "id": 1,
            "order_number": 1,
            "status": 1,
            "estimated_distance_km": 1,
            "actual_distance_km": 1,
            "created_at": 1,
            "picked_up_at": 1,
            "delivered_at": 1
        }
    ).to_list(2000)
    
    delivered = [o for o in orders if o["status"] == OrderStatus.DELIVERED]
    total_distance = sum(
        (o.get("actual_distance_km") or o.get("estimated_distance_km") or 0.0)
        for o in delivered
    )
    avg_duration = None
    if delivered:
        durations = []
        for o in delivered:
            start_ts = _format_dt(o.get("picked_up_at"))
            end_ts = _format_dt(o.get("delivered_at"))
            if start_ts and end_ts:
                durations.append((datetime.fromisoformat(end_ts) - datetime.fromisoformat(start_ts)).total_seconds() / 60)
        if durations:
            avg_duration = sum(durations) / len(durations)
    
    return {
        "driver_id": driver_id,
        "time_window": {
            "start": start_dt.isoformat(),
            "end": end_dt.isoformat()
        },
        "orders_total": len(orders),
        "orders_delivered": len(delivered),
        "total_distance_km": round(total_distance, 2),
        "average_delivery_minutes": round(avg_duration, 2) if avg_duration else None,
        "orders": orders
    }