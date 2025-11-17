from fastapi import APIRouter, HTTPException, status, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from models import Vendor, VendorCreate, VendorResponse, User
from middleware import get_current_user
from utils import get_password_hash, get_coordinates
import os
from datetime import datetime
from typing import List

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