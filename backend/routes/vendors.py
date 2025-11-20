from fastapi import APIRouter, HTTPException, status, Depends, Query
from motor.motor_asyncio import AsyncIOMotorClient
from models import Vendor, VendorCreate, VendorResponse, User, OrderStatus
from middleware import get_current_user
from utils import get_password_hash, get_coordinates
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict

router = APIRouter(prefix="/vendors", tags=["Vendors"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_vendor(vendor_data: VendorCreate):
    """
    Register a new vendor
    """
    # Check if email already exists
    existing_user = await db.users.find_one({"email": vendor_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user account
    user = User(
        email=vendor_data.email,
        full_name=vendor_data.business_name,
        phone=vendor_data.phone,
        role="vendor",
        hashed_password=get_password_hash(vendor_data.password)
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    user_dict['updated_at'] = user_dict['updated_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Get coordinates for address
    coords = get_coordinates(vendor_data.address)
    if coords:
        vendor_data.latitude, vendor_data.longitude = coords
    
    # Create vendor profile
    vendor = Vendor(
        business_name=vendor_data.business_name,
        email=vendor_data.email,
        phone=vendor_data.phone,
        address=vendor_data.address,
        latitude=vendor_data.latitude,
        longitude=vendor_data.longitude,
        user_id=user.id
    )
    
    vendor_dict = vendor.model_dump()
    vendor_dict['created_at'] = vendor_dict['created_at'].isoformat()
    vendor_dict['updated_at'] = vendor_dict['updated_at'].isoformat()
    
    await db.vendors.insert_one(vendor_dict)
    
    return {
        "message": "Vendor registered successfully",
        "vendor_id": vendor.id,
        "user_id": user.id
    }

@router.get("", response_model=List[VendorResponse])
async def get_vendors(current_user: dict = Depends(get_current_user)):
    """
    Get all vendors
    """
    vendors = await db.vendors.find({}, {"_id": 0}).to_list(1000)
    
    # Parse datetime strings
    for vendor in vendors:
        if isinstance(vendor.get('created_at'), str):
            vendor['created_at'] = datetime.fromisoformat(vendor['created_at'])
        if isinstance(vendor.get('updated_at'), str):
            vendor['updated_at'] = datetime.fromisoformat(vendor['updated_at'])
    
    return [VendorResponse(**vendor) for vendor in vendors]

@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(vendor_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get specific vendor by ID
    """
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Parse datetime
    if isinstance(vendor.get('created_at'), str):
        vendor['created_at'] = datetime.fromisoformat(vendor['created_at'])
    if isinstance(vendor.get('updated_at'), str):
        vendor['updated_at'] = datetime.fromisoformat(vendor['updated_at'])
    
    return VendorResponse(**vendor)

@router.get("/{vendor_id}/drivers")
async def get_vendor_drivers(vendor_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get all drivers for a vendor
    """
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    driver_ids = vendor.get("driver_ids", [])
    
    if not driver_ids:
        return []
    
    drivers = await db.drivers.find({"id": {"$in": driver_ids}}, {"_id": 0}).to_list(1000)
    
    # Parse datetime strings
    for driver in drivers:
        if isinstance(driver.get('created_at'), str):
            driver['created_at'] = datetime.fromisoformat(driver['created_at'])
        if isinstance(driver.get('updated_at'), str):
            driver['updated_at'] = datetime.fromisoformat(driver['updated_at'])
        if driver.get('last_location_update') and isinstance(driver['last_location_update'], str):
            driver['last_location_update'] = datetime.fromisoformat(driver['last_location_update'])
    
    return drivers

def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)

async def _get_vendor_profile_for_user(user_id: str) -> Optional[Dict]:
    return await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1})

@router.get("/{vendor_id}/fleet/live")
async def get_vendor_fleet_live(vendor_id: str, current_user: dict = Depends(get_current_user)):
    """
    Returns live snapshot of all drivers for a vendor, including active orders
    """
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    
    if current_user["role"] == "vendor":
        vendor_profile = await _get_vendor_profile_for_user(current_user["id"])
        if not vendor_profile or vendor_profile["id"] != vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    drivers = await db.drivers.find(
        {"vendor_id": vendor_id},
        {
            "_id": 0,
            "id": 1,
            "full_name": 1,
            "phone": 1,
            "status": 1,
            "current_latitude": 1,
            "current_longitude": 1,
            "last_location_update": 1
        }
    ).to_list(1000)
    
    driver_ids = [driver["id"] for driver in drivers]
    
    active_orders_by_driver: Dict[str, List[dict]] = {}
    if driver_ids:
        active_orders = await db.orders.find(
            {
                "driver_id": {"$in": driver_ids},
                "status": {"$nin": [OrderStatus.DELIVERED, OrderStatus.CANCELLED]}
            },
            {
                "_id": 0,
                "id": 1,
                "order_number": 1,
                "driver_id": 1,
                "status": 1,
                "customer_name": 1,
                "delivery_latitude": 1,
                "delivery_longitude": 1,
                "customer_current_latitude": 1,
                "customer_current_longitude": 1,
                "customer_last_location_update": 1
            }
        ).to_list(1000)
        
        for order in active_orders:
            driver_list = active_orders_by_driver.setdefault(order["driver_id"], [])
            driver_list.append({
                "order_id": order["id"],
                "order_number": order["order_number"],
                "status": order["status"],
                "customer_name": order.get("customer_name"),
                "delivery_latitude": order.get("delivery_latitude"),
                "delivery_longitude": order.get("delivery_longitude"),
                "customer_live_location": {
                    "latitude": order.get("customer_current_latitude"),
                    "longitude": order.get("customer_current_longitude"),
                    "last_update": order.get("customer_last_location_update")
                } if order.get("customer_current_latitude") and order.get("customer_current_longitude") else None
            })
    
    fleet = []
    for driver in drivers:
        fleet.append({
            "driver_id": driver["id"],
            "name": driver["full_name"],
            "phone": driver["phone"],
            "status": driver.get("status"),
            "location": {
                "latitude": driver.get("current_latitude"),
                "longitude": driver.get("current_longitude"),
                "last_update": _parse_iso_datetime(driver.get("last_location_update")).isoformat() if driver.get("last_location_update") else None
            },
            "active_orders": active_orders_by_driver.get(driver["id"], [])
        })
    
    return {
        "vendor_id": vendor_id,
        "drivers": fleet,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

@router.get("/{vendor_id}/drivers/report")
async def get_vendor_driver_report(
    vendor_id: str,
    start_date: Optional[str] = Query(None, description="ISO date/time"),
    end_date: Optional[str] = Query(None, description="ISO date/time"),
    current_user: dict = Depends(get_current_user)
):
    """
    Aggregated metrics per driver (completed deliveries, total distance, avg duration)
    """
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    
    if current_user["role"] == "vendor":
        vendor_profile = await _get_vendor_profile_for_user(current_user["id"])
        if not vendor_profile or vendor_profile["id"] != vendor_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    now = datetime.now(timezone.utc)
    start_dt = datetime.fromisoformat(start_date) if start_date else now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = datetime.fromisoformat(end_date) if end_date else now
    
    query: Dict = {
        "vendor_id": vendor_id,
        "status": OrderStatus.DELIVERED
    }
    
    query["delivered_at"] = {
        "$gte": start_dt.isoformat(),
        "$lte": end_dt.isoformat()
    }
    
    orders = await db.orders.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "order_number": 1,
            "driver_id": 1,
            "actual_distance_km": 1,
            "estimated_distance_km": 1,
            "picked_up_at": 1,
            "delivered_at": 1
        }
    ).to_list(5000)
    
    metrics: Dict[str, Dict] = {}
    for order in orders:
        driver_id = order.get("driver_id")
        if not driver_id:
            continue
        driver_metrics = metrics.setdefault(driver_id, {
            "driver_id": driver_id,
            "orders_delivered": 0,
            "total_distance_km": 0.0,
            "total_time_minutes": 0.0,
            "order_ids": []
        })
        driver_metrics["orders_delivered"] += 1
        driver_metrics["order_ids"].append(order["id"])
        distance = order.get("actual_distance_km") or order.get("estimated_distance_km") or 0.0
        driver_metrics["total_distance_km"] += distance
        
        picked_up = _parse_iso_datetime(order.get("picked_up_at"))
        delivered = _parse_iso_datetime(order.get("delivered_at"))
        if picked_up and delivered:
            driver_metrics["total_time_minutes"] += (delivered - picked_up).total_seconds() / 60
    
    driver_ids = list(metrics.keys())
    if driver_ids:
        driver_profiles = await db.drivers.find(
            {"id": {"$in": driver_ids}},
            {"_id": 0, "id": 1, "full_name": 1, "phone": 1}
        ).to_list(len(driver_ids))
    else:
        driver_profiles = []
    
    profile_lookup = {driver["id"]: driver for driver in driver_profiles}
    
    report = []
    for driver_id, stat in metrics.items():
        profile = profile_lookup.get(driver_id, {})
        avg_time = stat["total_time_minutes"] / stat["orders_delivered"] if stat["orders_delivered"] else 0.0
        report.append({
            "driver_id": driver_id,
            "driver_name": profile.get("full_name"),
            "phone": profile.get("phone"),
            "orders_delivered": stat["orders_delivered"],
            "total_distance_km": round(stat["total_distance_km"], 2),
            "average_delivery_time_minutes": round(avg_time, 2),
            "order_ids": stat["order_ids"]
        })
    
    return {
        "vendor_id": vendor_id,
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
        "drivers": report
    }