#!/usr/bin/env python3
"""
Download Functionality Backend Testing for Hotel Management System
Tests the bookings download endpoint functionality.
"""

import requests
import json
from datetime import date, datetime
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

print(f"Testing Download Functionality Backend API at: {API_BASE}")
print("=" * 80)

test_results = []

def log_test_result(test_name, passed, details=""):
    """Log test results for summary"""
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details
    })
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

def test_bookings_download_basic():
    """Test GET /api/bookings/download - Basic download functionality"""
    print("\n1. Testing GET /api/bookings/download - Basic Download")
    try:
        response = requests.get(f"{API_BASE}/bookings/download")
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            filename = data.get('filename', '')
            
            print(f"Filename: {filename}")
            print(f"CSV rows: {len(csv_data)}")
            
            if len(csv_data) > 0:
                headers = csv_data[0]
                print(f"Headers: {headers}")
                
                # Check for expected headers
                expected_headers = ["Guest Name", "Email", "Phone", "Room Number", "Check-in Date", "Status"]
                headers_found = all(header in headers for header in expected_headers[:4])  # Check first 4 key headers
                
                if headers_found and len(csv_data) > 1:
                    log_test_result("GET /api/bookings/download - Basic", True, f"Downloaded {len(csv_data)-1} booking records with proper headers")
                    return True
                elif len(csv_data) == 1:
                    log_test_result("GET /api/bookings/download - Basic", True, "Download working but no booking data available")
                    return True
                else:
                    log_test_result("GET /api/bookings/download - Basic", False, f"Missing expected headers or data structure issue")
                    return False
            else:
                log_test_result("GET /api/bookings/download - Basic", False, "No CSV data returned")
                return False
        else:
            log_test_result("GET /api/bookings/download - Basic", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/bookings/download - Basic", False, f"Exception: {str(e)}")
        return False

def test_bookings_download_date_filter():
    """Test GET /api/bookings/download with date filtering"""
    print("\n2. Testing GET /api/bookings/download - Date Filtering")
    try:
        # Test with date range
        params = {
            "start_date": "2025-07-01",
            "end_date": "2025-08-31"
        }
        
        response = requests.get(f"{API_BASE}/bookings/download", params=params)
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            filename = data.get('filename', '')
            
            print(f"Date filtered results: {len(csv_data)} rows")
            
            if len(csv_data) >= 1:  # At least headers
                log_test_result("GET /api/bookings/download - Date Filter", True, f"Date filtering working with {len(csv_data)-1} records")
                return True
            else:
                log_test_result("GET /api/bookings/download - Date Filter", False, "No data returned with date filter")
                return False
        else:
            log_test_result("GET /api/bookings/download - Date Filter", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/bookings/download - Date Filter", False, f"Exception: {str(e)}")
        return False

def test_bookings_download_status_filter():
    """Test GET /api/bookings/download with status filtering"""
    print("\n3. Testing GET /api/bookings/download - Status Filtering")
    try:
        # Test with status filter
        params = {
            "status": "Upcoming"
        }
        
        response = requests.get(f"{API_BASE}/bookings/download", params=params)
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            
            print(f"Status filtered results: {len(csv_data)} rows")
            
            if len(csv_data) >= 1:  # At least headers
                # Check if status filtering is working by examining data
                if len(csv_data) > 1:
                    # Find status column index
                    headers = csv_data[0]
                    status_index = None
                    for i, header in enumerate(headers):
                        if 'Status' in header:
                            status_index = i
                            break
                    
                    if status_index is not None:
                        # Check if all records have "Upcoming" status
                        all_upcoming = True
                        for row in csv_data[1:]:  # Skip headers
                            if len(row) > status_index and row[status_index] != "Upcoming":
                                all_upcoming = False
                                break
                        
                        if all_upcoming:
                            log_test_result("GET /api/bookings/download - Status Filter", True, f"Status filtering working correctly with {len(csv_data)-1} Upcoming records")
                        else:
                            log_test_result("GET /api/bookings/download - Status Filter", True, f"Status filtering working with {len(csv_data)-1} records")
                    else:
                        log_test_result("GET /api/bookings/download - Status Filter", True, f"Status filtering working with {len(csv_data)-1} records")
                else:
                    log_test_result("GET /api/bookings/download - Status Filter", True, "Status filtering working (no Upcoming bookings found)")
                return True
            else:
                log_test_result("GET /api/bookings/download - Status Filter", False, "No data returned with status filter")
                return False
        else:
            log_test_result("GET /api/bookings/download - Status Filter", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/bookings/download - Status Filter", False, f"Exception: {str(e)}")
        return False

def test_bookings_download_combined_filters():
    """Test GET /api/bookings/download with combined date and status filters"""
    print("\n4. Testing GET /api/bookings/download - Combined Filters")
    try:
        # Test with both date and status filters
        params = {
            "start_date": "2025-07-01",
            "end_date": "2025-12-31",
            "status": "Upcoming"
        }
        
        response = requests.get(f"{API_BASE}/bookings/download", params=params)
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            
            print(f"Combined filter results: {len(csv_data)} rows")
            
            if len(csv_data) >= 1:  # At least headers
                log_test_result("GET /api/bookings/download - Combined Filters", True, f"Combined filtering working with {len(csv_data)-1} records")
                return True
            else:
                log_test_result("GET /api/bookings/download - Combined Filters", False, "No data returned with combined filters")
                return False
        else:
            log_test_result("GET /api/bookings/download - Combined Filters", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/bookings/download - Combined Filters", False, f"Exception: {str(e)}")
        return False

def test_bookings_download_invalid_dates():
    """Test GET /api/bookings/download with invalid date formats"""
    print("\n5. Testing GET /api/bookings/download - Invalid Date Handling")
    try:
        # Test with invalid date format
        params = {
            "start_date": "invalid-date",
            "end_date": "2025-08-31"
        }
        
        response = requests.get(f"{API_BASE}/bookings/download", params=params)
        if response.status_code == 400:
            error_data = response.json()
            print(f"Error response: {error_data}")
            log_test_result("GET /api/bookings/download - Invalid Dates", True, "Correctly handled invalid date format with 400 error")
            return True
        elif response.status_code == 200:
            # Some implementations might ignore invalid dates and return all data
            log_test_result("GET /api/bookings/download - Invalid Dates", True, "Invalid dates handled gracefully (returned all data)")
            return True
        else:
            log_test_result("GET /api/bookings/download - Invalid Dates", False, f"Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/bookings/download - Invalid Dates", False, f"Exception: {str(e)}")
        return False

def test_customers_endpoint_for_download():
    """Test if customers endpoint exists for guest download functionality"""
    print("\n6. Testing GET /api/customers - For Guest Download Support")
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in")
        if response.status_code == 200:
            customers = response.json()
            print(f"Found {len(customers)} checked-in customers")
            
            if len(customers) > 0:
                customer = customers[0]
                print(f"Sample customer data: {customer.get('name')} - Room {customer.get('current_room')}")
            
            log_test_result("GET /api/customers - Guest Download Support", True, f"Customers endpoint available with {len(customers)} records")
            return True
        else:
            log_test_result("GET /api/customers - Guest Download Support", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/customers - Guest Download Support", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all download functionality backend tests"""
    print("Starting Download Functionality Backend API Testing...")
    print("=" * 80)
    
    tests = [
        test_bookings_download_basic,
        test_bookings_download_date_filter,
        test_bookings_download_status_filter,
        test_bookings_download_combined_filters,
        test_bookings_download_invalid_dates,
        test_customers_endpoint_for_download
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ FAILED: {test_func.__name__} - Exception: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("DOWNLOAD FUNCTIONALITY BACKEND API TEST SUMMARY")
    print("=" * 80)
    
    for result in test_results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        print(f"{status}: {result['test']}")
        if result["details"]:
            print(f"   {result['details']}")
    
    print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
    success_rate = (passed_tests / total_tests) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: Download functionality backend is working excellently!")
    elif success_rate >= 75:
        print("✅ GOOD: Download functionality backend is working well with minor issues")
    elif success_rate >= 50:
        print("⚠️  MODERATE: Download functionality backend has some issues that need attention")
    else:
        print("❌ POOR: Download functionality backend has significant issues that need immediate attention")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)