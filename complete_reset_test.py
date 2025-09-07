#!/usr/bin/env python3
"""
Enhanced Complete Database Reset Functionality Testing
Tests the complete database reset feature that includes cash and bank balance re-initialization.
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

print(f"Testing Enhanced Complete Database Reset at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
auth_token = None

def get_admin_token():
    """Get admin authentication token"""
    global auth_token
    print("\n🔐 Getting admin authentication token...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data.get("access_token")
            print("✅ Admin authentication successful")
            return True
        else:
            print(f"❌ Admin authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Admin authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers with bearer token"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def test_setup_initial_data():
    """Setup initial data for testing complete reset functionality"""
    print("\n1. Setting up initial test data...")
    
    try:
        # Initialize sample data
        response = requests.post(f"{API_BASE}/init-data")
        if response.status_code != 200:
            print(f"❌ Failed to initialize sample data - Status: {response.status_code}")
            return False
        
        # Complete setup wizard with initial balances
        setup_data = {
            "hotel_name": "Test Hotel for Reset",
            "hotel_address": "123 Test Street, Test City",
            "hotel_email": "test@testhotel.com",
            "timezone": "UTC",
            "cash_balance": 5000.0,
            "bank_balance": 10000.0
        }
        
        setup_response = requests.post(f"{API_BASE}/setup/complete", json=setup_data)
        if setup_response.status_code == 200:
            print("✅ Initial setup completed with balances")
        elif setup_response.status_code == 400 and "already completed" in setup_response.text:
            print("✅ Setup already completed (expected)")
        else:
            print(f"❌ Setup completion failed - Status: {setup_response.status_code}")
            return False
        
        # Add some test expenses and incomes
        headers = get_auth_headers()
        
        # Add test expense
        expense_data = {
            "description": "Test Expense Before Reset",
            "amount": 500.0,
            "category": "Maintenance",
            "payment_method": "Cash",
            "expense_date": datetime.now().date().isoformat()
        }
        requests.post(f"{API_BASE}/expenses", json=expense_data, headers=headers)
        
        # Add test income
        income_data = {
            "description": "Test Income Before Reset",
            "amount": 1000.0,
            "category": "Restaurant",
            "payment_method": "Card",
            "income_date": datetime.now().date().isoformat()
        }
        requests.post(f"{API_BASE}/incomes", json=income_data, headers=headers)
        
        print("✅ Initial test data setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Initial data setup failed - Exception: {e}")
        return False

def test_pre_reset_data_verification():
    """Verify data exists before reset"""
    print("\n2. Verifying data exists before reset...")
    
    try:
        headers = get_auth_headers()
        
        # Check setup status
        setup_response = requests.get(f"{API_BASE}/setup/status")
        if setup_response.status_code == 200:
            setup_status = setup_response.json()
            if setup_status.get("is_completed"):
                print("✅ Setup wizard is completed (as expected)")
            else:
                print("❌ Setup wizard should be completed before reset")
                return False
        else:
            print(f"❌ Failed to get setup status - Status: {setup_response.status_code}")
            return False
        
        # Check rooms exist
        rooms_response = requests.get(f"{API_BASE}/rooms")
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            print(f"✅ Found {len(rooms)} rooms before reset")
        else:
            print("❌ Failed to get rooms data")
            return False
        
        # Check bookings exist
        bookings_response = requests.get(f"{API_BASE}/bookings")
        if bookings_response.status_code == 200:
            bookings_data = bookings_response.json()
            bookings = bookings_data.get("bookings", [])
            print(f"✅ Found {len(bookings)} bookings before reset")
        else:
            print("❌ Failed to get bookings data")
            return False
        
        # Check expenses exist
        expenses_response = requests.get(f"{API_BASE}/expenses", headers=headers)
        if expenses_response.status_code == 200:
            expenses = expenses_response.json()
            print(f"✅ Found {len(expenses)} expenses before reset")
        else:
            print("❌ Failed to get expenses data")
            return False
        
        # Check incomes exist
        incomes_response = requests.get(f"{API_BASE}/incomes", headers=headers)
        if incomes_response.status_code == 200:
            incomes = incomes_response.json()
            print(f"✅ Found {len(incomes)} incomes before reset")
        else:
            print("❌ Failed to get incomes data")
            return False
        
        print("✅ Pre-reset data verification completed")
        return True
        
    except Exception as e:
        print(f"❌ Pre-reset data verification failed - Exception: {e}")
        return False

def test_complete_database_reset():
    """Test the complete database reset endpoint"""
    print("\n3. Testing complete database reset endpoint...")
    
    try:
        headers = get_auth_headers()
        
        # Perform complete database reset
        response = requests.post(f"{API_BASE}/admin/complete-reset", headers=headers)
        print(f"Reset Status Code: {response.status_code}")
        
        if response.status_code == 200:
            reset_data = response.json()
            print(f"Reset Response: {json.dumps(reset_data, indent=2)}")
            
            # Verify response structure
            required_fields = ["message", "reset_summary", "requires_setup"]
            missing_fields = [field for field in required_fields if field not in reset_data]
            
            if missing_fields:
                print(f"❌ Missing required fields in response: {missing_fields}")
                return False
            
            # Verify requires_setup flag
            if reset_data.get("requires_setup") != True:
                print(f"❌ requires_setup should be True, got: {reset_data.get('requires_setup')}")
                return False
            
            # Verify reset_summary contains setup_wizard_reset
            reset_summary = reset_data.get("reset_summary", {})
            if reset_summary.get("setup_wizard_reset") != True:
                print(f"❌ setup_wizard_reset should be True, got: {reset_summary.get('setup_wizard_reset')}")
                return False
            
            # Verify collections were cleared
            expected_cleared = ["rooms", "bookings", "customers", "expenses", "incomes", "activity_logs", "daily_sales"]
            for collection in expected_cleared:
                if collection not in reset_summary:
                    print(f"❌ Collection '{collection}' not found in reset summary")
                    return False
                print(f"✅ Collection '{collection}' cleared: {reset_summary[collection]} records")
            
            print("✅ Complete database reset endpoint PASSED")
            return True
            
        else:
            print(f"❌ Complete database reset FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complete database reset test FAILED - Exception: {e}")
        return False

def test_setup_status_after_reset():
    """Test that setup status returns is_completed: false after reset"""
    print("\n4. Testing setup status after reset...")
    
    try:
        response = requests.get(f"{API_BASE}/setup/status")
        print(f"Setup Status Code: {response.status_code}")
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"Setup Status Response: {status_data}")
            
            if status_data.get("is_completed") == False:
                print("✅ Setup status correctly shows is_completed: false after reset")
                return True
            else:
                print(f"❌ Setup status should show is_completed: false, got: {status_data.get('is_completed')}")
                return False
        else:
            print(f"❌ Setup status check FAILED - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Setup status test FAILED - Exception: {e}")
        return False

def test_collections_cleared():
    """Test that expected collections are cleared after reset"""
    print("\n5. Testing that collections are cleared after reset...")
    
    try:
        headers = get_auth_headers()
        
        # Check rooms are cleared
        rooms_response = requests.get(f"{API_BASE}/rooms")
        if rooms_response.status_code == 200:
            rooms = rooms_response.json()
            if len(rooms) == 0:
                print("✅ Rooms collection cleared")
            else:
                print(f"❌ Rooms collection not cleared - Found {len(rooms)} rooms")
                return False
        else:
            print("❌ Failed to check rooms after reset")
            return False
        
        # Check bookings are cleared
        bookings_response = requests.get(f"{API_BASE}/bookings")
        if bookings_response.status_code == 200:
            bookings_data = bookings_response.json()
            bookings = bookings_data.get("bookings", [])
            if len(bookings) == 0:
                print("✅ Bookings collection cleared")
            else:
                print(f"❌ Bookings collection not cleared - Found {len(bookings)} bookings")
                return False
        else:
            print("❌ Failed to check bookings after reset")
            return False
        
        # Check expenses are cleared
        expenses_response = requests.get(f"{API_BASE}/expenses", headers=headers)
        if expenses_response.status_code == 200:
            expenses = expenses_response.json()
            if len(expenses) == 0:
                print("✅ Expenses collection cleared")
            else:
                print(f"❌ Expenses collection not cleared - Found {len(expenses)} expenses")
                return False
        else:
            print("❌ Failed to check expenses after reset")
            return False
        
        # Check incomes are cleared
        incomes_response = requests.get(f"{API_BASE}/incomes", headers=headers)
        if incomes_response.status_code == 200:
            incomes = incomes_response.json()
            if len(incomes) == 0:
                print("✅ Incomes collection cleared")
            else:
                print(f"❌ Incomes collection not cleared - Found {len(incomes)} incomes")
                return False
        else:
            print("❌ Failed to check incomes after reset")
            return False
        
        # Check customers are cleared
        customers_response = requests.get(f"{API_BASE}/customers/checked-in")
        if customers_response.status_code == 200:
            customers = customers_response.json()
            if len(customers) == 0:
                print("✅ Customers collection cleared")
            else:
                print(f"❌ Customers collection not cleared - Found {len(customers)} customers")
                return False
        else:
            print("❌ Failed to check customers after reset")
            return False
        
        print("✅ All expected collections cleared after reset")
        return True
        
    except Exception as e:
        print(f"❌ Collections clearing test FAILED - Exception: {e}")
        return False

def test_hotel_settings_preserved():
    """Test that hotel settings are preserved but setup_wizard is reset"""
    print("\n6. Testing that hotel settings are preserved...")
    
    try:
        headers = get_auth_headers()
        
        # Check hotel settings
        settings_response = requests.get(f"{API_BASE}/settings", headers=headers)
        if settings_response.status_code == 200:
            settings = settings_response.json()
            print(f"Hotel settings after reset: {settings.get('hotel_name', 'No name')}")
            
            # Settings should exist (either preserved or default)
            if settings.get("hotel_name"):
                print("✅ Hotel settings preserved/exist after reset")
            else:
                print("❌ Hotel settings missing after reset")
                return False
        else:
            print(f"❌ Failed to get hotel settings - Status: {settings_response.status_code}")
            return False
        
        # Verify admin account still exists
        users_response = requests.get(f"{API_BASE}/users", headers=headers)
        if users_response.status_code == 200:
            users = users_response.json()
            admin_users = [user for user in users if user.get("username") == "admin"]
            
            if admin_users:
                print("✅ Admin account preserved after reset")
            else:
                print("❌ Admin account not found after reset")
                return False
        else:
            print(f"❌ Failed to get users - Status: {users_response.status_code}")
            return False
        
        print("✅ Hotel settings and admin account preservation test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Hotel settings preservation test FAILED - Exception: {e}")
        return False

def test_activity_logging():
    """Test that reset activity is properly logged"""
    print("\n7. Testing activity logging for reset...")
    
    try:
        headers = get_auth_headers()
        
        # Get activity logs
        logs_response = requests.get(f"{API_BASE}/activity-logs?action=complete_system_reset", headers=headers)
        if logs_response.status_code == 200:
            logs_data = logs_response.json()
            logs = logs_data.get("logs", [])
            
            if logs:
                reset_log = logs[0]  # Most recent log
                print(f"Reset activity log found:")
                print(f"  Action: {reset_log.get('action')}")
                print(f"  Description: {reset_log.get('description')}")
                print(f"  User: {reset_log.get('user_name')}")
                print(f"  Entity Type: {reset_log.get('entity_type')}")
                
                # Verify log contains setup_wizard information
                details = reset_log.get("details", {})
                if details.get("setup_wizard_reset") == True:
                    print("✅ Activity log contains setup_wizard_reset information")
                    return True
                else:
                    print("❌ Activity log missing setup_wizard_reset information")
                    return False
            else:
                print("❌ No reset activity log found")
                return False
        else:
            print(f"❌ Failed to get activity logs - Status: {logs_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Activity logging test FAILED - Exception: {e}")
        return False

def test_admin_authentication_required():
    """Test that admin authentication is required for reset"""
    print("\n8. Testing admin authentication requirement...")
    
    try:
        # Try reset without authentication
        response = requests.post(f"{API_BASE}/admin/complete-reset")
        
        if response.status_code == 401 or response.status_code == 403:
            print("✅ Admin authentication correctly required for reset")
            return True
        else:
            print(f"❌ Reset should require admin authentication - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Admin authentication test FAILED - Exception: {e}")
        return False

def test_post_reset_setup_functionality():
    """Test that setup wizard works correctly after reset"""
    print("\n9. Testing post-reset setup functionality...")
    
    try:
        # Complete setup wizard again with new balances
        new_setup_data = {
            "hotel_name": "Reset Test Hotel",
            "hotel_address": "456 Reset Avenue, Reset City",
            "hotel_email": "reset@testhotel.com",
            "timezone": "UTC",
            "cash_balance": 3000.0,
            "bank_balance": 7000.0
        }
        
        setup_response = requests.post(f"{API_BASE}/setup/complete", json=new_setup_data)
        print(f"Post-reset setup Status Code: {setup_response.status_code}")
        
        if setup_response.status_code == 200:
            print("✅ Setup wizard completed successfully after reset")
            
            # Verify setup status is now completed
            status_response = requests.get(f"{API_BASE}/setup/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("is_completed") == True:
                    print("✅ Setup status correctly shows completed after re-setup")
                    
                    # Verify new balances are reflected in financial summary
                    headers = get_auth_headers()
                    financial_response = requests.get(f"{API_BASE}/daily-financial-summary", headers=headers)
                    if financial_response.status_code == 200:
                        financial_data = financial_response.json()
                        cash_balance = financial_data.get("cash_balance", 0)
                        bank_balance = financial_data.get("bank_balance", 0)
                        
                        print(f"Financial summary after re-setup:")
                        print(f"  Cash Balance: {cash_balance}")
                        print(f"  Bank Balance: {bank_balance}")
                        
                        if cash_balance == 3000.0 and bank_balance == 7000.0:
                            print("✅ New balances correctly reflected in financial summary")
                            return True
                        else:
                            print(f"❌ Balance mismatch - Expected Cash: 3000.0, Bank: 7000.0")
                            return False
                    else:
                        print("❌ Failed to get financial summary after re-setup")
                        return False
                else:
                    print(f"❌ Setup status should be completed after re-setup")
                    return False
            else:
                print("❌ Failed to get setup status after re-setup")
                return False
        else:
            print(f"❌ Post-reset setup FAILED - Status: {setup_response.status_code}")
            print(f"Response: {setup_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Post-reset setup test FAILED - Exception: {e}")
        return False

def main():
    """Run all enhanced complete database reset tests"""
    print("Starting Enhanced Complete Database Reset Tests")
    print("=" * 70)
    
    # Get admin authentication first
    if not get_admin_token():
        print("❌ Cannot proceed without admin authentication")
        return False
    
    test_results = []
    
    # Test 1: Setup initial data
    test_results.append(("Setup Initial Data", test_setup_initial_data()))
    
    # Test 2: Pre-reset data verification
    test_results.append(("Pre-Reset Data Verification", test_pre_reset_data_verification()))
    
    # Test 3: Complete database reset endpoint
    test_results.append(("Complete Database Reset", test_complete_database_reset()))
    
    # Test 4: Setup status after reset
    test_results.append(("Setup Status After Reset", test_setup_status_after_reset()))
    
    # Test 5: Collections cleared
    test_results.append(("Collections Cleared", test_collections_cleared()))
    
    # Test 6: Hotel settings preserved
    test_results.append(("Hotel Settings Preserved", test_hotel_settings_preserved()))
    
    # Test 7: Activity logging
    test_results.append(("Activity Logging", test_activity_logging()))
    
    # Test 8: Admin authentication required
    test_results.append(("Admin Auth Required", test_admin_authentication_required()))
    
    # Test 9: Post-reset setup functionality
    test_results.append(("Post-Reset Setup", test_post_reset_setup_functionality()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - ENHANCED COMPLETE DATABASE RESET")
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
        print("\n🎉 ALL TESTS PASSED! Enhanced complete database reset functionality is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)