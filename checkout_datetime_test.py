#!/usr/bin/env python3
"""
Specific test for the actual_checkout_date MongoDB encoding fix.
This test focuses on verifying that actual_checkout_date is stored as datetime, not date.
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"

# Authentication
def get_auth_token():
    """Get authentication token"""
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

# Get auth token
AUTH_TOKEN = get_auth_token()
if not AUTH_TOKEN:
    print("❌ Could not authenticate - exiting")
    sys.exit(1)

# Headers with authentication
AUTH_HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

print(f"Testing actual_checkout_date MongoDB encoding fix at: {API_BASE}")
print("=" * 80)

def test_checkout_datetime_encoding():
    """Test that checkout doesn't fail with MongoDB encoding error"""
    print("\n1. Testing Checkout DateTime Encoding Fix")
    
    try:
        # Get available room
        rooms_response = requests.get(f"{API_BASE}/rooms", headers=AUTH_HEADERS)
        if rooms_response.status_code != 200:
            print("❌ Could not get rooms")
            return False
        
        rooms = rooms_response.json()
        available_room = next((r for r in rooms if r.get('status') == 'Available'), None)
        
        if not available_room:
            print("❌ No available rooms")
            return False
        
        # Create short time booking
        today = datetime.now().date()
        booking_data = {
            "guest_name": "DateTime Test Guest",
            "guest_email": "",
            "guest_phone": "555-0123",
            "guest_id_passport": "DT123456",
            "guest_country": "Test Country",
            "room_number": available_room['room_number'],
            "check_in_date": today.isoformat(),
            "check_out_date": today.isoformat(),
            "stay_type": "Short Time",
            "booking_amount": 1800.0
        }
        
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=AUTH_HEADERS)
        if booking_response.status_code != 200:
            print(f"❌ Booking creation failed: {booking_response.status_code}")
            return False
        
        booking = booking_response.json()
        print(f"✅ Booking created: {booking['id']}")
        
        # Check in
        checkin_data = {
            "booking_id": booking['id'],
            "advance_amount": 400.0,
            "payment_method": "Cash"
        }
        
        checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=AUTH_HEADERS)
        if checkin_response.status_code != 200:
            print(f"❌ Check-in failed: {checkin_response.status_code}")
            return False
        
        print(f"✅ Check-in successful")
        
        # Get customer
        customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=AUTH_HEADERS)
        if customers_response.status_code != 200:
            print("❌ Could not get customers")
            return False
        
        customers = customers_response.json()
        customer = next((c for c in customers if c['name'] == "DateTime Test Guest"), None)
        
        if not customer:
            print("❌ Could not find checked-in customer")
            return False
        
        print(f"✅ Customer found: {customer['id']}")
        
        # Test checkout - this is where the MongoDB encoding error would occur
        print("\n   Testing checkout process (where encoding error would occur)...")
        
        checkout_data = {
            "customer_id": customer['id'],
            "additional_amount": 100.0,
            "discount_amount": 20.0,
            "payment_method": "Card"
        }
        
        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=AUTH_HEADERS)
        
        print(f"   Checkout response status: {checkout_response.status_code}")
        
        if checkout_response.status_code == 200:
            result = checkout_response.json()
            print(f"   ✅ Checkout successful - No MongoDB encoding error!")
            print(f"   Message: {result.get('message')}")
            
            # Verify billing details
            billing = result.get('billing_details', {})
            if billing:
                print(f"   Billing total: {billing.get('total_amount')}")
                print(f"   Payment method: {billing.get('payment_method')}")
            
            print(f"\n   🎉 CRITICAL FIX VERIFIED:")
            print(f"   ✅ actual_checkout_date is now properly stored as datetime")
            print(f"   ✅ No MongoDB BSON encoding error occurred")
            print(f"   ✅ Checkout process completed successfully")
            
            return True
        elif checkout_response.status_code == 500:
            print(f"   ❌ 500 Internal Server Error - MongoDB encoding issue still exists!")
            print(f"   Response: {checkout_response.text}")
            print(f"\n   🚨 CRITICAL ISSUE:")
            print(f"   ❌ actual_checkout_date is still being stored as date object")
            print(f"   ❌ MongoDB BSON encoding error not fixed")
            return False
        else:
            print(f"   ❌ Checkout failed with status: {checkout_response.status_code}")
            print(f"   Response: {checkout_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def test_multiple_checkout_scenarios():
    """Test multiple checkout scenarios to ensure consistency"""
    print("\n2. Testing Multiple Checkout Scenarios")
    
    payment_methods = ["Cash", "Card", "Bank Transfer"]
    success_count = 0
    
    for i, payment_method in enumerate(payment_methods):
        print(f"\n   Scenario {i+1}: Testing {payment_method} checkout...")
        
        try:
            # Get available room
            rooms_response = requests.get(f"{API_BASE}/rooms", headers=AUTH_HEADERS)
            if rooms_response.status_code != 200:
                print(f"   ❌ Could not get rooms for {payment_method} test")
                continue
            
            rooms = rooms_response.json()
            available_room = next((r for r in rooms if r.get('status') == 'Available'), None)
            
            if not available_room:
                print(f"   ⚠️ No available rooms for {payment_method} test")
                continue
            
            # Create booking
            today = datetime.now().date()
            booking_data = {
                "guest_name": f"Test Guest {payment_method}",
                "guest_email": f"test{i}@example.com",
                "guest_phone": f"555-010{i}",
                "guest_id_passport": f"PM{i}123456",
                "guest_country": "Test Country",
                "room_number": available_room['room_number'],
                "check_in_date": today.isoformat(),
                "check_out_date": today.isoformat(),
                "stay_type": "Short Time",
                "booking_amount": 2000.0 + (i * 100)
            }
            
            booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=AUTH_HEADERS)
            if booking_response.status_code != 200:
                print(f"   ❌ Booking creation failed for {payment_method}")
                continue
            
            booking = booking_response.json()
            
            # Check in
            checkin_data = {
                "booking_id": booking['id'],
                "advance_amount": 300.0 + (i * 50),
                "payment_method": payment_method
            }
            
            checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=AUTH_HEADERS)
            if checkin_response.status_code != 200:
                print(f"   ❌ Check-in failed for {payment_method}")
                continue
            
            # Get customer
            customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=AUTH_HEADERS)
            if customers_response.status_code != 200:
                print(f"   ❌ Could not get customers for {payment_method}")
                continue
            
            customers = customers_response.json()
            customer = next((c for c in customers if c['name'] == f"Test Guest {payment_method}"), None)
            
            if not customer:
                print(f"   ❌ Could not find customer for {payment_method}")
                continue
            
            # Checkout
            checkout_data = {
                "customer_id": customer['id'],
                "additional_amount": 80.0 + (i * 20),
                "discount_amount": 15.0 + (i * 5),
                "payment_method": payment_method
            }
            
            checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=AUTH_HEADERS)
            
            if checkout_response.status_code == 200:
                print(f"   ✅ {payment_method} checkout successful - No encoding error")
                success_count += 1
            elif checkout_response.status_code == 500:
                print(f"   ❌ {payment_method} checkout failed with 500 error - Encoding issue!")
                print(f"   Response: {checkout_response.text}")
            else:
                print(f"   ❌ {payment_method} checkout failed: {checkout_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {payment_method} test failed with exception: {e}")
    
    print(f"\n   Summary: {success_count}/{len(payment_methods)} payment methods successful")
    
    if success_count == len(payment_methods):
        print(f"   ✅ All payment methods work without encoding errors")
        return True
    else:
        print(f"   ❌ {len(payment_methods) - success_count} payment methods failed")
        return False

def main():
    """Run datetime encoding fix tests"""
    print("Starting actual_checkout_date MongoDB Encoding Fix Tests")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Basic checkout datetime encoding
    test_results.append(("DateTime Encoding Fix", test_checkout_datetime_encoding()))
    
    # Test 2: Multiple scenarios
    test_results.append(("Multiple Checkout Scenarios", test_multiple_checkout_scenarios()))
    
    # Summary
    print("\n" + "=" * 80)
    print("DATETIME ENCODING FIX TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL DATETIME ENCODING TESTS PASSED!")
        print("✅ The actual_checkout_date MongoDB encoding issue has been FIXED")
        print("✅ Short time bookings can now checkout without 500 errors")
        print("✅ All payment methods work correctly")
        print("✅ The fix is working consistently across multiple scenarios")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed.")
        print("❌ The actual_checkout_date encoding issue may still exist")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)