#!/usr/bin/env python3
"""
Comprehensive Booking ID Persistence Test
Tests if booking IDs remain consistent throughout the booking lifecycle.
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

print(f"Testing Booking ID Persistence at: {API_BASE}")
print("=" * 80)

# Global variables
auth_token = None
test_booking_id = None
test_room_number = "998"

def authenticate():
    """Authenticate as admin user"""
    print("\n🔐 Authenticating as admin user...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ Authentication successful")
                return f"Bearer {token}"
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Authentication failed - Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return None

def create_test_room():
    """Create a test room"""
    print(f"\n🏨 Creating test room {test_room_number}...")
    
    try:
        room_data = {
            "room_number": test_room_number,
            "room_type": "Double",
            "price_per_night": 8500.0,
            "max_occupancy": 2,
            "amenities": ["WiFi", "AC", "TV"]
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/rooms", json=room_data, headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Test room {test_room_number} created successfully")
            return True
        else:
            print(f"❌ Room creation failed - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Room creation failed - Exception: {e}")
        return False

def create_booking():
    """Create a test booking and track its ID"""
    print("\n📝 Creating test booking...")
    global test_booking_id
    
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        day_after = (datetime.now() + timedelta(days=2)).date()
        
        booking_data = {
            "guest_name": "Alice Johnson",
            "guest_email": "alice.johnson@example.com",
            "guest_phone": "+1987654321",
            "guest_id_passport": "P987654321",
            "guest_country": "Canada",
            "room_number": test_room_number,
            "check_in_date": tomorrow.isoformat(),
            "check_out_date": day_after.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 8500.0,
            "booking_channel_id": "",
            "booking_channel_name": "Direct",
            "additional_notes": "Test booking for ID persistence check",
            "booking_status": "Upcoming"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        
        if response.status_code == 200:
            booking = response.json()
            test_booking_id = booking.get("id")
            print(f"✅ Booking created successfully")
            print(f"   Original Booking ID: {test_booking_id}")
            print(f"   Guest: {booking.get('guest_name')}")
            print(f"   Room: {booking.get('room_number')}")
            print(f"   Status: {booking.get('status')}")
            return True
        else:
            print(f"❌ Booking creation failed - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Booking creation failed - Exception: {e}")
        return False

def verify_booking_id_after_creation():
    """Verify the booking can be found immediately after creation"""
    print(f"\n🔍 Verifying booking ID {test_booking_id} after creation...")
    
    try:
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            found_booking = None
            for booking in bookings:
                if booking.get("id") == test_booking_id:
                    found_booking = booking
                    break
            
            if found_booking:
                print(f"✅ Booking found after creation")
                print(f"   ID: {found_booking.get('id')}")
                print(f"   Status: {found_booking.get('status')}")
                return True
            else:
                print(f"❌ Booking not found after creation!")
                return False
        else:
            print(f"❌ Failed to get bookings - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Verification failed - Exception: {e}")
        return False

def edit_booking():
    """Edit the booking and verify ID remains the same"""
    print(f"\n✏️ Editing booking {test_booking_id}...")
    
    try:
        new_checkout = (datetime.now() + timedelta(days=3)).date()
        
        update_data = {
            "check_out_date": new_checkout.isoformat(),
            "additional_notes": "Updated during ID persistence test"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.put(f"{API_BASE}/bookings/{test_booking_id}", json=update_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Booking edit successful")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Booking edit failed - Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Booking edit failed - Exception: {e}")
        return False

def verify_booking_id_after_edit():
    """Verify the booking ID is still the same after edit"""
    print(f"\n🔍 Verifying booking ID {test_booking_id} after edit...")
    
    try:
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            found_booking = None
            for booking in bookings:
                if booking.get("id") == test_booking_id:
                    found_booking = booking
                    break
            
            if found_booking:
                print(f"✅ Booking found after edit")
                print(f"   ID: {found_booking.get('id')} (unchanged)")
                print(f"   Status: {found_booking.get('status')}")
                print(f"   Notes: {found_booking.get('additional_notes')}")
                return True
            else:
                print(f"❌ Booking not found after edit!")
                return False
        else:
            print(f"❌ Failed to get bookings - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Verification failed - Exception: {e}")
        return False

def checkin_booking():
    """Check-in the booking and verify ID persistence"""
    print(f"\n🏨 Checking in booking {test_booking_id}...")
    
    try:
        checkin_data = {
            "booking_id": test_booking_id,
            "advance_amount": 1500.0,
            "notes": "Test check-in for ID persistence",
            "payment_method": "Cash"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Check-in successful")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Check-in failed - Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Check-in failed - Exception: {e}")
        return False

def verify_booking_id_after_checkin():
    """Verify the booking ID is still the same after check-in"""
    print(f"\n🔍 Verifying booking ID {test_booking_id} after check-in...")
    
    try:
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            found_booking = None
            for booking in bookings:
                if booking.get("id") == test_booking_id:
                    found_booking = booking
                    break
            
            if found_booking:
                print(f"✅ Booking found after check-in")
                print(f"   ID: {found_booking.get('id')} (unchanged)")
                print(f"   Status: {found_booking.get('status')}")
                print(f"   Guest: {found_booking.get('guest_name')}")
                print(f"   Room: {found_booking.get('room_number')}")
                return True, found_booking
            else:
                print(f"❌ Booking not found after check-in!")
                print(f"   This could be the source of the 'booking not found' error!")
                
                # Let's see what bookings do exist
                print(f"\n   Available bookings:")
                for booking in bookings[:5]:
                    print(f"     ID: {booking.get('id')}, Guest: {booking.get('guest_name')}, Status: {booking.get('status')}")
                
                return False, None
        else:
            print(f"❌ Failed to get bookings - Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Verification failed - Exception: {e}")
        return False, None

def attempt_edit_after_checkin():
    """Attempt to edit the booking after check-in"""
    print(f"\n🚫 Attempting to edit booking {test_booking_id} after check-in...")
    
    try:
        update_data = {
            "additional_notes": "Trying to edit after check-in - should fail properly"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.put(f"{API_BASE}/bookings/{test_booking_id}", json=update_data, headers=headers)
        
        print(f"   Edit Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        if response.status_code == 404:
            print(f"❌ BUG CONFIRMED: Got 'booking not found' error")
            return False
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                if "Cannot modify booking" in error_detail:
                    print(f"✅ Proper error message received")
                    return True
                else:
                    print(f"❌ Wrong error message: {error_detail}")
                    return False
            except:
                print(f"❌ Could not parse error response")
                return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Edit attempt failed - Exception: {e}")
        return False

def main():
    """Run the comprehensive booking ID persistence test"""
    print("🔍 BOOKING ID PERSISTENCE TEST")
    print("=" * 50)
    print("Testing if booking IDs remain consistent throughout the booking lifecycle")
    print("=" * 50)
    
    global auth_token
    
    # Authenticate first
    auth_token = authenticate()
    if not auth_token:
        print("❌ Cannot proceed without authentication")
        return False
    
    test_results = []
    
    # Create test room
    test_results.append(("Create Test Room", create_test_room()))
    if not test_results[-1][1]:
        return False
    
    # Create booking
    test_results.append(("Create Booking", create_booking()))
    if not test_results[-1][1]:
        return False
    
    # Verify booking ID after creation
    test_results.append(("Verify ID After Creation", verify_booking_id_after_creation()))
    
    # Edit booking
    test_results.append(("Edit Booking", edit_booking()))
    
    # Verify booking ID after edit
    test_results.append(("Verify ID After Edit", verify_booking_id_after_edit()))
    
    # Check-in booking
    test_results.append(("Check-in Booking", checkin_booking()))
    
    # Verify booking ID after check-in (CRITICAL TEST)
    found_after_checkin, booking_data = verify_booking_id_after_checkin()
    test_results.append(("Verify ID After Check-in", found_after_checkin))
    
    # Attempt edit after check-in
    if found_after_checkin:
        test_results.append(("Edit After Check-in", attempt_edit_after_checkin()))
    else:
        print(f"\n❌ CRITICAL BUG FOUND: Booking disappears after check-in!")
        print(f"   This explains the 'booking not found' error reported by user")
        test_results.append(("Edit After Check-in", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("🔍 BOOKING ID PERSISTENCE TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    # Bug analysis
    print(f"\n🐛 BUG ANALYSIS:")
    if not found_after_checkin:
        print(f"❌ CRITICAL BUG CONFIRMED: Booking record disappears after check-in")
        print(f"   Root Cause: Booking ID not preserved during check-in process")
        print(f"   Impact: Edit attempts return 'booking not found' instead of proper error")
        print(f"   Original Booking ID: {test_booking_id}")
    else:
        print(f"✅ Booking ID persistence working correctly")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)