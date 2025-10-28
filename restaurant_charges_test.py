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

def test_get_checked_in_customers():
    """Get checked-in customers to verify room 203 customer exists"""
    print("\n1. Testing Get Checked-in Customers (Verify Room 203)")
    
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            customers = response.json()
            print(f"Number of checked-in customers: {len(customers)}")
            
            # Look for customer in room 203
            room_203_customer = None
            for customer in customers:
                print(f"  Customer: {customer['name']} - Room {customer['current_room']}")
                print(f"    Restaurant charges: {customer.get('restaurant_charges', 0.0)}")
                if customer['current_room'] == '203':
                    room_203_customer = customer
            
            if room_203_customer:
                print(f"✅ Found customer in room 203: {room_203_customer['name']}")
                return True, customers, room_203_customer
            else:
                print("❌ No customer found in room 203")
                return False, customers, None
        else:
            print(f"❌ Failed to get customers - Status: {response.status_code}")
            return False, [], None
    except Exception as e:
        print(f"❌ Get customers failed - Exception: {e}")
        return False, [], None

def test_create_room_service_order(room_number="203", customer_name="Test Customer"):
    """Create a room service order for testing"""
    print(f"\n2. Creating Room Service Order for Room {room_number}")
    
    try:
        # First get menu items
        menu_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=auth_headers)
        if menu_response.status_code != 200:
            print("❌ Failed to get menu items")
            return False, None
        
        menu_items = menu_response.json()
        if not menu_items:
            print("❌ No menu items available")
            return False, None
        
        # Use first menu item for the order
        test_item = menu_items[0]
        print(f"Using menu item: {test_item['name']} - Price: {test_item['price']}")
        
        # Create room service order
        order_data = {
            "order_type": "room_service",
            "room_number": room_number,
            "customer_name": customer_name,
            "items": [
                {
                    "menu_item_id": test_item["id"],
                    "menu_item_name": test_item["name"],
                    "quantity": 2,
                    "unit_price": test_item["price"],
                    "total_price": test_item["price"] * 2,
                    "special_notes": "Test order for room service"
                }
            ],
            "notes": "Test room service order for restaurant charges integration"
        }
        
        response = requests.post(f"{API_BASE}/restaurant/orders", json=order_data, headers=auth_headers)
        print(f"Create Order Status Code: {response.status_code}")
        
        if response.status_code == 200:
            order = response.json()
            print(f"✅ Room service order created successfully")
            print(f"  Order ID: {order['id']}")
            print(f"  Order Number: {order['order_number']}")
            print(f"  Room Number: {order['room_number']}")
            print(f"  Total Amount: {order['total_amount']}")
            print(f"  Payment Status: {order['payment_status']}")
            return True, order
        else:
            print(f"❌ Failed to create order - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Create order failed - Exception: {e}")
        return False, None

def test_pay_room_service_order_with_room_bill(order, room_number="203"):
    """Pay room service order with 'add to room bill' option"""
    print(f"\n3. Paying Room Service Order with 'Add to Room Bill'")
    
    try:
        order_id = order["id"]
        payment_data = {
            "payment_method": "Cash",
            "add_to_room_bill": True
        }
        
        response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay", 
                               json=payment_data, headers=auth_headers)
        print(f"Payment Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment processed successfully")
            print(f"Response: {result}")
            return True
        else:
            print(f"❌ Payment failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Payment failed - Exception: {e}")
        return False

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