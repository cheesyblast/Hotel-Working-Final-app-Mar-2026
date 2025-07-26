#!/usr/bin/env python3
"""
Simple Booking Edit Bug Fix Verification Test
Tests the backend API directly to verify the booking edit functionality for checked-in bookings
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

def test_backend_booking_edit():
    """
    Test the backend booking edit functionality directly
    """
    print("\n📋 BACKEND BOOKING EDIT TEST")
    print("=" * 50)
    
    # Step 1: Create a test booking with future dates
    print("\n1. Creating a test booking...")
    
    booking_data = {
        "guest_name": "Backend Edit Test Guest",
        "guest_email": "backendtest@example.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "BACKEND123",
        "guest_country": "Test Country",
        "room_number": "101",
        "check_in_date": "2025-08-10",
        "check_out_date": "2025-08-11",
        "stay_type": "Night Stay",
        "booking_amount": 8500.0,
        "additional_notes": "Backend test booking for edit verification"
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
    
    # Step 2: Test editing the booking while it's still "Upcoming"
    print("\n2. Testing edit on 'Upcoming' booking (should work)...")
    
    edit_data = {
        "additional_notes": "Updated notes - testing edit on upcoming booking"
    }
    
    try:
        response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=edit_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            print("✅ Edit on 'Upcoming' booking successful")
        else:
            print(f"❌ Edit on 'Upcoming' booking failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Edit on 'Upcoming' booking failed - Exception: {e}")
        return False
    
    # Step 3: Check-in the booking
    print("\n3. Checking in the booking...")
    
    checkin_data = {
        "booking_id": booking_id,
        "advance_amount": 1000.0,
        "notes": "Backend test check-in",
        "payment_method": "Cash"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            checkin_result = response.json()
            customer_id = checkin_result.get("customer_id")
            print(f"✅ Booking checked in successfully")
            print(f"   Customer ID: {customer_id}")
        else:
            print(f"❌ Failed to check in booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to check in booking - Exception: {e}")
        return False
    
    # Step 4: Verify booking status is now 'Checked-in'
    print("\n4. Verifying booking status after check-in...")
    
    try:
        response = requests.get(f"{API_BASE}/bookings?search=Backend Edit Test Guest", headers=get_auth_headers())
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get("bookings", [])
            
            if bookings:
                test_booking = bookings[0]
                print(f"✅ Found booking with ID: {test_booking['id']}")
                print(f"   Current status: {test_booking['status']}")
                
                if test_booking['status'] == 'Checked-in':
                    print("✅ Booking status correctly updated to 'Checked-in'")
                else:
                    print(f"❌ Expected status 'Checked-in', got '{test_booking['status']}'")
                    return False
            else:
                print("❌ Could not find booking after check-in")
                return False
        else:
            print(f"❌ Failed to get bookings - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to verify booking status - Exception: {e}")
        return False
    
    # Step 5: Try to edit the checked-in booking (MAIN TEST)
    print("\n5. Testing edit on 'Checked-in' booking (should fail with proper error)...")
    
    edit_data = {
        "additional_notes": "Updated notes - testing edit on checked-in booking"
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
                print("✅ Backend correctly prevents editing checked-in bookings")
                return True
            else:
                print(f"❌ INCORRECT ERROR MESSAGE")
                print(f"Expected: {expected_message}")
                print(f"Got: {error_message}")
                return False
                
        elif response.status_code == 404:
            # This would indicate a bug where booking was not found
            error_data = response.json()
            error_message = error_data.get("detail", "")
            print(f"❌ BOOKING NOT FOUND ERROR: {error_message}")
            print("❌ This indicates a potential issue with booking lookup")
            return False
            
        else:
            print(f"❌ Unexpected response status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to test booking edit - Exception: {e}")
        return False

def main():
    """Run the backend booking edit test"""
    print("BACKEND BOOKING EDIT VERIFICATION")
    print("=" * 50)
    print("Testing backend API directly to verify booking edit functionality")
    print("Expected: Proper error message when trying to edit checked-in bookings")
    print()
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return False
    
    # Run the test
    test_passed = test_backend_booking_edit()
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKEND TEST SUMMARY")
    print("=" * 60)
    
    if test_passed:
        print("✅ BACKEND TEST PASSED!")
        print("✅ Backend correctly handles booking edit requests")
        print("✅ Proper error messages are returned for checked-in booking edits")
        print("\n🔍 CONCLUSION:")
        print("   The backend API is working correctly. If users are still seeing")
        print("   'booking not found' errors, the issue is likely in the frontend")
        print("   code where it might be using wrong booking IDs.")
        return True
    else:
        print("❌ BACKEND TEST FAILED!")
        print("❌ Backend booking edit functionality has issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)