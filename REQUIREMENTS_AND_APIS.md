# 🔧 MedEx Backend - Requirements & External API Guide

## ✅ What You Need to Run This Backend

### **Local Requirements** (Essential)

| Requirement | Version | How to Install |
|-------------|---------|-----------------|
| **Python** | 3.11+ | https://www.python.org |
| **MongoDB** | 5.0+ | `docker run -d -p 27017:27017 mongo` |
| **pip** | Latest | Comes with Python |

**That's it! Everything else is installed automatically.**

---

## 📦 Python Dependencies (Auto-Installed)

When you run `pip install -r requirements.txt`, these are installed:

| Package | Version | Purpose |
|---------|---------|---------|
| **fastapi** | 0.110.1 | Web framework (REST API) |
| **uvicorn** | 0.25.0 | ASGI server (runs the app) |
| **motor** | 3.3.1 | Async MongoDB driver |
| **pydantic** | 2.6.4+ | Data validation |
| **python-dotenv** | 1.0.1+ | Load .env configuration |
| **python-jose** | 3.3.0+ | JWT token creation |
| **passlib** | 1.7.4+ | Password hashing utilities |
| **bcrypt** | 4.1.3 | Password encryption |
| **pyjwt** | 2.10.1+ | JWT token handling |
| **email-validator** | 2.2.0+ | Email validation |
| **python-multipart** | 0.0.9+ | Form data handling |
| **requests** | 2.31.0+ | HTTP client (for API calls) |
| **aiofiles** | 23.2.1+ | Async file operations |
| **websockets** | 12.0+ | WebSocket support |

---

## 🚀 MongoDB Setup (Choose One)

### **Option 1: Docker (Recommended - Easiest)**

```bash
# Install Docker first from https://www.docker.com

# Start MongoDB container
docker run -d -p 27017:27017 --name medex-mongo mongo:latest

# To stop later
docker stop medex-mongo
```

### **Option 2: Local Installation**

Download from [MongoDB Community Edition](https://www.mongodb.com/try/download/community)

```bash
# Start MongoDB service (Linux)
sudo systemctl start mongod

# Start MongoDB service (Mac)
brew services start mongodb-community

# Start MongoDB service (Windows)
# Use MongoDB Compass or start service from Services app
```

### **Option 3: Cloud MongoDB (Optional)**

Use MongoDB Atlas (cloud):
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free cluster
3. Get connection string
4. Update `.env`: `MONGO_URL="mongodb+srv://..."`

---

## 🗺️ External APIs (Optional)

### **Google Maps API - OPTIONAL** ⭐

**What it's used for:**
- Convert addresses to coordinates (geocoding)
- Calculate distances between locations
- Estimate delivery times

**Is it required?** ❌ **NO** - Works without it!

**What happens without it?**
- ✅ Uses mock coordinates (40.7128, -74.0060 - NYC)
- ✅ Distance calculated using Haversine formula
- ✅ All features work perfectly
- ✅ Perfect for local development

**Cost:** ~$5-10/month after free tier (~$200 credit)

**Setup (if you want it):**

1. **Create Google Cloud Project**
   - Go to: https://console.cloud.google.com
   - Click "Create Project"
   - Enter name: "MedEx"
   - Click "Create"

2. **Enable Required APIs**
   - In Console, search for "Geocoding API" → Enable
   - Search for "Distance Matrix API" → Enable
   - Search for "Routes API" → Enable
   - Search for "Maps JavaScript API" → Enable

3. **Create API Key**
   - Go to "Credentials" → "Create Credentials" → "API Key"
   - Restrict to "HTTP" only
   - Copy the key

4. **Add to .env**
   ```properties
   GOOGLE_MAPS_API_KEY="paste_your_key_here"
   ```

5. **Test it**
   ```bash
   curl "http://localhost:8000/api/orders" -H "Authorization: Bearer TOKEN"
   # Should use real geocoding now
   ```

**For local testing:** Just leave `GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY_HERE"` in .env

---

## 🛠️ Optional External Services

### **Redis (For Scaling WebSockets)**

**What it's for:** High-performance WebSocket scaling

**Is it required?** ❌ **NO** - In-memory works fine locally

**Setup (if needed later):**
```bash
# Docker
docker run -d -p 6379:6379 redis:latest

# Add to .env
REDIS_URL="redis://localhost:6379/0"
```

---

### **S3 Storage (For File Uploads)**

**What it's for:** Cloud file storage instead of local

**Is it required?** ❌ **NO** - Local storage works fine

**Setup (if needed later):**
- Get AWS S3 bucket
- Add credentials to .env
- Backend is already S3-ready!

---

### **Email Service (For Notifications)**

**What it's for:** Send order status emails

**Is it required?** ❌ **NO** - Not implemented yet

**Options when needed:**
- SendGrid
- AWS SES
- Mailgun

---

## 📋 Complete Environment Variables

### **Required** (In .env)
```properties
# MongoDB - Must be running
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medex_delivery"

# JWT - Generate a random secret
JWT_SECRET_KEY="your-super-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS - Allow frontend requests
CORS_ORIGINS="*"

# File Storage
UPLOAD_DIR="/app/backend/uploads"
MAX_UPLOAD_SIZE_MB=10
```

### **Optional** (Can be added later)
```properties
# Google Maps
GOOGLE_MAPS_API_KEY="YOUR_API_KEY_HERE"

# Redis (for scaling)
REDIS_URL="redis://localhost:6379/0"

# Email (future use)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your-email@gmail.com"
SMTP_PASSWORD="app-password"
```

---

## 🔍 Pre-Flight Checklist

Before starting, verify:

- [ ] Python 3.11+ installed: `python3 --version`
- [ ] MongoDB running: `docker ps | grep mongo` (or local service running)
- [ ] Can connect to MongoDB: MongoDB Compass or mongosh
- [ ] Port 8000 is free (or plan to use different port)
- [ ] All files in `backend/` directory exist
- [ ] `.env` file created with required variables

---

## 📊 System Requirements

### **Minimum (Local Development)**
- **CPU:** 2 cores
- **RAM:** 2 GB
- **Storage:** 1 GB (for MongoDB + code)
- **Network:** Localhost only (no internet needed)

### **Recommended (Local Development)**
- **CPU:** 4 cores
- **RAM:** 4 GB
- **Storage:** 2 GB
- **OS:** Windows 10+, Mac 10.14+, Ubuntu 18.04+

### **Production (Cloud/Server)**
- **CPU:** 4 cores minimum
- **RAM:** 4 GB minimum
- **Storage:** 20 GB SSD
- **Network:** Public IP, HTTPS enabled

---

## ⚡ Quick Reference

### **Install Everything**
```bash
cd backend
pip install -r requirements.txt
```

### **Start MongoDB**
```bash
# Docker (easiest)
docker run -d -p 27017:27017 mongo

# Local (if installed)
sudo systemctl start mongod  # Linux
brew services start mongodb-community  # Mac
```

### **Run Backend**
```bash
cd backend
source venv/bin/activate  # Linux/Mac
python -m uvicorn server:app --reload
```

### **Access API**
```
http://localhost:8000
http://localhost:8000/docs (Swagger)
http://localhost:8000/redoc (ReDoc)
```

---

## 🆘 Common Issues

### **"ModuleNotFoundError: No module named 'fastapi'**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### **"Connection refused to MongoDB"**
```bash
# Start MongoDB with Docker
docker run -d -p 27017:27017 mongo

# Or check local service
sudo systemctl status mongod  # Linux
```

### **"Port 8000 already in use"**
```bash
# Use different port
uvicorn server:app --port 8001 --reload

# Or kill existing process
sudo lsof -ti:8000 | xargs kill -9
```

### **"Google Maps API not working"**
```
✓ System works without it (uses mock data)
✓ Add real API key later when needed
✓ Leave as default for local development
```

---

## 📚 Dependencies Visualization

```
┌─────────────────────────────────────────────────────┐
│                FastAPI Backend                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Core Dependencies:                                 │
│  ├── FastAPI (Web Framework)                       │
│  ├── Uvicorn (Server)                              │
│  ├── Pydantic (Validation)                         │
│  └── Python-dotenv (Configuration)                 │
│                                                     │
│  Database:                                          │
│  ├── Motor (Async MongoDB Driver)                  │
│  └── MongoDB (Database)                            │
│                                                     │
│  Authentication:                                    │
│  ├── Python-jose (JWT Library)                     │
│  ├── Bcrypt (Password Hashing)                     │
│  ├── Passlib (Hashing Utilities)                   │
│  └── PyJWT (Token Handling)                        │
│                                                     │
│  External Services (Optional):                      │
│  ├── Google Maps API (Geocoding)                   │
│  ├── Redis (WebSocket Scaling)                     │
│  └── S3 (File Storage)                             │
│                                                     │
│  Utilities:                                         │
│  ├── Requests (HTTP Client)                        │
│  ├── aiofiles (Async File IO)                      │
│  └── websockets (Real-time)                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## ✅ Verification Commands

```bash
# Check Python
python3 --version  # Should be 3.11+

# Check MongoDB
docker ps | grep mongo  # Should show running container
# OR
mongosh  # Try to connect

# Check virtual environment
source venv/bin/activate
which python  # Should show venv path

# Test backend startup
cd backend
uvicorn server:app --reload
# Should print: "Uvicorn running on http://0.0.0.0:8000"

# Test API
curl http://localhost:8000/api/health
# Should return: {"status": "healthy", "database": "connected"}
```

---

## 🎯 Next Steps

1. **Install Python & MongoDB** (if not already)
2. **Run setup script** (`./setup-and-run.sh`)
3. **Verify at** http://localhost:8000/docs
4. **Read** QUICK_START.md for first API calls
5. **Add Google Maps API** (optional, later)

---

## 📞 Need Help?

- **API Docs**: http://localhost:8000/docs (interactive)
- **Installation**: See QUICK_START.md
- **Testing**: See API_TESTING.md
- **Architecture**: See ARCHITECTURE.md

---

**You're ready to go! 🚀**

All external dependencies are **optional**. The system works perfectly without them!

Start with QUICK_START.md for setup instructions.
