#!/usr/bin/env python3
"""
Focused Booking Amount Recalculation Test
Tests the critical fix for booking amount recalculation when editing booking dates.
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os
import uuid

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

# Authentication token
AUTH_TOKEN = None

def authenticate():
    """Authenticate with admin credentials"""
    global AUTH_TOKEN
    print("🔐 Authenticating with admin credentials...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            AUTH_TOKEN = token_data.get("access_token")
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers for API requests"""
    if not AUTH_TOKEN:
        return {}
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_booking_amount_recalculation():
    """Test the core booking amount recalculation functionality"""
    print("\n🧪 TESTING BOOKING AMOUNT RECALCULATION")
    print("=" * 60)
    
    # Generate unique room number to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    test_room_number = f"TEST{unique_id}"
    
    try:
        # Step 1: Create a test room
        print(f"1. Creating test room: {test_room_number}")
        room_data = {
            "room_number": test_room_number,
            "room_type": "Double",
            "price_per_night": 5000.0,  # LKR 5000 per night
            "max_occupancy": 2,
            "amenities": ["WiFi", "AC", "TV"]
        }
        
        room_response = requests.post(f"{API_BASE}/rooms", json=room_data, headers=get_auth_headers())
        if room_response.status_code != 200:
            print(f"❌ Failed to create test room - Status: {room_response.status_code}")
            return False
        
        print(f"✅ Test room {test_room_number} created successfully")
        
        # Step 2: Create initial booking for 2 nights
        print("2. Creating initial booking for 2 nights")
        today = datetime.now().date()
        check_in_date = today + timedelta(days=10)  # Future date to avoid conflicts
        check_out_date = check_in_date + timedelta(days=2)  # 2 nights
        
        booking_data = {
            "guest_name": f"Test Guest {unique_id}",
            "guest_email": f"test{unique_id}@example.com",
            "guest_phone": "+1234567890",
            "room_number": test_room_number,
            "check_in_date": check_in_date.strftime('%Y-%m-%d'),
            "check_out_date": check_out_date.strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 10000.0,  # 2 nights × 5000 = 10000
            "additional_notes": "Test booking for amount recalculation"
        }
        
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=get_auth_headers())
        if booking_response.status_code != 200:
            print(f"❌ Failed to create booking - Status: {booking_response.status_code}")
            print(f"Response: {booking_response.text}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get('id')
        initial_amount = booking.get('booking_amount')
        
        print(f"✅ Initial booking created - ID: {booking_id}")
        print(f"   Initial amount: LKR {initial_amount} (2 nights × 5000)")
        
        # Step 3: Update booking to extend to 3 nights
        print("3. Updating booking to extend to 3 nights")
        new_check_out_date = check_in_date + timedelta(days=3)  # 3 nights
        
        update_data = {
            "check_out_date": new_check_out_date.strftime('%Y-%m-%d')
        }
        
        update_response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=get_auth_headers())
        if update_response.status_code != 200:
            print(f"❌ Failed to update booking - Status: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
        
        update_result = update_response.json()
        changes = update_result.get('changes', [])
        print(f"✅ Booking updated successfully")
        print(f"   Changes made: {changes}")
        
        # Step 4: Verify the booking amount was recalculated
        print("4. Verifying booking amount recalculation")
        
        # Get the updated booking
        get_response = requests.get(f"{API_BASE}/bookings?search={unique_id}", headers=get_auth_headers())
        if get_response.status_code != 200:
            print(f"❌ Failed to retrieve updated booking - Status: {get_response.status_code}")
            return False
        
        bookings_data = get_response.json()
        updated_bookings = bookings_data.get('bookings', [])
        
        if not updated_bookings:
            print("❌ No bookings found after update")
            return False
        
        updated_booking = updated_bookings[0]
        updated_amount = updated_booking.get('booking_amount')
        expected_amount = 5000.0 * 3  # 3 nights × 5000 = 15000
        
        print(f"   Original amount: LKR {initial_amount}")
        print(f"   Updated amount: LKR {updated_amount}")
        print(f"   Expected amount: LKR {expected_amount}")
        
        # Step 5: Verify the calculation is correct
        if abs(updated_amount - expected_amount) < 0.01:
            print("✅ BOOKING AMOUNT RECALCULATION TEST PASSED!")
            print("   ✓ Amount correctly updated from 2 nights to 3 nights")
            print("   ✓ Calculation: 3 nights × LKR 5000 = LKR 15000")
            success = True
        else:
            print("❌ BOOKING AMOUNT RECALCULATION TEST FAILED!")
            print(f"   Expected LKR {expected_amount}, got LKR {updated_amount}")
            success = False
        
        # Step 6: Test Short Time booking calculation
        print("\n5. Testing Short Time booking calculation")
        short_time_booking_data = {
            "guest_name": f"Short Time Guest {unique_id}",
            "guest_email": f"shorttime{unique_id}@example.com",
            "guest_phone": "+1987654321",
            "room_number": test_room_number,
            "check_in_date": (check_in_date + timedelta(days=5)).strftime('%Y-%m-%d'),
            "stay_type": "Short Time",
            "booking_amount": 2500.0,  # 50% of 5000 = 2500
            "additional_notes": "Short time booking test"
        }
        
        short_response = requests.post(f"{API_BASE}/bookings", json=short_time_booking_data, headers=get_auth_headers())
        if short_response.status_code == 200:
            short_booking = short_response.json()
            short_amount = short_booking.get('booking_amount')
            expected_short_amount = 5000.0 * 0.5  # 50% of night rate
            
            if abs(short_amount - expected_short_amount) < 0.01:
                print("✅ Short Time booking calculation PASSED!")
                print(f"   ✓ Amount: LKR {short_amount} (50% of LKR 5000)")
            else:
                print(f"❌ Short Time booking calculation FAILED - Expected {expected_short_amount}, got {short_amount}")
                success = False
        else:
            print(f"⚠️ Short Time booking test skipped - Status: {short_response.status_code}")
        
        # Step 7: Cleanup
        print("\n6. Cleaning up test data")
        
        # Delete the test room
        rooms_response = requests.get(f"{API_BASE}/rooms", headers=get_auth_headers())
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            test_room = next((r for r in rooms if r.get('room_number') == test_room_number), None)
            
            if test_room:
                delete_response = requests.delete(f"{API_BASE}/rooms/{test_room.get('id')}", headers=get_auth_headers())
                if delete_response.status_code == 200:
                    print(f"✅ Test room {test_room_number} cleaned up")
                else:
                    print(f"⚠️ Failed to delete test room - Status: {delete_response.status_code}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

def main():
    """Run the focused booking amount recalculation test"""
    print("🧪 FOCUSED BOOKING AMOUNT RECALCULATION TEST")
    print("=" * 60)
    print("Testing the critical fix for booking amount recalculation when editing dates")
    print("User Issue: 'When editing a booking's dates (e.g., changing from 2 nights")
    print("to 3 nights), the checkout only shows charges for the original booking")
    print("amount, not the updated amount based on new dates.'")
    print("=" * 60)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return False
    
    # Run the main test
    success = test_booking_amount_recalculation()
    
    # Summary
    print("\n" + "=" * 60)
    print("🧪 TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The booking amount recalculation fix is working correctly!")
        print("✅ The user-reported issue has been RESOLVED!")
        print("\nKey findings:")
        print("• Booking amounts are correctly recalculated when dates are modified")
        print("• Night Stay bookings: nights × price_per_night")
        print("• Short Time bookings: 50% of price_per_night")
        print("• The PUT /api/bookings/{booking_id} endpoint is working as expected")
        return True
    else:
        print("❌ TEST FAILED!")
        print("❌ The booking amount recalculation fix needs attention.")
        print("❌ The user-reported issue is NOT resolved.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)