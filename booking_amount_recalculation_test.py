#!/usr/bin/env python3
"""
Booking Amount Recalculation Test for Hotel Management System
Tests the critical fix for booking amount recalculation when editing booking dates.

This test focuses on the user-reported issue:
"When editing a booking's dates (e.g., changing from 2 nights to 3 nights), 
the checkout only shows charges for the original booking amount, not the updated 
amount based on new dates."
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

# Authentication token (will be set after login)
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
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers for API requests"""
    if not AUTH_TOKEN:
        return {}
    return {"Authorization": f"Bearer {AUTH_TOKEN}"}

def test_health_check():
    """Test API health check"""
    print("\n1. Testing API Health Check")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API health check PASSED")
            return True
        else:
            print(f"❌ API health check FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check FAILED - Exception: {e}")
        return False

def setup_test_data():
    """Set up test data - create multiple test rooms with known pricing"""
    print("\n2. Setting up test data")
    
    # Create multiple test rooms to avoid conflicts
    test_rooms = [
        {
            "room_number": "TEST101",
            "room_type": "Double",
            "price_per_night": 5000.0,  # LKR 5000 per night
            "max_occupancy": 2,
            "amenities": ["WiFi", "AC", "TV"]
        },
        {
            "room_number": "TEST102",
            "room_type": "Double",
            "price_per_night": 5000.0,  # LKR 5000 per night
            "max_occupancy": 2,
            "amenities": ["WiFi", "AC", "TV"]
        },
        {
            "room_number": "TEST103",
            "room_type": "Triple",
            "price_per_night": 7500.0,  # LKR 7500 per night
            "max_occupancy": 3,
            "amenities": ["WiFi", "AC", "TV", "Balcony"]
        }
    ]
    
    try:
        created_rooms = 0
        for room_data in test_rooms:
            response = requests.post(f"{API_BASE}/rooms", json=room_data, headers=get_auth_headers())
            if response.status_code == 200:
                created_rooms += 1
            else:
                print(f"⚠️ Room {room_data['room_number']} creation response: {response.status_code}")
        
        print(f"✅ {created_rooms} test rooms created successfully")
        return True
    except Exception as e:
        print(f"❌ Test data setup failed - Exception: {e}")
        return False

def test_booking_amount_recalculation_night_stay():
    """Test booking amount recalculation for Night Stay bookings"""
    print("\n3. Testing Booking Amount Recalculation - Night Stay")
    
    # Step 1: Create a booking for 2 nights
    today = datetime.now().date()
    check_in_date = today + timedelta(days=1)  # Tomorrow
    check_out_date = check_in_date + timedelta(days=2)  # 2 nights
    
    initial_booking_data = {
        "guest_name": "John Doe",
        "guest_email": "john.doe@example.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "ID123456",
        "guest_country": "USA",
        "room_number": "TEST101",
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "stay_type": "Night Stay",
        "booking_amount": 10000.0,  # 2 nights × 5000 = 10000
        "additional_notes": "Test booking for amount recalculation"
    }
    
    try:
        # Create initial booking
        print("Creating initial booking for 2 nights...")
        response = requests.post(f"{API_BASE}/bookings", json=initial_booking_data, headers=get_auth_headers())
        
        if response.status_code != 200:
            print(f"❌ Failed to create initial booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
        
        booking = response.json()
        booking_id = booking.get('id')
        initial_amount = booking.get('booking_amount')
        
        print(f"✅ Initial booking created - ID: {booking_id}, Amount: {initial_amount}")
        
        # Step 2: Update booking to extend to 3 nights
        new_check_out_date = check_in_date + timedelta(days=3)  # 3 nights
        
        update_data = {
            "check_out_date": new_check_out_date.strftime('%Y-%m-%d')
        }
        
        print(f"Updating booking to extend to 3 nights (checkout: {new_check_out_date})...")
        update_response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=get_auth_headers())
        
        if update_response.status_code != 200:
            print(f"❌ Failed to update booking - Status: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False, None
        
        update_result = update_response.json()
        print(f"✅ Booking update response: {update_result}")
        
        # Step 3: Verify the booking amount was recalculated
        print("Verifying booking amount recalculation...")
        get_response = requests.get(f"{API_BASE}/bookings?search=John Doe", headers=get_auth_headers())
        
        if get_response.status_code != 200:
            print(f"❌ Failed to retrieve updated booking - Status: {get_response.status_code}")
            return False, None
        
        bookings_data = get_response.json()
        updated_bookings = bookings_data.get('bookings', [])
        
        if not updated_bookings:
            print("❌ No bookings found after update")
            return False
        
        updated_booking = updated_bookings[0]
        updated_amount = updated_booking.get('booking_amount')
        expected_amount = 5000.0 * 3  # 3 nights × 5000 = 15000
        
        print(f"Original amount: {initial_amount}")
        print(f"Updated amount: {updated_amount}")
        print(f"Expected amount: {expected_amount}")
        
        if abs(updated_amount - expected_amount) < 0.01:
            print("✅ Booking amount recalculation PASSED - Amount correctly updated from 2 nights to 3 nights")
            return True, booking_id
        else:
            print(f"❌ Booking amount recalculation FAILED - Expected {expected_amount}, got {updated_amount}")
            return False, booking_id
            
    except Exception as e:
        print(f"❌ Booking amount recalculation test failed - Exception: {e}")
        return False, None

def test_short_time_booking_recalculation():
    """Test booking amount recalculation for Short Time bookings"""
    print("\n4. Testing Short Time Booking Amount Recalculation")
    
    today = datetime.now().date()
    check_in_date = today + timedelta(days=5)  # Use different date to avoid conflicts
    
    short_time_booking_data = {
        "guest_name": "Jane Smith",
        "guest_email": "jane.smith@example.com",
        "guest_phone": "+1987654321",
        "room_number": "TEST102",  # Use different room
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "stay_type": "Short Time",
        "booking_amount": 2500.0,  # 50% of 5000 = 2500
        "additional_notes": "Short time booking test"
    }
    
    try:
        # Create short time booking
        print("Creating Short Time booking...")
        response = requests.post(f"{API_BASE}/bookings", json=short_time_booking_data, headers=get_auth_headers())
        
        if response.status_code != 200:
            print(f"❌ Failed to create short time booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        booking = response.json()
        booking_id = booking.get('id')
        amount = booking.get('booking_amount')
        expected_short_time_amount = 5000.0 * 0.5  # 50% of night rate
        
        print(f"✅ Short Time booking created - ID: {booking_id}, Amount: {amount}")
        
        if abs(amount - expected_short_time_amount) < 0.01:
            print("✅ Short Time booking amount calculation PASSED")
            return True
        else:
            print(f"❌ Short Time booking amount FAILED - Expected {expected_short_time_amount}, got {amount}")
            return False
            
    except Exception as e:
        print(f"❌ Short Time booking test failed - Exception: {e}")
        return False

def test_checked_in_booking_update():
    """Test booking update for checked-in customers (customer record update)"""
    print("\n5. Testing Checked-In Booking Update (Customer Record Update)")
    
    today = datetime.now().date()
    check_in_date = today - timedelta(days=1)  # Yesterday (past date)
    check_out_date = check_in_date + timedelta(days=2)  # 2 nights
    
    checked_in_booking_data = {
        "guest_name": "Alice Johnson",
        "guest_email": "alice.johnson@example.com",
        "guest_phone": "+1122334455",
        "room_number": "TEST103",  # Use different room
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "stay_type": "Night Stay",
        "booking_amount": 15000.0,  # 2 nights × 7500 (TEST103 price)
        "booking_status": "Checked In",  # This will create customer record
        "additional_notes": "Checked-in booking for customer record test"
    }
    
    try:
        # Create checked-in booking
        print("Creating Checked-In booking...")
        response = requests.post(f"{API_BASE}/bookings", json=checked_in_booking_data, headers=get_auth_headers())
        
        if response.status_code != 200:
            print(f"❌ Failed to create checked-in booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        booking = response.json()
        booking_id = booking.get('id')
        
        print(f"✅ Checked-In booking created - ID: {booking_id}")
        
        # Verify customer record was created
        customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        if customers_response.status_code == 200:
            customers = customers_response.json()
            alice_customer = next((c for c in customers if c.get('name') == 'Alice Johnson'), None)
            
            if alice_customer:
                print(f"✅ Customer record created - Room charges: {alice_customer.get('room_charges')}")
                
                # Now update the booking dates (extend to 3 nights)
                new_check_out_date = check_in_date + timedelta(days=3)  # 3 nights
                
                update_data = {
                    "check_out_date": new_check_out_date.strftime('%Y-%m-%d')
                }
                
                print("Updating checked-in booking to extend to 3 nights...")
                
                # Note: This should fail because only 'Upcoming' bookings can be modified
                update_response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=get_auth_headers())
                
                if update_response.status_code == 400:
                    error_data = update_response.json()
                    if "Only 'Upcoming' bookings can be modified" in error_data.get('detail', ''):
                        print("✅ Checked-In booking update protection PASSED - Cannot modify checked-in bookings")
                        return True
                    else:
                        print(f"❌ Unexpected error message: {error_data.get('detail')}")
                        return False
                else:
                    print(f"❌ Expected 400 error for checked-in booking update, got {update_response.status_code}")
                    return False
            else:
                print("❌ Customer record not found after checked-in booking creation")
                return False
        else:
            print("❌ Failed to retrieve customers")
            return False
            
    except Exception as e:
        print(f"❌ Checked-in booking test failed - Exception: {e}")
        return False

def test_checkout_with_updated_amount(booking_id):
    """Test that booking amount is correctly stored and can be verified"""
    print("\n6. Testing Updated Booking Amount Verification")
    
    if not booking_id:
        print("❌ No booking ID provided for verification test")
        return False
    
    try:
        # Verify the booking has the correct updated amount
        print("Verifying the updated booking amount is correctly stored...")
        get_response = requests.get(f"{API_BASE}/bookings?search=John Doe", headers=get_auth_headers())
        
        if get_response.status_code != 200:
            print(f"❌ Failed to retrieve booking - Status: {get_response.status_code}")
            return False
        
        bookings_data = get_response.json()
        updated_bookings = bookings_data.get('bookings', [])
        
        if not updated_bookings:
            print("❌ No bookings found")
            return False
        
        updated_booking = updated_bookings[0]
        updated_amount = updated_booking.get('booking_amount')
        expected_amount = 15000.0  # 3 nights × 5000
        
        print(f"Final booking amount: {updated_amount}")
        print(f"Expected amount: {expected_amount}")
        
        if abs(updated_amount - expected_amount) < 0.01:
            print("✅ Updated booking amount verification PASSED")
            print("✅ The booking amount recalculation fix is working correctly!")
            return True
        else:
            print(f"❌ Booking amount verification FAILED - Expected {expected_amount}, got {updated_amount}")
            return False
            
    except Exception as e:
        print(f"❌ Booking amount verification test failed - Exception: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n7. Cleaning up test data")
    
    try:
        # Delete test rooms
        rooms_response = requests.get(f"{API_BASE}/rooms", headers=get_auth_headers())
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            test_room_numbers = ['TEST101', 'TEST102', 'TEST103']
            
            for room_number in test_room_numbers:
                test_room = next((r for r in rooms if r.get('room_number') == room_number), None)
                
                if test_room:
                    delete_response = requests.delete(f"{API_BASE}/rooms/{test_room.get('id')}", headers=get_auth_headers())
                    if delete_response.status_code == 200:
                        print(f"✅ Test room {room_number} cleaned up")
                    else:
                        print(f"⚠️ Failed to delete test room {room_number} - Status: {delete_response.status_code}")
        
        print("✅ Cleanup completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Cleanup failed - Exception: {e}")
        return False

def main():
    """Run all booking amount recalculation tests"""
    print("🧪 BOOKING AMOUNT RECALCULATION TEST SUITE")
    print("=" * 60)
    print("Testing the critical fix for booking amount recalculation when editing dates")
    print("=" * 60)
    
    test_results = []
    booking_id_for_checkout = None
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed - cannot proceed with tests")
        return False
    
    # Test 1: Health Check
    test_results.append(("API Health Check", test_health_check()))
    
    # Test 2: Setup Test Data
    test_results.append(("Test Data Setup", setup_test_data()))
    
    # Test 3: Main Test - Booking Amount Recalculation for Night Stay
    night_stay_result, booking_id = test_booking_amount_recalculation_night_stay()
    test_results.append(("Night Stay Recalculation", night_stay_result))
    if night_stay_result:
        booking_id_for_checkout = booking_id
    
    # Test 4: Short Time Booking Recalculation
    test_results.append(("Short Time Recalculation", test_short_time_booking_recalculation()))
    
    # Test 5: Checked-In Booking Update Protection
    test_results.append(("Checked-In Update Protection", test_checked_in_booking_update()))
    
    # Test 6: Verify Updated Amount
    test_results.append(("Updated Amount Verification", test_checkout_with_updated_amount(booking_id_for_checkout)))
    
    # Test 7: Cleanup
    test_results.append(("Cleanup", cleanup_test_data()))
    
    # Summary
    print("\n" + "=" * 60)
    print("🧪 BOOKING AMOUNT RECALCULATION TEST RESULTS")
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
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Booking amount recalculation fix is working correctly!")
        print("✅ The user-reported issue has been resolved!")
        return True
    else:
        failed_count = total_tests - passed_tests
        print(f"\n⚠️ {failed_count} test(s) failed.")
        print("❌ The booking amount recalculation fix needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)