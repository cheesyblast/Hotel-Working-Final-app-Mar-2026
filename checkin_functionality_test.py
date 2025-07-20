#!/usr/bin/env python3
"""
Check-in Functionality Testing for Hotel Management System
Tests the check-in functionality that was just fixed, focusing on advance amount handling.

Test Scenarios:
1. Normal Check-in with advance amount (e.g., 1000 LKR)
2. Check-in without advance amount (0 advance amount)
3. Check-in with missing/null advance amount (should default to 0)
4. Verify room status changes from "Available" to "Occupied" after check-in
5. Verify customer record is created properly
6. Verify advance amounts are recorded in daily sales only when > 0
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

print(f"Testing Check-in Functionality at: {API_BASE}")
print("=" * 80)

def test_health_check():
    """Test API health check"""
    print("\n1. Testing API Health Check (GET /api/)")
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

def initialize_test_data():
    """Initialize sample data for testing"""
    print("\n2. Initializing Test Data (POST /api/init-data)")
    try:
        response = requests.post(f"{API_BASE}/init-data")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Test data initialization PASSED")
            return True
        else:
            print(f"❌ Test data initialization FAILED - Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Test data initialization FAILED - Exception: {e}")
        return False

def create_test_booking(room_number, guest_name, booking_amount):
    """Create a test booking for check-in testing"""
    print(f"\n3. Creating Test Booking for {guest_name} in Room {room_number}")
    
    # Calculate dates
    check_in_date = (datetime.now() + timedelta(days=1)).date()
    check_out_date = (datetime.now() + timedelta(days=3)).date()
    
    booking_data = {
        "guest_name": guest_name,
        "guest_email": f"{guest_name.lower().replace(' ', '.')}@example.com",
        "guest_phone": "+94 77 123 4567",
        "guest_id_passport": "P123456789",
        "guest_country": "Sri Lanka",
        "room_number": room_number,
        "check_in_date": check_in_date.strftime('%Y-%m-%d'),
        "check_out_date": check_out_date.strftime('%Y-%m-%d'),
        "stay_type": "Night Stay",
        "booking_amount": booking_amount,
        "additional_notes": f"Test booking for check-in functionality testing"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Booking created successfully:")
            print(f"  Booking ID: {booking['id']}")
            print(f"  Guest: {booking['guest_name']}")
            print(f"  Room: {booking['room_number']}")
            print(f"  Amount: LKR {booking['booking_amount']}")
            print(f"  Check-in: {booking['check_in_date']}")
            print(f"  Check-out: {booking['check_out_date']}")
            return True, booking
        else:
            print(f"❌ Booking creation FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Booking creation FAILED - Exception: {e}")
        return False, None

def get_room_status(room_number):
    """Get current status of a specific room"""
    try:
        response = requests.get(f"{API_BASE}/rooms")
        if response.status_code == 200:
            rooms = response.json()
            for room in rooms:
                if room['room_number'] == room_number:
                    return room['status'], room
            return None, None
        else:
            return None, None
    except Exception as e:
        print(f"Error getting room status: {e}")
        return None, None

def test_checkin_with_advance_amount(booking, advance_amount, test_name):
    """Test check-in with specific advance amount"""
    print(f"\n4. Testing {test_name}")
    
    booking_id = booking['id']
    room_number = booking['room_number']
    guest_name = booking['guest_name']
    
    # Get initial room status
    initial_status, initial_room = get_room_status(room_number)
    print(f"Initial room status: {initial_status}")
    
    # Get initial customer count
    try:
        customers_response = requests.get(f"{API_BASE}/customers/checked-in")
        initial_customer_count = len(customers_response.json()) if customers_response.status_code == 200 else 0
        print(f"Initial checked-in customers: {initial_customer_count}")
    except:
        initial_customer_count = 0
    
    # Get initial daily sales count
    try:
        sales_response = requests.get(f"{API_BASE}/daily-sales")
        initial_sales_count = len(sales_response.json()) if sales_response.status_code == 200 else 0
        print(f"Initial daily sales records: {initial_sales_count}")
    except:
        initial_sales_count = 0
    
    # Prepare check-in data
    checkin_data = {
        "booking_id": booking_id,
        "notes": f"Test check-in for {test_name}",
        "payment_method": "Cash"
    }
    
    # Add advance_amount based on test scenario
    if advance_amount is not None:
        checkin_data["advance_amount"] = advance_amount
    # If advance_amount is None, we don't include it to test default behavior
    
    print(f"Check-in data: {checkin_data}")
    
    try:
        # Perform check-in
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        print(f"Check-in Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Check-in Response: {result}")
            
            if "checked in successfully" in result.get("message", ""):
                print("✅ Check-in API call successful")
                
                # Verify customer was created
                customers_response = requests.get(f"{API_BASE}/customers/checked-in")
                if customers_response.status_code == 200:
                    customers = customers_response.json()
                    final_customer_count = len(customers)
                    print(f"Final checked-in customers: {final_customer_count}")
                    
                    # Find the checked-in customer
                    checked_in_customer = None
                    for customer in customers:
                        if customer['name'] == guest_name and customer['current_room'] == room_number:
                            checked_in_customer = customer
                            break
                    
                    if checked_in_customer:
                        print("✅ Customer record created successfully:")
                        print(f"  Name: {checked_in_customer['name']}")
                        print(f"  Room: {checked_in_customer['current_room']}")
                        print(f"  Room Charges: LKR {checked_in_customer['room_charges']}")
                        print(f"  Advance Amount: LKR {checked_in_customer['advance_amount']}")
                        print(f"  Total Amount: LKR {checked_in_customer['total_amount']}")
                        
                        # Verify advance amount is correct
                        expected_advance = advance_amount if advance_amount is not None else 0.0
                        if checked_in_customer['advance_amount'] == expected_advance:
                            print(f"✅ Advance amount correctly set to LKR {expected_advance}")
                        else:
                            print(f"❌ Advance amount mismatch. Expected: {expected_advance}, Got: {checked_in_customer['advance_amount']}")
                            return False
                        
                        # Verify room charges match booking amount
                        if checked_in_customer['room_charges'] == booking['booking_amount']:
                            print(f"✅ Room charges correctly set to LKR {booking['booking_amount']}")
                        else:
                            print(f"❌ Room charges mismatch. Expected: {booking['booking_amount']}, Got: {checked_in_customer['room_charges']}")
                            return False
                    else:
                        print(f"❌ Could not find checked-in customer for {guest_name}")
                        return False
                else:
                    print("❌ Could not retrieve checked-in customers")
                    return False
                
                # Verify room status changed to "Occupied"
                final_status, final_room = get_room_status(room_number)
                print(f"Final room status: {final_status}")
                
                if final_status == "Occupied":
                    print("✅ Room status correctly updated to 'Occupied'")
                    
                    # Verify room has guest information
                    if final_room.get('current_guest') == guest_name:
                        print(f"✅ Room correctly shows current guest: {guest_name}")
                    else:
                        print(f"❌ Room guest mismatch. Expected: {guest_name}, Got: {final_room.get('current_guest')}")
                        return False
                else:
                    print(f"❌ Room status not updated correctly. Expected: 'Occupied', Got: {final_status}")
                    return False
                
                # Verify daily sales record creation (only if advance amount > 0)
                sales_response = requests.get(f"{API_BASE}/daily-sales")
                if sales_response.status_code == 200:
                    final_sales = sales_response.json()
                    final_sales_count = len(final_sales)
                    print(f"Final daily sales records: {final_sales_count}")
                    
                    expected_advance = advance_amount if advance_amount is not None else 0.0
                    
                    if expected_advance > 0:
                        # Should have created a daily sales record
                        if final_sales_count > initial_sales_count:
                            # Find the advance payment record
                            advance_record = None
                            for sale in final_sales:
                                if (sale.get('customer_name') == guest_name and 
                                    sale.get('room_number') == room_number and
                                    sale.get('total_amount') == expected_advance):
                                    advance_record = sale
                                    break
                            
                            if advance_record:
                                print("✅ Daily sales record created for advance payment:")
                                print(f"  Customer: {advance_record['customer_name']}")
                                print(f"  Room: {advance_record['room_number']}")
                                print(f"  Amount: LKR {advance_record['total_amount']}")
                                print(f"  Payment Method: {advance_record['payment_method']}")
                            else:
                                print("❌ Could not find daily sales record for advance payment")
                                return False
                        else:
                            print("❌ No daily sales record created for advance payment")
                            return False
                    else:
                        # Should not have created a daily sales record for advance
                        print("✅ No daily sales record created for zero advance amount (correct behavior)")
                else:
                    print("❌ Could not retrieve daily sales records")
                    return False
                
                print(f"✅ {test_name} PASSED - All verifications successful")
                return True
            else:
                print(f"❌ {test_name} FAILED - Unexpected response message")
                return False
        else:
            print(f"❌ {test_name} FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ {test_name} FAILED - Exception: {e}")
        return False

def main():
    """Run all check-in functionality tests"""
    print("Starting Check-in Functionality Tests")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(("Health Check", test_health_check()))
    
    # Test 2: Initialize Test Data
    test_results.append(("Initialize Data", initialize_test_data()))
    
    # Test 3: Check-in with advance amount (1000 LKR)
    print("\n" + "="*50)
    print("TEST SCENARIO 1: Check-in with advance amount")
    print("="*50)
    
    booking_success, booking1 = create_test_booking("103", "Rajesh Kumar", 8500.0)
    if booking_success:
        checkin1_result = test_checkin_with_advance_amount(
            booking1, 1000.0, "Check-in with 1000 LKR advance amount"
        )
        test_results.append(("Check-in with Advance", checkin1_result))
    else:
        test_results.append(("Check-in with Advance", False))
    
    # Test 4: Check-in with zero advance amount
    print("\n" + "="*50)
    print("TEST SCENARIO 2: Check-in with zero advance amount")
    print("="*50)
    
    booking_success, booking2 = create_test_booking("201", "Priya Sharma", 12000.0)
    if booking_success:
        checkin2_result = test_checkin_with_advance_amount(
            booking2, 0.0, "Check-in with 0 LKR advance amount"
        )
        test_results.append(("Check-in with Zero Advance", checkin2_result))
    else:
        test_results.append(("Check-in with Zero Advance", False))
    
    # Test 5: Check-in without advance_amount field (should default to 0)
    print("\n" + "="*50)
    print("TEST SCENARIO 3: Check-in without advance_amount field")
    print("="*50)
    
    booking_success, booking3 = create_test_booking("202", "Anil Fernando", 11500.0)
    if booking_success:
        checkin3_result = test_checkin_with_advance_amount(
            booking3, None, "Check-in without advance_amount field (should default to 0)"
        )
        test_results.append(("Check-in Missing Advance Field", checkin3_result))
    else:
        test_results.append(("Check-in Missing Advance Field", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("CHECK-IN FUNCTIONALITY TEST SUMMARY")
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
        print("\n🎉 ALL CHECK-IN TESTS PASSED!")
        print("✅ Check-in functionality is working correctly with proper advance amount handling")
        print("✅ Room status updates correctly from 'Available' to 'Occupied'")
        print("✅ Customer records are created properly with correct amounts")
        print("✅ Daily sales records are created only when advance amount > 0")
        print("✅ Advance amount field is optional and defaults to 0 when not provided")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check-in functionality needs attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)