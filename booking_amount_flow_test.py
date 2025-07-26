#!/usr/bin/env python3
"""
CRITICAL BUG INVESTIGATION - BOOKING AMOUNT FLOW
Testing the specific user-reported bug with booking amount calculation flow.

SCENARIO TO TEST:
1. Create a SHORT TIME booking 
2. Update the booking dates while it's in "Upcoming" status (should trigger booking amount recalculation)
3. Click check-in (moves to "Checked-in Customer" section)
4. Click checkout - USER REPORTS it shows different amount than expected

INVESTIGATION FOCUS:
- Verify booking_amount is updated correctly when dates are changed
- Verify customer record gets correct room_charges from updated booking_amount
- Verify checkout shows correct room charges (should match updated booking_amount)
"""

import requests
import json
from datetime import date, datetime, timedelta
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

print(f"🔍 CRITICAL BUG INVESTIGATION - BOOKING AMOUNT FLOW")
print(f"Testing Hotel Management API at: {API_BASE}")
print("=" * 80)

# Global variables to store test data
auth_token = None
test_booking_id = None
test_customer_id = None

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
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            print("✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return False

def get_auth_headers():
    """Get authorization headers"""
    if not auth_token:
        return {}
    return {"Authorization": f"Bearer {auth_token}"}

def step1_create_short_time_booking():
    """Step 1: Create a SHORT TIME booking and note the initial booking_amount"""
    global test_booking_id
    print("\n📝 STEP 1: Create Short Time Booking")
    print("-" * 50)
    
    try:
        # First, get available rooms
        rooms_response = requests.get(f"{API_BASE}/rooms")
        if rooms_response.status_code != 200:
            print("❌ Failed to get rooms")
            return False
        
        rooms = rooms_response.json()
        available_room = None
        for room in rooms:
            if room.get('status') == 'Available':
                available_room = room
                break
        
        if not available_room:
            print("❌ No available rooms found")
            return False
        
        room_number = available_room['room_number']
        room_price = available_room.get('price_per_night', 5000)
        
        print(f"Using room: {room_number} (Price per night: {room_price})")
        
        # Create Short Time booking
        today = datetime.now().date()
        booking_data = {
            "guest_name": "Test Guest - Short Time",
            "guest_email": "testguest@example.com",
            "guest_phone": "+1234567890",
            "guest_id_passport": "TEST123456",
            "guest_country": "Test Country",
            "room_number": room_number,
            "check_in_date": today.isoformat(),
            "check_out_date": today.isoformat(),  # Same day for Short Time
            "stay_type": "Short Time",
            "booking_amount": room_price * 0.5,  # Short Time = 50% of night rate
            "additional_notes": "Test booking for amount flow investigation"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            booking = response.json()
            test_booking_id = booking['id']
            initial_amount = booking['booking_amount']
            
            print(f"✅ Short Time booking created successfully")
            print(f"   Booking ID: {test_booking_id}")
            print(f"   Room: {room_number}")
            print(f"   Stay Type: {booking['stay_type']}")
            print(f"   Check-in Date: {booking['check_in_date']}")
            print(f"   Check-out Date: {booking['check_out_date']}")
            print(f"   Initial Booking Amount: {initial_amount}")
            print(f"   Expected Amount (50% of {room_price}): {room_price * 0.5}")
            
            # Verify the booking amount is correct for Short Time
            expected_amount = room_price * 0.5
            if abs(initial_amount - expected_amount) < 0.01:
                print("✅ Initial booking amount is correct for Short Time")
                return True, initial_amount, room_number, room_price
            else:
                print(f"❌ Initial booking amount incorrect. Expected: {expected_amount}, Got: {initial_amount}")
                return False, initial_amount, room_number, room_price
        else:
            print(f"❌ Failed to create booking - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, 0, "", 0
            
    except Exception as e:
        print(f"❌ Step 1 failed - Exception: {e}")
        return False, 0, "", 0

def step2_update_booking_dates(initial_amount, room_number, room_price):
    """Step 2: Update booking dates while in 'Upcoming' status and verify amount recalculation"""
    print("\n🔄 STEP 2: Update Booking Dates (Should Trigger Amount Recalculation)")
    print("-" * 70)
    
    try:
        # First, verify booking is in "Upcoming" status
        booking_response = requests.get(f"{API_BASE}/bookings/{test_booking_id}", headers=get_auth_headers())
        if booking_response.status_code != 200:
            print("❌ Failed to get booking details")
            return False, initial_amount
        
        booking = booking_response.json()
        print(f"Current booking status: {booking.get('status')}")
        
        if booking.get('status') != 'Upcoming':
            print("❌ Booking is not in 'Upcoming' status - cannot update dates")
            return False, initial_amount
        
        # Update booking dates - extend by 1 day (convert Short Time to Night Stay)
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        update_data = {
            "check_in_date": today.isoformat(),
            "check_out_date": tomorrow.isoformat(),  # Extend to next day
            "additional_notes": "Updated dates - should recalculate amount"
        }
        
        print(f"Updating booking dates:")
        print(f"   Original: {booking.get('check_in_date')} to {booking.get('check_out_date')}")
        print(f"   New: {today} to {tomorrow}")
        print(f"   This should change from Short Time (50% rate) to Night Stay (full rate)")
        
        response = requests.put(f"{API_BASE}/bookings/{test_booking_id}", json=update_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            print("✅ Booking dates updated successfully")
            
            # Get updated booking to verify amount recalculation
            updated_booking_response = requests.get(f"{API_BASE}/bookings/{test_booking_id}", headers=get_auth_headers())
            if updated_booking_response.status_code != 200:
                print("❌ Failed to get updated booking details")
                return False, initial_amount
            
            updated_booking = updated_booking_response.json()
            new_amount = updated_booking.get('booking_amount')
            
            print(f"📊 AMOUNT COMPARISON:")
            print(f"   Original Amount: {initial_amount} (Short Time - 50% rate)")
            print(f"   Updated Amount: {new_amount}")
            print(f"   Expected Amount: {room_price} (1 night × {room_price})")
            
            # For a 1-night stay, the amount should be the full room price
            expected_new_amount = room_price
            
            if abs(new_amount - expected_new_amount) < 0.01:
                print("✅ Booking amount recalculation WORKING CORRECTLY")
                print(f"   Amount correctly updated from {initial_amount} to {new_amount}")
                return True, new_amount
            else:
                print("❌ CRITICAL BUG FOUND: Booking amount recalculation NOT WORKING")
                print(f"   Expected: {expected_new_amount}, Got: {new_amount}")
                return False, new_amount
        else:
            print(f"❌ Failed to update booking dates - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False, initial_amount
            
    except Exception as e:
        print(f"❌ Step 2 failed - Exception: {e}")
        return False, initial_amount

def step3_check_in_booking(updated_amount):
    """Step 3: Check in the booking and verify customer record gets correct room_charges"""
    global test_customer_id
    print("\n🏨 STEP 3: Check-in Process (Verify Customer Record Gets Updated Amount)")
    print("-" * 70)
    
    try:
        # Perform check-in
        checkin_data = {
            "booking_id": test_booking_id,
            "advance_amount": 500.0,
            "notes": "Test check-in for amount flow investigation",
            "payment_method": "Cash"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            checkin_result = response.json()
            print("✅ Check-in successful")
            print(f"Response: {checkin_result}")
            
            # Get checked-in customers to find our customer
            customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=get_auth_headers())
            if customers_response.status_code != 200:
                print("❌ Failed to get checked-in customers")
                return False
            
            customers = customers_response.json()
            test_customer = None
            
            for customer in customers:
                if customer.get('name') == 'Test Guest - Short Time':
                    test_customer = customer
                    test_customer_id = customer['id']
                    break
            
            if not test_customer:
                print("❌ Could not find checked-in customer")
                return False
            
            customer_room_charges = test_customer.get('room_charges')
            customer_total_amount = test_customer.get('total_amount')
            
            print(f"📊 CUSTOMER RECORD VERIFICATION:")
            print(f"   Customer ID: {test_customer_id}")
            print(f"   Room Charges: {customer_room_charges}")
            print(f"   Total Amount: {customer_total_amount}")
            print(f"   Expected Room Charges: {updated_amount} (from updated booking)")
            
            if abs(customer_room_charges - updated_amount) < 0.01:
                print("✅ Customer record has CORRECT room charges from updated booking")
                return True
            else:
                print("❌ CRITICAL BUG FOUND: Customer record has INCORRECT room charges")
                print(f"   Expected: {updated_amount}, Got: {customer_room_charges}")
                return False
        else:
            print(f"❌ Check-in failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Step 3 failed - Exception: {e}")
        return False

def step4_checkout_verification(updated_amount):
    """Step 4: Test checkout and verify it shows correct room charges"""
    print("\n💳 STEP 4: Checkout Process (Verify Correct Amount Display)")
    print("-" * 60)
    
    try:
        if not test_customer_id:
            print("❌ No customer ID available for checkout")
            return False
        
        # Perform checkout
        checkout_data = {
            "customer_id": test_customer_id,
            "additional_amount": 100.0,
            "discount_amount": 50.0,
            "payment_method": "Card"
        }
        
        response = requests.post(f"{API_BASE}/checkout", json=checkout_data, headers=get_auth_headers())
        
        if response.status_code == 200:
            checkout_result = response.json()
            billing_details = checkout_result.get('billing_details', {})
            
            print("✅ Checkout successful")
            print(f"📊 CHECKOUT BILLING VERIFICATION:")
            
            if billing_details:
                room_charges = billing_details.get('room_charges')
                additional_charges = billing_details.get('additional_charges')
                discount_amount = billing_details.get('discount_amount')
                total_amount = billing_details.get('total_amount')
                
                print(f"   Room Charges: {room_charges}")
                print(f"   Additional Charges: {additional_charges}")
                print(f"   Discount Amount: {discount_amount}")
                print(f"   Total Amount: {total_amount}")
                print(f"   Expected Room Charges: {updated_amount}")
                
                if abs(room_charges - updated_amount) < 0.01:
                    print("✅ CHECKOUT SHOWS CORRECT ROOM CHARGES")
                    print("✅ BOOKING AMOUNT FLOW IS WORKING CORRECTLY")
                    return True
                else:
                    print("❌ CRITICAL BUG CONFIRMED: CHECKOUT SHOWS INCORRECT ROOM CHARGES")
                    print(f"   Expected: {updated_amount}, Got: {room_charges}")
                    print("❌ USER REPORTED BUG IS CONFIRMED")
                    return False
            else:
                print("❌ No billing details in checkout response")
                return False
        else:
            print(f"❌ Checkout failed - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Step 4 failed - Exception: {e}")
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test booking if it exists
        if test_booking_id:
            requests.delete(f"{API_BASE}/bookings/{test_booking_id}", headers=get_auth_headers())
        
        # Note: Customer should be automatically removed by checkout
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

def main():
    """Run the complete booking amount flow investigation"""
    print("🔍 STARTING CRITICAL BUG INVESTIGATION")
    print("Testing the exact user-reported booking amount flow scenario")
    print("=" * 80)
    
    # Authenticate first
    if not authenticate():
        print("❌ Cannot proceed without authentication")
        return False
    
    try:
        # Step 1: Create Short Time Booking
        step1_success, initial_amount, room_number, room_price = step1_create_short_time_booking()
        if not step1_success:
            print("❌ Investigation failed at Step 1")
            return False
        
        # Step 2: Update Booking Dates
        step2_success, updated_amount = step2_update_booking_dates(initial_amount, room_number, room_price)
        if not step2_success:
            print("❌ CRITICAL BUG FOUND at Step 2: Booking amount recalculation not working")
            cleanup_test_data()
            return False
        
        # Step 3: Check-in Process
        step3_success = step3_check_in_booking(updated_amount)
        if not step3_success:
            print("❌ CRITICAL BUG FOUND at Step 3: Customer record not getting updated amount")
            cleanup_test_data()
            return False
        
        # Step 4: Checkout Verification
        step4_success = step4_checkout_verification(updated_amount)
        if not step4_success:
            print("❌ CRITICAL BUG CONFIRMED at Step 4: Checkout showing incorrect amount")
            cleanup_test_data()
            return False
        
        # All steps passed
        print("\n" + "=" * 80)
        print("🎉 INVESTIGATION COMPLETE - NO BUGS FOUND!")
        print("✅ All steps in the booking amount flow are working correctly:")
        print("   1. ✅ Short Time booking created with correct amount")
        print("   2. ✅ Booking amount recalculated correctly when dates updated")
        print("   3. ✅ Customer record received correct room charges during check-in")
        print("   4. ✅ Checkout displayed correct room charges")
        print("\n💡 The user-reported bug may have been fixed or was a different scenario.")
        print("=" * 80)
        
        cleanup_test_data()
        return True
        
    except Exception as e:
        print(f"❌ Investigation failed with exception: {e}")
        cleanup_test_data()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)