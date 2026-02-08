"""
Test P1 Features for Hotel Management System
- Login with admin/admin123
- Taxes endpoint
- Payroll settings endpoint
- Restaurant expenses endpoint
- SMS settings (notify.lk provider)
- Email settings (brevo provider)
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://innkeeper-32.preview.emergentagent.com').rstrip('/')


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_with_admin_credentials(self):
        """Test login with admin/admin123 credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer", "Token type should be bearer"
        print(f"SUCCESS: Login with admin/admin123 - Token received")
        return data["access_token"]
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "invalid",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Invalid credentials rejected with 401")


class TestTaxesEndpoint:
    """Test /api/taxes endpoint"""
    
    def test_taxes_returns_array(self):
        """Test that /api/taxes returns an array"""
        response = requests.get(f"{BASE_URL}/api/taxes")
        
        assert response.status_code == 200, f"Taxes endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"SUCCESS: /api/taxes returns array with {len(data)} items")


class TestPayrollSettings:
    """Test /api/payroll/settings endpoint (requires authentication)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_payroll_settings_returns_data(self, auth_token):
        """Test that /api/payroll/settings returns payroll settings"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/payroll/settings", headers=headers)
        
        assert response.status_code == 200, f"Payroll settings failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "enable_epf" in data, "Missing enable_epf field"
        assert "epf_employee_rate" in data, "Missing epf_employee_rate field"
        assert "epf_employer_rate" in data, "Missing epf_employer_rate field"
        assert "enable_etf" in data, "Missing enable_etf field"
        assert "etf_rate" in data, "Missing etf_rate field"
        
        print(f"SUCCESS: /api/payroll/settings returns valid data")
        print(f"  - EPF Employee Rate: {data.get('epf_employee_rate')}%")
        print(f"  - EPF Employer Rate: {data.get('epf_employer_rate')}%")
        print(f"  - ETF Rate: {data.get('etf_rate')}%")


class TestRestaurantExpenses:
    """Test /api/restaurant/expenses endpoint"""
    
    def test_restaurant_expenses_returns_array(self):
        """Test that /api/restaurant/expenses returns an array"""
        response = requests.get(f"{BASE_URL}/api/restaurant/expenses")
        
        assert response.status_code == 200, f"Restaurant expenses failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"SUCCESS: /api/restaurant/expenses returns array with {len(data)} items")


class TestSMSSettings:
    """Test /api/sms-settings endpoint"""
    
    def test_sms_settings_returns_data(self):
        """Test that /api/sms-settings returns SMS settings with notify.lk fields"""
        response = requests.get(f"{BASE_URL}/api/sms-settings")
        
        assert response.status_code == 200, f"SMS settings failed: {response.text}"
        data = response.json()
        
        # Verify notify.lk fields exist
        assert "provider" in data, "Missing provider field"
        assert "notify_lk_user_id" in data, "Missing notify_lk_user_id field"
        assert "notify_lk_api_key" in data, "Missing notify_lk_api_key field"
        assert "notify_lk_sender_id" in data, "Missing notify_lk_sender_id field"
        
        print(f"SUCCESS: /api/sms-settings returns valid data with notify.lk fields")
        print(f"  - Current provider: {data.get('provider')}")


class TestEmailSettings:
    """Test /api/email-settings endpoint (requires authentication)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed")
    
    def test_email_settings_returns_data(self, auth_token):
        """Test that /api/email-settings returns email settings with brevo fields"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/email-settings", headers=headers)
        
        assert response.status_code == 200, f"Email settings failed: {response.text}"
        data = response.json()
        
        # Verify brevo fields exist
        assert "provider" in data, "Missing provider field"
        assert "brevo_api_key" in data, "Missing brevo_api_key field"
        
        print(f"SUCCESS: /api/email-settings returns valid data with brevo fields")
        print(f"  - Current provider: {data.get('provider')}")


class TestRoomsEndpoint:
    """Test /api/rooms endpoint"""
    
    def test_rooms_returns_array(self):
        """Test that /api/rooms returns an array"""
        response = requests.get(f"{BASE_URL}/api/rooms")
        
        assert response.status_code == 200, f"Rooms endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"SUCCESS: /api/rooms returns array with {len(data)} rooms")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
