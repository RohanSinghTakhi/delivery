# 📮 MedEx Backend - API Testing Guide

## Using Postman Collection

A complete Postman collection is available at `postman_collection.json` in the project root.

### **Import Collection in Postman**

1. Open Postman
2. Click **Import** (top left)
3. Select **File**
4. Choose `postman_collection.json`
5. Collection imported! ✅

---

## 🔑 Important: Set Environment Variables

In Postman, create an environment with these variables:

```
base_url = http://localhost:8000
access_token = (populated after login)
vendor_id = (populated after vendor registration)
driver_id = (populated after driver registration)
user_id = (populated after user registration)
order_id = (populated after creating order)
tracking_token = (populated after creating order)
```

---

## 🧪 Testing Workflow (In Order)

### **1. Health Check**
```
GET http://localhost:8000/api/health
```
**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### **2. Register User**
```
POST http://localhost:8000/api/auth/register
Content-Type: application/json

{
  "email": "user@test.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "role": "user",
  "password": "testpass123"
}
```

**Save:**
- `user_id` from response

---

### **3. Register Vendor**
```
POST http://localhost:8000/api/vendors/register
Content-Type: application/json

{
  "email": "vendor@test.com",
  "business_name": "My Pharmacy Inc",
  "phone": "+1098765432",
  "password": "vendorpass123",
  "address": "123 Main Street, NYC",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

**Save:**
- `vendor_id` from response

---

### **4. Register Driver**
```
POST http://localhost:8000/api/drivers/register
Content-Type: application/json

{
  "email": "driver@test.com",
  "full_name": "Driver Mike",
  "phone": "+1122334455",
  "password": "driverpass123",
  "vendor_id": "{{vendor_id}}",
  "vehicle_type": "bike",
  "vehicle_number": "ABC-1234",
  "license_number": "DL-123456"
}
```

**Save:**
- `driver_id` from response

---

### **5. User Login**
```
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "user@test.com",
  "password": "testpass123"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": "user-uuid",
    "email": "user@test.com",
    "full_name": "John Doe",
    "role": "user"
  },
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Save:**
- `access_token` to environment
- `user_id` to environment

---

### **6. Get Current User Profile**
```
GET http://localhost:8000/api/auth/me
Authorization: Bearer {{access_token}}
```

---

### **7. Create Order**
```
POST http://localhost:8000/api/orders
Content-Type: application/json
Authorization: Bearer {{access_token}}

{
  "user_id": "{{user_id}}",
  "vendor_id": "{{vendor_id}}",
  "pickup_address": "123 Main Street, NYC",
  "pickup_latitude": 40.7128,
  "pickup_longitude": -74.0060,
  "delivery_address": "456 Park Avenue, NYC",
  "delivery_latitude": 40.7580,
  "delivery_longitude": -73.9855,
  "customer_name": "John Doe",
  "customer_phone": "+1234567890",
  "items": [
    {"name": "Aspirin 500mg", "quantity": 2},
    {"name": "Vitamin D", "quantity": 1}
  ],
  "notes": "Call before delivery"
}
```

**Response:**
```json
{
  "id": "order-uuid",
  "order_number": "ORD-ABC12345",
  "status": "pending",
  "tracking_token": "tracking-uuid",
  "delivery_fee": 12.50,
  ...
}
```

**Save:**
- `order_id` (id field)
- `tracking_token` for public tracking

---

### **8. Get All Orders (User)**
```
GET http://localhost:8000/api/orders
Authorization: Bearer {{access_token}}
```

---

### **9. Get Order Details**
```
GET http://localhost:8000/api/orders/{{order_id}}
Authorization: Bearer {{access_token}}
```

---

### **10. Track Order (Public - No Auth)**
```
GET http://localhost:8000/api/tracking/{{tracking_token}}
```

**Response:**
```json
{
  "order": {
    "order_number": "ORD-ABC12345",
    "status": "out_for_delivery",
    "customer_name": "John Doe",
    "delivery_address": "456 Park Avenue",
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

### **11. Vendor Login**
```
POST http://localhost:8000/api/auth/login
Content-Type: application/json

{
  "email": "vendor@test.com",
  "password": "vendorpass123"
}
```

**Save vendor's `access_token`**

---

### **12. Get Vendor Orders**
```
GET http://localhost:8000/api/orders?vendor_id={{vendor_id}}
Authorization: Bearer {{access_token}}
```

---

### **13. Accept Order (Vendor)**
```
PATCH http://localhost:8000/api/orders/{{order_id}}/status
Content-Type: application/json
Authorization: Bearer {{vendor_access_token}}

{
  "status": "accepted"
}
```

---

### **14. Assign Driver to Order**
```
POST http://localhost:8000/api/orders/{{order_id}}/assign-driver
Content-Type: application/json
Authorization: Bearer {{vendor_access_token}}

{
  "driver_id": "{{driver_id}}"
}
```

---

### **15. Update Order Status (Driver)**
```
PATCH http://localhost:8000/api/orders/{{order_id}}/status
Content-Type: application/json
Authorization: Bearer {{driver_access_token}}

{
  "status": "picked_up"
}
```

**Status flow:**
- `pending` → (vendor accepts)
- `accepted` → (vendor assigns)
- `driver_assigned` → (driver picks up)
- `picked_up` → (driver delivers)
- `out_for_delivery` → (driver marks delivered)
- `delivered`

---

### **16. Update Driver Status**
```
PATCH http://localhost:8000/api/drivers/{{driver_id}}/status
Content-Type: application/json
Authorization: Bearer {{driver_access_token}}

{
  "status": "available"
}
```

**Possible values:**
- `offline`
- `available`
- `busy`
- `on_break`

---

### **17. Get Vendor Report**
```
GET http://localhost:8000/api/reports/vendors/{{vendor_id}}
Authorization: Bearer {{vendor_access_token}}
```

---

### **18. Upload Proof of Delivery**
```
POST http://localhost:8000/api/uploads/proof
Authorization: Bearer {{access_token}}

Form Data:
- file: <select image file>
- order_id: {{order_id}}
```

---

### **19. Get Driver Earnings**
```
GET http://localhost:8000/api/drivers/{{driver_id}}/earnings
Authorization: Bearer {{driver_access_token}}
```

---

### **20. Get Driver Delivery History**
```
GET http://localhost:8000/api/drivers/{{driver_id}}/deliveries
Authorization: Bearer {{driver_access_token}}
```

---

## 🔐 Authentication Header

All protected endpoints require:
```
Authorization: Bearer {{access_token}}
```

In Postman:
1. Go to **Authorization** tab
2. Select **Bearer Token**
3. Paste access token or use `{{access_token}}`

---

## 📊 Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | GET /orders |
| 201 | Created | POST /orders |
| 400 | Bad Request | Invalid data |
| 401 | Unauthorized | No/invalid token |
| 403 | Forbidden | Insufficient role |
| 404 | Not Found | Order doesn't exist |
| 500 | Server Error | Database error |

---

## 🧩 Role-Based Access

| Endpoint | User | Vendor | Driver | Admin |
|----------|------|--------|--------|-------|
| Create Order | ✅ | - | - | ✅ |
| View Own Orders | ✅ | ✅ | ✅ | ✅ |
| Accept Order | - | ✅ | - | ✅ |
| Assign Driver | - | ✅ | - | ✅ |
| Update Status | ✅ | ✅ | ✅ | ✅ |
| View Reports | - | ✅ | ✅ | ✅ |
| Track (Public) | ✅ | ✅ | ✅ | ✅ |

---

## 💾 Database Queries (MongoDB)

View data in MongoDB Compass:

```javascript
// Connected to: mongodb://localhost:27017

// View all users
db.users.find({})

// View all orders
db.orders.find({})

// View all drivers
db.drivers.find({})

// View all vendors
db.vendors.find({})

// Find orders by status
db.orders.find({ status: "delivered" })

// Find driver's orders
db.orders.find({ driver_id: "driver-uuid" })
```

---

## 📝 Common Testing Scenarios

### **Scenario 1: Complete Delivery Flow**

1. User registers and logs in
2. Vendor registers
3. Driver registers with vendor
4. User creates order
5. Vendor accepts order
6. Vendor assigns driver
7. Driver updates status: picked_up
8. Driver uploads proof photo
9. Driver marks delivered
10. Public tracking shows delivered

### **Scenario 2: Real-time Tracking**

1. User gets `tracking_token` from order creation
2. Share token with customer
3. Customer visits: http://localhost:8000/api/tracking/{token}
4. See live driver location (if assigned)
5. See ETA to delivery

### **Scenario 3: Vendor Analytics**

1. Vendor logs in
2. Gets daily report: `/api/reports/vendors/{vendor_id}`
3. Views per-driver statistics
4. Exports as CSV

---

## 🚀 Performance Testing

Use Postman Runner to test multiple requests:

1. Select **New** → **Runner**
2. Choose the collection
3. Set iterations: 10
4. Click **Run**

Monitor:
- Response times
- Success rate
- Error rate

---

## 🔍 Debugging Tips

1. **Check Response Body** - Read error messages
2. **Check Status Code** - Understand the issue
3. **Check Headers** - Authorization header present?
4. **Check Environment** - Variables set correctly?
5. **Check Database** - Data actually saved?

---

## ✅ Test Checklist

- [ ] Health check passes
- [ ] User registration works
- [ ] User login returns token
- [ ] Can create order with token
- [ ] Order has tracking_token
- [ ] Can track order publicly
- [ ] Vendor can accept order
- [ ] Vendor can assign driver
- [ ] Driver can update status
- [ ] Reports generate correctly
- [ ] File uploads work

---

**All tests passing? You're ready to integrate with frontend! 🎉**
