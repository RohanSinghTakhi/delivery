# MedEx Delivery - B2B Medical Delivery System

A complete, production-ready B2B medical delivery system similar to Zomato-style logistics, built with FastAPI (Python) + React + MongoDB.

## 🚀 Features

### Core Modules

#### 1. **User Features**
- User registration and JWT authentication
- Address management with Google Maps geocoding
- Create orders with live location sharing
- Real-time order tracking
- Public tracking link (no auth required)
- Order status tracking:
  - Pending → Accepted → Driver Assigned → Picked Up → Out for Delivery → Delivered

#### 2. **Vendor Features**
- Vendor registration and dashboard
- View incoming orders in real-time
- Assign drivers to orders (manual/auto-assign)
- Live driver fleet tracking on map
- Daily driver reports and analytics
- Order management and status updates
- CSV export functionality

#### 3. **Driver Features**
- Driver registration and mobile-first web UI
- Receive and accept/decline orders
- Real-time location broadcasting (every 3-5 seconds)
- Update delivery status:
  - Picked Up → Out for Delivery → Delivered
- Proof of delivery (photo + signature upload)
- Earnings dashboard and delivery history
- Auto-update availability (online/offline)

## 📁 Project Structure

```
/app/
├── backend/                 # FastAPI Backend
│   ├── models/             # Pydantic models
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic
│   ├── websockets/         # WebSocket handlers
│   ├── middleware/         # Auth & middleware
│   ├── utils/              # Helpers (JWT, Maps, Files)
│   ├── uploads/            # Local file storage
│   ├── server.py           # Main application
│   ├── requirements.txt
│   └── .env
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── pages/          # Main pages
│   │   ├── components/     # Reusable components
│   │   ├── services/       # API & WebSocket clients
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── .env
├── docker-compose.yml      # Container orchestration
└── README.md
```

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python) with async/await
- **Database**: MongoDB with 2dsphere geospatial indexes
- **Real-time**: WebSocket (in-memory, Redis-ready)
- **Frontend**: React with Tailwind CSS + shadcn/ui
- **Auth**: JWT (access + refresh tokens)
- **Maps**: Google Maps APIs (Geocoding, Directions, Distance Matrix)
- **File Storage**: Local uploads (S3-ready architecture)

## 🚦 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB
- Google Maps API Key (optional for development)

### Installation

1. **Clone the repository**
```bash
cd /app
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Update .env with your configuration
cp .env.example .env
```

3. **Frontend Setup**
```bash
cd frontend
yarn install

# Update .env with your configuration
cp .env.example .env
```

4. **Start Services**
```bash
# Backend (via supervisor)
sudo supervisorctl restart backend

# Frontend (via supervisor)
sudo supervisorctl restart frontend
```

### Configuration

#### Backend (.env)
```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="medex_delivery"
CORS_ORIGINS="*"

# JWT Configuration
JWT_SECRET_KEY="your-secret-key"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Maps API (add your key)
GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY_HERE"

# File Upload
UPLOAD_DIR="/app/backend/uploads"
MAX_UPLOAD_SIZE_MB=10
```

#### Frontend (.env)
```env
REACT_APP_BACKEND_URL=https://your-backend-url.com
REACT_APP_GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE
```

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

### Key API Endpoints

#### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

#### Orders
- `POST /api/orders` - Create order
- `GET /api/orders` - Get orders (filtered by role)
- `GET /api/orders/{id}` - Get specific order
- `PATCH /api/orders/{id}/status` - Update order status
- `POST /api/orders/{id}/assign` - Assign driver

#### Drivers
- `POST /api/drivers/register` - Register driver
- `GET /api/drivers` - Get drivers
- `PATCH /api/drivers/{id}/status` - Update driver status
- `POST /api/drivers/{id}/location` - Update location (HTTP fallback)

#### Tracking
- `GET /api/tracking/{token}` - Public order tracking

#### Reports
- `GET /api/reports/vendors/{id}` - Vendor daily report
- `GET /api/reports/drivers/{id}` - Driver earnings report

#### Webhooks
- `POST /api/webhooks/wc/order-created` - WooCommerce order webhook
- `POST /api/webhooks/wc/order-updated` - WooCommerce update webhook

### WebSocket Endpoints

- `WS /ws/driver?token={jwt}` - Driver location streaming
- `WS /ws/vendor/{vendor_id}?token={jwt}` - Vendor fleet tracking
- `WS /ws/tracking/{tracking_token}` - Public order tracking

## 🗺️ Google Maps Integration

The system uses Google Maps APIs for:

1. **Geocoding API**: Convert addresses to coordinates
2. **Directions API**: Calculate routes and ETA
3. **Distance Matrix API**: Calculate distances
4. **Maps JavaScript API**: Display maps in frontend

### Required APIs
Enable these in Google Cloud Console:
- Geocoding API
- Directions API
- Distance Matrix API
- Maps JavaScript API

### Development Mode
Without a valid API key, the system uses:
- Mock coordinates (NYC default)
- Haversine distance calculation
- Estimated ETA based on average speed

## 🔄 WebSocket Architecture

### In-Memory Implementation (Current)
The system uses an in-memory connection manager for MVP deployment.

### Redis Scaling (Future)
For production scale:

```python
# Install: pip install redis aioredis
# Replace WebSocket manager with Redis pub/sub
# See /app/backend/websockets/manager.py for migration guide
```

## 📱 Mobile Upgrade Path

The Driver Web UI is built mobile-first and can be converted to native apps:

### Option 1: Expo (React Native)
See `MOBILE_UPGRADE.md` for detailed migration steps.

### Option 2: PWA
The current React app can be configured as a Progressive Web App:
- Add service worker
- Configure manifest.json
- Enable "Add to Home Screen"

## 🔐 Security

- JWT-based authentication with refresh tokens
- Role-based access control (user, vendor, driver, admin)
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- File upload size limits

## 📊 Database Indexes

MongoDB indexes are created automatically on startup:

```python
# Geospatial indexes (2dsphere)
- drivers: (current_latitude, current_longitude)
- orders: (pickup_latitude, pickup_longitude)
- orders: (delivery_latitude, delivery_longitude)
- location_events: (latitude, longitude)

# TTL index
- location_events: expires after 30 days

# Unique indexes
- users: email, id
- orders: order_number, tracking_token
- drivers: id
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Checklist

- [ ] Update JWT_SECRET_KEY
- [ ] Configure production MongoDB URL
- [ ] Add Google Maps API key
- [ ] Set up cloud storage (S3/Cloudinary)
- [ ] Configure Redis for WebSocket scaling
- [ ] Set up SSL/TLS certificates
- [ ] Configure rate limiting
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure backup strategy
- [ ] Set up logging aggregation

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest
```

### Frontend Testing
```bash
cd frontend
yarn test
```

### API Testing
Import `postman_collection.json` into Postman for pre-configured API tests.

## 📝 Environment Variables

### Backend
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `JWT_SECRET_KEY`: Secret for JWT signing
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- `CORS_ORIGINS`: Allowed CORS origins
- `UPLOAD_DIR`: File upload directory

### Frontend
- `REACT_APP_BACKEND_URL`: Backend API URL
- `REACT_APP_GOOGLE_MAPS_API_KEY`: Google Maps API key

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check `ARCHITECTURE.md` for system design details
- See `MOBILE_UPGRADE.md` for mobile app migration

## 🔮 Roadmap

- [ ] Redis integration for WebSocket scaling
- [ ] S3 integration for file storage
- [ ] Advanced driver assignment algorithms
- [ ] Route optimization
- [ ] In-app chat between driver and customer
- [ ] Push notifications
- [ ] Stripe/PayPal payment integration
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Mobile apps (iOS/Android)

---

**Built with ❤️ for efficient medical deliveries**