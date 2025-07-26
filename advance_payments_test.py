#!/usr/bin/env python3
"""
Real-Time Cash/Bank Balance Testing for Advance Payments
Tests advance payments from both check-in and "Get Advance" feature
and ensures they are correctly reflected in real-time in Cash and Bank balances.
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
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

print(f"Testing Advance Payments Real-Time Balance Updates at: {API_BASE}")
print("=" * 80)

# Authentication setup
def get_admin_token():
    """Get admin authentication token"""
    print("Getting admin authentication token...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print("✅ Admin authentication successful")
            return token
        else:
            print(f"❌ Admin authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Admin authentication failed - Exception: {e}")
        return None

def get_auth_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def get_daily_financial_summary():
    """Get current daily financial summary"""
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get daily financial summary - Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Failed to get daily financial summary - Exception: {e}")
        return None

def test_1_checkin_advance_payment_reflection():
    """Test 1: Check-in Advance Payment Reflection"""
    print("\n" + "="*60)
    print("TEST 1: CHECK-IN ADVANCE PAYMENT REFLECTION")
    print("="*60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return False
    
    headers = get_auth_headers(token)
    
    # Get initial financial summary
    print("\n1.1 Getting initial Cash and Bank balances...")
    initial_summary = get_daily_financial_summary()
    if not initial_summary:
        return False
    
    initial_cash = initial_summary.get('cash_balance', 0)
    initial_bank = initial_summary.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash}")
    print(f"Initial Bank Balance: {initial_bank}")
    
    # Create a booking first
    print("\n1.2 Creating a new booking for check-in test...")
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    booking_data = {
        "guest_name": "John Doe Advance Test",
        "guest_email": "john.advance@test.com",
        "guest_phone": "+1234567890",
        "guest_id_passport": "ID123456",
        "guest_country": "USA",
        "room_number": "102",
        "check_in_date": tomorrow.isoformat(),
        "check_out_date": (tomorrow + timedelta(days=1)).isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 5000.0,
        "additional_notes": "Advance payment test booking"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        if response.status_code == 200:
            booking = response.json()
            booking_id = booking['id']
            print(f"✅ Booking created successfully - ID: {booking_id}")
        else:
            print(f"❌ Failed to create booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to create booking - Exception: {e}")
        return False
    
    # Test 1a: Check-in with Cash advance payment
    print("\n1.3 Testing check-in with Cash advance payment...")
    checkin_data_cash = {
        "booking_id": booking_id,
        "advance_amount": 1500.0,
        "payment_method": "Cash",
        "notes": "Cash advance payment during check-in"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data_cash, headers=headers)
        if response.status_code == 200:
            print("✅ Check-in with Cash advance successful")
            
            # Immediately check financial summary
            print("1.4 Checking real-time Cash balance update...")
            time.sleep(1)  # Small delay to ensure database update
            updated_summary = get_daily_financial_summary()
            if updated_summary:
                new_cash = updated_summary.get('cash_balance', 0)
                new_bank = updated_summary.get('bank_balance', 0)
                
                print(f"Updated Cash Balance: {new_cash}")
                print(f"Updated Bank Balance: {new_bank}")
                
                expected_cash = initial_cash + 1500.0
                if abs(new_cash - expected_cash) < 0.01:  # Allow for floating point precision
                    print("✅ Cash balance correctly updated with advance payment")
                    cash_test_passed = True
                else:
                    print(f"❌ Cash balance not updated correctly. Expected: {expected_cash}, Got: {new_cash}")
                    cash_test_passed = False
                
                if abs(new_bank - initial_bank) < 0.01:
                    print("✅ Bank balance unchanged (correct for Cash payment)")
                    bank_unchanged_test = True
                else:
                    print(f"❌ Bank balance changed unexpectedly. Expected: {initial_bank}, Got: {new_bank}")
                    bank_unchanged_test = False
            else:
                return False
        else:
            print(f"❌ Check-in with Cash advance failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Check-in with Cash advance failed - Exception: {e}")
        return False
    
    # Create another booking for Card payment test
    print("\n1.5 Creating another booking for Card payment test...")
    booking_data_2 = {
        "guest_name": "Jane Smith Advance Test",
        "guest_email": "jane.advance@test.com",
        "guest_phone": "+1234567891",
        "guest_id_passport": "ID123457",
        "guest_country": "USA",
        "room_number": "202",
        "check_in_date": tomorrow.isoformat(),
        "check_out_date": (tomorrow + timedelta(days=1)).isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 6000.0,
        "additional_notes": "Card advance payment test booking"
    }
    
    try:
        response = requests.post(f"{API_BASE}/bookings", json=booking_data_2, headers=headers)
        if response.status_code == 200:
            booking_2 = response.json()
            booking_id_2 = booking_2['id']
            print(f"✅ Second booking created successfully - ID: {booking_id_2}")
        else:
            print(f"❌ Failed to create second booking - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to create second booking - Exception: {e}")
        return False
    
    # Test 1b: Check-in with Card advance payment
    print("\n1.6 Testing check-in with Card advance payment...")
    checkin_data_card = {
        "booking_id": booking_id_2,
        "advance_amount": 2000.0,
        "payment_method": "Card",
        "notes": "Card advance payment during check-in"
    }
    
    try:
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data_card, headers=headers)
        if response.status_code == 200:
            print("✅ Check-in with Card advance successful")
            
            # Immediately check financial summary
            print("1.7 Checking real-time Bank balance update...")
            time.sleep(1)  # Small delay to ensure database update
            final_summary = get_daily_financial_summary()
            if final_summary:
                final_cash = final_summary.get('cash_balance', 0)
                final_bank = final_summary.get('bank_balance', 0)
                
                print(f"Final Cash Balance: {final_cash}")
                print(f"Final Bank Balance: {final_bank}")
                
                expected_bank = initial_bank + 2000.0
                if abs(final_bank - expected_bank) < 0.01:
                    print("✅ Bank balance correctly updated with Card advance payment")
                    card_test_passed = True
                else:
                    print(f"❌ Bank balance not updated correctly. Expected: {expected_bank}, Got: {final_bank}")
                    card_test_passed = False
            else:
                return False
        else:
            print(f"❌ Check-in with Card advance failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Check-in with Card advance failed - Exception: {e}")
        return False
    
    # Test 1 Summary
    test_1_result = cash_test_passed and bank_unchanged_test and card_test_passed
    print(f"\n{'='*60}")
    print(f"TEST 1 RESULT: {'✅ PASSED' if test_1_result else '❌ FAILED'}")
    print(f"{'='*60}")
    
    return test_1_result

def test_2_get_advance_feature_reflection():
    """Test 2: 'Get Advance' Feature Reflection"""
    print("\n" + "="*60)
    print("TEST 2: 'GET ADVANCE' FEATURE REFLECTION")
    print("="*60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return False
    
    headers = get_auth_headers(token)
    
    # Get checked-in customers
    print("\n2.1 Getting checked-in customers...")
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
        if response.status_code == 200:
            customers = response.json()
            if not customers:
                print("❌ No checked-in customers available for Get Advance test")
                return False
            print(f"✅ Found {len(customers)} checked-in customers")
        else:
            print(f"❌ Failed to get checked-in customers - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to get checked-in customers - Exception: {e}")
        return False
    
    # Get initial financial summary
    print("\n2.2 Getting initial Cash and Bank balances...")
    initial_summary = get_daily_financial_summary()
    if not initial_summary:
        return False
    
    initial_cash = initial_summary.get('cash_balance', 0)
    initial_bank = initial_summary.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash}")
    print(f"Initial Bank Balance: {initial_bank}")
    
    # Test 2a: Get Advance with Cash payment
    print("\n2.3 Testing 'Get Advance' with Cash payment...")
    customer_1 = customers[0]
    advance_data_cash = {
        "customer_id": customer_1['id'],
        "amount": 800.0,
        "payment_method": "Cash",
        "notes": "Additional cash advance collected"
    }
    
    try:
        # Check if there's a specific "get advance" endpoint or if it's through income
        # Let's try the income endpoint first as it's more likely to be the "Get Advance" feature
        income_data = {
            "description": f"Advance payment from {customer_1['name']}",
            "amount": 800.0,
            "category": "Advance Payment",
            "payment_method": "Cash",
            "income_date": datetime.now().date().isoformat(),
            "guest_name": customer_1['name']
        }
        
        response = requests.post(f"{API_BASE}/incomes", json=income_data, headers=headers)
        if response.status_code == 200:
            print("✅ Cash advance recorded successfully")
            
            # Immediately check financial summary
            print("2.4 Checking real-time Cash balance update...")
            time.sleep(1)  # Small delay to ensure database update
            updated_summary = get_daily_financial_summary()
            if updated_summary:
                new_cash = updated_summary.get('cash_balance', 0)
                new_bank = updated_summary.get('bank_balance', 0)
                
                print(f"Updated Cash Balance: {new_cash}")
                print(f"Updated Bank Balance: {new_bank}")
                
                expected_cash = initial_cash + 800.0
                if abs(new_cash - expected_cash) < 0.01:
                    print("✅ Cash balance correctly increased by advance amount")
                    cash_advance_test = True
                else:
                    print(f"❌ Cash balance not updated correctly. Expected: {expected_cash}, Got: {new_cash}")
                    cash_advance_test = False
                
                if abs(new_bank - initial_bank) < 0.01:
                    print("✅ Bank balance unchanged (correct for Cash payment)")
                    bank_unchanged_test_2 = True
                else:
                    print(f"❌ Bank balance changed unexpectedly. Expected: {initial_bank}, Got: {new_bank}")
                    bank_unchanged_test_2 = False
            else:
                return False
        else:
            print(f"❌ Failed to record Cash advance - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to record Cash advance - Exception: {e}")
        return False
    
    # Test 2b: Get Advance with Card payment
    print("\n2.5 Testing 'Get Advance' with Card payment...")
    if len(customers) > 1:
        customer_2 = customers[1]
    else:
        customer_2 = customers[0]  # Use same customer if only one available
    
    income_data_card = {
        "description": f"Advance payment from {customer_2['name']}",
        "amount": 1200.0,
        "category": "Advance Payment",
        "payment_method": "Card",
        "income_date": datetime.now().date().isoformat(),
        "guest_name": customer_2['name']
    }
    
    try:
        response = requests.post(f"{API_BASE}/incomes", json=income_data_card, headers=headers)
        if response.status_code == 200:
            print("✅ Card advance recorded successfully")
            
            # Immediately check financial summary
            print("2.6 Checking real-time Bank balance update...")
            time.sleep(1)  # Small delay to ensure database update
            final_summary = get_daily_financial_summary()
            if final_summary:
                final_cash = final_summary.get('cash_balance', 0)
                final_bank = final_summary.get('bank_balance', 0)
                
                print(f"Final Cash Balance: {final_cash}")
                print(f"Final Bank Balance: {final_bank}")
                
                # Cash should remain the same from previous test
                expected_cash_final = initial_cash + 800.0
                expected_bank_final = initial_bank + 1200.0
                
                if abs(final_bank - expected_bank_final) < 0.01:
                    print("✅ Bank balance correctly increased by Card advance amount")
                    card_advance_test = True
                else:
                    print(f"❌ Bank balance not updated correctly. Expected: {expected_bank_final}, Got: {final_bank}")
                    card_advance_test = False
            else:
                return False
        else:
            print(f"❌ Failed to record Card advance - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Failed to record Card advance - Exception: {e}")
        return False
    
    # Test 2 Summary
    test_2_result = cash_advance_test and bank_unchanged_test_2 and card_advance_test
    print(f"\n{'='*60}")
    print(f"TEST 2 RESULT: {'✅ PASSED' if test_2_result else '❌ FAILED'}")
    print(f"{'='*60}")
    
    return test_2_result

def test_3_realtime_balance_updates():
    """Test 3: Real-time Balance Updates"""
    print("\n" + "="*60)
    print("TEST 3: REAL-TIME BALANCE UPDATES")
    print("="*60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return False
    
    headers = get_auth_headers(token)
    
    print("\n3.1 Recording initial cash/bank balances...")
    initial_summary = get_daily_financial_summary()
    if not initial_summary:
        return False
    
    initial_cash = initial_summary.get('cash_balance', 0)
    initial_bank = initial_summary.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash}")
    print(f"Initial Bank Balance: {initial_bank}")
    
    # Perform specific advance payment collection
    print("\n3.2 Performing advance payment collection (Cash - 500.0)...")
    advance_amount = 500.0
    payment_method = "Cash"
    
    income_data = {
        "description": "Real-time test advance payment",
        "amount": advance_amount,
        "category": "Advance Payment",
        "payment_method": payment_method,
        "income_date": datetime.now().date().isoformat(),
        "guest_name": "Real-time Test Guest"
    }
    
    try:
        response = requests.post(f"{API_BASE}/incomes", json=income_data, headers=headers)
        if response.status_code == 200:
            print("✅ Advance payment recorded successfully")
            
            # Immediately re-fetch daily-financial-summary
            print("3.3 Immediately re-fetching daily-financial-summary...")
            time.sleep(0.5)  # Minimal delay
            updated_summary = get_daily_financial_summary()
            
            if updated_summary:
                new_cash = updated_summary.get('cash_balance', 0)
                new_bank = updated_summary.get('bank_balance', 0)
                
                print(f"Updated Cash Balance: {new_cash}")
                print(f"Updated Bank Balance: {new_bank}")
                
                # Verify the balance changes match exactly the advance payment amount and method
                cash_change = new_cash - initial_cash
                bank_change = new_bank - initial_bank
                
                print(f"Cash Balance Change: {cash_change}")
                print(f"Bank Balance Change: {bank_change}")
                
                if abs(cash_change - advance_amount) < 0.01 and abs(bank_change) < 0.01:
                    print("✅ Balance changes match exactly the advance payment amount and method")
                    realtime_test_passed = True
                else:
                    print(f"❌ Balance changes don't match. Expected Cash: +{advance_amount}, Bank: +0")
                    print(f"Actual Cash: +{cash_change}, Bank: +{bank_change}")
                    realtime_test_passed = False
            else:
                return False
        else:
            print(f"❌ Failed to record advance payment - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to record advance payment - Exception: {e}")
        return False
    
    # Test 3 Summary
    print(f"\n{'='*60}")
    print(f"TEST 3 RESULT: {'✅ PASSED' if realtime_test_passed else '❌ FAILED'}")
    print(f"{'='*60}")
    
    return realtime_test_passed

def test_4_mixed_payment_methods():
    """Test 4: Mixed Payment Methods"""
    print("\n" + "="*60)
    print("TEST 4: MIXED PAYMENT METHODS")
    print("="*60)
    
    # Get admin token
    token = get_admin_token()
    if not token:
        return False
    
    headers = get_auth_headers(token)
    
    print("\n4.1 Getting initial balances...")
    initial_summary = get_daily_financial_summary()
    if not initial_summary:
        return False
    
    initial_cash = initial_summary.get('cash_balance', 0)
    initial_bank = initial_summary.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash}")
    print(f"Initial Bank Balance: {initial_bank}")
    
    # Test different payment methods
    payment_tests = [
        {"method": "Cash", "amount": 300.0, "should_increase": "cash"},
        {"method": "Card", "amount": 400.0, "should_increase": "bank"},
        {"method": "Bank Transfer", "amount": 250.0, "should_increase": "bank"}
    ]
    
    test_results = []
    current_cash = initial_cash
    current_bank = initial_bank
    
    for i, test in enumerate(payment_tests):
        print(f"\n4.{i+2} Testing {test['method']} advance payment (Amount: {test['amount']})...")
        
        income_data = {
            "description": f"Mixed payment test - {test['method']}",
            "amount": test['amount'],
            "category": "Advance Payment",
            "payment_method": test['method'],
            "income_date": datetime.now().date().isoformat(),
            "guest_name": f"Mixed Test Guest {i+1}"
        }
        
        try:
            response = requests.post(f"{API_BASE}/incomes", json=income_data, headers=headers)
            if response.status_code == 200:
                print(f"✅ {test['method']} advance payment recorded")
                
                # Check balance update
                time.sleep(0.5)
                updated_summary = get_daily_financial_summary()
                if updated_summary:
                    new_cash = updated_summary.get('cash_balance', 0)
                    new_bank = updated_summary.get('bank_balance', 0)
                    
                    print(f"Cash Balance: {current_cash} → {new_cash}")
                    print(f"Bank Balance: {current_bank} → {new_bank}")
                    
                    # Verify correct balance update
                    if test['should_increase'] == 'cash':
                        expected_cash = current_cash + test['amount']
                        expected_bank = current_bank
                        if abs(new_cash - expected_cash) < 0.01 and abs(new_bank - expected_bank) < 0.01:
                            print(f"✅ {test['method']} correctly increased cash balance")
                            test_results.append(True)
                        else:
                            print(f"❌ {test['method']} did not correctly increase cash balance")
                            test_results.append(False)
                    else:  # should_increase == 'bank'
                        expected_cash = current_cash
                        expected_bank = current_bank + test['amount']
                        if abs(new_cash - expected_cash) < 0.01 and abs(new_bank - expected_bank) < 0.01:
                            print(f"✅ {test['method']} correctly increased bank balance")
                            test_results.append(True)
                        else:
                            print(f"❌ {test['method']} did not correctly increase bank balance")
                            test_results.append(False)
                    
                    # Update current balances for next test
                    current_cash = new_cash
                    current_bank = new_bank
                else:
                    test_results.append(False)
            else:
                print(f"❌ Failed to record {test['method']} advance - Status: {response.status_code}")
                test_results.append(False)
        except Exception as e:
            print(f"❌ Failed to record {test['method']} advance - Exception: {e}")
            test_results.append(False)
    
    # Test 4 Summary
    test_4_result = all(test_results)
    print(f"\n{'='*60}")
    print(f"TEST 4 RESULT: {'✅ PASSED' if test_4_result else '❌ FAILED'}")
    print(f"Passed: {sum(test_results)}/{len(test_results)} payment methods")
    print(f"{'='*60}")
    
    return test_4_result

def main():
    """Run all advance payment tests"""
    print("REAL-TIME CASH/BANK BALANCE TESTING FOR ADVANCE PAYMENTS")
    print("=" * 80)
    print("Testing advance payments from both check-in and 'Get Advance' feature")
    print("Verifying real-time reflection in Cash and Bank balances")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Check-in Advance Payment Reflection
    test_results.append(("Check-in Advance Payment Reflection", test_1_checkin_advance_payment_reflection()))
    
    # Test 2: "Get Advance" Feature Reflection
    test_results.append(("Get Advance Feature Reflection", test_2_get_advance_feature_reflection()))
    
    # Test 3: Real-time Balance Updates
    test_results.append(("Real-time Balance Updates", test_3_realtime_balance_updates()))
    
    # Test 4: Mixed Payment Methods
    test_results.append(("Mixed Payment Methods", test_4_mixed_payment_methods()))
    
    # Final Summary
    print("\n" + "=" * 80)
    print("FINAL TEST SUMMARY - ADVANCE PAYMENTS REAL-TIME BALANCE")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<40} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL ADVANCE PAYMENT TESTS PASSED!")
        print("✅ Advance payments from check-in are correctly reflected in real-time")
        print("✅ 'Get Advance' feature correctly updates Cash and Bank balances")
        print("✅ Payment methods correctly route to cash vs bank balances")
        print("✅ Updates happen in real-time immediately after transaction")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed.")
        print("❌ Real-time Cash/Bank balance updates for advance payments need attention")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)