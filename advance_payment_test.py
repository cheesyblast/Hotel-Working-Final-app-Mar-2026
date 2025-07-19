#!/usr/bin/env python3
"""
Advance Amount Payment Method and Daily Revenue Integration Test
Tests the enhanced check-in functionality with payment method selection and daily revenue integration.
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

print(f"Testing Advance Amount Payment Method and Daily Revenue Integration at: {API_BASE}")
print("=" * 80)

# Test results tracking
test_results = []

def log_test_result(test_name, passed, details=""):
    """Log test result for summary"""
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details
    })
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")

def test_health_check():
    """Test 1: Health check endpoint to ensure backend is running"""
    print("\n1. Testing Health Check (GET /api/)")
    try:
        response = requests.get(f"{API_BASE}/")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Hotel Management API":
                log_test_result("Health Check", True, f"API responding correctly: {data['message']}")
                return True
            else:
                log_test_result("Health Check", False, f"Unexpected response: {data}")
                return False
        else:
            log_test_result("Health Check", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Health Check", False, f"Exception: {str(e)}")
        return False

def setup_test_data():
    """Setup test data - initialize sample data and create test booking"""
    print("\n2. Setting up test data")
    
    # Initialize sample data
    try:
        response = requests.post(f"{API_BASE}/init-data")
        print(f"Sample data initialization: {response.status_code}")
    except Exception as e:
        print(f"Warning: Could not initialize sample data: {e}")
    
    # Create a test booking for check-in
    booking_data = {
        "guest_name": "Test Guest Advance Payment",
        "guest_email": "testadvance@example.com",
        "guest_phone": "555-0123",
        "guest_id_passport": "TEST123456",
        "guest_country": "Test Country",
        "room_number": "101",
        "check_in_date": "2025-01-19",
        "check_out_date": "2025-01-21",
        "stay_type": "Night Stay",
        "booking_amount": 5000.0,
        "additional_notes": "Test booking for advance payment testing"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Test booking created: {booking['id']}")
            return booking['id']
        else:
            print(f"❌ Failed to create test booking: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Exception creating test booking: {e}")
        return None

def test_checkin_with_cash_advance(booking_id):
    """Test 3: Check-in with Cash advance payment"""
    print("\n3. Testing Check-in with Cash Advance Payment")
    
    checkin_data = {
        "booking_id": booking_id,
        "advance_amount": 1500.0,
        "notes": "Cash advance payment test",
        "payment_method": "Cash"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        
        if response.status_code == 200:
            data = response.json()
            log_test_result("Check-in with Cash Advance", True, 
                          f"Customer checked in with {checkin_data['advance_amount']} Cash advance")
            return data.get('customer', {}).get('id')
        else:
            log_test_result("Check-in with Cash Advance", False, 
                          f"Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        log_test_result("Check-in with Cash Advance", False, f"Exception: {str(e)}")
        return None

def test_daily_sales_entry_created():
    """Test 4: Verify advance amount created daily sales entry"""
    print("\n4. Testing Daily Sales Entry Creation")
    
    try:
        # Get today's daily sales
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(f"{API_BASE}/daily-sales", 
                              params={"start_date": today, "end_date": today})
        
        if response.status_code == 200:
            daily_sales = response.json()
            
            # Look for our advance payment entry
            advance_entries = [sale for sale in daily_sales 
                             if sale.get('customer_name') == 'Test Guest Advance Payment' 
                             and sale.get('payment_method') == 'Cash'
                             and sale.get('additional_charges') == 1500.0]
            
            if advance_entries:
                entry = advance_entries[0]
                log_test_result("Daily Sales Entry Created", True, 
                              f"Advance payment recorded: {entry['additional_charges']} via {entry['payment_method']}")
                return True
            else:
                log_test_result("Daily Sales Entry Created", False, 
                              f"No advance payment entry found in {len(daily_sales)} daily sales records")
                return False
        else:
            log_test_result("Daily Sales Entry Created", False, 
                          f"Failed to get daily sales: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Daily Sales Entry Created", False, f"Exception: {str(e)}")
        return False

def test_daily_financial_summary_cash_balance():
    """Test 5: Verify advance amount included in cash balance"""
    print("\n5. Testing Daily Financial Summary - Cash Balance")
    
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        
        if response.status_code == 200:
            summary = response.json()
            
            cash_balance = summary.get('cash_balance', 0)
            payment_breakdown = summary.get('payment_method_breakdown', {})
            cash_payments = payment_breakdown.get('Cash', 0)
            
            # Check if our advance payment is included
            if cash_balance >= 1500.0 and cash_payments >= 1500.0:
                log_test_result("Cash Balance Includes Advance", True, 
                              f"Cash balance: {cash_balance}, Cash payments: {cash_payments}")
                return True
            else:
                log_test_result("Cash Balance Includes Advance", False, 
                              f"Cash balance: {cash_balance}, Cash payments: {cash_payments} (expected >= 1500)")
                return False
        else:
            log_test_result("Cash Balance Includes Advance", False, 
                          f"Failed to get daily financial summary: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Cash Balance Includes Advance", False, f"Exception: {str(e)}")
        return False

def test_checkin_with_card_advance():
    """Test 6: Check-in with Card advance payment (new booking)"""
    print("\n6. Testing Check-in with Card Advance Payment")
    
    # Create another test booking
    booking_data = {
        "guest_name": "Test Guest Card Payment",
        "guest_email": "testcard@example.com",
        "guest_phone": "555-0124",
        "room_number": "102",
        "check_in_date": "2025-01-19",
        "check_out_date": "2025-01-21",
        "booking_amount": 4000.0
    }
    
    try:
        # Create booking
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        if response.status_code != 200:
            log_test_result("Check-in with Card Advance", False, "Failed to create test booking")
            return False
        
        booking_id = response.json()['id']
        
        # Check-in with Card advance
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 1200.0,
            "notes": "Card advance payment test",
            "payment_method": "Card"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        
        if response.status_code == 200:
            log_test_result("Check-in with Card Advance", True, 
                          f"Customer checked in with {checkin_data['advance_amount']} Card advance")
            return True
        else:
            log_test_result("Check-in with Card Advance", False, 
                          f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Check-in with Card Advance", False, f"Exception: {str(e)}")
        return False

def test_bank_balance_includes_card_advance():
    """Test 7: Verify Card advance included in bank balance"""
    print("\n7. Testing Bank Balance Includes Card Advance")
    
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        
        if response.status_code == 200:
            summary = response.json()
            
            bank_balance = summary.get('bank_balance', 0)
            payment_breakdown = summary.get('payment_method_breakdown', {})
            card_payments = payment_breakdown.get('Card', 0)
            
            # Check if our Card advance payment is included
            if bank_balance >= 1200.0 and card_payments >= 1200.0:
                log_test_result("Bank Balance Includes Card Advance", True, 
                              f"Bank balance: {bank_balance}, Card payments: {card_payments}")
                return True
            else:
                log_test_result("Bank Balance Includes Card Advance", False, 
                              f"Bank balance: {bank_balance}, Card payments: {card_payments} (expected >= 1200)")
                return False
        else:
            log_test_result("Bank Balance Includes Card Advance", False, 
                          f"Failed to get daily financial summary: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Bank Balance Includes Card Advance", False, f"Exception: {str(e)}")
        return False

def test_bank_transfer_advance():
    """Test 8: Check-in with Bank Transfer advance payment"""
    print("\n8. Testing Check-in with Bank Transfer Advance Payment")
    
    # Create another test booking
    booking_data = {
        "guest_name": "Test Guest Bank Transfer",
        "guest_email": "testbank@example.com",
        "guest_phone": "555-0125",
        "room_number": "103",
        "check_in_date": "2025-01-19",
        "check_out_date": "2025-01-21",
        "booking_amount": 3500.0
    }
    
    try:
        # Create booking
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        if response.status_code != 200:
            log_test_result("Check-in with Bank Transfer Advance", False, "Failed to create test booking")
            return False
        
        booking_id = response.json()['id']
        
        # Check-in with Bank Transfer advance
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 800.0,
            "notes": "Bank Transfer advance payment test",
            "payment_method": "Bank Transfer"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        
        if response.status_code == 200:
            log_test_result("Check-in with Bank Transfer Advance", True, 
                          f"Customer checked in with {checkin_data['advance_amount']} Bank Transfer advance")
            return True
        else:
            log_test_result("Check-in with Bank Transfer Advance", False, 
                          f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Check-in with Bank Transfer Advance", False, f"Exception: {str(e)}")
        return False

def test_zero_advance_amount():
    """Test 9: Check-in with zero advance amount (should not create daily sale entry)"""
    print("\n9. Testing Check-in with Zero Advance Amount")
    
    # Create another test booking
    booking_data = {
        "guest_name": "Test Guest Zero Advance",
        "guest_email": "testzero@example.com",
        "guest_phone": "555-0126",
        "room_number": "201",
        "check_in_date": "2025-01-19",
        "check_out_date": "2025-01-21",
        "booking_amount": 2500.0
    }
    
    try:
        # Create booking
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        if response.status_code != 200:
            log_test_result("Check-in with Zero Advance", False, "Failed to create test booking")
            return False
        
        booking_id = response.json()['id']
        
        # Get current daily sales count
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(f"{API_BASE}/daily-sales", 
                              params={"start_date": today, "end_date": today})
        initial_sales_count = len(response.json()) if response.status_code == 200 else 0
        
        # Check-in with zero advance
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 0.0,
            "notes": "Zero advance payment test",
            "payment_method": "Cash"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        
        if response.status_code == 200:
            # Check if daily sales count increased (it shouldn't for zero advance)
            response = requests.get(f"{API_BASE}/daily-sales", 
                                  params={"start_date": today, "end_date": today})
            final_sales_count = len(response.json()) if response.status_code == 200 else 0
            
            if final_sales_count == initial_sales_count:
                log_test_result("Check-in with Zero Advance", True, 
                              f"No daily sale entry created for zero advance (sales count unchanged: {final_sales_count})")
                return True
            else:
                log_test_result("Check-in with Zero Advance", False, 
                              f"Daily sale entry created for zero advance (sales count: {initial_sales_count} -> {final_sales_count})")
                return False
        else:
            log_test_result("Check-in with Zero Advance", False, 
                          f"Check-in failed: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Check-in with Zero Advance", False, f"Exception: {str(e)}")
        return False

def test_payment_method_breakdown():
    """Test 10: Verify payment method breakdown includes all advance payments"""
    print("\n10. Testing Payment Method Breakdown")
    
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        
        if response.status_code == 200:
            summary = response.json()
            payment_breakdown = summary.get('payment_method_breakdown', {})
            
            # Check if all payment methods are present with expected amounts
            cash_amount = payment_breakdown.get('Cash', 0)
            card_amount = payment_breakdown.get('Card', 0)
            bank_transfer_amount = payment_breakdown.get('Bank Transfer', 0)
            
            # We expect at least our test amounts
            expected_cash = 1500.0  # From test 3
            expected_card = 1200.0  # From test 6
            expected_bank_transfer = 800.0  # From test 8
            
            success = (cash_amount >= expected_cash and 
                      card_amount >= expected_card and 
                      bank_transfer_amount >= expected_bank_transfer)
            
            if success:
                log_test_result("Payment Method Breakdown", True, 
                              f"Cash: {cash_amount}, Card: {card_amount}, Bank Transfer: {bank_transfer_amount}")
                return True
            else:
                log_test_result("Payment Method Breakdown", False, 
                              f"Cash: {cash_amount} (expected >= {expected_cash}), "
                              f"Card: {card_amount} (expected >= {expected_card}), "
                              f"Bank Transfer: {bank_transfer_amount} (expected >= {expected_bank_transfer})")
                return False
        else:
            log_test_result("Payment Method Breakdown", False, 
                          f"Failed to get daily financial summary: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("Payment Method Breakdown", False, f"Exception: {str(e)}")
        return False

def print_test_summary():
    """Print comprehensive test summary"""
    print("\n" + "=" * 80)
    print("ADVANCE AMOUNT PAYMENT METHOD AND DAILY REVENUE INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = [t for t in test_results if t['passed']]
    failed_tests = [t for t in test_results if not t['passed']]
    
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {len(passed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Success Rate: {len(passed_tests)/len(test_results)*100:.1f}%")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['details']}")
    
    if passed_tests:
        print("\n✅ PASSED TESTS:")
        for test in passed_tests:
            print(f"  - {test['test']}")
    
    print("\n" + "=" * 80)
    
    # Overall result
    if len(failed_tests) == 0:
        print("🎉 ALL TESTS PASSED - Advance Amount Payment Method and Daily Revenue Integration is working perfectly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - Advance Amount Payment Method and Daily Revenue Integration needs attention.")
        return False

def main():
    """Run all advance payment integration tests"""
    print("Starting Advance Amount Payment Method and Daily Revenue Integration Tests...")
    
    # Test 1: Health check
    if not test_health_check():
        print("❌ Health check failed. Cannot proceed with testing.")
        return False
    
    # Test 2: Setup test data
    booking_id = setup_test_data()
    if not booking_id:
        print("❌ Failed to setup test data. Cannot proceed with testing.")
        return False
    
    # Test 3: Check-in with Cash advance
    customer_id = test_checkin_with_cash_advance(booking_id)
    
    # Test 4: Verify daily sales entry created
    test_daily_sales_entry_created()
    
    # Test 5: Verify cash balance includes advance
    test_daily_financial_summary_cash_balance()
    
    # Test 6: Check-in with Card advance
    test_checkin_with_card_advance()
    
    # Test 7: Verify bank balance includes Card advance
    test_bank_balance_includes_card_advance()
    
    # Test 8: Check-in with Bank Transfer advance
    test_bank_transfer_advance()
    
    # Test 9: Check-in with zero advance amount
    test_zero_advance_amount()
    
    # Test 10: Verify payment method breakdown
    test_payment_method_breakdown()
    
    # Print summary
    return print_test_summary()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)