# Quick WordPress Sync Check - Quick Reference

## 🚀 Fastest Way to Check Sync

### 1. Check Sync Statistics (No Auth Required)
```bash
curl http://13.201.101.182:8000/api/woocommerce/orders/stats
```

**Or visit in browser:**
```
http://13.201.101.182:8000/api/woocommerce/orders/stats
```

This shows:
- Total synced orders
- Recent orders (last 24h)
- Orders by status

### 2. Check Specific Order
```bash
# Replace ORDER_ID with your WooCommerce order ID
curl http://13.201.101.182:8000/api/woocommerce/orders/check/ORDER_ID
```

**Example:**
```
http://13.201.101.182:8000/api/woocommerce/orders/check/12345
```

### 3. Run Test Script
```bash
cd /home/rohan/embolo/delivery/delivery
python3 test_wordpress_sync.py
```

### 4. Check WordPress Logs
```bash
# SSH into WordPress server
tail -f /path/to/wordpress/wp-content/debug.log | grep "MedEx Sync"
```

---

## ✅ What to Look For

### In Backend Response:
- `"synced": true` = Order is in backend ✅
- `"synced": false` = Order not found ❌

### In WordPress Logs:
- `[MedEx Sync] SUCCESS` = Sync worked ✅
- `[MedEx Sync] FAILED` = Sync failed ❌
- `[MedEx Sync] ERROR` = Connection/API error ❌

---

## 🔧 Quick Fixes

### If sync is not working:

1. **Check Secret Match:**
   - Plugin: `WOOCOMMERCE_SYNC_SECRET = 'my_super_secret_key_123'`
   - Backend `.env`: `WOOCOMMERCE_SYNC_SECRET=my_super_secret_key_123`
   - Must match exactly!

2. **Check Backend URL:**
   - Plugin: `MEDEX_API_URL = 'http://13.201.101.182:8000'`
   - Test: `curl http://13.201.101.182:8000/api/health`

3. **Check Vendor ID:**
   - Vendor must exist in backend
   - Must have `woo_vendor_id` field matching WordPress vendor ID

---

## 📝 Test Order Creation

1. Go to WooCommerce → Add Order
2. Create test order
3. Complete/place order
4. Check sync status:
   ```bash
   curl http://13.201.101.182:8000/api/woocommerce/orders/check/ORDER_ID
   ```

---

## 🔍 Full Documentation

See `TEST_WORDPRESS_SYNC.md` for complete testing guide.

