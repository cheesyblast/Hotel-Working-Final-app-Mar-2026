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

def test_verify_customer_restaurant_charges(room_number="203", expected_amount=None):
    """Verify that customer restaurant_charges field is updated correctly"""
    print(f"\n4. Verifying Customer Restaurant Charges for Room {room_number}")
    
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
        
        if response.status_code == 200:
            customers = response.json()
            
            # Find customer in specified room
            target_customer = None
            for customer in customers:
                if customer['current_room'] == room_number:
                    target_customer = customer
                    break
            
            if target_customer:
                restaurant_charges = target_customer.get('restaurant_charges', 0.0)
                print(f"✅ Found customer: {target_customer['name']}")
                print(f"  Current restaurant charges: {restaurant_charges}")
                
                if expected_amount is not None:
                    if restaurant_charges >= expected_amount:
                        print(f"✅ Restaurant charges updated correctly (>= {expected_amount})")
                        return True, restaurant_charges
                    else:
                        print(f"❌ Restaurant charges not updated correctly. Expected >= {expected_amount}, got {restaurant_charges}")
                        return False, restaurant_charges
                else:
                    if restaurant_charges > 0:
                        print(f"✅ Restaurant charges updated (amount: {restaurant_charges})")
                        return True, restaurant_charges
                    else:
                        print(f"❌ Restaurant charges not updated (still 0)")
                        return False, restaurant_charges
            else:
                print(f"❌ Customer not found in room {room_number}")
                return False, 0
        else:
            print(f"❌ Failed to get customers - Status: {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"❌ Verify charges failed - Exception: {e}")
        return False, 0

def test_checkout_includes_restaurant_charges(room_number="203"):
    """Test that checkout process includes restaurant charges"""
    print(f"\n5. Testing Checkout Process Includes Restaurant Charges")
    
    try:
        # Get customer for checkout
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
        if response.status_code != 200:
            print("❌ Failed to get customers for checkout test")
            return False
        
        customers = response.json()
        target_customer = None
        for customer in customers:
            if customer['current_room'] == room_number:
                target_customer = customer
                break
        
        if not target_customer:
            print(f"❌ No customer found in room {room_number} for checkout test")
            return False
        
        customer_id = target_customer['id']
        restaurant_charges_before = target_customer.get('restaurant_charges', 0.0)
        
        print(f"Customer: {target_customer['name']}")
        print(f"Restaurant charges before checkout: {restaurant_charges_before}")
        
        # Perform checkout
        checkout_data = {
            "customer_id": customer_id,
            "additional_amount": 0.0,
            "discount_amount": 0.0,
            "payment_method": "Cash"
        }
        
        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=auth_headers)
        print(f"Checkout Status Code: {checkout_response.status_code}")
        
        if checkout_response.status_code == 200:
            checkout_result = checkout_response.json()
            print(f"✅ Checkout completed successfully")
            
            # Check if billing details include restaurant charges
            billing_details = checkout_result.get("billing_details", {})
            if billing_details:
                restaurant_charges_in_bill = billing_details.get("restaurant_charges", 0.0)
                total_amount = billing_details.get("total_amount", 0.0)
                
                print(f"  Restaurant charges in bill: {restaurant_charges_in_bill}")
                print(f"  Total amount: {total_amount}")
                
                if restaurant_charges_in_bill > 0:
                    print(f"✅ Restaurant charges included in checkout ({restaurant_charges_in_bill})")
                    return True
                else:
                    print(f"❌ Restaurant charges not included in checkout")
                    return False
            else:
                print("❌ No billing details in checkout response")
                return False
        else:
            print(f"❌ Checkout failed - Status: {checkout_response.status_code}")
            print(f"Response: {checkout_response.text}")
            return False
    except Exception as e:
        print(f"❌ Checkout test failed - Exception: {e}")
        return False

def test_multiple_room_numbers():
    """Test the fix works for different room numbers"""
    print("\n6. Testing Multiple Room Numbers (Universal Fix Verification)")
    
    test_rooms = ["201", "202", "204"]  # Test different rooms
    results = []
    
    for room_num in test_rooms:
        print(f"\n  Testing Room {room_num}:")
        
        try:
            # Check if there's a customer in this room
            response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
            if response.status_code != 200:
                print(f"    ❌ Failed to get customers")
                results.append(False)
                continue
            
            customers = response.json()
            room_customer = None
            for customer in customers:
                if customer['current_room'] == room_num:
                    room_customer = customer
                    break
            
            if not room_customer:
                print(f"    ⚠️ No customer in room {room_num} - skipping")
                results.append(True)  # Not a failure, just no customer
                continue
            
            print(f"    Found customer: {room_customer['name']}")
            
            # Create and pay room service order
            order_success, order = test_create_room_service_order(room_num, room_customer['name'])
            if not order_success:
                print(f"    ❌ Failed to create order for room {room_num}")
                results.append(False)
                continue
            
            payment_success = test_pay_room_service_order_with_room_bill(order, room_num)
            if not payment_success:
                print(f"    ❌ Failed to pay order for room {room_num}")
                results.append(False)
                continue
            
            # Verify charges updated
            charges_success, charges = test_verify_customer_restaurant_charges(room_num, order['total_amount'])
            if charges_success:
                print(f"    ✅ Room {room_num} test passed - charges updated to {charges}")
                results.append(True)
            else:
                print(f"    ❌ Room {room_num} test failed - charges not updated")
                results.append(False)
                
        except Exception as e:
            print(f"    ❌ Room {room_num} test failed - Exception: {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    if success_count == total_count:
        print(f"\n✅ Multiple room test PASSED ({success_count}/{total_count})")
        return True
    else:
        print(f"\n❌ Multiple room test FAILED ({success_count}/{total_count})")
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