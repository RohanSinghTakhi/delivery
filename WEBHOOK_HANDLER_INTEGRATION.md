# Integrating MedEx Sync with Existing Webhook Handler

## Quick Integration Guide

Your existing `Webhook_Handler` class already handles order creation and status changes. To add MedEx sync, you have two options:

### Option 1: Use the Standalone Plugin (Recommended)

The plugin (`wordpress-plugin-woocommerce-sync-integrated.php`) already hooks into the same events as your webhook handler:
- `woocommerce_new_order` - Same hook your handler uses
- `woocommerce_order_status_changed` - Same hook your handler uses

**Just activate the plugin** - it will work alongside your existing webhook handler automatically.

### Option 2: Add MedEx Sync Directly to Webhook Handler

Add MedEx sync calls directly in your `Webhook_Handler` class methods:

```php
// In handle_new_order method, add after sending webhook:
foreach ($vendor_ids as $vendor_id) {
    // Existing webhook code...
    $this->send_webhook($vendor_id, 'order_created', $order);
    
    // ADD THIS: Sync to MedEx
    if (function_exists('medex_sync_order_to_backend')) {
        medex_sync_order_to_backend($order_id, $vendor_id);
    }
}

// In handle_order_status_changed method, add:
// ADD THIS: Sync status to MedEx
if (function_exists('medex_sync_order_status')) {
    medex_sync_order_status($order_id, $new_status);
}
```

---

## Why Orders Aren't Syncing

Based on the stats showing 0 orders, here are the most likely issues:

### 1. Plugin Not Activated
- Go to WordPress Admin → Plugins
- Activate "WooCommerce Order Sync to MedEx (Integrated)"

### 2. Vendor ID Mismatch
The sync requires vendors to exist in MedEx backend with matching `woo_vendor_id`.

**Check if vendor exists:**
```bash
# Check backend for vendors
curl http://13.201.101.182:8000/api/vendors
```

**Create vendor in backend if missing:**
```bash
curl -X POST "http://13.201.101.182:8000/api/vendors/register" \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "Your Vendor Name",
    "email": "vendor@example.com",
    "phone": "1234567890",
    "address": "Vendor Address",
    "password": "secure_password"
  }'
```

**Then update vendor with woo_vendor_id:**
```bash
# You'll need to update the vendor document in MongoDB to add woo_vendor_id
# Or add an endpoint to update vendor with woo_vendor_id
```

### 3. Secret Mismatch
- Plugin: `WOOCOMMERCE_SYNC_SECRET = 'my_super_secret_key_123'`
- Backend `.env`: `WOOCOMMERCE_SYNC_SECRET=my_super_secret_key_123`
- Must match exactly!

### 4. Check WordPress Error Logs
```bash
# SSH into WordPress server
tail -f wp-content/debug.log | grep "MedEx Sync"
```

Look for:
- `[MedEx Sync] SUCCESS` = Working ✅
- `[MedEx Sync] FAILED` = Check error message ❌
- `[MedEx Sync] ERROR` = Connection/API issue ❌

---

## Testing the Integration

### Step 1: Test Sync Function Directly

Add this to your WordPress theme's `functions.php` temporarily:

```php
add_action('init', function() {
    if (isset($_GET['test_medex_sync']) && current_user_can('manage_options')) {
        $order_id = intval($_GET['order_id'] ?? 0);
        if ($order_id) {
            if (function_exists('medex_sync_order_to_backend')) {
                $result = medex_sync_order_to_backend($order_id);
                wp_die($result ? 'Sync successful!' : 'Sync failed - check logs');
            } else {
                wp_die('MedEx sync function not found - plugin may not be active');
            }
        }
    }
});
```

Then visit: `https://embolo.in/?test_medex_sync=1&order_id=YOUR_ORDER_ID`

### Step 2: Create Test Order

1. Create a new order in WooCommerce
2. Check WordPress logs: `tail -f wp-content/debug.log | grep "MedEx Sync"`
3. Check backend: `curl http://13.201.101.182:8000/api/woocommerce/orders/stats`

### Step 3: Verify Vendor Mapping

The sync uses the same vendor ID logic as your webhook handler:
- Gets vendor from product meta `_vendor_id`
- Falls back to product author
- Falls back to order author

Make sure your vendors in MedEx backend have the `woo_vendor_id` field matching these WordPress user IDs.

---

## Quick Fix: Add Vendor Endpoint

Add this endpoint to your backend to easily map WordPress vendors:

```python
# In backend/routes/vendors.py
@router.post("/vendors/{vendor_id}/woo-id")
async def set_woo_vendor_id(vendor_id: str, woo_vendor_id: str, current_user: dict = Depends(get_current_user)):
    """Set WooCommerce vendor ID for a MedEx vendor"""
    await db.vendors.update_one(
        {"id": vendor_id},
        {"$set": {"woo_vendor_id": woo_vendor_id}}
    )
    return {"message": "WooCommerce vendor ID set", "vendor_id": vendor_id, "woo_vendor_id": woo_vendor_id}
```

Then call it to map your vendors:
```bash
curl -X POST "http://13.201.101.182:8000/api/vendors/VENDOR_ID/woo-id?woo_vendor_id=WORDPRESS_VENDOR_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Expected Behavior

When an order is created:
1. Your webhook handler sends to SSE server ✅ (already working)
2. MedEx plugin syncs to backend ✅ (should work after setup)
3. Both happen independently and don't interfere

When order status changes:
1. Your webhook handler sends status update ✅
2. MedEx plugin syncs status to backend ✅

---

## Debugging Checklist

- [ ] Plugin is activated
- [ ] `WOOCOMMERCE_SYNC_SECRET` matches in plugin and backend
- [ ] `MEDEX_API_URL` is correct in plugin
- [ ] Backend is accessible from WordPress server
- [ ] Vendors exist in backend with matching `woo_vendor_id`
- [ ] WordPress error logs show sync attempts
- [ ] Backend logs show incoming requests

---

## Next Steps

1. **Activate the integrated plugin**
2. **Map your vendors** - Ensure vendors in backend have `woo_vendor_id`
3. **Create a test order** - Watch logs and check stats endpoint
4. **Verify sync** - Check `http://13.201.101.182:8000/api/woocommerce/orders/stats`

