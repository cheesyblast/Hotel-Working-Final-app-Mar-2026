#!/usr/bin/env python3
"""
Room Availability Validation Fix Test for Hotel Management System
Tests the newly implemented room availability validation fix to ensure:
1. Room availability validation is working
2. Double bookings are prevented
3. Proper error messages are returned for conflicts
4. Past date booking functionality still works correctly
5. Both "Upcoming" and "Checked In" status bookings work with availability validation
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

print(f"Testing Room Availability Validation Fix at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
auth_token = None

def authenticate():
    """Authenticate with admin credentials"""
    global auth_token
    print("\n🔐 Authenticating with admin credentials...")
    
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
            print(f"❌ Authentication failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers for API requests"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

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

def setup_test_data():
    """Setup test rooms and clear existing bookings for clean testing"""
    print("\n2. Setting up test data...")
    
    try:
        # Create test rooms if they don't exist
        print("Ensuring test rooms exist...")
        rooms_response = requests.get(f"{API_BASE}/rooms")
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            room_numbers = [room['room_number'] for room in rooms]
            
            # Create test rooms if they don't exist
            test_rooms = [
                {"room_number": "AVTEST101", "room_type": "Double", "price_per_night": 5000.0, "max_occupancy": 2},
                {"room_number": "AVTEST102", "room_type": "Triple", "price_per_night": 7500.0, "max_occupancy": 3},
                {"room_number": "AVTEST103", "room_type": "Suite", "price_per_night": 10000.0, "max_occupancy": 4}
            ]
            
            for room_data in test_rooms:
                if room_data["room_number"] not in room_numbers:
                    create_response = requests.post(f"{API_BASE}/rooms", json=room_data)
                    if create_response.status_code == 200:
                        print(f"✅ Created test room {room_data['room_number']}")
                    else:
                        print(f"⚠️ Could not create room {room_data['room_number']}")
            
            print("✅ Test data setup completed")
            return True
        else:
            print(f"❌ Could not get rooms - Status: {rooms_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test data setup failed - Exception: {e}")
        return False

def test_room_availability_validation():
    """Test that room availability validation prevents double bookings"""
    print("\n3. Testing Room Availability Validation (Core Fix)")
    
    try:
        # Test dates - future dates to avoid past date logic
        today = datetime.now().date()
        check_in_date = today + timedelta(days=7)  # 1 week from now
        check_out_date = today + timedelta(days=9)  # 2 days stay
        
        test_room = "AVTEST101"
        
        print(f"Testing room availability for {test_room} from {check_in_date} to {check_out_date}")
        
        # First booking - should succeed
        print("\n3.1 Creating first booking (should succeed)...")
        first_booking = {
            "guest_name": "John Doe",
            "guest_email": "john@example.com",
            "guest_phone": "+1234567890",
            "room_number": test_room,
            "check_in_date": check_in_date.isoformat(),
            "check_out_date": check_out_date.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 10000.0,
            "booking_status": "Upcoming"
        }
        
        response1 = requests.post(f"{API_BASE}/bookings", json=first_booking, headers=get_auth_headers())
        print(f"First booking status: {response1.status_code}")
        
        if response1.status_code == 200:
            booking1_data = response1.json()
            booking1_id = booking1_data.get('id')
            print(f"✅ First booking created successfully - ID: {booking1_id}")
            
            # Second booking - should fail due to conflict
            print("\n3.2 Creating conflicting booking (should fail)...")
            second_booking = {
                "guest_name": "Jane Smith",
                "guest_email": "jane@example.com", 
                "guest_phone": "+1987654321",
                "room_number": test_room,
                "check_in_date": check_in_date.isoformat(),
                "check_out_date": check_out_date.isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 10000.0,
                "booking_status": "Upcoming"
            }
            
            response2 = requests.post(f"{API_BASE}/bookings", json=second_booking, headers=get_auth_headers())
            print(f"Second booking status: {response2.status_code}")
            
            if response2.status_code == 400:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                print(f"✅ Second booking correctly rejected with error: {error_message}")
                
                # Verify error message contains room conflict information
                if test_room in error_message and "already booked" in error_message.lower():
                    print("✅ Error message contains proper conflict details")
                    return True
                else:
                    print(f"❌ Error message doesn't contain expected conflict details: {error_message}")
                    return False
            else:
                print(f"❌ Second booking should have been rejected but got status: {response2.status_code}")
                if response2.status_code == 200:
                    print("❌ CRITICAL: Double booking was allowed! Room availability validation is not working.")
                return False
        else:
            print(f"❌ First booking failed - Status: {response1.status_code}")
            print(f"Response: {response1.text}")
            return False
            
    except Exception as e:
        print(f"❌ Room availability validation test failed - Exception: {e}")
        return False

def test_overlapping_date_conflicts():
    """Test various overlapping date scenarios"""
    print("\n4. Testing Overlapping Date Conflict Detection")
    
    try:
        today = datetime.now().date()
        base_check_in = today + timedelta(days=10)
        base_check_out = today + timedelta(days=12)
        test_room = "AVTEST102"
        
        # Create base booking
        print(f"4.1 Creating base booking for {test_room} from {base_check_in} to {base_check_out}")
        base_booking = {
            "guest_name": "Base Guest",
            "guest_email": "base@example.com",
            "room_number": test_room,
            "check_in_date": base_check_in.isoformat(),
            "check_out_date": base_check_out.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 15000.0,
            "booking_status": "Upcoming"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=base_booking, headers=get_auth_headers())
        if response.status_code != 200:
            print(f"❌ Could not create base booking - Status: {response.status_code}")
            return False
        
        print("✅ Base booking created")
        
        # Test different overlap scenarios
        overlap_scenarios = [
            {
                "name": "Starts during existing booking",
                "check_in": base_check_in + timedelta(days=1),
                "check_out": base_check_out + timedelta(days=1)
            },
            {
                "name": "Ends during existing booking", 
                "check_in": base_check_in - timedelta(days=1),
                "check_out": base_check_out - timedelta(days=1)
            },
            {
                "name": "Encompasses existing booking",
                "check_in": base_check_in - timedelta(days=1),
                "check_out": base_check_out + timedelta(days=1)
            },
            {
                "name": "Same exact dates",
                "check_in": base_check_in,
                "check_out": base_check_out
            }
        ]
        
        all_conflicts_detected = True
        
        for i, scenario in enumerate(overlap_scenarios):
            print(f"\n4.{i+2} Testing: {scenario['name']}")
            conflict_booking = {
                "guest_name": f"Conflict Guest {i+1}",
                "guest_email": f"conflict{i+1}@example.com",
                "room_number": test_room,
                "check_in_date": scenario['check_in'].isoformat(),
                "check_out_date": scenario['check_out'].isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 15000.0,
                "booking_status": "Upcoming"
            }
            
            conflict_response = requests.post(f"{API_BASE}/bookings", json=conflict_booking, headers=get_auth_headers())
            
            if conflict_response.status_code == 400:
                error_data = conflict_response.json()
                print(f"✅ Conflict correctly detected: {error_data.get('detail', '')}")
            else:
                print(f"❌ Conflict NOT detected - Status: {conflict_response.status_code}")
                all_conflicts_detected = False
        
        return all_conflicts_detected
        
    except Exception as e:
        print(f"❌ Overlapping date conflict test failed - Exception: {e}")
        return False

def test_past_date_booking_with_validation():
    """Test that past date bookings still work with validation"""
    print("\n5. Testing Past Date Booking with Validation")
    
    try:
        today = datetime.now().date()
        past_date = today - timedelta(days=5)
        test_room = "AVTEST103"
        
        # Test past date booking with "Upcoming" status
        print("5.1 Testing past date booking with 'Upcoming' status...")
        past_booking_upcoming = {
            "guest_name": "Past Guest Upcoming",
            "guest_email": "pastupcoming@example.com",
            "room_number": test_room,
            "check_in_date": past_date.isoformat(),
            "check_out_date": past_date.isoformat(),
            "stay_type": "Short Time",
            "booking_amount": 5000.0,
            "booking_status": "Upcoming"
        }
        
        response1 = requests.post(f"{API_BASE}/bookings", json=past_booking_upcoming, headers=get_auth_headers())
        
        if response1.status_code == 200:
            print("✅ Past date booking with 'Upcoming' status created successfully")
            
            # Test past date booking with "Checked In" status (different date to avoid conflict)
            print("5.2 Testing past date booking with 'Checked In' status...")
            past_booking_checkedin = {
                "guest_name": "Past Guest Checked In",
                "guest_email": "pastcheckedin@example.com",
                "room_number": test_room,
                "check_in_date": (past_date - timedelta(days=2)).isoformat(),
                "check_out_date": (past_date - timedelta(days=2)).isoformat(),
                "stay_type": "Short Time",
                "booking_amount": 5000.0,
                "booking_status": "Checked In"
            }
            
            response2 = requests.post(f"{API_BASE}/bookings", json=past_booking_checkedin, headers=get_auth_headers())
            
            if response2.status_code == 200:
                print("✅ Past date booking with 'Checked In' status created successfully")
                
                # Verify room status was updated for checked-in booking
                rooms_response = requests.get(f"{API_BASE}/rooms")
                if rooms_response.status_code == 200:
                    rooms = rooms_response.json()
                    test_room_data = next((r for r in rooms if r['room_number'] == test_room), None)
                    
                    if test_room_data and test_room_data.get('status') == 'Occupied':
                        print("✅ Room status correctly updated to 'Occupied' for checked-in booking")
                        return True
                    else:
                        print(f"❌ Room status not updated correctly. Current status: {test_room_data.get('status') if test_room_data else 'Room not found'}")
                        return False
                else:
                    print("❌ Could not verify room status")
                    return False
            else:
                print(f"❌ Past date booking with 'Checked In' status failed - Status: {response2.status_code}")
                return False
        else:
            print(f"❌ Past date booking with 'Upcoming' status failed - Status: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Past date booking test failed - Exception: {e}")
        return False

def test_room_existence_validation():
    """Test that bookings for non-existent rooms are rejected"""
    print("\n6. Testing Room Existence Validation")
    
    try:
        today = datetime.now().date()
        future_date = today + timedelta(days=15)
        non_existent_room = "NONEXISTENT999"
        
        print(f"6.1 Testing booking for non-existent room: {non_existent_room}")
        
        invalid_room_booking = {
            "guest_name": "Invalid Room Guest",
            "guest_email": "invalid@example.com",
            "room_number": non_existent_room,
            "check_in_date": future_date.isoformat(),
            "check_out_date": (future_date + timedelta(days=1)).isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 5000.0,
            "booking_status": "Upcoming"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=invalid_room_booking, headers=get_auth_headers())
        
        if response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('detail', '')
            print(f"✅ Non-existent room booking correctly rejected: {error_message}")
            
            if "does not exist" in error_message.lower():
                print("✅ Error message correctly indicates room doesn't exist")
                return True
            else:
                print(f"❌ Error message doesn't indicate room existence issue: {error_message}")
                return False
        else:
            print(f"❌ Non-existent room booking should have been rejected but got status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Room existence validation test failed - Exception: {e}")
        return False

def test_occupied_room_validation():
    """Test that bookings for currently occupied rooms are handled correctly"""
    print("\n7. Testing Occupied Room Validation")
    
    try:
        # Use a different room to avoid conflicts with previous tests
        today = datetime.now().date()
        past_date = today - timedelta(days=2)
        future_checkout = today + timedelta(days=3)
        test_room = "AVTEST101"  # Reuse room but with different dates
        
        print("7.1 Creating a checked-in booking to occupy the room...")
        occupied_booking = {
            "guest_name": "Occupying Guest",
            "guest_email": "occupying@example.com",
            "room_number": test_room,
            "check_in_date": past_date.isoformat(),
            "check_out_date": future_checkout.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 10000.0,
            "booking_status": "Checked In"
        }
        
        response1 = requests.post(f"{API_BASE}/bookings", json=occupied_booking, headers=get_auth_headers())
        
        if response1.status_code == 200:
            print("✅ Room occupation booking created")
            
            # Now try to book the same room for dates that overlap with the occupation
            print("7.2 Testing booking for occupied room with overlapping dates...")
            conflicting_booking = {
                "guest_name": "Conflicting Guest",
                "guest_email": "conflicting@example.com",
                "room_number": test_room,
                "check_in_date": today.isoformat(),
                "check_out_date": (today + timedelta(days=1)).isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 10000.0,
                "booking_status": "Upcoming"
            }
            
            response2 = requests.post(f"{API_BASE}/bookings", json=conflicting_booking, headers=get_auth_headers())
            
            if response2.status_code == 400:
                error_data = response2.json()
                error_message = error_data.get('detail', '')
                print(f"✅ Occupied room booking correctly rejected: {error_message}")
                
                if "already booked" in error_message.lower() or "occupied" in error_message.lower():
                    print("✅ Error message correctly indicates room conflict")
                    return True
                else:
                    print(f"❌ Error message doesn't clearly indicate room conflict: {error_message}")
                    return False
            else:
                print(f"❌ Occupied room booking should have been rejected but got status: {response2.status_code}")
                return False
        else:
            print(f"❌ Could not create room occupation booking - Status: {response1.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Occupied room validation test failed - Exception: {e}")
        return False

def main():
    """Run all room availability validation tests"""
    print("Starting Room Availability Validation Fix Tests")
    print("=" * 80)
    
    test_results = []
    
    # Authentication
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return False
    
    # Test 1: Health Check
    test_results.append(("API Health Check", test_health_check()))
    
    # Test 2: Setup Test Data
    test_results.append(("Test Data Setup", setup_test_data()))
    
    # Test 3: Core Room Availability Validation
    test_results.append(("Room Availability Validation", test_room_availability_validation()))
    
    # Test 4: Overlapping Date Conflicts
    test_results.append(("Overlapping Date Conflicts", test_overlapping_date_conflicts()))
    
    # Test 5: Past Date Booking with Validation
    test_results.append(("Past Date Booking with Validation", test_past_date_booking_with_validation()))
    
    # Test 6: Room Existence Validation
    test_results.append(("Room Existence Validation", test_room_existence_validation()))
    
    # Test 7: Occupied Room Validation
    test_results.append(("Occupied Room Validation", test_occupied_room_validation()))
    
    # Summary
    print("\n" + "=" * 80)
    print("ROOM AVAILABILITY VALIDATION FIX TEST SUMMARY")
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
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Room availability validation is working correctly")
        print("✅ Double bookings are prevented")
        print("✅ Proper error messages are returned")
        print("✅ Past date booking functionality works with validation")
        print("✅ Both 'Upcoming' and 'Checked In' status bookings work correctly")
        print("✅ CRITICAL ISSUE RESOLVED: Room availability validation fix is working!")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed.")
        print("❌ Room availability validation may have issues that need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)