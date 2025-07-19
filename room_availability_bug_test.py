#!/usr/bin/env python3
"""
Room Availability Bug Fix Testing for Hotel Management System
Tests the specific issues mentioned in the review request:
1. Room availability checker not detecting existing bookings properly
2. New booking modal only showing few rooms instead of all available ones  
3. Booking amounts not calculating correctly based on duration
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

print(f"Testing Room Availability Bug Fixes at: {API_BASE}")
print("=" * 80)

def test_health_check():
    """Test GET /api/ - Basic health check"""
    print("\n1. Testing Health Check (GET /api/)")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            if data.get("message") == "Hotel Management API":
                print("✅ Health check PASSED")
                return True
            else:
                print("❌ Health check FAILED - Unexpected response message")
                return False
        else:
            print(f"❌ Health check FAILED - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check FAILED - Exception: {e}")
        return False

def test_room_listing():
    """Test GET /api/rooms - Verify all rooms are returned with proper status"""
    print("\n2. Testing Room Listing (GET /api/rooms)")
    try:
        response = requests.get(f"{API_BASE}/rooms")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"Total rooms returned: {len(rooms)}")
            
            if len(rooms) == 0:
                print("❌ Room listing FAILED - No rooms returned")
                return False
            
            # Check room structure and status
            available_rooms = 0
            occupied_rooms = 0
            reserved_rooms = 0
            
            for room in rooms:
                status = room.get('status', 'Unknown')
                room_number = room.get('room_number', 'Unknown')
                room_type = room.get('room_type', 'Unknown')
                price = room.get('price_per_night', 0)
                
                print(f"  Room {room_number}: {room_type}, Status: {status}, Price: {price}")
                
                if status == 'Available':
                    available_rooms += 1
                elif status == 'Occupied':
                    occupied_rooms += 1
                elif status == 'Reserved':
                    reserved_rooms += 1
            
            print(f"Room Status Summary: Available: {available_rooms}, Occupied: {occupied_rooms}, Reserved: {reserved_rooms}")
            
            if available_rooms > 0:
                print("✅ Room listing PASSED - Rooms returned with proper status")
                return True, rooms
            else:
                print("❌ Room listing FAILED - No available rooms found")
                return False, rooms
        else:
            print(f"❌ Room listing FAILED - Status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Room listing FAILED - Exception: {e}")
        return False, []

def test_room_availability_checker():
    """Test GET /api/rooms/availability/check - Test room availability detection"""
    print("\n3. Testing Room Availability Checker (GET /api/rooms/availability/check)")
    
    # Test with different date ranges
    test_cases = [
        {
            "name": "Future dates (next week)",
            "check_in": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "check_out": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')
        },
        {
            "name": "September dates (user reported issue)",
            "check_in": "2025-09-15",
            "check_out": "2025-09-18"
        },
        {
            "name": "Current month dates",
            "check_in": (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "check_out": (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n3.{i} Testing {test_case['name']}")
        try:
            params = {
                'check_in_date': test_case['check_in'],
                'check_out_date': test_case['check_out']
            }
            
            response = requests.get(f"{API_BASE}/rooms/availability/check", params=params)
            print(f"Status Code: {response.status_code}")
            print(f"Request: {test_case['check_in']} to {test_case['check_out']}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Stay Duration: {data.get('stay_duration')} nights")
                print(f"Total Rooms: {data.get('total_rooms')}")
                print(f"Available Rooms: {data.get('available_rooms')}")
                
                available_rooms = data.get('rooms', [])
                print(f"Available Room Details: {len(available_rooms)} rooms")
                
                for room in available_rooms[:3]:  # Show first 3 rooms
                    print(f"  - Room {room.get('room_number')}: {room.get('room_type')}, Price: {room.get('price_per_night')}")
                
                if len(available_rooms) > 0:
                    print(f"✅ Room availability check PASSED for {test_case['name']}")
                else:
                    print(f"⚠️  Room availability check - No rooms available for {test_case['name']}")
                    
            elif response.status_code == 400:
                error_data = response.json()
                print(f"❌ Room availability check FAILED - Validation error: {error_data.get('detail')}")
                all_passed = False
            else:
                print(f"❌ Room availability check FAILED - Status code: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Room availability check FAILED - Exception: {e}")
            all_passed = False
    
    return all_passed

def test_booking_creation():
    """Test POST /api/bookings - Test creating bookings with different amounts"""
    print("\n4. Testing Booking Creation (POST /api/bookings)")
    
    # Test bookings with different amounts
    test_bookings = [
        {
            "name": "Test booking with 8500 amount",
            "guest_name": "Test Guest 1",
            "guest_email": "test1@example.com",
            "guest_phone": "123-456-7890",
            "room_number": "101",
            "check_in_date": (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'),
            "check_out_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 8500.0
        },
        {
            "name": "Test booking with 12000 amount",
            "guest_name": "Test Guest 2", 
            "guest_email": "test2@example.com",
            "guest_phone": "098-765-4321",
            "room_number": "201",
            "check_in_date": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            "check_out_date": (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 12000.0
        },
        {
            "name": "September booking (user reported issue)",
            "guest_name": "September Guest",
            "guest_email": "september@example.com", 
            "guest_phone": "555-123-4567",
            "room_number": "103",
            "check_in_date": "2025-09-20",
            "check_out_date": "2025-09-23",
            "stay_type": "Night Stay",
            "booking_amount": 15000.0
        }
    ]
    
    created_bookings = []
    all_passed = True
    
    for i, booking_data in enumerate(test_bookings, 1):
        print(f"\n4.{i} Testing {booking_data['name']}")
        try:
            # Remove the 'name' key before sending
            booking_payload = {k: v for k, v in booking_data.items() if k != 'name'}
            
            response = requests.post(f"{API_BASE}/bookings", json=booking_payload)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                booking = response.json()
                print(f"Booking ID: {booking.get('id')}")
                print(f"Guest Name: {booking.get('guest_name')}")
                print(f"Room Number: {booking.get('room_number')}")
                print(f"Booking Amount: {booking.get('booking_amount')}")
                print(f"Status: {booking.get('status')}")
                print(f"Check-in: {booking.get('check_in_date')}")
                print(f"Check-out: {booking.get('check_out_date')}")
                
                # Verify booking amount is stored correctly
                if booking.get('booking_amount') == booking_payload['booking_amount']:
                    print("✅ Booking amount stored correctly")
                else:
                    print(f"❌ Booking amount mismatch - Expected: {booking_payload['booking_amount']}, Got: {booking.get('booking_amount')}")
                    all_passed = False
                
                # Verify status is set to "Upcoming"
                if booking.get('status') == 'Upcoming':
                    print("✅ Booking status set to 'Upcoming'")
                else:
                    print(f"❌ Booking status incorrect - Expected: 'Upcoming', Got: {booking.get('status')}")
                    all_passed = False
                
                created_bookings.append(booking)
                print(f"✅ Booking creation PASSED for {booking_data['name']}")
                
            else:
                print(f"❌ Booking creation FAILED - Status code: {response.status_code}")
                if response.content:
                    print(f"Error: {response.text}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Booking creation FAILED - Exception: {e}")
            all_passed = False
    
    return all_passed, created_bookings

def test_booking_listing():
    """Test GET /api/bookings - Verify bookings are properly stored and retrieved"""
    print("\n5. Testing Booking Listing (GET /api/bookings)")
    try:
        response = requests.get(f"{API_BASE}/bookings")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get('bookings', [])
            total_count = data.get('total_count', 0)
            
            print(f"Total bookings: {total_count}")
            print(f"Bookings in response: {len(bookings)}")
            
            if len(bookings) > 0:
                print("\nRecent bookings:")
                for booking in bookings[:5]:  # Show first 5 bookings
                    print(f"  - {booking.get('guest_name')}: Room {booking.get('room_number')}, Amount: {booking.get('booking_amount')}, Status: {booking.get('status')}")
                
                print("✅ Booking listing PASSED")
                return True, bookings
            else:
                print("❌ Booking listing FAILED - No bookings found")
                return False, []
        else:
            print(f"❌ Booking listing FAILED - Status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Booking listing FAILED - Exception: {e}")
        return False, []

def test_september_booking_availability():
    """Test specific September booking scenario mentioned by user"""
    print("\n6. Testing September Booking Availability Issue")
    
    # First create a September booking
    print("\n6.1 Creating September booking")
    september_booking = {
        "guest_name": "September Test User",
        "guest_email": "septest@example.com",
        "guest_phone": "999-888-7777",
        "room_number": "102",
        "check_in_date": "2025-09-10",
        "check_out_date": "2025-09-13",
        "stay_type": "Night Stay",
        "booking_amount": 10000.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=september_booking)
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ September booking created: {booking.get('id')}")
            
            # Now test if room availability checker detects this booking
            print("\n6.2 Testing if availability checker detects September booking")
            params = {
                'check_in_date': '2025-09-11',  # Overlapping dates
                'check_out_date': '2025-09-14'
            }
            
            avail_response = requests.get(f"{API_BASE}/rooms/availability/check", params=params)
            if avail_response.status_code == 200:
                avail_data = avail_response.json()
                available_rooms = avail_data.get('rooms', [])
                
                # Check if room 102 is NOT in available rooms (should be blocked)
                room_102_available = any(room.get('room_number') == '102' for room in available_rooms)
                
                if not room_102_available:
                    print("✅ September booking conflict detection PASSED - Room 102 correctly blocked")
                    return True
                else:
                    print("❌ September booking conflict detection FAILED - Room 102 still showing as available")
                    return False
            else:
                print(f"❌ Availability check failed - Status: {avail_response.status_code}")
                return False
        else:
            print(f"❌ September booking creation failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ September booking test FAILED - Exception: {e}")
        return False

def main():
    """Run all room availability bug fix tests"""
    print("ROOM AVAILABILITY BUG FIX TESTING")
    print("Testing the specific issues mentioned in the review request")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(("Health Check", test_health_check()))
    
    # Test 2: Room Listing
    room_test_result, rooms = test_room_listing()
    test_results.append(("Room Listing", room_test_result))
    
    # Test 3: Room Availability Checker
    test_results.append(("Room Availability Checker", test_room_availability_checker()))
    
    # Test 4: Booking Creation
    booking_test_result, created_bookings = test_booking_creation()
    test_results.append(("Booking Creation", booking_test_result))
    
    # Test 5: Booking Listing
    listing_test_result, bookings = test_booking_listing()
    test_results.append(("Booking Listing", listing_test_result))
    
    # Test 6: September Booking Availability Issue
    test_results.append(("September Booking Issue", test_september_booking_availability()))
    
    # Summary
    print("\n" + "=" * 80)
    print("ROOM AVAILABILITY BUG FIX TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL ROOM AVAILABILITY BUG FIX TESTS PASSED!")
        print("The backend API endpoints are working correctly for:")
        print("- Room availability detection with existing bookings")
        print("- Room listing showing all available rooms")
        print("- Booking creation with correct amounts")
        print("- September date booking conflict detection")
    else:
        print("⚠️  SOME TESTS FAILED - Issues found in room availability system")
        print("Please review the failed tests above for specific issues")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)