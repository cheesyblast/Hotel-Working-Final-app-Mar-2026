#!/usr/bin/env python3
"""
Short Time Booking Extension After Check-in Test
Tests the specific scenario where a short time booking is checked in and then attempted to be extended.
This test verifies that the proper error message is returned instead of "booking not found".
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

print(f"Testing Short Time Booking Extension After Check-in at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
auth_token = None
auth_headers = {}

def authenticate():
    """Authenticate with admin credentials"""
    global auth_token, auth_headers
    print("\n🔐 Authenticating with admin credentials...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data.get("access_token")
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def test_health_check():
    """Test basic API health"""
    print("\n1. Testing API Health Check")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API is healthy")
            return True
        else:
            print(f"❌ API health check failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed - Exception: {e}")
        return False

def get_available_room():
    """Get an available room for booking"""
    print("\n2. Getting available room for booking...")
    try:
        response = requests.get(f"{API_BASE}/rooms")
        if response.status_code == 200:
            rooms = response.json()
            available_rooms = [room for room in rooms if room.get('status') == 'Available']
            
            if available_rooms:
                selected_room = available_rooms[0]
                print(f"✅ Found available room: {selected_room['room_number']} ({selected_room['room_type']})")
                return selected_room['room_number']
            else:
                print("❌ No available rooms found")
                return None
        else:
            print(f"❌ Failed to get rooms - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to get rooms - Exception: {e}")
        return None

def create_short_time_booking(room_number):
    """Create a short time booking (same check-in and check-out date)"""
    print(f"\n3. Creating Short Time Booking for room {room_number}...")
    
    today = datetime.now().date()
    
    booking_data = {
        "guest_name": "John Smith",
        "guest_email": "john.smith@example.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "ID123456",
        "guest_country": "USA",
        "room_number": room_number,
        "check_in_date": today.isoformat(),
        "check_out_date": today.isoformat(),  # Same day for short time
        "stay_type": "Short Time",
        "booking_amount": 2500.0,
        "booking_channel_name": "Direct",
        "additional_notes": "Short time booking test",
        "booking_status": "Upcoming"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
        
        if response.status_code == 200:
            booking = response.json()
            booking_id = booking.get('id')
            print(f"✅ Short Time booking created successfully")
            print(f"   Booking ID: {booking_id}")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Room: {booking['room_number']}")
            print(f"   Stay Type: {booking['stay_type']}")
            print(f"   Check-in Date: {booking['check_in_date']}")
            print(f"   Check-out Date: {booking['check_out_date']}")
            print(f"   Status: {booking['status']}")
            return booking_id
        else:
            print(f"❌ Failed to create booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Failed to create booking - Exception: {e}")
        return None

def check_in_booking(booking_id):
    """Check-in the booking to move it to 'Checked-in' status"""
    print(f"\n4. Checking in booking {booking_id}...")
    
    checkin_data = {
        "booking_id": booking_id,
        "advance_amount": 0.0,
        "notes": "Check-in for short time booking test",
        "payment_method": "Cash"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Booking checked in successfully")
            print(f"   Message: {result.get('message', 'No message')}")
            
            # Verify the booking is now in checked-in status
            booking_response = requests.get(f"{API_BASE}/bookings", headers=auth_headers)
            if booking_response.status_code == 200:
                bookings_data = booking_response.json()
                bookings = bookings_data.get('bookings', [])
                
                checked_in_booking = None
                for booking in bookings:
                    if booking.get('id') == booking_id:
                        checked_in_booking = booking
                        break
                
                if checked_in_booking and checked_in_booking.get('status') == 'Checked-in':
                    print(f"✅ Booking status confirmed as: {checked_in_booking['status']}")
                    return True
                else:
                    print(f"❌ Booking status not updated correctly. Current status: {checked_in_booking.get('status') if checked_in_booking else 'Not found'}")
                    return False
            else:
                print("⚠️ Could not verify booking status after check-in")
                return True  # Assume success if we can't verify
        else:
            print(f"❌ Failed to check in booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to check in booking - Exception: {e}")
        return False

def attempt_to_edit_checked_in_booking(booking_id):
    """Attempt to edit/extend the checked-in booking"""
    print(f"\n5. Attempting to edit/extend checked-in booking {booking_id}...")
    
    # Try to extend the booking by changing the check-out date
    tomorrow = (datetime.now().date() + timedelta(days=1))
    
    update_data = {
        "check_out_date": tomorrow.isoformat(),
        "additional_notes": "Attempting to extend short time booking after check-in"
    }
    
    try:
        response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=auth_headers)
        
        print(f"Edit attempt status code: {response.status_code}")
        
        if response.status_code == 400:
            # This is the expected response for checked-in bookings
            error_data = response.json()
            error_message = error_data.get('detail', '')
            
            print(f"Response message: {error_message}")
            
            # Check if we get the proper error message
            expected_message_parts = ["Cannot modify booking", "Checked-in", "Upcoming"]
            
            if all(part in error_message for part in expected_message_parts):
                print("✅ CORRECT ERROR MESSAGE: Proper status-based error returned")
                print(f"   Expected behavior: Cannot modify checked-in bookings")
                print(f"   Actual message: {error_message}")
                return True, "correct_error"
            elif "booking not found" in error_message.lower():
                print("❌ INCORRECT ERROR MESSAGE: 'Booking not found' error returned")
                print(f"   This is the bug we're testing for!")
                print(f"   Actual message: {error_message}")
                return False, "booking_not_found_error"
            else:
                print(f"❌ UNEXPECTED ERROR MESSAGE: {error_message}")
                return False, "unexpected_error"
                
        elif response.status_code == 200:
            print("❌ UNEXPECTED SUCCESS: Booking was modified when it should have been rejected")
            print("   Checked-in bookings should not be modifiable")
            return False, "unexpected_success"
            
        elif response.status_code == 404:
            print("❌ BOOKING NOT FOUND: This is the specific bug we're testing for")
            print("   The booking should be found but rejected due to status")
            return False, "booking_not_found_error"
            
        else:
            print(f"❌ UNEXPECTED STATUS CODE: {response.status_code}")
            print(f"Response: {response.text}")
            return False, "unexpected_status"
            
    except Exception as e:
        print(f"❌ Failed to attempt booking edit - Exception: {e}")
        return False, "exception_error"

def verify_booking_persistence(booking_id):
    """Verify that the booking still exists and can be found by ID"""
    print(f"\n6. Verifying booking persistence for ID {booking_id}...")
    
    try:
        # Try to get all bookings and find our booking
        response = requests.get(f"{API_BASE}/bookings", headers=auth_headers)
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get('bookings', [])
            
            target_booking = None
            for booking in bookings:
                if booking.get('id') == booking_id:
                    target_booking = booking
                    break
            
            if target_booking:
                print("✅ Booking found in database")
                print(f"   Booking ID: {target_booking['id']}")
                print(f"   Guest Name: {target_booking['guest_name']}")
                print(f"   Room Number: {target_booking['room_number']}")
                print(f"   Status: {target_booking['status']}")
                print(f"   Stay Type: {target_booking['stay_type']}")
                return True
            else:
                print("❌ Booking not found in database")
                print("   This indicates a data persistence issue")
                return False
        else:
            print(f"❌ Failed to retrieve bookings - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify booking persistence - Exception: {e}")
        return False

def main():
    """Run the complete short time booking extension test"""
    print("🧪 SHORT TIME BOOKING EXTENSION AFTER CHECK-IN TEST")
    print("=" * 60)
    print("Testing scenario:")
    print("1. Create short time booking (same check-in/check-out date)")
    print("2. Check-in the booking (move to 'Checked-in' status)")
    print("3. Attempt to edit/extend the booking")
    print("4. Verify proper error message (not 'booking not found')")
    print("=" * 60)
    
    # Step 0: Authenticate
    if not authenticate():
        print("\n❌ TEST FAILED: Could not authenticate")
        return False
    
    # Step 1: Health check
    if not test_health_check():
        print("\n❌ TEST FAILED: API health check failed")
        return False
    
    # Step 2: Get available room
    room_number = get_available_room()
    if not room_number:
        print("\n❌ TEST FAILED: No available room found")
        return False
    
    # Step 3: Create short time booking
    booking_id = create_short_time_booking(room_number)
    if not booking_id:
        print("\n❌ TEST FAILED: Could not create short time booking")
        return False
    
    # Step 4: Check-in the booking
    if not check_in_booking(booking_id):
        print("\n❌ TEST FAILED: Could not check in booking")
        return False
    
    # Step 5: Verify booking persistence
    if not verify_booking_persistence(booking_id):
        print("\n❌ TEST FAILED: Booking not found after check-in")
        return False
    
    # Step 6: Attempt to edit the checked-in booking
    edit_success, error_type = attempt_to_edit_checked_in_booking(booking_id)
    
    # Final results
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if edit_success and error_type == "correct_error":
        print("✅ TEST PASSED: Short time booking extension after check-in works correctly")
        print("   ✓ Booking was created successfully")
        print("   ✓ Booking was checked in successfully")
        print("   ✓ Booking persists after check-in")
        print("   ✓ Edit attempt returns proper error message")
        print("   ✓ No 'booking not found' error")
        print("\n🎉 The reported issue has been RESOLVED!")
        return True
    else:
        print("❌ TEST FAILED: Short time booking extension issue still exists")
        print("   ✓ Booking was created successfully")
        print("   ✓ Booking was checked in successfully")
        
        if error_type == "booking_not_found_error":
            print("   ❌ CRITICAL ISSUE: 'Booking not found' error returned")
            print("   ❌ Expected: 'Cannot modify booking with status Checked-in'")
            print("\n🚨 The reported BUG is still PRESENT!")
        elif error_type == "unexpected_success":
            print("   ❌ ISSUE: Booking was modified when it should be rejected")
        else:
            print(f"   ❌ ISSUE: Unexpected error type: {error_type}")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)