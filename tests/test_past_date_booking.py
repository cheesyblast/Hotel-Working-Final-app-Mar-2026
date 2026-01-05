"""
Test suite for Hotel Management System - Past Date Booking Bug Fix
Tests the following features:
1. Past-date booking creation with 'Checked In' status
2. Past-date booking creation with 'Upcoming' status
3. Login should not have 403 errors on /api/auth/me endpoint
4. Room status should update correctly when past-date booking is created with 'Checked In'
5. Customer record should be created when past-date booking uses 'Checked In' status
6. Regular check-in flow should still work correctly
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthentication:
    """Test authentication flows - Login and /api/auth/me endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_login_success(self):
        """Test successful login with admin credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer"
        print(f"✓ Login successful, token received")
        return data["access_token"]
    
    def test_auth_me_endpoint_no_403(self):
        """Test that /api/auth/me does not return 403 after login"""
        # First login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Set authorization header
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Call /api/auth/me
        me_response = self.session.get(f"{BASE_URL}/api/auth/me")
        
        # Should NOT be 403 or 401
        assert me_response.status_code != 403, f"/api/auth/me returned 403 Forbidden"
        assert me_response.status_code != 401, f"/api/auth/me returned 401 Unauthorized"
        assert me_response.status_code == 200, f"/api/auth/me returned {me_response.status_code}: {me_response.text}"
        
        data = me_response.json()
        assert "username" in data
        assert data["username"] == "admin"
        print(f"✓ /api/auth/me works correctly, no 403 error")


class TestPastDateBooking:
    """Test past-date booking creation with different statuses"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login and get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get available rooms
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms")
        self.rooms = rooms_response.json() if rooms_response.status_code == 200 else []
        
        # Calculate past date (3 days ago)
        self.past_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        self.past_checkout = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        self.future_checkout = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
    
    def get_available_room(self):
        """Get an available room for testing"""
        for room in self.rooms:
            if room.get('status') == 'Available':
                return room['room_number']
        return None
    
    def test_past_date_booking_with_checked_in_status(self):
        """Test creating a past-date booking with 'Checked In' status"""
        room_number = self.get_available_room()
        if not room_number:
            pytest.skip("No available rooms for testing")
        
        booking_data = {
            "guest_name": "TEST_PastDateCheckedIn",
            "guest_email": "pastdate@test.com",
            "guest_phone": "1234567890",
            "guest_country": "Test Country",
            "guest_id_passport": "TEST123",
            "room_number": room_number,
            "check_in_date": self.past_date,
            "check_out_date": self.past_checkout,
            "stay_type": "Night Stay",
            "booking_amount": 5000,
            "booking_status": "Checked In",  # Key: Using "Checked In" status
            "additional_notes": "Test past date booking with Checked In status"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        
        # Should NOT return 401 Unauthorized
        assert response.status_code != 401, f"Got 401 Unauthorized when creating past-date booking: {response.text}"
        assert response.status_code == 200, f"Failed to create past-date booking: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["status"] == "Checked In", f"Expected status 'Checked In', got '{data['status']}'"
        assert data["guest_name"] == "TEST_PastDateCheckedIn"
        print(f"✓ Past-date booking with 'Checked In' status created successfully")
        
        return data["id"], room_number
    
    def test_past_date_booking_with_upcoming_status(self):
        """Test creating a past-date booking with 'Upcoming' status"""
        room_number = self.get_available_room()
        if not room_number:
            pytest.skip("No available rooms for testing")
        
        booking_data = {
            "guest_name": "TEST_PastDateUpcoming",
            "guest_email": "pastupcoming@test.com",
            "guest_phone": "0987654321",
            "guest_country": "Test Country",
            "guest_id_passport": "TEST456",
            "room_number": room_number,
            "check_in_date": self.past_date,
            "check_out_date": self.past_checkout,
            "stay_type": "Night Stay",
            "booking_amount": 4000,
            "booking_status": "Upcoming",  # Using "Upcoming" status for past date
            "additional_notes": "Test past date booking with Upcoming status"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        
        assert response.status_code != 401, f"Got 401 Unauthorized: {response.text}"
        assert response.status_code == 200, f"Failed to create booking: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["status"] == "Upcoming", f"Expected status 'Upcoming', got '{data['status']}'"
        print(f"✓ Past-date booking with 'Upcoming' status created successfully")
        
        return data["id"]
    
    def test_room_status_updates_on_checked_in_booking(self):
        """Test that room status updates to 'Occupied' when past-date booking is created with 'Checked In'"""
        room_number = self.get_available_room()
        if not room_number:
            pytest.skip("No available rooms for testing")
        
        # Create past-date booking with Checked In status
        booking_data = {
            "guest_name": "TEST_RoomStatusCheck",
            "guest_email": "roomstatus@test.com",
            "guest_phone": "1112223333",
            "room_number": room_number,
            "check_in_date": self.past_date,
            "check_out_date": self.future_checkout,  # Checkout in future so room stays occupied
            "stay_type": "Night Stay",
            "booking_amount": 6000,
            "booking_status": "Checked In",
            "additional_notes": "Test room status update"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Failed to create booking: {response.text}"
        
        # Check room status
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms")
        assert rooms_response.status_code == 200
        
        rooms = rooms_response.json()
        target_room = next((r for r in rooms if r['room_number'] == room_number), None)
        
        assert target_room is not None, f"Room {room_number} not found"
        assert target_room['status'] == 'Occupied', f"Expected room status 'Occupied', got '{target_room['status']}'"
        assert target_room['current_guest'] == "TEST_RoomStatusCheck", f"Expected guest name 'TEST_RoomStatusCheck', got '{target_room.get('current_guest')}'"
        
        print(f"✓ Room status correctly updated to 'Occupied' for past-date Checked In booking")
    
    def test_customer_record_created_on_checked_in_booking(self):
        """Test that customer record is created when past-date booking uses 'Checked In' status"""
        room_number = self.get_available_room()
        if not room_number:
            pytest.skip("No available rooms for testing")
        
        guest_name = "TEST_CustomerRecord"
        
        booking_data = {
            "guest_name": guest_name,
            "guest_email": "customerrecord@test.com",
            "guest_phone": "4445556666",
            "room_number": room_number,
            "check_in_date": self.past_date,
            "check_out_date": self.future_checkout,
            "stay_type": "Night Stay",
            "booking_amount": 7000,
            "booking_status": "Checked In",
            "additional_notes": "Test customer record creation"
        }
        
        response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert response.status_code == 200, f"Failed to create booking: {response.text}"
        
        # Check if customer record was created
        customers_response = self.session.get(f"{BASE_URL}/api/customers/checked-in")
        assert customers_response.status_code == 200, f"Failed to get customers: {customers_response.text}"
        
        customers = customers_response.json()
        target_customer = next((c for c in customers if c['name'] == guest_name), None)
        
        assert target_customer is not None, f"Customer record for '{guest_name}' not found in checked-in customers"
        assert target_customer['current_room'] == room_number
        assert target_customer['is_checked_out'] == False
        
        print(f"✓ Customer record correctly created for past-date Checked In booking")


class TestRegularCheckinFlow:
    """Test that regular check-in flow still works correctly"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login and get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get available rooms
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms")
        self.rooms = rooms_response.json() if rooms_response.status_code == 200 else []
        
        # Calculate dates
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.checkout_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    def get_available_room(self):
        """Get an available room for testing"""
        for room in self.rooms:
            if room.get('status') == 'Available':
                return room['room_number']
        return None
    
    def test_regular_booking_and_checkin(self):
        """Test creating a regular booking and then checking in"""
        room_number = self.get_available_room()
        if not room_number:
            pytest.skip("No available rooms for testing")
        
        # Create a regular booking (future date or today with Upcoming status)
        booking_data = {
            "guest_name": "TEST_RegularCheckin",
            "guest_email": "regular@test.com",
            "guest_phone": "7778889999",
            "room_number": room_number,
            "check_in_date": self.today,
            "check_out_date": self.checkout_date,
            "stay_type": "Night Stay",
            "booking_amount": 8000,
            "booking_status": "Upcoming",
            "additional_notes": "Test regular check-in flow"
        }
        
        booking_response = self.session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        assert booking_response.status_code == 200, f"Failed to create booking: {booking_response.text}"
        
        booking = booking_response.json()
        booking_id = booking["id"]
        assert booking["status"] == "Upcoming"
        print(f"✓ Regular booking created with Upcoming status")
        
        # Now perform check-in
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 1000,
            "notes": "Test check-in",
            "payment_method": "Cash"
        }
        
        checkin_response = self.session.post(f"{BASE_URL}/api/checkin", json=checkin_data)
        assert checkin_response.status_code == 200, f"Check-in failed: {checkin_response.text}"
        
        checkin_result = checkin_response.json()
        assert "customer" in checkin_result
        assert checkin_result["customer"]["name"] == "TEST_RegularCheckin"
        
        print(f"✓ Regular check-in flow works correctly")
        
        # Verify room is now occupied
        rooms_response = self.session.get(f"{BASE_URL}/api/rooms")
        rooms = rooms_response.json()
        target_room = next((r for r in rooms if r['room_number'] == room_number), None)
        
        assert target_room['status'] == 'Occupied', f"Room should be Occupied after check-in"
        print(f"✓ Room status updated to Occupied after regular check-in")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login and get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_cleanup_test_bookings(self):
        """Cleanup test bookings created during tests"""
        # Get all bookings
        response = self.session.get(f"{BASE_URL}/api/bookings")
        if response.status_code != 200:
            print("Could not fetch bookings for cleanup")
            return
        
        bookings = response.json().get("bookings", [])
        
        # Cancel test bookings
        cancelled_count = 0
        for booking in bookings:
            if booking.get("guest_name", "").startswith("TEST_"):
                cancel_response = self.session.post(f"{BASE_URL}/api/cancel/{booking['id']}")
                if cancel_response.status_code == 200:
                    cancelled_count += 1
        
        print(f"✓ Cleaned up {cancelled_count} test bookings")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
