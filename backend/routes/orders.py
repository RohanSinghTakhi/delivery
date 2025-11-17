from fastapi import APIRouter, HTTPException, status, Depends, Query
from motor.motor_asyncio import AsyncIOMotorClient
from models import Order, OrderCreate, OrderResponse, OrderStatus
from middleware import get_current_user, require_role
from utils import get_coordinates, calculate_distance
import os
from datetime import datetime, timezone
from typing import List, Optional

router = APIRouter(prefix="/orders", tags=["Orders"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_data: OrderCreate, current_user: dict = Depends(get_current_user)):
    """
    Create a new order (User role)
    """
    # Validate coordinates if not provided
    if not order_data.pickup_latitude or not order_data.pickup_longitude:
        pickup_coords = get_coordinates(order_data.pickup_address)
        if pickup_coords:
            order_data.pickup_latitude, order_data.pickup_longitude = pickup_coords
    
    if not order_data.delivery_latitude or not order_data.delivery_longitude:
        delivery_coords = get_coordinates(order_data.delivery_address)
        if delivery_coords:
            order_data.delivery_latitude, order_data.delivery_longitude = delivery_coords
    
    # Calculate distance
    distance = calculate_distance(
        (order_data.pickup_latitude, order_data.pickup_longitude),
        (order_data.delivery_latitude, order_data.delivery_longitude)
    )
    
    # Create order
    order = Order(**order_data.model_dump())
    order.estimated_distance_km = distance
    order.delivery_fee = round(distance * 2.5, 2) if distance else 0  # $2.5 per km
    
    # Save to database
    order_dict = order.model_dump()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    order_dict['updated_at'] = order_dict['updated_at'].isoformat()
    
    await db.orders.insert_one(order_dict)
    
    return OrderResponse(**order.model_dump())

@router.get("", response_model=List[OrderResponse])
async def get_orders(
    vendor_id: Optional[str] = Query(None),
    driver_id: Optional[str] = Query(None),
    status: Optional[OrderStatus] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get orders with filters
    """
    query = {}
    
    # Role-based filtering
    if current_user["role"] == "user":
        query["user_id"] = current_user["id"]
    elif current_user["role"] == "vendor" and vendor_id:
        query["vendor_id"] = vendor_id
    elif current_user["role"] == "driver" and driver_id:
        query["driver_id"] = driver_id
    
    if vendor_id and current_user["role"] in ["admin", "vendor"]:
        query["vendor_id"] = vendor_id
    
    if driver_id and current_user["role"] in ["admin", "vendor", "driver"]:
        query["driver_id"] = driver_id
    
    if status:
        query["status"] = status
    
    orders = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Parse datetime strings
    for order in orders:
        if isinstance(order.get('created_at'), str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if isinstance(order.get('updated_at'), str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return [OrderResponse(**order) for order in orders]

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get specific order by ID
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check access permissions
    if current_user["role"] == "user" and order["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Parse datetime
    if isinstance(order.get('created_at'), str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order.get('updated_at'), str):
        order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return OrderResponse(**order)

@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    new_status: OrderStatus,
    current_user: dict = Depends(get_current_user)
):
    """
    Update order status (Vendor/Driver role)
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update timestamps based on status
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if new_status == OrderStatus.ACCEPTED:
        update_data["accepted_at"] = datetime.now(timezone.utc).isoformat()
    elif new_status == OrderStatus.PICKED_UP:
        update_data["picked_up_at"] = datetime.now(timezone.utc).isoformat()
    elif new_status == OrderStatus.OUT_FOR_DELIVERY:
        update_data["out_for_delivery_at"] = datetime.now(timezone.utc).isoformat()
    elif new_status == OrderStatus.DELIVERED:
        update_data["delivered_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.orders.update_one({"id": order_id}, {"$set": update_data})
    
    # Fetch updated order
    updated_order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    
    # Parse datetime
    if isinstance(updated_order.get('created_at'), str):
        updated_order['created_at'] = datetime.fromisoformat(updated_order['created_at'])
    if isinstance(updated_order.get('updated_at'), str):
        updated_order['updated_at'] = datetime.fromisoformat(updated_order['updated_at'])
    
    return OrderResponse(**updated_order)

@router.post("/{order_id}/assign", response_model=dict)
async def assign_driver(
    order_id: str,
    driver_id: str,
    current_user: dict = Depends(require_role(["vendor", "admin"]))
):
    """
    Assign driver to order (Vendor/Admin role)
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    driver = await db.drivers.find_one({"id": driver_id}, {"_id": 0})
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    
    # Update order
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "driver_id": driver_id,
                "status": OrderStatus.DRIVER_ASSIGNED,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Create assignment
    from models import Assignment
    assignment = Assignment(
        order_id=order_id,
        driver_id=driver_id,
        vendor_id=order["vendor_id"]
    )
    
    assignment_dict = assignment.model_dump()
    assignment_dict['assigned_at'] = assignment_dict['assigned_at'].isoformat()
    
    await db.assignments.insert_one(assignment_dict)
    
    # Update order with assignment ID
    await db.orders.update_one(
        {"id": order_id},
        {"$set": {"assignment_id": assignment.id}}
    )
    
    return {
        "message": "Driver assigned successfully",
        "order_id": order_id,
        "driver_id": driver_id,
        "assignment_id": assignment.id
    }