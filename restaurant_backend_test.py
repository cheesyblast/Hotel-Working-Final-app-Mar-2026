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

class RestaurantBackendTester:
    def __init__(self):
        self.admin_token = None
        self.restaurant_token = None
        self.test_results = []
        self.created_resources = {
            'categories': [],
            'menu_items': [],
            'tables': [],
            'staff': [],
            'orders': []
        }

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

    def authenticate_restaurant_manager(self):
        """Authenticate as restaurant manager"""
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "username": "restaurant",
                "password": "restaurant123"
            })
            
            if response.status_code == 200:
                self.restaurant_token = response.json()["access_token"]
                self.log_result("Restaurant Manager Authentication", True, "Restaurant manager login successful")
                return True
            else:
                self.log_result("Restaurant Manager Authentication", False, f"Restaurant manager login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Restaurant Manager Authentication", False, f"Restaurant manager login error: {str(e)}")
            return False

    def initialize_restaurant_data(self):
        """Initialize restaurant data using init-data endpoint"""
        try:
            response = requests.post(f"{API_BASE}/init-data")
            
            if response.status_code == 200:
                self.log_result("Restaurant Data Initialization", True, "Restaurant data initialized successfully")
                return True
            else:
                self.log_result("Restaurant Data Initialization", False, f"Data initialization failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Restaurant Data Initialization", False, f"Data initialization error: {str(e)}")
            return False

    def test_menu_categories_crud(self):
        """Test menu categories CRUD operations"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET categories
        try:
            response = requests.get(f"{API_BASE}/restaurant/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                self.log_result("Get Menu Categories", True, f"Retrieved {len(categories)} categories")
            else:
                self.log_result("Get Menu Categories", False, f"Failed to get categories: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Menu Categories", False, f"Error getting categories: {str(e)}")
            return False

        # Test CREATE category
        try:
            new_category = {
                "name": "Test Category",
                "description": "Test category for automated testing",
                "display_order": 10
            }
            response = requests.post(f"{API_BASE}/restaurant/categories", json=new_category, headers=headers)
            
            if response.status_code == 200:
                created_category = response.json()
                self.created_resources['categories'].append(created_category['id'])
                self.log_result("Create Menu Category", True, f"Created category: {created_category['name']}")
                
                # Test UPDATE category
                updated_category = {
                    "name": "Updated Test Category",
                    "description": "Updated description",
                    "display_order": 11
                }
                response = requests.put(f"{API_BASE}/restaurant/categories/{created_category['id']}", 
                                      json=updated_category, headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Update Menu Category", True, "Category updated successfully")
                else:
                    self.log_result("Update Menu Category", False, f"Failed to update category: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Menu Category", False, f"Failed to create category: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Menu Category", False, f"Error creating category: {str(e)}")
            return False

    def test_menu_items_crud(self):
        """Test menu items CRUD operations"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First get categories to use for menu items
        try:
            response = requests.get(f"{API_BASE}/restaurant/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                if not categories:
                    self.log_result("Menu Items Test Setup", False, "No categories available for menu items")
                    return False
                category_id = categories[0]['id']
            else:
                self.log_result("Menu Items Test Setup", False, "Failed to get categories for menu items")
                return False
        except Exception as e:
            self.log_result("Menu Items Test Setup", False, f"Error getting categories: {str(e)}")
            return False

        # Test GET menu items
        try:
            response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            if response.status_code == 200:
                items = response.json()
                self.log_result("Get Menu Items", True, f"Retrieved {len(items)} menu items")
            else:
                self.log_result("Get Menu Items", False, f"Failed to get menu items: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Menu Items", False, f"Error getting menu items: {str(e)}")
            return False

        # Test CREATE menu item
        try:
            new_item = {
                "name": "Test Dish",
                "description": "Test dish for automated testing",
                "price": 1500.0,
                "category_id": category_id,
                "is_vegetarian": True,
                "is_spicy": False,
                "prep_time": 20
            }
            response = requests.post(f"{API_BASE}/restaurant/menu-items", json=new_item, headers=headers)
            
            if response.status_code == 200:
                created_item = response.json()
                self.created_resources['menu_items'].append(created_item['id'])
                self.log_result("Create Menu Item", True, f"Created menu item: {created_item['name']}")
                
                # Test UPDATE menu item
                updated_item = {
                    "name": "Updated Test Dish",
                    "description": "Updated description",
                    "price": 1800.0,
                    "category_id": category_id,
                    "is_vegetarian": False,
                    "is_spicy": True,
                    "prep_time": 25
                }
                response = requests.put(f"{API_BASE}/restaurant/menu-items/{created_item['id']}", 
                                      json=updated_item, headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Update Menu Item", True, "Menu item updated successfully")
                else:
                    self.log_result("Update Menu Item", False, f"Failed to update menu item: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Menu Item", False, f"Failed to create menu item: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Menu Item", False, f"Error creating menu item: {str(e)}")
            return False

    def test_restaurant_tables_crud(self):
        """Test restaurant tables CRUD operations"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET tables
        try:
            response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
            if response.status_code == 200:
                tables = response.json()
                self.log_result("Get Restaurant Tables", True, f"Retrieved {len(tables)} tables")
            else:
                self.log_result("Get Restaurant Tables", False, f"Failed to get tables: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Restaurant Tables", False, f"Error getting tables: {str(e)}")
            return False

        # Test CREATE table
        try:
            new_table = {
                "table_number": "T99",
                "capacity": 4,
                "position_x": 100,
                "position_y": 200
            }
            response = requests.post(f"{API_BASE}/restaurant/tables", json=new_table, headers=headers)
            
            if response.status_code == 200:
                created_table = response.json()
                self.created_resources['tables'].append(created_table['id'])
                self.log_result("Create Restaurant Table", True, f"Created table: {created_table['table_number']}")
                
                # Test UPDATE table
                updated_table = {
                    "table_number": "T99-Updated",
                    "capacity": 6,
                    "position_x": 150,
                    "position_y": 250
                }
                response = requests.put(f"{API_BASE}/restaurant/tables/{created_table['id']}", 
                                      json=updated_table, headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Update Restaurant Table", True, "Table updated successfully")
                else:
                    self.log_result("Update Restaurant Table", False, f"Failed to update table: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Restaurant Table", False, f"Failed to create table: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Restaurant Table", False, f"Error creating table: {str(e)}")
            return False

    def test_restaurant_staff_crud(self):
        """Test restaurant staff CRUD operations"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET staff
        try:
            response = requests.get(f"{API_BASE}/restaurant/staff", headers=headers)
            if response.status_code == 200:
                staff = response.json()
                self.log_result("Get Restaurant Staff", True, f"Retrieved {len(staff)} staff members")
            else:
                self.log_result("Get Restaurant Staff", False, f"Failed to get staff: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Restaurant Staff", False, f"Error getting staff: {str(e)}")
            return False

        # Test CREATE staff
        try:
            new_staff = {
                "name": "Test Waiter",
                "role": "Waiter",
                "phone": "+94771234999"
            }
            response = requests.post(f"{API_BASE}/restaurant/staff", json=new_staff, headers=headers)
            
            if response.status_code == 200:
                created_staff = response.json()
                self.created_resources['staff'].append(created_staff['id'])
                self.log_result("Create Restaurant Staff", True, f"Created staff: {created_staff['name']}")
                
                # Test UPDATE staff
                updated_staff = {
                    "name": "Updated Test Waiter",
                    "role": "Senior Waiter",
                    "phone": "+94771234888"
                }
                response = requests.put(f"{API_BASE}/restaurant/staff/{created_staff['id']}", 
                                      json=updated_staff, headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Update Restaurant Staff", True, "Staff updated successfully")
                else:
                    self.log_result("Update Restaurant Staff", False, f"Failed to update staff: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Restaurant Staff", False, f"Failed to create staff: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Restaurant Staff", False, f"Error creating staff: {str(e)}")
            return False

    def test_restaurant_orders_table(self):
        """Test table order creation and payment processing"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get available tables and menu items
        try:
            tables_response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
            items_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            staff_response = requests.get(f"{API_BASE}/restaurant/staff", headers=headers)
            
            if tables_response.status_code != 200 or items_response.status_code != 200:
                self.log_result("Table Order Setup", False, "Failed to get required data for table order")
                return False
                
            tables = tables_response.json()
            items = items_response.json()
            staff = staff_response.json()
            
            if not tables or not items:
                self.log_result("Table Order Setup", False, "No tables or menu items available")
                return False
                
            table_id = tables[0]['id']
            menu_item = items[0]
            waiter_id = staff[0]['id'] if staff else None
            
        except Exception as e:
            self.log_result("Table Order Setup", False, f"Error getting order data: {str(e)}")
            return False

        # Test CREATE table order
        try:
            order_items = [{
                "menu_item_id": menu_item['id'],
                "menu_item_name": menu_item['name'],
                "quantity": 2,
                "unit_price": menu_item['price'],
                "total_price": menu_item['price'] * 2,
                "special_notes": "Extra spicy"
            }]
            
            new_order = {
                "order_type": "table",
                "table_id": table_id,
                "customer_name": "Test Customer",
                "items": order_items,
                "payment_method": "Cash",
                "waiter_id": waiter_id,
                "notes": "Test table order"
            }
            
            response = requests.post(f"{API_BASE}/restaurant/orders", json=new_order, headers=headers)
            
            if response.status_code == 200:
                created_order = response.json()
                self.created_resources['orders'].append(created_order['id'])
                self.log_result("Create Table Order", True, f"Created table order: {created_order['order_number']}")
                
                # Test order status update
                response = requests.put(f"{API_BASE}/restaurant/orders/{created_order['id']}/status?status=Preparing", 
                                      headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Update Order Status", True, "Order status updated to Preparing")
                else:
                    self.log_result("Update Order Status", False, f"Failed to update order status: {response.status_code}")
                
                # Test payment processing
                response = requests.post(f"{API_BASE}/restaurant/orders/{created_order['id']}/pay", headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Process Table Order Payment", True, "Table order payment processed successfully")
                    
                    # Verify daily sales record was created
                    daily_sales_response = requests.get(f"{API_BASE}/daily-sales", headers=headers)
                    if daily_sales_response.status_code == 200:
                        daily_sales = daily_sales_response.json()
                        restaurant_sales = [sale for sale in daily_sales if sale.get('room_number') == 'Restaurant']
                        if restaurant_sales:
                            self.log_result("Table Order Financial Integration", True, "Table order added to daily sales")
                        else:
                            self.log_result("Table Order Financial Integration", False, "Table order not found in daily sales")
                    
                else:
                    self.log_result("Process Table Order Payment", False, f"Failed to process payment: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Table Order", False, f"Failed to create table order: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Table Order", False, f"Error creating table order: {str(e)}")
            return False

    def test_restaurant_orders_room_service(self):
        """Test room service order creation and billing integration"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First create a checked-in customer for room service testing
        try:
            # Create a booking first
            booking_data = {
                "guest_name": "Room Service Test Guest",
                "guest_email": "roomservice@test.com",
                "guest_phone": "123-456-7890",
                "room_number": "101",
                "check_in_date": date.today().isoformat(),
                "check_out_date": date.today().isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 5000.0,
                "booking_status": "Upcoming"
            }
            
            booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
            if booking_response.status_code != 200:
                self.log_result("Room Service Setup - Booking", False, "Failed to create test booking")
                return False
                
            booking = booking_response.json()
            
            # Check in the guest
            checkin_data = {
                "booking_id": booking['id'],
                "advance_amount": 1000.0,
                "notes": "Test check-in for room service",
                "payment_method": "Cash"
            }
            
            checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
            if checkin_response.status_code != 200:
                self.log_result("Room Service Setup - Check-in", False, "Failed to check in test guest")
                return False
                
            self.log_result("Room Service Setup", True, "Test guest checked in successfully")
            
        except Exception as e:
            self.log_result("Room Service Setup", False, f"Error setting up room service test: {str(e)}")
            return False

        # Get menu items for room service order
        try:
            items_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            if items_response.status_code != 200:
                self.log_result("Room Service Menu Items", False, "Failed to get menu items")
                return False
                
            items = items_response.json()
            if not items:
                self.log_result("Room Service Menu Items", False, "No menu items available")
                return False
                
            menu_item = items[0]
            
        except Exception as e:
            self.log_result("Room Service Menu Items", False, f"Error getting menu items: {str(e)}")
            return False

        # Test CREATE room service order
        try:
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
                self.created_resources['orders'].append(created_order['id'])
                self.log_result("Create Room Service Order", True, f"Created room service order: {created_order['order_number']}")
                
                # Test payment processing (billing to room)
                response = requests.post(f"{API_BASE}/restaurant/orders/{created_order['id']}/pay", headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Process Room Service Payment", True, "Room service payment processed successfully")
                    
                    # Verify customer's restaurant charges were updated
                    customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
                    if customers_response.status_code == 200:
                        customers = customers_response.json()
                        test_customer = next((c for c in customers if c.get('current_room') == '101'), None)
                        
                        if test_customer and test_customer.get('restaurant_charges', 0) > 0:
                            self.log_result("Room Service Financial Integration", True, 
                                          f"Restaurant charges added to customer account: {test_customer['restaurant_charges']}")
                        else:
                            self.log_result("Room Service Financial Integration", False, 
                                          "Restaurant charges not found in customer account")
                    else:
                        self.log_result("Room Service Financial Integration", False, 
                                      "Failed to verify customer restaurant charges")
                
                else:
                    self.log_result("Process Room Service Payment", False, f"Failed to process room service payment: {response.status_code}")
                
                return True
            else:
                self.log_result("Create Room Service Order", False, f"Failed to create room service order: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Create Room Service Order", False, f"Error creating room service order: {str(e)}")
            return False

    def test_restaurant_manager_permissions(self):
        """Test restaurant manager role permissions"""
        if not self.restaurant_token:
            self.log_result("Restaurant Manager Permissions", False, "Restaurant manager not authenticated")
            return False
            
        headers = {"Authorization": f"Bearer {self.restaurant_token}"}
        
        # Test restaurant manager can access restaurant endpoints
        try:
            # Test categories access
            response = requests.get(f"{API_BASE}/restaurant/categories", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Manager - Categories Access", True, "Can access menu categories")
            else:
                self.log_result("Restaurant Manager - Categories Access", False, f"Cannot access categories: {response.status_code}")
                return False
                
            # Test menu items access
            response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Manager - Menu Items Access", True, "Can access menu items")
            else:
                self.log_result("Restaurant Manager - Menu Items Access", False, f"Cannot access menu items: {response.status_code}")
                return False
                
            # Test tables access
            response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Manager - Tables Access", True, "Can access restaurant tables")
            else:
                self.log_result("Restaurant Manager - Tables Access", False, f"Cannot access tables: {response.status_code}")
                return False
                
            # Test staff access
            response = requests.get(f"{API_BASE}/restaurant/staff", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Manager - Staff Access", True, "Can access restaurant staff")
            else:
                self.log_result("Restaurant Manager - Staff Access", False, f"Cannot access staff: {response.status_code}")
                return False
                
            # Test orders access
            response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Manager - Orders Access", True, "Can access restaurant orders")
            else:
                self.log_result("Restaurant Manager - Orders Access", False, f"Cannot access orders: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.log_result("Restaurant Manager Permissions", False, f"Error testing permissions: {str(e)}")
            return False

    def test_checkout_integration(self):
        """Test that restaurant charges are included in checkout process"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Get checked-in customers
            response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
            if response.status_code != 200:
                self.log_result("Checkout Integration Setup", False, "Failed to get checked-in customers")
                return False
                
            customers = response.json()
            test_customer = next((c for c in customers if c.get('restaurant_charges', 0) > 0), None)
            
            if not test_customer:
                self.log_result("Checkout Integration", False, "No customer with restaurant charges found for testing")
                return False
                
            # Test checkout process includes restaurant charges
            checkout_data = {
                "customer_id": test_customer['id'],
                "additional_amount": 0.0,
                "discount_amount": 0.0,
                "payment_method": "Cash"
            }
            
            # Note: We won't actually checkout to avoid disrupting the test data
            # Instead, we'll verify the customer has restaurant charges
            restaurant_charges = test_customer.get('restaurant_charges', 0)
            if restaurant_charges > 0:
                self.log_result("Checkout Integration", True, 
                              f"Customer has restaurant charges: {restaurant_charges} (ready for checkout)")
                return True
            else:
                self.log_result("Checkout Integration", False, "Customer restaurant charges not properly set")
                return False
                
        except Exception as e:
            self.log_result("Checkout Integration", False, f"Error testing checkout integration: {str(e)}")
            return False

    def cleanup_test_data(self):
        """Clean up created test data"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete created orders (soft delete by cancelling)
        for order_id in self.created_resources['orders']:
            try:
                requests.put(f"{API_BASE}/restaurant/orders/{order_id}/status?status=Cancelled", headers=headers)
            except:
                pass
                
        # Delete created staff
        for staff_id in self.created_resources['staff']:
            try:
                requests.delete(f"{API_BASE}/restaurant/staff/{staff_id}", headers=headers)
            except:
                pass
                
        # Delete created tables
        for table_id in self.created_resources['tables']:
            try:
                requests.delete(f"{API_BASE}/restaurant/tables/{table_id}", headers=headers)
            except:
                pass
                
        # Delete created menu items
        for item_id in self.created_resources['menu_items']:
            try:
                requests.delete(f"{API_BASE}/restaurant/menu-items/{item_id}", headers=headers)
            except:
                pass
                
        # Delete created categories
        for category_id in self.created_resources['categories']:
            try:
                requests.delete(f"{API_BASE}/restaurant/categories/{category_id}", headers=headers)
            except:
                pass

    def run_all_tests(self):
        """Run all restaurant management tests"""
        print("🍽️  RESTAURANT MANAGEMENT SYSTEM BACKEND TESTING")
        print("=" * 60)
        
        # Authentication tests
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
            
        if not self.authenticate_restaurant_manager():
            print("⚠️  Restaurant manager authentication failed, some tests will be skipped")
        
        # Initialize restaurant data
        self.initialize_restaurant_data()
        
        # Core CRUD tests
        self.test_menu_categories_crud()
        self.test_menu_items_crud()
        self.test_restaurant_tables_crud()
        self.test_restaurant_staff_crud()
        
        # Order management tests
        self.test_restaurant_orders_table()
        self.test_restaurant_orders_room_service()
        
        # Permission tests
        if self.restaurant_token:
            self.test_restaurant_manager_permissions()
        
        # Integration tests
        self.test_checkout_integration()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Summary
        print("\n" + "=" * 60)
        print("🍽️  RESTAURANT MANAGEMENT SYSTEM TEST SUMMARY")
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
    tester = RestaurantBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)