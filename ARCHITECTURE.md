# MedEx Delivery - System Architecture

## System Overview

MedEx Delivery is a full-stack B2B medical delivery platform built on a modern microservices-inspired architecture with real-time capabilities.

## Architecture Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│                 │       │                 │       │                 │
│  React Frontend │◄──────┤  FastAPI        │◄──────┤   MongoDB       │
│  (Web/PWA)      │       │  Backend        │       │   Database      │
│                 │       │                 │       │                 │
└────────┬────────┘       └────────┬────────┘       └─────────────────┘
         │                         │
         │ WebSocket               │ WebSocket
         │                         │
         ▼                         ▼
┌─────────────────────────────────────────┐
│                                         │
│    WebSocket Connection Manager         │
│    (In-Memory / Redis Pub/Sub)          │
│                                         │
└─────────────────────────────────────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐
│  Driver Clients │       │  Vendor Clients │
│  (Mobile Web)   │       │  (Dashboard)    │
└─────────────────┘       └─────────────────┘
```

## Technology Stack

### Backend
- **Framework**: FastAPI 0.110+
- **Language**: Python 3.11+
- **Database**: MongoDB 5.0+ with Motor (async driver)
- **Real-time**: WebSockets (native FastAPI support)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: Bcrypt
- **Validation**: Pydantic v2
- **HTTP Client**: Requests (for Google Maps APIs)

### Frontend
- **Framework**: React 19
- **Routing**: React Router v7
- **UI Library**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **WebSocket Client**: socket.io-client
- **HTTP Client**: Axios
- **Maps**: Google Maps JavaScript API
- **Notifications**: React Toastify

### Infrastructure
- **Database**: MongoDB
- **Cache/Pub-Sub** (Optional): Redis
- **File Storage**: Local (upgradeable to S3)
- **Deployment**: Docker + Docker Compose

## Database Schema

### Collections

#### 1. Users
```javascript
{
  id: "uuid",
  email: "user@example.com",
  full_name: "John Doe",
  phone: "+1234567890",
  role: "user|vendor|driver|admin",
  hashed_password: "bcrypt_hash",
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
}
```
**Indexes**: email (unique), id (unique)

#### 2. Vendors
```javascript
{
  id: "uuid",
  user_id: "uuid",
  business_name: "MedPharm Inc",
  email: "vendor@example.com",
  phone: "+1234567890",
  address: "123 Main St",
  latitude: 40.7128,
  longitude: -74.0060,
  driver_ids: ["driver_uuid_1", "driver_uuid_2"],
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
}
```
**Indexes**: id (unique), user_id

#### 3. Drivers
```javascript
{
  id: "uuid",
  user_id: "uuid",
  vendor_id: "uuid",
  full_name: "Driver Name",
  email: "driver@example.com",
  phone: "+1234567890",
  vehicle_type: "bike|scooter|car|van",
  vehicle_number: "ABC-1234",
  license_number: "DL-123456",
  status: "offline|available|busy|on_break",
  current_latitude: 40.7128,
  current_longitude: -74.0060,
  last_location_update: ISODate(),
  total_deliveries: 0,
  total_earnings: 0.0,
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
}
```
**Indexes**: 
- id (unique)
- vendor_id
- user_id
- status
- (current_latitude, current_longitude) 2dsphere

#### 4. Orders
```javascript
{
  id: "uuid",
  order_number: "ORD-12345678",
  user_id: "uuid",
  vendor_id: "uuid",
  driver_id: "uuid",
  assignment_id: "uuid",
  status: "pending|accepted|driver_assigned|picked_up|out_for_delivery|delivered|cancelled",
  tracking_token: "uuid",
  
  // Pickup
  pickup_address: "123 Vendor St",
  pickup_latitude: 40.7128,
  pickup_longitude: -74.0060,
  
  // Delivery
  delivery_address: "456 Customer Ave",
  delivery_latitude: 40.7580,
  delivery_longitude: -73.9855,
  customer_name: "Jane Smith",
  customer_phone: "+1234567890",
  
  // Items
  items: [{name: "Medicine A", quantity: 2}],
  notes: "Leave at door",
  
  // Tracking
  estimated_distance_km: 5.2,
  actual_distance_km: 5.5,
  delivery_fee: 13.0,
  estimated_delivery_time: ISODate(),
  
  // Proof
  proof_photo_url: "/uploads/proof/abc.jpg",
  signature_url: "/uploads/signatures/xyz.png",
  
  // Timestamps
  created_at: ISODate(),
  accepted_at: ISODate(),
  picked_up_at: ISODate(),
  out_for_delivery_at: ISODate(),
  delivered_at: ISODate(),
  updated_at: ISODate()
}
```
**Indexes**:
- id (unique)
- order_number (unique)
- tracking_token (unique)
- user_id, vendor_id, driver_id
- status, created_at
- (pickup_latitude, pickup_longitude) 2dsphere
- (delivery_latitude, delivery_longitude) 2dsphere

#### 5. Location Events
```javascript
{
  id: "uuid",
  driver_id: "uuid",
  order_id: "uuid",
  latitude: 40.7128,
  longitude: -74.0060,
  speed: 45.5,        // km/h
  heading: 90.0,      // degrees
  accuracy: 10.0,     // meters
  timestamp: ISODate()
}
```
**Indexes**:
- driver_id
- timestamp (TTL: 30 days)
- (latitude, longitude) 2dsphere

#### 6. Assignments
```javascript
{
  id: "uuid",
  order_id: "uuid",
  driver_id: "uuid",
  vendor_id: "uuid",
  status: "pending|accepted|declined|completed",
  assigned_at: ISODate(),
  accepted_at: ISODate(),
  declined_at: ISODate(),
  completed_at: ISODate()
}
```
**Indexes**: id (unique), order_id, driver_id, vendor_id

## WebSocket Architecture

### Connection Manager

#### In-Memory Implementation (Current)
```python
class ConnectionManager:
    active_connections: Dict[user_id, WebSocket]
    rooms: Dict[room_name, Set[user_id]]
```

**Features**:
- User-specific connections
- Room-based broadcasting
- Automatic cleanup on disconnect

**Limitations**:
- Single-server only
- No horizontal scaling
- No persistence across restarts

#### Redis Implementation (Production)
```python
class RedisConnectionManager:
    redis: RedisClient
    pubsub: RedisPubSub
    local_connections: Dict[user_id, WebSocket]
```

**Features**:
- Multi-server support
- Horizontal scaling
- Message persistence
- Cross-server broadcasting

**Migration Steps**:
1. Install Redis: `pip install redis aioredis`
2. Replace ConnectionManager in `websockets/manager.py`
3. Set `REDIS_URL` in environment
4. Implement pub/sub listeners

### WebSocket Rooms

#### 1. Vendor Room: `vendor_{vendor_id}`
- **Subscribers**: Vendor dashboard users
- **Publishers**: Drivers (location updates)
- **Messages**: Driver location, status changes

#### 2. Order Room: `order_{order_id}`
- **Subscribers**: Tracking page users (public)
- **Publishers**: Assigned driver
- **Messages**: Driver location, ETA updates, status changes

#### 3. Driver Room: `driver_{driver_id}`
- **Subscribers**: Driver (single connection)
- **Publishers**: Vendor (assignment notifications)
- **Messages**: New assignments, order updates

### Message Formats

#### Driver Location Update
```json
{
  "type": "driver_location",
  "driver_id": "uuid",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "speed": 45.5,
  "heading": 90.0,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Order Status Update
```json
{
  "type": "order_status",
  "order_id": "uuid",
  "status": "picked_up",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### Assignment Notification
```json
{
  "type": "new_assignment",
  "order_id": "uuid",
  "pickup_address": "123 Main St",
  "delivery_address": "456 Oak Ave",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## API Architecture

### Request Flow

```
Client → API Endpoint → Middleware (Auth) → Route Handler → Business Logic → Database → Response
```

### Authentication Flow

1. **Login**: 
   - Client sends credentials
   - Server validates and returns access + refresh tokens
   - Client stores tokens in localStorage

2. **Protected Request**:
   - Client sends request with `Authorization: Bearer {access_token}`
   - Middleware validates JWT
   - If valid, request proceeds
   - If expired, client uses refresh token

3. **Token Refresh**:
   - Client sends refresh token
   - Server validates and issues new access token
   - Client updates stored access token

### Role-Based Access Control

```python
@router.get("/admin-only")
async def admin_endpoint(
    current_user: dict = Depends(require_role(["admin"]))
):
    # Only admin can access
    pass
```

**Roles**:
- `user`: Create orders, track deliveries
- `vendor`: Manage orders, assign drivers, view reports
- `driver`: Accept orders, update status, share location
- `admin`: Full system access

## Google Maps Integration

### API Usage

#### 1. Geocoding
```python
get_coordinates("123 Main St, NYC")
# Returns: (40.7128, -74.0060)
```

#### 2. Distance Calculation
```python
calculate_distance(
    origin=(40.7128, -74.0060),
    destination=(40.7580, -73.9855)
)
# Returns: 5.2 (km)
```

#### 3. ETA Calculation
```python
calculate_eta(
    driver_location=(40.7128, -74.0060),
    destination=(40.7580, -73.9855)
)
# Returns: 15 (minutes)
```

#### 4. Route Polyline
```python
get_route_polyline(
    origin=(40.7128, -74.0060),
    destination=(40.7580, -73.9855)
)
# Returns: encoded polyline string
```

### Rate Limiting

Google Maps APIs have usage limits:
- Geocoding: 50 requests/sec
- Directions: 50 requests/sec
- Distance Matrix: 100 elements/sec

**Strategy**:
- Cache geocoded addresses
- Batch distance calculations
- Use client-side Maps JS API when possible

## File Storage Architecture

### Current: Local Storage
```
/app/backend/uploads/
├── proof/
│   └── {uuid}.jpg
└── signatures/
    └── {uuid}.png
```

### Future: Cloud Storage (S3)

```python
async def save_upload_file(file, subfolder):
    # Current: Save to local filesystem
    # Future: Upload to S3
    s3_client.upload_fileobj(
        file,
        bucket_name,
        f"{subfolder}/{uuid}.{ext}"
    )
    return f"https://cdn.example.com/{subfolder}/{uuid}.{ext}"
```

## Scaling Considerations

### Horizontal Scaling

1. **Backend Scaling**
   - Run multiple FastAPI instances behind load balancer
   - Use Redis for WebSocket pub/sub
   - Share session state via Redis

2. **Database Scaling**
   - MongoDB replica sets for read scaling
   - Sharding by vendor_id for large deployments
   - Use read preferences for non-critical queries

3. **WebSocket Scaling**
   - Redis pub/sub for cross-server messaging
   - Sticky sessions at load balancer
   - Connection limits per server

### Performance Optimization

1. **Database**
   - Proper indexes on frequently queried fields
   - TTL indexes for automatic data cleanup
   - Geospatial indexes for location queries

2. **Caching**
   - Cache geocoded addresses (Redis)
   - Cache driver locations (1-minute TTL)
   - Cache vendor/driver lists

3. **API**
   - Pagination for list endpoints
   - Field projection to reduce payload size
   - Background tasks for non-critical operations

## Security Best Practices

1. **Authentication**
   - JWT tokens with short expiration
   - Refresh token rotation
   - Secure password hashing (bcrypt)

2. **Authorization**
   - Role-based access control
   - Resource ownership validation
   - API rate limiting

3. **Data Protection**
   - HTTPS only in production
   - CORS configuration
   - Input validation
   - SQL injection prevention (MongoDB parameterization)

4. **File Uploads**
   - File type validation
   - Size limits
   - Virus scanning (production)

## Monitoring & Logging

### Recommended Tools

1. **Application Monitoring**
   - Sentry (error tracking)
   - DataDog (APM)
   - New Relic

2. **Logging**
   - ELK Stack (Elasticsearch, Logstash, Kibana)
   - CloudWatch Logs (AWS)
   - Google Cloud Logging

3. **Metrics**
   - Prometheus + Grafana
   - CloudWatch Metrics
   - Custom dashboards

### Key Metrics to Track

- Request latency (p50, p95, p99)
- Error rates by endpoint
- WebSocket connection count
- Active orders count
- Driver utilization rate
- Average delivery time
- Database query performance

## Deployment Architecture

### Production Setup

```
Load Balancer (NGINX/ALB)
    |
    ├─ FastAPI Instance 1
    ├─ FastAPI Instance 2
    └─ FastAPI Instance 3
         |
         ├─ MongoDB Replica Set
         ├─ Redis Cluster
         └─ S3 (File Storage)
```

### Environment Configuration

**Development**:
- Single FastAPI instance
- MongoDB standalone
- Local file storage
- Mock Google Maps

**Staging**:
- 2 FastAPI instances
- MongoDB replica set (3 nodes)
- Redis single instance
- S3 storage
- Real Google Maps

**Production**:
- 3+ FastAPI instances
- MongoDB replica set (5+ nodes)
- Redis cluster (3+ nodes)
- S3 storage + CloudFront CDN
- Real Google Maps with billing

---

**For more information, see README.md and MOBILE_UPGRADE.md**