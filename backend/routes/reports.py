from fastapi import APIRouter, HTTPException, status, Depends, Query
from motor.motor_asyncio import AsyncIOMotorClient
from middleware import get_current_user, require_role
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

router = APIRouter(prefix="/reports", tags=["Reports"])

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@router.get("/vendors/{vendor_id}")
async def get_vendor_report(
    vendor_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    current_user: dict = Depends(require_role(["vendor", "admin"]))
):
    """
    Get vendor daily report with per-driver statistics
    """
    vendor = await db.vendors.find_one({"id": vendor_id}, {"_id": 0})
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Parse date or use today
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )
    else:
        report_date = datetime.now(timezone.utc)
    
    # Get start and end of day
    start_of_day = report_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    
    # Get all drivers for this vendor
    drivers = await db.drivers.find({"vendor_id": vendor_id}, {"_id": 0}).to_list(1000)
    
    driver_reports = []
    total_deliveries = 0
    total_distance = 0
    total_earnings = 0
    
    for driver in drivers:
        # Get orders for this driver on this date
        orders = await db.orders.find({
            "driver_id": driver["id"],
            "delivered_at": {
                "$gte": start_of_day.isoformat(),
                "$lt": end_of_day.isoformat()
            },
            "status": "delivered"
        }, {"_id": 0}).to_list(1000)
        
        # Calculate stats
        deliveries_count = len(orders)
        total_km = sum([order.get("actual_distance_km", 0) for order in orders])
        earnings = sum([order.get("delivery_fee", 0) for order in orders])
        
        driver_reports.append({
            "driver_id": driver["id"],
            "driver_name": driver["full_name"],
            "vehicle_type": driver["vehicle_type"],
            "deliveries": deliveries_count,
            "total_km": round(total_km, 2),
            "earnings": round(earnings, 2)
        })
        
        total_deliveries += deliveries_count
        total_distance += total_km
        total_earnings += earnings
    
    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor["business_name"],
        "date": report_date.strftime("%Y-%m-%d"),
        "summary": {
            "total_deliveries": total_deliveries,
            "total_distance_km": round(total_distance, 2),
            "total_earnings": round(total_earnings, 2),
            "active_drivers": len([d for d in driver_reports if d["deliveries"] > 0])
        },
        "drivers": driver_reports
    }

@router.get("/drivers/{driver_id}")
async def get_driver_report(
    driver_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """
    Get driver earnings and delivery history
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
    
    # Build query
    query = {"driver_id": driver_id, "status": "delivered"}
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            try:
                date_filter["$gte"] = datetime.strptime(start_date, "%Y-%m-%d").isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                date_filter["$lt"] = end.isoformat()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        query["delivered_at"] = date_filter
    
    # Get orders
    orders = await db.orders.find(query, {"_id": 0}).sort("delivered_at", -1).to_list(1000)
    
    # Calculate stats
    total_deliveries = len(orders)
    total_earnings = sum([order.get("delivery_fee", 0) for order in orders])
    total_distance = sum([order.get("actual_distance_km", 0) for order in orders])
    
    return {
        "driver_id": driver_id,
        "driver_name": driver["full_name"],
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "stats": {
            "total_deliveries": total_deliveries,
            "total_earnings": round(total_earnings, 2),
            "total_distance_km": round(total_distance, 2),
            "average_per_delivery": round(total_earnings / total_deliveries, 2) if total_deliveries > 0 else 0
        },
        "orders": [
            {
                "order_number": order["order_number"],
                "delivered_at": order.get("delivered_at"),
                "distance_km": order.get("actual_distance_km", 0),
                "fee": order.get("delivery_fee", 0)
            }
            for order in orders[:50]  # Limit to recent 50
        ]
    }