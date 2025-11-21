#!/usr/bin/env python3
"""
Test script to verify WordPress order sync is working
Run this script to check if orders are being synced from WordPress
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "http://13.201.101.182:8000"
WC_SECRET = "my_super_secret_key_123"  # Must match plugin secret

def test_sync_endpoint():
    """Test the sync endpoint with a sample order"""
    print("=" * 60)
    print("Testing WooCommerce Sync Endpoint")
    print("=" * 60)
    
    test_payload = {
        "woo_order_id": f"TEST_{int(datetime.now().timestamp())}",
        "woo_vendor_id": "1",  # Update with your vendor ID
        "status": "pending",
        "total": 150.00,
        "customer_name": "Test Customer",
        "customer_phone": "1234567890",
        "pickup_address": "123 Store Street, Test City",
        "delivery_address": "456 Customer Avenue, Test City",
        "items": [
            {
                "name": "Test Product",
                "quantity": 1,
                "price": 150.00
            }
        ],
        "notes": "This is a test order from sync verification script"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/woocommerce/orders/sync",
            json=test_payload,
            headers={
                "Content-Type": "application/json",
                "X-WC-Secret": WC_SECRET
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code in [200, 201]:
            print("\n✅ Sync endpoint is working!")
            return True
        else:
            print(f"\n❌ Sync failed: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to backend at {BACKEND_URL}")
        print("   Make sure the backend server is running")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def check_synced_orders():
    """Check for orders synced from WooCommerce"""
    print("\n" + "=" * 60)
    print("Checking for Synced Orders")
    print("=" * 60)
    
    try:
        # Note: This requires authentication token
        # For now, we'll just check if endpoint exists
        response = requests.get(
            f"{BACKEND_URL}/api/health",
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Backend is accessible")
            print(f"   Health: {response.json()}")
        else:
            print(f"⚠️  Backend responded with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False
    
    return True

def check_backend_health():
    """Check if backend is running"""
    print("\n" + "=" * 60)
    print("Checking Backend Health")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/health",
            timeout=5
        )
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Backend Status: {health.get('status', 'unknown')}")
            print(f"   Database: {health.get('database', 'unknown')}")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BACKEND_URL}")
        print("   Make sure backend is running and accessible")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("WordPress Order Sync Verification")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Secret: {WC_SECRET[:10]}...")
    print()
    
    # Step 1: Check backend health
    if not check_backend_health():
        print("\n❌ Backend is not accessible. Please start the backend server.")
        sys.exit(1)
    
    # Step 2: Test sync endpoint
    sync_works = test_sync_endpoint()
    
    # Step 3: Check for existing synced orders
    check_synced_orders()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    if sync_works:
        print("✅ Sync endpoint is working correctly!")
        print("\nNext steps:")
        print("1. Create a test order in WordPress")
        print("2. Check WordPress error logs for sync messages")
        print("3. Query backend API to verify order was synced")
    else:
        print("❌ Sync endpoint test failed")
        print("\nTroubleshooting:")
        print("1. Verify WOOCOMMERCE_SYNC_SECRET matches in both plugin and backend")
        print("2. Check backend logs for errors")
        print("3. Ensure vendor exists in backend with matching woo_vendor_id")
    
    print()

if __name__ == "__main__":
    main()

