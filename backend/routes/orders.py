from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from motor.motor_asyncio import AsyncIOMotorClient
from models import (
    Order,
    OrderCreate,
    OrderResponse,
    OrderStatus,
    CustomerLocationUpdate,
    Assignment,
    AssignmentDecision,
    AssignmentStatus
)
from middleware import get_current_user, require_role
from utils import (
    get_coordinates,
    calculate_distance,
    calculate_eta,
    get_route_polyline,
    save_upload_file,
    get_file_url
)
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
        if order.get("driver_id"):
            await db.drivers.update_one(
                {"id": order["driver_id"]},
                {
                    "$inc": {
                        "total_deliveries": 1,
                        "total_earnings": order.get("delivery_fee", 0)
                    }
                }
            )
        if order.get("assignment_id"):
            await db.assignments.update_one(
                {"id": order["assignment_id"]},
                {
                    "$set": {
                        "status": AssignmentStatus.COMPLETED,
                        "completed_at": update_data["delivered_at"]
                    }
                }
            )
    
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

@router.post("/{order_id}/assignment/respond", response_model=dict)
async def respond_to_assignment(
    order_id: str,
    decision: AssignmentDecision,
    current_user: dict = Depends(get_current_user)
):
    """
    Drivers accept/decline assignment; vendors/admin can override
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    driver_id = order.get("driver_id")
    if not driver_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order has no assigned driver")
    
    # Determine acting role
    role = current_user["role"]
    if role == "driver":
        acting_driver_id = await _get_driver_id_for_user(current_user["id"])
        if acting_driver_id != driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "vendor":
        vendor_id = await _get_vendor_id_for_user(current_user["id"])
        if vendor_id != order["vendor_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    assignment = None
    if order.get("assignment_id"):
        assignment = await db.assignments.find_one({"id": order["assignment_id"]}, {"_id": 0})
    if not assignment:
        assignment = await db.assignments.find_one(
            {"order_id": order_id, "driver_id": driver_id},
            {"_id": 0}
        )
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment record not found")
    
    now_iso = datetime.now(timezone.utc).isoformat()
    decision_value = decision.action
    
    if decision_value == "accept":
        await db.assignments.update_one(
            {"id": assignment["id"]},
            {
                "$set": {
                    "status": AssignmentStatus.ACCEPTED,
                    "accepted_at": now_iso,
                    "decline_reason": None
                }
            }
        )
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {"status": OrderStatus.DRIVER_ASSIGNED, "updated_at": now_iso}}
        )
        result_message = "Assignment accepted"
    else:
        await db.assignments.update_one(
            {"id": assignment["id"]},
            {
                "$set": {
                    "status": AssignmentStatus.DECLINED,
                    "declined_at": now_iso,
                    "decline_reason": decision.reason
                }
            }
        )
        await db.orders.update_one(
            {"id": order_id},
            {
                "$set": {
                    "status": OrderStatus.ACCEPTED,
                    "driver_id": None,
                    "assignment_id": None,
                    "updated_at": now_iso
                }
            }
        )
        result_message = "Assignment declined"
    
    return {
        "message": result_message,
        "order_id": order_id,
        "assignment_id": assignment["id"],
        "status": decision_value
    }

async def _get_vendor_id_for_user(user_id: str) -> Optional[str]:
    vendor = await db.vendors.find_one({"user_id": user_id}, {"_id": 0, "id": 1})
    return vendor["id"] if vendor else None

async def _get_driver_id_for_user(user_id: str) -> Optional[str]:
    driver = await db.drivers.find_one({"user_id": user_id}, {"_id": 0, "id": 1})
    return driver["id"] if driver else None

def _format_datetime(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value

async def _ensure_order_access(order: dict, current_user: dict):
    role = current_user["role"]
    if role == "user":
        if order["user_id"] != current_user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "vendor":
        vendor_id = await _get_vendor_id_for_user(current_user["id"])
        if vendor_id != order["vendor_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "driver":
        driver_id = await _get_driver_id_for_user(current_user["id"])
        if not driver_id or order.get("driver_id") != driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

@router.post("/{order_id}/customer-location", response_model=dict)
async def update_customer_location(
    order_id: str,
    location: CustomerLocationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Allow customer app (or assigned driver/vendor) to push live location updates
    """
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    role = current_user["role"]
    
    if role == "user" and order["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "vendor":
        vendor_id = await _get_vendor_id_for_user(current_user["id"])
        if vendor_id != order["vendor_id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role == "driver":
        driver_id = await _get_driver_id_for_user(current_user["id"])
        if not driver_id or order.get("driver_id") != driver_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    elif role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    update_payload = {
        "customer_current_latitude": location.latitude,
        "customer_current_longitude": location.longitude,
        "customer_location_accuracy": location.accuracy,
        "customer_location_heading": location.heading,
        "customer_location_speed": location.speed,
        "customer_last_location_update": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.orders.update_one({"id": order_id}, {"$set": update_payload})
    
    return {
        "message": "Customer location updated",
        "order_id": order_id,
        "location": {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "accuracy": location.accuracy,
            "heading": location.heading,
            "speed": location.speed,
            "updated_at": update_payload["customer_last_location_update"]
        }
    }

@router.get("/{order_id}/live", response_model=dict)
async def get_live_order_snapshot(order_id: str, current_user: dict = Depends(get_current_user)):
    """
    Provide a live snapshot combining order info, customer share, and driver GPS
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    await _ensure_order_access(order, current_user)
    
    driver_snapshot = None
    eta_minutes = None
    route_polyline = None
    
    if order.get("driver_id"):
        driver = await db.drivers.find_one(
            {"id": order["driver_id"]},
            {
                "_id": 0,
                "id": 1,
                "full_name": 1,
                "phone": 1,
                "current_latitude": 1,
                "current_longitude": 1,
                "last_location_update": 1,
                "status": 1
            }
        )
        if driver and driver.get("current_latitude") and driver.get("current_longitude"):
            driver_snapshot = {
                "id": driver["id"],
                "name": driver["full_name"],
                "phone": driver["phone"],
                "status": driver.get("status"),
                "latitude": driver["current_latitude"],
                "longitude": driver["current_longitude"],
                "last_update": _format_datetime(driver.get("last_location_update"))
            }
            eta_minutes = calculate_eta(
                (driver["current_latitude"], driver["current_longitude"]),
                (order["delivery_latitude"], order["delivery_longitude"])
            )
            try:
                route_polyline = get_route_polyline(
                    (driver["current_latitude"], driver["current_longitude"]),
                    (order["delivery_latitude"], order["delivery_longitude"])
                )
            except Exception:
                route_polyline = None
    
    customer_location = None
    if order.get("customer_current_latitude") and order.get("customer_current_longitude"):
        customer_location = {
            "latitude": order["customer_current_latitude"],
            "longitude": order["customer_current_longitude"],
            "accuracy": order.get("customer_location_accuracy"),
            "heading": order.get("customer_location_heading"),
            "speed": order.get("customer_location_speed"),
            "last_update": _format_datetime(order.get("customer_last_location_update"))
        }
    
    return {
        "order": {
            "id": order["id"],
            "order_number": order["order_number"],
            "status": order["status"],
            "driver_id": order.get("driver_id"),
            "tracking_token": order["tracking_token"],
            "delivery_latitude": order["delivery_latitude"],
            "delivery_longitude": order["delivery_longitude"],
            "created_at": _format_datetime(order.get("created_at")),
            "updated_at": _format_datetime(order.get("updated_at"))
        },
        "driver": driver_snapshot,
        "customer_location": customer_location,
        "eta_minutes": eta_minutes,
        "route_polyline": route_polyline
    }

@router.post("/{order_id}/proof", response_model=dict)
async def upload_order_proof(
    order_id: str,
    proof_type: str = Form("photo"),
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload proof of delivery assets (photo/signature) tied to order
    """
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    await _ensure_order_access(order, current_user)
    
    allowed_types = {"photo": "proof", "signature": "signatures"}
    proof_key = proof_type.lower()
    if proof_key not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof type")
    
    saved_path = await save_upload_file(file, subfolder=allowed_types[proof_key])
    file_url = get_file_url(saved_path)
    
    field_map = {
        "photo": "proof_photo_url",
        "signature": "signature_url"
    }
    
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                field_map[proof_key]: file_url,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "message": "Proof uploaded",
        "order_id": order_id,
        "type": proof_key,
        "file_url": file_url
    }