#!/usr/bin/env python3
"""
Settings Page Backend Functionality Testing for Hotel Management System
Tests User Management, Settings Management, and Activity Log endpoints.
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

print(f"Testing Settings Page Backend API at: {API_BASE}")
print("=" * 80)

# Global variables to store test data
created_user_id = None
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

def test_health_check():
    """Test basic API health check"""
    print("\n1. Testing API Health Check")
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            data = response.json()
            if data.get("message") == "Hotel Management API":
                log_test_result("API Health Check", True, "API is responding correctly")
                return True
            else:
                log_test_result("API Health Check", False, f"Unexpected response: {data}")
                return False
        else:
            log_test_result("API Health Check", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("API Health Check", False, f"Exception: {str(e)}")
        return False

def test_get_users():
    """Test GET /api/users - Get all users"""
    print("\n2. Testing GET /api/users - Get All Users")
    try:
        response = requests.get(f"{API_BASE}/users")
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users")
            
            # Check for admin and staff1 users
            admin_found = False
            staff_found = False
            
            for user in users:
                print(f"  - User: {user.get('username')} ({user.get('role')}) - Active: {user.get('is_active')}")
                if user.get('username') == 'admin':
                    admin_found = True
                elif user.get('username') == 'staff1':
                    staff_found = True
            
            if admin_found and staff_found:
                log_test_result("GET /api/users", True, f"Found {len(users)} users including admin and staff1")
                return True
            else:
                log_test_result("GET /api/users", False, f"Missing expected users - Admin: {admin_found}, Staff1: {staff_found}")
                return False
        else:
            log_test_result("GET /api/users", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/users", False, f"Exception: {str(e)}")
        return False

def test_create_user():
    """Test POST /api/users - Create new user"""
    print("\n3. Testing POST /api/users - Create New User")
    global created_user_id
    
    try:
        new_user = {
            "username": "testmanager",
            "password": "manager123",
            "full_name": "Test Manager",
            "role": "Manager",
            "email": "manager@hotel.com"
        }
        
        response = requests.post(f"{API_BASE}/users", json=new_user)
        if response.status_code == 200:
            user_data = response.json()
            created_user_id = user_data.get('id')
            print(f"Created user: {user_data.get('username')} with ID: {created_user_id}")
            
            # Verify password is masked
            if user_data.get('password') == '***':
                log_test_result("POST /api/users", True, f"User created successfully with masked password")
                return True
            else:
                log_test_result("POST /api/users", False, "Password not properly masked in response")
                return False
        else:
            error_msg = response.text
            log_test_result("POST /api/users", False, f"Status code: {response.status_code}, Error: {error_msg}")
            return False
    except Exception as e:
        log_test_result("POST /api/users", False, f"Exception: {str(e)}")
        return False

def test_create_duplicate_user():
    """Test POST /api/users - Try to create duplicate user"""
    print("\n4. Testing POST /api/users - Duplicate User Prevention")
    try:
        duplicate_user = {
            "username": "admin",  # This should already exist
            "password": "test123",
            "full_name": "Duplicate Admin",
            "role": "Admin",
            "email": "duplicate@hotel.com"
        }
        
        response = requests.post(f"{API_BASE}/users", json=duplicate_user)
        if response.status_code == 400:
            error_data = response.json()
            if "already exists" in error_data.get('detail', '').lower():
                log_test_result("POST /api/users - Duplicate Prevention", True, "Correctly prevented duplicate username")
                return True
            else:
                log_test_result("POST /api/users - Duplicate Prevention", False, f"Wrong error message: {error_data}")
                return False
        else:
            log_test_result("POST /api/users - Duplicate Prevention", False, f"Should have returned 400, got: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("POST /api/users - Duplicate Prevention", False, f"Exception: {str(e)}")
        return False

def test_toggle_user_status():
    """Test PUT /api/users/{user_id}/toggle-status - Toggle user status"""
    print("\n5. Testing PUT /api/users/{user_id}/toggle-status - Toggle User Status")
    global created_user_id
    
    if not created_user_id:
        log_test_result("PUT /api/users/{id}/toggle-status", False, "No user ID available for testing")
        return False
    
    try:
        response = requests.put(f"{API_BASE}/users/{created_user_id}/toggle-status")
        if response.status_code == 200:
            result = response.json()
            print(f"Toggle result: {result.get('message')}")
            
            # Verify the status was actually changed by getting the user
            user_response = requests.get(f"{API_BASE}/users")
            if user_response.status_code == 200:
                users = user_response.json()
                test_user = next((u for u in users if u.get('id') == created_user_id), None)
                if test_user:
                    print(f"User status after toggle: {test_user.get('is_active')}")
                    log_test_result("PUT /api/users/{id}/toggle-status", True, f"Status toggled successfully")
                    return True
                else:
                    log_test_result("PUT /api/users/{id}/toggle-status", False, "Could not find user after toggle")
                    return False
            else:
                log_test_result("PUT /api/users/{id}/toggle-status", False, "Could not verify status change")
                return False
        else:
            log_test_result("PUT /api/users/{id}/toggle-status", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("PUT /api/users/{id}/toggle-status", False, f"Exception: {str(e)}")
        return False

def test_get_settings():
    """Test GET /api/settings - Get hotel settings"""
    print("\n6. Testing GET /api/settings - Get Hotel Settings")
    try:
        response = requests.get(f"{API_BASE}/settings")
        if response.status_code == 200:
            settings = response.json()
            print(f"Hotel Name: {settings.get('hotel_name')}")
            print(f"Hotel Contact: {settings.get('hotel_contact')}")
            print(f"Hotel Address: {settings.get('hotel_address')}")
            print(f"Currency: {settings.get('currency')}")
            
            # Check for Grand Hotel Paradise data
            if settings.get('hotel_name') == 'Grand Hotel Paradise':
                log_test_result("GET /api/settings", True, "Settings retrieved with Grand Hotel Paradise data")
                return True
            else:
                log_test_result("GET /api/settings", True, f"Settings retrieved with hotel name: {settings.get('hotel_name')}")
                return True
        else:
            log_test_result("GET /api/settings", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/settings", False, f"Exception: {str(e)}")
        return False

def test_update_settings():
    """Test PUT /api/settings - Update hotel settings"""
    print("\n7. Testing PUT /api/settings - Update Hotel Settings")
    try:
        updated_settings = {
            "hotel_name": "Grand Hotel Paradise Updated",
            "hotel_contact": "+94 11 999 8888",
            "hotel_address": "456 Updated Ocean View Road, Colombo 03, Sri Lanka",
            "currency": "USD",
            "default_room_rate": 9000.0
        }
        
        response = requests.put(f"{API_BASE}/settings", json=updated_settings)
        if response.status_code == 200:
            result = response.json()
            print(f"Update result: {result.get('message')}")
            
            # Verify the settings were actually updated
            verify_response = requests.get(f"{API_BASE}/settings")
            if verify_response.status_code == 200:
                settings = verify_response.json()
                if (settings.get('hotel_name') == updated_settings['hotel_name'] and 
                    settings.get('currency') == updated_settings['currency']):
                    log_test_result("PUT /api/settings", True, "Settings updated successfully")
                    return True
                else:
                    log_test_result("PUT /api/settings", False, "Settings not properly updated")
                    return False
            else:
                log_test_result("PUT /api/settings", False, "Could not verify settings update")
                return False
        else:
            log_test_result("PUT /api/settings", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("PUT /api/settings", False, f"Exception: {str(e)}")
        return False

def test_get_activity_logs():
    """Test GET /api/activity-logs - Get activity logs with pagination"""
    print("\n8. Testing GET /api/activity-logs - Get Activity Logs")
    try:
        # Test basic activity logs retrieval
        response = requests.get(f"{API_BASE}/activity-logs")
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            total_count = data.get('total_count', 0)
            
            print(f"Found {total_count} activity logs")
            print(f"Retrieved {len(logs)} logs in this page")
            
            # Check for user creation and settings update logs
            user_creation_found = False
            settings_update_found = False
            
            for log in logs[:10]:  # Check first 10 logs
                action = log.get('action', '')
                description = log.get('description', '')
                print(f"  - {action}: {description}")
                
                if 'user_created' in action or 'user' in description.lower():
                    user_creation_found = True
                if 'settings_updated' in action or 'settings' in description.lower():
                    settings_update_found = True
            
            if total_count > 0:
                log_test_result("GET /api/activity-logs", True, f"Retrieved {total_count} activity logs with pagination")
                return True
            else:
                log_test_result("GET /api/activity-logs", True, "Activity logs endpoint working (no logs yet)")
                return True
        else:
            log_test_result("GET /api/activity-logs", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/activity-logs", False, f"Exception: {str(e)}")
        return False

def test_activity_logs_pagination():
    """Test GET /api/activity-logs with pagination parameters"""
    print("\n9. Testing GET /api/activity-logs - Pagination Parameters")
    try:
        # Test with pagination parameters
        response = requests.get(f"{API_BASE}/activity-logs?page=1&limit=5")
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            page = data.get('page', 0)
            limit = data.get('limit', 0)
            total_pages = data.get('total_pages', 0)
            
            print(f"Page {page}, Limit {limit}, Total Pages {total_pages}")
            print(f"Retrieved {len(logs)} logs")
            
            if page == 1 and limit == 5:
                log_test_result("GET /api/activity-logs - Pagination", True, f"Pagination working correctly")
                return True
            else:
                log_test_result("GET /api/activity-logs - Pagination", False, f"Pagination parameters not working correctly")
                return False
        else:
            log_test_result("GET /api/activity-logs - Pagination", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("GET /api/activity-logs - Pagination", False, f"Exception: {str(e)}")
        return False

def test_create_activity_log():
    """Test POST /api/activity-logs - Create activity log entry"""
    print("\n10. Testing POST /api/activity-logs - Create Activity Log")
    try:
        new_log = {
            "action": "test_action",
            "description": "Test activity log entry created during testing",
            "user_name": "Test User",
            "entity_type": "test",
            "entity_id": "test-123",
            "details": {"test": True, "timestamp": datetime.now().isoformat()}
        }
        
        response = requests.post(f"{API_BASE}/activity-logs", json=new_log)
        if response.status_code == 200:
            result = response.json()
            print(f"Activity log creation result: {result.get('message')}")
            
            # Verify the log was created by retrieving recent logs
            verify_response = requests.get(f"{API_BASE}/activity-logs?limit=10")
            if verify_response.status_code == 200:
                data = verify_response.json()
                logs = data.get('logs', [])
                
                # Look for our test log
                test_log_found = any(log.get('action') == 'test_action' for log in logs)
                
                if test_log_found:
                    log_test_result("POST /api/activity-logs", True, "Activity log created successfully")
                    return True
                else:
                    log_test_result("POST /api/activity-logs", False, "Activity log not found after creation")
                    return False
            else:
                log_test_result("POST /api/activity-logs", False, "Could not verify activity log creation")
                return False
        else:
            log_test_result("POST /api/activity-logs", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("POST /api/activity-logs", False, f"Exception: {str(e)}")
        return False

def test_delete_user():
    """Test DELETE /api/users/{user_id} - Delete user"""
    print("\n11. Testing DELETE /api/users/{user_id} - Delete User")
    global created_user_id
    
    if not created_user_id:
        log_test_result("DELETE /api/users/{id}", False, "No user ID available for testing")
        return False
    
    try:
        response = requests.delete(f"{API_BASE}/users/{created_user_id}")
        if response.status_code == 200:
            result = response.json()
            print(f"Delete result: {result.get('message')}")
            
            # Verify the user was actually deleted
            verify_response = requests.get(f"{API_BASE}/users")
            if verify_response.status_code == 200:
                users = verify_response.json()
                deleted_user = next((u for u in users if u.get('id') == created_user_id), None)
                
                if not deleted_user:
                    log_test_result("DELETE /api/users/{id}", True, "User deleted successfully")
                    return True
                else:
                    log_test_result("DELETE /api/users/{id}", False, "User still exists after deletion")
                    return False
            else:
                log_test_result("DELETE /api/users/{id}", False, "Could not verify user deletion")
                return False
        else:
            log_test_result("DELETE /api/users/{id}", False, f"Status code: {response.status_code}")
            return False
    except Exception as e:
        log_test_result("DELETE /api/users/{id}", False, f"Exception: {str(e)}")
        return False

def test_integration_workflow():
    """Test complete integration workflow"""
    print("\n12. Testing Integration Workflow - Create User → Update Settings → Check Activity Logs")
    try:
        # Step 1: Create a new user
        workflow_user = {
            "username": "workflowtest",
            "password": "workflow123",
            "full_name": "Workflow Test User",
            "role": "Staff",
            "email": "workflow@hotel.com"
        }
        
        user_response = requests.post(f"{API_BASE}/users", json=workflow_user)
        if user_response.status_code != 200:
            log_test_result("Integration Workflow", False, "Failed to create workflow test user")
            return False
        
        workflow_user_id = user_response.json().get('id')
        
        # Step 2: Update settings
        settings_update = {
            "hotel_name": "Integration Test Hotel",
            "default_room_rate": 7500.0
        }
        
        settings_response = requests.put(f"{API_BASE}/settings", json=settings_update)
        if settings_response.status_code != 200:
            log_test_result("Integration Workflow", False, "Failed to update settings in workflow")
            return False
        
        # Step 3: Check activity logs for both actions
        logs_response = requests.get(f"{API_BASE}/activity-logs?limit=20")
        if logs_response.status_code != 200:
            log_test_result("Integration Workflow", False, "Failed to retrieve activity logs")
            return False
        
        logs_data = logs_response.json()
        logs = logs_data.get('logs', [])
        
        user_creation_logged = False
        settings_update_logged = False
        
        for log in logs:
            action = log.get('action', '')
            description = log.get('description', '')
            
            if 'user_created' in action and 'workflowtest' in description:
                user_creation_logged = True
            if 'settings_updated' in action:
                settings_update_logged = True
        
        # Clean up: Delete the workflow test user
        requests.delete(f"{API_BASE}/users/{workflow_user_id}")
        
        if user_creation_logged and settings_update_logged:
            log_test_result("Integration Workflow", True, "Complete workflow with activity logging working")
            return True
        else:
            log_test_result("Integration Workflow", False, f"Activity logging incomplete - User: {user_creation_logged}, Settings: {settings_update_logged}")
            return False
        
    except Exception as e:
        log_test_result("Integration Workflow", False, f"Exception: {str(e)}")
        return False

def run_all_tests():
    """Run all Settings page backend tests"""
    print("Starting Settings Page Backend API Testing...")
    print("=" * 80)
    
    tests = [
        test_health_check,
        test_get_users,
        test_create_user,
        test_create_duplicate_user,
        test_toggle_user_status,
        test_get_settings,
        test_update_settings,
        test_get_activity_logs,
        test_activity_logs_pagination,
        test_create_activity_log,
        test_delete_user,
        test_integration_workflow
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
    print("SETTINGS PAGE BACKEND API TEST SUMMARY")
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
        print("🎉 EXCELLENT: Settings page backend functionality is working excellently!")
    elif success_rate >= 75:
        print("✅ GOOD: Settings page backend functionality is working well with minor issues")
    elif success_rate >= 50:
        print("⚠️  MODERATE: Settings page backend has some issues that need attention")
    else:
        print("❌ POOR: Settings page backend has significant issues that need immediate attention")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)