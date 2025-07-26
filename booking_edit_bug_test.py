#!/usr/bin/env python3
"""
Booking Edit Bug Investigation Test
Tests the specific scenario where editing a "Checked In" booking returns "booking not found" 
instead of proper error message.

User Scenario:
1. ✅ Create a booking (works)
2. ✅ Edit booking dates while it's "Upcoming" status (works - the previous fix is working)
3. ✅ Check-in the booking (moves to "Checked In" status)
4. ❌ Try to edit the booking again → Gets "booking not found" error instead of proper error message

Expected: "Cannot modify booking with status 'Checked In'. Only 'Upcoming' bookings can be modified."
Actual: "booking not found" error
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

print(f"Testing Booking Edit Bug at: {API_BASE}")
print("=" * 80)

# Global variables to store test data
auth_token = None
test_booking_id = None
test_room_number = "101"

def authenticate():
    """Authenticate as admin user"""
    print("\n🔐 Authenticating as admin user...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")
        
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
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return None

def step0_create_test_room():
    """Step 0: Create a test room for our booking"""
    print("\n🏨 STEP 0: Creating a test room...")
    
    try:
        room_data = {
            "room_number": "999",
            "room_type": "Double",
            "price_per_night": 8500.0,
            "max_occupancy": 2,
            "amenities": ["WiFi", "AC", "TV"]
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/rooms", json=room_data, headers=headers)
        print(f"Create Room Status Code: {response.status_code}")
        
        if response.status_code == 200:
            room = response.json()
            print(f"✅ Test room created successfully")
            print(f"   Room Number: {room.get('room_number')}")
            print(f"   Room Type: {room.get('room_type')}")
            print(f"   Status: {room.get('status')}")
            return True
        else:
            print(f"❌ Room creation failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Room creation failed - Exception: {e}")
        return False

def step1_create_booking():
    """Step 1: Create a test booking"""
    print("\n📝 STEP 1: Creating a test booking...")
    global test_booking_id, test_room_number
    test_room_number = "999"  # Use our test room
    
    try:
        # Create booking for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        day_after = (datetime.now() + timedelta(days=2)).date()
        
        booking_data = {
            "guest_name": "John Smith",
            "guest_email": "john.smith@example.com",
            "guest_phone": "+1234567890",
            "guest_id_passport": "P123456789",
            "guest_country": "USA",
            "room_number": test_room_number,
            "check_in_date": tomorrow.isoformat(),
            "check_out_date": day_after.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 8500.0,
            "booking_channel_id": "",
            "booking_channel_name": "Direct",
            "additional_notes": "Test booking for bug investigation",
            "booking_status": "Upcoming"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        print(f"Create Booking Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            test_booking_id = booking.get("id")
            print(f"✅ Booking created successfully")
            print(f"   Booking ID: {test_booking_id}")
            print(f"   Guest: {booking.get('guest_name')}")
            print(f"   Room: {booking.get('room_number')}")
            print(f"   Status: {booking.get('status')}")
            print(f"   Check-in: {booking.get('check_in_date')}")
            print(f"   Check-out: {booking.get('check_out_date')}")
            return True
        else:
            print(f"❌ Booking creation failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Booking creation failed - Exception: {e}")
        return False

def step2_edit_upcoming_booking():
    """Step 2: Edit booking dates while it's "Upcoming" status (should work)"""
    print("\n✏️ STEP 2: Editing booking while 'Upcoming' status...")
    
    try:
        # Update check-out date to 3 days later
        new_checkout = (datetime.now() + timedelta(days=3)).date()
        
        update_data = {
            "check_out_date": new_checkout.isoformat(),
            "additional_notes": "Updated checkout date - test edit while upcoming"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.put(f"{API_BASE}/bookings/{test_booking_id}", json=update_data, headers=headers)
        print(f"Edit Upcoming Booking Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upcoming booking edit successful")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Upcoming booking edit failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upcoming booking edit failed - Exception: {e}")
        return False

def step3_checkin_booking():
    """Step 3: Check-in the booking (moves to "Checked In" status)"""
    print("\n🏨 STEP 3: Checking in the booking...")
    
    try:
        checkin_data = {
            "booking_id": test_booking_id,
            "advance_amount": 1000.0,
            "notes": "Test check-in for bug investigation",
            "payment_method": "Cash"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
        print(f"Check-in Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Check-in successful")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Check-in failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Check-in failed - Exception: {e}")
        return False

def step4_verify_booking_exists():
    """Step 4: Verify booking still exists and can be found after check-in"""
    print("\n🔍 STEP 4: Verifying booking exists after check-in...")
    
    try:
        # Get all bookings to find our test booking
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        print(f"Get Bookings Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            # Find our test booking
            test_booking = None
            for booking in bookings:
                if booking.get("id") == test_booking_id:
                    test_booking = booking
                    break
            
            if test_booking:
                print(f"✅ Booking found after check-in")
                print(f"   Booking ID: {test_booking.get('id')}")
                print(f"   Guest: {test_booking.get('guest_name')}")
                print(f"   Room: {test_booking.get('room_number')}")
                print(f"   Status: {test_booking.get('status')}")
                print(f"   Check-in: {test_booking.get('check_in_date')}")
                print(f"   Check-out: {test_booking.get('check_out_date')}")
                
                # Verify status is "Checked-in"
                if test_booking.get('status') == 'Checked-in':
                    print(f"✅ Booking status correctly updated to 'Checked-in'")
                    return True
                else:
                    print(f"❌ Booking status is '{test_booking.get('status')}', expected 'Checked-in'")
                    return False
            else:
                print(f"❌ Booking not found after check-in - This is the bug!")
                print(f"   Searched for booking ID: {test_booking_id}")
                print(f"   Total bookings found: {len(bookings)}")
                return False
        else:
            print(f"❌ Failed to get bookings - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Booking verification failed - Exception: {e}")
        return False

def step5_attempt_edit_checked_in():
    """Step 5: Try to edit the "Checked In" booking (this should fail with proper error message)"""
    print("\n🚫 STEP 5: Attempting to edit 'Checked In' booking...")
    
    try:
        # Try to update the booking notes
        update_data = {
            "additional_notes": "Trying to edit checked-in booking - should fail with proper error"
        }
        
        headers = {"Authorization": auth_token}
        response = requests.put(f"{API_BASE}/bookings/{test_booking_id}", json=update_data, headers=headers)
        print(f"Edit Checked-in Booking Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 404:
            print(f"❌ BUG CONFIRMED: Got 'booking not found' error (404)")
            print(f"   This is the bug - booking exists but returns 404")
            return False
        elif response.status_code == 400:
            # Check if we get the proper error message
            try:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                if "Cannot modify booking" in error_detail and "Checked" in error_detail:
                    print(f"✅ Proper error message received: {error_detail}")
                    return True
                else:
                    print(f"❌ Wrong error message: {error_detail}")
                    return False
            except:
                print(f"❌ Could not parse error response")
                return False
        elif response.status_code == 200:
            print(f"❌ BUG: Edit succeeded when it should have failed")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Edit attempt failed - Exception: {e}")
        return False

def step6_analyze_booking_lookup():
    """Step 6: Analyze booking lookup mechanism"""
    print("\n🔬 STEP 6: Analyzing booking lookup mechanism...")
    
    try:
        # Try to get the specific booking by ID using different endpoints
        headers = {"Authorization": auth_token}
        
        # Method 1: Get all bookings and search
        print("Method 1: Searching in all bookings...")
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            found_in_all = any(b.get("id") == test_booking_id for b in bookings)
            print(f"   Found in all bookings: {found_in_all}")
        
        # Method 2: Search by status
        print("Method 2: Searching in 'Checked-in' status bookings...")
        response = requests.get(f"{API_BASE}/bookings?status=Checked-in", headers=headers)
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            found_in_checked_in = any(b.get("id") == test_booking_id for b in bookings)
            print(f"   Found in checked-in bookings: {found_in_checked_in}")
            
            if found_in_checked_in:
                # Show the booking details
                for booking in bookings:
                    if booking.get("id") == test_booking_id:
                        print(f"   Booking details:")
                        print(f"     ID: {booking.get('id')}")
                        print(f"     Status: {booking.get('status')}")
                        print(f"     Guest: {booking.get('guest_name')}")
                        print(f"     Room: {booking.get('room_number')}")
                        break
        
        # Method 3: Check customers collection
        print("Method 3: Checking customers collection...")
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
        if response.status_code == 200:
            customers = response.json()
            found_customer = any(c.get("name") == "John Smith" for c in customers)
            print(f"   Found customer record: {found_customer}")
        
        return True
    except Exception as e:
        print(f"❌ Analysis failed - Exception: {e}")
        return False

def main():
    """Run the complete booking edit bug investigation"""
    print("🐛 BOOKING EDIT BUG INVESTIGATION")
    print("=" * 50)
    print("Reproducing the scenario where editing a 'Checked In' booking")
    print("returns 'booking not found' instead of proper error message.")
    print("=" * 50)
    
    global auth_token
    
    # Authenticate first
    auth_token = authenticate()
    if not auth_token:
        print("❌ Cannot proceed without authentication")
        return False
    
    test_results = []
    
    # Step 1: Create a booking
    test_results.append(("Create Booking", step1_create_booking()))
    
    if not test_results[-1][1]:
        print("❌ Cannot proceed without a test booking")
        return False
    
    # Step 2: Edit booking while "Upcoming"
    test_results.append(("Edit Upcoming Booking", step2_edit_upcoming_booking()))
    
    # Step 3: Check-in the booking
    test_results.append(("Check-in Booking", step3_checkin_booking()))
    
    # Step 4: Verify booking exists after check-in
    test_results.append(("Verify Booking Exists", step4_verify_booking_exists()))
    
    # Step 5: Attempt to edit "Checked In" booking
    test_results.append(("Edit Checked-in Booking", step5_attempt_edit_checked_in()))
    
    # Step 6: Analyze booking lookup
    test_results.append(("Analyze Booking Lookup", step6_analyze_booking_lookup()))
    
    # Summary
    print("\n" + "=" * 70)
    print("🐛 BUG INVESTIGATION SUMMARY")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Steps: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    # Bug analysis
    print("\n🔍 BUG ANALYSIS:")
    if not test_results[4][1]:  # Edit Checked-in Booking failed
        if test_results[3][1]:  # But booking exists
            print("❌ BUG CONFIRMED: Booking exists but edit returns 'booking not found'")
            print("   Root Cause: Issue in booking lookup logic for edit endpoint")
            print("   Expected: Proper error message about status restriction")
            print("   Actual: 'booking not found' error")
        else:
            print("❌ BUG CONFIRMED: Booking disappears after check-in")
            print("   Root Cause: Booking record lost during check-in process")
    else:
        print("✅ No bug found - proper error handling working")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)