#!/usr/bin/env python3
"""
Comprehensive Backend Testing for NEW ENHANCEMENTS
Tests the new features implemented as per the review request:
1. Advance Payment Collection
2. Enhanced Cancel Booking for Admin
3. Booking Amount Recalculation
4. Stay Type Recalculation
5. Authorization Testing
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

print(f"Testing NEW ENHANCEMENTS at: {API_BASE}")
print("=" * 80)

# Global variables for authentication
admin_token = None
non_admin_token = None

def get_admin_token():
    """Get admin authentication token"""
    global admin_token
    if admin_token:
        return admin_token
    
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            admin_token = data.get("access_token")
            return admin_token
        else:
            print(f"Failed to get admin token: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting admin token: {e}")
        return None

def get_auth_headers():
    """Get authorization headers for admin"""
    token = get_admin_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def test_advance_payment_collection():
    """Test 1: Advance Payment Collection"""
    print("\n1. Testing Advance Payment Collection (POST /api/advance-payment)")
    
    try:
        # First, create a booking and check it in
        print("Step 1: Creating and checking in a booking...")
        
        # Create booking
        booking_data = {
            "guest_name": "John Doe",
            "guest_email": "john.doe@example.com",
            "guest_phone": "+1234567890",
            "guest_id_passport": "ID123456",
            "guest_country": "USA",
            "room_number": "999",  # Use available room
            "check_in_date": datetime.now().date().isoformat(),
            "check_out_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 15000.0,
            "additional_notes": "Test booking for advance payment"
        }
        
        headers = get_auth_headers()
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        
        if booking_response.status_code != 200:
            print(f"❌ Failed to create booking: {booking_response.status_code}")
            print(f"Response: {booking_response.text}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get("id")
        print(f"✅ Booking created with ID: {booking_id}")
        
        # Check in the booking
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 5000.0,
            "notes": "Initial check-in",
            "payment_method": "Cash"
        }
        
        checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
        
        if checkin_response.status_code != 200:
            print(f"❌ Failed to check in booking: {checkin_response.status_code}")
            print(f"Response: {checkin_response.text}")
            return False
        
        checkin_result = checkin_response.json()
        customer_id = checkin_result.get("customer_id")
        print(f"✅ Booking checked in, customer ID: {customer_id}")
        
        # Step 2: Test advance payment collection
        print("Step 2: Testing advance payment collection...")
        
        advance_payment_data = {
            "customer_id": customer_id,
            "amount": 3000.0,
            "payment_method": "Card",
            "notes": "Additional advance payment for room service"
        }
        
        advance_response = requests.post(f"{API_BASE}/advance-payment", json=advance_payment_data, headers=headers)
        print(f"Advance Payment Status Code: {advance_response.status_code}")
        
        if advance_response.status_code == 200:
            result = advance_response.json()
            print(f"Advance Payment Response: {result}")
            
            # Step 3: Verify customer's advance amount is updated
            print("Step 3: Verifying customer's advance amount update...")
            
            customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
            if customers_response.status_code == 200:
                customers = customers_response.json()
                test_customer = next((c for c in customers if c.get("id") == customer_id), None)
                
                if test_customer:
                    expected_advance = 5000.0 + 3000.0  # Initial + additional
                    actual_advance = test_customer.get("advance_amount", 0)
                    print(f"Expected advance amount: {expected_advance}")
                    print(f"Actual advance amount: {actual_advance}")
                    
                    if actual_advance == expected_advance:
                        print("✅ Customer's advance amount correctly updated")
                        
                        # Step 4: Verify income record is created
                        print("Step 4: Verifying income record creation...")
                        
                        # Check if income was recorded
                        incomes_response = requests.get(f"{API_BASE}/incomes", headers=headers)
                        if incomes_response.status_code == 200:
                            incomes = incomes_response.json()
                            advance_income = next((i for i in incomes if 
                                                 i.get("description", "").lower().find("advance") != -1 and
                                                 i.get("amount") == 3000.0), None)
                            
                            if advance_income:
                                print("✅ Income record created for advance payment")
                                
                                # Step 5: Verify daily sale is recorded
                                print("Step 5: Verifying daily sale record...")
                                
                                daily_sales_response = requests.get(f"{API_BASE}/daily-sales", headers=headers)
                                if daily_sales_response.status_code == 200:
                                    daily_sales = daily_sales_response.json()
                                    advance_sale = next((s for s in daily_sales if 
                                                       s.get("customer_name") == "John Doe" and
                                                       s.get("payment_method") == "Card"), None)
                                    
                                    if advance_sale:
                                        print("✅ Daily sale recorded for advance payment")
                                        print("✅ ADVANCE PAYMENT COLLECTION TEST PASSED")
                                        return True
                                    else:
                                        print("❌ Daily sale not recorded for advance payment")
                                        return False
                                else:
                                    print(f"❌ Failed to get daily sales: {daily_sales_response.status_code}")
                                    return False
                            else:
                                print("❌ Income record not created for advance payment")
                                return False
                        else:
                            print(f"❌ Failed to get incomes: {incomes_response.status_code}")
                            return False
                    else:
                        print(f"❌ Customer's advance amount not updated correctly")
                        return False
                else:
                    print("❌ Could not find test customer after advance payment")
                    return False
            else:
                print(f"❌ Failed to get checked-in customers: {customers_response.status_code}")
                return False
        else:
            print(f"❌ Advance payment failed: {advance_response.status_code}")
            print(f"Response: {advance_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Advance payment test failed with exception: {e}")
        return False

def test_admin_cancel_booking_upcoming():
    """Test 2: Admin Cancel Booking - Upcoming"""
    print("\n2. Testing Admin Cancel Booking - Upcoming (POST /api/cancel/{booking_id})")
    
    try:
        # Step 1: Create an upcoming booking
        print("Step 1: Creating an upcoming booking...")
        
        future_date = datetime.now().date() + timedelta(days=5)
        booking_data = {
            "guest_name": "Jane Smith",
            "guest_email": "jane.smith@example.com",
            "guest_phone": "+1987654321",
            "guest_id_passport": "ID789012",
            "guest_country": "Canada",
            "room_number": "102",
            "check_in_date": future_date.isoformat(),
            "check_out_date": (future_date + timedelta(days=2)).isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 12000.0,
            "additional_notes": "Test booking for cancellation"
        }
        
        headers = get_auth_headers()
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        
        if booking_response.status_code != 200:
            print(f"❌ Failed to create upcoming booking: {booking_response.status_code}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get("id")
        print(f"✅ Upcoming booking created with ID: {booking_id}")
        
        # Step 2: Cancel the booking using admin credentials
        print("Step 2: Cancelling booking with admin credentials...")
        
        cancel_response = requests.post(f"{API_BASE}/cancel/{booking_id}", headers=headers)
        print(f"Cancel Status Code: {cancel_response.status_code}")
        
        if cancel_response.status_code == 200:
            result = cancel_response.json()
            print(f"Cancel Response: {result}")
            
            # Step 3: Verify booking status changed to "Cancelled"
            print("Step 3: Verifying booking status changed to 'Cancelled'...")
            
            booking_check_response = requests.get(f"{API_BASE}/bookings", headers=headers)
            if booking_check_response.status_code == 200:
                bookings_data = booking_check_response.json()
                bookings = bookings_data.get("bookings", [])
                cancelled_booking = next((b for b in bookings if b.get("id") == booking_id), None)
                
                if cancelled_booking and cancelled_booking.get("status") == "Cancelled":
                    print("✅ Booking status correctly changed to 'Cancelled'")
                    
                    # Step 4: Verify room is made available
                    print("Step 4: Verifying room is made available...")
                    
                    rooms_response = requests.get(f"{API_BASE}/rooms", headers=headers)
                    if rooms_response.status_code == 200:
                        rooms = rooms_response.json()
                        room_102 = next((r for r in rooms if r.get("room_number") == "102"), None)
                        
                        if room_102 and room_102.get("status") == "Available":
                            print("✅ Room 102 is now available")
                            print("✅ ADMIN CANCEL BOOKING - UPCOMING TEST PASSED")
                            return True
                        else:
                            print(f"❌ Room 102 status: {room_102.get('status') if room_102 else 'Not found'}")
                            return False
                    else:
                        print(f"❌ Failed to get rooms: {rooms_response.status_code}")
                        return False
                else:
                    print(f"❌ Booking status not changed correctly. Current status: {cancelled_booking.get('status') if cancelled_booking else 'Booking not found'}")
                    return False
            else:
                print(f"❌ Failed to get bookings: {booking_check_response.status_code}")
                return False
        else:
            print(f"❌ Cancel booking failed: {cancel_response.status_code}")
            print(f"Response: {cancel_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Admin cancel booking - upcoming test failed with exception: {e}")
        return False

def test_admin_cancel_booking_checked_in():
    """Test 3: Admin Cancel Booking - Checked-in"""
    print("\n3. Testing Admin Cancel Booking - Checked-in (POST /api/cancel/{booking_id})")
    
    try:
        # Step 1: Create and check in a booking
        print("Step 1: Creating and checking in a booking...")
        
        booking_data = {
            "guest_name": "Bob Wilson",
            "guest_email": "bob.wilson@example.com",
            "guest_phone": "+1555666777",
            "guest_id_passport": "ID345678",
            "guest_country": "UK",
            "room_number": "103",
            "check_in_date": datetime.now().date().isoformat(),
            "check_out_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 10000.0,
            "additional_notes": "Test booking for checked-in cancellation"
        }
        
        headers = get_auth_headers()
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        
        if booking_response.status_code != 200:
            print(f"❌ Failed to create booking: {booking_response.status_code}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get("id")
        print(f"✅ Booking created with ID: {booking_id}")
        
        # Check in the booking
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 2000.0,
            "notes": "Check-in for cancellation test",
            "payment_method": "Cash"
        }
        
        checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
        
        if checkin_response.status_code != 200:
            print(f"❌ Failed to check in booking: {checkin_response.status_code}")
            return False
        
        checkin_result = checkin_response.json()
        customer_id = checkin_result.get("customer_id")
        print(f"✅ Booking checked in, customer ID: {customer_id}")
        
        # Step 2: Cancel the checked-in booking using admin credentials
        print("Step 2: Cancelling checked-in booking with admin credentials...")
        
        cancel_response = requests.post(f"{API_BASE}/cancel/{booking_id}", headers=headers)
        print(f"Cancel Status Code: {cancel_response.status_code}")
        
        if cancel_response.status_code == 200:
            result = cancel_response.json()
            print(f"Cancel Response: {result}")
            
            # Step 3: Verify booking is cancelled
            print("Step 3: Verifying booking is cancelled...")
            
            booking_check_response = requests.get(f"{API_BASE}/bookings", headers=headers)
            if booking_check_response.status_code == 200:
                bookings_data = booking_check_response.json()
                bookings = bookings_data.get("bookings", [])
                cancelled_booking = next((b for b in bookings if b.get("id") == booking_id), None)
                
                if cancelled_booking and cancelled_booking.get("status") == "Cancelled":
                    print("✅ Booking status correctly changed to 'Cancelled'")
                    
                    # Step 4: Verify customer is removed
                    print("Step 4: Verifying customer is removed...")
                    
                    customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
                    if customers_response.status_code == 200:
                        customers = customers_response.json()
                        removed_customer = next((c for c in customers if c.get("id") == customer_id), None)
                        
                        if not removed_customer:
                            print("✅ Customer successfully removed from checked-in list")
                            
                            # Step 5: Verify room is made available
                            print("Step 5: Verifying room is made available...")
                            
                            rooms_response = requests.get(f"{API_BASE}/rooms", headers=headers)
                            if rooms_response.status_code == 200:
                                rooms = rooms_response.json()
                                room_103 = next((r for r in rooms if r.get("room_number") == "103"), None)
                                
                                if room_103 and room_103.get("status") == "Available":
                                    print("✅ Room 103 is now available")
                                    print("✅ ADMIN CANCEL BOOKING - CHECKED-IN TEST PASSED")
                                    return True
                                else:
                                    print(f"❌ Room 103 status: {room_103.get('status') if room_103 else 'Not found'}")
                                    return False
                            else:
                                print(f"❌ Failed to get rooms: {rooms_response.status_code}")
                                return False
                        else:
                            print("❌ Customer was not removed from checked-in list")
                            return False
                    else:
                        print(f"❌ Failed to get checked-in customers: {customers_response.status_code}")
                        return False
                else:
                    print(f"❌ Booking status not changed correctly. Current status: {cancelled_booking.get('status') if cancelled_booking else 'Booking not found'}")
                    return False
            else:
                print(f"❌ Failed to get bookings: {booking_check_response.status_code}")
                return False
        else:
            print(f"❌ Cancel checked-in booking failed: {cancel_response.status_code}")
            print(f"Response: {cancel_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Admin cancel booking - checked-in test failed with exception: {e}")
        return False

def test_booking_amount_recalculation():
    """Test 4: Booking Amount Recalculation"""
    print("\n4. Testing Booking Amount Recalculation (PUT /api/bookings/{id})")
    
    try:
        # Test Case 1: Short Time → Night Stay
        print("Test Case 1: Short Time booking extended to Night Stay...")
        
        # Create short time booking
        booking_data = {
            "guest_name": "Alice Johnson",
            "guest_email": "alice.johnson@example.com",
            "guest_phone": "+1444555666",
            "guest_id_passport": "ID111222",
            "guest_country": "Australia",
            "room_number": "201",
            "check_in_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
            "check_out_date": (datetime.now().date() + timedelta(days=1)).isoformat(),  # Same day = Short Time
            "stay_type": "Short Time",
            "booking_amount": 6000.0,  # Short time rate
            "additional_notes": "Short time booking for recalculation test"
        }
        
        headers = get_auth_headers()
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        
        if booking_response.status_code != 200:
            print(f"❌ Failed to create short time booking: {booking_response.status_code}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get("id")
        original_amount = booking.get("booking_amount")
        original_stay_type = booking.get("stay_type")
        print(f"✅ Short time booking created - ID: {booking_id}, Amount: {original_amount}, Stay Type: {original_stay_type}")
        
        # Update booking to extend dates (should trigger recalculation)
        update_data = {
            "check_in_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
            "check_out_date": (datetime.now().date() + timedelta(days=3)).isoformat(),  # 2 nights
            "additional_notes": "Extended to multiple days"
        }
        
        update_response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=headers)
        print(f"Update Status Code: {update_response.status_code}")
        
        if update_response.status_code == 200:
            result = update_response.json()
            print(f"Update Response: {result}")
            
            # Verify booking was updated with recalculated amount and stay type
            booking_check_response = requests.get(f"{API_BASE}/bookings", headers=headers)
            if booking_check_response.status_code == 200:
                bookings_data = booking_check_response.json()
                bookings = bookings_data.get("bookings", [])
                updated_booking = next((b for b in bookings if b.get("id") == booking_id), None)
                
                if updated_booking:
                    new_amount = updated_booking.get("booking_amount")
                    new_stay_type = updated_booking.get("stay_type")
                    print(f"Updated booking - Amount: {new_amount}, Stay Type: {new_stay_type}")
                    
                    if new_stay_type == "Night Stay" and new_amount != original_amount:
                        print("✅ Stay type recalculated from Short Time to Night Stay")
                        print("✅ Booking amount recalculated correctly")
                        
                        # Test Case 2: Night Stay date change
                        print("\nTest Case 2: Night Stay booking date change...")
                        
                        # Create another booking for night stay test
                        night_booking_data = {
                            "guest_name": "Charlie Brown",
                            "guest_email": "charlie.brown@example.com",
                            "guest_phone": "+1777888999",
                            "guest_id_passport": "ID333444",
                            "guest_country": "Germany",
                            "room_number": "202",
                            "check_in_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
                            "check_out_date": (datetime.now().date() + timedelta(days=4)).isoformat(),  # 2 nights
                            "stay_type": "Night Stay",
                            "booking_amount": 12000.0,  # 2 nights
                            "additional_notes": "Night stay booking for recalculation test"
                        }
                        
                        night_booking_response = requests.post(f"{API_BASE}/bookings", json=night_booking_data, headers=headers)
                        
                        if night_booking_response.status_code == 200:
                            night_booking = night_booking_response.json()
                            night_booking_id = night_booking.get("id")
                            night_original_amount = night_booking.get("booking_amount")
                            print(f"✅ Night stay booking created - ID: {night_booking_id}, Amount: {night_original_amount}")
                            
                            # Update to different dates (should recalculate amount)
                            night_update_data = {
                                "check_in_date": (datetime.now().date() + timedelta(days=2)).isoformat(),
                                "check_out_date": (datetime.now().date() + timedelta(days=6)).isoformat(),  # 4 nights now
                                "additional_notes": "Extended to 4 nights"
                            }
                            
                            night_update_response = requests.put(f"{API_BASE}/bookings/{night_booking_id}", json=night_update_data, headers=headers)
                            
                            if night_update_response.status_code == 200:
                                # Check if amount was recalculated
                                night_booking_check_response = requests.get(f"{API_BASE}/bookings", headers=headers)
                                if night_booking_check_response.status_code == 200:
                                    night_bookings_data = night_booking_check_response.json()
                                    night_bookings = night_bookings_data.get("bookings", [])
                                    night_updated_booking = next((b for b in night_bookings if b.get("id") == night_booking_id), None)
                                    
                                    if night_updated_booking:
                                        night_new_amount = night_updated_booking.get("booking_amount")
                                        print(f"Night stay updated booking - Amount: {night_new_amount}")
                                        
                                        if night_new_amount != night_original_amount:
                                            print("✅ Night stay booking amount recalculated correctly")
                                            print("✅ BOOKING AMOUNT RECALCULATION TEST PASSED")
                                            return True
                                        else:
                                            print("❌ Night stay booking amount not recalculated")
                                            return False
                                    else:
                                        print("❌ Could not find updated night stay booking")
                                        return False
                                else:
                                    print(f"❌ Failed to get bookings for night stay check: {night_booking_check_response.status_code}")
                                    return False
                            else:
                                print(f"❌ Failed to update night stay booking: {night_update_response.status_code}")
                                return False
                        else:
                            print(f"❌ Failed to create night stay booking: {night_booking_response.status_code}")
                            return False
                    else:
                        print(f"❌ Stay type or amount not recalculated correctly. Stay type: {new_stay_type}, Amount change: {new_amount != original_amount}")
                        return False
                else:
                    print("❌ Could not find updated booking")
                    return False
            else:
                print(f"❌ Failed to get bookings: {booking_check_response.status_code}")
                return False
        else:
            print(f"❌ Failed to update booking: {update_response.status_code}")
            print(f"Response: {update_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Booking amount recalculation test failed with exception: {e}")
        return False

def test_authorization():
    """Test 5: Authorization Testing"""
    print("\n5. Testing Authorization for Admin-Only Endpoints")
    
    try:
        # Test advance payment with admin credentials (should work)
        print("Test 1: Advance payment with admin credentials...")
        
        headers = get_auth_headers()
        if not headers.get("Authorization"):
            print("❌ Could not get admin token")
            return False
        
        # Create a test customer first
        booking_data = {
            "guest_name": "Auth Test User",
            "guest_email": "auth.test@example.com",
            "guest_phone": "+1000000000",
            "room_number": "301",
            "check_in_date": datetime.now().date().isoformat(),
            "check_out_date": (datetime.now().date() + timedelta(days=1)).isoformat(),
            "stay_type": "Night Stay",
            "booking_amount": 8000.0
        }
        
        booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
        if booking_response.status_code != 200:
            print(f"❌ Failed to create test booking: {booking_response.status_code}")
            return False
        
        booking = booking_response.json()
        booking_id = booking.get("id")
        
        # Check in the booking
        checkin_data = {
            "booking_id": booking_id,
            "advance_amount": 1000.0,
            "notes": "Auth test check-in"
        }
        
        checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=headers)
        if checkin_response.status_code != 200:
            print(f"❌ Failed to check in test booking: {checkin_response.status_code}")
            return False
        
        customer_id = checkin_response.json().get("customer_id")
        
        # Test advance payment with admin credentials
        advance_data = {
            "customer_id": customer_id,
            "amount": 500.0,
            "payment_method": "Cash",
            "notes": "Auth test advance payment"
        }
        
        advance_response = requests.post(f"{API_BASE}/advance-payment", json=advance_data, headers=headers)
        
        if advance_response.status_code == 200:
            print("✅ Advance payment with admin credentials PASSED")
            
            # Test cancel booking with admin credentials (should work)
            print("Test 2: Cancel booking with admin credentials...")
            
            cancel_response = requests.post(f"{API_BASE}/cancel/{booking_id}", headers=headers)
            
            if cancel_response.status_code == 200:
                print("✅ Cancel booking with admin credentials PASSED")
                
                # Test without authorization headers (should fail)
                print("Test 3: Testing endpoints without authorization...")
                
                # Test advance payment without auth
                advance_no_auth_response = requests.post(f"{API_BASE}/advance-payment", json=advance_data)
                
                if advance_no_auth_response.status_code in [401, 403]:
                    print("✅ Advance payment without auth correctly rejected")
                    
                    # Create another booking for cancel test
                    booking_response2 = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=headers)
                    if booking_response2.status_code == 200:
                        booking_id2 = booking_response2.json().get("id")
                        
                        # Test cancel without auth
                        cancel_no_auth_response = requests.post(f"{API_BASE}/cancel/{booking_id2}")
                        
                        if cancel_no_auth_response.status_code in [401, 403]:
                            print("✅ Cancel booking without auth correctly rejected")
                            print("✅ AUTHORIZATION TEST PASSED")
                            return True
                        else:
                            print(f"❌ Cancel booking without auth should be rejected, got: {cancel_no_auth_response.status_code}")
                            return False
                    else:
                        print("❌ Failed to create second test booking")
                        return False
                else:
                    print(f"❌ Advance payment without auth should be rejected, got: {advance_no_auth_response.status_code}")
                    return False
            else:
                print(f"❌ Cancel booking with admin credentials failed: {cancel_response.status_code}")
                return False
        else:
            print(f"❌ Advance payment with admin credentials failed: {advance_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Authorization test failed with exception: {e}")
        return False

def main():
    """Run all new enhancement tests"""
    print("Starting NEW ENHANCEMENTS Backend API Tests")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Advance Payment Collection
    test_results.append(("Advance Payment Collection", test_advance_payment_collection()))
    
    # Test 2: Admin Cancel Booking - Upcoming
    test_results.append(("Admin Cancel - Upcoming", test_admin_cancel_booking_upcoming()))
    
    # Test 3: Admin Cancel Booking - Checked-in
    test_results.append(("Admin Cancel - Checked-in", test_admin_cancel_booking_checked_in()))
    
    # Test 4: Booking Amount Recalculation
    test_results.append(("Booking Amount Recalculation", test_booking_amount_recalculation()))
    
    # Test 5: Authorization
    test_results.append(("Authorization", test_authorization()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY - NEW ENHANCEMENTS")
    print("=" * 70)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL NEW ENHANCEMENT TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)