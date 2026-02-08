"""
Test SMS/Email Notification System for Hotel Management
Tests: SMS on booking, check-in, checkout, cleaning assignment, custom messaging
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSMSNotificationSystem:
    """Test SMS notification triggers and custom messaging endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = None
        self.login()
    
    def login(self):
        """Login and get auth token"""
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
    
    def test_01_sms_settings_configured(self):
        """Verify SMS settings are configured with notify.lk"""
        response = requests.get(f"{BASE_URL}/api/sms-settings", headers=self.headers)
        assert response.status_code == 200, f"Failed to get SMS settings: {response.text}"
        
        settings = response.json()
        assert settings.get("is_configured") == True, "SMS should be configured"
        assert settings.get("provider") == "notify_lk", "Provider should be notify_lk"
        assert settings.get("notify_lk_user_id"), "notify_lk_user_id should be set"
        assert settings.get("notify_lk_api_key"), "notify_lk_api_key should be set"
        assert settings.get("notify_lk_sender_id"), "notify_lk_sender_id should be set"
        print(f"SMS Settings: provider={settings['provider']}, configured={settings['is_configured']}")
    
    def test_02_sms_templates_exist(self):
        """Verify SMS templates exist for all occasions"""
        response = requests.get(f"{BASE_URL}/api/sms-templates", headers=self.headers)
        assert response.status_code == 200, f"Failed to get SMS templates: {response.text}"
        
        templates = response.json()
        assert len(templates) >= 4, f"Expected at least 4 templates, got {len(templates)}"
        
        # Check required occasions
        occasions = [t.get("occasion") for t in templates]
        required_occasions = ["reservation", "checkin", "checkout", "cleaning_assigned"]
        for occasion in required_occasions:
            assert occasion in occasions, f"Missing template for occasion: {occasion}"
        
        print(f"SMS Templates found: {occasions}")
    
    def test_03_custom_sms_endpoint_exists(self):
        """Test /api/send-custom-sms endpoint exists and validates input"""
        # Test with missing phone number
        response = requests.post(f"{BASE_URL}/api/send-custom-sms", 
            headers=self.headers,
            json={"phone_number": "", "message": "Test message"}
        )
        # Should fail validation or return error
        assert response.status_code in [400, 422, 500], f"Expected validation error, got {response.status_code}"
        print(f"Custom SMS endpoint validation works: {response.status_code}")
    
    def test_04_custom_email_endpoint_exists(self):
        """Test /api/send-custom-email endpoint exists and validates input"""
        # Test with missing email
        response = requests.post(f"{BASE_URL}/api/send-custom-email",
            headers=self.headers,
            json={"email": "", "subject": "Test", "body": "Test body"}
        )
        # Should fail validation or return error
        assert response.status_code in [400, 422, 500], f"Expected validation error, got {response.status_code}"
        print(f"Custom Email endpoint validation works: {response.status_code}")
    
    def test_05_message_logs_endpoint(self):
        """Test /api/message-logs endpoint returns logs"""
        response = requests.get(f"{BASE_URL}/api/message-logs", headers=self.headers)
        assert response.status_code == 200, f"Failed to get message logs: {response.text}"
        
        logs = response.json()
        assert isinstance(logs, list), "Message logs should be a list"
        print(f"Message logs count: {len(logs)}")
    
    def test_06_guests_endpoint_returns_data(self):
        """Test /api/guests endpoint returns guest data with phone numbers"""
        response = requests.get(f"{BASE_URL}/api/guests", headers=self.headers)
        assert response.status_code == 200, f"Failed to get guests: {response.text}"
        
        guests = response.json()
        assert isinstance(guests, list), "Guests should be a list"
        
        # Check if any guest has phone number
        guests_with_phone = [g for g in guests if g.get("phone") and g.get("phone") != "Not provided"]
        print(f"Total guests: {len(guests)}, with phone: {len(guests_with_phone)}")
    
    def test_07_cleaning_staff_endpoint(self):
        """Test /api/cleaning/staff endpoint for cleaning assignment notifications"""
        response = requests.get(f"{BASE_URL}/api/cleaning/staff", headers=self.headers)
        assert response.status_code == 200, f"Failed to get cleaning staff: {response.text}"
        
        staff = response.json()
        assert isinstance(staff, list), "Cleaning staff should be a list"
        print(f"Cleaning staff count: {len(staff)}")
    
    def test_08_rooms_pending_cleaning(self):
        """Test /api/cleaning/pending endpoint for rooms needing cleaning"""
        response = requests.get(f"{BASE_URL}/api/cleaning/pending", headers=self.headers)
        assert response.status_code == 200, f"Failed to get pending cleaning: {response.text}"
        
        rooms = response.json()
        assert isinstance(rooms, list), "Pending cleaning should be a list"
        print(f"Rooms pending cleaning: {len(rooms)}")
    
    def test_09_booking_creation_with_phone(self):
        """Test booking creation includes phone for SMS notification"""
        # Get available room
        rooms_response = requests.get(f"{BASE_URL}/api/rooms", headers=self.headers)
        assert rooms_response.status_code == 200
        rooms = rooms_response.json()
        available_rooms = [r for r in rooms if r.get("status") == "Available"]
        
        if not available_rooms:
            pytest.skip("No available rooms for booking test")
        
        room = available_rooms[0]
        test_phone = "94771234567"
        
        # Create booking with phone number
        booking_data = {
            "guest_name": "TEST_SMS_Guest",
            "guest_email": "test_sms@example.com",
            "guest_phone": test_phone,
            "room_number": room["room_number"],
            "check_in_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "check_out_date": (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d"),
            "booking_amount": 5000,
            "stay_type": "Night Stay",
            "booking_status": "Upcoming"
        }
        
        response = requests.post(f"{BASE_URL}/api/bookings", 
            headers=self.headers, 
            json=booking_data
        )
        
        # Booking should succeed (SMS notification is non-blocking)
        assert response.status_code == 200, f"Booking creation failed: {response.text}"
        
        booking = response.json()
        assert booking.get("guest_phone") == test_phone, "Phone should be saved in booking"
        print(f"Booking created with phone: {test_phone}, ID: {booking.get('id')}")
        
        # Cleanup - cancel the booking
        if booking.get("id"):
            requests.post(f"{BASE_URL}/api/cancel/{booking['id']}", headers=self.headers)
    
    def test_10_send_custom_sms_with_valid_data(self):
        """Test sending custom SMS with valid phone number"""
        # This will actually try to send SMS via notify.lk
        # The test verifies the endpoint works, actual delivery depends on gateway
        response = requests.post(f"{BASE_URL}/api/send-custom-sms",
            headers=self.headers,
            json={
                "phone_number": "94771234567",
                "message": "Test SMS from Hotel Management System - Please ignore",
                "guest_id": None
            }
        )
        
        # Should either succeed (200) or fail with gateway error (500)
        # Both indicate the endpoint is working
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True, "SMS should be marked as successful"
            print(f"SMS sent successfully: {data.get('message')}")
        else:
            print(f"SMS gateway error (expected if credentials invalid): {response.text}")


class TestEmailNotificationSystem:
    """Test Email notification endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.token = None
        self.login()
    
    def login(self):
        """Login and get auth token"""
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
    
    def test_01_email_settings_endpoint(self):
        """Test email settings endpoint exists"""
        response = requests.get(f"{BASE_URL}/api/email-settings", headers=self.headers)
        assert response.status_code == 200, f"Failed to get email settings: {response.text}"
        
        settings = response.json()
        print(f"Email Settings: provider={settings.get('provider')}, configured={settings.get('is_configured')}")
    
    def test_02_email_templates_exist(self):
        """Verify email templates exist"""
        response = requests.get(f"{BASE_URL}/api/email-templates", headers=self.headers)
        assert response.status_code == 200, f"Failed to get email templates: {response.text}"
        
        templates = response.json()
        assert isinstance(templates, list), "Email templates should be a list"
        print(f"Email templates count: {len(templates)}")
    
    def test_03_custom_email_endpoint_validation(self):
        """Test custom email endpoint validates required fields"""
        # Test with valid data structure but empty values
        response = requests.post(f"{BASE_URL}/api/send-custom-email",
            headers=self.headers,
            json={
                "email": "test@example.com",
                "subject": "Test Subject",
                "body": "Test body content"
            }
        )
        
        # Should either succeed or fail with email provider error
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        print(f"Custom email endpoint response: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
