#!/usr/bin/env python3
"""
Daily Financial Summary API Testing for Inc & Exp Page Enhancement
Tests the new /api/daily-financial-summary endpoint and Bank Transfer payment method functionality.
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

print(f"Testing Daily Financial Summary API at: {API_BASE}")
print("=" * 80)

def test_health_check():
    """Test GET /api/ - Basic health check to ensure backend is running"""
    print("\n1. Testing Health Check (GET /api/)")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            if data.get("message") == "Hotel Management API":
                print("✅ Health check PASSED - Backend is running")
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

def test_daily_financial_summary_endpoint():
    """Test GET /api/daily-financial-summary - New daily financial summary endpoint"""
    print("\n2. Testing Daily Financial Summary Endpoint (GET /api/daily-financial-summary)")
    try:
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response structure: {list(data.keys())}")
            
            # Verify required fields are present
            required_fields = [
                'total_revenue', 'total_expenses', 'cash_balance', 
                'bank_balance', 'payment_method_breakdown', 'date'
            ]
            
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("✅ All required fields present in response:")
                print(f"  - total_revenue: {data.get('total_revenue')}")
                print(f"  - total_expenses: {data.get('total_expenses')}")
                print(f"  - cash_balance: {data.get('cash_balance')}")
                print(f"  - bank_balance: {data.get('bank_balance')}")
                print(f"  - payment_method_breakdown: {data.get('payment_method_breakdown')}")
                print(f"  - date: {data.get('date')}")
                
                # Verify date is current day
                today = datetime.now().date().isoformat()
                response_date = data.get('date')
                
                if response_date == today:
                    print(f"✅ Date verification PASSED - Returns current day data ({today})")
                    return True, data
                else:
                    print(f"❌ Date verification FAILED - Expected {today}, got {response_date}")
                    return False, data
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False, data
        else:
            print(f"❌ Daily financial summary endpoint FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, {}
    except Exception as e:
        print(f"❌ Daily financial summary endpoint FAILED - Exception: {e}")
        return False, {}

def test_payment_method_balance_calculation():
    """Test that cash_balance and bank_balance are calculated correctly based on payment methods"""
    print("\n3. Testing Payment Method Balance Calculations")
    
    # First, initialize sample data and create some daily sales with different payment methods
    print("Initializing sample data...")
    try:
        init_response = requests.post(f"{API_BASE}/init-data")
        if init_response.status_code != 200:
            print("❌ Could not initialize sample data")
            return False
        
        # Get checked-in customers for checkout tests
        customers_response = requests.get(f"{API_BASE}/customers/checked-in")
        if customers_response.status_code != 200:
            print("❌ Could not get checked-in customers")
            return False
        
        customers = customers_response.json()
        if len(customers) < 3:
            print("❌ Need at least 3 customers for payment method testing")
            return False
        
        # Perform checkouts with different payment methods
        payment_methods = ["Cash", "Card", "Bank Transfer"]
        checkout_amounts = []
        
        for i, payment_method in enumerate(payment_methods):
            if i >= len(customers):
                break
                
            customer = customers[i]
            checkout_data = {
                "customer_id": customer['id'],
                "additional_amount": 100.0 * (i + 1),  # Different amounts for each
                "discount_amount": 25.0,
                "payment_method": payment_method
            }
            
            print(f"Performing checkout with {payment_method} payment...")
            checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data)
            
            if checkout_response.status_code == 200:
                result = checkout_response.json()
                billing_details = result.get("billing_details", {})
                total_amount = billing_details.get("total_amount", 0)
                checkout_amounts.append((payment_method, total_amount))
                print(f"✅ {payment_method} checkout successful - Amount: {total_amount}")
            else:
                print(f"❌ {payment_method} checkout failed")
                return False
        
        # Now test the daily financial summary
        print("\nTesting daily financial summary after checkouts...")
        summary_response = requests.get(f"{API_BASE}/daily-financial-summary")
        
        if summary_response.status_code != 200:
            print("❌ Could not get daily financial summary")
            return False
        
        summary_data = summary_response.json()
        cash_balance = summary_data.get('cash_balance', 0)
        bank_balance = summary_data.get('bank_balance', 0)
        payment_breakdown = summary_data.get('payment_method_breakdown', {})
        
        print(f"Payment method breakdown: {payment_breakdown}")
        print(f"Cash balance: {cash_balance}")
        print(f"Bank balance: {bank_balance}")
        
        # Verify cash balance includes only Cash payments
        expected_cash = payment_breakdown.get('Cash', 0)
        if cash_balance == expected_cash:
            print(f"✅ Cash balance calculation PASSED - {cash_balance} (Cash payments only)")
        else:
            print(f"❌ Cash balance calculation FAILED - Expected {expected_cash}, got {cash_balance}")
            return False
        
        # Verify bank balance includes Card and Bank Transfer payments
        expected_bank = payment_breakdown.get('Card', 0) + payment_breakdown.get('Bank Transfer', 0)
        if bank_balance == expected_bank:
            print(f"✅ Bank balance calculation PASSED - {bank_balance} (Card + Bank Transfer payments)")
        else:
            print(f"❌ Bank balance calculation FAILED - Expected {expected_bank}, got {bank_balance}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Payment method balance calculation test FAILED - Exception: {e}")
        return False

def test_bank_transfer_payment_method():
    """Test that Bank Transfer payment method works correctly in checkout"""
    print("\n4. Testing Bank Transfer Payment Method in Checkout")
    
    try:
        # Reinitialize data to get fresh customers
        print("Reinitializing sample data for Bank Transfer test...")
        init_response = requests.post(f"{API_BASE}/init-data")
        if init_response.status_code != 200:
            print("❌ Could not reinitialize sample data")
            return False
        
        # Get a customer for checkout
        customers_response = requests.get(f"{API_BASE}/customers/checked-in")
        if customers_response.status_code != 200:
            print("❌ Could not get checked-in customers")
            return False
        
        customers = customers_response.json()
        if not customers:
            print("❌ No customers available for Bank Transfer test")
            return False
        
        test_customer = customers[0]
        customer_id = test_customer['id']
        customer_name = test_customer['name']
        
        print(f"Testing Bank Transfer checkout for customer: {customer_name}")
        
        # Perform checkout with Bank Transfer
        checkout_data = {
            "customer_id": customer_id,
            "additional_amount": 150.0,
            "discount_amount": 30.0,
            "payment_method": "Bank Transfer"
        }
        
        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data)
        print(f"Checkout Status Code: {checkout_response.status_code}")
        
        if checkout_response.status_code == 200:
            result = checkout_response.json()
            billing_details = result.get("billing_details", {})
            
            if billing_details.get('payment_method') == 'Bank Transfer':
                print("✅ Bank Transfer payment method PASSED - Correctly recorded in billing")
                
                # Verify it appears in daily sales
                sales_response = requests.get(f"{API_BASE}/daily-sales")
                if sales_response.status_code == 200:
                    sales_data = sales_response.json()
                    bank_transfer_sales = [sale for sale in sales_data if sale.get('payment_method') == 'Bank Transfer']
                    
                    if bank_transfer_sales:
                        print("✅ Bank Transfer payment method PASSED - Recorded in daily sales")
                        return True
                    else:
                        print("❌ Bank Transfer payment method FAILED - Not found in daily sales")
                        return False
                else:
                    print("❌ Could not verify Bank Transfer in daily sales")
                    return False
            else:
                print(f"❌ Bank Transfer payment method FAILED - Expected 'Bank Transfer', got '{billing_details.get('payment_method')}'")
                return False
        else:
            print(f"❌ Bank Transfer checkout FAILED - Status code: {checkout_response.status_code}")
            print(f"Response: {checkout_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Bank Transfer payment method test FAILED - Exception: {e}")
        return False

def test_current_day_data_only():
    """Test that the endpoint returns current day data only"""
    print("\n5. Testing Current Day Data Only Requirement")
    
    try:
        # Get the daily financial summary
        response = requests.get(f"{API_BASE}/daily-financial-summary")
        
        if response.status_code != 200:
            print("❌ Could not get daily financial summary")
            return False
        
        summary_data = response.json()
        response_date = summary_data.get('date')
        today = datetime.now().date().isoformat()
        
        if response_date == today:
            print(f"✅ Current day data verification PASSED - Date: {response_date}")
            
            # Additional verification: Check that the data reflects only today's transactions
            # by comparing with daily sales for today
            sales_response = requests.get(f"{API_BASE}/daily-sales")
            if sales_response.status_code == 200:
                sales_data = sales_response.json()
                today_sales = [sale for sale in sales_data if sale.get('date') == today]
                
                # Calculate expected totals from today's sales
                expected_revenue = sum(sale.get('total_amount', 0) for sale in today_sales)
                actual_revenue = summary_data.get('total_revenue', 0)
                
                # Note: actual_revenue might include additional income, so it could be >= expected_revenue
                if actual_revenue >= expected_revenue:
                    print(f"✅ Revenue calculation consistency PASSED - Summary revenue ({actual_revenue}) >= Daily sales revenue ({expected_revenue})")
                    return True
                else:
                    print(f"❌ Revenue calculation inconsistency - Summary revenue ({actual_revenue}) < Daily sales revenue ({expected_revenue})")
                    return False
            else:
                print("⚠️ Could not verify against daily sales, but date check passed")
                return True
        else:
            print(f"❌ Current day data verification FAILED - Expected {today}, got {response_date}")
            return False
            
    except Exception as e:
        print(f"❌ Current day data test FAILED - Exception: {e}")
        return False

def main():
    """Run all daily financial summary tests"""
    print("Starting Daily Financial Summary API Tests for Inc & Exp Page Enhancement")
    print("=" * 80)
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(("Health Check", test_health_check()))
    
    # Test 2: Daily Financial Summary Endpoint Structure
    endpoint_passed, summary_data = test_daily_financial_summary_endpoint()
    test_results.append(("Daily Financial Summary Endpoint", endpoint_passed))
    
    # Test 3: Payment Method Balance Calculations
    test_results.append(("Payment Method Balance Calculations", test_payment_method_balance_calculation()))
    
    # Test 4: Bank Transfer Payment Method
    test_results.append(("Bank Transfer Payment Method", test_bank_transfer_payment_method()))
    
    # Test 5: Current Day Data Only
    test_results.append(("Current Day Data Only", test_current_day_data_only()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY - DAILY FINANCIAL SUMMARY API")
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
        print("\n🎉 ALL TESTS PASSED! Daily Financial Summary API is working correctly.")
        print("✅ New /api/daily-financial-summary endpoint is functional and ready for Inc & Exp page enhancement.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)