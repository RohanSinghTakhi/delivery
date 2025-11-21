# Testing WordPress Order Sync - Complete Guide

## Quick Verification Methods

### Method 1: Check Backend API for Synced Orders

```bash
# Get all orders synced from WooCommerce
curl -X GET "http://13.201.101.182:8000/api/orders?source=woocommerce" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Or check via browser
# http://13.201.101.182:8000/api/orders?source=woocommerce
```

### Method 2: Test Sync Endpoint Directly

```bash
# Test the sync endpoint with a sample payload
curl -X POST "http://13.201.101.182:8000/api/woocommerce/orders/sync" \
  -H "Content-Type: application/json" \
  -H "X-WC-Secret: my_super_secret_key_123" \
  -d '{
    "woo_order_id": "999",
    "woo_vendor_id": "1",
    "status": "pending",
    "customer_name": "Test Customer",
    "customer_phone": "1234567890",
    "pickup_address": "123 Store St, City",
    "delivery_address": "456 Customer Ave, City",
    "items": [
      {
        "name": "Test Product",
        "quantity": 1,
        "price": 100.00
      }
    ]
  }'
```

### Method 3: Check WordPress Error Logs

```bash
# SSH into your WordPress server and check error logs
tail -f /path/to/wordpress/wp-content/debug.log

# Or check PHP error log
tail -f /var/log/php/error.log
```

### Method 4: Check Backend Server Logs

```bash
# If running with uvicorn, check console output
# Or check application logs if configured
```

### Method 5: Query MongoDB Directly

```bash
# Connect to MongoDB and check orders collection
mongosh "mongodb://your-connection-string"
use medex_delivery
db.orders.find({ source: "woocommerce" }).pretty()
db.orders.find({ woo_order_id: "YOUR_ORDER_ID" })
```

---

## Step-by-Step Testing Process

### Step 1: Verify Plugin Configuration

1. **Check Plugin Constants** in `wordpress-plugin-woocommerce-sync.php`:
   ```php
   WOOCOMMERCE_SYNC_SECRET = 'my_super_secret_key_123'
   MEDEX_API_URL = 'http://13.201.101.182:8000'
   ```

2. **Verify Backend Environment**:
   ```bash
   # Check backend .env file
   cat backend/.env | grep WOOCOMMERCE_SYNC_SECRET
   # Should match the plugin secret
   ```

### Step 2: Create a Test Order in WordPress

1. Go to WooCommerce → Orders
2. Create a new test order (or use existing)
3. Complete the order (this triggers `woocommerce_thankyou` hook)
4. Check if sync was triggered

### Step 3: Check Sync Status

**Option A: Via Backend API**
```bash
# Get order by WooCommerce ID
curl "http://13.201.101.182:8000/api/orders?woo_order_id=YOUR_ORDER_ID"
```

**Option B: Via Backend Admin Panel**
- Visit: `http://13.201.101.182:8000/docs`
- Use the `/api/orders` endpoint to search for orders with `source: "woocommerce"`

### Step 4: Test Status Update Sync

1. In WordPress, change an order status (e.g., pending → processing)
2. This should trigger `medex_sync_order_on_status_change`
3. Check backend to verify status was updated

---

## Enhanced Plugin with Better Logging

The plugin already logs errors, but you can enhance it for better debugging:

```php
// Add to wordpress-plugin-woocommerce-sync.php after line 112

// Add success logging
if ($status_code === 200 || $status_code === 201) {
    error_log('MedEx sync successful for order #' . $order_id);
    $response_body = wp_remote_retrieve_body($response);
    error_log('MedEx response: ' . $response_body);
}
```

---

## Troubleshooting Common Issues

### Issue 1: "Unknown vendor for WooCommerce sync"

**Solution**: The vendor must exist in MedEx backend with matching `woo_vendor_id`
- Check: `GET /api/vendors` to see existing vendors
- Ensure vendor has `woo_vendor_id` field set

### Issue 2: "Invalid WooCommerce secret"

**Solution**: Secret mismatch between plugin and backend
- Verify `WOOCOMMERCE_SYNC_SECRET` in both places match exactly

### Issue 3: Connection refused / Timeout

**Solution**: Backend not accessible from WordPress server
- Check firewall rules
- Verify backend URL is correct
- Test connectivity: `curl http://13.201.101.182:8000/api/health`

### Issue 4: Orders not appearing in backend

**Solution**: Check multiple things
1. Plugin is activated in WordPress
2. WordPress hooks are firing (check error logs)
3. Backend is running and accessible
4. MongoDB is connected and working

---

## Automated Test Script

See `test_wordpress_sync.py` for automated testing.

