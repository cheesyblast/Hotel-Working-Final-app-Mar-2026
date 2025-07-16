#!/usr/bin/env python3
"""
Comprehensive Testing for Updated Bookings API Endpoints
Tests the new pagination, search, status filtering, and CSV download features.
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

print(f"Testing Updated Bookings API at: {API_BASE}")
print("=" * 80)

def setup_test_data():
    """Initialize sample data and create additional test bookings"""
    print("\n🔧 Setting up test data...")
    
    # Initialize sample data
    try:
        response = requests.post(f"{API_BASE}/init-data")
        if response.status_code == 200:
            print("✅ Sample data initialized")
        else:
            print(f"⚠️ Sample data response: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to initialize sample data: {e}")
        return False
    
    # Create additional test bookings with different statuses and guest info
    test_bookings = [
        {
            "guest_name": "Emma Thompson",
            "guest_email": "emma.thompson@email.com",
            "guest_phone": "555-0101",
            "guest_id_passport": "P111222333",
            "guest_country": "Australia",
            "room_number": "103",
            "check_in_date": "2025-08-01",
            "check_out_date": "2025-08-05",
            "stay_type": "Night Stay",
            "booking_amount": 3200.0,
            "additional_notes": "Honeymoon suite requested"
        },
        {
            "guest_name": "Michael Chen",
            "guest_email": "m.chen@business.com",
            "guest_phone": "555-0202",
            "guest_id_passport": "P444555666",
            "guest_country": "Singapore",
            "room_number": "201",
            "check_in_date": "2025-07-25",
            "check_out_date": "2025-07-28",
            "stay_type": "Night Stay",
            "booking_amount": 2700.0,
            "additional_notes": "Business traveler"
        },
        {
            "guest_name": "Sarah Williams",
            "guest_email": "sarah.w@gmail.com",
            "guest_phone": "555-0303",
            "guest_id_passport": "P777888999",
            "guest_country": "New Zealand",
            "room_number": "301",
            "check_in_date": "2025-08-10",
            "check_out_date": "2025-08-12",
            "stay_type": "Short Time",
            "booking_amount": 1500.0,
            "additional_notes": "Weekend getaway"
        },
        {
            "guest_name": "David Rodriguez",
            "guest_email": "david.rodriguez@company.org",
            "guest_phone": "555-0404",
            "guest_id_passport": "P000111222",
            "guest_country": "Mexico",
            "room_number": "202",
            "check_in_date": "2025-07-30",
            "check_out_date": "2025-08-02",
            "stay_type": "Night Stay",
            "booking_amount": 2400.0,
            "additional_notes": "Conference attendee"
        },
        {
            "guest_name": "Lisa Anderson",
            "guest_email": "lisa.anderson@email.net",
            "guest_phone": "555-0505",
            "guest_id_passport": "P333444555",
            "guest_country": "Sweden",
            "room_number": "204",
            "check_in_date": "2025-08-15",
            "check_out_date": "2025-08-20",
            "stay_type": "Night Stay",
            "booking_amount": 4000.0,
            "additional_notes": "Family vacation"
        }
    ]
    
    created_bookings = 0
    for booking_data in test_bookings:
        try:
            response = requests.post(f"{API_BASE}/bookings", json=booking_data)
            if response.status_code == 200:
                created_bookings += 1
            else:
                print(f"⚠️ Failed to create booking for {booking_data['guest_name']}: {response.status_code}")
        except Exception as e:
            print(f"❌ Exception creating booking for {booking_data['guest_name']}: {e}")
    
    print(f"✅ Created {created_bookings} additional test bookings")
    return True

def test_basic_pagination():
    """Test basic pagination functionality"""
    print("\n1. Testing Basic Pagination (GET /api/bookings)")
    
    try:
        # Test page 1 with limit 20 (default)
        print("Testing page=1, limit=20 (default)...")
        response = requests.get(f"{API_BASE}/bookings?page=1&limit=20")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            required_keys = ['bookings', 'total_count', 'page', 'limit', 'total_pages']
            missing_keys = [key for key in required_keys if key not in data]
            
            if missing_keys:
                print(f"❌ Missing keys in response: {missing_keys}")
                return False
            
            bookings = data['bookings']
            total_count = data['total_count']
            page = data['page']
            limit = data['limit']
            total_pages = data['total_pages']
            
            print(f"✅ Response structure correct:")
            print(f"  Total bookings: {total_count}")
            print(f"  Current page: {page}")
            print(f"  Limit per page: {limit}")
            print(f"  Total pages: {total_pages}")
            print(f"  Bookings returned: {len(bookings)}")
            
            # Verify pagination logic
            expected_total_pages = (total_count + limit - 1) // limit
            if total_pages == expected_total_pages:
                print("✅ Total pages calculation correct")
            else:
                print(f"❌ Total pages calculation incorrect. Expected: {expected_total_pages}, Got: {total_pages}")
                return False
            
            # Verify bookings data structure
            if bookings and len(bookings) > 0:
                sample_booking = bookings[0]
                required_booking_fields = ['id', 'guest_name', 'room_number', 'check_in_date', 'status']
                missing_booking_fields = [field for field in required_booking_fields if field not in sample_booking]
                
                if missing_booking_fields:
                    print(f"❌ Missing fields in booking data: {missing_booking_fields}")
                    return False
                
                print("✅ Booking data structure correct")
                print(f"  Sample booking: {sample_booking['guest_name']} - Room {sample_booking['room_number']}")
                
                return True
            else:
                print("❌ No bookings returned")
                return False
        else:
            print(f"❌ Basic pagination FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Basic pagination FAILED - Exception: {e}")
        return False

def test_pagination_page_2():
    """Test pagination with page 2"""
    print("\n2. Testing Pagination Page 2 (GET /api/bookings?page=2)")
    
    try:
        # First get total count to see if page 2 should have data
        response1 = requests.get(f"{API_BASE}/bookings?page=1&limit=5")
        if response1.status_code != 200:
            print("❌ Could not get initial data for page 2 test")
            return False
        
        data1 = response1.json()
        total_count = data1['total_count']
        
        # Test page 2 with smaller limit to ensure we have page 2
        print(f"Total bookings: {total_count}, testing page 2 with limit=5...")
        response = requests.get(f"{API_BASE}/bookings?page=2&limit=5")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bookings = data['bookings']
            page = data['page']
            limit = data['limit']
            
            print(f"✅ Page 2 response received:")
            print(f"  Current page: {page}")
            print(f"  Limit: {limit}")
            print(f"  Bookings on page 2: {len(bookings)}")
            
            if page == 2:
                print("✅ Page parameter correctly returned")
                
                # If total_count > 5, we should have data on page 2
                if total_count > 5:
                    if len(bookings) > 0:
                        print("✅ Page 2 contains expected data")
                        return True
                    else:
                        print("❌ Page 2 should contain data but is empty")
                        return False
                else:
                    print("✅ Page 2 correctly empty (not enough total data)")
                    return True
            else:
                print(f"❌ Page parameter incorrect. Expected: 2, Got: {page}")
                return False
        else:
            print(f"❌ Page 2 test FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Page 2 test FAILED - Exception: {e}")
        return False

def test_search_by_guest_name():
    """Test search functionality by guest name"""
    print("\n3. Testing Search by Guest Name (GET /api/bookings?search=)")
    
    try:
        # Search for a specific guest name
        search_term = "Alice"
        print(f"Searching for guest name containing '{search_term}'...")
        response = requests.get(f"{API_BASE}/bookings?search={search_term}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bookings = data['bookings']
            total_count = data['total_count']
            
            print(f"✅ Search response received:")
            print(f"  Total matching bookings: {total_count}")
            print(f"  Bookings returned: {len(bookings)}")
            
            # Verify search results contain the search term
            if bookings:
                all_match = True
                for booking in bookings:
                    guest_name = booking.get('guest_name', '').lower()
                    if search_term.lower() not in guest_name:
                        print(f"❌ Booking doesn't match search: {booking.get('guest_name')}")
                        all_match = False
                
                if all_match:
                    print("✅ All search results match the search term")
                    print(f"  Sample result: {bookings[0]['guest_name']}")
                    return True
                else:
                    print("❌ Some search results don't match")
                    return False
            else:
                print("⚠️ No results found for search term - this might be expected")
                return True
        else:
            print(f"❌ Search by guest name FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Search by guest name FAILED - Exception: {e}")
        return False

def test_search_by_email_phone_room():
    """Test search functionality by email, phone, and room number"""
    print("\n4. Testing Search by Email, Phone, and Room Number")
    
    search_tests = [
        ("email", "alice@example.com"),
        ("phone", "123-456"),
        ("room", "103")
    ]
    
    results = []
    
    for search_type, search_term in search_tests:
        try:
            print(f"\nTesting search by {search_type}: '{search_term}'")
            response = requests.get(f"{API_BASE}/bookings?search={search_term}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                bookings = data['bookings']
                total_count = data['total_count']
                
                print(f"  Results found: {total_count}")
                
                if bookings:
                    # Verify search results
                    found_match = False
                    for booking in bookings:
                        if search_type == "email" and search_term.lower() in booking.get('guest_email', '').lower():
                            found_match = True
                        elif search_type == "phone" and search_term in booking.get('guest_phone', ''):
                            found_match = True
                        elif search_type == "room" and search_term in booking.get('room_number', ''):
                            found_match = True
                    
                    if found_match:
                        print(f"✅ Search by {search_type} working correctly")
                        results.append(True)
                    else:
                        print(f"❌ Search by {search_type} returned results but no matches found")
                        results.append(False)
                else:
                    print(f"⚠️ No results for {search_type} search - might be expected")
                    results.append(True)  # Empty results are valid
            else:
                print(f"❌ Search by {search_type} FAILED - Status code: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Search by {search_type} FAILED - Exception: {e}")
            results.append(False)
    
    if all(results):
        print("\n✅ All search functionality tests PASSED")
        return True
    else:
        failed_count = len(results) - sum(results)
        print(f"\n❌ {failed_count} search functionality tests FAILED")
        return False

def test_status_filtering():
    """Test status filtering functionality"""
    print("\n5. Testing Status Filtering (GET /api/bookings?status=)")
    
    # Test different status filters
    status_tests = ["Upcoming", "Checked-in", "Completed", "Cancelled"]
    results = []
    
    for status in status_tests:
        try:
            print(f"\nTesting status filter: '{status}'")
            response = requests.get(f"{API_BASE}/bookings?status={status}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                bookings = data['bookings']
                total_count = data['total_count']
                
                print(f"  Bookings with status '{status}': {total_count}")
                
                # Verify all returned bookings have the correct status
                if bookings:
                    all_correct_status = True
                    for booking in bookings:
                        if booking.get('status') != status:
                            print(f"❌ Booking has wrong status: Expected '{status}', Got '{booking.get('status')}'")
                            all_correct_status = False
                    
                    if all_correct_status:
                        print(f"✅ Status filtering for '{status}' working correctly")
                        results.append(True)
                    else:
                        print(f"❌ Status filtering for '{status}' returned incorrect results")
                        results.append(False)
                else:
                    print(f"⚠️ No bookings with status '{status}' - might be expected")
                    results.append(True)  # Empty results are valid
            else:
                print(f"❌ Status filtering for '{status}' FAILED - Status code: {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ Status filtering for '{status}' FAILED - Exception: {e}")
            results.append(False)
    
    if all(results):
        print("\n✅ All status filtering tests PASSED")
        return True
    else:
        failed_count = len(results) - sum(results)
        print(f"\n❌ {failed_count} status filtering tests FAILED")
        return False

def test_combined_search_and_status():
    """Test combined search and status filtering"""
    print("\n6. Testing Combined Search and Status Filtering")
    
    try:
        # Test search + status combination
        search_term = "Alice"
        status = "Upcoming"
        print(f"Testing combined search='{search_term}' and status='{status}'...")
        
        response = requests.get(f"{API_BASE}/bookings?search={search_term}&status={status}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            bookings = data['bookings']
            total_count = data['total_count']
            
            print(f"✅ Combined filter response received:")
            print(f"  Total matching bookings: {total_count}")
            print(f"  Bookings returned: {len(bookings)}")
            
            # Verify results match both criteria
            if bookings:
                all_match = True
                for booking in bookings:
                    guest_name = booking.get('guest_name', '').lower()
                    booking_status = booking.get('status', '')
                    
                    if search_term.lower() not in guest_name or booking_status != status:
                        print(f"❌ Booking doesn't match combined criteria: {booking.get('guest_name')} - {booking_status}")
                        all_match = False
                
                if all_match:
                    print("✅ Combined search and status filtering working correctly")
                    return True
                else:
                    print("❌ Some results don't match combined criteria")
                    return False
            else:
                print("⚠️ No results for combined filter - might be expected")
                return True
        else:
            print(f"❌ Combined search and status FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Combined search and status FAILED - Exception: {e}")
        return False

def test_csv_download_basic():
    """Test basic CSV download without filters"""
    print("\n7. Testing Basic CSV Download (GET /api/bookings/download)")
    
    try:
        print("Testing basic CSV download without filters...")
        response = requests.get(f"{API_BASE}/bookings/download")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            if 'data' in data and 'filename' in data:
                csv_data = data['data']
                filename = data['filename']
                
                print(f"✅ CSV download response received:")
                print(f"  Filename: {filename}")
                print(f"  CSV rows: {len(csv_data)}")
                
                # Verify CSV structure
                if csv_data and len(csv_data) > 0:
                    headers = csv_data[0]
                    expected_headers = [
                        "Guest Name", "Email", "Phone", "ID/Passport", "Country",
                        "Room Number", "Check-in Date", "Check-out Date", "Stay Type",
                        "Booking Amount", "Status", "Created At", "Additional Notes"
                    ]
                    
                    if headers == expected_headers:
                        print("✅ CSV headers correct")
                        
                        # Check if we have data rows
                        if len(csv_data) > 1:
                            sample_row = csv_data[1]
                            print(f"  Sample data row: {sample_row[0]} - Room {sample_row[5]}")
                            print("✅ Basic CSV download PASSED")
                            return True
                        else:
                            print("⚠️ CSV has headers but no data rows - might be expected")
                            return True
                    else:
                        print(f"❌ CSV headers incorrect. Expected: {expected_headers}")
                        print(f"Got: {headers}")
                        return False
                else:
                    print("❌ CSV data is empty")
                    return False
            else:
                print("❌ Response missing 'data' or 'filename' fields")
                return False
        else:
            print(f"❌ Basic CSV download FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Basic CSV download FAILED - Exception: {e}")
        return False

def test_csv_download_with_date_filters():
    """Test CSV download with date range filters"""
    print("\n8. Testing CSV Download with Date Range Filters")
    
    try:
        # Test with date range
        start_date = "2025-07-01"
        end_date = "2025-08-31"
        print(f"Testing CSV download with date range: {start_date} to {end_date}")
        
        response = requests.get(f"{API_BASE}/bookings/download?start_date={start_date}&end_date={end_date}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            filename = data.get('filename', '')
            
            print(f"✅ CSV download with date filter response received:")
            print(f"  Filename: {filename}")
            print(f"  CSV rows: {len(csv_data)}")
            
            # Verify filename contains date info or timestamp
            if 'bookings_' in filename and '.csv' in filename:
                print("✅ Filename format correct")
                
                if len(csv_data) > 0:
                    print("✅ CSV download with date filters PASSED")
                    return True
                else:
                    print("⚠️ No data in date range - might be expected")
                    return True
            else:
                print(f"❌ Filename format incorrect: {filename}")
                return False
        else:
            print(f"❌ CSV download with date filters FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CSV download with date filters FAILED - Exception: {e}")
        return False

def test_csv_download_with_status_filter():
    """Test CSV download with status filter"""
    print("\n9. Testing CSV Download with Status Filter")
    
    try:
        status = "Upcoming"
        print(f"Testing CSV download with status filter: {status}")
        
        response = requests.get(f"{API_BASE}/bookings/download?status={status}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            
            print(f"✅ CSV download with status filter response received:")
            print(f"  CSV rows: {len(csv_data)}")
            
            # Verify data contains only the specified status
            if len(csv_data) > 1:  # More than just headers
                # Find status column index
                headers = csv_data[0]
                status_index = headers.index("Status") if "Status" in headers else -1
                
                if status_index >= 0:
                    all_correct_status = True
                    for row in csv_data[1:]:  # Skip headers
                        if len(row) > status_index and row[status_index] != status:
                            print(f"❌ Row has wrong status: Expected '{status}', Got '{row[status_index]}'")
                            all_correct_status = False
                    
                    if all_correct_status:
                        print("✅ CSV download with status filter PASSED")
                        return True
                    else:
                        print("❌ CSV contains rows with wrong status")
                        return False
                else:
                    print("❌ Status column not found in CSV headers")
                    return False
            else:
                print("⚠️ No data rows with specified status - might be expected")
                return True
        else:
            print(f"❌ CSV download with status filter FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CSV download with status filter FAILED - Exception: {e}")
        return False

def test_csv_download_combined_filters():
    """Test CSV download with both date range and status filters"""
    print("\n10. Testing CSV Download with Combined Filters")
    
    try:
        start_date = "2025-07-01"
        end_date = "2025-08-31"
        status = "Upcoming"
        
        print(f"Testing CSV download with date range ({start_date} to {end_date}) and status ({status})")
        
        response = requests.get(f"{API_BASE}/bookings/download?start_date={start_date}&end_date={end_date}&status={status}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            csv_data = data.get('data', [])
            
            print(f"✅ CSV download with combined filters response received:")
            print(f"  CSV rows: {len(csv_data)}")
            
            if len(csv_data) > 0:
                print("✅ CSV download with combined filters PASSED")
                return True
            else:
                print("⚠️ No data matching combined filters - might be expected")
                return True
        else:
            print(f"❌ CSV download with combined filters FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CSV download with combined filters FAILED - Exception: {e}")
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n11. Testing Edge Cases and Error Handling")
    
    edge_case_results = []
    
    # Test 1: Invalid date format in download
    print("\nTesting invalid date format in CSV download...")
    try:
        response = requests.get(f"{API_BASE}/bookings/download?start_date=invalid-date&end_date=2025-08-31")
        if response.status_code == 400:
            print("✅ Invalid date format correctly rejected")
            edge_case_results.append(True)
        else:
            print(f"❌ Invalid date format not handled properly: {response.status_code}")
            edge_case_results.append(False)
    except Exception as e:
        print(f"❌ Invalid date format test failed: {e}")
        edge_case_results.append(False)
    
    # Test 2: Empty search results
    print("\nTesting empty search results...")
    try:
        response = requests.get(f"{API_BASE}/bookings?search=nonexistentguest12345")
        if response.status_code == 200:
            data = response.json()
            if data.get('total_count', 0) == 0 and len(data.get('bookings', [])) == 0:
                print("✅ Empty search results handled correctly")
                edge_case_results.append(True)
            else:
                print("❌ Empty search results not handled correctly")
                edge_case_results.append(False)
        else:
            print(f"❌ Empty search test failed: {response.status_code}")
            edge_case_results.append(False)
    except Exception as e:
        print(f"❌ Empty search test failed: {e}")
        edge_case_results.append(False)
    
    # Test 3: Pagination beyond available pages
    print("\nTesting pagination beyond available pages...")
    try:
        response = requests.get(f"{API_BASE}/bookings?page=999&limit=10")
        if response.status_code == 200:
            data = response.json()
            if len(data.get('bookings', [])) == 0:
                print("✅ Pagination beyond available pages handled correctly")
                edge_case_results.append(True)
            else:
                print("❌ Pagination beyond available pages not handled correctly")
                edge_case_results.append(False)
        else:
            print(f"❌ Pagination beyond pages test failed: {response.status_code}")
            edge_case_results.append(False)
    except Exception as e:
        print(f"❌ Pagination beyond pages test failed: {e}")
        edge_case_results.append(False)
    
    # Test 4: Very large page numbers
    print("\nTesting very large page numbers...")
    try:
        response = requests.get(f"{API_BASE}/bookings?page=1000000&limit=10")
        if response.status_code == 200:
            data = response.json()
            if data.get('page') == 1000000 and len(data.get('bookings', [])) == 0:
                print("✅ Very large page numbers handled correctly")
                edge_case_results.append(True)
            else:
                print("❌ Very large page numbers not handled correctly")
                edge_case_results.append(False)
        else:
            print(f"❌ Very large page numbers test failed: {response.status_code}")
            edge_case_results.append(False)
    except Exception as e:
        print(f"❌ Very large page numbers test failed: {e}")
        edge_case_results.append(False)
    
    if all(edge_case_results):
        print("\n✅ All edge case tests PASSED")
        return True
    else:
        failed_count = len(edge_case_results) - sum(edge_case_results)
        print(f"\n❌ {failed_count} edge case tests FAILED")
        return False

def main():
    """Run all updated bookings API tests"""
    print("Starting Updated Bookings API Tests")
    print("=" * 70)
    
    # Setup test data first
    if not setup_test_data():
        print("❌ Failed to setup test data. Exiting.")
        return False
    
    test_results = []
    
    # Test 1: Basic Pagination
    test_results.append(("Basic Pagination", test_basic_pagination()))
    
    # Test 2: Pagination Page 2
    test_results.append(("Pagination Page 2", test_pagination_page_2()))
    
    # Test 3: Search by Guest Name
    test_results.append(("Search by Guest Name", test_search_by_guest_name()))
    
    # Test 4: Search by Email, Phone, Room
    test_results.append(("Search by Email/Phone/Room", test_search_by_email_phone_room()))
    
    # Test 5: Status Filtering
    test_results.append(("Status Filtering", test_status_filtering()))
    
    # Test 6: Combined Search and Status
    test_results.append(("Combined Search & Status", test_combined_search_and_status()))
    
    # Test 7: Basic CSV Download
    test_results.append(("Basic CSV Download", test_csv_download_basic()))
    
    # Test 8: CSV Download with Date Filters
    test_results.append(("CSV Download Date Filters", test_csv_download_with_date_filters()))
    
    # Test 9: CSV Download with Status Filter
    test_results.append(("CSV Download Status Filter", test_csv_download_with_status_filter()))
    
    # Test 10: CSV Download Combined Filters
    test_results.append(("CSV Download Combined", test_csv_download_combined_filters()))
    
    # Test 11: Edge Cases
    test_results.append(("Edge Cases", test_edge_cases()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - UPDATED BOOKINGS API")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Updated bookings API with pagination, search, and CSV download is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)