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
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


@pytest.fixture(scope="module")
def auth_session():
    """Create authenticated session for all tests"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    
    # Login and get token
    login_response = session.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    
    return session


@pytest.fixture(scope="module")
def available_rooms(auth_session):
    """Get list of available rooms"""
    rooms_response = auth_session.get(f"{BASE_URL}/api/rooms")
    rooms = rooms_response.json() if rooms_response.status_code == 200 else []
    available = [r['room_number'] for r in rooms if r.get('status') == 'Available']
    return available


@pytest.fixture(scope="module")
def test_dates():
    """Calculate test dates"""
    return {
        'past_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
        'past_checkout': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
        'today': datetime.now().strftime('%Y-%m-%d'),
        'future_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        'future_checkout': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
    }


class TestAuthentication:
    """Test authentication flows - Login and /api/auth/me endpoint"""
    
    def test_login_success(self):
        """Test successful login with admin credentials"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["token_type"] == "bearer"
        print(f"✓ Login successful, token received")
    
    def test_auth_me_endpoint_no_403(self):
        """Test that /api/auth/me does not return 403 after login"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # First login
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Set authorization header
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Call /api/auth/me
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        
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
    
    def test_past_date_booking_with_checked_in_status(self, auth_session, available_rooms, test_dates):
        """Test creating a past-date booking with 'Checked In' status"""
        if not available_rooms:
            pytest.skip("No available rooms for testing")
        
        room_number = available_rooms[0]
        unique_id = str(uuid.uuid4())[:8]
        
        booking_data = {
            "guest_name": f"TEST_CheckedIn_{unique_id}",
            "guest_email": "pastdate@test.com",
            "guest_phone": "1234567890",
            "guest_country": "Test Country",
            "guest_id_passport": "TEST123",
            "room_number": room_number,
            "check_in_date": test_dates['past_date'],
            "check_out_date": test_dates['future_checkout'],  # Use future checkout to keep room occupied
            "stay_type": "Night Stay",
            "booking_amount": 5000,
            "booking_status": "Checked In",  # Key: Using "Checked In" status
            "additional_notes": "Test past date booking with Checked In status"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        
        # Should NOT return 401 Unauthorized
        assert response.status_code != 401, f"Got 401 Unauthorized when creating past-date booking: {response.text}"
        assert response.status_code == 200, f"Failed to create past-date booking: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["status"] == "Checked In", f"Expected status 'Checked In', got '{data['status']}'"
        print(f"✓ Past-date booking with 'Checked In' status created successfully")
        
        # Verify room status is now Occupied
        rooms_response = auth_session.get(f"{BASE_URL}/api/rooms")
        rooms = rooms_response.json()
        target_room = next((r for r in rooms if r['room_number'] == room_number), None)
        
        assert target_room is not None, f"Room {room_number} not found"
        assert target_room['status'] == 'Occupied', f"Expected room status 'Occupied', got '{target_room['status']}'"
        print(f"✓ Room status correctly updated to 'Occupied'")
        
        # Verify customer record was created
        customers_response = auth_session.get(f"{BASE_URL}/api/customers/checked-in")
        customers = customers_response.json()
        target_customer = next((c for c in customers if c['name'] == f"TEST_CheckedIn_{unique_id}"), None)
        
        assert target_customer is not None, f"Customer record not found"
        assert target_customer['current_room'] == room_number
        print(f"✓ Customer record correctly created")
    
    def test_past_date_booking_with_upcoming_status(self, auth_session, available_rooms, test_dates):
        """Test creating a past-date booking with 'Upcoming' status"""
        if len(available_rooms) < 2:
            pytest.skip("Not enough available rooms for testing")
        
        room_number = available_rooms[1] if len(available_rooms) > 1 else available_rooms[0]
        unique_id = str(uuid.uuid4())[:8]
        
        booking_data = {
            "guest_name": f"TEST_Upcoming_{unique_id}",
            "guest_email": "pastupcoming@test.com",
            "guest_phone": "0987654321",
            "guest_country": "Test Country",
            "guest_id_passport": "TEST456",
            "room_number": room_number,
            "check_in_date": test_dates['past_date'],
            "check_out_date": test_dates['past_checkout'],
            "stay_type": "Night Stay",
            "booking_amount": 4000,
            "booking_status": "Upcoming",  # Using "Upcoming" status for past date
            "additional_notes": "Test past date booking with Upcoming status"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
        
        assert response.status_code != 401, f"Got 401 Unauthorized: {response.text}"
        assert response.status_code == 200, f"Failed to create booking: {response.status_code} - {response.text}"
        
        data = response.json()
        assert data["status"] == "Upcoming", f"Expected status 'Upcoming', got '{data['status']}'"
        print(f"✓ Past-date booking with 'Upcoming' status created successfully")


class TestRegularCheckinFlow:
    """Test that regular check-in flow still works correctly"""
    
    def test_regular_booking_and_checkin(self, auth_session, available_rooms, test_dates):
        """Test creating a regular booking and then checking in"""
        if len(available_rooms) < 3:
            pytest.skip("Not enough available rooms for testing")
        
        room_number = available_rooms[2] if len(available_rooms) > 2 else available_rooms[0]
        unique_id = str(uuid.uuid4())[:8]
        guest_name = f"TEST_Regular_{unique_id}"
        
        # Create a regular booking (today with Upcoming status)
        booking_data = {
            "guest_name": guest_name,
            "guest_email": "regular@test.com",
            "guest_phone": "7778889999",
            "room_number": room_number,
            "check_in_date": test_dates['today'],
            "check_out_date": test_dates['future_checkout'],
            "stay_type": "Night Stay",
            "booking_amount": 8000,
            "booking_status": "Upcoming",
            "additional_notes": "Test regular check-in flow"
        }
        
        booking_response = auth_session.post(f"{BASE_URL}/api/bookings", json=booking_data)
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
        
        checkin_response = auth_session.post(f"{BASE_URL}/api/checkin", json=checkin_data)
        assert checkin_response.status_code == 200, f"Check-in failed: {checkin_response.text}"
        
        checkin_result = checkin_response.json()
        assert "customer" in checkin_result
        assert checkin_result["customer"]["name"] == guest_name
        
        print(f"✓ Regular check-in flow works correctly")
        
        # Verify room is now occupied
        rooms_response = auth_session.get(f"{BASE_URL}/api/rooms")
        rooms = rooms_response.json()
        target_room = next((r for r in rooms if r['room_number'] == room_number), None)
        
        assert target_room['status'] == 'Occupied', f"Room should be Occupied after check-in"
        print(f"✓ Room status updated to Occupied after regular check-in")


class TestStatusConsistency:
    """Test that both 'Checked-in' and 'Checked In' status variants work"""
    
    def test_status_variants_in_queries(self, auth_session):
        """Test that status queries handle both 'Checked-in' and 'Checked In' variants"""
        # Get checked-in customers (should work regardless of status variant)
        response = auth_session.get(f"{BASE_URL}/api/customers/checked-in")
        assert response.status_code == 200, f"Failed to get checked-in customers: {response.text}"
        
        # Get bookings with Checked-in status
        response = auth_session.get(f"{BASE_URL}/api/bookings?status=Checked-in")
        assert response.status_code == 200, f"Failed to get Checked-in bookings: {response.text}"
        
        print(f"✓ Status variant queries work correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
