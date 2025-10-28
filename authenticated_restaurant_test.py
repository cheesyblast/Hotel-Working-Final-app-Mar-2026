#!/usr/bin/env python3
"""
Authenticated Restaurant Charges Integration Test for Room 203
Investigates the specific issue where restaurant items were added for 
a checked-in customer in room 203, but charges are not showing during checkout.
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
print("Investigating Room 203 Restaurant Charges Issue")
print("=" * 80)

# Global variable to store auth token
auth_token = None

def authenticate():
    """Authenticate with admin credentials"""
    global auth_token
    print("\n🔐 Authenticating with admin credentials...")
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        print(f"Login Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            auth_token = result.get('access_token')
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication exception: {e}")
        return False

def get_auth_headers():
    """Get authentication headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

def test_room_203_customer_status():
    """Test 1: Check if there's a customer checked into room 203"""
    print("\n1. Testing Room 203 Customer Status")
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            customers = response.json()
            print(f"Total checked-in customers: {len(customers)}")
            
            # Look for room 203 customer (check both "203" and "Room 203" formats)
            room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
            
            if room_203_customers:
                customer = room_203_customers[0]
                print(f"✅ Found customer in room 203:")
                print(f"  Name: {customer.get('name')}")
                print(f"  Email: {customer.get('email')}")
                print(f"  Phone: {customer.get('phone')}")
                print(f"  Current Room: {customer.get('current_room')}")
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
        response = requests.get(f"{API_BASE}/restaurant/orders", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print(f"Total restaurant orders: {len(orders)}")
            
            # Look for room 203 orders (check both "203" and "Room 203" formats)
            room_203_orders = [o for o in orders if o.get('room_number') in ['203', 'Room 203']]
            
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
                for order in orders[:10]:  # Show first 10 orders
                    print(f"  Order {order.get('order_number')}: Room {order.get('room_number')} - {order.get('customer_name')} - Status: {order.get('payment_status')}")
                
                return False, []
        else:
            print(f"❌ Failed to get restaurant orders - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, []
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, []

def test_create_room_service_order_for_room_203(customer):
    """Test 3: Create a room service order for room 203 to test the integration"""
    print("\n3. Testing Room Service Order Creation for Room 203")
    
    if not customer:
        print("❌ No customer data available")
        return False, None
    
    try:
        # Get menu items first
        menu_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=get_auth_headers())
        print(f"Menu Items Status Code: {menu_response.status_code}")
        
        if menu_response.status_code != 200:
            print("❌ Failed to get menu items")
            return False, None
        
        menu_items = menu_response.json()
        if not menu_items:
            print("❌ No menu items available")
            return False, None
        
        # Look for Sun Crush or use first available item
        sun_crush_item = None
        for item in menu_items:
            if 'Sun Crush' in item.get('name', ''):
                sun_crush_item = item
                break
        
        if not sun_crush_item:
            sun_crush_item = menu_items[0]  # Use first item if Sun Crush not found
            print(f"ℹ️ Sun Crush not found, using: {sun_crush_item.get('name')}")
        else:
            print(f"✅ Found Sun Crush item: {sun_crush_item.get('name')}")
        
        # Create room service order
        room_number = customer.get('current_room')
        if room_number == 'Room 203':
            room_number = '203'  # Normalize room number
        
        order_data = {
            "order_type": "room_service",
            "room_number": room_number,
            "customer_name": customer.get('name'),
            "items": [
                {
                    "menu_item_id": sun_crush_item['id'],
                    "menu_item_name": sun_crush_item['name'],
                    "quantity": 2,
                    "unit_price": sun_crush_item['price'],
                    "total_price": sun_crush_item['price'] * 2,
                    "special_notes": "Test order for room 203 integration"
                }
            ],
            "notes": "Test room service order for restaurant charges integration"
        }
        
        print(f"Creating room service order for room {room_number}...")
        create_response = requests.post(f"{API_BASE}/restaurant/orders", json=order_data, headers=get_auth_headers())
        print(f"Create Order Status Code: {create_response.status_code}")
        
        if create_response.status_code == 200:
            order_result = create_response.json()
            order_id = order_result.get('id')
            print(f"✅ Created test order: {order_id}")
            print(f"Order total: {order_result.get('total_amount')}")
            print(f"Payment status: {order_result.get('payment_status')}")
            
            return True, order_result
        else:
            print(f"❌ Failed to create test order - Status code: {create_response.status_code}")
            print(f"Response: {create_response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Exception during order creation: {e}")
        return False, None

def test_restaurant_order_payment_and_integration(order, customer):
    """Test 4: Test restaurant order payment and customer integration"""
    print("\n4. Testing Restaurant Order Payment and Customer Integration")
    
    if not order or not customer:
        print("❌ No order or customer data available")
        return False
    
    order_id = order.get('id')
    customer_id = customer.get('id')
    
    try:
        # Get customer charges before payment
        print("Getting customer charges before payment...")
        before_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        if before_response.status_code == 200:
            customers = before_response.json()
            room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
            if room_203_customers:
                before_customer = room_203_customers[0]
                before_restaurant_charges = before_customer.get('restaurant_charges', 0)
                print(f"Restaurant charges before payment: {before_restaurant_charges}")
            else:
                print("❌ Could not find customer before payment")
                return False
        else:
            print("❌ Failed to get customer data before payment")
            return False
        
        # Pay the restaurant order
        print(f"Processing payment for order: {order_id}")
        payment_response = requests.post(f"{API_BASE}/restaurant/orders/{order_id}/pay", headers=get_auth_headers())
        print(f"Payment Status Code: {payment_response.status_code}")
        
        if payment_response.status_code == 200:
            payment_result = payment_response.json()
            print(f"✅ Payment processed: {payment_result}")
            
            # Check if customer charges were updated
            print("Checking if customer charges were updated...")
            after_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
            if after_response.status_code == 200:
                customers = after_response.json()
                room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
                
                if room_203_customers:
                    after_customer = room_203_customers[0]
                    after_restaurant_charges = after_customer.get('restaurant_charges', 0)
                    print(f"Restaurant charges after payment: {after_restaurant_charges}")
                    
                    charge_difference = after_restaurant_charges - before_restaurant_charges
                    order_amount = order.get('total_amount', 0)
                    
                    print(f"Expected charge increase: {order_amount}")
                    print(f"Actual charge increase: {charge_difference}")
                    
                    if charge_difference > 0 and abs(charge_difference - order_amount) < 0.01:
                        print("✅ Restaurant charges were correctly added to customer record")
                        return True
                    else:
                        print("❌ Restaurant charges were NOT correctly added to customer record")
                        print("This indicates a problem with the payment integration")
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
            
    except Exception as e:
        print(f"❌ Exception during payment integration test: {e}")
        return False

def test_checkout_with_restaurant_charges(customer):
    """Test 5: Test checkout process with restaurant charges"""
    print("\n5. Testing Checkout Process with Restaurant Charges")
    
    if not customer:
        print("❌ No customer data available")
        return False
    
    customer_id = customer.get('id')
    
    try:
        # Get current customer data
        print("Getting current customer data for checkout...")
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        if response.status_code == 200:
            customers = response.json()
            room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
            
            if room_203_customers:
                current_customer = room_203_customers[0]
                restaurant_charges = current_customer.get('restaurant_charges', 0)
                room_charges = current_customer.get('room_charges', 0)
                
                print(f"Customer: {current_customer.get('name')}")
                print(f"Room charges: {room_charges}")
                print(f"Restaurant charges: {restaurant_charges}")
                print(f"Total expected in bill: {room_charges + restaurant_charges}")
                
                # Perform checkout
                checkout_data = {
                    "customer_id": customer_id,
                    "additional_amount": 0.0,
                    "discount_amount": 0.0,
                    "payment_method": "Cash"
                }
                
                print("Performing checkout...")
                checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=get_auth_headers())
                print(f"Checkout Status Code: {checkout_response.status_code}")
                
                if checkout_response.status_code == 200:
                    checkout_result = checkout_response.json()
                    print(f"Checkout successful: {checkout_result.get('message')}")
                    
                    billing_details = checkout_result.get('billing_details', {})
                    if billing_details:
                        bill_room_charges = billing_details.get('room_charges', 0)
                        bill_restaurant_charges = billing_details.get('restaurant_charges', 0)
                        bill_total = billing_details.get('total_amount', 0)
                        
                        print(f"\nBilling Details:")
                        print(f"  Room charges in bill: {bill_room_charges}")
                        print(f"  Restaurant charges in bill: {bill_restaurant_charges}")
                        print(f"  Total amount in bill: {bill_total}")
                        
                        if bill_restaurant_charges > 0:
                            print("✅ Restaurant charges are included in checkout bill")
                            if abs(bill_restaurant_charges - restaurant_charges) < 0.01:
                                print("✅ Restaurant charges amount is correct")
                                return True
                            else:
                                print(f"❌ Restaurant charges amount mismatch. Expected: {restaurant_charges}, Got: {bill_restaurant_charges}")
                                return False
                        else:
                            print("❌ Restaurant charges are NOT included in checkout bill")
                            print("🔍 This is the root cause of the reported issue!")
                            return False
                    else:
                        print("❌ No billing details in checkout response")
                        return False
                else:
                    print(f"❌ Checkout failed - Status code: {checkout_response.status_code}")
                    print(f"Response: {checkout_response.text}")
                    return False
            else:
                print("❌ Could not find room 203 customer for checkout")
                return False
        else:
            print("❌ Failed to get customer data for checkout")
            return False
            
    except Exception as e:
        print(f"❌ Exception during checkout test: {e}")
        return False

def main():
    """Run comprehensive restaurant charges integration test"""
    print("Starting Authenticated Restaurant Charges Integration Investigation")
    print("Focus: Room 203 Restaurant Charges Issue")
    print("=" * 70)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return False
    
    test_results = []
    
    # Test 1: Check Room 203 Customer Status
    customer_found, customer_data = test_room_203_customer_status()
    test_results.append(("Room 203 Customer Check", customer_found))
    
    # Test 2: Check Restaurant Orders for Room 203
    orders_found, orders_data = test_restaurant_orders_for_room_203()
    test_results.append(("Restaurant Orders for Room 203", orders_found))
    
    # Test 3: Create Room Service Order for Testing
    order_created, order_data = test_create_room_service_order_for_room_203(customer_data)
    test_results.append(("Create Room Service Order", order_created))
    
    # Test 4: Test Payment and Integration
    payment_integration_works = test_restaurant_order_payment_and_integration(order_data, customer_data)
    test_results.append(("Payment Integration", payment_integration_works))
    
    # Test 5: Test Checkout Integration
    checkout_integration_works = test_checkout_with_restaurant_charges(customer_data)
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
    
    if customer_found:
        print("✅ Customer found in room 203")
    else:
        print("🔍 ISSUE: No customer found in room 203")
    
    if orders_found:
        print("✅ Restaurant orders found for room 203")
    else:
        print("🔍 INFO: No existing restaurant orders for room 203")
    
    if order_created:
        print("✅ Successfully created test room service order")
    else:
        print("🔍 ISSUE: Could not create test room service order")
    
    if payment_integration_works:
        print("✅ Payment integration working - charges added to customer")
    else:
        print("🔍 ISSUE: Payment integration not working - charges not added to customer")
    
    if checkout_integration_works:
        print("✅ Checkout integration working - restaurant charges included")
    else:
        print("🔍 CRITICAL ISSUE: Checkout integration not working - restaurant charges NOT included")
    
    print("\n" + "=" * 70)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 70)
    
    if not checkout_integration_works:
        print("🚨 ROOT CAUSE IDENTIFIED:")
        print("   The checkout process is NOT including restaurant_charges in the billing")
        print("   This explains why restaurant items don't show during checkout")
        print("\n💡 SOLUTION NEEDED:")
        print("   Update the checkout endpoint (/api/checkout) to:")
        print("   1. Include restaurant_charges in billing_details")
        print("   2. Add restaurant_charges to total_amount calculation")
        print("   3. Ensure restaurant_charges are displayed in checkout UI")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)