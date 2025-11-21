<?php
/**
 * Plugin Name: WooCommerce Order Sync to MedEx (Integrated)
 * Description: Sync WooCommerce orders to MedEx delivery backend API - Integrated with existing webhook handler
 * Version: 1.0.0
 * Author: MedEx Team
 */

if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}

// Configuration - Update these values
if (!defined('WOOCOMMERCE_SYNC_SECRET')) {
    define('WOOCOMMERCE_SYNC_SECRET', 'my_super_secret_key_123'); // Must match backend WOOCOMMERCE_SYNC_SECRET
}

if (!defined('MEDEX_API_URL')) {
    define('MEDEX_API_URL', 'http://13.201.101.182:8000'); // Update to your AWS backend URL
}

/**
 * Sync order to MedEx backend
 * This function can be called from the existing webhook handler
 */
function medex_sync_order_to_backend($order_id, $vendor_id = null) {
    if (!$order_id) {
        error_log('[MedEx Sync] No order ID provided');
        return false;
    }
    
    $order = wc_get_order($order_id);
    if (!$order) {
        error_log('[MedEx Sync] Order not found: ' . $order_id);
        return false;
    }

    // Get vendor ID if not provided (use same logic as webhook handler)
    if (!$vendor_id) {
        // Try Dokan first
        if (function_exists('dokan_get_seller_id_by_order')) {
            $vendor_id = dokan_get_seller_id_by_order($order_id);
        } else {
            // Fallback: get from order items (same as webhook handler)
            foreach ($order->get_items() as $item) {
                $product = $item->get_product();
                if ($product) {
                    $item_vendor_id = $product->get_meta('_vendor_id');
                    if (!$item_vendor_id) {
                        $item_vendor_id = get_post_field('post_author', $product->get_id());
                    }
                    if ($item_vendor_id) {
                        $vendor_id = $item_vendor_id;
                        break;
                    }
                }
            }
            
            // Final fallback
            if (!$vendor_id) {
                $vendor_id = get_post_field('post_author', $order_id);
            }
        }
    }

    if (!$vendor_id) {
        error_log('[MedEx Sync] No vendor ID found for order: ' . $order_id);
        return false;
    }

    // Get store/vendor address for pickup (if available)
    $pickup_address = '';
    if ($vendor_id && function_exists('dokan_get_store_info')) {
        $store_info = dokan_get_store_info($vendor_id);
        if (!empty($store_info['address'])) {
            $addr = $store_info['address'];
            $pickup_address = sprintf(
                '%s, %s, %s %s',
                $addr['street_1'] ?? '',
                $addr['city'] ?? '',
                $addr['state'] ?? '',
                $addr['zip'] ?? ''
            );
        }
    }
    
    // Fallback to store address or shipping address
    if (empty($pickup_address)) {
        $pickup_address = $order->get_shipping_address_1() . ', ' . $order->get_shipping_city();
    }

    // Build order items array (only for this vendor)
    $items = [];
    $vendor_total = 0;
    foreach ($order->get_items() as $item_id => $item) {
        $product = $item->get_product();
        if ($product) {
            $item_vendor_id = $product->get_meta('_vendor_id');
            if (!$item_vendor_id) {
                $item_vendor_id = get_post_field('post_author', $product->get_id());
            }
            
            // Only include items for this vendor
            if ($item_vendor_id == $vendor_id) {
                $item_total = (float) $item->get_total();
                $vendor_total += $item_total;
                
                $items[] = [
                    'sku' => $product ? $product->get_sku() : null,
                    'name' => $item->get_name(),
                    'quantity' => $item->get_quantity(),
                    'price' => $item_total
                ];
            }
        }
    }

    // If no items for this vendor, skip sync
    if (empty($items)) {
        error_log('[MedEx Sync] No items found for vendor ' . $vendor_id . ' in order: ' . $order_id);
        return false;
    }

    // Get customer shop details (same as webhook handler)
    $customer_id = $order->get_customer_id();
    $customer_name = trim($order->get_billing_first_name() . ' ' . $order->get_billing_last_name());
    
    // Prepare payload
    $payload = [
        'woo_order_id' => (string) $order_id,
        'woo_vendor_id' => (string) $vendor_id,
        'status' => $order->get_status(),
        'total' => (float) $vendor_total,
        'customer_name' => $customer_name ?: 'Customer',
        'customer_phone' => $order->get_billing_phone(),
        'pickup_address' => trim($pickup_address),
        'pickup_latitude' => null, // Optional: geocode if needed
        'pickup_longitude' => null,
        'delivery_address' => $order->get_formatted_shipping_address() ?: $order->get_shipping_address_1() . ', ' . $order->get_shipping_city(),
        'delivery_latitude' => null, // Optional: geocode if needed
        'delivery_longitude' => null,
        'items' => $items,
        'notes' => $order->get_customer_note()
    ];

    // Send to MedEx backend
    $response = wp_remote_post(MEDEX_API_URL . '/api/woocommerce/orders/sync', [
        'headers' => [
            'Content-Type' => 'application/json',
            'X-WC-Secret' => WOOCOMMERCE_SYNC_SECRET,
        ],
        'body' => json_encode($payload),
        'timeout' => 10,
    ]);

    // Enhanced logging for debugging
    if (is_wp_error($response)) {
        error_log('[MedEx Sync] ERROR for order #' . $order_id . ' (vendor: ' . $vendor_id . '): ' . $response->get_error_message());
        return false;
    } else {
        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        
        if ($status_code === 200 || $status_code === 201) {
            // Success - log for verification
            error_log('[MedEx Sync] SUCCESS for order #' . $order_id . ' (vendor: ' . $vendor_id . ') - HTTP ' . $status_code);
            $response_data = json_decode($body, true);
            if ($response_data && isset($response_data['id'])) {
                error_log('[MedEx Sync] Order synced with MedEx ID: ' . $response_data['id']);
            }
            return true;
        } else {
            // Error - log details
            error_log('[MedEx Sync] FAILED for order #' . $order_id . ' (vendor: ' . $vendor_id . ') - HTTP ' . $status_code . ': ' . $body);
            return false;
        }
    }
}

/**
 * Sync order status change to MedEx
 */
function medex_sync_order_status($order_id, $new_status) {
    if (!$order_id) return false;
    
    $order = wc_get_order($order_id);
    if (!$order) return false;

    // Send status update to MedEx
    $response = wp_remote_request(
        MEDEX_API_URL . '/api/woocommerce/orders/' . $order_id . '/status',
        [
            'method' => 'PATCH',
            'headers' => [
                'Content-Type' => 'application/json',
                'X-WC-Secret' => WOOCOMMERCE_SYNC_SECRET,
            ],
            'body' => json_encode(['status' => $new_status]),
            'timeout' => 10,
        ]
    );

    // Enhanced logging for status updates
    if (is_wp_error($response)) {
        error_log('[MedEx Sync] Status update ERROR for order #' . $order_id . ': ' . $response->get_error_message());
        return false;
    } else {
        $status_code = wp_remote_retrieve_response_code($response);
        if ($status_code === 200 || $status_code === 204) {
            error_log('[MedEx Sync] Status updated for order #' . $order_id . ': ' . $new_status);
            return true;
        } else {
            $body = wp_remote_retrieve_body($response);
            error_log('[MedEx Sync] Status update FAILED for order #' . $order_id . ' (HTTP ' . $status_code . '): ' . $body);
            return false;
        }
    }
}

/**
 * Hook into WooCommerce order events
 * These hooks will work alongside the existing webhook handler
 */
add_action('woocommerce_new_order', 'medex_sync_on_new_order', 20, 1);
add_action('woocommerce_order_status_changed', 'medex_sync_on_status_change', 20, 4);
add_action('woocommerce_thankyou', 'medex_sync_on_thankyou', 20, 1);

/**
 * Sync when new order is created (same hook as webhook handler)
 */
function medex_sync_on_new_order($order_id) {
    error_log('[MedEx Sync] New order hook triggered: ' . $order_id);
    
    $order = wc_get_order($order_id);
    if (!$order) return;
    
    // Get vendor IDs from order (same logic as webhook handler)
    $vendor_ids = medex_get_vendor_ids_from_order($order);
    
    // Sync for each vendor
    foreach ($vendor_ids as $vendor_id) {
        medex_sync_order_to_backend($order_id, $vendor_id);
    }
}

/**
 * Sync when order status changes
 */
function medex_sync_on_status_change($order_id, $old_status, $new_status, $order) {
    error_log('[MedEx Sync] Status change hook triggered: ' . $order_id . ' - ' . $old_status . ' → ' . $new_status);
    
    // Sync status update
    medex_sync_order_status($order_id, $new_status);
    
    // Also re-sync full order to ensure data is up to date
    if (!$order) {
        $order = wc_get_order($order_id);
    }
    if ($order) {
        $vendor_ids = medex_get_vendor_ids_from_order($order);
        foreach ($vendor_ids as $vendor_id) {
            medex_sync_order_to_backend($order_id, $vendor_id);
        }
    }
}

/**
 * Sync on thankyou page (backup hook)
 */
function medex_sync_on_thankyou($order_id) {
    error_log('[MedEx Sync] Thankyou hook triggered: ' . $order_id);
    
    $order = wc_get_order($order_id);
    if (!$order) return;
    
    $vendor_ids = medex_get_vendor_ids_from_order($order);
    foreach ($vendor_ids as $vendor_id) {
        medex_sync_order_to_backend($order_id, $vendor_id);
    }
}

/**
 * Get vendor IDs from order (same logic as webhook handler)
 */
function medex_get_vendor_ids_from_order($order) {
    $vendor_ids = [];
    
    foreach ($order->get_items() as $item) {
        $product = $item->get_product();
        if ($product) {
            $vendor_id = $product->get_meta('_vendor_id');
            if (!$vendor_id) {
                // Fallback: get author of the product
                $vendor_id = get_post_field('post_author', $product->get_id());
            }
            
            if ($vendor_id && !in_array($vendor_id, $vendor_ids)) {
                $vendor_ids[] = $vendor_id;
            }
        }
    }
    
    // If no vendor found, use order author or default
    if (empty($vendor_ids)) {
        $vendor_ids[] = $order->get_customer_id() ?: 1;
    }
    
    return $vendor_ids;
}

/**
 * Function that can be called directly from webhook handler
 * Add this call in your Webhook_Handler class methods
 */
function medex_sync_from_webhook_handler($order_id, $vendor_id) {
    return medex_sync_order_to_backend($order_id, $vendor_id);
}

