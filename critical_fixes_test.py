#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST - BOTH CRITICAL FIXES

Testing the two critical user-reported issues:
1. Advance Payment Double Counting Bug (Fixed)
2. Date Extension for Checked-in Bookings (Fixed)

This test verifies both fixes are working correctly.
"""

import requests
import json
from datetime import datetime, date, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BASE_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_URL = f"{BASE_URL}/api"

# Test credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

class HotelTestSuite:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_results = []
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate as admin user"""
        try:
            response = self.session.post(f"{API_URL}/auth/login", json={
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data['access_token']
                self.session.headers.update({
                    'Authorization': f'Bearer {self.auth_token}'
                })
                self.log_result("Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Authentication", False, f"Login failed: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Authentication", False, f"Authentication error: {str(e)}")
            return False
    
    def get_financial_balance(self):
        """Get current financial balance"""
        try:
            response = self.session.get(f"{API_URL}/daily-financial-summary")
            if response.status_code == 200:
                data = response.json()
                return {
                    'cash_balance': data.get('cash_balance', 0),
                    'bank_balance': data.get('bank_balance', 0),
                    'total_revenue': data.get('total_revenue', 0),
                    'total_expenses': data.get('total_expenses', 0)
                }
            else:
                self.log_result("Get Financial Balance", False, f"Failed to get balance: {response.text}")
                return None
        except Exception as e:
            self.log_result("Get Financial Balance", False, f"Error getting balance: {str(e)}")
            return None
    
    def create_test_room(self, room_number="TEST101", price=1000.0):
        """Create a test room"""
        try:
            room_data = {
                "room_number": room_number,
                "room_type": "Double",
                "price_per_night": price,
                "max_occupancy": 2,
                "amenities": ["WiFi", "AC"]
            }
            
            response = self.session.post(f"{API_URL}/rooms", json=room_data)
            if response.status_code == 200:
                self.log_result("Create Test Room", True, f"Room {room_number} created successfully")
                return True
            else:
                self.log_result("Create Test Room", False, f"Failed to create room: {response.text}")
                return False
        except Exception as e:
            self.log_result("Create Test Room", False, f"Error creating room: {str(e)}")
            return False
    
    def create_test_booking(self, guest_name="John Doe", room_number="TEST101", stay_type="Night Stay", booking_amount=1000.0):
        """Create a test booking"""
        try:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            booking_data = {
                "guest_name": guest_name,
                "guest_email": "john@example.com",
                "guest_phone": "+1234567890",
                "guest_id_passport": "ID123456",
                "guest_country": "USA",
                "room_number": room_number,
                "check_in_date": today.isoformat(),
                "check_out_date": tomorrow.isoformat() if stay_type == "Night Stay" else today.isoformat(),
                "stay_type": stay_type,
                "booking_amount": booking_amount,
                "additional_notes": "Test booking for advance payment testing"
            }
            
            response = self.session.post(f"{API_URL}/bookings", json=booking_data)
            if response.status_code == 200:
                booking = response.json()
                self.log_result("Create Test Booking", True, f"Booking created for {guest_name}")
                return booking['id']
            else:
                self.log_result("Create Test Booking", False, f"Failed to create booking: {response.text}")
                return None
        except Exception as e:
            self.log_result("Create Test Booking", False, f"Error creating booking: {str(e)}")
            return None
    
    def checkin_booking(self, booking_id, advance_amount=0.0, payment_method="Cash"):
        """Check in a booking with advance payment"""
        try:
            checkin_data = {
                "booking_id": booking_id,
                "advance_amount": advance_amount,
                "payment_method": payment_method,
                "notes": "Test check-in with advance payment"
            }
            
            response = self.session.post(f"{API_URL}/checkin", json=checkin_data)
            if response.status_code == 200:
                data = response.json()
                customer = data.get('customer', {})
                self.log_result("Check-in Booking", True, f"Customer checked in successfully")
                return customer.get('id')
            else:
                self.log_result("Check-in Booking", False, f"Failed to check in: {response.text}")
                return None
        except Exception as e:
            self.log_result("Check-in Booking", False, f"Error during check-in: {str(e)}")
            return None
    
    def collect_advance_payment(self, customer_id, amount, payment_method="Cash"):
        """Collect additional advance payment using Get Advance feature"""
        try:
            advance_data = {
                "customer_id": customer_id,
                "amount": amount,
                "payment_method": payment_method,
                "notes": "Additional advance payment via Get Advance feature"
            }
            
            response = self.session.post(f"{API_URL}/advance-payment", json=advance_data)
            if response.status_code == 200:
                self.log_result("Collect Advance Payment", True, f"Advance payment of {amount} collected successfully")
                return True
            else:
                self.log_result("Collect Advance Payment", False, f"Failed to collect advance: {response.text}")
                return False
        except Exception as e:
            self.log_result("Collect Advance Payment", False, f"Error collecting advance: {str(e)}")
            return False
    
    def extend_booking_date(self, booking_id, new_checkout_date):
        """Extend booking checkout date"""
        try:
            update_data = {
                "check_out_date": new_checkout_date.isoformat()
            }
            
            response = self.session.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
            if response.status_code == 200:
                self.log_result("Extend Booking Date", True, f"Booking extended to {new_checkout_date}")
                return True
            else:
                self.log_result("Extend Booking Date", False, f"Failed to extend booking: {response.text}")
                return False
        except Exception as e:
            self.log_result("Extend Booking Date", False, f"Error extending booking: {str(e)}")
            return False
    
    def test_advance_payment_no_double_counting(self):
        """
        TEST 1: Advance Payment Real-time Balance (Fixed)
        Verify advance payments appear in financial balances without double counting
        """
        print("\n" + "="*80)
        print("TEST 1: ADVANCE PAYMENT REAL-TIME BALANCE (NO DOUBLE COUNTING)")
        print("="*80)
        
        # Get initial balance
        initial_balance = self.get_financial_balance()
        if not initial_balance:
            return False
        
        print(f"Initial Balance - Cash: {initial_balance['cash_balance']}, Bank: {initial_balance['bank_balance']}")
        
        # Create test room and booking
        if not self.create_test_room("ADV101", 1500.0):
            return False
        
        booking_id = self.create_test_booking("Alice Smith", "ADV101", "Night Stay", 1500.0)
        if not booking_id:
            return False
        
        # Check in with advance payment (Cash)
        customer_id = self.checkin_booking(booking_id, advance_amount=750.0, payment_method="Cash")
        if not customer_id:
            return False
        
        # Get balance after check-in advance
        balance_after_checkin = self.get_financial_balance()
        if not balance_after_checkin:
            return False
        
        print(f"After Check-in Advance - Cash: {balance_after_checkin['cash_balance']}, Bank: {balance_after_checkin['bank_balance']}")
        
        # Verify cash balance increased by exactly 750 (no double counting)
        expected_cash = initial_balance['cash_balance'] + 750.0
        actual_cash = balance_after_checkin['cash_balance']
        
        if abs(actual_cash - expected_cash) < 0.01:
            self.log_result("Check-in Advance Payment Balance", True, 
                          f"Cash balance correctly increased by 750.0 (Expected: {expected_cash}, Actual: {actual_cash})")
        else:
            self.log_result("Check-in Advance Payment Balance", False, 
                          f"Cash balance incorrect! Expected: {expected_cash}, Actual: {actual_cash}, Difference: {actual_cash - expected_cash}")
            return False
        
        # Collect additional advance payment (Card)
        if not self.collect_advance_payment(customer_id, 500.0, "Card"):
            return False
        
        # Get balance after additional advance
        balance_after_additional = self.get_financial_balance()
        if not balance_after_additional:
            return False
        
        print(f"After Additional Advance - Cash: {balance_after_additional['cash_balance']}, Bank: {balance_after_additional['bank_balance']}")
        
        # Verify bank balance increased by exactly 500 (no double counting)
        expected_bank = initial_balance['bank_balance'] + 500.0
        actual_bank = balance_after_additional['bank_balance']
        
        if abs(actual_bank - expected_bank) < 0.01:
            self.log_result("Additional Advance Payment Balance", True, 
                          f"Bank balance correctly increased by 500.0 (Expected: {expected_bank}, Actual: {actual_bank})")
        else:
            self.log_result("Additional Advance Payment Balance", False, 
                          f"Bank balance incorrect! Expected: {expected_bank}, Actual: {actual_bank}, Difference: {actual_bank - expected_bank}")
            return False
        
        # Verify cash balance remained the same
        if abs(balance_after_additional['cash_balance'] - balance_after_checkin['cash_balance']) < 0.01:
            self.log_result("Cash Balance Unchanged", True, "Cash balance correctly unchanged after Card payment")
        else:
            self.log_result("Cash Balance Unchanged", False, "Cash balance incorrectly changed after Card payment")
            return False
        
        return True
    
    def test_checked_in_booking_date_extension(self):
        """
        TEST 2: Checked-in Booking Date Extension (Fixed)
        Verify checked-in bookings can extend checkout dates successfully
        """
        print("\n" + "="*80)
        print("TEST 2: CHECKED-IN BOOKING DATE EXTENSION")
        print("="*80)
        
        # Create test room and booking
        if not self.create_test_room("EXT102", 2000.0):
            return False
        
        # Create short time booking first
        booking_id = self.create_test_booking("Bob Johnson", "EXT102", "Short Time", 1000.0)
        if not booking_id:
            return False
        
        # Check in the booking
        customer_id = self.checkin_booking(booking_id, advance_amount=200.0, payment_method="Cash")
        if not customer_id:
            return False
        
        # Try to extend checkout date (should work for checked-in bookings)
        today = datetime.now().date()
        extended_date = today + timedelta(days=2)
        
        if self.extend_booking_date(booking_id, extended_date):
            self.log_result("Short Time Booking Extension", True, 
                          f"Successfully extended short time booking to {extended_date}")
        else:
            return False
        
        # Test night stay booking extension
        if not self.create_test_room("EXT103", 2000.0):
            return False
            
        booking_id_2 = self.create_test_booking("Carol Davis", "EXT103", "Night Stay", 2000.0)
        if not booking_id_2:
            return False
        
        # Check in the night stay booking
        customer_id_2 = self.checkin_booking(booking_id_2, advance_amount=500.0, payment_method="Card")
        if not customer_id_2:
            return False
        
        # Extend night stay booking
        extended_date_2 = today + timedelta(days=3)
        
        if self.extend_booking_date(booking_id_2, extended_date_2):
            self.log_result("Night Stay Booking Extension", True, 
                          f"Successfully extended night stay booking to {extended_date_2}")
        else:
            return False
        
        return True
    
    def test_validation_rules(self):
        """
        TEST 3: Validation Rules (Working)
        Verify proper validation prevents invalid modifications
        """
        print("\n" + "="*80)
        print("TEST 3: VALIDATION RULES FOR CHECKED-IN BOOKINGS")
        print("="*80)
        
        # Create test room and booking
        if not self.create_test_room("VAL103", 1800.0):
            return False
        
        booking_id = self.create_test_booking("David Wilson", "VAL103", "Night Stay", 1800.0)
        if not booking_id:
            return False
        
        # Check in the booking
        customer_id = self.checkin_booking(booking_id, advance_amount=300.0, payment_method="Cash")
        if not customer_id:
            return False
        
        # Test 1: Try to change check-in date (should be blocked)
        try:
            yesterday = datetime.now().date() - timedelta(days=1)
            update_data = {"check_in_date": yesterday.isoformat()}
            
            response = self.session.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
            if response.status_code == 400 and "Cannot change check-in date for checked-in bookings" in response.text:
                self.log_result("Block Check-in Date Change", True, "Correctly blocked check-in date change for checked-in booking")
            else:
                self.log_result("Block Check-in Date Change", False, f"Failed to block check-in date change: {response.text}")
                return False
        except Exception as e:
            self.log_result("Block Check-in Date Change", False, f"Error testing check-in date change: {str(e)}")
            return False
        
        # Test 2: Try to shorten checkout date (should be blocked)
        try:
            today = datetime.now().date()
            shortened_date = today  # Same day (shortening from tomorrow)
            update_data = {"check_out_date": shortened_date.isoformat()}
            
            response = self.session.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
            if response.status_code == 400 and "Cannot shorten checkout date for checked-in bookings" in response.text:
                self.log_result("Block Checkout Date Shortening", True, "Correctly blocked checkout date shortening for checked-in booking")
            else:
                self.log_result("Block Checkout Date Shortening", False, f"Failed to block checkout date shortening: {response.text}")
                return False
        except Exception as e:
            self.log_result("Block Checkout Date Shortening", False, f"Error testing checkout date shortening: {str(e)}")
            return False
        
        # Test 3: Try to change room (should be blocked)
        try:
            update_data = {"room_number": "VAL104"}
            
            response = self.session.put(f"{API_URL}/bookings/{booking_id}", json=update_data)
            if response.status_code == 400 and "Cannot change room for booking with status" in response.text:
                self.log_result("Block Room Change", True, "Correctly blocked room change for checked-in booking")
            else:
                self.log_result("Block Room Change", False, f"Failed to block room change: {response.text}")
                return False
        except Exception as e:
            self.log_result("Block Room Change", False, f"Error testing room change: {str(e)}")
            return False
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Get all rooms and delete test rooms
            response = self.session.get(f"{API_URL}/rooms")
            if response.status_code == 200:
                rooms = response.json()
                for room in rooms:
                    if room['room_number'].startswith('TEST') or room['room_number'].startswith('ADV') or \
                       room['room_number'].startswith('EXT') or room['room_number'].startswith('VAL'):
                        self.session.delete(f"{API_URL}/rooms/{room['id']}")
            
            print("✅ Test data cleanup completed")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 STARTING FINAL COMPREHENSIVE TEST - BOTH CRITICAL FIXES")
        print("="*80)
        
        # Authenticate
        if not self.authenticate():
            return False
        
        # Run tests
        test1_success = self.test_advance_payment_no_double_counting()
        test2_success = self.test_checked_in_booking_date_extension()
        test3_success = self.test_validation_rules()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "="*80)
        print("FINAL TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if "✅ PASS" in r['status']])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result['status']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Overall result
        all_critical_tests_passed = test1_success and test2_success and test3_success
        
        print("\n" + "="*80)
        if all_critical_tests_passed:
            print("🎉 ALL CRITICAL FIXES VERIFIED SUCCESSFULLY!")
            print("✅ Advance payments appear in financial balances without double counting")
            print("✅ Checked-in bookings can extend checkout dates successfully")
            print("✅ Proper validation prevents invalid modifications")
            print("✅ Both user-reported issues completely resolved")
            print("🚀 SYSTEM READY FOR PRODUCTION")
        else:
            print("❌ CRITICAL ISSUES STILL EXIST!")
            if not test1_success:
                print("❌ Advance payment double counting issue NOT resolved")
            if not test2_success:
                print("❌ Checked-in booking date extension issue NOT resolved")
            if not test3_success:
                print("❌ Validation rules not working properly")
        
        print("="*80)
        return all_critical_tests_passed

if __name__ == "__main__":
    test_suite = HotelTestSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)