# 🚀 MedEx Backend - Quick Start Guide

## ⚡ 5-Minute Setup

### **Linux/Mac Users:**

```bash
# 1. Navigate to backend directory
cd /home/rohan/embolo/delivery/delivery/backend

# 2. Make script executable
chmod +x setup-and-run.sh

# 3. Run the setup script
./setup-and-run.sh
```

**That's it!** The script will:
- ✅ Check Python installation
- ✅ Start MongoDB (if Docker available)
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup configuration files
- ✅ Start the FastAPI server

---

### **Windows Users:**

```batch
# 1. Open Command Prompt in backend directory
cd C:\path\to\backend

# 2. Run the batch script
setup-and-run.bat
```

---

### **Manual Setup (if scripts don't work):**

#### Step 1: Ensure MongoDB is Running
```bash
# Using Docker (Recommended):
docker run -d -p 27017:27017 --name medex-mongodb mongo:latest

# Or ensure local MongoDB is running
```

#### Step 2: Create Virtual Environment
```bash
cd backend
python3 -m venv venv

# Activate it:
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Setup Environment Variables
```bash
# Copy the example config
cp .env.example .env

# Edit .env if needed (Google Maps API is optional)
```

#### Step 5: Run the Server
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Accessing the Backend

Once running, access:

| Resource | URL |
|----------|-----|
| **API Root** | http://localhost:8000 |
| **Swagger Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/health |

---

## 📝 First Steps - Test the API

### **1. Register a User**

Go to http://localhost:8000/docs and try:

```json
POST /api/auth/register
{
  "email": "testuser@example.com",
  "full_name": "Test User",
  "phone": "+1234567890",
  "role": "user",
  "password": "testpassword123"
}
```

### **2. Login**

```json
POST /api/auth/login
{
  "email": "testuser@example.com",
  "password": "testpassword123"
}
```

Copy the `access_token` from response.

### **3. Register a Vendor**

```json
POST /api/vendors/register
{
  "email": "vendor@example.com",
  "business_name": "My Pharmacy",
  "phone": "+1234567890",
  "password": "vendorpass123",
  "address": "123 Main Street",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

Copy the `vendor_id` from response.

### **4. Register a Driver**

```json
POST /api/drivers/register
{
  "email": "driver@example.com",
  "full_name": "Driver John",
  "phone": "+1987654321",
  "password": "driverpass123",
  "vendor_id": "PASTE_VENDOR_ID_HERE",
  "vehicle_type": "bike",
  "vehicle_number": "ABC-1234",
  "license_number": "DL-123456"
}
```

### **5. Create an Order**

Use the `access_token` from login and try:

```json
POST /api/orders
Authorization: Bearer YOUR_ACCESS_TOKEN

{
  "user_id": "YOUR_USER_ID",
  "vendor_id": "VENDOR_ID",
  "pickup_address": "123 Pharmacy",
  "pickup_latitude": 40.7128,
  "pickup_longitude": -74.0060,
  "delivery_address": "456 Home Street",
  "delivery_latitude": 40.7580,
  "delivery_longitude": -73.9855,
  "customer_name": "Test Customer",
  "customer_phone": "+1122334455",
  "items": [
    {"name": "Aspirin", "quantity": 2},
    {"name": "Vitamin D", "quantity": 1}
  ],
  "notes": "Call before delivery"
}
```

### **6. Track Order (No Auth Needed)**

```
GET /api/tracking/{tracking_token}
```

Use the `tracking_token` from order creation response.

---

## 📡 Testing with curl

If you prefer command line:

```bash
# Register User
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "full_name": "John Doe",
    "phone": "+1234567890",
    "role": "user",
    "password": "password123"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "password123"
  }'

# Health Check
curl "http://localhost:8000/api/health"
```

---

## 🔧 Configuration Reference

### **.env File**

The `.env` file in the backend directory controls everything:

```properties
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medex_delivery"

# Security (JWT)
JWT_SECRET_KEY="your-secret-key"

# Google Maps (Optional)
GOOGLE_MAPS_API_KEY="YOUR_API_KEY"

# File Uploads
UPLOAD_DIR="/app/backend/uploads"
MAX_UPLOAD_SIZE_MB=10
```

**Default values work fine for local testing!**

---

## ❌ Troubleshooting

### **Port 8000 is Already in Use**

Run on different port:
```bash
uvicorn server:app --port 8001 --reload
```

### **MongoDB Connection Error**

```bash
# Check if MongoDB is running
docker ps | grep mongo

# If not, start it:
docker run -d -p 27017:27017 --name medex-mongo mongo:latest

# Or verify local MongoDB is running:
# Linux/Mac:
sudo systemctl status mongod
```

### **Module Import Errors**

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### **Python Version Error**

```bash
# Check Python version
python3 --version

# Must be Python 3.11 or higher
# Install from: https://www.python.org
```

---

## 📚 API Routes Overview

| Category | Routes |
|----------|--------|
| **Auth** | POST /api/auth/register, POST /api/auth/login |
| **Orders** | POST /api/orders, GET /api/orders, PATCH /api/orders/{id} |
| **Drivers** | POST /api/drivers/register, GET /api/drivers, PATCH /api/drivers/{id}/status |
| **Vendors** | POST /api/vendors/register, GET /api/vendors |
| **Tracking** | GET /api/tracking/{token} (No auth) |
| **Reports** | GET /api/reports/vendors/{vendor_id} |
| **Uploads** | POST /api/uploads/proof, POST /api/uploads/signature |
| **Health** | GET /api/health |

Complete documentation: **http://localhost:8000/docs**

---

## 🎯 Next Steps

1. **Explore the API** - Visit http://localhost:8000/docs
2. **Test workflows** - Create users, orders, drivers
3. **Check MongoDB** - Use MongoDB Compass to view data
4. **Connect Frontend** - Update frontend API URL to http://localhost:8000
5. **Integrate Google Maps** (Optional) - Add real API key for geocoding

---

## 📞 API Key Setup (Optional)

### Getting Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project
3. Enable these APIs:
   - Geocoding API
   - Distance Matrix API
   - Maps JavaScript API
4. Create API Key (Restrict to HTTP)
5. Add to `.env`:
   ```
   GOOGLE_MAPS_API_KEY="your_api_key_here"
   ```

**⚠️ Not needed for local testing!** System uses mock coordinates by default.

---

## ✅ System Running Successfully When:

- ✅ Server starts without errors
- ✅ http://localhost:8000 shows API info
- ✅ http://localhost:8000/docs loads Swagger UI
- ✅ http://localhost:8000/api/health returns `{"status": "healthy", "database": "connected"}`
- ✅ Can register/login users

---

## 📖 Need More Help?

- **API Docs**: http://localhost:8000/docs
- **Full Analysis**: See `BACKEND_ANALYSIS.md`
- **Architecture**: See `ARCHITECTURE.md`
- **Database Schema**: See `ARCHITECTURE.md` (Database Schema section)

---

**Ready to build! 🚀**
