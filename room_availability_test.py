#!/usr/bin/env python3
"""
Room Availability Checker API Testing
Tests the room availability endpoint as specified in the review request.
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

print(f"Testing Room Availability Checker API at: {API_BASE}")
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

def test_room_availability_valid_dates():
    """Test room availability checker with valid dates"""
    print("\n2. Testing Room Availability with Valid Dates")
    
    # Use future dates for testing
    check_in = (datetime.now().date() + timedelta(days=7)).strftime('%Y-%m-%d')
    check_out = (datetime.now().date() + timedelta(days=9)).strftime('%Y-%m-%d')
    
    print(f"Testing availability from {check_in} to {check_out}")
    
    try:
        response = requests.get(f"{API_BASE}/rooms/availability/check", params={
            'check_in_date': check_in,
            'check_out_date': check_out
        })
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response received with {len(str(data))} characters")
            
            # Verify response structure includes required fields
            required_fields = ['check_in_date', 'check_out_date', 'stay_duration', 'total_rooms', 'available_rooms', 'rooms']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            print(f"✅ All required response fields present")
            print(f"Check-in Date: {data['check_in_date']}")
            print(f"Check-out Date: {data['check_out_date']}")
            print(f"Stay Duration: {data['stay_duration']} nights")
            print(f"Total Rooms: {data['total_rooms']}")
            print(f"Available Rooms: {data['available_rooms']}")
            
            # Verify room data structure
            if data['rooms']:
                sample_room = data['rooms'][0]
                required_room_fields = ['id', 'room_number', 'room_type', 'price_per_night', 'max_occupancy', 'amenities']
                missing_room_fields = [field for field in required_room_fields if field not in sample_room]
                
                if missing_room_fields:
                    print(f"❌ Missing required room fields: {missing_room_fields}")
                    return False
                
                print(f"✅ Room data structure verified")
                print(f"Sample room: {sample_room['room_number']} - {sample_room['room_type']} - LKR {sample_room['price_per_night']}/night")
                print(f"Max Occupancy: {sample_room['max_occupancy']}, Amenities: {len(sample_room['amenities'])}")
                
                # Verify stay duration calculation
                expected_duration = (datetime.strptime(check_out, '%Y-%m-%d').date() - 
                                   datetime.strptime(check_in, '%Y-%m-%d').date()).days
                
                if data['stay_duration'] == expected_duration:
                    print(f"✅ Stay duration calculation correct: {expected_duration} nights")
                    print("✅ Room availability with valid dates PASSED")
                    return True
                else:
                    print(f"❌ Stay duration calculation incorrect. Expected: {expected_duration}, Got: {data['stay_duration']}")
                    return False
            else:
                print("⚠️ No available rooms found - this might be expected if all rooms are booked")
                print("✅ Room availability endpoint structure PASSED (empty rooms array is valid)")
                return True
                
        else:
            print(f"❌ Room availability FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Room availability test FAILED - Exception: {e}")
        return False

def test_room_availability_invalid_date_formats():
    """Test error handling for invalid date formats"""
    print("\n3. Testing Room Availability with Invalid Date Formats")
    
    invalid_date_tests = [
        ("invalid-date", "2025-07-20", "Invalid check-in date format"),
        ("2025-07-18", "invalid-date", "Invalid check-out date format"),
        ("2025/07/18", "2025/07/20", "Wrong date format (slashes)"),
        ("18-07-2025", "20-07-2025", "Wrong date format (DD-MM-YYYY)"),
        ("", "2025-07-20", "Empty check-in date"),
        ("2025-07-18", "", "Empty check-out date")
    ]
    
    passed_tests = 0
    total_tests = len(invalid_date_tests)
    
    for check_in, check_out, test_description in invalid_date_tests:
        print(f"\nTesting: {test_description}")
        print(f"Check-in: '{check_in}', Check-out: '{check_out}'")
        
        try:
            response = requests.get(f"{API_BASE}/rooms/availability/check", params={
                'check_in_date': check_in,
                'check_out_date': check_out
            })
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Correctly returned 400 for invalid date format")
                passed_tests += 1
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception during test: {e}")
    
    if passed_tests == total_tests:
        print(f"\n✅ Invalid date format handling PASSED ({passed_tests}/{total_tests})")
        return True
    else:
        print(f"\n❌ Invalid date format handling FAILED ({passed_tests}/{total_tests})")
        return False

def test_room_availability_edge_cases():
    """Test edge cases for room availability"""
    print("\n4. Testing Room Availability Edge Cases")
    
    edge_case_tests = []
    
    # Test 1: Check-out date before check-in date
    future_date = datetime.now().date() + timedelta(days=10)
    past_date = datetime.now().date() + timedelta(days=8)
    edge_case_tests.append((
        future_date.strftime('%Y-%m-%d'),
        past_date.strftime('%Y-%m-%d'),
        "Check-out before check-in"
    ))
    
    # Test 2: Check-in date in the past
    past_date = datetime.now().date() - timedelta(days=1)
    future_date = datetime.now().date() + timedelta(days=1)
    edge_case_tests.append((
        past_date.strftime('%Y-%m-%d'),
        future_date.strftime('%Y-%m-%d'),
        "Check-in date in the past"
    ))
    
    # Test 3: Same day check-in and check-out
    same_date = (datetime.now().date() + timedelta(days=5)).strftime('%Y-%m-%d')
    edge_case_tests.append((
        same_date,
        same_date,
        "Same day check-in and check-out"
    ))
    
    passed_tests = 0
    total_tests = len(edge_case_tests)
    
    for check_in, check_out, test_description in edge_case_tests:
        print(f"\nTesting: {test_description}")
        print(f"Check-in: {check_in}, Check-out: {check_out}")
        
        try:
            response = requests.get(f"{API_BASE}/rooms/availability/check", params={
                'check_in_date': check_in,
                'check_out_date': check_out
            })
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 400:
                print("✅ Correctly returned 400 for invalid date range")
                passed_tests += 1
            else:
                print(f"❌ Expected 400, got {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {data}")
                
        except Exception as e:
            print(f"❌ Exception during test: {e}")
    
    if passed_tests == total_tests:
        print(f"\n✅ Edge case handling PASSED ({passed_tests}/{total_tests})")
        return True
    else:
        print(f"\n❌ Edge case handling FAILED ({passed_tests}/{total_tests})")
        return False

def test_room_availability_different_durations():
    """Test room availability for different stay durations"""
    print("\n5. Testing Room Availability for Different Stay Durations")
    
    base_date = datetime.now().date() + timedelta(days=15)
    duration_tests = [
        (1, "1 night stay"),
        (3, "3 nights stay"),
        (7, "1 week stay"),
        (14, "2 weeks stay")
    ]
    
    passed_tests = 0
    total_tests = len(duration_tests)
    
    for duration, test_description in duration_tests:
        check_in = base_date.strftime('%Y-%m-%d')
        check_out = (base_date + timedelta(days=duration)).strftime('%Y-%m-%d')
        
        print(f"\nTesting: {test_description}")
        print(f"Check-in: {check_in}, Check-out: {check_out}")
        
        try:
            response = requests.get(f"{API_BASE}/rooms/availability/check", params={
                'check_in_date': check_in,
                'check_out_date': check_out
            })
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data['stay_duration'] == duration:
                    print(f"✅ Stay duration correctly calculated: {duration} nights")
                    print(f"Available rooms: {data['available_rooms']}/{data['total_rooms']}")
                    passed_tests += 1
                else:
                    print(f"❌ Stay duration incorrect. Expected: {duration}, Got: {data['stay_duration']}")
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Exception during test: {e}")
        
        # Add small delay between requests
        base_date += timedelta(days=20)
    
    if passed_tests == total_tests:
        print(f"\n✅ Different duration testing PASSED ({passed_tests}/{total_tests})")
        return True
    else:
        print(f"\n❌ Different duration testing FAILED ({passed_tests}/{total_tests})")
        return False

def test_room_availability_response_consistency():
    """Test that room availability responses are consistent"""
    print("\n6. Testing Room Availability Response Consistency")
    
    # Make the same request multiple times to ensure consistency
    check_in = (datetime.now().date() + timedelta(days=30)).strftime('%Y-%m-%d')
    check_out = (datetime.now().date() + timedelta(days=32)).strftime('%Y-%m-%d')
    
    print(f"Making multiple requests for {check_in} to {check_out}")
    
    responses = []
    
    try:
        for i in range(3):
            response = requests.get(f"{API_BASE}/rooms/availability/check", params={
                'check_in_date': check_in,
                'check_out_date': check_out
            })
            
            if response.status_code == 200:
                responses.append(response.json())
            else:
                print(f"❌ Request {i+1} failed with status code: {response.status_code}")
                return False
        
        # Compare responses for consistency
        if len(responses) == 3:
            first_response = responses[0]
            
            consistent = True
            for i, response in enumerate(responses[1:], 2):
                if (response['total_rooms'] != first_response['total_rooms'] or
                    response['available_rooms'] != first_response['available_rooms'] or
                    response['stay_duration'] != first_response['stay_duration']):
                    print(f"❌ Response {i} inconsistent with first response")
                    consistent = False
            
            if consistent:
                print("✅ All responses are consistent")
                print(f"Total rooms: {first_response['total_rooms']}")
                print(f"Available rooms: {first_response['available_rooms']}")
                print(f"Stay duration: {first_response['stay_duration']} nights")
                return True
            else:
                print("❌ Responses are inconsistent")
                return False
        else:
            print("❌ Could not get all responses")
            return False
            
    except Exception as e:
        print(f"❌ Consistency test FAILED - Exception: {e}")
        return False

def main():
    """Run all room availability checker tests"""
    print("Starting Room Availability Checker API Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(("Health Check", test_health_check()))
    
    # Test 2: Valid Dates
    test_results.append(("Valid Dates", test_room_availability_valid_dates()))
    
    # Test 3: Invalid Date Formats
    test_results.append(("Invalid Date Formats", test_room_availability_invalid_date_formats()))
    
    # Test 4: Edge Cases
    test_results.append(("Edge Cases", test_room_availability_edge_cases()))
    
    # Test 5: Different Durations
    test_results.append(("Different Durations", test_room_availability_different_durations()))
    
    # Test 6: Response Consistency
    test_results.append(("Response Consistency", test_room_availability_response_consistency()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY - ROOM AVAILABILITY CHECKER")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<25} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Room Availability Checker API is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)