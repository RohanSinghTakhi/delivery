from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

# Load environment variables FIRST, before any imports that need them
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import routes (after .env is loaded)
from routes import (
    auth_router,
    orders_router,
    drivers_router,
    vendors_router,
    tracking_router,
    reports_router,
    webhooks_router,
    uploads_router,
    optimization_router,
    woocommerce_router
)

# Import WebSocket handlers
from socket_handlers.handlers import (
    handle_driver_location,
    handle_vendor_tracking,
    handle_order_tracking
)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(
    title="MedEx Delivery API",
    description="B2B Medical Delivery System API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers with /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(drivers_router, prefix="/api")
app.include_router(vendors_router, prefix="/api")
app.include_router(tracking_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(optimization_router, prefix="/api")
app.include_router(woocommerce_router, prefix="/api")

# WebSocket routes
@app.websocket("/ws/driver")
async def websocket_driver_endpoint(websocket, token: str):
    """WebSocket endpoint for driver location streaming"""
    await handle_driver_location(websocket, token)

@app.websocket("/ws/vendor/{vendor_id}")
async def websocket_vendor_endpoint(websocket, vendor_id: str, token: str):
    """WebSocket endpoint for vendor fleet tracking"""
    await handle_vendor_tracking(websocket, vendor_id, token)

@app.websocket("/ws/tracking/{tracking_token}")
async def websocket_tracking_endpoint(websocket, tracking_token: str):
    """WebSocket endpoint for public order tracking"""
    await handle_order_tracking(websocket, tracking_token)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MedEx Delivery API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check
@app.get("/api/health")
async def health_check():
    try:
        # Test MongoDB connection
        await db.command("ping")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# Create database indexes on startup
@app.on_event("startup")
async def create_indexes():
    """Create MongoDB indexes for better performance"""
    try:
        # Users index
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        
        # Drivers indexes
        await db.drivers.create_index("id", unique=True)
        await db.drivers.create_index("vendor_id")
        await db.drivers.create_index("user_id")
        await db.drivers.create_index("status")
        # Geospatial index for driver locations
        await db.drivers.create_index([("current_latitude", "2dsphere"), ("current_longitude", "2dsphere")])
        
        # Orders indexes
        await db.orders.create_index("id", unique=True)
        await db.orders.create_index("order_number", unique=True)
        await db.orders.create_index("tracking_token", unique=True)
        await db.orders.create_index("user_id")
        await db.orders.create_index("vendor_id")
        await db.orders.create_index("driver_id")
        await db.orders.create_index("status")
        await db.orders.create_index("created_at")
        # Geospatial indexes for pickup and delivery locations
        await db.orders.create_index([("pickup_latitude", "2dsphere"), ("pickup_longitude", "2dsphere")])
        await db.orders.create_index([("delivery_latitude", "2dsphere"), ("delivery_longitude", "2dsphere")])
        
        # Location events indexes
        await db.location_events.create_index("driver_id")
        await db.location_events.create_index("timestamp")
        await db.location_events.create_index([("latitude", "2dsphere"), ("longitude", "2dsphere")])
        # TTL index to auto-delete old location events after 30 days
        await db.location_events.create_index("timestamp", expireAfterSeconds=2592000)
        
        # Vendors index
        await db.vendors.create_index("id", unique=True)
        await db.vendors.create_index("user_id")
        
        # Assignments index
        await db.assignments.create_index("id", unique=True)
        await db.assignments.create_index("order_id")
        await db.assignments.create_index("driver_id")
        await db.assignments.create_index("vendor_id")
        
        logging.info("Database indexes created successfully")
    except Exception as e:
        logging.error(f"Error creating indexes: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)