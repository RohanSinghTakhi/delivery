<?php
/**
 * Plugin Name: WooCommerce Order Sync to MedEx
 * Description: Sync WooCommerce orders to MedEx delivery backend API.
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
 * Sync order to MedEx backend when order is created or updated
 */
add_action('woocommerce_thankyou', 'medex_sync_order', 10, 1);
add_action('woocommerce_order_status_changed', 'medex_sync_order_on_status_change', 10, 3);

function medex_sync_order($order_id) {
    if (!$order_id) return;
    
    $order = wc_get_order($order_id);
    if (!$order) return;

    // Get vendor ID (Dokan support)
    $vendor_id = null;
    if (function_exists('dokan_get_seller_id_by_order')) {
        $vendor_id = dokan_get_seller_id_by_order($order_id);
    } else {
        $vendor_id = get_post_field('post_author', $order_id);
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

    // Build order items array
    $items = [];
    foreach ($order->get_items() as $item_id => $item) {
        $product = $item->get_product();
        $items[] = [
            'sku' => $product ? $product->get_sku() : null,
            'name' => $item->get_name(),
            'quantity' => $item->get_quantity(),
            'price' => (float) $item->get_total()
        ];
    }

    // Prepare payload
    $payload = [
        'woo_order_id' => (string) $order_id,
        'woo_vendor_id' => $vendor_id ? (string) $vendor_id : null,
        'status' => $order->get_status(),
        'total' => (float) $order->get_total(),
        'customer_name' => $order->get_formatted_billing_full_name() ?: $order->get_billing_first_name() . ' ' . $order->get_billing_last_name(),
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

    // Log errors (optional)
    if (is_wp_error($response)) {
        error_log('MedEx sync error: ' . $response->get_error_message());
    } else {
        $status_code = wp_remote_retrieve_response_code($response);
        if ($status_code !== 200 && $status_code !== 201) {
            $body = wp_remote_retrieve_body($response);
            error_log('MedEx sync failed (HTTP ' . $status_code . '): ' . $body);
        }
    }
}

/**
 * Sync order status change to MedEx
 */
function medex_sync_order_on_status_change($order_id, $old_status, $new_status) {
    if (!$order_id) return;
    
    $order = wc_get_order($order_id);
    if (!$order) return;

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

    if (is_wp_error($response)) {
        error_log('MedEx status sync error: ' . $response->get_error_message());
    }
}

