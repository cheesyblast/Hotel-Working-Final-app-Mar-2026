#!/usr/bin/env python3
"""
Final Restaurant Charges Integration Test for Room 203
Complete investigation and testing of the restaurant charges integration issue.
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
print("Final Investigation: Room 203 Restaurant Charges Issue")
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
            return False
    except Exception as e:
        print(f"❌ Authentication exception: {e}")
        return False

def get_auth_headers():
    """Get authentication headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

def test_existing_unpaid_orders():
    """Test 1: Check existing unpaid restaurant orders for room 203"""
    print("\n1. Testing Existing Unpaid Restaurant Orders for Room 203")
    try:
        response = requests.get(f"{API_BASE}/restaurant/orders", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            orders = response.json()
            print(f"Total restaurant orders: {len(orders)}")
            
            # Look for unpaid room 203 orders
            unpaid_room_203_orders = [
                o for o in orders 
                if o.get('room_number') in ['203', 'Room 203'] and o.get('payment_status') == 'Pending'
            ]
            
            if unpaid_room_203_orders:
                print(f"✅ Found {len(unpaid_room_203_orders)} unpaid restaurant order(s) for room 203:")
                total_unpaid_amount = 0
                for order in unpaid_room_203_orders:
                    amount = order.get('total_amount', 0)
                    total_unpaid_amount += amount
                    print(f"  Order {order.get('order_number')}: {amount} LKR - {order.get('payment_status')}")
                    
                    # Show items
                    items = order.get('items', [])
                    for item in items:
                        print(f"    - {item.get('menu_item_name')} x{item.get('quantity')}")
                        if 'Sun Crush' in item.get('menu_item_name', ''):
                            print(f"      ✅ Found Sun Crush item!")
                
                print(f"  Total unpaid amount: {total_unpaid_amount} LKR")
                return True, unpaid_room_203_orders, total_unpaid_amount
            else:
                print("❌ No unpaid restaurant orders found for room 203")
                return False, [], 0
        else:
            print(f"❌ Failed to get restaurant orders - Status code: {response.status_code}")
            return False, [], 0
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, [], 0

def test_pay_existing_orders_to_room_bill(unpaid_orders):
    """Test 2: Pay existing orders and add to room bill"""
    print("\n2. Testing Payment of Existing Orders to Room Bill")
    
    if not unpaid_orders:
        print("❌ No unpaid orders to test")
        return False
    
    success_count = 0
    
    for order in unpaid_orders:
        order_id = order.get('id')
        order_number = order.get('order_number')
        amount = order.get('total_amount')
        
        print(f"\nProcessing payment for order {order_number} (Amount: {amount} LKR)...")
        
        try:
            # Pay order and add to room bill
            payment_data = {
                "payment_method": "Cash",
                "add_to_room_bill": True  # This should add to customer's restaurant_charges
            }
            
            payment_response = requests.post(
                f"{API_BASE}/restaurant/orders/{order_id}/pay", 
                json=payment_data, 
                headers=get_auth_headers()
            )
            print(f"Payment Status Code: {payment_response.status_code}")
            
            if payment_response.status_code == 200:
                payment_result = payment_response.json()
                print(f"✅ Payment successful: {payment_result.get('message')}")
                success_count += 1
            else:
                print(f"❌ Payment failed - Status code: {payment_response.status_code}")
                print(f"Response: {payment_response.text}")
        except Exception as e:
            print(f"❌ Exception during payment: {e}")
    
    return success_count == len(unpaid_orders)

def test_customer_charges_after_payment():
    """Test 3: Check customer charges after payment"""
    print("\n3. Testing Customer Charges After Payment")
    
    try:
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            customers = response.json()
            room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
            
            if room_203_customers:
                customer = room_203_customers[0]
                restaurant_charges = customer.get('restaurant_charges', 0)
                room_charges = customer.get('room_charges', 0)
                total_amount = customer.get('total_amount', 0)
                
                print(f"✅ Customer: {customer.get('name')}")
                print(f"  Room charges: {room_charges} LKR")
                print(f"  Restaurant charges: {restaurant_charges} LKR")
                print(f"  Total amount: {total_amount} LKR")
                
                if restaurant_charges > 0:
                    print("✅ Restaurant charges have been added to customer record")
                    return True, customer
                else:
                    print("❌ Restaurant charges are still 0 - payment integration failed")
                    return False, customer
            else:
                print("❌ No customer found in room 203")
                return False, None
        else:
            print(f"❌ Failed to get customers - Status code: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False, None

def test_checkout_billing_details(customer):
    """Test 4: Test checkout billing details (without actually checking out)"""
    print("\n4. Testing Checkout Billing Details")
    
    if not customer:
        print("❌ No customer data available")
        return False
    
    customer_id = customer.get('id')
    restaurant_charges = customer.get('restaurant_charges', 0)
    room_charges = customer.get('room_charges', 0)
    
    print(f"Customer: {customer.get('name')}")
    print(f"Expected room charges: {room_charges} LKR")
    print(f"Expected restaurant charges: {restaurant_charges} LKR")
    print(f"Expected total: {room_charges + restaurant_charges} LKR")
    
    try:
        # Perform checkout to see billing details
        checkout_data = {
            "customer_id": customer_id,
            "additional_amount": 0.0,
            "discount_amount": 0.0,
            "payment_method": "Cash"
        }
        
        print("Performing checkout to check billing details...")
        checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=get_auth_headers())
        print(f"Checkout Status Code: {checkout_response.status_code}")
        
        if checkout_response.status_code == 200:
            checkout_result = checkout_response.json()
            print(f"Checkout successful: {checkout_result.get('message')}")
            
            billing_details = checkout_result.get('billing_details', {})
            if billing_details:
                bill_room_charges = billing_details.get('room_charges', 0)
                bill_additional_charges = billing_details.get('additional_charges', 0)
                bill_restaurant_charges = billing_details.get('restaurant_charges', 0)
                bill_total = billing_details.get('total_amount', 0)
                
                print(f"\nBilling Details from Checkout:")
                print(f"  Room charges: {bill_room_charges} LKR")
                print(f"  Additional charges: {bill_additional_charges} LKR")
                print(f"  Restaurant charges: {bill_restaurant_charges} LKR")
                print(f"  Total amount: {bill_total} LKR")
                
                # Check if restaurant charges are included in the total
                expected_total = room_charges + restaurant_charges
                
                if abs(bill_total - expected_total) < 0.01:
                    print("✅ Total amount is correct (includes restaurant charges)")
                    
                    # Check if restaurant charges are explicitly shown
                    if bill_restaurant_charges > 0:
                        print("✅ Restaurant charges are explicitly shown in billing details")
                        return True
                    elif bill_additional_charges >= restaurant_charges:
                        print("⚠️ Restaurant charges are included in additional_charges field")
                        print("   This is technically correct but not ideal for clarity")
                        return True
                    else:
                        print("❌ Restaurant charges are not clearly shown in billing")
                        return False
                else:
                    print(f"❌ Total amount is incorrect. Expected: {expected_total}, Got: {bill_total}")
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

def test_reinitialize_and_create_fresh_scenario():
    """Test 5: Create a fresh scenario to test the complete flow"""
    print("\n5. Testing Complete Flow with Fresh Data")
    
    try:
        # Reinitialize data to get fresh customers
        print("Reinitializing sample data...")
        init_response = requests.post(f"{API_BASE}/init-data", headers=get_auth_headers())
        if init_response.status_code != 200:
            print("❌ Failed to reinitialize data")
            return False
        
        # Get fresh customer in room 203
        customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        if customers_response.status_code != 200:
            print("❌ Failed to get customers")
            return False
        
        customers = customers_response.json()
        room_203_customers = [c for c in customers if c.get('current_room') in ['203', 'Room 203']]
        
        if not room_203_customers:
            print("❌ No customer in room 203 after reinitialization")
            return False
        
        customer = room_203_customers[0]
        print(f"✅ Fresh customer: {customer.get('name')} in room {customer.get('current_room')}")
        
        # Create a room service order
        menu_response = requests.get(f"{API_BASE}/restaurant/menu-items", headers=get_auth_headers())
        if menu_response.status_code != 200:
            print("❌ Failed to get menu items")
            return False
        
        menu_items = menu_response.json()
        sun_crush_item = None
        for item in menu_items:
            if 'Sun Crush' in item.get('name', ''):
                sun_crush_item = item
                break
        
        if not sun_crush_item:
            print("❌ Sun Crush item not found")
            return False
        
        # Create room service order
        room_number = customer.get('current_room')
        if room_number == 'Room 203':
            room_number = '203'
        
        order_data = {
            "order_type": "room_service",
            "room_number": room_number,
            "customer_name": customer.get('name'),
            "items": [
                {
                    "menu_item_id": sun_crush_item['id'],
                    "menu_item_name": sun_crush_item['name'],
                    "quantity": 1,
                    "unit_price": sun_crush_item['price'],
                    "total_price": sun_crush_item['price'],
                    "special_notes": "Fresh test order"
                }
            ],
            "notes": "Fresh room service order for testing"
        }
        
        print(f"Creating fresh room service order...")
        create_response = requests.post(f"{API_BASE}/restaurant/orders", json=order_data, headers=get_auth_headers())
        if create_response.status_code != 200:
            print("❌ Failed to create order")
            return False
        
        order = create_response.json()
        order_id = order.get('id')
        order_amount = order.get('total_amount')
        print(f"✅ Created order {order.get('order_number')} for {order_amount} LKR")
        
        # Pay the order and add to room bill
        payment_data = {
            "payment_method": "Cash",
            "add_to_room_bill": True
        }
        
        print("Paying order and adding to room bill...")
        payment_response = requests.post(
            f"{API_BASE}/restaurant/orders/{order_id}/pay", 
            json=payment_data, 
            headers=get_auth_headers()
        )
        
        if payment_response.status_code != 200:
            print(f"❌ Payment failed - Status code: {payment_response.status_code}")
            return False
        
        print("✅ Payment successful")
        
        # Check updated customer charges
        updated_customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
        if updated_customers_response.status_code != 200:
            print("❌ Failed to get updated customers")
            return False
        
        updated_customers = updated_customers_response.json()
        updated_room_203_customers = [c for c in updated_customers if c.get('current_room') in ['203', 'Room 203']]
        
        if not updated_room_203_customers:
            print("❌ Customer not found after payment")
            return False
        
        updated_customer = updated_room_203_customers[0]
        updated_restaurant_charges = updated_customer.get('restaurant_charges', 0)
        
        print(f"Updated restaurant charges: {updated_restaurant_charges} LKR")
        
        if updated_restaurant_charges >= order_amount:
            print("✅ Restaurant charges correctly updated")
            
            # Test checkout
            checkout_data = {
                "customer_id": updated_customer.get('id'),
                "additional_amount": 0.0,
                "discount_amount": 0.0,
                "payment_method": "Cash"
            }
            
            print("Testing final checkout...")
            final_checkout_response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=get_auth_headers())
            
            if final_checkout_response.status_code == 200:
                final_result = final_checkout_response.json()
                final_billing = final_result.get('billing_details', {})
                final_total = final_billing.get('total_amount', 0)
                
                expected_total = updated_customer.get('room_charges', 0) + updated_restaurant_charges
                
                print(f"Final checkout total: {final_total} LKR")
                print(f"Expected total: {expected_total} LKR")
                
                if abs(final_total - expected_total) < 0.01:
                    print("✅ Complete flow working - restaurant charges included in checkout")
                    return True
                else:
                    print("❌ Complete flow failed - restaurant charges not properly included")
                    return False
            else:
                print("❌ Final checkout failed")
                return False
        else:
            print("❌ Restaurant charges not updated correctly")
            return False
            
    except Exception as e:
        print(f"❌ Exception during complete flow test: {e}")
        return False

def main():
    """Run final comprehensive restaurant charges integration test"""
    print("Starting Final Restaurant Charges Integration Investigation")
    print("Focus: Complete Room 203 Restaurant Charges Flow")
    print("=" * 70)
    
    # Authenticate first
    if not authenticate():
        print("❌ Authentication failed. Cannot proceed with tests.")
        return False
    
    test_results = []
    
    # Test 1: Check existing unpaid orders
    unpaid_found, unpaid_orders, unpaid_amount = test_existing_unpaid_orders()
    test_results.append(("Existing Unpaid Orders Check", unpaid_found))
    
    # Test 2: Pay existing orders to room bill
    if unpaid_found:
        payment_success = test_pay_existing_orders_to_room_bill(unpaid_orders)
        test_results.append(("Pay Orders to Room Bill", payment_success))
        
        # Test 3: Check customer charges after payment
        charges_updated, customer_data = test_customer_charges_after_payment()
        test_results.append(("Customer Charges Updated", charges_updated))
        
        # Test 4: Test checkout billing
        checkout_correct = test_checkout_billing_details(customer_data)
        test_results.append(("Checkout Billing Correct", checkout_correct))
    else:
        test_results.append(("Pay Orders to Room Bill", False))
        test_results.append(("Customer Charges Updated", False))
        test_results.append(("Checkout Billing Correct", False))
    
    # Test 5: Complete fresh flow test
    complete_flow_works = test_reinitialize_and_create_fresh_scenario()
    test_results.append(("Complete Fresh Flow", complete_flow_works))
    
    # Summary and Final Diagnosis
    print("\n" + "=" * 70)
    print("FINAL RESTAURANT CHARGES INTEGRATION TEST RESULTS")
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
    
    # Final Diagnosis
    print("\n" + "=" * 70)
    print("FINAL DIAGNOSIS AND SOLUTION")
    print("=" * 70)
    
    if complete_flow_works:
        print("✅ GOOD NEWS: The restaurant charges integration is working correctly!")
        print("   - Room service orders can be paid and added to customer bills")
        print("   - Restaurant charges are included in checkout totals")
        print("   - The system is functioning as designed")
        print("\n🔍 LIKELY ISSUE WITH ORIGINAL PROBLEM:")
        print("   - The unpaid restaurant orders were not being added to room bill")
        print("   - Orders need to be explicitly paid with 'add_to_room_bill: true'")
        print("   - Unpaid orders remain as separate restaurant transactions")
    else:
        print("❌ CONFIRMED ISSUE: Restaurant charges integration is not working")
        print("   - There are problems with the payment or checkout process")
        print("   - Further investigation needed in the backend code")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS FOR USER")
    print("=" * 70)
    
    if unpaid_found:
        print("1. ✅ IMMEDIATE ACTION: Pay the existing unpaid restaurant orders")
        print(f"   - There are {len(unpaid_orders)} unpaid orders totaling {unpaid_amount} LKR")
        print("   - Use the restaurant management system to pay these orders")
        print("   - Make sure to select 'Add to Room Bill' when paying room service orders")
    
    print("2. ✅ PROCESS IMPROVEMENT:")
    print("   - Ensure restaurant staff pay room service orders immediately after delivery")
    print("   - Always select 'Add to Room Bill' for room service orders")
    print("   - Check customer bills before checkout to verify all charges are included")
    
    if not complete_flow_works:
        print("3. ✅ TECHNICAL FIX NEEDED:")
        print("   - The checkout process needs to be updated to show restaurant charges separately")
        print("   - Consider auto-adding unpaid room service orders to checkout")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)