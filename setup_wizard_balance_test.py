#!/usr/bin/env python3
"""
Setup Wizard with Cash and Bank Balance Initialization Testing
Tests the new Setup Wizard feature that accepts cash_balance and bank_balance fields
and creates initial income records to establish opening balances.
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

print(f"Testing Setup Wizard with Cash and Bank Balance Initialization at: {API_BASE}")
print("=" * 80)

# Global variables for test data
auth_token = None
test_results = []

def authenticate():
    """Authenticate and get JWT token"""
    print("\n🔐 Authenticating...")
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if response.status_code == 200:
            data = response.json()
            global auth_token
            auth_token = data.get("access_token")
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False

def get_auth_headers():
    """Get authorization headers"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def reset_setup_for_testing():
    """Reset setup status for testing"""
    print("\n🔄 Resetting setup status for testing...")
    try:
        # First, let's check if we can access the database directly or use admin reset
        response = requests.post(f"{API_BASE}/admin/complete-reset", headers=get_auth_headers())
        if response.status_code == 200:
            print("✅ System reset successful")
            return True
        else:
            print(f"⚠️ Could not reset system: {response.status_code}")
            # Continue anyway as setup might not be completed yet
            return True
    except Exception as e:
        print(f"⚠️ Reset error (continuing anyway): {str(e)}")
        return True

def test_setup_status_check():
    """Test GET /api/setup/status"""
    print("\n1. Testing Setup Status Check (GET /api/setup/status)")
    try:
        response = requests.get(f"{API_BASE}/setup/status")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            is_completed = data.get("is_completed", False)
            print(f"Setup completed: {is_completed}")
            print("✅ Setup status check PASSED")
            test_results.append(("Setup Status Check", True, "Setup status endpoint working correctly"))
            return True, is_completed
        else:
            print(f"❌ Setup status check FAILED: {response.status_code} - {response.text}")
            test_results.append(("Setup Status Check", False, f"Status code: {response.status_code}"))
            return False, False
    except Exception as e:
        print(f"❌ Setup status check ERROR: {str(e)}")
        test_results.append(("Setup Status Check", False, f"Exception: {str(e)}"))
        return False, False

def test_setup_completion_with_balances():
    """Test POST /api/setup/complete with cash and bank balances"""
    print("\n2. Testing Setup Completion with Cash and Bank Balances")
    
    setup_data = {
        "hotel_name": "Test Hotel Balance Setup",
        "hotel_address": "123 Test Street, Test City",
        "hotel_email": "test@testhotel.com",
        "timezone": "Asia/Colombo",
        "cash_balance": 5000.0,
        "bank_balance": 10000.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/setup/complete", json=setup_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Setup completion response: {data}")
            print("✅ Setup completion with balances PASSED")
            test_results.append(("Setup Completion with Balances", True, "Setup completed successfully with cash and bank balances"))
            return True
        else:
            print(f"❌ Setup completion FAILED: {response.status_code} - {response.text}")
            test_results.append(("Setup Completion with Balances", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Setup completion ERROR: {str(e)}")
        test_results.append(("Setup Completion with Balances", False, f"Exception: {str(e)}"))
        return False

def test_initial_income_records():
    """Test that initial income records are created for cash and bank balances"""
    print("\n3. Testing Initial Income Records Creation (GET /api/incomes)")
    
    try:
        response = requests.get(f"{API_BASE}/incomes", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            incomes = response.json()
            print(f"Found {len(incomes)} income records")
            
            # Look for initial setup income records
            cash_setup_record = None
            bank_setup_record = None
            
            for income in incomes:
                print(f"Income: {income.get('description')} - {income.get('amount')} - {income.get('category')} - {income.get('payment_method')}")
                
                if income.get('category') == 'Initial Setup':
                    if income.get('payment_method') == 'Cash':
                        cash_setup_record = income
                    elif income.get('payment_method') == 'Bank Transfer':
                        bank_setup_record = income
            
            # Verify cash balance record
            if cash_setup_record:
                if cash_setup_record.get('amount') == 5000.0:
                    print("✅ Cash balance initial record found and correct")
                else:
                    print(f"❌ Cash balance amount incorrect: expected 5000.0, got {cash_setup_record.get('amount')}")
                    test_results.append(("Initial Cash Income Record", False, f"Incorrect amount: {cash_setup_record.get('amount')}"))
                    return False
            else:
                print("❌ Cash balance initial record not found")
                test_results.append(("Initial Cash Income Record", False, "Cash setup record not found"))
                return False
            
            # Verify bank balance record
            if bank_setup_record:
                if bank_setup_record.get('amount') == 10000.0:
                    print("✅ Bank balance initial record found and correct")
                else:
                    print(f"❌ Bank balance amount incorrect: expected 10000.0, got {bank_setup_record.get('amount')}")
                    test_results.append(("Initial Bank Income Record", False, f"Incorrect amount: {bank_setup_record.get('amount')}"))
                    return False
            else:
                print("❌ Bank balance initial record not found")
                test_results.append(("Initial Bank Income Record", False, "Bank setup record not found"))
                return False
            
            print("✅ Initial income records verification PASSED")
            test_results.append(("Initial Income Records", True, "Both cash and bank setup records created correctly"))
            return True
            
        else:
            print(f"❌ Income records check FAILED: {response.status_code} - {response.text}")
            test_results.append(("Initial Income Records", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Income records check ERROR: {str(e)}")
        test_results.append(("Initial Income Records", False, f"Exception: {str(e)}"))
        return False

def test_daily_financial_summary():
    """Test that balances are reflected in daily financial summary"""
    print("\n4. Testing Daily Financial Summary Reflects Initial Balances")
    
    try:
        today = datetime.now().date().isoformat()
        response = requests.get(f"{API_BASE}/daily-financial-summary?date={today}", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            summary = response.json()
            print(f"Financial Summary: {json.dumps(summary, indent=2)}")
            
            # Check if cash and bank balances are reflected
            cash_balance = summary.get('cash_balance', 0)
            bank_balance = summary.get('bank_balance', 0)
            total_income = summary.get('total_income', 0)
            
            print(f"Cash Balance: {cash_balance}")
            print(f"Bank Balance: {bank_balance}")
            print(f"Total Income: {total_income}")
            
            # Verify balances
            expected_cash = 5000.0
            expected_bank = 10000.0
            expected_total = 15000.0
            
            if cash_balance == expected_cash and bank_balance == expected_bank:
                print("✅ Daily financial summary reflects initial balances correctly")
                test_results.append(("Daily Financial Summary", True, f"Cash: {cash_balance}, Bank: {bank_balance}"))
                return True
            else:
                print(f"❌ Financial summary balances incorrect - Cash: {cash_balance} (expected {expected_cash}), Bank: {bank_balance} (expected {expected_bank})")
                test_results.append(("Daily Financial Summary", False, f"Incorrect balances - Cash: {cash_balance}, Bank: {bank_balance}"))
                return False
                
        else:
            print(f"❌ Financial summary check FAILED: {response.status_code} - {response.text}")
            test_results.append(("Daily Financial Summary", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Financial summary check ERROR: {str(e)}")
        test_results.append(("Daily Financial Summary", False, f"Exception: {str(e)}"))
        return False

def test_setup_with_zero_balances():
    """Test setup completion with zero balances"""
    print("\n5. Testing Setup Completion with Zero Balances")
    
    # First reset the system
    reset_setup_for_testing()
    
    setup_data = {
        "hotel_name": "Test Hotel Zero Balance",
        "hotel_address": "456 Zero Street, Zero City",
        "hotel_email": "zero@testhotel.com",
        "timezone": "UTC",
        "cash_balance": 0.0,
        "bank_balance": 0.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/setup/complete", json=setup_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Setup completion with zero balances PASSED")
            test_results.append(("Setup with Zero Balances", True, "Setup completed successfully with zero balances"))
            return True
        else:
            print(f"❌ Setup with zero balances FAILED: {response.status_code} - {response.text}")
            test_results.append(("Setup with Zero Balances", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Setup with zero balances ERROR: {str(e)}")
        test_results.append(("Setup with Zero Balances", False, f"Exception: {str(e)}"))
        return False

def test_setup_with_partial_balances():
    """Test setup completion with only cash or only bank balance"""
    print("\n6. Testing Setup Completion with Partial Balances")
    
    # Test with only cash balance
    print("\n6a. Testing with only cash balance")
    reset_setup_for_testing()
    
    setup_data_cash_only = {
        "hotel_name": "Test Hotel Cash Only",
        "hotel_address": "789 Cash Street, Cash City",
        "hotel_email": "cash@testhotel.com",
        "timezone": "UTC",
        "cash_balance": 3000.0,
        "bank_balance": 0.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/setup/complete", json=setup_data_cash_only)
        if response.status_code == 200:
            print("✅ Setup with cash only PASSED")
            
            # Verify only cash income record is created
            income_response = requests.get(f"{API_BASE}/incomes", headers=get_auth_headers())
            if income_response.status_code == 200:
                incomes = income_response.json()
                cash_records = [i for i in incomes if i.get('category') == 'Initial Setup' and i.get('payment_method') == 'Cash']
                bank_records = [i for i in incomes if i.get('category') == 'Initial Setup' and i.get('payment_method') == 'Bank Transfer']
                
                if len(cash_records) == 1 and cash_records[0].get('amount') == 3000.0 and len(bank_records) == 0:
                    print("✅ Cash only setup verification PASSED")
                    test_results.append(("Setup Cash Only", True, "Only cash record created correctly"))
                else:
                    print(f"❌ Cash only verification FAILED - Cash records: {len(cash_records)}, Bank records: {len(bank_records)}")
                    test_results.append(("Setup Cash Only", False, f"Incorrect records created"))
                    return False
            else:
                print("❌ Could not verify cash only setup")
                test_results.append(("Setup Cash Only", False, "Could not verify income records"))
                return False
        else:
            print(f"❌ Setup with cash only FAILED: {response.status_code}")
            test_results.append(("Setup Cash Only", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Setup with cash only ERROR: {str(e)}")
        test_results.append(("Setup Cash Only", False, f"Exception: {str(e)}"))
        return False
    
    # Test with only bank balance
    print("\n6b. Testing with only bank balance")
    reset_setup_for_testing()
    
    setup_data_bank_only = {
        "hotel_name": "Test Hotel Bank Only",
        "hotel_address": "101 Bank Street, Bank City",
        "hotel_email": "bank@testhotel.com",
        "timezone": "UTC",
        "cash_balance": 0.0,
        "bank_balance": 7500.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/setup/complete", json=setup_data_bank_only)
        if response.status_code == 200:
            print("✅ Setup with bank only PASSED")
            
            # Verify only bank income record is created
            income_response = requests.get(f"{API_BASE}/incomes", headers=get_auth_headers())
            if income_response.status_code == 200:
                incomes = income_response.json()
                cash_records = [i for i in incomes if i.get('category') == 'Initial Setup' and i.get('payment_method') == 'Cash']
                bank_records = [i for i in incomes if i.get('category') == 'Initial Setup' and i.get('payment_method') == 'Bank Transfer']
                
                if len(bank_records) == 1 and bank_records[0].get('amount') == 7500.0 and len(cash_records) == 0:
                    print("✅ Bank only setup verification PASSED")
                    test_results.append(("Setup Bank Only", True, "Only bank record created correctly"))
                    return True
                else:
                    print(f"❌ Bank only verification FAILED - Cash records: {len(cash_records)}, Bank records: {len(bank_records)}")
                    test_results.append(("Setup Bank Only", False, f"Incorrect records created"))
                    return False
            else:
                print("❌ Could not verify bank only setup")
                test_results.append(("Setup Bank Only", False, "Could not verify income records"))
                return False
        else:
            print(f"❌ Setup with bank only FAILED: {response.status_code}")
            test_results.append(("Setup Bank Only", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Setup with bank only ERROR: {str(e)}")
        test_results.append(("Setup Bank Only", False, f"Exception: {str(e)}"))
        return False

def test_activity_logging():
    """Test that activity logging includes balance information"""
    print("\n7. Testing Activity Logging for Balance Setup")
    
    try:
        response = requests.get(f"{API_BASE}/activity-logs?action=setup_completed", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            print(f"Found {len(logs)} setup completion logs")
            
            # Look for setup completion log with balance information
            balance_log_found = False
            for log in logs:
                description = log.get('description', '')
                print(f"Log: {description}")
                
                if 'initial balances' in description.lower() and ('cash:' in description.lower() or 'bank:' in description.lower()):
                    balance_log_found = True
                    print("✅ Activity log with balance information found")
                    break
            
            if balance_log_found:
                test_results.append(("Activity Logging", True, "Setup completion logged with balance information"))
                return True
            else:
                print("❌ Activity log with balance information not found")
                test_results.append(("Activity Logging", False, "Balance information not found in activity logs"))
                return False
                
        else:
            print(f"❌ Activity logs check FAILED: {response.status_code} - {response.text}")
            test_results.append(("Activity Logging", False, f"Status code: {response.status_code}"))
            return False
    except Exception as e:
        print(f"❌ Activity logs check ERROR: {str(e)}")
        test_results.append(("Activity Logging", False, f"Exception: {str(e)}"))
        return False

def test_setup_wizard_data_storage():
    """Test that setup wizard data is stored with balance fields"""
    print("\n8. Testing Setup Wizard Data Storage with Balance Fields")
    
    # This test would require direct database access or a specific endpoint
    # For now, we'll verify through the setup status and settings endpoints
    
    try:
        # Check setup status
        setup_response = requests.get(f"{API_BASE}/setup/status")
        settings_response = requests.get(f"{API_BASE}/settings", headers=get_auth_headers())
        
        if setup_response.status_code == 200 and settings_response.status_code == 200:
            setup_data = setup_response.json()
            settings_data = settings_response.json()
            
            print(f"Setup completed: {setup_data.get('is_completed')}")
            print(f"Hotel name in settings: {settings_data.get('hotel_name')}")
            print(f"Hotel email in settings: {settings_data.get('hotel_email')}")
            print(f"Timezone in settings: {settings_data.get('timezone')}")
            
            if setup_data.get('is_completed') and settings_data.get('hotel_name'):
                print("✅ Setup wizard data storage verification PASSED")
                test_results.append(("Setup Data Storage", True, "Setup data properly stored in settings"))
                return True
            else:
                print("❌ Setup wizard data storage verification FAILED")
                test_results.append(("Setup Data Storage", False, "Setup data not properly stored"))
                return False
        else:
            print(f"❌ Setup data storage check FAILED - Setup: {setup_response.status_code}, Settings: {settings_response.status_code}")
            test_results.append(("Setup Data Storage", False, "Could not verify data storage"))
            return False
    except Exception as e:
        print(f"❌ Setup data storage check ERROR: {str(e)}")
        test_results.append(("Setup Data Storage", False, f"Exception: {str(e)}"))
        return False

def print_test_summary():
    """Print comprehensive test summary"""
    print("\n" + "=" * 80)
    print("SETUP WIZARD WITH CASH AND BANK BALANCE INITIALIZATION - TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed, details in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {test_name}: {details}")
        if passed:
            passed_tests += 1
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Setup Wizard with Cash and Bank Balance Initialization is working correctly!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Setup Wizard with Cash and Bank Balance Initialization needs attention")
        return False

def main():
    """Main test execution"""
    print("Starting Setup Wizard with Cash and Bank Balance Initialization Testing...")
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return False
    
    # Reset system for clean testing
    reset_setup_for_testing()
    
    # Run all tests
    test_setup_status_check()
    test_setup_completion_with_balances()
    test_initial_income_records()
    test_daily_financial_summary()
    test_setup_with_zero_balances()
    test_setup_with_partial_balances()
    test_activity_logging()
    test_setup_wizard_data_storage()
    
    # Print summary
    return print_test_summary()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)