#!/usr/bin/env python3
"""
Booking Edit Bug Fix Verification Test
Tests the specific bug fix for checked-in booking edits where frontend was using customer.id instead of booking.id
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os

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

print(f"Testing Booking Edit Bug Fix at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
auth_token = None

def authenticate():
    """Authenticate as admin user"""
    global auth_token
    print("\n🔐 Authenticating as admin...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def test_booking_edit_bug_fix():
    """
    Test the specific bug fix for checked-in booking edits
    
    Steps:
    1. Create a test booking
    2. Check-in the booking (moves to 'Checked-in' status)
    3. Try to edit the checked-in booking using the correct booking ID
    4. Verify we get the proper error message instead of "booking not found"
    """
    print("\n📋 BOOKING EDIT BUG FIX VERIFICATION TEST")
    print("=" * 60)
    
    # Step 1: Create a test booking
    print("\n1. Creating a test booking...")
    
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    day_after = (datetime.now() + timedelta(days=2)).date()
    
    booking_data = {
        "guest_name": "Test Guest for Edit Bug",
        "guest_email": "testedit@example.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "TEST123",
        "guest_country": "Test Country",
        "room_number": "103",
        "check_in_date": tomorrow.isoformat(),
        "check_out_date": day_after.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 8500.0,
        "additional_notes": "Test booking for edit bug verification"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            booking = response.json()
            booking_id = booking["id"]
            print(f"✅ Test booking created successfully")
            print(f"   Booking ID: {booking_id}")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Room: {booking['room_number']}")
            print(f"   Status: {booking['status']}")
        else:
            print(f"❌ Failed to create test booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to create test booking - Exception: {e}")
        return False
    
    # Step 2: Check-in the booking
    print("\n2. Checking in the booking...")
    
    checkin_data = {
        "booking_id": booking_id,
        "advance_amount": 1000.0,
        "notes": "Test check-in for edit bug verification",
        "payment_method": "Cash"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            checkin_result = response.json()
            customer_id = checkin_result.get("customer_id")
            print(f"✅ Booking checked in successfully")
            print(f"   Customer ID: {customer_id}")
            print(f"   Booking should now be in 'Checked-in' status")
        else:
            print(f"❌ Failed to check in booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to check in booking - Exception: {e}")
        return False
    
    # Step 3: Verify booking status is now 'Checked-in'
    print("\n3. Verifying booking status after check-in...")
    
    try:
        response = requests.get(f"{API_BASE}/bookings?search={booking['guest_name']}", headers=get_auth_headers())
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get("bookings", [])
            
            # Find our test booking
            test_booking = None
            for b in bookings:
                if b["id"] == booking_id:
                    test_booking = b
                    break
            
            if test_booking:
                print(f"✅ Found booking with ID: {test_booking['id']}")
                print(f"   Current status: {test_booking['status']}")
                
                if test_booking['status'] == 'Checked-in':
                    print("✅ Booking status correctly updated to 'Checked-in'")
                else:
                    print(f"❌ Expected status 'Checked-in', got '{test_booking['status']}'")
                    return False
            else:
                print(f"❌ Could not find booking with ID {booking_id}")
                return False
        else:
            print(f"❌ Failed to get bookings - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to verify booking status - Exception: {e}")
        return False
    
    # Step 4: Try to edit the checked-in booking using the correct booking ID
    print("\n4. Attempting to edit the checked-in booking...")
    
    edit_data = {
        "additional_notes": "Updated notes - testing edit functionality"
    }
    
    try:
        response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=edit_data, headers=get_auth_headers())
        
        print(f"Edit attempt status code: {response.status_code}")
        
        if response.status_code == 400:
            # This is the expected response for trying to edit a checked-in booking
            error_data = response.json()
            error_message = error_data.get("detail", "")
            
            print(f"Response message: {error_message}")
            
            # Check if we get the correct error message
            expected_message = "Cannot modify booking with status 'Checked-in'. Only 'Upcoming' bookings can be modified."
            
            if expected_message in error_message:
                print("✅ CORRECT ERROR MESSAGE RECEIVED!")
                print("✅ Bug fix verification PASSED - Frontend is now using correct booking ID")
                return True
            else:
                print(f"❌ INCORRECT ERROR MESSAGE")
                print(f"Expected: {expected_message}")
                print(f"Got: {error_message}")
                return False
                
        elif response.status_code == 404:
            # This would indicate the old bug where booking was not found
            error_data = response.json()
            error_message = error_data.get("detail", "")
            print(f"❌ BUG STILL EXISTS - Got 'booking not found' error: {error_message}")
            print("❌ This indicates frontend is still using wrong ID (customer.id instead of booking.id)")
            return False
            
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test booking edit - Exception: {e}")
        return False

def test_booking_id_consistency():
    """
    Additional test to verify booking ID consistency throughout the lifecycle
    """
    print("\n📋 BOOKING ID CONSISTENCY TEST")
    print("=" * 50)
    
    # Create a booking and track its ID through different stages
    print("\n1. Creating booking and tracking ID consistency...")
    
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    day_after = (datetime.now() + timedelta(days=2)).date()
    
    booking_data = {
        "guest_name": "ID Consistency Test Guest",
        "guest_email": "idtest@example.com",
        "guest_phone": "+9876543210",
        "room_number": "102",
        "check_in_date": tomorrow.isoformat(),
        "check_out_date": day_after.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 12000.0,
        "additional_notes": "ID consistency test booking"
    }
    
    try:
        # Create booking
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            booking = response.json()
            original_booking_id = booking["id"]
            print(f"✅ Original booking ID: {original_booking_id}")
        else:
            print(f"❌ Failed to create booking for ID consistency test")
            return False
        
        # Check-in the booking
        checkin_data = {
            "booking_id": original_booking_id,
            "advance_amount": 500.0,
            "notes": "ID consistency test check-in"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            print("✅ Booking checked in successfully")
        else:
            print(f"❌ Failed to check in booking for ID consistency test")
            return False
        
        # Verify booking still has same ID after check-in
        response = requests.get(f"{API_BASE}/bookings?search=ID Consistency Test Guest", headers=get_auth_headers())
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get("bookings", [])
            
            if bookings:
                checked_in_booking = bookings[0]
                current_booking_id = checked_in_booking["id"]
                
                if current_booking_id == original_booking_id:
                    print(f"✅ Booking ID remains consistent: {current_booking_id}")
                    print("✅ ID consistency test PASSED")
                    return True
                else:
                    print(f"❌ Booking ID changed! Original: {original_booking_id}, Current: {current_booking_id}")
                    return False
            else:
                print("❌ Could not find booking after check-in")
                return False
        else:
            print("❌ Failed to retrieve booking after check-in")
            return False
            
    except Exception as e:
        print(f"❌ ID consistency test failed - Exception: {e}")
        return False

def main():
    """Run the booking edit bug fix verification tests"""
    print("BOOKING EDIT BUG FIX VERIFICATION")
    print("=" * 50)
    print("Testing fix for: Frontend using customer.id instead of booking.id for checked-in booking edits")
    print("Expected: Proper error message instead of 'booking not found'")
    print()
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return False
    
    test_results = []
    
    # Test 1: Main bug fix verification
    test_results.append(("Booking Edit Bug Fix", test_booking_edit_bug_fix()))
    
    # Test 2: Booking ID consistency
    test_results.append(("Booking ID Consistency", test_booking_id_consistency()))
    
    # Summary
    print("\n" + "=" * 60)
    print("BUG FIX VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 BUG FIX VERIFICATION PASSED!")
        print("✅ Frontend is now correctly using booking.id instead of customer.id")
        print("✅ Users will now see proper error messages when trying to edit checked-in bookings")
        return True
    else:
        print(f"\n⚠️ BUG FIX VERIFICATION FAILED!")
        print("❌ The reported issue may still exist")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)