#!/usr/bin/env python3
"""
Restaurant Charges Integration Test for Room Service Orders
Tests the critical fix for restaurant charges integration where payment processing
now correctly uses "current_room" field to find customers instead of "room_number".
"""

import requests
import json
from datetime import date, datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except Exception as e:
        print(f"Error reading backend URL: {e}")
        return None

BASE_URL = get_backend_url()
if not BASE_URL:
    print("ERROR: Could not get backend URL from frontend/.env")
    sys.exit(1)

API_BASE = f"{BASE_URL}/api"

print(f"Testing Restaurant Charges Integration at: {API_BASE}")
print("Testing the critical fix for room service order billing")
print("=" * 80)

# Global variables for authentication
auth_token = None
auth_headers = {}

def authenticate():
    """Authenticate as admin to get access token"""
    global auth_token, auth_headers
    print("\n🔐 Authenticating as admin...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data["access_token"]
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def setup_test_data():
    """Initialize test data and ensure we have the required setup"""
    print("\n📋 Setting up test data...")
    
    try:
        # Initialize sample data
        response = requests.post(f"{API_BASE}/init-data", headers=auth_headers)
        if response.status_code != 200:
            print(f"❌ Failed to initialize sample data - Status: {response.status_code}")
            return False
        
        print("✅ Sample data initialized")
        return True
    except Exception as e:
        print(f"❌ Setup failed - Exception: {e}")
        return False

def test_room_203_customer_status():
    """Test 1: Check if there's a customer checked into room 203"""
    print("\n1. Testing Room 203 Customer Status")
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            customers = response.json()
            print(f"Total checked-in customers: {len(customers)}")
            
            # Look for room 203 customer
            room_203_customers = [c for c in customers if c.get('current_room') == '203']
            
            if room_203_customers:
                customer = room_203_customers[0]
                print(f"✅ Found customer in room 203:")
                print(f"  Name: {customer.get('name')}")
                print(f"  Email: {customer.get('email')}")
                print(f"  Phone: {customer.get('phone')}")
                print(f"  Check-in Date: {customer.get('check_in_date')}")
                print(f"  Check-out Date: {customer.get('check_out_date')}")
                print(f"  Room Charges: {customer.get('room_charges', 0)}")
                print(f"  Restaurant Charges: {customer.get('restaurant_charges', 0)}")
                print(f"  Additional Charges: {customer.get('additional_charges', 0)}")
                print(f"  Total Amount: {customer.get('total_amount', 0)}")
                return True, customer
            else:
                print("❌ No customer found in room 203")
                print("Available rooms with customers:")
                for customer in customers:
                    print(f"  Room {customer.get('current_room')}: {customer.get('name')}")
                return False, None
        else:
            print(f"❌ Failed to get checked-in customers - Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None

def test_restaurant_orders_for_room_203():
    """Test 2: Look for restaurant orders for room 203"""
    print("\n2. Testing Restaurant Orders for Room 203")
    try:
        response = requests.get(f"{API_BASE}/restaurant/orders")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print(f"Total restaurant orders: {len(orders)}")
            
            # Look for room 203 orders
            room_203_orders = [o for o in orders if o.get('room_number') == '203']
            
            if room_203_orders:
                print(f"✅ Found {len(room_203_orders)} restaurant order(s) for room 203:")
                for i, order in enumerate(room_203_orders):
                    print(f"\n  Order {i+1}:")
                    print(f"    Order ID: {order.get('id')}")
                    print(f"    Order Number: {order.get('order_number')}")
                    print(f"    Order Type: {order.get('order_type')}")
                    print(f"    Customer Name: {order.get('customer_name')}")
                    print(f"    Room Number: {order.get('room_number')}")
                    print(f"    Payment Status: {order.get('payment_status')}")
                    print(f"    Order Status: {order.get('order_status')}")
                    print(f"    Total Amount: {order.get('total_amount')}")
                    print(f"    Payment Method: {order.get('payment_method')}")
                    print(f"    Order Date: {order.get('order_date')}")
                    
                    # Check items
                    items = order.get('items', [])
                    print(f"    Items ({len(items)}):")
                    for item in items:
                        print(f"      - {item.get('menu_item_name')} x{item.get('quantity')} = {item.get('total_price')}")
                        if 'Sun Crush' in item.get('menu_item_name', ''):
                            print(f"        ✅ Found Sun Crush item!")
                
                return True, room_203_orders
            else:
                print("❌ No restaurant orders found for room 203")
                
                # Show all orders for debugging
                print("All restaurant orders:")
                for order in orders:
                    print(f"  Order {order.get('order_number')}: Room {order.get('room_number')} - {order.get('customer_name')} - Status: {order.get('payment_status')}")
                
                return False, []
        else:
            print(f"❌ Failed to get restaurant orders - Status code: {response.status_code}")
            return False, []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, []

def test_unpaid_restaurant_orders():
    """Test 3: Check for unpaid restaurant orders for room 203"""
    print("\n3. Testing Unpaid Restaurant Orders for Room 203")
    try:
        response = requests.get(f"{API_BASE}/restaurant/orders")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            
            # Look for unpaid room 203 orders
            unpaid_room_203_orders = [
                o for o in orders 
                if o.get('room_number') == '203' and o.get('payment_status') == 'Pending'
            ]
            
            if unpaid_room_203_orders:
                print(f"✅ Found {len(unpaid_room_203_orders)} unpaid restaurant order(s) for room 203:")
                total_unpaid_amount = 0
                for order in unpaid_room_203_orders:
                    amount = order.get('total_amount', 0)
                    total_unpaid_amount += amount
                    print(f"  Order {order.get('order_number')}: {amount} - Status: {order.get('payment_status')}")
                
                print(f"  Total unpaid amount: {total_unpaid_amount}")
                return True, unpaid_room_203_orders, total_unpaid_amount
            else:
                print("❌ No unpaid restaurant orders found for room 203")
                
                # Check if there are paid orders
                paid_room_203_orders = [
                    o for o in orders 
                    if o.get('room_number') == '203' and o.get('payment_status') == 'Paid'
                ]
                
                if paid_room_203_orders:
                    print(f"ℹ️ Found {len(paid_room_203_orders)} paid restaurant order(s) for room 203")
                    for order in paid_room_203_orders:
                        print(f"  Order {order.get('order_number')}: {order.get('total_amount')} - Status: {order.get('payment_status')}")
                
                return False, [], 0
        else:
            print(f"❌ Failed to get restaurant orders - Status code: {response.status_code}")
            return False, [], 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, [], 0

def test_customer_restaurant_charges_field(customer):
    """Test 4: Check if customer record has restaurant_charges field updated"""
    print("\n4. Testing Customer Restaurant Charges Field")
    
    if not customer:
        print("❌ No customer data available for testing")
        return False
    
    restaurant_charges = customer.get('restaurant_charges', 0)
    print(f"Customer restaurant_charges field: {restaurant_charges}")
    
    if restaurant_charges > 0:
        print(f"✅ Customer has restaurant charges: {restaurant_charges}")
        return True
    else:
        print("❌ Customer restaurant_charges field is 0 or missing")
        print("This indicates restaurant orders are not being added to customer bill")
        return False

def test_restaurant_order_payment_process():
    """Test 5: Test restaurant order payment process for room service orders"""
    print("\n5. Testing Restaurant Order Payment Process")
    
    # First, create a test room service order for room 203
    print("Creating test room service order for room 203...")
    
    try:
        # Get menu items first
        menu_response = requests.get(f"{API_BASE}/restaurant/menu-items")
        if menu_response.status_code != 200:
            print("❌ Failed to get menu items")
            return False
        
        menu_items = menu_response.json()
        if not menu_items:
            print("❌ No menu items available")
            return False
        
        # Use first menu item for test
        test_item = menu_items[0]
        
        # Create room service order
        order_data = {
            "order_type": "room_service",
            "room_number": "203",
            "customer_name": "Test Customer Room 203",
            "items": [
                {
                    "menu_item_id": test_item['id'],
                    "menu_item_name": test_item['name'],
                    "quantity": 2,
                    "unit_price": test_item['price'],
                    "total_price": test_item['price'] * 2,
                    "special_notes": "Test order for room 203"
                }
            ],
            "notes": "Test room service order for integration testing"
        }
        
        create_response = requests.post(f"{API_BASE}/restaurant/orders", json=order_data)
        print(f"Create Order Status Code: {create_response.status_code}")
        
        if create_response.status_code == 200:
            order_result = create_response.json()
            order_id = order_result.get('id')
            print(f"✅ Created test order: {order_id}")
            print(f"Order total: {order_result.get('total_amount')}")
            
            # Now test payment process
            print("Testing order payment process...")
            payment_response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay")
            print(f"Payment Status Code: {payment_response.status_code}")
            
            if payment_response.status_code == 200:
                payment_result = payment_response.json()
                print(f"✅ Payment processed: {payment_result}")
                
                # Check if customer charges were updated
                print("Checking if customer charges were updated...")
                customers_response = requests.get(f"{API_BASE}/customers/checked-in")
                if customers_response.status_code == 200:
                    customers = customers_response.json()
                    room_203_customers = [c for c in customers if c.get('current_room') == '203']
                    
                    if room_203_customers:
                        updated_customer = room_203_customers[0]
                        new_restaurant_charges = updated_customer.get('restaurant_charges', 0)
                        print(f"Updated customer restaurant_charges: {new_restaurant_charges}")
                        
                        if new_restaurant_charges > 0:
                            print("✅ Restaurant charges were added to customer record")
                            return True
                        else:
                            print("❌ Restaurant charges were NOT added to customer record")
                            return False
                    else:
                        print("❌ Could not find room 203 customer after payment")
                        return False
                else:
                    print("❌ Failed to get updated customer data")
                    return False
            else:
                print(f"❌ Payment failed - Status code: {payment_response.status_code}")
                print(f"Response: {payment_response.text}")
                return False
        else:
            print(f"❌ Failed to create test order - Status code: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during payment process test: {e}")
        return False

def test_checkout_integration_with_restaurant_charges(customer):
    """Test 6: Verify checkout process includes restaurant charges"""
    print("\n6. Testing Checkout Integration with Restaurant Charges")
    
    if not customer:
        print("❌ No customer data available for checkout test")
        return False
    
    customer_id = customer.get('id')
    print(f"Testing checkout for customer: {customer.get('name')} (ID: {customer_id})")
    print(f"Current restaurant charges: {customer.get('restaurant_charges', 0)}")
    
    try:
        # Perform checkout
        checkout_data = {
            "customer_id": customer_id,
            "additional_amount": 0.0,
            "discount_amount": 0.0,
            "payment_method": "Cash"
        }
        
        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data)
        print(f"Checkout Status Code: {checkout_response.status_code}")
        
        if checkout_response.status_code == 200:
            checkout_result = checkout_response.json()
            print(f"Checkout Response: {checkout_result}")
            
            billing_details = checkout_result.get('billing_details', {})
            if billing_details:
                restaurant_charges_in_bill = billing_details.get('restaurant_charges', 0)
                total_amount = billing_details.get('total_amount', 0)
                
                print(f"Restaurant charges in bill: {restaurant_charges_in_bill}")
                print(f"Total amount in bill: {total_amount}")
                
                if restaurant_charges_in_bill > 0:
                    print("✅ Restaurant charges are included in checkout bill")
                    return True
                else:
                    print("❌ Restaurant charges are NOT included in checkout bill")
                    print("This is the root cause of the issue!")
                    return False
            else:
                print("❌ No billing details in checkout response")
                return False
        else:
            print(f"❌ Checkout failed - Status code: {checkout_response.status_code}")
            print(f"Response: {checkout_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during checkout test: {e}")
        return False

def main():
    """Run comprehensive restaurant charges integration test"""
    print("Starting Restaurant Charges Integration Investigation")
    print("Focus: Room 203 Restaurant Charges Issue")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Check Room 203 Customer Status
    customer_found, customer_data = test_room_203_customer_status()
    test_results.append(("Room 203 Customer Check", customer_found))
    
    # Test 2: Check Restaurant Orders for Room 203
    orders_found, orders_data = test_restaurant_orders_for_room_203()
    test_results.append(("Restaurant Orders for Room 203", orders_found))
    
    # Test 3: Check Unpaid Restaurant Orders
    unpaid_found, unpaid_orders, unpaid_amount = test_unpaid_restaurant_orders()
    test_results.append(("Unpaid Restaurant Orders", unpaid_found))
    
    # Test 4: Check Customer Restaurant Charges Field
    charges_updated = test_customer_restaurant_charges_field(customer_data)
    test_results.append(("Customer Restaurant Charges Field", charges_updated))
    
    # Test 5: Test Restaurant Order Payment Process
    payment_process_works = test_restaurant_order_payment_process()
    test_results.append(("Restaurant Order Payment Process", payment_process_works))
    
    # Test 6: Test Checkout Integration
    checkout_integration_works = test_checkout_integration_with_restaurant_charges(customer_data)
    test_results.append(("Checkout Integration", checkout_integration_works))
    
    # Summary and Diagnosis
    print("\n" + "=" * 70)
    print("RESTAURANT CHARGES INTEGRATION TEST RESULTS")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    # Diagnosis
    print("\n" + "=" * 70)
    print("DIAGNOSIS AND FINDINGS")
    print("=" * 70)
    
    if not customer_found:
        print("🔍 ISSUE: No customer found in room 203")
        print("   - Check if customer is properly checked in")
        print("   - Verify room number is correct")
    
    if not orders_found:
        print("🔍 ISSUE: No restaurant orders found for room 203")
        print("   - Check if orders were created with correct room number")
        print("   - Verify order creation process")
    
    if not charges_updated:
        print("🔍 ISSUE: Customer restaurant_charges field not updated")
        print("   - Restaurant orders are not being linked to customer records")
        print("   - Payment process may not be updating customer charges")
    
    if not checkout_integration_works:
        print("🔍 CRITICAL ISSUE: Restaurant charges not included in checkout")
        print("   - This is likely the root cause of the reported problem")
        print("   - Checkout process needs to include restaurant_charges in billing")
    
    if unpaid_found:
        print(f"🔍 FINDING: {len(unpaid_orders)} unpaid restaurant orders found")
        print(f"   - Total unpaid amount: {unpaid_amount}")
        print("   - These orders should be added to customer bill")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if not checkout_integration_works:
        print("1. ✅ PRIORITY: Fix checkout process to include restaurant_charges")
        print("   - Update checkout endpoint to add restaurant_charges to billing")
        print("   - Ensure restaurant_charges are included in total_amount calculation")
    
    if not charges_updated:
        print("2. ✅ Fix restaurant order payment process")
        print("   - Ensure room service orders update customer restaurant_charges")
        print("   - Link paid restaurant orders to customer records")
    
    if unpaid_found:
        print("3. ✅ Handle unpaid restaurant orders")
        print("   - Add unpaid restaurant orders to customer bill during checkout")
        print("   - Or require payment of restaurant orders before checkout")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)