#!/usr/bin/env python3

import requests
import json
import sys

# Test the payroll settings functionality
BASE_URL = "http://localhost:8001"

def test_payroll_settings():
    """Test payroll settings endpoints"""
    session = requests.Session()
    
    try:
        # 1. Login as admin
        print("1. Testing admin login...")
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
        print("✅ Admin login successful")
        
        # 2. Get current payroll settings
        print("\n2. Testing get payroll settings...")
        get_response = session.get(f"{BASE_URL}/api/payroll/settings")
        
        if get_response.status_code != 200:
            print(f"❌ Get payroll settings failed: {get_response.status_code}")
            print(f"Response: {get_response.text}")
            return False
            
        settings = get_response.json()
        print("✅ Get payroll settings successful")
        print(f"Current settings: {json.dumps(settings, indent=2)}")
        
        # 3. Update payroll settings
        print("\n3. Testing update payroll settings...")
        update_data = {
            "enable_epf": True,
            "epf_employee_rate": 10.0,
            "epf_employer_rate": 15.0,
            "enable_etf": True,
            "etf_rate": 5.0,
            "tax_enabled": True,
            "tax_rate": 2.5
        }
        
        update_response = session.put(f"{BASE_URL}/api/payroll/settings", json=update_data)
        
        if update_response.status_code != 200:
            print(f"❌ Update payroll settings failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
        updated_settings = update_response.json()
        print("✅ Update payroll settings successful")
        print(f"Updated settings: {json.dumps(updated_settings, indent=2)}")
        
        # 4. Verify the update
        print("\n4. Verifying updated settings...")
        verify_response = session.get(f"{BASE_URL}/api/payroll/settings")
        
        if verify_response.status_code != 200:
            print(f"❌ Verify payroll settings failed: {verify_response.status_code}")
            return False
            
        verified_settings = verify_response.json()
        
        # Check if the values were updated correctly
        if (verified_settings.get("epf_employee_rate") == 10.0 and
            verified_settings.get("epf_employer_rate") == 15.0 and
            verified_settings.get("etf_rate") == 5.0 and
            verified_settings.get("tax_rate") == 2.5):
            print("✅ Settings updated correctly")
        else:
            print("❌ Settings not updated correctly")
            print(f"Expected EPF employee rate: 10.0, got: {verified_settings.get('epf_employee_rate')}")
            return False
        
        print("\n🎉 All payroll settings tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Payroll Settings Functionality")
    print("=" * 50)
    
    success = test_payroll_settings()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)