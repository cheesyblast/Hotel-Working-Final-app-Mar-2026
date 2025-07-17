#!/usr/bin/env python3
"""
Comprehensive Backend API Health Check for Hotel Management System
Tests ALL endpoints as specified in the review request including recent updates:
- Room availability checker
- Booking pagination, search, and CSV download
- All CRUD operations and error handling
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import os
import time

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

print(f"🏨 COMPREHENSIVE HOTEL MANAGEMENT API HEALTH CHECK")
print(f"Testing API at: {API_BASE}")
print("=" * 80)

# Global test results
test_results = []

def add_test_result(test_name, passed, details=""):
    """Add test result to global results list"""
    test_results.append({
        "name": test_name,
        "passed": passed,
        "details": details
    })
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status} - {test_name}")
    if details and not passed:
        print(f"   Details: {details}")

# ============================================================================
# 1. CORE HEALTH CHECK
# ============================================================================

def test_health_endpoint():
    """Test /api/ endpoint - Basic health check"""
    print("\n🔍 1. CORE HEALTH CHECK")
    print("-" * 40)
    
    try:
        response = requests.get(f"{API_BASE}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Hotel Management API":
                add_test_result("Health Endpoint", True)
                return True
            else:
                add_test_result("Health Endpoint", False, f"Unexpected response: {data}")
                return False
        else:
            add_test_result("Health Endpoint", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Health Endpoint", False, f"Exception: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity by initializing sample data"""
    print("\nTesting Database Connectivity...")
    
    try:
        response = requests.post(f"{API_BASE}/init-data", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "Sample data" in data.get("message", ""):
                add_test_result("Database Connectivity", True)
                return True
            else:
                add_test_result("Database Connectivity", False, f"Unexpected response: {data}")
                return False
        else:
            add_test_result("Database Connectivity", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Database Connectivity", False, f"Exception: {e}")
        return False

# ============================================================================
# 2. ROOM MANAGEMENT
# ============================================================================

def test_room_management():
    """Test room management endpoints"""
    print("\n🏠 2. ROOM MANAGEMENT")
    print("-" * 40)
    
    # Test GET /api/rooms
    try:
        response = requests.get(f"{API_BASE}/rooms", timeout=10)
        
        if response.status_code == 200:
            rooms = response.json()
            if len(rooms) >= 10:
                add_test_result("GET /api/rooms", True, f"Retrieved {len(rooms)} rooms")
                
                # Test room creation
                test_room_creation()
                
                # Test room availability checker
                test_room_availability_checker()
                
                return True
            else:
                add_test_result("GET /api/rooms", False, f"Expected ≥10 rooms, got {len(rooms)}")
                return False
        else:
            add_test_result("GET /api/rooms", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("GET /api/rooms", False, f"Exception: {e}")
        return False

def test_room_creation():
    """Test room creation endpoint"""
    print("\nTesting Room Creation...")
    
    try:
        new_room = {
            "room_number": "TEST001",
            "room_type": "Double",
            "price_per_night": 7500.0,
            "max_occupancy": 2,
            "amenities": ["WiFi", "TV", "AC"]
        }
        
        response = requests.post(f"{API_BASE}/rooms", json=new_room, timeout=10)
        
        if response.status_code == 200:
            room_data = response.json()
            if room_data.get("room_number") == "TEST001":
                add_test_result("Room Creation", True)
                
                # Clean up - delete the test room
                try:
                    requests.delete(f"{API_BASE}/rooms/{room_data.get('id')}", timeout=10)
                except:
                    pass  # Ignore cleanup errors
                
                return True
            else:
                add_test_result("Room Creation", False, "Room data mismatch")
                return False
        else:
            add_test_result("Room Creation", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Room Creation", False, f"Exception: {e}")
        return False

def test_room_availability_checker():
    """Test the new room availability checker endpoint"""
    print("\nTesting Room Availability Checker...")
    
    try:
        # Test with future dates
        check_in = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        check_out = (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')
        
        response = requests.get(
            f"{API_BASE}/rooms/availability/check?check_in_date={check_in}&check_out_date={check_out}",
            timeout=10
        )
        
        if response.status_code == 200:
            availability_data = response.json()
            required_fields = ['check_in_date', 'check_out_date', 'stay_duration', 'total_rooms', 'available_rooms', 'rooms']
            
            if all(field in availability_data for field in required_fields):
                add_test_result("Room Availability Checker", True, 
                              f"Found {availability_data['available_rooms']}/{availability_data['total_rooms']} available rooms")
                return True
            else:
                missing_fields = [f for f in required_fields if f not in availability_data]
                add_test_result("Room Availability Checker", False, f"Missing fields: {missing_fields}")
                return False
        else:
            add_test_result("Room Availability Checker", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Room Availability Checker", False, f"Exception: {e}")
        return False

# ============================================================================
# 3. BOOKING MANAGEMENT
# ============================================================================

def test_booking_management():
    """Test booking management endpoints with new features"""
    print("\n📅 3. BOOKING MANAGEMENT")
    print("-" * 40)
    
    # Test enhanced GET /api/bookings with pagination
    test_booking_pagination()
    
    # Test booking creation
    test_booking_creation()
    
    # Test GET /api/bookings/upcoming
    test_upcoming_bookings()
    
    # Test CSV download endpoint
    test_booking_csv_download()
    
    # Test search and filtering
    test_booking_search_filtering()

def test_booking_pagination():
    """Test GET /api/bookings with pagination"""
    print("\nTesting Booking Pagination...")
    
    try:
        # Test basic pagination
        response = requests.get(f"{API_BASE}/bookings?page=1&limit=5", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['bookings', 'total_count', 'page', 'limit', 'total_pages']
            
            if all(field in data for field in required_fields):
                add_test_result("Booking Pagination", True, 
                              f"Page 1: {len(data['bookings'])} bookings, Total: {data['total_count']}")
                return True
            else:
                missing_fields = [f for f in required_fields if f not in data]
                add_test_result("Booking Pagination", False, f"Missing fields: {missing_fields}")
                return False
        else:
            add_test_result("Booking Pagination", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Booking Pagination", False, f"Exception: {e}")
        return False

def test_booking_creation():
    """Test booking creation"""
    print("\nTesting Booking Creation...")
    
    try:
        new_booking = {
            "guest_name": "Test Guest",
            "guest_email": "test@example.com",
            "guest_phone": "123-456-7890",
            "guest_id_passport": "TEST123",
            "guest_country": "Test Country",
            "room_number": "101",
            "check_in_date": (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d'),
            "check_out_date": (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 15000.0,
            "additional_notes": "Test booking"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=new_booking, timeout=10)
        
        if response.status_code == 200:
            booking_data = response.json()
            if booking_data.get("guest_name") == "Test Guest":
                add_test_result("Booking Creation", True)
                return True
            else:
                add_test_result("Booking Creation", False, "Booking data mismatch")
                return False
        else:
            add_test_result("Booking Creation", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Booking Creation", False, f"Exception: {e}")
        return False

def test_upcoming_bookings():
    """Test GET /api/bookings/upcoming"""
    print("\nTesting Upcoming Bookings...")
    
    try:
        response = requests.get(f"{API_BASE}/bookings/upcoming", timeout=10)
        
        if response.status_code == 200:
            bookings = response.json()
            add_test_result("Upcoming Bookings", True, f"Retrieved {len(bookings)} upcoming bookings")
            return True
        else:
            add_test_result("Upcoming Bookings", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Upcoming Bookings", False, f"Exception: {e}")
        return False

def test_booking_csv_download():
    """Test the new CSV download endpoint"""
    print("\nTesting Booking CSV Download...")
    
    try:
        response = requests.get(f"{API_BASE}/bookings/download", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'filename' in data:
                csv_data = data['data']
                if len(csv_data) > 0 and isinstance(csv_data[0], list):  # Should have headers
                    add_test_result("Booking CSV Download", True, f"Generated CSV with {len(csv_data)} rows")
                    return True
                else:
                    add_test_result("Booking CSV Download", False, "Invalid CSV data format")
                    return False
            else:
                add_test_result("Booking CSV Download", False, "Missing data or filename in response")
                return False
        else:
            add_test_result("Booking CSV Download", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Booking CSV Download", False, f"Exception: {e}")
        return False

def test_booking_search_filtering():
    """Test search and filtering functionality"""
    print("\nTesting Booking Search and Filtering...")
    
    try:
        # Test search functionality
        response = requests.get(f"{API_BASE}/bookings?search=Alice&page=1&limit=10", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            search_results = data.get('bookings', [])
            
            # Test status filtering
            status_response = requests.get(f"{API_BASE}/bookings?status=Upcoming&page=1&limit=10", timeout=10)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_results = status_data.get('bookings', [])
                
                add_test_result("Booking Search & Filtering", True, 
                              f"Search: {len(search_results)} results, Status filter: {len(status_results)} results")
                return True
            else:
                add_test_result("Booking Search & Filtering", False, f"Status filter failed: {status_response.status_code}")
                return False
        else:
            add_test_result("Booking Search & Filtering", False, f"Search failed: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Booking Search & Filtering", False, f"Exception: {e}")
        return False

# ============================================================================
# 4. CUSTOMER MANAGEMENT
# ============================================================================

def test_customer_management():
    """Test customer management endpoints"""
    print("\n👥 4. CUSTOMER MANAGEMENT")
    print("-" * 40)
    
    # Test GET /api/customers/checked-in
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", timeout=10)
        
        if response.status_code == 200:
            customers = response.json()
            add_test_result("GET Checked-in Customers", True, f"Retrieved {len(customers)} customers")
            
            # Test check-in and checkout functionality
            test_checkin_checkout_functionality()
            
            return True
        else:
            add_test_result("GET Checked-in Customers", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("GET Checked-in Customers", False, f"Exception: {e}")
        return False

def test_checkin_checkout_functionality():
    """Test check-in and checkout functionality"""
    print("\nTesting Check-in and Checkout Functionality...")
    
    try:
        # First, get upcoming bookings to check someone in
        bookings_response = requests.get(f"{API_BASE}/bookings/upcoming", timeout=10)
        
        if bookings_response.status_code == 200:
            bookings = bookings_response.json()
            
            if bookings:
                # Test check-in
                test_booking = bookings[0]
                checkin_data = {
                    "booking_id": test_booking['id'],
                    "advance_amount": 1000.0,
                    "notes": "Test check-in"
                }
                
                checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, timeout=10)
                
                if checkin_response.status_code == 200:
                    add_test_result("Check-in Functionality", True)
                    
                    # Test checkout
                    checkin_result = checkin_response.json()
                    customer_data = checkin_result.get('customer', {})
                    
                    if customer_data.get('id'):
                        checkout_data = {
                            "customer_id": customer_data['id'],
                            "additional_amount": 500.0,
                            "discount_amount": 100.0,
                            "payment_method": "Cash"
                        }
                        
                        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, timeout=10)
                        
                        if checkout_response.status_code == 200:
                            add_test_result("Checkout Functionality", True)
                            return True
                        else:
                            add_test_result("Checkout Functionality", False, f"Status code: {checkout_response.status_code}")
                            return False
                    else:
                        add_test_result("Checkout Functionality", False, "No customer ID from check-in")
                        return False
                else:
                    add_test_result("Check-in Functionality", False, f"Status code: {checkin_response.status_code}")
                    return False
            else:
                add_test_result("Check-in Functionality", False, "No bookings available for check-in")
                return False
        else:
            add_test_result("Check-in Functionality", False, f"Could not get bookings: {bookings_response.status_code}")
            return False
    except Exception as e:
        add_test_result("Check-in/Checkout Functionality", False, f"Exception: {e}")
        return False

# ============================================================================
# 5. DATA INITIALIZATION
# ============================================================================

def test_data_initialization():
    """Test /api/init-data endpoint"""
    print("\n🗄️ 5. DATA INITIALIZATION")
    print("-" * 40)
    
    try:
        response = requests.post(f"{API_BASE}/init-data", timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if "Sample data" in data.get("message", ""):
                add_test_result("Data Initialization", True)
                return True
            else:
                add_test_result("Data Initialization", False, f"Unexpected response: {data}")
                return False
        else:
            add_test_result("Data Initialization", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        add_test_result("Data Initialization", False, f"Exception: {e}")
        return False

# ============================================================================
# 6. PERFORMANCE AND ERROR HANDLING
# ============================================================================

def test_performance_and_error_handling():
    """Test API response times and error handling"""
    print("\n⚡ 6. PERFORMANCE AND ERROR HANDLING")
    print("-" * 40)
    
    # Test API response times
    test_api_response_times()
    
    # Test error handling
    test_error_handling_scenarios()

def test_api_response_times():
    """Test API response times"""
    print("\nTesting API Response Times...")
    
    endpoints_to_test = [
        ("/", "Health Check"),
        ("/rooms", "Get Rooms"),
        ("/bookings?page=1&limit=10", "Get Bookings"),
        ("/customers/checked-in", "Get Customers")
    ]
    
    response_times = []
    
    for endpoint, name in endpoints_to_test:
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            response_times.append(response_time)
            
            if response.status_code == 200 and response_time < 5000:  # Less than 5 seconds
                print(f"  ✅ {name}: {response_time:.0f}ms")
            else:
                print(f"  ⚠️ {name}: {response_time:.0f}ms (slow or failed)")
        except Exception as e:
            print(f"  ❌ {name}: Failed - {e}")
            response_times.append(10000)  # Mark as very slow
    
    avg_response_time = sum(response_times) / len(response_times)
    
    if avg_response_time < 2000:  # Less than 2 seconds average
        add_test_result("API Response Times", True, f"Average: {avg_response_time:.0f}ms")
        return True
    else:
        add_test_result("API Response Times", False, f"Average: {avg_response_time:.0f}ms (too slow)")
        return False

def test_error_handling_scenarios():
    """Test error handling for invalid requests"""
    print("\nTesting Error Handling Scenarios...")
    
    passed_error_tests = 0
    total_error_tests = 0
    
    # Test invalid room ID
    try:
        response = requests.get(f"{API_BASE}/rooms/invalid-room-id", timeout=10)
        total_error_tests += 1
        if response.status_code == 404:
            print(f"  ✅ Invalid Room ID: Correctly returned {response.status_code}")
            passed_error_tests += 1
        else:
            print(f"  ❌ Invalid Room ID: Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"  ❌ Invalid Room ID: Exception - {e}")
        total_error_tests += 1
    
    # Test invalid customer checkout
    try:
        response = requests.post(f"{API_BASE}/checkout", json={"customer_id": "invalid-id"}, timeout=10)
        total_error_tests += 1
        if response.status_code == 404:
            print(f"  ✅ Invalid Customer Checkout: Correctly returned {response.status_code}")
            passed_error_tests += 1
        else:
            print(f"  ❌ Invalid Customer Checkout: Expected 404, got {response.status_code}")
    except Exception as e:
        print(f"  ❌ Invalid Customer Checkout: Exception - {e}")
        total_error_tests += 1
    
    # Test invalid date format
    try:
        response = requests.get(f"{API_BASE}/rooms/availability/check?check_in_date=invalid&check_out_date=invalid", timeout=10)
        total_error_tests += 1
        if response.status_code == 400:
            print(f"  ✅ Invalid Date Format: Correctly returned {response.status_code}")
            passed_error_tests += 1
        else:
            print(f"  ❌ Invalid Date Format: Expected 400, got {response.status_code}")
    except Exception as e:
        print(f"  ❌ Invalid Date Format: Exception - {e}")
        total_error_tests += 1
    
    if total_error_tests > 0 and passed_error_tests >= total_error_tests * 0.75:  # At least 75% should pass
        add_test_result("Error Handling", True, f"{passed_error_tests}/{total_error_tests} tests passed")
        return True
    else:
        add_test_result("Error Handling", False, f"Only {passed_error_tests}/{total_error_tests} tests passed")
        return False

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

def main():
    """Run comprehensive backend API health check"""
    print("🚀 Starting Comprehensive Backend API Health Check...")
    print("=" * 80)
    
    # Run all test categories
    test_health_endpoint()
    test_database_connectivity()
    test_room_management()
    test_booking_management()
    test_customer_management()
    test_data_initialization()
    test_performance_and_error_handling()
    
    # Generate final summary
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results if result["passed"])
    total_tests = len(test_results)
    
    for result in test_results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{result['name']:<35} {status}")
        if result["details"]:
            print(f"{'':>37} {result['details']}")
    
    print("-" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Hotel Management API is fully functional.")
        return True
    elif passed_tests >= total_tests * 0.9:  # 90% or more
        print(f"\n✅ MOSTLY SUCCESSFUL! {passed_tests}/{total_tests} tests passed.")
        return True
    else:
        print(f"\n⚠️ ISSUES DETECTED! Only {passed_tests}/{total_tests} tests passed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)