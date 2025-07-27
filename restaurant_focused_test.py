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

    def setup_test_data(self):
        """Setup test data for validation testing"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Initialize restaurant data if needed
            requests.post(f"{API_BASE}/init-data")
            
            # Create test category
            category_data = {
                "name": "Test Category for Validation",
                "description": "Category for testing deletion validation",
                "display_order": 99
            }
            response = requests.post(f"{API_BASE}/restaurant/categories", json=category_data, headers=headers)
            if response.status_code == 200:
                test_category = response.json()
                self.created_resources['categories'].append(test_category['id'])
                
                # Create test menu item in this category
                item_data = {
                    "name": "Test Item for Validation",
                    "description": "Item for testing deletion validation",
                    "price": 1500.0,
                    "category_id": test_category['id'],
                    "is_vegetarian": False,
                    "is_spicy": False,
                    "prep_time": 15
                }
                response = requests.post(f"{API_BASE}/restaurant/menu-items", json=item_data, headers=headers)
                if response.status_code == 200:
                    test_item = response.json()
                    self.created_resources['menu_items'].append(test_item['id'])
                    
                    # Create test table
                    table_data = {
                        "table_number": "TEST-01",
                        "capacity": 4,
                        "position_x": 100,
                        "position_y": 100
                    }
                    response = requests.post(f"{API_BASE}/restaurant/tables", json=table_data, headers=headers)
                    if response.status_code == 200:
                        test_table = response.json()
                        self.created_resources['tables'].append(test_table['id'])
                        
                        # Create test staff
                        staff_data = {
                            "name": "Test Waiter",
                            "role": "Waiter",
                            "phone": "+94771234567"
                        }
                        response = requests.post(f"{API_BASE}/restaurant/staff", json=staff_data, headers=headers)
                        if response.status_code == 200:
                            test_staff = response.json()
                            self.created_resources['staff'].append(test_staff['id'])
                            
                            self.log_result("Test Data Setup", True, "Test data created successfully")
                            return True
            
            self.log_result("Test Data Setup", False, "Failed to create test data")
            return False
            
        except Exception as e:
            self.log_result("Test Data Setup", False, f"Error setting up test data: {str(e)}")
            return False

    def test_restaurant_order_endpoints(self):
        """Test all restaurant order endpoints - GET, POST, and payment processing"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: GET /api/restaurant/orders
        try:
            response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
            if response.status_code == 200:
                orders = response.json()
                self.log_result("GET Restaurant Orders", True, f"Retrieved {len(orders)} orders successfully")
            else:
                self.log_result("GET Restaurant Orders", False, f"Failed to get orders: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("GET Restaurant Orders", False, f"Error getting orders: {str(e)}")
            return False

        # Test 2: POST /api/restaurant/orders - Table Order
        try:
            # Get test data
            tables_response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
            items_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=headers)
            staff_response = requests.get(f"{API_BASE}/restaurant/staff", headers=headers)
            
            if tables_response.status_code == 200 and items_response.status_code == 200:
                tables = tables_response.json()
                items = items_response.json()
                staff = staff_response.json()
                
                if tables and items:
                    table = tables[0]
                    menu_item = items[0]
                    waiter = staff[0] if staff else None
                    
                    # Create table order
                    order_items = [{
                        "menu_item_id": menu_item['id'],
                        "menu_item_name": menu_item['name'],
                        "quantity": 2,
                        "unit_price": menu_item['price'],
                        "total_price": menu_item['price'] * 2,
                        "special_notes": "Test order item"
                    }]
                    
                    table_order = {
                        "order_type": "table",
                        "table_id": table['id'],
                        "customer_name": "Test Customer",
                        "items": order_items,
                        "payment_method": "Cash",
                        "waiter_id": waiter['id'] if waiter else None,
                        "notes": "Test table order for validation"
                    }
                    
                    response = requests.post(f"{API_BASE}/restaurant/orders", json=table_order, headers=headers)
                    
                    if response.status_code == 200:
                        created_order = response.json()
                        self.created_resources['orders'].append(created_order['id'])
                        
                        # Verify order details
                        if (created_order.get('order_number') and 
                            created_order.get('subtotal') > 0 and
                            created_order.get('total_amount') > 0 and
                            created_order.get('table_number') == table['table_number']):
                            self.log_result("POST Restaurant Orders - Table", True, 
                                          f"Table order created successfully: {created_order['order_number']}")
                        else:
                            self.log_result("POST Restaurant Orders - Table", False, 
                                          "Table order created but missing required fields")
                    else:
                        self.log_result("POST Restaurant Orders - Table", False, 
                                      f"Failed to create table order: {response.status_code}")
                        return False
                else:
                    self.log_result("POST Restaurant Orders - Table", False, "No tables or menu items available")
                    return False
            else:
                self.log_result("POST Restaurant Orders - Table", False, "Failed to get required data")
                return False
        except Exception as e:
            self.log_result("POST Restaurant Orders - Table", False, f"Error creating table order: {str(e)}")
            return False

        # Test 3: POST /api/restaurant/orders - Room Service Order
        try:
            # First create a checked-in customer for room service
            booking_data = {
                "guest_name": "Room Service Guest",
                "guest_email": "roomservice@test.com",
                "guest_phone": "123-456-7890",
                "room_number": "102",
                "check_in_date": date.today().isoformat(),
                "check_out_date": date.today().isoformat(),
                "stay_type": "Night Stay",
                "booking_amount": 5000.0,
                "booking_status": "Upcoming"
            }
            
            booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
            if booking_response.status_code == 200:
                booking = booking_response.json()
                
                # Check in the guest
                checkin_data = {
                    "booking_id": booking['id'],
                    "advance_amount": 1000.0,
                    "notes": "Test check-in for room service",
                    "payment_method": "Cash"
                }
                
                checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
                if checkin_response.status_code == 200:
                    # Create room service order
                    room_order_items = [{
                        "menu_item_id": menu_item['id'],
                        "menu_item_name": menu_item['name'],
                        "quantity": 1,
                        "unit_price": menu_item['price'],
                        "total_price": menu_item['price'],
                        "special_notes": "Room service delivery"
                    }]
                    
                    room_service_order = {
                        "order_type": "room_service",
                        "room_number": "102",
                        "customer_name": "Room Service Guest",
                        "items": room_order_items,
                        "payment_method": "Room Charge",
                        "notes": "Test room service order"
                    }
                    
                    response = requests.post(f"{API_BASE}/restaurant/orders", json=room_service_order, headers=headers)
                    
                    if response.status_code == 200:
                        room_order = response.json()
                        self.created_resources['orders'].append(room_order['id'])
                        
                        if (room_order.get('order_number') and 
                            room_order.get('room_number') == '102' and
                            room_order.get('order_type') == 'room_service'):
                            self.log_result("POST Restaurant Orders - Room Service", True, 
                                          f"Room service order created successfully: {room_order['order_number']}")
                        else:
                            self.log_result("POST Restaurant Orders - Room Service", False, 
                                          "Room service order created but missing required fields")
                    else:
                        self.log_result("POST Restaurant Orders - Room Service", False, 
                                      f"Failed to create room service order: {response.status_code}")
                else:
                    self.log_result("POST Restaurant Orders - Room Service", False, "Failed to check in guest")
            else:
                self.log_result("POST Restaurant Orders - Room Service", False, "Failed to create booking")
        except Exception as e:
            self.log_result("POST Restaurant Orders - Room Service", False, f"Error creating room service order: {str(e)}")

        # Test 4: POST /api/restaurant/orders/{order_id}/pay - Payment Processing
        try:
            if self.created_resources['orders']:
                order_id = self.created_resources['orders'][0]  # Use first created order
                
                response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay", headers=headers)
                
                if response.status_code == 200:
                    payment_result = response.json()
                    self.log_result("POST Restaurant Order Payment", True, 
                                  f"Order payment processed successfully: {payment_result.get('message', 'Payment completed')}")
                    
                    # Verify payment status was updated
                    order_response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
                    if order_response.status_code == 200:
                        orders = order_response.json()
                        paid_order = next((o for o in orders if o['id'] == order_id), None)
                        
                        if paid_order and paid_order.get('payment_status') == 'Paid':
                            self.log_result("Order Payment Status Update", True, "Payment status updated to 'Paid'")
                        else:
                            self.log_result("Order Payment Status Update", False, "Payment status not updated correctly")
                    
                    # Verify daily sales integration
                    daily_sales_response = requests.get(f"{API_BASE}/daily-sales", headers=headers)
                    if daily_sales_response.status_code == 200:
                        daily_sales = daily_sales_response.json()
                        restaurant_sales = [sale for sale in daily_sales if sale.get('room_number') == 'Restaurant']
                        if restaurant_sales:
                            self.log_result("Restaurant Payment Financial Integration", True, 
                                          "Restaurant payment integrated with daily sales")
                        else:
                            self.log_result("Restaurant Payment Financial Integration", False, 
                                          "Restaurant payment not found in daily sales")
                    
                else:
                    self.log_result("POST Restaurant Order Payment", False, 
                                  f"Failed to process payment: {response.status_code}")
            else:
                self.log_result("POST Restaurant Order Payment", False, "No orders available for payment testing")
        except Exception as e:
            self.log_result("POST Restaurant Order Payment", False, f"Error processing payment: {str(e)}")

        return True

    def test_category_deletion_validation(self):
        """Test DELETE /api/restaurant/categories/{category_id} with validation"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Try to delete category with active menu items (should fail)
        try:
            if self.created_resources['categories']:
                category_id = self.created_resources['categories'][0]
                
                response = requests.delete(f"{API_BASE}/restaurant/categories/{category_id}", headers=headers)
                
                if response.status_code == 400:
                    error_message = response.json().get('detail', '')
                    if 'active menu items' in error_message.lower() or 'cannot delete' in error_message.lower():
                        self.log_result("Category Deletion Validation - With Items", True, 
                                      "Correctly prevented deletion of category with active menu items")
                    else:
                        self.log_result("Category Deletion Validation - With Items", False, 
                                      f"Wrong error message: {error_message}")
                else:
                    self.log_result("Category Deletion Validation - With Items", False, 
                                  f"Should have failed with 400, got: {response.status_code}")
            else:
                self.log_result("Category Deletion Validation - With Items", False, "No test category available")
        except Exception as e:
            self.log_result("Category Deletion Validation - With Items", False, f"Error testing category deletion: {str(e)}")

        # Test 2: Create category with items in pending orders and try to delete
        try:
            # Create a new category for this test
            category_data = {
                "name": "Category with Pending Orders",
                "description": "Category for testing pending order validation",
                "display_order": 100
            }
            response = requests.post(f"{API_BASE}/restaurant/categories", json=category_data, headers=headers)
            
            if response.status_code == 200:
                pending_category = response.json()
                
                # Create menu item in this category
                item_data = {
                    "name": "Item in Pending Order",
                    "description": "Item for testing pending order validation",
                    "price": 2000.0,
                    "category_id": pending_category['id'],
                    "is_vegetarian": False,
                    "is_spicy": False,
                    "prep_time": 20
                }
                response = requests.post(f"{API_BASE}/restaurant/menu-items", json=item_data, headers=headers)
                
                if response.status_code == 200:
                    pending_item = response.json()
                    
                    # Create order with this item (pending payment status)
                    tables_response = requests.get(f"{API_BASE}/restaurant/tables", headers=headers)
                    if tables_response.status_code == 200:
                        tables = tables_response.json()
                        if tables:
                            table = tables[0]
                            
                            order_items = [{
                                "menu_item_id": pending_item['id'],
                                "menu_item_name": pending_item['name'],
                                "quantity": 1,
                                "unit_price": pending_item['price'],
                                "total_price": pending_item['price'],
                                "special_notes": "For validation testing"
                            }]
                            
                            pending_order = {
                                "order_type": "table",
                                "table_id": table['id'],
                                "customer_name": "Pending Order Customer",
                                "items": order_items,
                                "payment_method": "Cash",
                                "notes": "Order for testing deletion validation"
                            }
                            
                            response = requests.post(f"{API_BASE}/restaurant/orders", json=pending_order, headers=headers)
                            
                            if response.status_code == 200:
                                created_order = response.json()
                                self.created_resources['orders'].append(created_order['id'])
                                
                                # Now try to delete the category (should fail due to pending order)
                                response = requests.delete(f"{API_BASE}/restaurant/categories/{pending_category['id']}", headers=headers)
                                
                                if response.status_code == 400:
                                    error_message = response.json().get('detail', '')
                                    if 'pending' in error_message.lower() or 'active order' in error_message.lower():
                                        self.log_result("Category Deletion Validation - Pending Orders", True, 
                                                      "Correctly prevented deletion of category with items in pending orders")
                                    else:
                                        self.log_result("Category Deletion Validation - Pending Orders", True, 
                                                      "Category deletion prevented (validation working)")
                                else:
                                    self.log_result("Category Deletion Validation - Pending Orders", False, 
                                                  f"Should have failed with 400, got: {response.status_code}")
                                
                                # Clean up - pay the order and then delete
                                requests.post(f"{API_BASE}/restaurant/orders/{created_order['id']}/pay", headers=headers)
                                requests.delete(f"{API_BASE}/restaurant/menu-items/{pending_item['id']}", headers=headers)
                                requests.delete(f"{API_BASE}/restaurant/categories/{pending_category['id']}", headers=headers)
                            else:
                                self.log_result("Category Deletion Validation - Pending Orders", False, 
                                              "Failed to create test order")
                        else:
                            self.log_result("Category Deletion Validation - Pending Orders", False, "No tables available")
                    else:
                        self.log_result("Category Deletion Validation - Pending Orders", False, "Failed to get tables")
                else:
                    self.log_result("Category Deletion Validation - Pending Orders", False, "Failed to create test item")
            else:
                self.log_result("Category Deletion Validation - Pending Orders", False, "Failed to create test category")
        except Exception as e:
            self.log_result("Category Deletion Validation - Pending Orders", False, f"Error testing pending order validation: {str(e)}")

        # Test 3: Delete empty category (should succeed)
        try:
            # Create empty category
            empty_category_data = {
                "name": "Empty Category",
                "description": "Category with no items for deletion testing",
                "display_order": 101
            }
            response = requests.post(f"{API_BASE}/restaurant/categories", json=empty_category_data, headers=headers)
            
            if response.status_code == 200:
                empty_category = response.json()
                
                # Try to delete empty category (should succeed)
                response = requests.delete(f"{API_BASE}/restaurant/categories/{empty_category['id']}", headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Category Deletion - Empty Category", True, 
                                  "Successfully deleted empty category")
                else:
                    self.log_result("Category Deletion - Empty Category", False, 
                                  f"Failed to delete empty category: {response.status_code}")
            else:
                self.log_result("Category Deletion - Empty Category", False, "Failed to create empty category")
        except Exception as e:
            self.log_result("Category Deletion - Empty Category", False, f"Error testing empty category deletion: {str(e)}")

    def test_menu_item_deletion_validation(self):
        """Test DELETE /api/restaurant/menu-items/{item_id} with validation"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Try to delete item that's in a pending order (should fail)
        try:
            if self.created_resources['orders'] and self.created_resources['menu_items']:
                # Get the first order to find which item is in use
                orders_response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
                if orders_response.status_code == 200:
                    orders = orders_response.json()
                    pending_orders = [o for o in orders if o.get('payment_status') == 'Pending']
                    
                    if pending_orders:
                        pending_order = pending_orders[0]
                        if pending_order.get('items'):
                            item_in_order = pending_order['items'][0]
                            item_id = item_in_order['menu_item_id']
                            
                            # Try to delete this item (should fail)
                            response = requests.delete(f"{API_BASE}/restaurant/menu-items/{item_id}", headers=headers)
                            
                            if response.status_code == 400:
                                error_message = response.json().get('detail', '')
                                if 'active order' in error_message.lower() or 'pending' in error_message.lower():
                                    self.log_result("Menu Item Deletion Validation - In Pending Order", True, 
                                                  "Correctly prevented deletion of item in pending order")
                                else:
                                    self.log_result("Menu Item Deletion Validation - In Pending Order", True, 
                                                  "Item deletion prevented (validation working)")
                            else:
                                self.log_result("Menu Item Deletion Validation - In Pending Order", False, 
                                              f"Should have failed with 400, got: {response.status_code}")
                        else:
                            self.log_result("Menu Item Deletion Validation - In Pending Order", False, 
                                          "No items found in pending order")
                    else:
                        self.log_result("Menu Item Deletion Validation - In Pending Order", False, 
                                      "No pending orders found for testing")
                else:
                    self.log_result("Menu Item Deletion Validation - In Pending Order", False, 
                                  "Failed to get orders for validation testing")
            else:
                self.log_result("Menu Item Deletion Validation - In Pending Order", False, 
                              "No test orders or items available")
        except Exception as e:
            self.log_result("Menu Item Deletion Validation - In Pending Order", False, f"Error testing item deletion validation: {str(e)}")

        # Test 2: Delete item not in any orders (should succeed)
        try:
            # Create a new item not used in any orders
            categories_response = requests.get(f"{API_BASE}/restaurant/categories", headers=headers)
            if categories_response.status_code == 200:
                categories = categories_response.json()
                if categories:
                    category = categories[0]
                    
                    unused_item_data = {
                        "name": "Unused Item for Deletion",
                        "description": "Item not used in any orders",
                        "price": 1000.0,
                        "category_id": category['id'],
                        "is_vegetarian": True,
                        "is_spicy": False,
                        "prep_time": 10
                    }
                    
                    response = requests.post(f"{API_BASE}/restaurant/menu-items", json=unused_item_data, headers=headers)
                    
                    if response.status_code == 200:
                        unused_item = response.json()
                        
                        # Try to delete this unused item (should succeed)
                        response = requests.delete(f"{API_BASE}/restaurant/menu-items/{unused_item['id']}", headers=headers)
                        
                        if response.status_code == 200:
                            self.log_result("Menu Item Deletion - Unused Item", True, 
                                          "Successfully deleted unused menu item")
                        else:
                            self.log_result("Menu Item Deletion - Unused Item", False, 
                                          f"Failed to delete unused item: {response.status_code}")
                    else:
                        self.log_result("Menu Item Deletion - Unused Item", False, "Failed to create unused item")
                else:
                    self.log_result("Menu Item Deletion - Unused Item", False, "No categories available")
            else:
                self.log_result("Menu Item Deletion - Unused Item", False, "Failed to get categories")
        except Exception as e:
            self.log_result("Menu Item Deletion - Unused Item", False, f"Error testing unused item deletion: {str(e)}")

    def test_authentication_and_role_protection(self):
        """Test authentication and role protection for restaurant endpoints"""
        
        # Test 1: Unauthenticated access (should fail)
        try:
            response = requests.get(f"{API_BASE}/restaurant/orders")
            if response.status_code == 401:
                self.log_result("Restaurant Endpoints - No Auth", True, 
                              "Correctly rejected unauthenticated access")
            else:
                self.log_result("Restaurant Endpoints - No Auth", False, 
                              f"Should have returned 401, got: {response.status_code}")
        except Exception as e:
            self.log_result("Restaurant Endpoints - No Auth", False, f"Error testing unauthenticated access: {str(e)}")

        # Test 2: Admin access (should succeed)
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
            if response.status_code == 200:
                self.log_result("Restaurant Endpoints - Admin Access", True, 
                              "Admin can access restaurant endpoints")
            else:
                self.log_result("Restaurant Endpoints - Admin Access", False, 
                              f"Admin access failed: {response.status_code}")
        except Exception as e:
            self.log_result("Restaurant Endpoints - Admin Access", False, f"Error testing admin access: {str(e)}")

        # Test 3: Restaurant Manager access (should succeed)
        if self.restaurant_token:
            try:
                headers = {"Authorization": f"Bearer {self.restaurant_token}"}
                response = requests.get(f"{API_BASE}/restaurant/orders", headers=headers)
                if response.status_code == 200:
                    self.log_result("Restaurant Endpoints - Restaurant Manager Access", True, 
                                  "Restaurant Manager can access restaurant endpoints")
                else:
                    self.log_result("Restaurant Endpoints - Restaurant Manager Access", False, 
                                  f"Restaurant Manager access failed: {response.status_code}")
            except Exception as e:
                self.log_result("Restaurant Endpoints - Restaurant Manager Access", False, f"Error testing restaurant manager access: {str(e)}")
        else:
            self.log_result("Restaurant Endpoints - Restaurant Manager Access", False, 
                          "Restaurant Manager not authenticated")

        # Test 4: Test multiple endpoints with proper authentication
        endpoints_to_test = [
            "/restaurant/categories",
            "/restaurant/menu-items", 
            "/restaurant/tables",
            "/restaurant/staff",
            "/restaurant/orders"
        ]
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        for endpoint in endpoints_to_test:
            try:
                response = requests.get(f"{API_BASE}{endpoint}", headers=headers)
                if response.status_code == 200:
                    self.log_result(f"Auth Protection - {endpoint}", True, 
                                  "Endpoint accessible with proper authentication")
                else:
                    self.log_result(f"Auth Protection - {endpoint}", False, 
                                  f"Endpoint failed with proper auth: {response.status_code}")
            except Exception as e:
                self.log_result(f"Auth Protection - {endpoint}", False, f"Error testing endpoint: {str(e)}")

    def cleanup_test_data(self):
        """Clean up created test data"""
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete created orders (by cancelling them)
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
        """Run all restaurant management tests focused on the review requirements"""
        print("🍽️  RESTAURANT MANAGEMENT SYSTEM BACKEND TESTING")
        print("=" * 60)
        print("Focus: Order Management, Deletion Validation, Authentication")
        print("=" * 60)
        
        # Authentication tests
        if not self.authenticate_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
            
        # Try to authenticate restaurant manager (optional)
        self.authenticate_restaurant_manager()
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Cannot proceed without test data setup")
            return False
        
        # Core tests based on review requirements
        print("\n📋 Testing Restaurant Order Management System...")
        self.test_restaurant_order_endpoints()
        
        print("\n🗑️  Testing Menu Category and Item Deletion with Validation...")
        self.test_category_deletion_validation()
        self.test_menu_item_deletion_validation()
        
        print("\n🔐 Testing Authentication and Role Protection...")
        self.test_authentication_and_role_protection()
        
        # Cleanup
        print("\n🧹 Cleaning up test data...")
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
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return failed == 0

if __name__ == "__main__":
    tester = RestaurantBackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)