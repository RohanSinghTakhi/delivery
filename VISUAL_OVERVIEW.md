# 🎯 MedEx Backend - Visual Overview & Summary

## 📊 System At A Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                    MedEx Delivery System                         │
│                   B2B Medical Delivery                           │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                      Who Uses What?                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  👤 USER (Customer)                                             │
│  ├── Register & Login                                           │
│  ├── Create delivery orders                                     │
│  ├── Track orders in real-time                                  │
│  ├── Share public tracking link                                 │
│  └── View order history                                         │
│                                                                  │
│  🏪 VENDOR (Pharmacy)                                           │
│  ├── Register business                                          │
│  ├── View incoming orders                                       │
│  ├── Accept/reject orders                                       │
│  ├── Manage drivers                                             │
│  ├── Assign drivers to orders                                   │
│  ├── View fleet on map (real-time)                              │
│  └── Generate daily reports                                     │
│                                                                  │
│  🚗 DRIVER (Delivery Partner)                                   │
│  ├── Register with vendor                                       │
│  ├── Accept/decline orders                                      │
│  ├── Broadcast location (every 3-5 seconds)                     │
│  ├── Update delivery status                                     │
│  ├── Upload proof of delivery                                   │
│  ├── View earnings                                              │
│  └── Track performance                                          │
│                                                                  │
│  👨‍💼 ADMIN (System)                                             │
│  ├── Do everything                                              │
│  └── Manage system configuration                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Order Lifecycle

```
┌────────────────────────────────────────────────────────────────────┐
│                    ORDER FLOW IN THE SYSTEM                         │
└────────────────────────────────────────────────────────────────────┘

STEP 1: USER CREATES ORDER
  ├─ User logs in
  ├─ Selects pharmacy (vendor)
  ├─ Enters delivery address
  ├─ Lists medicines to order
  ├─ Gets unique tracking token
  └─ Order Status: PENDING ✓

         ⬇️ (Notification sent to vendor)

STEP 2: VENDOR ACCEPTS ORDER
  ├─ Vendor sees order notification
  ├─ Reviews order details
  ├─ Clicks "Accept"
  └─ Order Status: ACCEPTED ✓

         ⬇️ (Vendor now needs to assign driver)

STEP 3: VENDOR ASSIGNS DRIVER
  ├─ Vendor selects driver from available list
  ├─ Driver notified of assignment
  ├─ Driver location tracking starts
  └─ Order Status: DRIVER_ASSIGNED ✓

         ⬇️ (Real-time tracking begins)

STEP 4: DRIVER PICKS UP ORDER
  ├─ Driver arrives at vendor location
  ├─ Collects order items
  ├─ Takes photo/signature
  ├─ Starts delivery
  └─ Order Status: PICKED_UP ✓

         ⬇️ (Location updates in real-time)

STEP 5: DRIVER OUT FOR DELIVERY
  ├─ Driver heading to customer location
  ├─ User & Vendor see live location
  ├─ ETA calculated & displayed
  └─ Order Status: OUT_FOR_DELIVERY ✓

         ⬇️ (Nearly at destination)

STEP 6: DRIVER DELIVERS ORDER
  ├─ Driver arrives at customer location
  ├─ Customer receives items
  ├─ Takes photo proof
  ├─ Gets signature
  ├─ Driver marks as delivered
  ├─ Order automatically closed
  └─ Order Status: DELIVERED ✓

         ⬇️ (Delivery complete)

STEP 7: REPORTING
  ├─ Order appears in vendor reports
  ├─ Driver gets earnings credit
  ├─ Data saved for analytics
  └─ Report can be exported as CSV

```

---

## 🌐 API Endpoints Map

```
┌─────────────────────────────────────────────────────────────────┐
│                  API ENDPOINT CATEGORIES                         │
└─────────────────────────────────────────────────────────────────┘

/api/auth ─────────────────── AUTHENTICATION
  ├─ POST   /register         Create new account
  ├─ POST   /login            Login with email/password
  ├─ POST   /refresh          Get new access token
  └─ GET    /me               Get current user profile

/api/orders ──────────────── ORDER MANAGEMENT
  ├─ POST   /                 Create new order
  ├─ GET    /                 List orders (filtered by role)
  ├─ GET    /{id}             Get order details
  ├─ PATCH  /{id}             Update status
  ├─ POST   /{id}/assign-driver  Assign driver
  └─ DELETE /{id}             Cancel order

/api/drivers ─────────────── DRIVER MANAGEMENT
  ├─ POST   /register         Register driver
  ├─ GET    /                 List drivers
  ├─ GET    /{id}             Get driver details
  ├─ PATCH  /{id}             Update driver info
  ├─ PATCH  /{id}/status      Change availability
  ├─ GET    /{id}/earnings    View earnings
  └─ GET    /{id}/deliveries  Delivery history

/api/vendors ─────────────── VENDOR MANAGEMENT
  ├─ POST   /register         Register pharmacy
  ├─ GET    /                 List all vendors
  ├─ GET    /{id}             Get vendor details
  ├─ GET    /{id}/orders      Get vendor orders
  ├─ PATCH  /{id}             Update profile
  └─ POST   /{id}/export-csv  Export reports

/api/tracking ────────────── PUBLIC TRACKING (No auth)
  └─ GET    /{token}          Track order by token

/api/reports ─────────────── ANALYTICS
  ├─ GET    /vendors/{id}     Daily vendor report
  └─ GET    /vendors/{id}/drivers  Driver statistics

/api/uploads ─────────────── FILE STORAGE
  ├─ POST   /proof            Upload delivery photo
  └─ POST   /signature        Upload signature

/api/webhooks ────────────── INTEGRATIONS
  └─ POST   /wc/order-created  WooCommerce webhook

/api/health ──────────────── MONITORING
  └─ GET                      System health status

/ws/driver ───────────────── WEBSOCKET: Driver location
/ws/vendor/{id} ──────────── WEBSOCKET: Vendor fleet tracking
/ws/tracking/{token} ──────── WEBSOCKET: Public tracking
```

---

## 💾 Database Schema Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE COLLECTIONS                         │
└─────────────────────────────────────────────────────────────────┘

📝 USERS Collection
├─ id               UUID (primary key)
├─ email            Email address (unique)
├─ full_name        User's full name
├─ phone            Phone number
├─ role             "user", "vendor", "driver", "admin"
├─ hashed_password  Bcrypt hash
├─ is_active        Boolean
├─ created_at       Timestamp
└─ updated_at       Timestamp

🏪 VENDORS Collection
├─ id               UUID
├─ user_id         Foreign key → users.id
├─ business_name    Pharmacy name
├─ email            Contact email
├─ phone            Contact phone
├─ address          Physical address
├─ latitude         Location coordinates
├─ longitude        Location coordinates
├─ driver_ids       Array of driver UUIDs
├─ is_active        Boolean
├─ created_at       Timestamp
└─ updated_at       Timestamp

🚗 DRIVERS Collection
├─ id               UUID
├─ user_id         Foreign key → users.id
├─ vendor_id       Foreign key → vendors.id
├─ full_name        Driver's name
├─ email            Email address
├─ phone            Phone number
├─ vehicle_type    "bike", "scooter", "car", "van"
├─ vehicle_number   License plate
├─ license_number   Driver license
├─ status           "offline", "available", "busy", "on_break"
├─ current_latitude   Current location
├─ current_longitude  Current location
├─ last_location_update  Last update timestamp
├─ total_deliveries Number of deliveries
├─ total_earnings   Total money earned
├─ is_active        Boolean
├─ created_at       Timestamp
└─ updated_at       Timestamp

📦 ORDERS Collection
├─ id               UUID
├─ order_number     "ORD-XXXXXXXX" (unique reference)
├─ user_id         Foreign key → users.id
├─ vendor_id       Foreign key → vendors.id
├─ driver_id       Foreign key → drivers.id
├─ tracking_token   Public token for tracking
├─ status           Lifecycle status (pending → delivered)
│
├─ PICKUP LOCATION
├─ pickup_address    Vendor address
├─ pickup_latitude   Coordinates
├─ pickup_longitude  Coordinates
│
├─ DELIVERY LOCATION
├─ delivery_address    Customer address
├─ delivery_latitude   Coordinates
├─ delivery_longitude  Coordinates
│
├─ CUSTOMER INFO
├─ customer_name      Name
├─ customer_phone     Phone
├─ items              Array of medicines
├─ notes              Special instructions
│
├─ PRICING
├─ estimated_distance_km   Calculated distance
├─ actual_distance_km      Recorded distance
├─ delivery_fee           Price
│
├─ PROOF
├─ proof_photo_url     Photo file URL
├─ signature_url       Signature file URL
│
├─ STATUS TIMESTAMPS
├─ accepted_at         When vendor accepted
├─ picked_up_at        When driver picked up
├─ out_for_delivery_at When driver left vendor
├─ delivered_at        When delivery completed
│
├─ created_at          Order creation time
└─ updated_at          Last modified time
```

---

## 🔐 Authentication Flow

```
┌────────────────────────────────────────────────────────────────┐
│                  JWT AUTHENTICATION FLOW                        │
└────────────────────────────────────────────────────────────────┘

CLIENT (Browser/App)                SERVER
       │                               │
       │────── POST /register ──────→  │
       │      Email + Password         │
       │                               │
       │←── User ID + Tokens ──────────│
       │  (Access + Refresh)           │
       │                               │
       │────── GET /api/orders ────→   │
       │   + Authorization: Bearer     │
       │     {access_token}            │
       │                               │
       │←──── Orders List ─────────────│
       │                               │
  [15 min expires]                    │
       │                               │
       │────── POST /refresh ─────────→│
       │   + Refresh Token             │
       │                               │
       │←── New Access Token ──────────│
       │   (7 days valid)              │
       │                               │
       │────── Continue Using ────────→│
       │    New Access Token           │
       │                               │

TOKENS CONTAIN:
├─ Access Token (15 min expiry)
│  ├─ User ID
│  ├─ User Role
│  └─ Encrypted with JWT_SECRET_KEY
│
└─ Refresh Token (7 day expiry)
   └─ Can request new access token
```

---

## 📊 Real-time Communication (WebSockets)

```
┌────────────────────────────────────────────────────────────────┐
│                   WEBSOCKET CONNECTIONS                         │
└────────────────────────────────────────────────────────────────┘

DRIVER LOCATION TRACKING
  Driver App                          Backend                    Vendor/User
      │                                 │                           │
      ├── Connect /ws/driver ────────→ │                           │
      │   (sends auth token)            │                           │
      │                                 │                           │
      ├── Update location ────────────→ │                           │
      │   (every 3-5 seconds)           │───→ Broadcast to ALL ──→ │
      │                                 │     connected clients    │
      ├── Update location ────────────→ │                           │
      │   (another 3-5 seconds)         │───→ Real-time updates ─→ │
      │                                 │                           │
      └── Disconnect ─────────────────→ │                           │

VENDOR FLEET TRACKING
  Vendor Dashboard                    Backend               Multiple Drivers
      │                                 │                      │
      ├── Connect /ws/vendor/{id} ────→ │                      │
      │   (watch all my drivers)        │                      │
      │                                 │←─ Driver A location ─┤
      │←── Fleet map updates ──────────│←─ Driver B location ─┤
      │   (all drivers shown)           │←─ Driver C location ─┤
      │                                 │
      └── Disconnect ─────────────────→ │

PUBLIC TRACKING
  Customer (Any Browser)              Backend                    Driver
      │                                 │                        │
      ├── Open tracking link ─────────→ │                        │
      │   /api/tracking/{token}         │                        │
      │                                 │                        │
      │←── Order status + location ────│←─ Get driver location ─┤
      │   (updates as driver moves)     │                        │
      │                                 │                        │
      └── Page refresh for updates ───→ │

BENEFITS:
✓ Real-time updates (no page refresh needed)
✓ Driver location streamed live
✓ ETA calculated automatically
✓ Efficient (only changed data sent)
```

---

## 🚀 Deployment Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                PRODUCTION DEPLOYMENT SETUP                        │
└──────────────────────────────────────────────────────────────────┘

LOCAL DEVELOPMENT (Current)
  Client (localhost:3000)
         ↓
    FastAPI (localhost:8000)
         ↓
    MongoDB (localhost:27017)


PRODUCTION (Scalable)
  ┌─────────────────────────────────────────────┐
  │        LOAD BALANCER (nginx)                │
  │   (Distributes traffic)                     │
  └──────────────┬──────────────────────────────┘
                 │
         ┌───────┼───────┐
         │       │       │
         ▼       ▼       ▼
     ┌────┐ ┌────┐ ┌────┐
     │API │ │API │ │API │  (Multiple instances)
     │Pod │ │Pod │ │Pod │
     └─┬──┘ └─┬──┘ └─┬──┘
       │      │      │
       └──────┼──────┘
              │
         ┌────▼──────────┐
         │  MongoDB      │  (Replicated)
         │  Cluster      │
         └───────────────┘
              │
         ┌────▼──────────┐
         │  Redis        │  (Optional)
         │  Cache/Pub-Sub│
         └───────────────┘

KUBERNETES POD EXAMPLE:
┌─────────────────────────────────┐
│    FastAPI Backend Container    │
├─────────────────────────────────┤
│  ├─ App runs on port 8000      │
│  ├─ Auto-restarts on crash     │
│  ├─ Health checks enabled      │
│  ├─ Requests load balanced     │
│  └─ Logs centralized           │
└─────────────────────────────────┘
```

---

## 📈 Features & Status

```
┌──────────────────────────────────────────────────────────────────┐
│                   FEATURE CHECKLIST                              │
└──────────────────────────────────────────────────────────────────┘

AUTHENTICATION & SECURITY
  ✅ User Registration
  ✅ Email & Password Login
  ✅ JWT Tokens (Access + Refresh)
  ✅ Bcrypt Password Hashing
  ✅ Role-Based Access Control
  ✅ Token Expiry (15 min access, 7 day refresh)
  ✅ CORS Configuration

USER FEATURES
  ✅ User Registration
  ✅ User Dashboard
  ✅ Create Orders
  ✅ Track Orders in Real-time
  ✅ Public Tracking (No auth required)
  ✅ Order History
  ✅ Share Tracking Link

VENDOR FEATURES
  ✅ Vendor Registration
  ✅ Vendor Dashboard
  ✅ Accept/Reject Orders
  ✅ View Incoming Orders
  ✅ Assign Drivers
  ✅ Live Fleet Tracking (WebSocket)
  ✅ Driver Performance Reports
  ✅ Daily Analytics
  ✅ CSV Export

DRIVER FEATURES
  ✅ Driver Registration
  ✅ Accept/Decline Orders
  ✅ Real-time Location Streaming
  ✅ Update Delivery Status
  ✅ Proof of Delivery (Photo + Signature)
  ✅ Earnings Dashboard
  ✅ Delivery History
  ✅ Performance Stats

SYSTEM FEATURES
  ✅ Distance Calculation
  ✅ ETA Calculation
  ✅ File Uploads (Local)
  ✅ Order Status Tracking
  ✅ WebSocket Support
  ✅ Health Checks
  ✅ Error Handling
  ✅ Logging

OPTIONAL (Not Implemented Yet)
  ⭕ Email Notifications
  ⭕ SMS Notifications
  ⭕ Push Notifications
  ⭕ Payment Integration
  ⭕ Insurance
  ⭕ Rating & Reviews
```

---

## 📚 Documentation Overview

```
QUICK START
    │
    └─→ QUICK_START.md (5-minute setup)
            │
            ├─→ Installation steps
            ├─→ Configuration
            ├─→ Running locally
            └─→ First API calls

DETAILED ANALYSIS
    │
    ├─→ BACKEND_ANALYSIS.md (Complete system)
    │   ├─→ Overview
    │   ├─→ Architecture
    │   ├─→ Database schema
    │   ├─→ All API endpoints
    │   ├─→ Authentication
    │   └─→ Common issues
    │
    ├─→ ARCHITECTURE.md (Technical deep dive)
    │   ├─→ System design
    │   ├─→ Technology stack
    │   ├─→ Database collections
    │   └─→ Deployment
    │
    └─→ API_TESTING.md (Testing workflows)
        ├─→ Postman collection
        ├─→ Testing scenarios
        ├─→ cURL examples
        └─→ Status codes

SETUP & DEPLOYMENT
    │
    ├─→ REQUIREMENTS_AND_APIS.md
    │   ├─→ What you need
    │   ├─→ Dependencies
    │   ├─→ External APIs
    │   └─→ MongoDB setup
    │
    └─→ setup-and-run.sh / setup-and-run.bat
        └─→ Automated installation script

THIS FILE
    │
    └─→ VISUAL_OVERVIEW.md (What you're reading)
        ├─→ System at a glance
        ├─→ All workflows visualized
        ├─→ Architecture diagrams
        └─→ Feature checklist
```

---

## 🎯 Getting Started Path

```
START HERE: QUICK_START.md

    ↓

INSTALLATION COMPLETE?

    ↓ YES

Check: http://localhost:8000/docs

    ↓

API DOCUMENTATION LOADED?

    ↓ YES

READY TO TEST? → Follow API_TESTING.md

    ↓

WANT TO UNDERSTAND SYSTEM? → Read BACKEND_ANALYSIS.md

    ↓

NEED TECHNICAL DETAILS? → Study ARCHITECTURE.md

    ↓

READY TO DEPLOY? → Check REQUIREMENTS_AND_APIS.md

    ↓

SUCCESS! 🎉
```

---

## ✅ Verification Checklist

```
SETUP COMPLETE WHEN:

✅ Python 3.11+ installed
✅ MongoDB running on localhost:27017
✅ Virtual environment created
✅ Dependencies installed (pip install -r requirements.txt)
✅ .env file configured
✅ Backend started (uvicorn server:app --reload)
✅ http://localhost:8000 responds with API info
✅ http://localhost:8000/docs loads Swagger UI
✅ http://localhost:8000/api/health returns "healthy"
✅ Can register user via /api/auth/register
✅ Can login via /api/auth/login
✅ Can view profile via /api/auth/me with token
✅ All tests passing ✓

THEN YOU'RE READY TO:
→ Build frontend UI
→ Integrate with mobile app
→ Connect to payment gateway
→ Deploy to production
```

---

## 📞 Quick Reference Card

| Need | Action |
|------|--------|
| **Start Fresh** | Run `setup-and-run.sh` |
| **Start MongoDB** | `docker run -d -p 27017:27017 mongo` |
| **Run Server** | `uvicorn server:app --reload` |
| **View Docs** | Open http://localhost:8000/docs |
| **Test API** | Import postman_collection.json |
| **Check Health** | `curl http://localhost:8000/api/health` |
| **View Database** | Use MongoDB Compass |
| **Troubleshoot** | See QUICK_START.md "Troubleshooting" |
| **Learn More** | Read BACKEND_ANALYSIS.md |
| **Get Details** | Study ARCHITECTURE.md |

---

## 🎉 You're All Set!

This backend is **production-ready** and **fully functional** on localhost!

**Next Step:** Open [QUICK_START.md](./QUICK_START.md) and follow the installation instructions.

**Then:** Visit http://localhost:8000/docs to explore the API!

---

**Generated:** November 18, 2025  
**Version:** 1.0.0  
**Status:** Ready for Production ✅
