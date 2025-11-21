# 📚 MedEx Backend - Complete Documentation Index

## 📖 Documentation Files

| Document | Purpose | For |
|----------|---------|-----|
| **QUICK_START.md** | 5-minute setup guide | Getting started fast |
| **BACKEND_ANALYSIS.md** | Complete system analysis | Understanding the system |
| **API_TESTING.md** | API testing workflows | Testing with Postman |
| **ARCHITECTURE.md** | System design details | Deep dive |
| **This File** | Documentation index | Navigation |

---

## 🎯 What is This Backend?

**MedEx Delivery** is a **B2B Medical Delivery System** - similar to Zomato but for pharmacies delivering medicines.

### **Key Features:**
- ✅ **Users** can order medicines from pharmacies
- ✅ **Vendors** (pharmacies) manage deliveries
- ✅ **Drivers** pick up and deliver orders
- ✅ **Real-time Tracking** via WebSockets
- ✅ **Public Tracking** - share link with customers
- ✅ **Analytics & Reports** for vendors
- ✅ **File Uploads** - proof of delivery photos
- ✅ **JWT Authentication** - secure access

---

## 🚀 Quick Links

### **For First-Time Setup:**
👉 Start here: [QUICK_START.md](./QUICK_START.md)

### **To Understand the System:**
👉 Read: [BACKEND_ANALYSIS.md](./BACKEND_ANALYSIS.md)

### **To Test the API:**
👉 Follow: [API_TESTING.md](./API_TESTING.md)

### **For Technical Details:**
👉 Study: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 📋 System Overview

### **Architecture**

```
┌────────────────────────────────────────┐
│      FastAPI Backend (localhost:8000)  │
├────────────────────────────────────────┤
│                                        │
│  REST API Routes (/api/...)            │
│  ├── auth        (Login/Register)      │
│  ├── orders      (Order Management)    │
│  ├── drivers     (Driver Management)   │
│  ├── vendors     (Vendor Dashboard)    │
│  ├── tracking    (Public Tracking)     │
│  ├── reports     (Analytics)           │
│  ├── uploads     (File Storage)        │
│  └── webhooks    (Integrations)        │
│                                        │
│  WebSocket Routes (/ws/...)            │
│  ├── /driver     (Location Tracking)   │
│  ├── /vendor     (Fleet Tracking)      │
│  └── /tracking   (Public Tracking)     │
│                                        │
└────────────────┬──────────────────────┘
                 │
                 ▼
         ┌──────────────────┐
         │    MongoDB       │
         │  (Port 27017)    │
         └──────────────────┘
```

### **Tech Stack**

- **Framework**: FastAPI (Python)
- **Database**: MongoDB
- **Real-time**: WebSockets
- **Auth**: JWT Tokens
- **Maps**: Google Maps (optional)
- **Server**: Uvicorn

---

## 📊 Database Collections

| Collection | Purpose | Key Fields |
|------------|---------|-----------|
| **users** | User accounts | email, role, password |
| **vendors** | Pharmacies | business_name, address, drivers |
| **drivers** | Delivery personnel | vehicle, vendor_id, status |
| **orders** | Delivery requests | user_id, vendor_id, driver_id |

---

## 🔑 API Routes (Summary)

### **Authentication (`/api/auth`)**
- POST `/register` - Register user
- POST `/login` - Login user
- POST `/refresh` - Refresh token
- GET `/me` - Current user profile

### **Orders (`/api/orders`)**
- POST `/` - Create order
- GET `/` - Get orders
- PATCH `/{id}` - Update status
- POST `/{id}/assign-driver` - Assign driver
- DELETE `/{id}` - Cancel order

### **Drivers (`/api/drivers`)**
- POST `/register` - Register driver
- GET `/` - List drivers
- PATCH `/{id}/status` - Update status
- GET `/{id}/earnings` - View earnings
- GET `/{id}/deliveries` - Delivery history

### **Vendors (`/api/vendors`)**
- POST `/register` - Register vendor
- GET `/` - List vendors
- GET `/{id}/orders` - Vendor orders
- POST `/{id}/export-csv` - Export report

### **Tracking (`/api/tracking`)**
- GET `/{tracking_token}` - Public order tracking

### **Reports (`/api/reports`)**
- GET `/vendors/{vendor_id}` - Vendor report
- GET `/vendors/{vendor_id}/drivers` - Driver stats

### **Uploads (`/api/uploads`)**
- POST `/proof` - Upload proof photo
- POST `/signature` - Upload signature

---

## ⚡ Installation (30 seconds)

### **Quick Setup:**

```bash
# Linux/Mac
cd backend
chmod +x setup-and-run.sh
./setup-and-run.sh

# Windows
cd backend
setup-and-run.bat
```

### **Manual Setup:**

```bash
# 1. Start MongoDB
docker run -d -p 27017:27017 mongo

# 2. Create Python environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run server
uvicorn server:app --reload
```

---

## 🌐 Accessing Services

| Service | URL |
|---------|-----|
| **API Server** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **API Docs (ReDoc)** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/health |
| **MongoDB** | mongodb://localhost:27017 |

---

## 📝 Testing the API

### **Using Swagger UI (Easiest):**
1. Go to http://localhost:8000/docs
2. Click "Try it out" on any endpoint
3. Fill in parameters and "Execute"

### **Using Postman:**
1. Import `postman_collection.json`
2. Follow workflows in [API_TESTING.md](./API_TESTING.md)

### **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "pass123"}'
```

---

## 🔐 Security Features

| Feature | Implementation |
|---------|-----------------|
| **Password Hashing** | Bcrypt (salted) |
| **Authentication** | JWT Tokens |
| **Authorization** | Role-based access control |
| **Token Expiry** | 15 min access, 7 day refresh |
| **CORS** | Configured for frontend |
| **HTTPS Ready** | Can be deployed with SSL |

---

## 🗂️ File Structure

```
backend/
├── server.py                 # Main application
├── requirements.txt          # Dependencies
├── .env                      # Configuration (create this)
├── .env.example              # Template
│
├── models/                   # Data models
│   ├── user.py
│   ├── order.py
│   ├── driver.py
│   ├── vendor.py
│   └── ...
│
├── routes/                   # API endpoints
│   ├── auth.py
│   ├── orders.py
│   ├── drivers.py
│   ├── vendors.py
│   ├── tracking.py
│   ├── reports.py
│   ├── uploads.py
│   └── webhooks.py
│
├── middleware/               # Auth & middleware
├── utils/                    # Helper functions
├── websockets/               # Real-time
└── uploads/                  # File storage
```

---

## 🆘 Troubleshooting

### **Problem: Port 8000 already in use**
```bash
# Use different port
uvicorn server:app --port 8001
```

### **Problem: MongoDB not found**
```bash
# Start MongoDB with Docker
docker run -d -p 27017:27017 mongo
```

### **Problem: Module import errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### **Problem: JWT token invalid**
```bash
# Change JWT_SECRET_KEY in .env
JWT_SECRET_KEY="new-secret-key-here"
```

For more solutions, see [QUICK_START.md](./QUICK_START.md)

---

## 🎓 Learning Path

1. **Start**: Read [QUICK_START.md](./QUICK_START.md)
2. **Setup**: Run setup script
3. **Test**: Use Swagger at http://localhost:8000/docs
4. **Learn**: Read [BACKEND_ANALYSIS.md](./BACKEND_ANALYSIS.md)
5. **Integrate**: Connect frontend to API
6. **Deploy**: See [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## 🔄 User Roles & Permissions

| Action | User | Vendor | Driver | Admin |
|--------|------|--------|--------|-------|
| Create Account | ✅ | ✅ | ✅ | ✅ |
| Create Order | ✅ | ✅ | - | ✅ |
| Accept Order | - | ✅ | - | ✅ |
| Assign Driver | - | ✅ | - | ✅ |
| Update Delivery Status | - | - | ✅ | ✅ |
| View Reports | - | ✅ | ✅ | ✅ |
| Public Tracking | ✅ | - | - | - |

---

## 📈 API Statistics

| Metric | Count |
|--------|-------|
| **REST Endpoints** | 50+ |
| **WebSocket Routes** | 3 |
| **Database Collections** | 4 |
| **Models/Schemas** | 10+ |
| **Authentication Methods** | JWT + Roles |
| **File Upload Types** | Images (JPG, PNG) |

---

## 🚀 External API Requirements

### **Google Maps (Optional)**

**What it does:**
- Converts addresses to coordinates (geocoding)
- Calculates delivery distances
- Estimates delivery times

**Cost:** ~$5-10/month (includes free tier)

**For local testing:** Not needed! System uses mock data.

**Setup:**
1. Get API key from [Google Cloud Console](https://console.cloud.google.com)
2. Add to `.env`: `GOOGLE_MAPS_API_KEY="your_key"`

**System works perfectly without it!** ✅

---

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:8000
- [ ] MongoDB connected successfully
- [ ] Swagger docs accessible at /docs
- [ ] Health check returns `healthy`
- [ ] Can register and login users
- [ ] Can create orders
- [ ] Can view orders
- [ ] Public tracking works (no auth)
- [ ] All responses have correct status codes

---

## 📞 Support Resources

| Resource | Link |
|----------|------|
| **API Documentation** | http://localhost:8000/docs |
| **Alternative Docs** | http://localhost:8000/redoc |
| **Database Visualization** | MongoDB Compass |
| **API Testing** | Postman + Collection |
| **Code Editor** | VS Code (recommended) |

---

## 🎯 Next Steps

1. **Run the backend** - Follow [QUICK_START.md](./QUICK_START.md)
2. **Test all APIs** - Use [API_TESTING.md](./API_TESTING.md)
3. **Connect frontend** - Update API URL in frontend
4. **Setup Google Maps** (optional) - Add API key to .env
5. **Deploy** - Use Docker for production

---

## 📦 Dependencies Summary

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.110.1 | Web framework |
| uvicorn | 0.25.0 | ASGI server |
| motor | 3.3.1 | MongoDB driver |
| pydantic | 2.6.4+ | Validation |
| python-jose | 3.3.0+ | JWT tokens |
| bcrypt | 4.1.3 | Password hashing |
| websockets | 12.0+ | Real-time |
| requests | 2.31.0+ | HTTP client |

See `requirements.txt` for full list.

---

## 🎉 You're All Set!

This backend is **production-ready** and can run on localhost **without any external dependencies**!

### **Start Now:**
```bash
cd backend
./setup-and-run.sh  # Linux/Mac
# or
setup-and-run.bat   # Windows
```

### **Then Visit:**
http://localhost:8000/docs

---

**Generated:** November 18, 2025  
**Version:** 1.0.0  
**Status:** Ready for Production ✅

---

## 📚 Document Index

- [📖 QUICK_START.md](./QUICK_START.md) - Get started in 5 minutes
- [📖 BACKEND_ANALYSIS.md](./BACKEND_ANALYSIS.md) - Complete system analysis
- [📖 API_TESTING.md](./API_TESTING.md) - Testing workflows
- [📖 ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture
- [📖 README.md](./README.md) - Original project README

---

**Happy coding! 🚀**
