#!/usr/bin/env python3
"""
Past Date Booking Functionality Testing for Hotel Management System
Tests the new past date booking functionality with status selection.
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

print(f"Testing Past Date Booking Functionality at: {API_BASE}")
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
            print("✅ API Health Check PASSED")
            return True
        else:
            print(f"❌ API Health Check FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health Check FAILED - Exception: {e}")
        return False

def test_get_rooms():
    """Get available rooms for testing"""
    print("\n2. Getting Available Rooms")
    try:
        response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
        if response.status_code == 200:
            rooms = response.json()
            available_rooms = [room for room in rooms if room['status'] == 'Available']
            print(f"✅ Found {len(available_rooms)} available rooms out of {len(rooms)} total rooms")
            return True, available_rooms
        else:
            print(f"❌ Failed to get rooms - Status: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Failed to get rooms - Exception: {e}")
        return False, []

def test_normal_future_booking(available_rooms):
    """Test 1: Create a normal future date booking (should work as before)"""
    print("\n3. Test 1: Normal Future Date Booking")
    
    if not available_rooms:
        print("❌ No available rooms for testing")
        return False
    
    test_room = available_rooms[0]['room_number']
    future_date = (datetime.now() + timedelta(days=7)).date()
    checkout_date = future_date + timedelta(days=2)
    
    booking_data = {
        "guest_name": "John Smith",
        "guest_email": "john.smith@email.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "P123456789",
        "guest_country": "USA",
        "room_number": test_room,
        "check_in_date": future_date.isoformat(),
        "check_out_date": checkout_date.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 15000.0,
        "booking_channel_name": "Direct",
        "additional_notes": "Test future booking",
        "booking_status": "Upcoming"  # Default status
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Future booking created successfully")
            print(f"   Booking ID: {booking['id']}")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Room: {booking['room_number']}")
            print(f"   Status: {booking['status']}")
            print(f"   Check-in: {booking['check_in_date']}")
            
            # Verify booking status is "Upcoming"
            if booking['status'] == 'Upcoming':
                print("✅ Booking status correctly set to 'Upcoming'")
                return True, booking
            else:
                print(f"❌ Expected status 'Upcoming', got '{booking['status']}'")
                return False, booking
        else:
            print(f"❌ Future booking creation failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Future booking creation failed - Exception: {e}")
        return False, None

def test_past_date_upcoming_booking(available_rooms):
    """Test 2: Create a past date booking with booking_status="Upcoming" """
    print("\n4. Test 2: Past Date Booking with Status 'Upcoming'")
    
    if len(available_rooms) < 2:
        print("❌ Need at least 2 available rooms for testing")
        return False
    
    test_room = available_rooms[1]['room_number']
    past_date = (datetime.now() - timedelta(days=3)).date()
    checkout_date = past_date + timedelta(days=1)
    
    booking_data = {
        "guest_name": "Alice Johnson",
        "guest_email": "alice.johnson@email.com",
        "guest_phone": "+1987654321",
        "guest_id_passport": "P987654321",
        "guest_country": "Canada",
        "room_number": test_room,
        "check_in_date": past_date.isoformat(),
        "check_out_date": checkout_date.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 12000.0,
        "booking_channel_name": "Direct",
        "additional_notes": "Test past date upcoming booking",
        "booking_status": "Upcoming"  # Past date but still upcoming status
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Past date 'Upcoming' booking created successfully")
            print(f"   Booking ID: {booking['id']}")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Room: {booking['room_number']}")
            print(f"   Status: {booking['status']}")
            print(f"   Check-in: {booking['check_in_date']} (past date)")
            
            # Verify booking status is "Upcoming"
            if booking['status'] == 'Upcoming':
                print("✅ Past date booking correctly maintained 'Upcoming' status")
                
                # Verify room status is still Available (not occupied)
                room_response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
                if room_response.status_code == 200:
                    rooms = room_response.json()
                    test_room_data = next((r for r in rooms if r['room_number'] == test_room), None)
                    if test_room_data and test_room_data['status'] == 'Available':
                        print("✅ Room status correctly remains 'Available' for upcoming booking")
                        return True, booking
                    else:
                        print(f"❌ Room status should be 'Available', got '{test_room_data['status'] if test_room_data else 'Room not found'}'")
                        return False, booking
                else:
                    print("❌ Could not verify room status")
                    return False, booking
            else:
                print(f"❌ Expected status 'Upcoming', got '{booking['status']}'")
                return False, booking
        else:
            print(f"❌ Past date upcoming booking creation failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Past date upcoming booking creation failed - Exception: {e}")
        return False, None

def test_past_date_checked_in_booking(available_rooms):
    """Test 3: Create a past date booking with booking_status="Checked In" """
    print("\n5. Test 3: Past Date Booking with Status 'Checked In'")
    
    if len(available_rooms) < 3:
        print("❌ Need at least 3 available rooms for testing")
        return False
    
    test_room = available_rooms[2]['room_number']
    past_date = (datetime.now() - timedelta(days=2)).date()
    checkout_date = past_date + timedelta(days=2)
    
    booking_data = {
        "guest_name": "Bob Wilson",
        "guest_email": "bob.wilson@email.com",
        "guest_phone": "+1555666777",
        "guest_id_passport": "P555666777",
        "guest_country": "UK",
        "room_number": test_room,
        "check_in_date": past_date.isoformat(),
        "check_out_date": checkout_date.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 18000.0,
        "booking_channel_name": "Direct",
        "additional_notes": "Test past date checked-in booking",
        "booking_status": "Checked In"  # Past date with checked-in status
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Past date 'Checked In' booking created successfully")
            print(f"   Booking ID: {booking['id']}")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Room: {booking['room_number']}")
            print(f"   Status: {booking['status']}")
            print(f"   Check-in: {booking['check_in_date']} (past date)")
            
            # Verify booking status is "Checked In"
            if booking['status'] == 'Checked In':
                print("✅ Past date booking correctly set to 'Checked In' status")
                
                # Verify customer record was created
                customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
                if customers_response.status_code == 200:
                    customers = customers_response.json()
                    customer = next((c for c in customers if c['name'] == booking['guest_name']), None)
                    
                    if customer:
                        print("✅ Customer record automatically created")
                        print(f"   Customer ID: {customer['id']}")
                        print(f"   Name: {customer['name']}")
                        print(f"   Room: {customer['current_room']}")
                        print(f"   Room Charges: {customer['room_charges']}")
                        
                        # Verify room status is now Occupied
                        room_response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
                        if room_response.status_code == 200:
                            rooms = room_response.json()
                            test_room_data = next((r for r in rooms if r['room_number'] == test_room), None)
                            
                            if test_room_data:
                                if test_room_data['status'] == 'Occupied':
                                    print("✅ Room status correctly updated to 'Occupied'")
                                    print(f"   Current Guest: {test_room_data['current_guest']}")
                                    print(f"   Check-in Date: {test_room_data['check_in_date']}")
                                    print(f"   Check-out Date: {test_room_data['check_out_date']}")
                                    
                                    # Verify guest name matches
                                    if test_room_data['current_guest'] == booking['guest_name']:
                                        print("✅ Room guest information correctly set")
                                        return True, booking, customer
                                    else:
                                        print(f"❌ Room guest mismatch. Expected: {booking['guest_name']}, Got: {test_room_data['current_guest']}")
                                        return False, booking, customer
                                else:
                                    print(f"❌ Room status should be 'Occupied', got '{test_room_data['status']}'")
                                    return False, booking, customer
                            else:
                                print("❌ Could not find room data")
                                return False, booking, customer
                        else:
                            print("❌ Could not verify room status")
                            return False, booking, customer
                    else:
                        print("❌ Customer record was not created automatically")
                        return False, booking, None
                else:
                    print("❌ Could not verify customer creation")
                    return False, booking, None
            else:
                print(f"❌ Expected status 'Checked In', got '{booking['status']}'")
                return False, booking, None
        else:
            print(f"❌ Past date checked-in booking creation failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None, None
    except Exception as e:
        print(f"❌ Past date checked-in booking creation failed - Exception: {e}")
        return False, None, None

def test_room_availability_validation(available_rooms):
    """Test 4: Verify room availability is properly checked for both past and future dates"""
    print("\n6. Test 4: Room Availability Validation")
    
    if len(available_rooms) < 4:
        print("❌ Need at least 4 available rooms for testing")
        return False
    
    # Use the same room that was booked in previous test (should be occupied now)
    occupied_room = available_rooms[2]['room_number']  # This was used in test 3
    
    # Try to book the same room for overlapping dates (should fail)
    past_date = (datetime.now() - timedelta(days=1)).date()
    checkout_date = past_date + timedelta(days=1)
    
    conflicting_booking_data = {
        "guest_name": "Charlie Brown",
        "guest_email": "charlie.brown@email.com",
        "guest_phone": "+1888999000",
        "room_number": occupied_room,
        "check_in_date": past_date.isoformat(),
        "check_out_date": checkout_date.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 10000.0,
        "booking_status": "Checked In"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=conflicting_booking_data, headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 400 or response.status_code == 409:
            print("✅ Room availability validation working - Conflicting booking correctly rejected")
            print(f"   Response: {response.text}")
            
            # Now test with an available room (should succeed)
            available_room = available_rooms[3]['room_number']
            conflicting_booking_data['room_number'] = available_room
            conflicting_booking_data['guest_name'] = "Diana Prince"
            
            success_response = requests.post(f"{API_BASE}/bookings", json=conflicting_booking_data, headers=auth_headers)
            
            if success_response.status_code == 200:
                print("✅ Available room booking succeeded as expected")
                return True
            else:
                print(f"❌ Available room booking failed unexpectedly - Status: {success_response.status_code}")
                return False
        else:
            print(f"❌ Room availability validation failed - Expected 400/409, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Room availability validation test failed - Exception: {e}")
        return False

def test_short_time_booking():
    """Test 5: Test with different stay types (Night Stay vs Short Time)"""
    print("\n7. Test 5: Short Time Booking with Past Date")
    
    # Get available rooms again
    room_response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
    if room_response.status_code != 200:
        print("❌ Could not get rooms for short time test")
        return False
    
    rooms = room_response.json()
    available_rooms = [room for room in rooms if room['status'] == 'Available']
    
    if not available_rooms:
        print("❌ No available rooms for short time test")
        return False
    
    test_room = available_rooms[0]['room_number']
    past_date = (datetime.now() - timedelta(days=1)).date()
    
    # Short Time booking - checkout should be same day
    short_time_booking_data = {
        "guest_name": "Eva Martinez",
        "guest_email": "eva.martinez@email.com",
        "guest_phone": "+1777888999",
        "room_number": test_room,
        "check_in_date": past_date.isoformat(),
        "stay_type": "Short Time",
        "booking_amount": 5000.0,
        "booking_status": "Checked In"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=short_time_booking_data, headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Short Time booking created successfully")
            print(f"   Guest: {booking['guest_name']}")
            print(f"   Stay Type: {booking['stay_type']}")
            print(f"   Check-in: {booking['check_in_date']}")
            print(f"   Check-out: {booking['check_out_date']}")
            
            # Verify checkout date is same as check-in for Short Time
            checkin_date = booking['check_in_date'].split('T')[0] if 'T' in booking['check_in_date'] else booking['check_in_date']
            checkout_date = booking['check_out_date'].split('T')[0] if 'T' in booking['check_out_date'] else booking['check_out_date']
            
            if checkin_date == checkout_date:
                print("✅ Short Time booking correctly set same check-in and check-out dates")
                return True
            else:
                print(f"❌ Short Time booking dates mismatch - Check-in: {checkin_date}, Check-out: {checkout_date}")
                return False
        else:
            print(f"❌ Short Time booking creation failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Short Time booking test failed - Exception: {e}")
        return False

def test_booking_listing_verification():
    """Test 6: Verify bookings appear in appropriate lists"""
    print("\n8. Test 6: Booking Listing Verification")
    
    try:
        # Get all bookings
        all_bookings_response = requests.get(f"{API_BASE}/bookings", headers=auth_headers)
        if all_bookings_response.status_code != 200:
            print("❌ Could not get all bookings")
            return False
        
        all_bookings_data = all_bookings_response.json()
        all_bookings = all_bookings_data.get('bookings', [])
        
        # Get upcoming bookings
        upcoming_response = requests.get(f"{API_BASE}/bookings/upcoming", headers=auth_headers)
        if upcoming_response.status_code != 200:
            print("❌ Could not get upcoming bookings")
            return False
        
        upcoming_bookings = upcoming_response.json()
        
        print(f"Total bookings: {len(all_bookings)}")
        print(f"Upcoming bookings: {len(upcoming_bookings)}")
        
        # Count bookings by status
        status_counts = {}
        for booking in all_bookings:
            status = booking.get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Booking status distribution:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        # Verify we have both Upcoming and Checked In bookings
        if status_counts.get('Upcoming', 0) > 0 and status_counts.get('Checked In', 0) > 0:
            print("✅ Both 'Upcoming' and 'Checked In' bookings found")
            
            # Verify upcoming bookings list only contains Upcoming status
            upcoming_statuses = [b.get('status') for b in upcoming_bookings]
            if all(status == 'Upcoming' for status in upcoming_statuses):
                print("✅ Upcoming bookings list correctly filtered")
                return True
            else:
                print(f"❌ Upcoming bookings list contains non-upcoming bookings: {set(upcoming_statuses)}")
                return False
        else:
            print(f"❌ Missing expected booking statuses - Upcoming: {status_counts.get('Upcoming', 0)}, Checked In: {status_counts.get('Checked In', 0)}")
            return False
    except Exception as e:
        print(f"❌ Booking listing verification failed - Exception: {e}")
        return False

def main():
    """Run all past date booking functionality tests"""
    print("Starting Past Date Booking Functionality Tests")
    print("=" * 70)
    
    test_results = []
    
    # Authentication
    if not authenticate():
        print("❌ Authentication failed - Cannot proceed with tests")
        return False
    
    # Test 0: Health Check
    test_results.append(("API Health Check", test_health_check()))
    
    # Get available rooms
    rooms_passed, available_rooms = test_get_rooms()
    test_results.append(("Get Available Rooms", rooms_passed))
    
    if not rooms_passed or not available_rooms:
        print("❌ Cannot proceed without available rooms")
        return False
    
    # Test 1: Normal future date booking
    future_passed, future_booking = test_normal_future_booking(available_rooms)
    test_results.append(("Future Date Booking", future_passed))
    
    # Test 2: Past date booking with "Upcoming" status
    past_upcoming_passed, past_upcoming_booking = test_past_date_upcoming_booking(available_rooms)
    test_results.append(("Past Date Upcoming Booking", past_upcoming_passed))
    
    # Test 3: Past date booking with "Checked In" status
    past_checkedin_passed, past_checkedin_booking, customer = test_past_date_checked_in_booking(available_rooms)
    test_results.append(("Past Date Checked-In Booking", past_checkedin_passed))
    
    # Test 4: Room availability validation
    test_results.append(("Room Availability Validation", test_room_availability_validation(available_rooms)))
    
    # Test 5: Short Time booking
    test_results.append(("Short Time Booking", test_short_time_booking()))
    
    # Test 6: Booking listing verification
    test_results.append(("Booking Listing Verification", test_booking_listing_verification()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - PAST DATE BOOKING FUNCTIONALITY")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Past date booking functionality is working correctly.")
        print("\n✅ Key Features Verified:")
        print("   • Normal future date bookings work as before")
        print("   • Past date bookings with 'Upcoming' status are created correctly")
        print("   • Past date bookings with 'Checked In' status automatically:")
        print("     - Create customer records")
        print("     - Update room status to 'Occupied'")
        print("     - Set room's current guest and dates")
        print("   • Room availability checking works for both past and future dates")
        print("   • Short Time bookings handle dates correctly")
        print("   • Booking listings show appropriate bookings")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)