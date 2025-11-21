# WordPress Compatibility Guide

This guide explains how the MedEx backend integrates with your existing WooCommerce/Dokan installation so you can keep the WordPress vendor workflows unchanged while syncing everything into the AWS backend.

---

## 1. Overview

- **WooCommerce remains the source of truth** for vendor logins, storefront orders, billing, and email/SMS notifications.
- **MedEx FastAPI backend** stores mirrored copies of orders, drivers, and vendors so the mobile apps, live tracking, and analytics work without touching WordPress directly.
- A **secure sync layer** (new `/api/woocommerce/*` endpoints) accepts payloads from your WordPress plugin, translates status values, and keeps both systems in sync.

---

## 2. Environment Variables

Add these keys to `backend/.env` (or AWS secrets):

```
WOOCOMMERCE_SYNC_SECRET="super-secret-shared-key"
WORDPRESS_DOMAIN="https://embolo.in"
WOOCOMMERCE_BASE_URL="https://embolo.in"
```

**Important:** 
- `WOOCOMMERCE_SYNC_SECRET` must match the value in your WordPress plugin (`WOOCOMMERCE_SYNC_SECRET` constant).
- This secret is required in the `X-WC-Secret` header from WordPress so only your plugin can call the sync endpoints.
- `WORDPRESS_DOMAIN` is used for CORS and future callback integrations.

---

## 3. Data Model Additions

Orders now store:

- `woo_order_id`
- `woo_vendor_id`
- `woo_status`
- `source` (`medex` | `woocommerce`)

Vendors include `woo_vendor_id` so we can locate the correct MedEx vendor account when a WooCommerce payload arrives.

---

## 4. Sync Endpoints

### 4.1 Upsert/Sync Order

```
POST /api/woocommerce/orders/sync
Headers: X-WC-Secret: <WOOCOMMERCE_SYNC_SECRET>
```

Body:
```json
{
  "woo_order_id": "12345",
  "woo_vendor_id": "88",
  "status": "processing",
  "customer_name": "John Doe",
  "customer_phone": "+1 222 333 4444",
  "pickup_address": "...",
  "pickup_latitude": 12.97,
  "pickup_longitude": 77.59,
  "delivery_address": "...",
  "delivery_latitude": 12.99,
  "delivery_longitude": 77.63,
  "items": [
    { "sku": "SKU-1", "name": "Medicine A", "quantity": 2 }
  ]
}
```

Behavior:
- If `woo_order_id` already exists, the order is updated.
- Otherwise a new MedEx order is created with `source="woocommerce"`.
- Status is translated automatically:
  - `pending` → `pending`
  - `processing` → `accepted`
  - `driver-assigned` → `driver_assigned`
  - `picked-up` → `picked_up`
  - `out-for-delivery` → `out_for_delivery`
  - `completed/delivered` → `delivered`
  - `cancelled/failed` → `cancelled`

### 4.2 Status Update

```
PATCH /api/woocommerce/orders/{woo_order_id}/status
Headers: X-WC-Secret: <WOOCOMMERCE_SYNC_SECRET>
Body: { "status": "completed" }
```

This lets you drive status changes from WooCommerce (e.g., when the vendor updates the order in the WordPress dashboard).

---

## 5. Workflow

1. **Order placed in WooCommerce**
   - Plugin hooks into `woocommerce_thankyou` (or existing hook) and POSTs to `/api/woocommerce/orders/sync`.
2. **Vendor dashboard assigns driver (WordPress)**
   - Plugin POSTs to `/api/woocommerce/orders/sync` to update `driver_id` or calls `/api/orders/{id}/assign` if MedEx driver IDs are available.
3. **Driver/mobile apps update live status**
   - No change: the mobile apps talk to `/api/orders/*` and `/api/drivers/*`.
   - When a driver status change should reflect in WooCommerce, the backend can call back to the WP REST API (optional future step).
4. **Vendor changes status in WooCommerce**
   - Plugin calls `/api/woocommerce/orders/{woo_order_id}/status` so MedEx stays aligned.

---

## 6. Frontend (User/Vendor Apps)

The React “user app” now exposes helper functions to trigger WooCommerce sync flows:

```ts
import { woo } from '@/services/api';

woo.syncOrder(payload, secret); // calls /api/woocommerce/orders/sync
woo.updateStatus(wooOrderId, status, secret);
```

These helpers are meant for server-side plugin code or trusted Electron builds—never expose the secret key in the public web app.

---

## 7. WordPress Plugin Installation

A complete, production-ready plugin is provided in `wordpress-plugin-woocommerce-sync.php`.

### Installation Steps:

1. **Copy the plugin file** to your WordPress `wp-content/plugins/` directory:
   ```bash
   cp wordpress-plugin-woocommerce-sync.php /path/to/wordpress/wp-content/plugins/
   ```

2. **Update configuration constants** in the plugin file:
   - `WOOCOMMERCE_SYNC_SECRET`: Must match `WOOCOMMERCE_SYNC_SECRET` in your backend `.env`
   - `MEDEX_API_URL`: Set to your AWS backend URL (e.g., `http://13.201.101.182:8000`)

3. **Activate the plugin** in WordPress Admin → Plugins

4. **Test the sync** by creating a test order in WooCommerce and checking the backend logs

### Plugin Features:

- ✅ Automatically syncs orders when created (`woocommerce_thankyou` hook)
- ✅ Syncs status changes when order status updates in WooCommerce
- ✅ Supports Dokan multi-vendor (extracts vendor ID automatically)
- ✅ Includes order items, customer details, addresses
- ✅ Handles pickup address (uses vendor store address or falls back to shipping address)
- ✅ Error logging for debugging
- ✅ Secure authentication via `X-WC-Secret` header

### Fixes Applied:

The original plugin code had these issues that are now fixed:
- ❌ Missing `pickup_address` field (now included with vendor/store address fallback)
- ❌ Typo in secret constant (`WOOCOMMERCE_SYNC_SECRET20058847` → fixed)
- ❌ Missing order items array (now included)
- ❌ No status change sync (now included)
- ✅ Backend updated to make `pickup_address` optional with smart fallback

---

## 8. Next Steps

1. ✅ **Plugin is ready** - Install and configure the provided WordPress plugin
2. Store `woo_vendor_id` on MedEx vendor documents (one-time migration) so vendor lookups work correctly
3. Optional: add callbacks from MedEx to WooCommerce if you want mobile app status changes to appear in the WordPress dashboard automatically

With these additions, you can keep the entire WordPress workflow intact while leveraging the AWS backend for real-time logistics. Already-built mobile and vendor apps only need to know the MedEx order IDs, while the sync layer keeps everything matched to WooCommerce IDs behind the scenes.

