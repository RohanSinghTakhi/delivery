from fastapi import APIRouter, Depends, HTTPException, status
from middleware import get_current_user
from models import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RoutePoint
)
from utils import optimize_route

router = APIRouter(prefix="/routes", tags=["Routes"])

@router.post("/optimize", response_model=RouteOptimizationResponse)
async def optimize_delivery_route(
    payload: RouteOptimizationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Optimize the order of multiple stops using Google Directions API.
    Accessible to vendors, drivers, and admins.
    """
    if current_user["role"] not in ["vendor", "driver", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if not payload.stops:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one stop is required"
        )
    
    origin_tuple = (payload.origin.latitude, payload.origin.longitude)
    destination_point = payload.destination or payload.origin
    destination_tuple = (destination_point.latitude, destination_point.longitude)
    waypoint_tuples = [(stop.latitude, stop.longitude) for stop in payload.stops]
    
    optimization = optimize_route(origin_tuple, waypoint_tuples, destination_tuple)
    if not optimization:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to optimize route at this time"
        )
    
    ordered_stops = [
        payload.stops[index]
        for index in optimization["waypoint_order"]
    ]
    
    return RouteOptimizationResponse(
        origin=payload.origin,
        destination=destination_point,
        ordered_stops=ordered_stops,
        waypoint_order=optimization["waypoint_order"],
        total_distance_km=optimization.get("total_distance_km"),
        total_duration_minutes=optimization.get("total_duration_minutes"),
        polyline=optimization.get("polyline")
    )

