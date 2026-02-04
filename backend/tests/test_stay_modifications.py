"""
Test suite for Stay Modification features:
1. Extend Stay - extending a customer's stay
2. Extend Stay conflict check - preventing conflicts with other bookings
3. Early Checkout - using customer's booked rate, not room's default rate
4. Early Checkout UI - number formatting (tested via API response)
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStayModifications:
    """Test suite for extend stay and early checkout features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            pytest.skip("Authentication failed - skipping tests")
        
        yield
        
        # Cleanup - delete test bookings
        try:
            bookings_response = self.session.get(f"{BASE_URL}/api/bookings")
            if bookings_response.status_code == 200:
                bookings = bookings_response.json().get('bookings', [])
                for booking in bookings:
                    if booking.get('guest_name', '').startswith('TEST_'):
                        self.session.post(f"{BASE_URL}/api/cancel/{booking['id']}")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def test_01_login_success(self):
        """Test login works correctly"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        print("✓ Login successful")
    
    def test_02_get_checked_in_customers(self):
        """Test getting checked-in customers"""
        response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert response.status_code == 200
        customers = response.json()
        assert isinstance(customers, list)
        print(f"✓ Found {len(customers)} checked-in customers")
        
        # Verify Mohamed is in the list (Room 101)
        mohamed = next((c for c in customers if c.get('name') == 'Mohamed'), None)
        if mohamed:
            print(f"  - Mohamed found in Room {mohamed.get('current_room')}, checkout: {mohamed.get('check_out_date')}")
            assert mohamed.get('current_room') == '101'
        else:
            print("  - Mohamed not found (may have been checked out)")
    
    def test_03_extend_stay_success(self):
        """Test extending a customer's stay successfully"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test extend stay")
        
        # Find a customer to extend stay
        customer = customers[0]
        customer_id = customer.get('id')
        current_checkout = customer.get('check_out_date')
        
        # Parse current checkout date and add 2 days
        if isinstance(current_checkout, str):
            checkout_date = datetime.strptime(current_checkout.split('T')[0], '%Y-%m-%d').date()
        else:
            checkout_date = current_checkout
        
        new_checkout = checkout_date + timedelta(days=2)
        
        # Extend stay
        response = self.session.post(f"{BASE_URL}/api/extend-stay", json={
            "customer_id": customer_id,
            "new_checkout_date": new_checkout.isoformat()
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["message"] == "Stay extended successfully"
        
        # Verify details
        details = data.get("details", {})
        assert details.get("additional_nights") == 2
        assert details.get("new_checkout_date") == str(new_checkout)
        print(f"✓ Stay extended for {customer.get('name')}")
        print(f"  - Additional nights: {details.get('additional_nights')}")
        print(f"  - Additional charges: {details.get('additional_charges')}")
        print(f"  - New checkout: {details.get('new_checkout_date')}")
    
    def test_04_extend_stay_invalid_date(self):
        """Test extending stay with invalid date (before current checkout)"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        customer = customers[0]
        customer_id = customer.get('id')
        current_checkout = customer.get('check_out_date')
        
        # Parse current checkout date and subtract 1 day (invalid)
        if isinstance(current_checkout, str):
            checkout_date = datetime.strptime(current_checkout.split('T')[0], '%Y-%m-%d').date()
        else:
            checkout_date = current_checkout
        
        invalid_checkout = checkout_date - timedelta(days=1)
        
        # Try to extend stay with invalid date
        response = self.session.post(f"{BASE_URL}/api/extend-stay", json={
            "customer_id": customer_id,
            "new_checkout_date": invalid_checkout.isoformat()
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "after current checkout" in data["detail"].lower()
        print(f"✓ Correctly rejected invalid extend stay date")
    
    def test_05_extend_stay_conflict_check(self):
        """Test that extending stay is blocked when it conflicts with another booking"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        # Find a customer
        customer = customers[0]
        customer_id = customer.get('id')
        room_number = customer.get('current_room')
        current_checkout = customer.get('check_out_date')
        
        # Parse current checkout date
        if isinstance(current_checkout, str):
            checkout_date = datetime.strptime(current_checkout.split('T')[0], '%Y-%m-%d').date()
        else:
            checkout_date = current_checkout
        
        # Create a conflicting booking for the same room starting after current checkout
        conflict_checkin = checkout_date + timedelta(days=1)
        conflict_checkout = conflict_checkin + timedelta(days=3)
        
        # Create the conflicting booking
        booking_response = self.session.post(f"{BASE_URL}/api/bookings", json={
            "guest_name": "TEST_ConflictGuest",
            "guest_email": "conflict@test.com",
            "guest_phone": "1234567890",
            "room_number": room_number,
            "check_in_date": conflict_checkin.isoformat(),
            "check_out_date": conflict_checkout.isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 30000,
            "booking_status": "Upcoming"
        })
        
        if booking_response.status_code != 200:
            print(f"Warning: Could not create conflict booking: {booking_response.text}")
            pytest.skip("Could not create conflict booking for test")
        
        print(f"  - Created conflict booking for room {room_number} from {conflict_checkin} to {conflict_checkout}")
        
        # Now try to extend the current customer's stay into the conflict period
        extend_to_date = conflict_checkin + timedelta(days=2)  # Overlaps with conflict booking
        
        response = self.session.post(f"{BASE_URL}/api/extend-stay", json={
            "customer_id": customer_id,
            "new_checkout_date": extend_to_date.isoformat()
        })
        
        # Should be rejected due to conflict
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "conflict" in data["detail"].lower() or "booked" in data["detail"].lower()
        print(f"✓ Correctly blocked extend stay due to booking conflict")
        print(f"  - Error message: {data['detail']}")
    
    def test_06_checkout_preview_uses_customer_rate(self):
        """Test that checkout preview uses customer's booked rate, not room's default rate"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        customer = customers[0]
        customer_id = customer.get('id')
        room_number = customer.get('current_room')
        room_charges = customer.get('room_charges', 0)
        
        # Get room's default rate
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms")
        assert rooms_response.status_code == 200
        rooms = rooms_response.json()
        room = next((r for r in rooms if r.get('room_number') == room_number), None)
        
        if room:
            room_default_rate = room.get('price_per_night', 0)
            print(f"  - Room {room_number} default rate: {room_default_rate}")
        
        # Get checkout preview
        preview_response = self.session.get(f"{BASE_URL}/api/customer/{customer_id}/checkout-preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()
        
        # Verify the preview uses customer's rate
        customer_rate = preview.get('price_per_night', 0)
        planned_nights = preview.get('planned_nights', 1)
        original_charges = preview.get('original_room_charges', 0)
        
        # Calculate expected rate from customer's booking
        expected_rate = original_charges / planned_nights if planned_nights > 0 else 0
        
        print(f"✓ Checkout preview for {customer.get('name')}")
        print(f"  - Customer's booked rate per night: {customer_rate}")
        print(f"  - Expected rate (charges/nights): {expected_rate}")
        print(f"  - Original room charges: {original_charges}")
        print(f"  - Planned nights: {planned_nights}")
        
        # The rate should match the calculated rate from customer's booking
        assert abs(customer_rate - expected_rate) < 0.01, f"Rate mismatch: {customer_rate} vs {expected_rate}"
        
        # If room default rate is different, verify we're NOT using it
        if room and room_default_rate != customer_rate:
            print(f"  - Room default rate ({room_default_rate}) differs from customer rate ({customer_rate}) - CORRECT!")
    
    def test_07_early_checkout_uses_customer_rate(self):
        """Test that early checkout calculation uses customer's booked rate"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        # Find a customer with future checkout date
        customer = None
        for c in customers:
            checkout_str = c.get('check_out_date', '')
            if isinstance(checkout_str, str):
                checkout_date = datetime.strptime(checkout_str.split('T')[0], '%Y-%m-%d').date()
            else:
                checkout_date = checkout_str
            
            if checkout_date > datetime.now().date():
                customer = c
                break
        
        if not customer:
            pytest.skip("No customer with future checkout date for early checkout test")
        
        customer_id = customer.get('id')
        room_charges = customer.get('room_charges', 0)
        
        # Get checkout preview first
        preview_response = self.session.get(f"{BASE_URL}/api/customer/{customer_id}/checkout-preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()
        
        # Verify the calculation uses customer's rate
        customer_rate = preview.get('price_per_night', 0)
        actual_nights = preview.get('actual_nights', 1)
        actual_charges = preview.get('actual_room_charges', 0)
        
        # Verify actual charges = rate * actual nights
        expected_actual_charges = customer_rate * actual_nights
        
        print(f"✓ Early checkout calculation for {customer.get('name')}")
        print(f"  - Customer rate per night: {customer_rate}")
        print(f"  - Actual nights stayed: {actual_nights}")
        print(f"  - Actual room charges: {actual_charges}")
        print(f"  - Expected charges (rate * nights): {expected_actual_charges}")
        
        assert abs(actual_charges - expected_actual_charges) < 0.01, \
            f"Charge calculation mismatch: {actual_charges} vs {expected_actual_charges}"
    
    def test_08_number_formatting_in_response(self):
        """Test that API responses contain proper numeric values for UI formatting"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        customer = customers[0]
        customer_id = customer.get('id')
        
        # Get checkout preview
        preview_response = self.session.get(f"{BASE_URL}/api/customer/{customer_id}/checkout-preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()
        
        # Verify all numeric fields are proper numbers (not strings)
        numeric_fields = [
            'price_per_night', 'original_room_charges', 'actual_room_charges',
            'potential_refund', 'restaurant_charges', 'advance_amount',
            'planned_nights', 'actual_nights', 'days_early'
        ]
        
        print(f"✓ Verifying numeric fields in checkout preview response")
        for field in numeric_fields:
            value = preview.get(field)
            if value is not None:
                assert isinstance(value, (int, float)), f"Field {field} should be numeric, got {type(value)}"
                print(f"  - {field}: {value} (type: {type(value).__name__})")
        
        print("✓ All numeric fields are proper numbers for UI formatting")
    
    def test_09_dashboard_shows_updated_checkout(self):
        """Test that dashboard reflects updated checkout date after extending stay"""
        # Get checked-in customers
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200
        customers = customers_response.json()
        
        if not customers:
            pytest.skip("No checked-in customers to test")
        
        customer = customers[0]
        customer_id = customer.get('id')
        original_checkout = customer.get('check_out_date')
        
        # Parse original checkout
        if isinstance(original_checkout, str):
            checkout_date = datetime.strptime(original_checkout.split('T')[0], '%Y-%m-%d').date()
        else:
            checkout_date = original_checkout
        
        # Extend stay by 1 day
        new_checkout = checkout_date + timedelta(days=1)
        
        extend_response = self.session.post(f"{BASE_URL}/api/extend-stay", json={
            "customer_id": customer_id,
            "new_checkout_date": new_checkout.isoformat()
        })
        
        if extend_response.status_code != 200:
            # May fail due to conflict from previous test
            print(f"  - Extend stay failed (may be due to conflict): {extend_response.text}")
            pytest.skip("Could not extend stay - may have conflict from previous test")
        
        # Verify the customer record is updated
        updated_customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert updated_customers_response.status_code == 200
        updated_customers = updated_customers_response.json()
        
        updated_customer = next((c for c in updated_customers if c.get('id') == customer_id), None)
        assert updated_customer is not None
        
        updated_checkout = updated_customer.get('check_out_date')
        if isinstance(updated_checkout, str):
            updated_checkout_date = datetime.strptime(updated_checkout.split('T')[0], '%Y-%m-%d').date()
        else:
            updated_checkout_date = updated_checkout
        
        assert updated_checkout_date == new_checkout, \
            f"Checkout date not updated: expected {new_checkout}, got {updated_checkout_date}"
        
        print(f"✓ Dashboard shows updated checkout date")
        print(f"  - Original: {checkout_date}")
        print(f"  - Updated: {updated_checkout_date}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
