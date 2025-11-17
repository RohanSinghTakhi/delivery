from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from models import Driver, DriverCreate, DriverResponse, DriverStatus, User
from middleware import get_current_user, require_role
from utils import get_password_hash
import os
from datetime import datetime, timezone
from typing import List

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
    
    return {
        "message": "Location updated",
        "driver_id": driver_id,
        "latitude": latitude,
        "longitude": longitude
    }