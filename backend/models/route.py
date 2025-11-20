from pydantic import BaseModel, Field
from typing import List, Optional

class RoutePoint(BaseModel):
    latitude: float
    longitude: float
    label: Optional[str] = None

class RouteOptimizationRequest(BaseModel):
    origin: RoutePoint
    destination: Optional[RoutePoint] = None
    stops: List[RoutePoint] = Field(default_factory=list, description="Waypoints to optimize")

class RouteOptimizationResponse(BaseModel):
    origin: RoutePoint
    destination: RoutePoint
    ordered_stops: List[RoutePoint]
    waypoint_order: List[int]
    total_distance_km: Optional[float] = None
    total_duration_minutes: Optional[float] = None
    polyline: Optional[str] = None

