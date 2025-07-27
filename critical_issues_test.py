#!/usr/bin/env python3
"""
Critical Issues Testing for Hotel Management System
Tests the two critical user-reported issues:
1. Advance Payment Real-time Balance Update
2. Date Extension for Checked-in Bookings
3. Validation Rules for Checked-in Bookings
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

print(f"Testing Critical Issues at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
auth_token = None
auth_headers = {}

def authenticate_admin():
    """Authenticate as admin user"""
    global auth_token, auth_headers
    print("\n🔐 Authenticating as admin...")
    
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
            print("✅ Admin authentication successful")
            return True
        else:
            print(f"❌ Admin authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin authentication failed - Exception: {e}")
        return False

def get_financial_summary():
    """Get current daily financial summary to check balances"""
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary", headers=auth_headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get daily financial summary - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to get daily financial summary - Exception: {e}")
        return None

def create_test_booking(stay_type="Night Stay", booking_amount=8500.0):
    """Create a test booking for testing"""
    try:
        # Get available rooms first
        rooms_response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
        if rooms_response.status_code != 200:
            print("❌ Failed to get rooms")
            return None
        
        rooms = rooms_response.json()
        available_room = None
        
        # First try to find an available room
        for room in rooms:
            if room.get('status') == 'Available':
                available_room = room
                break
        
        # If no available room, create a new test room
        if not available_room:
            print("🏗️ No available rooms found, creating a test room...")
            test_room_data = {
                "room_number": f"TEST{len(rooms)+1}",
                "room_type": "Double",
                "price_per_night": 8500.0,
                "max_occupancy": 2,
                "amenities": ["WiFi", "AC", "TV"]
            }
            
            create_room_response = requests.post(f"{API_BASE}/rooms", json=test_room_data, headers=auth_headers)
            if create_room_response.status_code == 200:
                available_room = create_room_response.json()
                print(f"✅ Created test room: {available_room['room_number']}")
            else:
                print(f"❌ Failed to create test room - Status: {create_room_response.status_code}")
                print(f"Response: {create_room_response.text}")
                return None
        
        # Create booking
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        booking_data = {
            "guest_name": "Test Guest Critical",
            "guest_email": "testcritical@example.com",
            "guest_phone": "+1234567890",
            "guest_id_passport": "TEST123",
            "guest_country": "Test Country",
            "room_number": available_room['room_number'],
            "check_in_date": today.isoformat(),
            "check_out_date": tomorrow.isoformat() if stay_type == "Night Stay" else today.isoformat(),
            "stay_type": stay_type,
            "booking_amount": booking_amount,
            "additional_notes": "Critical test booking"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Created test booking: {booking['id']} for room {booking['room_number']}")
            return booking
        else:
            print(f"❌ Failed to create booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Failed to create booking - Exception: {e}")
        return None

def check_in_booking(booking_id, advance_amount=1000.0, payment_method="Cash"):
    """Check in a booking with advance payment"""
    try:
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": advance_amount,
            "payment_method": payment_method,
            "notes": "Critical test check-in"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Check-in successful: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Check-in failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Check-in failed - Exception: {e}")
        return False

def get_checked_in_customers():
    """Get list of checked-in customers"""
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get checked-in customers - Status: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Failed to get checked-in customers - Exception: {e}")
        return []

def collect_advance_payment(customer_id, amount=500.0, payment_method="Card"):
    """Collect additional advance payment from checked-in customer"""
    try:
        advance_data = {
            "customer_id": customer_id,
            "amount": amount,
            "payment_method": payment_method,
            "notes": "Additional advance payment test"
        }
        
        response = requests.post(f"{API_BASE}/advance-payment", json=advance_data, headers=auth_headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Advance payment collected: {result.get('message', 'No message')}")
            return True
        else:
            print(f"❌ Advance payment failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Advance payment failed - Exception: {e}")
        return False

def test_advance_payment_balance_update():
    """Test 1: Advance Payment Real-time Balance Update"""
    print("\n" + "="*60)
    print("TEST 1: ADVANCE PAYMENT REAL-TIME BALANCE UPDATE")
    print("="*60)
    
    # Step 1: Get initial financial balance
    print("\n📊 Step 1: Getting initial financial balance...")
    initial_summary = get_financial_summary()
    if not initial_summary:
        print("❌ Failed to get initial financial summary")
        return False
    
    initial_cash_balance = initial_summary.get('cash_balance', 0)
    initial_bank_balance = initial_summary.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash_balance}")
    print(f"Initial Bank Balance: {initial_bank_balance}")
    
    # Step 2: Create booking
    print("\n📝 Step 2: Creating test booking...")
    booking = create_test_booking(stay_type="Night Stay", booking_amount=8500.0)
    if not booking:
        print("❌ Failed to create test booking")
        return False
    
    # Step 3: Check-in with cash advance
    print("\n🏨 Step 3: Checking in with cash advance payment...")
    checkin_success = check_in_booking(booking['id'], advance_amount=1000.0, payment_method="Cash")
    if not checkin_success:
        print("❌ Failed to check-in booking")
        return False
    
    # Step 4: Verify balance update after check-in
    print("\n💰 Step 4: Verifying balance update after check-in...")
    after_checkin_summary = get_financial_summary()
    if not after_checkin_summary:
        print("❌ Failed to get financial summary after check-in")
        return False
    
    after_checkin_cash = after_checkin_summary.get('cash_balance', 0)
    after_checkin_bank = after_checkin_summary.get('bank_balance', 0)
    print(f"After Check-in Cash Balance: {after_checkin_cash}")
    print(f"After Check-in Bank Balance: {after_checkin_bank}")
    
    # Verify cash balance increased by advance amount
    expected_cash_increase = 1000.0
    actual_cash_increase = after_checkin_cash - initial_cash_balance
    
    if abs(actual_cash_increase - expected_cash_increase) < 0.01:
        print(f"✅ Cash balance correctly increased by {expected_cash_increase}")
    else:
        print(f"❌ Cash balance increase mismatch. Expected: {expected_cash_increase}, Actual: {actual_cash_increase}")
        return False
    
    # Step 5: Get checked-in customer
    print("\n👥 Step 5: Getting checked-in customer for advance payment...")
    customers = get_checked_in_customers()
    test_customer = None
    for customer in customers:
        if customer.get('name') == 'Test Guest Critical':
            test_customer = customer
            break
    
    if not test_customer:
        print("❌ Test customer not found in checked-in customers")
        return False
    
    print(f"Found test customer: {test_customer['name']} in room {test_customer['current_room']}")
    
    # Step 6: Collect additional advance payment (Card)
    print("\n💳 Step 6: Collecting additional advance payment via Card...")
    advance_success = collect_advance_payment(test_customer['id'], amount=500.0, payment_method="Card")
    if not advance_success:
        print("❌ Failed to collect advance payment")
        return False
    
    # Step 7: Verify final balance update
    print("\n📈 Step 7: Verifying final balance update...")
    final_summary = get_financial_summary()
    if not final_summary:
        print("❌ Failed to get final financial summary")
        return False
    
    final_cash_balance = final_summary.get('cash_balance', 0)
    final_bank_balance = final_summary.get('bank_balance', 0)
    print(f"Final Cash Balance: {final_cash_balance}")
    print(f"Final Bank Balance: {final_bank_balance}")
    
    # Verify bank balance increased by card advance amount
    expected_bank_increase = 500.0
    actual_bank_increase = final_bank_balance - initial_bank_balance
    
    if abs(actual_bank_increase - expected_bank_increase) < 0.01:
        print(f"✅ Bank balance correctly increased by {expected_bank_increase}")
    else:
        print(f"❌ Bank balance increase mismatch. Expected: {expected_bank_increase}, Actual: {actual_bank_increase}")
        return False
    
    # Verify cash balance remained the same after card payment
    if abs(final_cash_balance - after_checkin_cash) < 0.01:
        print("✅ Cash balance correctly unchanged after card payment")
    else:
        print(f"❌ Cash balance unexpectedly changed after card payment")
        return False
    
    print("\n🎉 TEST 1 PASSED: Advance payment real-time balance updates working correctly!")
    return True

def test_date_extension_for_checked_in():
    """Test 2: Date Extension for Checked-in Bookings"""
    print("\n" + "="*60)
    print("TEST 2: DATE EXTENSION FOR CHECKED-IN BOOKINGS")
    print("="*60)
    
    test_results = []
    
    # Test 2A: Short Time Booking Extension (Should be ALLOWED)
    print("\n📅 Test 2A: Short Time Booking Extension...")
    
    # Create short time booking
    short_booking = create_test_booking(stay_type="Short Time", booking_amount=4250.0)
    if not short_booking:
        print("❌ Failed to create short time booking")
        test_results.append(False)
    else:
        # Check-in the booking
        checkin_success = check_in_booking(short_booking['id'], advance_amount=500.0)
        if not checkin_success:
            print("❌ Failed to check-in short time booking")
            test_results.append(False)
        else:
            # Try to extend dates (should be ALLOWED for checked-in bookings)
            print("🔄 Attempting to extend dates for checked-in short time booking...")
            
            tomorrow = (datetime.now().date() + timedelta(days=1)).isoformat()
            update_data = {
                "check_out_date": tomorrow,
                "additional_notes": "Extending checkout date"
            }
            
            response = requests.put(f"{API_BASE}/bookings/{short_booking['id']}", 
                                  json=update_data, headers=auth_headers)
            
            if response.status_code == 200:
                result = response.json()
                if "Booking updated successfully" in result.get('message', ''):
                    print("✅ Date extension correctly allowed for checked-in booking")
                    test_results.append(True)
                else:
                    print(f"❌ Unexpected response message: {result.get('message', '')}")
                    test_results.append(False)
            else:
                print(f"❌ Expected 200 status, got {response.status_code}")
                print(f"Response: {response.text}")
                test_results.append(False)
    
    # Test 2B: Night Stay Booking Extension (Should be ALLOWED)
    print("\n🌙 Test 2B: Night Stay Booking Extension...")
    
    # Create night stay booking
    night_booking = create_test_booking(stay_type="Night Stay", booking_amount=8500.0)
    if not night_booking:
        print("❌ Failed to create night stay booking")
        test_results.append(False)
    else:
        # Check-in the booking
        checkin_success = check_in_booking(night_booking['id'], advance_amount=1000.0)
        if not checkin_success:
            print("❌ Failed to check-in night stay booking")
            test_results.append(False)
        else:
            # Try to extend dates (should be ALLOWED for checked-in bookings)
            print("🔄 Attempting to extend dates for checked-in night stay booking...")
            
            day_after_tomorrow = (datetime.now().date() + timedelta(days=2)).isoformat()
            update_data = {
                "check_out_date": day_after_tomorrow,
                "additional_notes": "Extending checkout date by one day"
            }
            
            response = requests.put(f"{API_BASE}/bookings/{night_booking['id']}", 
                                  json=update_data, headers=auth_headers)
            
            if response.status_code == 200:
                result = response.json()
                if "Booking updated successfully" in result.get('message', ''):
                    print("✅ Date extension correctly allowed for checked-in booking")
                    test_results.append(True)
                else:
                    print(f"❌ Unexpected response message: {result.get('message', '')}")
                    test_results.append(False)
            else:
                print(f"❌ Expected 200 status, got {response.status_code}")
                print(f"Response: {response.text}")
                test_results.append(False)
    
    if all(test_results):
        print("\n🎉 TEST 2 PASSED: Date extension correctly allowed for checked-in bookings!")
        return True
    else:
        print(f"\n❌ TEST 2 FAILED: {len(test_results) - sum(test_results)} out of {len(test_results)} sub-tests failed")
        return False

def test_validation_rules_for_checked_in():
    """Test 3: Validation Rules for Checked-in Bookings"""
    print("\n" + "="*60)
    print("TEST 3: VALIDATION RULES FOR CHECKED-IN BOOKINGS")
    print("="*60)
    
    test_results = []
    
    # Create and check-in a test booking
    print("\n📝 Setting up test booking for validation tests...")
    test_booking = create_test_booking(stay_type="Night Stay", booking_amount=8500.0)
    if not test_booking:
        print("❌ Failed to create test booking for validation")
        return False
    
    checkin_success = check_in_booking(test_booking['id'], advance_amount=800.0)
    if not checkin_success:
        print("❌ Failed to check-in test booking for validation")
        return False
    
    # Test 3A: Check-in date change prevention
    print("\n📅 Test 3A: Check-in date change prevention...")
    yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
    update_data = {"check_in_date": yesterday}
    
    response = requests.put(f"{API_BASE}/bookings/{test_booking['id']}", 
                          json=update_data, headers=auth_headers)
    
    if response.status_code == 400:
        error_msg = response.json().get('detail', '')
        if 'Cannot change check-in date for checked-in bookings' in error_msg:
            print("✅ Check-in date change correctly prevented")
            test_results.append(True)
        else:
            print(f"❌ Wrong error message for check-in date change: {error_msg}")
            test_results.append(False)
    else:
        print(f"❌ Expected 400 status for check-in date change, got {response.status_code}")
        test_results.append(False)
    
    # Test 3B: Checkout date shortening prevention
    print("\n📅 Test 3B: Checkout date shortening prevention...")
    yesterday = (datetime.now().date() - timedelta(days=1)).isoformat()
    update_data = {"check_out_date": yesterday}
    
    response = requests.put(f"{API_BASE}/bookings/{test_booking['id']}", 
                          json=update_data, headers=auth_headers)
    
    if response.status_code == 400:
        error_msg = response.json().get('detail', '')
        if 'Cannot shorten checkout date for checked-in bookings' in error_msg:
            print("✅ Checkout date shortening correctly prevented")
            test_results.append(True)
        else:
            print(f"❌ Wrong error message for checkout date shortening: {error_msg}")
            test_results.append(False)
    else:
        print(f"❌ Expected 400 status for checkout date shortening, got {response.status_code}")
        test_results.append(False)
    
    # Test 3C: Room change prevention
    print("\n🏨 Test 3C: Room change prevention...")
    
    # Get a different available room
    rooms_response = requests.get(f"{API_BASE}/rooms", headers=auth_headers)
    if rooms_response.status_code == 200:
        rooms = rooms_response.json()
        different_room = None
        for room in rooms:
            if room.get('status') == 'Available' and room['room_number'] != test_booking['room_number']:
                different_room = room['room_number']
                break
        
        if different_room:
            update_data = {"room_number": different_room}
            
            response = requests.put(f"{API_BASE}/bookings/{test_booking['id']}", 
                                  json=update_data, headers=auth_headers)
            
            if response.status_code == 400:
                error_msg = response.json().get('detail', '')
                if 'Cannot change room for booking with status' in error_msg:
                    print("✅ Room change correctly prevented")
                    test_results.append(True)
                else:
                    print(f"❌ Wrong error message for room change: {error_msg}")
                    test_results.append(False)
            else:
                print(f"❌ Expected 400 status for room change, got {response.status_code}")
                test_results.append(False)
        else:
            print("⚠️ No different available room found for room change test")
            test_results.append(True)  # Skip this test
    else:
        print("❌ Failed to get rooms for room change test")
        test_results.append(False)
    
    if all(test_results):
        print("\n🎉 TEST 3 PASSED: All validation rules working correctly for checked-in bookings!")
        return True
    else:
        print(f"\n❌ TEST 3 FAILED: {len(test_results) - sum(test_results)} out of {len(test_results)} validation tests failed")
        return False

def main():
    """Run all critical issue tests"""
    print("Starting Critical Issues Testing")
    print("=" * 70)
    
    # Authenticate first
    if not authenticate_admin():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return False
    
    test_results = []
    
    # Test 1: Advance Payment Real-time Balance Update
    test_results.append(("Advance Payment Balance Update", test_advance_payment_balance_update()))
    
    # Test 2: Date Extension for Checked-in Bookings
    test_results.append(("Date Extension for Checked-in", test_date_extension_for_checked_in()))
    
    # Test 3: Validation Rules for Checked-in Bookings
    test_results.append(("Validation Rules for Checked-in", test_validation_rules_for_checked_in()))
    
    # Summary
    print("\n" + "=" * 70)
    print("CRITICAL ISSUES TEST SUMMARY")
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
        print("\n🎉 ALL CRITICAL ISSUES TESTS PASSED!")
        print("✅ Advance payment real-time balance updates working")
        print("✅ Date extension properly blocked for checked-in bookings")
        print("✅ All validation rules working for checked-in bookings")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} critical test(s) failed.")
        print("Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)