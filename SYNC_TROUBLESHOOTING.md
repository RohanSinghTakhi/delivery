# WordPress Sync Troubleshooting - Step by Step

## Current Status
Based on `http://13.201.101.182:8000/api/woocommerce/orders/stats`:
- **Total synced orders: 0** ❌
- **Recent orders 24h: 0** ❌

This means orders are NOT syncing. Let's fix it step by step.

---

## Step 1: Check Plugin Activation

1. Go to WordPress Admin → Plugins
2. Look for "WooCommerce Order Sync to MedEx"
3. Make sure it's **Activated** (not just installed)

**If not activated:**
- Click "Activate"
- Check for any activation errors

---

## Step 2: Verify Configuration

### Check Plugin Constants
In `wordpress-plugin-woocommerce-sync-integrated.php` (or your active plugin file):

```php
WOOCOMMERCE_SYNC_SECRET = 'my_super_secret_key_123'
MEDEX_API_URL = 'http://13.201.101.182:8000'
```

### Check Backend .env
```bash
cd /home/rohan/embolo/delivery/delivery/backend
cat .env | grep WOOCOMMERCE_SYNC_SECRET
```

**Must match exactly!** No extra spaces, same case.

---

## Step 3: Map Your Vendors (CRITICAL)

The sync requires vendors to exist in MedEx backend with matching `woo_vendor_id`.

### Option A: Check Existing Vendors
```bash
# Get list of vendors (requires auth token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://13.201.101.182:8000/api/vendors
```

### Option B: Map Vendor Manually
```bash
# Set woo_vendor_id for a vendor
# Replace VENDOR_ID with MedEx vendor ID
# Replace WOO_VENDOR_ID with WordPress user ID (vendor ID)

curl -X PATCH \
  "http://13.201.101.182:8000/api/vendors/VENDOR_ID/woo-id?woo_vendor_id=WOO_VENDOR_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Option C: Check if Vendor is Mapped
```bash
# Check if WordPress vendor ID is mapped
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://13.201.101.182:8000/api/vendors/by-woo-id/WOO_VENDOR_ID"
```

**Example:**
If your WordPress vendor has user ID `5`, and your MedEx vendor ID is `abc123`:
```bash
curl -X PATCH \
  "http://13.201.101.182:8000/api/vendors/abc123/woo-id?woo_vendor_id=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Step 4: Test the Sync

### Create a Test Order
1. Go to WooCommerce → Add Order
2. Create a test order with products from your vendor
3. Complete/place the order

### Check WordPress Logs
```bash
# SSH into WordPress server
tail -f wp-content/debug.log | grep "MedEx Sync"
```

**Look for:**
- `[MedEx Sync] SUCCESS` = Working! ✅
- `[MedEx Sync] FAILED` = Check error message ❌
- `[MedEx Sync] ERROR` = Connection issue ❌
- No logs = Plugin not running or hooks not firing ❌

### Check Backend Stats
```bash
curl http://13.201.101.182:8000/api/woocommerce/orders/stats
```

Should show `total_synced_orders > 0` if working.

---

## Step 5: Common Issues & Fixes

### Issue: "Unknown vendor for WooCommerce sync"

**Cause:** Vendor doesn't exist in backend or `woo_vendor_id` not set

**Fix:**
1. Create vendor in backend (if doesn't exist)
2. Map vendor using Step 3 above

### Issue: "Invalid WooCommerce secret"

**Cause:** Secret mismatch

**Fix:**
1. Check plugin: `WOOCOMMERCE_SYNC_SECRET`
2. Check backend `.env`: `WOOCOMMERCE_SYNC_SECRET`
3. Must match exactly (no spaces, same case)
4. Restart backend after changing `.env`

### Issue: Connection refused / Timeout

**Cause:** Backend not accessible from WordPress server

**Fix:**
1. Test from WordPress server:
   ```bash
   curl http://13.201.101.182:8000/api/health
   ```
2. Check firewall rules
3. Verify backend is running:
   ```bash
   ps aux | grep uvicorn
   ```

### Issue: No logs in WordPress

**Cause:** Plugin not active or hooks not firing

**Fix:**
1. Verify plugin is activated
2. Check WordPress debug mode is enabled:
   ```php
   // In wp-config.php
   define('WP_DEBUG', true);
   define('WP_DEBUG_LOG', true);
   ```
3. Try the integrated plugin version

---

## Step 6: Use Integrated Plugin

The integrated plugin (`wordpress-plugin-woocommerce-sync-integrated.php`) uses the **same vendor ID logic** as your webhook handler:

1. Gets vendor from product meta `_vendor_id`
2. Falls back to product author
3. Falls back to order author

**To use it:**
1. Deactivate current plugin
2. Upload `wordpress-plugin-woocommerce-sync-integrated.php`
3. Activate it
4. It will work alongside your webhook handler automatically

---

## Quick Test Script

Add this to WordPress temporarily to test sync:

```php
// Add to functions.php temporarily
add_action('admin_init', function() {
    if (isset($_GET['test_medex']) && current_user_can('manage_options')) {
        $order_id = intval($_GET['order_id'] ?? 0);
        if ($order_id && function_exists('medex_sync_order_to_backend')) {
            $result = medex_sync_order_to_backend($order_id);
            wp_die($result ? '✅ Sync successful!' : '❌ Sync failed - check logs');
        }
    }
});
```

Then visit: `https://embolo.in/wp-admin/?test_medex=1&order_id=YOUR_ORDER_ID`

---

## Expected Flow

1. **Order created in WordPress** → `woocommerce_new_order` hook fires
2. **Your webhook handler** → Sends to SSE server ✅
3. **MedEx plugin** → Syncs to backend ✅
4. **Backend receives** → Creates/updates order in MongoDB
5. **Stats endpoint** → Shows synced orders

---

## Verification Checklist

- [ ] Plugin is activated
- [ ] `WOOCOMMERCE_SYNC_SECRET` matches in plugin and backend
- [ ] `MEDEX_API_URL` is correct
- [ ] Backend is accessible from WordPress server
- [ ] Vendors exist in backend
- [ ] Vendors have `woo_vendor_id` set
- [ ] WordPress debug logging is enabled
- [ ] Test order created
- [ ] WordPress logs show sync attempts
- [ ] Backend stats show synced orders

---

## Still Not Working?

1. **Check backend logs:**
   ```bash
   # If running with uvicorn --reload, check console
   # Or check application logs
   ```

2. **Test sync endpoint directly:**
   ```bash
   curl -X POST "http://13.201.101.182:8000/api/woocommerce/orders/sync" \
     -H "Content-Type: application/json" \
     -H "X-WC-Secret: my_super_secret_key_123" \
     -d '{
       "woo_order_id": "999",
       "woo_vendor_id": "1",
       "status": "pending",
       "customer_name": "Test",
       "customer_phone": "1234567890",
       "pickup_address": "123 Store St",
       "delivery_address": "456 Customer Ave",
       "items": [{"name": "Test", "quantity": 1, "price": 100}]
     }'
   ```

3. **Check MongoDB directly:**
   ```bash
   mongosh "your-connection-string"
   use medex_delivery
   db.orders.find({ source: "woocommerce" })
   ```

---

## Next Steps After Fix

Once sync is working:
1. Monitor stats endpoint regularly
2. Check WordPress logs for any errors
3. Set up alerts if sync fails
4. Consider adding retry logic for failed syncs

