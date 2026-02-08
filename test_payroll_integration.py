#!/usr/bin/env python3

import requests
import json
import sys

# Test the complete payroll settings integration
BASE_URL = "http://localhost:8001"

def test_payroll_settings_integration():
    """Test complete payroll settings integration"""
    session = requests.Session()
    
    try:
        print("🔐 Testing Authentication...")
        # 1. Login as admin
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        # Set authorization header
        token_data = login_response.json()
        session.headers.update({"Authorization": f"Bearer {token_data['access_token']}"})
        print("✅ Admin authentication successful")
        
        print("\n📊 Testing Payroll Settings CRUD Operations...")
        
        # 2. Test GET - Fetch default settings
        get_response = session.get(f"{BASE_URL}/api/payroll/settings")
        if get_response.status_code != 200:
            print(f"❌ GET payroll settings failed: {get_response.status_code}")
            return False
            
        default_settings = get_response.json()
        print("✅ GET payroll settings successful")
        print(f"   Default EPF Employee Rate: {default_settings.get('epf_employee_rate')}%")
        print(f"   Default EPF Employer Rate: {default_settings.get('epf_employer_rate')}%")
        print(f"   Default ETF Rate: {default_settings.get('etf_rate')}%")
        
        # 3. Test PUT - Update settings with Sri Lankan standard rates
        print("\n🇱🇰 Testing Sri Lankan Standard Payroll Rates...")
        sri_lankan_rates = {
            "enable_epf": True,
            "epf_employee_rate": 8.0,  # Standard Sri Lankan EPF employee contribution
            "epf_employer_rate": 12.0,  # Standard Sri Lankan EPF employer contribution
            "enable_etf": True,
            "etf_rate": 3.0,  # Standard Sri Lankan ETF rate
            "tax_enabled": True,
            "tax_rate": 5.0  # Sample tax rate
        }
        
        update_response = session.put(f"{BASE_URL}/api/payroll/settings", json=sri_lankan_rates)
        if update_response.status_code != 200:
            print(f"❌ PUT payroll settings failed: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
        updated_settings = update_response.json()
        print("✅ PUT payroll settings successful")
        print(f"   Updated EPF Employee Rate: {updated_settings.get('epf_employee_rate')}%")
        print(f"   Updated EPF Employer Rate: {updated_settings.get('epf_employer_rate')}%")
        print(f"   Updated ETF Rate: {updated_settings.get('etf_rate')}%")
        print(f"   Tax Enabled: {updated_settings.get('tax_enabled')}")
        print(f"   Tax Rate: {updated_settings.get('tax_rate')}%")
        
        # 4. Test validation - Verify all values were updated correctly
        print("\n✅ Testing Data Validation...")
        verification_response = session.get(f"{BASE_URL}/api/payroll/settings")
        if verification_response.status_code != 200:
            print(f"❌ Verification GET failed: {verification_response.status_code}")
            return False
            
        verified_settings = verification_response.json()
        
        # Validate each setting
        validations = [
            ("EPF Employee Rate", verified_settings.get("epf_employee_rate"), 8.0),
            ("EPF Employer Rate", verified_settings.get("epf_employer_rate"), 12.0),
            ("ETF Rate", verified_settings.get("etf_rate"), 3.0),
            ("Tax Enabled", verified_settings.get("tax_enabled"), True),
            ("Tax Rate", verified_settings.get("tax_rate"), 5.0),
        ]
        
        all_valid = True
        for name, actual, expected in validations:
            if actual == expected:
                print(f"   ✅ {name}: {actual} (correct)")
            else:
                print(f"   ❌ {name}: Expected {expected}, got {actual}")
                all_valid = False
        
        if not all_valid:
            return False
            
        # 5. Test edge cases - Disable features
        print("\n🔧 Testing Feature Toggle...")
        disabled_settings = {
            "enable_epf": False,
            "enable_etf": False,
            "tax_enabled": False
        }
        
        disable_response = session.put(f"{BASE_URL}/api/payroll/settings", json=disabled_settings)
        if disable_response.status_code != 200:
            print(f"❌ Feature disable failed: {disable_response.status_code}")
            return False
            
        disabled_result = disable_response.json()
        if (not disabled_result.get("enable_epf") and 
            not disabled_result.get("enable_etf") and 
            not disabled_result.get("tax_enabled")):
            print("✅ Feature toggle successful - All features disabled")
        else:
            print("❌ Feature toggle failed")
            return False
            
        # 6. Re-enable with different rates for final test
        print("\n🔄 Testing Final Configuration...")
        final_config = {
            "enable_epf": True,
            "epf_employee_rate": 10.0,
            "epf_employer_rate": 15.0,
            "enable_etf": True,
            "etf_rate": 4.0,
            "tax_enabled": True,
            "tax_rate": 7.5
        }
        
        final_response = session.put(f"{BASE_URL}/api/payroll/settings", json=final_config)
        if final_response.status_code != 200:
            print(f"❌ Final configuration failed: {final_response.status_code}")
            return False
            
        print("✅ Final configuration successful")
        
        # 7. Test that settings persist
        print("\n💾 Testing Settings Persistence...")
        persistence_response = session.get(f"{BASE_URL}/api/payroll/settings")
        if persistence_response.status_code != 200:
            print(f"❌ Persistence test failed: {persistence_response.status_code}")
            return False
            
        persisted_settings = persistence_response.json()
        if (persisted_settings.get("epf_employee_rate") == 10.0 and
            persisted_settings.get("tax_rate") == 7.5):
            print("✅ Settings persistence verified")
        else:
            print("❌ Settings not persisted correctly")
            return False
            
        print("\n🎉 All Payroll Settings Integration Tests Passed!")
        print("\n📋 Summary:")
        print("   ✅ Authentication working")
        print("   ✅ GET endpoint working")
        print("   ✅ PUT endpoint working")
        print("   ✅ Data validation working")
        print("   ✅ Feature toggles working")
        print("   ✅ Settings persistence working")
        print("   ✅ Sri Lankan payroll standards supported")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the backend is running on http://localhost:8001")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🏨 Hotel Management System - Payroll Settings Integration Test")
    print("=" * 70)
    
    success = test_payroll_settings_integration()
    
    if success:
        print("\n🎊 ALL TESTS PASSED! Payroll settings feature is ready for production.")
        sys.exit(0)
    else:
        print("\n💥 SOME TESTS FAILED! Please check the implementation.")
        sys.exit(1)