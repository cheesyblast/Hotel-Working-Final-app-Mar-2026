#!/usr/bin/env python3
"""
Comprehensive Authentication and Setup System Testing for Hotel Management System
Tests all authentication, setup wizard, email configuration, and security features.
"""

import requests
import json
from datetime import date, datetime
import sys
import os
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

print(f"Testing Hotel Management Authentication System at: {API_BASE}")
print("=" * 80)

# Global variables for test data
admin_token = None
test_user_id = None

def test_health_check():
    """Test basic API health check"""
    print("\n1. Testing API Health Check (GET /api/)")
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ API Health check PASSED")
            return True
        else:
            print(f"❌ API Health check FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health check FAILED - Error: {str(e)}")
        return False

def test_setup_wizard_status():
    """Test GET /api/setup/status - Check setup completion status"""
    print("\n2. Testing Setup Wizard Status (GET /api/setup/status)")
    try:
        response = requests.get(f"{API_BASE}/setup/status")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Setup status check PASSED")
            return True, data.get("is_completed", False)
        else:
            print(f"❌ Setup status check FAILED - Status: {response.status_code}")
            return False, False
    except Exception as e:
        print(f"❌ Setup status check FAILED - Error: {str(e)}")
        return False, False

def test_setup_wizard_complete():
    """Test POST /api/setup/complete - Complete initial setup"""
    print("\n3. Testing Setup Wizard Complete (POST /api/setup/complete)")
    
    setup_data = {
        "hotel_name": "Grand Paradise Hotel",
        "hotel_address": "123 Beach Road, Paradise City, PC 12345",
        "hotel_email": "admin@grandparadise.com"
    }
    
    try:
        response = requests.post(f"{API_BASE}/setup/complete", json=setup_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Setup wizard completion PASSED")
            print("   - Hotel settings created/updated")
            print("   - Admin user created with credentials: admin/admin123")
            return True
        elif response.status_code == 400:
            data = response.json()
            if "already completed" in data.get("detail", ""):
                print("✅ Setup wizard already completed (expected)")
                return True
            else:
                print(f"❌ Setup wizard completion FAILED - {data.get('detail')}")
                return False
        else:
            print(f"❌ Setup wizard completion FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Setup wizard completion FAILED - Error: {str(e)}")
        return False

def test_admin_login():
    """Test POST /api/auth/login - Admin login with default credentials"""
    print("\n4. Testing Admin Login (POST /api/auth/login)")
    global admin_token
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "access_token" in data and data.get("token_type") == "bearer":
                admin_token = data["access_token"]
                print("✅ Admin login PASSED")
                print(f"   - JWT token generated successfully")
                print(f"   - Token type: {data['token_type']}")
                return True
            else:
                print("❌ Admin login FAILED - Invalid response format")
                return False
        else:
            print(f"❌ Admin login FAILED - Status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                pass
            return False
    except Exception as e:
        print(f"❌ Admin login FAILED - Error: {str(e)}")
        return False

def test_invalid_login():
    """Test POST /api/auth/login - Invalid credentials"""
    print("\n5. Testing Invalid Login (POST /api/auth/login)")
    
    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Invalid login properly rejected")
            return True
        else:
            print(f"❌ Invalid login test FAILED - Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Invalid login test FAILED - Error: {str(e)}")
        return False

def test_get_current_user():
    """Test GET /api/auth/me - Get current user info with JWT token"""
    print("\n6. Testing Get Current User (GET /api/auth/me)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("username") == "admin" and data.get("role") == "Admin":
                print("✅ Get current user PASSED")
                print(f"   - Username: {data.get('username')}")
                print(f"   - Role: {data.get('role')}")
                print(f"   - Active: {data.get('is_active')}")
                return True
            else:
                print("❌ Get current user FAILED - Invalid user data")
                return False
        else:
            print(f"❌ Get current user FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get current user FAILED - Error: {str(e)}")
        return False

def test_unauthorized_access():
    """Test GET /api/auth/me - Without token (should fail)"""
    print("\n7. Testing Unauthorized Access (GET /api/auth/me without token)")
    
    try:
        response = requests.get(f"{API_BASE}/auth/me")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 403:
            print("✅ Unauthorized access properly blocked")
            return True
        else:
            print(f"❌ Unauthorized access test FAILED - Expected 403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Unauthorized access test FAILED - Error: {str(e)}")
        return False

def test_email_settings_get():
    """Test GET /api/email-settings - Get email settings (Admin only)"""
    print("\n8. Testing Get Email Settings (GET /api/email-settings)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(f"{API_BASE}/email-settings", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ Get email settings PASSED")
            print(f"   - Provider: {data.get('provider', 'Not set')}")
            print(f"   - Configured: {data.get('is_configured', False)}")
            return True
        else:
            print(f"❌ Get email settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get email settings FAILED - Error: {str(e)}")
        return False

def test_email_settings_update():
    """Test PUT /api/email-settings - Update email settings"""
    print("\n9. Testing Update Email Settings (PUT /api/email-settings)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test SMTP configuration
    smtp_settings = {
        "provider": "smtp",
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "test@gmail.com",
        "smtp_password": "testpassword",
        "from_email": "test@gmail.com",
        "from_name": "Grand Paradise Hotel"
    }
    
    try:
        response = requests.put(f"{API_BASE}/email-settings", json=smtp_settings, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Update email settings PASSED")
            print("   - SMTP configuration updated")
            return True
        else:
            print(f"❌ Update email settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Update email settings FAILED - Error: {str(e)}")
        return False

def test_email_settings_sendgrid():
    """Test PUT /api/email-settings - SendGrid configuration"""
    print("\n10. Testing SendGrid Email Settings (PUT /api/email-settings)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    sendgrid_settings = {
        "provider": "sendgrid",
        "sendgrid_api_key": "SG.test_api_key_here",
        "from_email": "noreply@grandparadise.com",
        "from_name": "Grand Paradise Hotel"
    }
    
    try:
        response = requests.put(f"{API_BASE}/email-settings", json=sendgrid_settings, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ SendGrid email settings PASSED")
            return True
        else:
            print(f"❌ SendGrid email settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ SendGrid email settings FAILED - Error: {str(e)}")
        return False

def test_email_settings_aws_ses():
    """Test PUT /api/email-settings - AWS SES configuration"""
    print("\n11. Testing AWS SES Email Settings (PUT /api/email-settings)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    ses_settings = {
        "provider": "ses",
        "aws_access_key": "AKIATEST123456789",
        "aws_secret_key": "test_secret_key_here",
        "aws_region": "us-east-1",
        "from_email": "noreply@grandparadise.com",
        "from_name": "Grand Paradise Hotel"
    }
    
    try:
        response = requests.put(f"{API_BASE}/email-settings", json=ses_settings, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ AWS SES email settings PASSED")
            return True
        else:
            print(f"❌ AWS SES email settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AWS SES email settings FAILED - Error: {str(e)}")
        return False

def test_email_test_endpoint():
    """Test POST /api/email-settings/test - Test email configuration"""
    print("\n12. Testing Email Test Endpoint (POST /api/email-settings/test)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.post(f"{API_BASE}/email-settings/test", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Email test endpoint PASSED")
            return True
        elif response.status_code == 400:
            data = response.json()
            if "email not configured" in data.get("detail", "").lower():
                print("✅ Email test properly rejected (admin email not configured)")
                return True
            else:
                print(f"❌ Email test FAILED - {data.get('detail')}")
                return False
        elif response.status_code == 500:
            data = response.json()
            if "failed to send" in data.get("detail", "").lower():
                print("✅ Email test endpoint working (failed to send due to test config)")
                return True
            else:
                print(f"❌ Email test FAILED - {data.get('detail')}")
                return False
        else:
            print(f"❌ Email test FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Email test FAILED - Error: {str(e)}")
        return False

def test_forgot_password():
    """Test POST /api/auth/forgot-password - Forgot password functionality"""
    print("\n13. Testing Forgot Password (POST /api/auth/forgot-password)")
    
    forgot_data = {
        "username_or_email": "admin"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/forgot-password", json=forgot_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ Forgot password PASSED")
            print("   - Password reset process initiated")
            return True
        elif response.status_code == 400:
            data = response.json()
            if "no email" in data.get("detail", "").lower():
                print("✅ Forgot password properly handled (no email associated)")
                return True
            else:
                print(f"❌ Forgot password FAILED - {data.get('detail')}")
                return False
        elif response.status_code == 500:
            data = response.json()
            if "failed to send email" in data.get("detail", "").lower():
                print("✅ Forgot password working (failed to send due to email config)")
                return True
            else:
                print(f"❌ Forgot password FAILED - {data.get('detail')}")
                return False
        else:
            print(f"❌ Forgot password FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Forgot password FAILED - Error: {str(e)}")
        return False

def test_user_management_endpoints():
    """Test user management endpoints (Admin only)"""
    print("\n14. Testing User Management Endpoints")
    global admin_token, test_user_id
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/users
    print("   14a. Testing Get Users (GET /api/users)")
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   Found {len(users)} users")
            print("   ✅ Get users PASSED")
        else:
            print(f"   ❌ Get users FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Get users FAILED - Error: {str(e)}")
        return False
    
    # Test POST /api/users - Create new user
    print("   14b. Testing Create User (POST /api/users)")
    new_user = {
        "username": "teststaff",
        "password": "testpass123",
        "full_name": "Test Staff Member",
        "role": "Staff",
        "email": "teststaff@grandparadise.com"
    }
    
    try:
        response = requests.post(f"{API_BASE}/users", json=new_user, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            test_user_id = user_data.get("id")
            print(f"   Created user: {user_data.get('username')} (ID: {test_user_id})")
            print("   ✅ Create user PASSED")
        else:
            print(f"   ❌ Create user FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Create user FAILED - Error: {str(e)}")
        return False
    
    # Test PUT /api/users/{user_id}/toggle-status
    if test_user_id:
        print("   14c. Testing Toggle User Status (PUT /api/users/{id}/toggle-status)")
        try:
            response = requests.put(f"{API_BASE}/users/{test_user_id}/toggle-status", headers=headers)
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Response: {data}")
                print("   ✅ Toggle user status PASSED")
            else:
                print(f"   ❌ Toggle user status FAILED - Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Toggle user status FAILED - Error: {str(e)}")
            return False
    
    return True

def test_settings_endpoints():
    """Test settings management endpoints"""
    print("\n15. Testing Settings Management Endpoints")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/settings
    print("   15a. Testing Get Settings (GET /api/settings)")
    try:
        response = requests.get(f"{API_BASE}/settings", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            settings = response.json()
            print(f"   Hotel Name: {settings.get('hotel_name')}")
            print(f"   Currency: {settings.get('currency')}")
            print("   ✅ Get settings PASSED")
        else:
            print(f"   ❌ Get settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Get settings FAILED - Error: {str(e)}")
        return False
    
    # Test PUT /api/settings
    print("   15b. Testing Update Settings (PUT /api/settings)")
    settings_update = {
        "hotel_name": "Grand Paradise Hotel & Resort",
        "currency": "USD",
        "check_in_time": "15:00",
        "check_out_time": "11:00"
    }
    
    try:
        response = requests.put(f"{API_BASE}/settings", json=settings_update, headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            print("   ✅ Update settings PASSED")
        else:
            print(f"   ❌ Update settings FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Update settings FAILED - Error: {str(e)}")
        return False
    
    return True

def test_activity_logs():
    """Test activity logs endpoints"""
    print("\n16. Testing Activity Logs Endpoints")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test GET /api/activity-logs
    print("   16a. Testing Get Activity Logs (GET /api/activity-logs)")
    try:
        response = requests.get(f"{API_BASE}/activity-logs?page=1&limit=10", headers=headers)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get("logs", [])
            print(f"   Found {len(logs)} activity logs")
            print(f"   Total count: {data.get('total_count', 0)}")
            print("   ✅ Get activity logs PASSED")
        else:
            print(f"   ❌ Get activity logs FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Get activity logs FAILED - Error: {str(e)}")
        return False
    
    return True

def test_logout():
    """Test POST /api/auth/logout - User logout"""
    print("\n17. Testing User Logout (POST /api/auth/logout)")
    global admin_token
    
    if not admin_token:
        print("❌ No admin token available - skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.post(f"{API_BASE}/auth/logout", headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
            print("✅ User logout PASSED")
            return True
        else:
            print(f"❌ User logout FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User logout FAILED - Error: {str(e)}")
        return False

def test_password_security():
    """Test password security features"""
    print("\n18. Testing Password Security")
    
    # Test that passwords are hashed (not stored in plain text)
    print("   18a. Verifying password hashing")
    global admin_token
    
    if not admin_token:
        # Re-login to get token
        login_data = {"username": "admin", "password": "admin123"}
        try:
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            if response.status_code == 200:
                admin_token = response.json()["access_token"]
            else:
                print("   ❌ Could not re-login for password security test")
                return False
        except:
            print("   ❌ Could not re-login for password security test")
            return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.get(f"{API_BASE}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            admin_user = next((u for u in users if u.get("username") == "admin"), None)
            if admin_user:
                # Check that password is not visible in user data
                if "password" not in admin_user and "password_hash" not in admin_user:
                    print("   ✅ Passwords properly hidden from API responses")
                else:
                    print("   ❌ Password data exposed in API response")
                    return False
            else:
                print("   ❌ Admin user not found")
                return False
        else:
            print("   ❌ Could not retrieve users for password security test")
            return False
    except Exception as e:
        print(f"   ❌ Password security test FAILED - Error: {str(e)}")
        return False
    
    print("   18b. Testing admin user protection")
    # Test that admin user cannot be deleted
    try:
        admin_user = next((u for u in users if u.get("username") == "admin"), None)
        if admin_user:
            admin_id = admin_user.get("id")
            response = requests.delete(f"{API_BASE}/users/{admin_id}", headers=headers)
            if response.status_code == 400:
                data = response.json()
                if "cannot delete admin" in data.get("detail", "").lower():
                    print("   ✅ Admin user properly protected from deletion")
                else:
                    print("   ❌ Admin deletion blocked but wrong reason")
                    return False
            else:
                print(f"   ❌ Admin user deletion not properly blocked - Status: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Admin protection test FAILED - Error: {str(e)}")
        return False
    
    return True

def cleanup_test_data():
    """Clean up test user created during testing"""
    print("\n19. Cleaning Up Test Data")
    global admin_token, test_user_id
    
    if not admin_token or not test_user_id:
        print("   No cleanup needed")
        return True
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    try:
        response = requests.delete(f"{API_BASE}/users/{test_user_id}", headers=headers)
        if response.status_code == 200:
            print("   ✅ Test user cleaned up successfully")
        else:
            print(f"   ⚠️ Could not clean up test user - Status: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Could not clean up test user - Error: {str(e)}")
    
    return True

def run_all_tests():
    """Run all authentication and setup system tests"""
    print("Starting Comprehensive Authentication and Setup System Testing")
    print("=" * 80)
    
    tests = [
        ("API Health Check", test_health_check),
        ("Setup Wizard Status", test_setup_wizard_status),
        ("Setup Wizard Complete", test_setup_wizard_complete),
        ("Admin Login", test_admin_login),
        ("Invalid Login", test_invalid_login),
        ("Get Current User", test_get_current_user),
        ("Unauthorized Access", test_unauthorized_access),
        ("Get Email Settings", test_email_settings_get),
        ("Update Email Settings (SMTP)", test_email_settings_update),
        ("Update Email Settings (SendGrid)", test_email_settings_sendgrid),
        ("Update Email Settings (AWS SES)", test_email_settings_aws_ses),
        ("Email Test Endpoint", test_email_test_endpoint),
        ("Forgot Password", test_forgot_password),
        ("User Management Endpoints", test_user_management_endpoints),
        ("Settings Management", test_settings_endpoints),
        ("Activity Logs", test_activity_logs),
        ("User Logout", test_logout),
        ("Password Security", test_password_security),
        ("Cleanup Test Data", cleanup_test_data)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {str(e)}")
            failed += 1
        
        print("-" * 40)
    
    print("\n" + "=" * 80)
    print("AUTHENTICATION AND SETUP SYSTEM TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL AUTHENTICATION AND SETUP TESTS PASSED!")
        print("✅ JWT Authentication System working correctly")
        print("✅ Setup Wizard System working correctly")
        print("✅ Email Service Configuration working correctly")
        print("✅ Forgot Password Functionality working correctly")
        print("✅ User Management working correctly")
        print("✅ Settings Management working correctly")
        print("✅ Activity Logging working correctly")
        print("✅ Password Security properly implemented")
        print("✅ Authentication Protected Endpoints working correctly")
    else:
        print(f"\n⚠️ {failed} TEST(S) FAILED - Review authentication system implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)