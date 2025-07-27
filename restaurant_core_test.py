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

class RestaurantCoreTest:
    def __init__(self):
        self.admin_token = None
        self.restaurant_token = None
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

    def create_restaurant_manager(self):
        """Create restaurant manager user"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            user_data = {
                "username": "restaurant",
                "password": "restaurant123",
                "full_name": "Restaurant Manager",
                "role": "Restaurant Manager",
                "email": "restaurant@hotel.com"
            }
            
            response = requests.post(f"{API_BASE}/users", json=user_data, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Create Restaurant Manager", True, "Restaurant manager user created")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                self.log_result("Create Restaurant Manager", True, "Restaurant manager user already exists")
                return True
            else:
                self.log_result("Create Restaurant Manager", False, f"Failed to create restaurant manager: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Create Restaurant Manager", False, f"Error creating restaurant manager: {str(e)}")
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

    def test_menu_categories_basic(self):
        """Test basic menu categories functionality"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET categories
        try:
            response = requests.get(f"{API_BASE}/restaurant/categories", headers=headers)
            if response.status_code == 200:
                categories = response.json()
                self.log_result("Get Menu Categories", True, f"Retrieved {len(categories)} categories")
                return True
            else:
                self.log_result("Get Menu Categories", False, f"Failed to get categories: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Menu Categories", False, f"Error getting categories: {str(e)}")
            return False

    def test_menu_items_basic(self):
        """Test basic menu items functionality"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET menu items
        try:
            response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            if response.status_code == 200:
                items = response.json()
                self.log_result("Get Menu Items", True, f"Retrieved {len(items)} menu items")
                return True
            else:
                self.log_result("Get Menu Items", False, f"Failed to get menu items: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Menu Items", False, f"Error getting menu items: {str(e)}")
            return False

    def test_restaurant_tables_basic(self):
        """Test basic restaurant tables functionality"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET tables
        try:
            response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
            if response.status_code == 200:
                tables = response.json()
                self.log_result("Get Restaurant Tables", True, f"Retrieved {len(tables)} tables")
                return True
            else:
                self.log_result("Get Restaurant Tables", False, f"Failed to get tables: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Restaurant Tables", False, f"Error getting tables: {str(e)}")
            return False

    def test_restaurant_staff_basic(self):
        """Test basic restaurant staff functionality"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET staff
        try:
            response = requests.get(f"{API_BASE}/restaurant/staff", headers=headers)
            if response.status_code == 200:
                staff = response.json()
                self.log_result("Get Restaurant Staff", True, f"Retrieved {len(staff)} staff members")
                return True
            else:
                self.log_result("Get Restaurant Staff", False, f"Failed to get staff: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Restaurant Staff", False, f"Error getting staff: {str(e)}")
            return False

    def test_restaurant_orders_basic(self):
        """Test basic restaurant orders functionality"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test GET orders
        try:
            response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
            if response.status_code == 200:
                orders = response.json()
                self.log_result("Get Restaurant Orders", True, f"Retrieved {len(orders)} orders")
                return True
            else:
                self.log_result("Get Restaurant Orders", False, f"Failed to get orders: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Get Restaurant Orders", False, f"Error getting orders: {str(e)}")
            return False

    def test_create_menu_category(self):
        """Test creating a menu category"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            new_category = {
                "name": "Test Appetizers",
                "description": "Test appetizers category",
                "display_order": 1
            }
            response = requests.post(f"{API_BASE}/restaurant/categories", json=new_category, headers=headers)
            
            if response.status_code == 200:
                created_category = response.json()
                self.log_result("Create Menu Category", True, f"Created category: {created_category['name']}")
                return created_category['id']
            else:
                self.log_result("Create Menu Category", False, f"Failed to create category: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Create Menu Category", False, f"Error creating category: {str(e)}")
            return None

    def test_create_menu_item(self, category_id):
        """Test creating a menu item"""
        if not category_id:
            self.log_result("Create Menu Item", False, "No category ID provided")
            return None
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            new_item = {
                "name": "Test Spring Rolls",
                "description": "Crispy test spring rolls",
                "price": 850.0,
                "category_id": category_id,
                "is_vegetarian": True,
                "is_spicy": False,
                "prep_time": 15
            }
            response = requests.post(f"{API_BASE}/restaurant/menu-items", json=new_item, headers=headers)
            
            if response.status_code == 200:
                created_item = response.json()
                self.log_result("Create Menu Item", True, f"Created menu item: {created_item['name']}")
                return created_item['id']
            else:
                self.log_result("Create Menu Item", False, f"Failed to create menu item: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Create Menu Item", False, f"Error creating menu item: {str(e)}")
            return None

    def test_create_restaurant_table(self):
        """Test creating a restaurant table"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            new_table = {
                "table_number": "T01",
                "capacity": 4,
                "position_x": 100,
                "position_y": 100
            }
            response = requests.post(f"{API_BASE}/restaurant/tables", json=new_table, headers=headers)
            
            if response.status_code == 200:
                created_table = response.json()
                self.log_result("Create Restaurant Table", True, f"Created table: {created_table['table_number']}")
                return created_table['id']
            else:
                self.log_result("Create Restaurant Table", False, f"Failed to create table: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Create Restaurant Table", False, f"Error creating table: {str(e)}")
            return None

    def test_create_restaurant_staff(self):
        """Test creating restaurant staff"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            new_staff = {
                "name": "John Waiter",
                "role": "Waiter",
                "phone": "+94771234567"
            }
            response = requests.post(f"{API_BASE}/restaurant/staff", json=new_staff, headers=headers)
            
            if response.status_code == 200:
                created_staff = response.json()
                self.log_result("Create Restaurant Staff", True, f"Created staff: {created_staff['name']}")
                return created_staff['id']
            else:
                self.log_result("Create Restaurant Staff", False, f"Failed to create staff: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Create Restaurant Staff", False, f"Error creating staff: {str(e)}")
            return None

    def test_create_table_order(self, table_id, menu_item_id, staff_id):
        """Test creating a table order"""
        if not all([table_id, menu_item_id]):
            self.log_result("Create Table Order", False, "Missing required IDs for order creation")
            return None
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            order_items = [{
                "menu_item_id": menu_item_id,
                "menu_item_name": "Test Spring Rolls",
                "quantity": 2,
                "unit_price": 850.0,
                "total_price": 1700.0,
                "special_notes": "Extra crispy"
            }]
            
            new_order = {
                "order_type": "table",
                "table_id": table_id,
                "customer_name": "Test Customer",
                "items": order_items,
                "payment_method": "Cash",
                "waiter_id": staff_id,
                "notes": "Test table order"
            }
            
            response = requests.post(f"{API_BASE}/restaurant/orders", json=new_order, headers=headers)
            
            if response.status_code == 200:
                created_order = response.json()
                self.log_result("Create Table Order", True, f"Created table order: {created_order['order_number']}")
                return created_order['id']
            else:
                self.log_result("Create Table Order", False, f"Failed to create table order: {response.status_code}")
                return None
        except Exception as e:
            self.log_result("Create Table Order", False, f"Error creating table order: {str(e)}")
            return None

    def test_process_table_order_payment(self, order_id):
        """Test processing table order payment"""
        if not order_id:
            self.log_result("Process Table Order Payment", False, "No order ID provided")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay", headers=headers)
            
            if response.status_code == 200:
                self.log_result("Process Table Order Payment", True, "Table order payment processed successfully")
                
                # Check if daily sales record was created
                daily_sales_response = requests.get(f"{API_BASE}/daily-sales", headers=headers)
                if daily_sales_response.status_code == 200:
                    daily_sales = daily_sales_response.json()
                    restaurant_sales = [sale for sale in daily_sales if sale.get('room_number') == 'Restaurant']
                    if restaurant_sales:
                        self.log_result("Table Order Financial Integration", True, "Table order added to daily sales")
                    else:
                        self.log_result("Table Order Financial Integration", False, "Table order not found in daily sales")
                
                return True
            else:
                self.log_result("Process Table Order Payment", False, f"Failed to process payment: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Process Table Order Payment", False, f"Error processing payment: {str(e)}")
            return False

    def test_restaurant_manager_permissions(self):
        """Test restaurant manager permissions"""
        if not self.restaurant_token:
            self.log_result("Restaurant Manager Permissions", False, "Restaurant manager not authenticated")
            return False
            
        headers = {"Authorization": f"Bearer {self.restaurant_token}"}
        
        # Test access to restaurant endpoints
        endpoints = [
            ("/restaurant/categories", "Categories"),
            ("/restaurant/menu-items", "Menu Items"),
            ("/restaurant/tables", "Tables"),
            ("/restaurant/staff", "Staff"),
            ("/restaurant/orders", "Orders")
        ]
        
        all_passed = True
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
                if response.status_code == 200:
                    self.log_result(f"Restaurant Manager - {name} Access", True, f"Can access {name.lower()}")
                else:
                    self.log_result(f"Restaurant Manager - {name} Access", False, f"Cannot access {name.lower()}: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result(f"Restaurant Manager - {name} Access", False, f"Error accessing {name.lower()}: {str(e)}")
                all_passed = False
        
        return all_passed

    def run_core_tests(self):
        """Run core restaurant management tests"""
        print("🍽️  RESTAURANT MANAGEMENT SYSTEM CORE TESTING")
        print("=" * 60)
        
        # Authentication
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Create restaurant manager user
        self.create_restaurant_manager()
        self.authenticate_restaurant_manager()
        
        # Test basic endpoint access
        self.test_menu_categories_basic()
        self.test_menu_items_basic()
        self.test_restaurant_tables_basic()
        self.test_restaurant_staff_basic()
        self.test_restaurant_orders_basic()
        
        # Test CRUD operations
        category_id = self.test_create_menu_category()
        menu_item_id = self.test_create_menu_item(category_id)
        table_id = self.test_create_restaurant_table()
        staff_id = self.test_create_restaurant_staff()
        
        # Test order creation and payment
        order_id = self.test_create_table_order(table_id, menu_item_id, staff_id)
        self.test_process_table_order_payment(order_id)
        
        # Test restaurant manager permissions
        if self.restaurant_token:
            self.test_restaurant_manager_permissions()
        
        # Summary
        print("\n" + "=" * 60)
        print("🍽️  RESTAURANT MANAGEMENT CORE TEST SUMMARY")
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
    tester = RestaurantCoreTest()
    success = tester.run_core_tests()
    sys.exit(0 if success else 1)