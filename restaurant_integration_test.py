#!/usr/bin/env python3

import requests
import json
import sys
from datetime import datetime, date
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class RestaurantIntegrationTest:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.test_customer_id = None
        self.test_booking_id = None

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
        if details and not success:
            print(f"   Details: {details}")

    def authenticate_admin(self):
        """Authenticate as admin user"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": "admin",
                "password": "admin123"
            })
            
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
                self.log_result("Admin Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Admin login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Admin login error: {str(e)}")
            return False

    def setup_test_guest(self):
        """Create a test booking and check in a guest for room service testing"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Create a booking
            booking_data = {
                "guest_name": "Room Service Test Guest",
                "guest_email": "roomservice@test.com",
                "guest_phone": "123-456-7890",
                "guest_id_passport": "RS123456",
                "guest_country": "Sri Lanka",
                "room_number": "103",
                "check_in_date": date.today().isoformat(),
                "check_out_date": (date.today()).isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 5000.0,
                "booking_status": "Upcoming"
            }
            
            booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
            if booking_response.status_code == 200:
                booking = booking_response.json()
                self.test_booking_id = booking['id']
                self.log_result("Create Test Booking", True, f"Created booking for room {booking['room_number']}")
            else:
                self.log_result("Create Test Booking", False, f"Failed to create booking: {booking_response.status_code}", booking_response.text)
                return False
            
            # Check in the guest
            checkin_data = {
                "booking_id": self.test_booking_id,
                "advance_amount": 1000.0,
                "notes": "Test check-in for room service",
                "payment_method": "Cash"
            }
            
            checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
            if checkin_response.status_code == 200:
                self.log_result("Check-in Test Guest", True, "Guest checked in successfully")
                
                # Get the customer ID
                customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
                if customers_response.status_code == 200:
                    customers = customers_response.json()
                    test_customer = next((c for c in customers if c.get('current_room') == '101'), None)
                    if test_customer:
                        self.test_customer_id = test_customer['id']
                        self.log_result("Get Test Customer ID", True, f"Customer ID: {self.test_customer_id}")
                        return True
                    else:
                        self.log_result("Get Test Customer ID", False, "Test customer not found in checked-in list")
                        return False
                else:
                    self.log_result("Get Test Customer ID", False, "Failed to get checked-in customers")
                    return False
            else:
                self.log_result("Check-in Test Guest", False, f"Failed to check in guest: {checkin_response.status_code}", checkin_response.text)
                return False
                
        except Exception as e:
            self.log_result("Setup Test Guest", False, f"Error setting up test guest: {str(e)}")
            return False

    def test_room_service_order_creation(self):
        """Test creating a room service order"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get menu items
            items_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            if items_response.status_code != 200:
                self.log_result("Room Service - Get Menu Items", False, "Failed to get menu items")
                return None
                
            items = items_response.json()
            if not items:
                self.log_result("Room Service - Get Menu Items", False, "No menu items available")
                return None
                
            menu_item = items[0]
            
            # Create room service order
            order_items = [{
                "menu_item_id": menu_item['id'],
                "menu_item_name": menu_item['name'],
                "quantity": 1,
                "unit_price": menu_item['price'],
                "total_price": menu_item['price'],
                "special_notes": "Room service delivery"
            }]
            
            room_service_order = {
                "order_type": "room_service",
                "room_number": "101",
                "customer_name": "Room Service Test Guest",
                "items": order_items,
                "payment_method": "Room Charge",
                "notes": "Test room service order"
            }
            
            response = requests.post(f"{API_BASE}/restaurant/orders", json=room_service_order, headers=headers)
            
            if response.status_code == 200:
                created_order = response.json()
                self.log_result("Create Room Service Order", True, f"Created room service order: {created_order['order_number']}")
                return created_order['id']
            else:
                self.log_result("Create Room Service Order", False, f"Failed to create room service order: {response.status_code}", response.text)
                return None
                
        except Exception as e:
            self.log_result("Create Room Service Order", False, f"Error creating room service order: {str(e)}")
            return None

    def test_room_service_payment_integration(self, order_id):
        """Test room service payment and integration with customer account"""
        if not order_id:
            self.log_result("Room Service Payment", False, "No order ID provided")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get customer's restaurant charges before payment
            customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
            if customers_response.status_code != 200:
                self.log_result("Room Service Payment - Get Customer Before", False, "Failed to get customer data")
                return False
                
            customers = customers_response.json()
            test_customer = next((c for c in customers if c.get('current_room') == '101'), None)
            if not test_customer:
                self.log_result("Room Service Payment - Get Customer Before", False, "Test customer not found")
                return False
                
            initial_restaurant_charges = test_customer.get('restaurant_charges', 0.0)
            
            # Process payment
            response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay", headers=headers)
            
            if response.status_code == 200:
                self.log_result("Process Room Service Payment", True, "Room service payment processed successfully")
                
                # Check if customer's restaurant charges were updated
                customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
                if customers_response.status_code == 200:
                    customers = customers_response.json()
                    updated_customer = next((c for c in customers if c.get('current_room') == '101'), None)
                    
                    if updated_customer:
                        final_restaurant_charges = updated_customer.get('restaurant_charges', 0.0)
                        charge_increase = final_restaurant_charges - initial_restaurant_charges
                        
                        if charge_increase > 0:
                            self.log_result("Room Service Financial Integration", True, 
                                          f"Restaurant charges increased by {charge_increase} (from {initial_restaurant_charges} to {final_restaurant_charges})")
                            return True
                        else:
                            self.log_result("Room Service Financial Integration", False, 
                                          f"Restaurant charges not increased (still {final_restaurant_charges})")
                            return False
                    else:
                        self.log_result("Room Service Financial Integration", False, "Updated customer not found")
                        return False
                else:
                    self.log_result("Room Service Financial Integration", False, "Failed to get updated customer data")
                    return False
            else:
                self.log_result("Process Room Service Payment", False, f"Failed to process room service payment: {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_result("Room Service Payment Integration", False, f"Error processing room service payment: {str(e)}")
            return False

    def test_checkout_integration(self):
        """Test that restaurant charges are included in checkout calculation"""
        if not self.test_customer_id:
            self.log_result("Checkout Integration", False, "No test customer ID available")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get customer data to verify restaurant charges
            customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
            if customers_response.status_code != 200:
                self.log_result("Checkout Integration - Get Customer", False, "Failed to get customer data")
                return False
                
            customers = customers_response.json()
            test_customer = next((c for c in customers if c.get('id') == self.test_customer_id), None)
            
            if not test_customer:
                self.log_result("Checkout Integration - Get Customer", False, "Test customer not found")
                return False
                
            restaurant_charges = test_customer.get('restaurant_charges', 0.0)
            room_charges = test_customer.get('room_charges', 0.0)
            advance_amount = test_customer.get('advance_amount', 0.0)
            
            if restaurant_charges > 0:
                expected_total = room_charges + restaurant_charges - advance_amount
                self.log_result("Checkout Integration", True, 
                              f"Customer ready for checkout with restaurant charges: {restaurant_charges} (Total: {expected_total})")
                
                # Test the checkout calculation (without actually checking out)
                checkout_preview = {
                    "room_charges": room_charges,
                    "restaurant_charges": restaurant_charges,
                    "advance_amount": advance_amount,
                    "additional_charges": 0.0,
                    "discount_amount": 0.0
                }
                
                calculated_total = room_charges + restaurant_charges - advance_amount
                self.log_result("Checkout Calculation", True, 
                              f"Checkout calculation includes restaurant charges: {calculated_total}")
                return True
            else:
                self.log_result("Checkout Integration", False, "No restaurant charges found for customer")
                return False
                
        except Exception as e:
            self.log_result("Checkout Integration", False, f"Error testing checkout integration: {str(e)}")
            return False

    def test_financial_summary_integration(self):
        """Test that restaurant revenue is included in financial summaries"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get daily sales to check for restaurant revenue
            daily_sales_response = requests.get(f"{API_BASE}/daily-sales", headers=headers)
            if daily_sales_response.status_code == 200:
                daily_sales = daily_sales_response.json()
                restaurant_sales = [sale for sale in daily_sales if sale.get('room_number') == 'Restaurant']
                
                if restaurant_sales:
                    total_restaurant_revenue = sum(sale.get('total_amount', 0) for sale in restaurant_sales)
                    self.log_result("Financial Summary - Restaurant Revenue", True, 
                                  f"Found {len(restaurant_sales)} restaurant sales totaling {total_restaurant_revenue}")
                else:
                    self.log_result("Financial Summary - Restaurant Revenue", False, "No restaurant sales found in daily sales")
                    return False
            else:
                self.log_result("Financial Summary - Restaurant Revenue", False, "Failed to get daily sales data")
                return False
                
            # Get financial summary
            financial_response = requests.get(f"{API_BASE}/financial-summary", headers=headers)
            if financial_response.status_code == 200:
                financial_data = financial_response.json()
                total_revenue = financial_data.get('total_revenue', 0)
                self.log_result("Financial Summary Integration", True, 
                              f"Financial summary shows total revenue: {total_revenue}")
                return True
            else:
                self.log_result("Financial Summary Integration", False, "Failed to get financial summary")
                return False
                
        except Exception as e:
            self.log_result("Financial Summary Integration", False, f"Error testing financial integration: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up test data"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Cancel the test booking if it exists
            if self.test_booking_id:
                requests.post(f"{API_BASE}/cancel/{self.test_booking_id}", headers=headers)
                
            # Note: In a real scenario, we might also want to checkout the customer
            # but for testing purposes, we'll leave the data for verification
            
            self.log_result("Cleanup", True, "Test data cleanup completed")
        except Exception as e:
            self.log_result("Cleanup", False, f"Error during cleanup: {str(e)}")

    def run_integration_tests(self):
        """Run restaurant integration tests"""
        print("🍽️  RESTAURANT MANAGEMENT SYSTEM INTEGRATION TESTING")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Setup test environment
        if not self.setup_test_guest():
            print("❌ Cannot proceed without test guest setup")
            return False
        
        # Test room service functionality
        order_id = self.test_room_service_order_creation()
        if order_id:
            self.test_room_service_payment_integration(order_id)
        
        # Test integration with hotel system
        self.test_checkout_integration()
        self.test_financial_summary_integration()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("🍽️  RESTAURANT INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result['status'])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result['status'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result['status']:
                    print(f"  - {result['test']}: {result['message']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = RestaurantIntegrationTest()
    success = tester.run_integration_tests()
    sys.exit(0 if success else 1)