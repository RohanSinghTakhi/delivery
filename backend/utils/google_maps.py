import os
import requests
from typing import Optional, Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

def get_coordinates(address: str) -> Optional[Tuple[float, float]]:
    """
    Geocode address to latitude/longitude using Google Geocoding API
    Returns: (latitude, longitude) or None
    """
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        logger.warning("Google Maps API key not configured. Using mock coordinates.")
        # Mock response for development
        return (40.7128, -74.0060)  # Default NYC coordinates
    
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data.get("results"):
            location = data["results"][0]["geometry"]["location"]
            return (location["lat"], location["lng"])
        else:
            logger.error(f"Geocoding failed: {data.get('status')}")
            return None
    except Exception as e:
        logger.error(f"Error in geocoding: {e}")
        return None

def calculate_distance(origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[float]:
    """
    Calculate distance in kilometers using Google Distance Matrix API
    Returns: distance in km or None
    """
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        logger.warning("Google Maps API key not configured. Using mock distance.")
        # Simple Haversine approximation for mock
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1 = origin
        lat2, lon2 = destination
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return round(km, 2)
    
    try:
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "origins": f"{origin[0]},{origin[1]}",
            "destinations": f"{destination[0]},{destination[1]}",
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data.get("rows"):
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                distance_meters = element["distance"]["value"]
                return round(distance_meters / 1000, 2)  # Convert to km
        
        logger.error(f"Distance calculation failed: {data.get('status')}")
        return None
    except Exception as e:
        logger.error(f"Error calculating distance: {e}")
        return None

def calculate_eta(driver_location: Tuple[float, float], destination: Tuple[float, float]) -> Optional[int]:
    """
    Calculate ETA in minutes using Google Directions API
    Returns: ETA in minutes or None
    """
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        logger.warning("Google Maps API key not configured. Using mock ETA.")
        # Mock: assume 30 km/h average speed
        distance = calculate_distance(driver_location, destination)
        if distance:
            return int((distance / 30) * 60)  # Convert to minutes
        return 15  # Default 15 minutes
    
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{driver_location[0]},{driver_location[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data.get("routes"):
            duration_seconds = data["routes"][0]["legs"][0]["duration"]["value"]
            return int(duration_seconds / 60)  # Convert to minutes
        
        logger.error(f"ETA calculation failed: {data.get('status')}")
        return None
    except Exception as e:
        logger.error(f"Error calculating ETA: {e}")
        return None

def get_route_polyline(origin: Tuple[float, float], destination: Tuple[float, float]) -> Optional[str]:
    """
    Get encoded polyline for route using Google Directions API
    Returns: encoded polyline string or None
    """
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        logger.warning("Google Maps API key not configured. Cannot generate polyline.")
        return None
    
    try:
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] == "OK" and data.get("routes"):
            polyline = data["routes"][0]["overview_polyline"]["points"]
            return polyline
        
        logger.error(f"Polyline generation failed: {data.get('status')}")
        return None
    except Exception as e:
        logger.error(f"Error getting polyline: {e}")
        return None

def optimize_route(
    origin: Tuple[float, float],
    waypoints: List[Tuple[float, float]],
    destination: Optional[Tuple[float, float]] = None
) -> Optional[Dict[str, Any]]:
    """
    Optimize route order using Google Directions API (optimize:true).
    Returns dict with waypoint order, distance, duration, polyline.
    """
    if not waypoints:
        return None
    
    destination = destination or origin
    
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        logger.warning("Google Maps API key not configured. Returning original waypoint order.")
        waypoint_order = list(range(len(waypoints)))
        total_distance = 0.0
        total_duration = 0.0
        prev = origin
        for idx in waypoint_order:
            wp = waypoints[idx]
            dist = calculate_distance(prev, wp) or 0
            total_distance += dist
            prev = wp
        total_distance += calculate_distance(prev, destination) or 0
        return {
            "waypoint_order": waypoint_order,
            "ordered_waypoints": waypoint_order,
            "total_distance_km": round(total_distance, 2),
            "total_duration_minutes": None,
            "polyline": None
        }
    
    try:
        waypoints_param = "optimize:true|" + "|".join(f"{lat},{lng}" for lat, lng in waypoints)
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "waypoints": waypoints_param,
            "key": GOOGLE_MAPS_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data["status"] != "OK" or not data.get("routes"):
            logger.error(f"Route optimization failed: {data.get('status')}")
            return None
        
        route = data["routes"][0]
        waypoint_order = route.get("waypoint_order", list(range(len(waypoints))))
        legs = route.get("legs", [])
        total_distance = sum(leg["distance"]["value"] for leg in legs if leg.get("distance"))
        total_duration = sum(leg["duration"]["value"] for leg in legs if leg.get("duration"))
        
        return {
            "waypoint_order": waypoint_order,
            "ordered_waypoints": waypoint_order,
            "total_distance_km": round(total_distance / 1000, 2) if total_distance else None,
            "total_duration_minutes": round(total_duration / 60, 2) if total_duration else None,
            "polyline": route.get("overview_polyline", {}).get("points")
        }
    except Exception as e:
        logger.error(f"Error optimizing route: {e}")
        return None