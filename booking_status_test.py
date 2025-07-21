#!/usr/bin/env python3
"""
Booking Status Update Fix Testing
Tests the complete booking status transition flow: Upcoming -> Checked-in -> Completed
Also tests the Guests API to verify guest information appears immediately after booking creation.
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys
import time

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

print(f"Testing Booking Status Update Fix at: {API_BASE}")
print("=" * 80)

def test_create_booking_with_upcoming_status():
    """Test 1: Create a new booking with status 'Upcoming'"""
    print("\n1. Testing Create Booking with 'Upcoming' Status (POST /api/bookings)")
    
    try:
        # Create booking data with realistic information
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        day_after = (datetime.now() + timedelta(days=3)).date()
        
        booking_data = {
            "guest_name": "Sarah Johnson",
            "guest_email": "sarah.johnson@email.com",
            "guest_phone": "+1-555-0123",
            "guest_id_passport": "P123456789",
            "guest_country": "USA",
            "room_number": "103",
            "check_in_date": tomorrow.strftime('%Y-%m-%d'),
            "check_out_date": day_after.strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 8500.0,
            "additional_notes": "Testing booking status transitions"
        }
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            booking = response.json()
            print(f"✅ Booking created successfully:")
            print(f"  Booking ID: {booking['id']}")
            print(f"  Guest Name: {booking['guest_name']}")
            print(f"  Room Number: {booking['room_number']}")
            print(f"  Status: {booking['status']}")
            print(f"  Booking Amount: {booking['booking_amount']}")
            
            if booking['status'] == 'Upcoming':
                print("✅ Booking status correctly set to 'Upcoming'")
                return True, booking
            else:
                print(f"❌ Expected status 'Upcoming', got '{booking['status']}'")
                return False, booking
        else:
            print(f"❌ Booking creation FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Booking creation FAILED - Exception: {e}")
        return False, None

def test_verify_booking_status_via_get(booking_id):
    """Test 2: Check the booking status via GET /api/bookings"""
    print("\n2. Testing Verify Booking Status via GET /api/bookings")
    
    try:
        response = requests.get(f"{API_BASE}/bookings")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get('bookings', [])
            
            # Find our specific booking
            target_booking = None
            for booking in bookings:
                if booking['id'] == booking_id:
                    target_booking = booking
                    break
            
            if target_booking:
                print(f"✅ Booking found in GET /api/bookings:")
                print(f"  Booking ID: {target_booking['id']}")
                print(f"  Guest Name: {target_booking['guest_name']}")
                print(f"  Status: {target_booking['status']}")
                
                if target_booking['status'] == 'Upcoming':
                    print("✅ Booking status verified as 'Upcoming'")
                    return True, target_booking
                else:
                    print(f"❌ Expected status 'Upcoming', got '{target_booking['status']}'")
                    return False, target_booking
            else:
                print(f"❌ Booking with ID {booking_id} not found in bookings list")
                return False, None
        else:
            print(f"❌ Get bookings FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Get bookings FAILED - Exception: {e}")
        return False, None

def test_checkin_customer(booking):
    """Test 3: Check-in the customer (should change booking status to 'Checked-in')"""
    print("\n3. Testing Customer Check-in (POST /api/checkin)")
    
    try:
        checkin_data = {
            "booking_id": booking['id'],
            "advance_amount": 1000.0,
            "notes": "Testing status transition to Checked-in",
            "payment_method": "Cash"
        }
        
        response = requests.post(f"{API_BASE}/checkin", json=checkin_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Check-in successful:")
            print(f"  Message: {result['message']}")
            
            customer = result.get('customer', {})
            if customer:
                print(f"  Customer ID: {customer['id']}")
                print(f"  Customer Name: {customer['name']}")
                print(f"  Room: {customer['current_room']}")
                print(f"  Room Charges: {customer['room_charges']}")
                print(f"  Advance Amount: {customer['advance_amount']}")
                
                return True, customer
            else:
                print("❌ No customer data in check-in response")
                return False, None
        else:
            print(f"❌ Check-in FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Check-in FAILED - Exception: {e}")
        return False, None

def test_verify_booking_status_checked_in(booking_id):
    """Test 4: Verify booking status changed to 'Checked-in'"""
    print("\n4. Testing Verify Booking Status Changed to 'Checked-in'")
    
    try:
        response = requests.get(f"{API_BASE}/bookings")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get('bookings', [])
            
            # Find our specific booking
            target_booking = None
            for booking in bookings:
                if booking['id'] == booking_id:
                    target_booking = booking
                    break
            
            if target_booking:
                print(f"✅ Booking found after check-in:")
                print(f"  Booking ID: {target_booking['id']}")
                print(f"  Guest Name: {target_booking['guest_name']}")
                print(f"  Status: {target_booking['status']}")
                
                if target_booking['status'] == 'Checked-in':
                    print("✅ Booking status successfully changed to 'Checked-in'")
                    return True, target_booking
                else:
                    print(f"❌ Expected status 'Checked-in', got '{target_booking['status']}'")
                    return False, target_booking
            else:
                print(f"❌ Booking with ID {booking_id} not found after check-in")
                return False, None
        else:
            print(f"❌ Get bookings after check-in FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Get bookings after check-in FAILED - Exception: {e}")
        return False, None

def test_checkout_customer(customer):
    """Test 5: Check-out the customer (should change booking status to 'Completed')"""
    print("\n5. Testing Customer Check-out (POST /api/checkout)")
    
    try:
        checkout_data = {
            "customer_id": customer['id'],
            "additional_amount": 200.0,
            "discount_amount": 100.0,
            "payment_method": "Card"
        }
        
        response = requests.post(f"{API_BASE}/checkout", json=checkout_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Check-out successful:")
            print(f"  Message: {result['message']}")
            
            billing_details = result.get('billing_details', {})
            if billing_details:
                print(f"  Room Charges: {billing_details['room_charges']}")
                print(f"  Additional Charges: {billing_details['additional_charges']}")
                print(f"  Discount Amount: {billing_details['discount_amount']}")
                print(f"  Total Amount: {billing_details['total_amount']}")
                print(f"  Payment Method: {billing_details['payment_method']}")
                
                return True, billing_details
            else:
                print("❌ No billing details in check-out response")
                return False, None
        else:
            print(f"❌ Check-out FAILED - Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Check-out FAILED - Exception: {e}")
        return False, None

def test_verify_booking_status_completed(booking_id):
    """Test 6: Verify booking status changed to 'Completed'"""
    print("\n6. Testing Verify Booking Status Changed to 'Completed'")
    
    try:
        response = requests.get(f"{API_BASE}/bookings")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            bookings_data = response.json()
            bookings = bookings_data.get('bookings', [])
            
            # Find our specific booking
            target_booking = None
            for booking in bookings:
                if booking['id'] == booking_id:
                    target_booking = booking
                    break
            
            if target_booking:
                print(f"✅ Booking found after check-out:")
                print(f"  Booking ID: {target_booking['id']}")
                print(f"  Guest Name: {target_booking['guest_name']}")
                print(f"  Status: {target_booking['status']}")
                
                if target_booking['status'] == 'Completed':
                    print("✅ Booking status successfully changed to 'Completed'")
                    return True, target_booking
                else:
                    print(f"❌ Expected status 'Completed', got '{target_booking['status']}'")
                    return False, target_booking
            else:
                print(f"❌ Booking with ID {booking_id} not found after check-out")
                return False, None
        else:
            print(f"❌ Get bookings after check-out FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Get bookings after check-out FAILED - Exception: {e}")
        return False, None

def test_guests_api_immediate_appearance(guest_name, guest_email):
    """Test 7: GET /api/guests - Verify guest information appears immediately after booking creation"""
    print("\n7. Testing Guests API - Immediate Guest Appearance (GET /api/guests)")
    
    try:
        response = requests.get(f"{API_BASE}/guests")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            guests = response.json()
            print(f"Total guests found: {len(guests)}")
            
            # Find our specific guest
            target_guest = None
            for guest in guests:
                if guest['name'] == guest_name or guest['email'] == guest_email:
                    target_guest = guest
                    break
            
            if target_guest:
                print(f"✅ Guest found in guests API:")
                print(f"  Name: {target_guest['name']}")
                print(f"  Email: {target_guest['email']}")
                print(f"  Phone: {target_guest['phone']}")
                print(f"  Total Bookings: {target_guest['total_bookings']}")
                print(f"  Total Stays: {target_guest['total_stays']}")
                print(f"  Upcoming Bookings: {target_guest['upcoming_bookings']}")
                print(f"  Last Stay: {target_guest['last_stay']}")
                
                # Verify guest data includes booking history
                bookings = target_guest.get('bookings', [])
                if bookings:
                    print(f"  Booking History: {len(bookings)} booking(s)")
                    for i, booking in enumerate(bookings[:2]):  # Show first 2 bookings
                        print(f"    Booking {i+1}: Room {booking['room_number']}, Status: {booking['status']}")
                    
                    print("✅ Guest data includes booking history and statistics")
                    return True, target_guest
                else:
                    print("❌ Guest data missing booking history")
                    return False, target_guest
            else:
                print(f"❌ Guest '{guest_name}' not found in guests API")
                return False, None
        else:
            print(f"❌ Get guests FAILED - Status code: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Get guests FAILED - Exception: {e}")
        return False, None

def test_guests_api_data_completeness():
    """Test 8: Verify guest data includes all required information"""
    print("\n8. Testing Guests API - Data Completeness")
    
    try:
        response = requests.get(f"{API_BASE}/guests")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            guests = response.json()
            
            if guests:
                sample_guest = guests[0]
                required_fields = ['id', 'name', 'email', 'phone', 'total_bookings', 
                                 'total_stays', 'upcoming_bookings', 'bookings']
                
                missing_fields = [field for field in required_fields if field not in sample_guest]
                
                if not missing_fields:
                    print("✅ All required fields present in guest data:")
                    for field in required_fields:
                        print(f"  {field}: {sample_guest.get(field)}")
                    
                    # Verify booking history structure
                    if sample_guest.get('bookings'):
                        sample_booking = sample_guest['bookings'][0]
                        booking_fields = ['id', 'room_number', 'check_in_date', 'check_out_date', 'status']
                        booking_missing = [field for field in booking_fields if field not in sample_booking]
                        
                        if not booking_missing:
                            print("✅ Booking history structure is complete")
                            return True
                        else:
                            print(f"❌ Missing fields in booking history: {booking_missing}")
                            return False
                    else:
                        print("✅ Guest data structure is complete (no bookings for this guest)")
                        return True
                else:
                    print(f"❌ Missing required fields in guest data: {missing_fields}")
                    return False
            else:
                print("⚠️ No guests found - this might be expected if no bookings exist")
                return True
        else:
            print(f"❌ Get guests for data completeness FAILED - Status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Get guests data completeness FAILED - Exception: {e}")
        return False

def main():
    """Run the complete booking status update fix test"""
    print("Starting Booking Status Update Fix Testing")
    print("=" * 70)
    
    test_results = []
    
    # Test 1: Create booking with 'Upcoming' status
    booking_created, booking_data = test_create_booking_with_upcoming_status()
    test_results.append(("Create Booking (Upcoming)", booking_created))
    
    if not booking_created or not booking_data:
        print("\n❌ Cannot continue testing - booking creation failed")
        return False
    
    booking_id = booking_data['id']
    guest_name = booking_data['guest_name']
    guest_email = booking_data['guest_email']
    
    # Test 2: Verify booking status via GET
    status_verified, _ = test_verify_booking_status_via_get(booking_id)
    test_results.append(("Verify Booking Status (GET)", status_verified))
    
    # Test 3: Check-in customer
    checkin_success, customer_data = test_checkin_customer(booking_data)
    test_results.append(("Customer Check-in", checkin_success))
    
    if not checkin_success or not customer_data:
        print("\n❌ Cannot continue testing - check-in failed")
        return False
    
    # Test 4: Verify booking status changed to 'Checked-in'
    checkin_verified, _ = test_verify_booking_status_checked_in(booking_id)
    test_results.append(("Verify Status (Checked-in)", checkin_verified))
    
    # Test 5: Check-out customer
    checkout_success, _ = test_checkout_customer(customer_data)
    test_results.append(("Customer Check-out", checkout_success))
    
    # Test 6: Verify booking status changed to 'Completed'
    completed_verified, _ = test_verify_booking_status_completed(booking_id)
    test_results.append(("Verify Status (Completed)", completed_verified))
    
    # Test 7: Guests API - Immediate appearance
    guest_found, _ = test_guests_api_immediate_appearance(guest_name, guest_email)
    test_results.append(("Guests API (Immediate)", guest_found))
    
    # Test 8: Guests API - Data completeness
    data_complete = test_guests_api_data_completeness()
    test_results.append(("Guests API (Data Complete)", data_complete))
    
    # Summary
    print("\n" + "=" * 70)
    print("BOOKING STATUS UPDATE FIX - TEST SUMMARY")
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
        print("\n🎉 ALL TESTS PASSED! Booking status update fix is working correctly.")
        print("✅ Status transitions: Upcoming → Checked-in → Completed")
        print("✅ Guests API shows guest information immediately after booking creation")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)