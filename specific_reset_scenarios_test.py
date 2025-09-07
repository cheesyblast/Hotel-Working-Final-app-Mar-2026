#!/usr/bin/env python3
"""
Specific Test Scenarios for Enhanced Complete Database Reset
Tests the exact scenarios mentioned in the review request.
"""

import requests
import json
from datetime import date, datetime
import sys

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
API_BASE = f"{BASE_URL}/api"

# Get admin token
def get_admin_token():
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def test_specific_scenarios():
    """Test the specific scenarios mentioned in the review request"""
    print("Testing Specific Enhanced Complete Database Reset Scenarios")
    print("=" * 70)
    
    token = get_admin_token()
    if not token:
        print("❌ Failed to get admin token")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Initialize some data first
    requests.post(f"{API_BASE}/init-data")
    
    print("\n1. Testing complete database reset endpoint (/admin/complete-reset)")
    print("   - Verify it clears setup_wizard data")
    
    reset_response = requests.post(f"{API_BASE}/admin/complete-reset", headers=headers)
    if reset_response.status_code != 200:
        print(f"❌ Reset failed with status: {reset_response.status_code}")
        return False
    
    reset_data = reset_response.json()
    print(f"✅ Reset endpoint working - Status: {reset_response.status_code}")
    
    print("\n2. Testing that response includes requires_setup: true flag")
    if reset_data.get("requires_setup") == True:
        print("✅ Response includes requires_setup: true")
    else:
        print(f"❌ requires_setup flag incorrect: {reset_data.get('requires_setup')}")
        return False
    
    print("\n3. Testing that setup status check returns is_completed: false after reset")
    status_response = requests.get(f"{API_BASE}/setup/status")
    if status_response.status_code == 200:
        status_data = status_response.json()
        if status_data.get("is_completed") == False:
            print("✅ Setup status returns is_completed: false after reset")
        else:
            print(f"❌ Setup status incorrect: {status_data.get('is_completed')}")
            return False
    else:
        print(f"❌ Setup status check failed: {status_response.status_code}")
        return False
    
    print("\n4. Verifying all expected collections are cleared (including setup_wizard)")
    reset_summary = reset_data.get("reset_summary", {})
    expected_collections = ["rooms", "bookings", "customers", "expenses", "incomes", "activity_logs", "daily_sales"]
    
    for collection in expected_collections:
        if collection in reset_summary:
            print(f"✅ Collection '{collection}' cleared: {reset_summary[collection]} records")
        else:
            print(f"❌ Collection '{collection}' not found in reset summary")
            return False
    
    if reset_summary.get("setup_wizard_reset") == True:
        print("✅ setup_wizard collection reset confirmed")
    else:
        print(f"❌ setup_wizard_reset flag incorrect: {reset_summary.get('setup_wizard_reset')}")
        return False
    
    print("\n5. Testing that hotel settings are preserved but setup_wizard is reset")
    settings_response = requests.get(f"{API_BASE}/settings", headers=headers)
    if settings_response.status_code == 200:
        settings = settings_response.json()
        if settings.get("hotel_name"):
            print(f"✅ Hotel settings preserved: {settings.get('hotel_name')}")
        else:
            print("❌ Hotel settings not preserved")
            return False
    else:
        print(f"❌ Settings check failed: {settings_response.status_code}")
        return False
    
    print("\n6. Verifying reset_summary includes setup_wizard_reset: true")
    if reset_summary.get("setup_wizard_reset") == True:
        print("✅ reset_summary includes setup_wizard_reset: true")
    else:
        print(f"❌ setup_wizard_reset missing or incorrect: {reset_summary.get('setup_wizard_reset')}")
        return False
    
    print("\n7. Testing activity logging includes appropriate reset information")
    logs_response = requests.get(f"{API_BASE}/activity-logs?action=complete_system_reset", headers=headers)
    if logs_response.status_code == 200:
        logs_data = logs_response.json()
        logs = logs_data.get("logs", [])
        
        if logs:
            reset_log = logs[0]
            if reset_log.get("action") == "complete_system_reset":
                print("✅ Reset activity logged with correct action")
                
                details = reset_log.get("details", {})
                if details.get("setup_wizard_reset") == True:
                    print("✅ Activity log includes setup_wizard reset information")
                else:
                    print("❌ Activity log missing setup_wizard reset information")
                    return False
            else:
                print(f"❌ Incorrect activity log action: {reset_log.get('action')}")
                return False
        else:
            print("❌ No reset activity log found")
            return False
    else:
        print(f"❌ Activity logs check failed: {logs_response.status_code}")
        return False
    
    print("\n8. Testing admin authentication requirement")
    # Test without auth
    no_auth_response = requests.post(f"{API_BASE}/admin/complete-reset")
    if no_auth_response.status_code in [401, 403]:
        print("✅ Admin authentication correctly required")
    else:
        print(f"❌ Authentication not properly enforced: {no_auth_response.status_code}")
        return False
    
    print("\n" + "=" * 70)
    print("🎉 ALL SPECIFIC SCENARIOS PASSED!")
    print("Enhanced complete database reset functionality meets all requirements.")
    return True

if __name__ == "__main__":
    success = test_specific_scenarios()
    sys.exit(0 if success else 1)