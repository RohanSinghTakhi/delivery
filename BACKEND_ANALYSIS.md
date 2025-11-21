# MedEx Delivery Backend - Complete Analysis

## 📋 Overview

**Project Name**: MedEx Delivery API  
**Type**: B2B Medical Delivery System (Similar to Zomato Logistics)  
**Framework**: FastAPI (Python)  
**Database**: MongoDB  
**Real-time**: WebSockets  
**Authentication**: JWT (JSON Web Tokens)

---

## 🎯 What This Backend Does

This is a **complete delivery management system** that enables:

1. **Medical Products Delivery** - Delivers medicines and medical products from vendors to customers
2. **Multi-user Ecosystem** - Manages Users (customers), Vendors (pharmacies), and Drivers
3. **Real-time Tracking** - WebSocket-based live location tracking for drivers and orders
4. **Order Management** - Complete order lifecycle from creation to delivery
5. **Driver Fleet Management** - Manage drivers, track performance, earnings
6. **Vendor Dashboard** - Analytics, reports, driver assignments

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Web Server (Port 8000)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  REST API Routes:                                   │
│  ├── /api/auth          (User Authentication)       │
│  ├── /api/orders        (Order Management)          │
│  ├── /api/drivers       (Driver Management)         │
│  ├── /api/vendors       (Vendor Management)         │
│  ├── /api/tracking      (Public Tracking)           │
│  ├── /api/reports       (Analytics & Reports)       │
│  ├── /api/uploads       (File Storage)              │
│  └── /api/webhooks      (External Integrations)     │
│                                                     │
│  WebSocket Routes:                                  │
│  ├── /ws/driver/{user_id}        (Driver Tracking) │
│  ├── /ws/vendor/{vendor_id}      (Fleet Tracking)  │
│  └── /ws/tracking/{token}        (Public Tracking) │
│                                                     │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
         ┌──────────────────┐
         │    MongoDB       │
         │    Database      │
         │   (localhost)    │
         └──────────────────┘
```

---

## 📦 Dependencies (requirements.txt)

```
fastapi==0.110.1              # Web framework
uvicorn==0.25.0               # ASGI server
motor==3.3.1                  # Async MongoDB driver
pydantic>=2.6.4               # Data validation
python-dotenv>=1.0.1          # Environment variables
python-jose>=3.3.0            # JWT token generation
passlib>=1.7.4                # Password hashing utilities
bcrypt==4.1.3                 # Password hashing
pyjwt>=2.10.1                 # JWT token handling
email-validator>=2.2.0        # Email validation
python-multipart>=0.0.9       # Form data handling
requests>=2.31.0              # HTTP client (for Google Maps)
aiofiles>=23.2.1              # Async file operations
websockets>=12.0              # WebSocket support
```

---

## 📊 Database Models

### 1. **Users Collection**
```javascript
{
  _id: ObjectId,
  id: "uuid",                    // Unique identifier
  email: "user@example.com",     // Unique email
  full_name: "John Doe",
  phone: "+1234567890",
  role: "user|vendor|driver|admin",
  hashed_password: "bcrypt_hash",
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
}
```

### 2. **Vendors Collection**
```javascript
{
  id: "uuid",
  user_id: "uuid",               // Link to user
  business_name: "MedPharm Inc",
  email: "vendor@example.com",
  phone: "+1234567890",
  address: "123 Main St",
  latitude: 40.7128,
  longitude: -74.0060,
  driver_ids: ["driver1", "driver2"],
  is_active: true,
  created_at: ISODate(),
  updated_at: ISODate()
}
```

### 3. **Drivers Collection**
```javascript
{
  id: "uuid",
  user_id: "uuid",
  vendor_id: "uuid",             // Which vendor employs them
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

### 4. **Orders Collection**
```javascript
{
  id: "uuid",
  order_number: "ORD-12345678",
  user_id: "uuid",               // Customer
  vendor_id: "uuid",             // From which pharmacy
  driver_id: "uuid",             // Assigned driver (optional)
  assignment_id: "uuid",         // Delivery assignment
  tracking_token: "uuid",        // Public tracking token
  status: "pending|accepted|driver_assigned|picked_up|out_for_delivery|delivered|cancelled",
  
  // Pickup Location
  pickup_address: "123 Vendor St",
  pickup_latitude: 40.7128,
  pickup_longitude: -74.0060,
  
  // Delivery Location
  delivery_address: "456 Customer Ave",
  delivery_latitude: 40.7580,
  delivery_longitude: -73.9855,
  
  customer_name: "Jane Smith",
  customer_phone: "+1987654321",
  items: [{name: "Medicine X", quantity: 2}],
  notes: "Handle with care",
  
  // Pricing
  estimated_distance_km: 5.2,
  actual_distance_km: 5.1,
  delivery_fee: 12.50,
  
  // Proof of Delivery
  proof_photo_url: "/uploads/proof/photo.jpg",
  signature_url: "/uploads/signatures/sig.png",
  
  // Status Timestamps
  accepted_at: ISODate(),
  picked_up_at: ISODate(),
  out_for_delivery_at: ISODate(),
  delivered_at: ISODate(),
  
  created_at: ISODate(),
  updated_at: ISODate()
}
```

---

## 🛣️ API Routes

### **Authentication Routes** (`/api/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register new user (user, vendor, driver) |
| POST | `/login` | No | Login and get JWT tokens |
| POST | `/refresh` | Yes | Refresh access token |
| GET | `/me` | Yes | Get current user profile |

**Register Request:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "user",
  "password": "securepassword"
}
```

**Login Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Login Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### **Orders Routes** (`/api/orders`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/` | Yes | Create new order (user) |
| GET | `/` | Yes | Get orders (filtered by role) |
| GET | `/{order_id}` | Yes | Get order details |
| PATCH | `/{order_id}` | Yes | Update order status |
| POST | `/{order_id}/accept` | Yes | Accept order (vendor) |
| POST | `/{order_id}/assign-driver` | Yes | Assign driver (vendor) |
| DELETE | `/{order_id}` | Yes | Cancel order |

**Create Order Request (User):**
```json
{
  "user_id": "uuid",
  "vendor_id": "uuid",
  "pickup_address": "123 Pharmacy St",
  "pickup_latitude": 40.7128,
  "pickup_longitude": -74.0060,
  "delivery_address": "456 Home Ave",
  "delivery_latitude": 40.7580,
  "delivery_longitude": -73.9855,
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "items": [{"name": "Aspirin", "quantity": 2}],
  "notes": "Call before delivery"
}
```

---

### **Drivers Routes** (`/api/drivers`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register new driver |
| GET | `/` | Yes | Get drivers (vendor/admin) |
| GET | `/{driver_id}` | Yes | Get driver details |
| PATCH | `/{driver_id}` | Yes | Update driver info |
| PATCH | `/{driver_id}/status` | Yes | Update availability status |
| GET | `/{driver_id}/earnings` | Yes | Get driver earnings |
| GET | `/{driver_id}/deliveries` | Yes | Get delivery history |

**Register Driver Request:**
```json
{
  "email": "driver@example.com",
  "full_name": "Driver Name",
  "phone": "+1234567890",
  "password": "securepassword",
  "vendor_id": "vendor_uuid",
  "vehicle_type": "bike",
  "vehicle_number": "ABC-1234",
  "license_number": "DL-123456"
}
```

---

### **Vendors Routes** (`/api/vendors`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | No | Register new vendor |
| GET | `/` | Yes | Get all vendors |
| GET | `/{vendor_id}` | Yes | Get vendor details |
| GET | `/{vendor_id}/orders` | Yes | Get vendor's orders |
| PATCH | `/{vendor_id}` | Yes | Update vendor profile |
| POST | `/{vendor_id}/export-csv` | Yes | Export orders as CSV |

**Register Vendor Request:**
```json
{
  "email": "vendor@example.com",
  "business_name": "MedPharm Inc",
  "phone": "+1234567890",
  "password": "securepassword",
  "address": "123 Main St",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

---

### **Tracking Routes** (`/api/tracking`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/{tracking_token}` | No | Track order by public token |

**Tracking Response:**
```json
{
  "order": {
    "order_number": "ORD-12345678",
    "status": "out_for_delivery",
    "customer_name": "John Doe",
    "delivery_address": "456 Home Ave",
    "delivery_latitude": 40.7580,
    "delivery_longitude": -73.9855,
    "estimated_delivery_time": "2024-01-15T14:30:00Z",
    "created_at": "2024-01-15T13:00:00Z"
  },
  "driver_location": {
    "latitude": 40.7200,
    "longitude": -73.9900,
    "last_update": "2024-01-15T13:45:30Z"
  },
  "eta_minutes": 12
}
```

---

### **Reports Routes** (`/api/reports`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/vendors/{vendor_id}` | Yes | Get vendor daily report |
| GET | `/vendors/{vendor_id}/drivers` | Yes | Get driver performance stats |
| GET | `/vendors/{vendor_id}/export-csv` | Yes | Export report as CSV |

---

### **Uploads Routes** (`/api/uploads`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/proof` | Yes | Upload proof of delivery photo |
| POST | `/signature` | Yes | Upload delivery signature |
| GET | `/file/{file_id}` | No | Download file |

---

### **Webhooks Routes** (`/api/webhooks`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/wc/order-created` | No | WooCommerce order webhook |

---

### **WebSocket Routes**

| Endpoint | Purpose | Query Params |
|----------|---------|--------------|
| `/ws/driver` | Driver location streaming | `token` |
| `/ws/vendor/{vendor_id}` | Vendor fleet tracking | `token` |
| `/ws/tracking/{tracking_token}` | Public order tracking | - |

---

## 🔑 External API Requirements

### **Google Maps API** (Optional but Recommended)

Google Maps is used for:
- **Geocoding** - Converting addresses to coordinates
- **Distance Matrix** - Calculating distances between locations
- **Routes** - Getting directions for delivery

**Required APIs:**
1. **Geocoding API** - Convert address to lat/lng
2. **Distance Matrix API** - Calculate delivery distances
3. **Routes API** (Optional) - Get turn-by-turn directions

**Cost:** ~$5-10/month for typical usage (includes free tier)

**How to get API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable these APIs:
   - Maps JavaScript API
   - Geocoding API
   - Distance Matrix API
4. Create an API key (restricted to HTTP)
5. Add to `.env`: `GOOGLE_MAPS_API_KEY="your_key_here"`

**Without Google Maps API:**
- System uses mock coordinates (default: NYC 40.7128, -74.0060)
- Distances calculated using Haversine formula (estimation)
- **Works fine for local development!**

---

## 🗄️ Environment Variables

Create `.env` file in `backend/` directory:

```properties
# MongoDB Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medex_delivery"

# CORS Configuration
CORS_ORIGINS="*"

# JWT Configuration
JWT_SECRET_KEY="your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Maps API (OPTIONAL)
GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY_HERE"

# Redis (OPTIONAL - for WebSocket scaling)
# REDIS_URL="redis://localhost:6379/0"

# File Upload
UPLOAD_DIR="/app/backend/uploads"
MAX_UPLOAD_SIZE_MB=10
```

---

## 🚀 Installation & Running

### **Prerequisites**
- Python 3.11+
- MongoDB running locally (or Docker)
- pip (Python package manager)

### **Step 1: Install MongoDB (if not installed)**

**Using Docker (Easiest):**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Or install locally:** Download from [mongodb.com](https://www.mongodb.com/try/download/community)

### **Step 2: Setup Backend**

```bash
cd /home/rohan/embolo/delivery/delivery/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env  # Or create .env manually with values above
```

### **Step 3: Run Backend**

```bash
cd /home/rohan/embolo/delivery/delivery/backend
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Server will start at:** `http://localhost:8000`

**API Documentation (Swagger):** `http://localhost:8000/docs`

---

## 📱 Testing Workflows

### **1. User Registration & Login**

```bash
# Register User
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "role": "user",
    "password": "password123"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### **2. Vendor Registration**

```bash
curl -X POST "http://localhost:8000/api/vendors/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "vendor@example.com",
    "business_name": "MedPharm Inc",
    "phone": "+1234567890",
    "password": "password123",
    "address": "123 Main St",
    "latitude": 40.7128,
    "longitude": -74.0060
  }'
```

### **3. Driver Registration**

```bash
curl -X POST "http://localhost:8000/api/drivers/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "driver@example.com",
    "full_name": "Driver John",
    "phone": "+1234567890",
    "password": "password123",
    "vendor_id": "vendor_uuid_here",
    "vehicle_type": "bike",
    "vehicle_number": "ABC-1234",
    "license_number": "DL-123456"
  }'
```

### **4. Create Order**

```bash
curl -X POST "http://localhost:8000/api/orders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "user_id": "user_uuid",
    "vendor_id": "vendor_uuid",
    "pickup_address": "123 Pharmacy St",
    "pickup_latitude": 40.7128,
    "pickup_longitude": -74.0060,
    "delivery_address": "456 Home Ave",
    "delivery_latitude": 40.7580,
    "delivery_longitude": -73.9855,
    "customer_name": "John Doe",
    "customer_phone": "+1234567890",
    "items": [{"name": "Aspirin", "quantity": 2}],
    "notes": "Call before delivery"
  }'
```

### **5. Track Order (No Auth Needed)**

```bash
curl "http://localhost:8000/api/tracking/tracking_token_here"
```

---

## 📊 Key Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| User Registration | ✅ Complete | Email + Password auth |
| JWT Authentication | ✅ Complete | Access + Refresh tokens |
| Order Management | ✅ Complete | Full CRUD + status tracking |
| Driver Management | ✅ Complete | Assignment + Performance |
| Real-time Tracking | ✅ WebSocket | Location streaming |
| File Uploads | ✅ Complete | Photos + Signatures |
| Distance Calculation | ✅ Complete | Mock or Google Maps |
| Reporting | ✅ Complete | Driver + Vendor reports |
| Public Tracking | ✅ Complete | No auth required |
| CSV Export | ✅ Complete | Orders + Reports |

---

## 🔒 Security Features

- ✅ **Bcrypt Password Hashing** - Secure password storage
- ✅ **JWT Tokens** - Secure API authentication
- ✅ **Token Expiry** - Access tokens expire in 15 minutes
- ✅ **Role-based Access Control** - User/Vendor/Driver/Admin roles
- ✅ **CORS Enabled** - Cross-origin requests configured
- ✅ **HTTPS Ready** - Can be deployed with HTTPS

---

## 📈 Scalability

Currently designed for:
- ✅ Single MongoDB instance (scales to millions of records)
- ✅ In-memory WebSocket management (can upgrade to Redis)
- ✅ Async/await for high concurrency
- ✅ Horizontal scaling ready (Docker-ready)

---

## 🐛 Common Issues & Solutions

### **Issue: MongoDB Connection Failed**
```
SOLUTION: Ensure MongoDB is running
- Docker: docker run -d -p 27017:27017 mongo
- Or check if service is running: sudo systemctl status mongod
```

### **Issue: Google Maps API Not Working**
```
SOLUTION: System uses mock coordinates by default
- Add real Google Maps API key to .env if needed
- Or leave as is for local testing
```

### **Issue: Port 8000 Already in Use**
```
SOLUTION: Run on different port
uvicorn server:app --port 8001 --reload
```

### **Issue: Import Errors**
```
SOLUTION: Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 File Structure

```
backend/
├── server.py                 # Main FastAPI app
├── requirements.txt          # Dependencies
├── .env                      # Configuration (create this)
│
├── models/                   # Pydantic data models
│   ├── user.py
│   ├── order.py
│   ├── driver.py
│   ├── vendor.py
│   ├── assignment.py
│   └── location_event.py
│
├── routes/                   # API endpoints
│   ├── auth.py              # Authentication
│   ├── orders.py            # Order management
│   ├── drivers.py           # Driver management
│   ├── vendors.py           # Vendor management
│   ├── tracking.py          # Public tracking
│   ├── reports.py           # Analytics
│   ├── uploads.py           # File uploads
│   └── webhooks.py          # External integrations
│
├── middleware/               # Authentication & middleware
│   ├── auth.py
│   └── jwt_handler.py
│
├── utils/                    # Helper functions
│   ├── jwt_handler.py       # JWT token creation
│   ├── google_maps.py       # Maps API integration
│   ├── file_handler.py      # File operations
│   └── password_utils.py    # Password hashing
│
├── websockets/               # Real-time communication
│   ├── manager.py           # WebSocket connection manager
│   └── handlers.py          # WebSocket message handlers
│
└── uploads/                  # File storage directory
```

---

## ✅ Ready to Run Locally!

This backend is **fully functional** and can run on localhost **without any external APIs** required. Google Maps is optional - the system works with mock data for local testing.

**Start here:**
```bash
# Terminal 1: Start MongoDB
docker run -d -p 27017:27017 mongo

# Terminal 2: Start Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload

# Then access: http://localhost:8000/docs
```

---

**Generated:** November 18, 2025  
**Version:** 1.0.0
