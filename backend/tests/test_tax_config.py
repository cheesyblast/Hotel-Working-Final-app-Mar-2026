"""
Test Tax/Levy Configuration Feature
Tests for creating, updating, toggling, and calculating taxes for bookings and restaurant
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTaxConfiguration:
    """Tax configuration endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json()["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_01_get_taxes_list(self):
        """Test GET /api/taxes returns list of taxes"""
        response = requests.get(f"{BASE_URL}/api/taxes")
        assert response.status_code == 200
        taxes = response.json()
        assert isinstance(taxes, list)
        print(f"Found {len(taxes)} tax configurations")
        
        # Verify Service Tax exists with apply_to_bookings=True
        service_tax = next((t for t in taxes if t["name"] == "Service Tax"), None)
        assert service_tax is not None, "Service Tax should exist"
        assert service_tax["rate"] == 10.0, "Service Tax rate should be 10%"
        assert service_tax["apply_to_bookings"] == True, "Service Tax should apply to bookings"
        print(f"Service Tax verified: rate={service_tax['rate']}%, apply_to_bookings={service_tax['apply_to_bookings']}")
    
    def test_02_calculate_booking_taxes(self):
        """Test /api/taxes/calculate-booking returns correct tax for 10% Service Tax"""
        response = requests.post(f"{BASE_URL}/api/taxes/calculate-booking?base_amount=10000")
        assert response.status_code == 200
        
        data = response.json()
        assert data["base_amount"] == 10000.0
        assert data["total_tax"] == 1000.0, f"Expected 1000 (10% of 10000), got {data['total_tax']}"
        assert data["total_with_tax"] == 11000.0
        
        # Verify breakdown
        assert len(data["breakdown"]) > 0, "Should have tax breakdown"
        service_tax_breakdown = next((b for b in data["breakdown"] if b["name"] == "Service Tax"), None)
        assert service_tax_breakdown is not None
        assert service_tax_breakdown["amount"] == 1000.0
        print(f"Booking tax calculation verified: {data['total_tax']} tax on {data['base_amount']} base")
    
    def test_03_calculate_restaurant_taxes(self):
        """Test /api/taxes/calculate-restaurant returns correct tax for 5% VAT"""
        response = requests.post(f"{BASE_URL}/api/taxes/calculate-restaurant?base_amount=1000")
        assert response.status_code == 200
        
        data = response.json()
        assert data["base_amount"] == 1000.0
        assert data["total_tax"] == 50.0, f"Expected 50 (5% of 1000), got {data['total_tax']}"
        assert data["total_with_tax"] == 1050.0
        
        # Verify breakdown
        if data["total_tax"] > 0:
            assert len(data["breakdown"]) > 0, "Should have tax breakdown"
            vat_breakdown = next((b for b in data["breakdown"] if b["name"] == "VAT"), None)
            assert vat_breakdown is not None
            assert vat_breakdown["amount"] == 50.0
        print(f"Restaurant tax calculation verified: {data['total_tax']} tax on {data['base_amount']} base")
    
    def test_04_toggle_apply_to_bookings(self):
        """Test toggling apply_to_bookings flag updates tax calculation"""
        # Get Service Tax ID
        response = requests.get(f"{BASE_URL}/api/taxes")
        taxes = response.json()
        service_tax = next((t for t in taxes if t["name"] == "Service Tax"), None)
        assert service_tax is not None
        tax_id = service_tax["id"]
        
        # Toggle apply_to_bookings to false
        response = requests.put(
            f"{BASE_URL}/api/taxes/{tax_id}",
            headers=self.headers,
            json={"apply_to_bookings": False}
        )
        assert response.status_code == 200
        
        # Verify booking tax is now 0
        response = requests.post(f"{BASE_URL}/api/taxes/calculate-booking?base_amount=10000")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tax"] == 0.0, f"Expected 0 tax after toggle, got {data['total_tax']}"
        print("Toggle to false verified: booking tax is now 0")
        
        # Toggle back to true
        response = requests.put(
            f"{BASE_URL}/api/taxes/{tax_id}",
            headers=self.headers,
            json={"apply_to_bookings": True}
        )
        assert response.status_code == 200
        
        # Verify booking tax is back to 1000
        response = requests.post(f"{BASE_URL}/api/taxes/calculate-booking?base_amount=10000")
        assert response.status_code == 200
        data = response.json()
        assert data["total_tax"] == 1000.0, f"Expected 1000 tax after toggle back, got {data['total_tax']}"
        print("Toggle back to true verified: booking tax is 1000 again")
    
    def test_05_create_new_tax(self):
        """Test creating a new tax configuration"""
        # Create a test tax
        response = requests.post(
            f"{BASE_URL}/api/taxes?name=TEST_Tourism_Levy&rate=2&type=percentage&apply_to_bookings=true&apply_to_restaurant=false&description=Test%20tourism%20levy"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tax configuration created"
        assert data["tax"]["name"] == "TEST_Tourism_Levy"
        assert data["tax"]["rate"] == 2.0
        print(f"Created test tax: {data['tax']['name']} at {data['tax']['rate']}%")
        
        # Verify it appears in the list
        response = requests.get(f"{BASE_URL}/api/taxes")
        taxes = response.json()
        test_tax = next((t for t in taxes if t["name"] == "TEST_Tourism_Levy"), None)
        assert test_tax is not None
        
        # Clean up - delete the test tax
        response = requests.delete(f"{BASE_URL}/api/taxes/{test_tax['id']}")
        assert response.status_code == 200
        print("Test tax deleted successfully")
    
    def test_06_verify_vat_for_restaurant(self):
        """Verify VAT tax exists and applies to restaurant"""
        response = requests.get(f"{BASE_URL}/api/taxes")
        taxes = response.json()
        
        vat_tax = next((t for t in taxes if t["name"] == "VAT"), None)
        assert vat_tax is not None, "VAT tax should exist"
        assert vat_tax["rate"] == 5.0, f"VAT rate should be 5%, got {vat_tax['rate']}"
        assert vat_tax["apply_to_restaurant"] == True, "VAT should apply to restaurant"
        assert vat_tax["apply_to_bookings"] == False, "VAT should not apply to bookings"
        print(f"VAT verified: rate={vat_tax['rate']}%, apply_to_restaurant={vat_tax['apply_to_restaurant']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
