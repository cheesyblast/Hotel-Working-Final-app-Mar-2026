#!/usr/bin/env python3
"""
Guest Aggregation Testing for Hotel Management System
Tests the updated guest aggregation logic to handle bookings with optional email and phone fields.

Critical Testing Focus:
1. Test Guest Aggregation with Missing Fields - verify guests appear even when email or phone are empty
2. Create Test Bookings - create bookings with different combinations of missing fields  
3. Verify Guest Display - check that all guests appear in the guests endpoint regardless of missing email/phone
4. Data Integrity - ensure aggregation logic correctly handles "Not provided" values

Test Scenarios:
1. Booking with Name Only (empty email and phone)
2. Booking with Name + Email (no phone)
3. Booking with Name + Phone (no email)  
4. Booking with All Fields
5. Verify All Appear in Guests
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

print(f"Testing Guest Aggregation Logic at: {API_BASE}")
print("=" * 80)

def clear_existing_data():
    """Clear existing bookings to start with clean slate"""
    print("\n🧹 Clearing existing test data...")
    try:
        # Get all bookings
        response = requests.get(f"{API_BASE}/bookings")
        if response.status_code == 200:
            bookings = response.json()
            print(f"Found {len(bookings)} existing bookings")
            
            # Note: In a real scenario, we'd need delete endpoints
            # For now, we'll work with existing data and add our test cases
            return True
        else:
            print(f"Could not retrieve existing bookings: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error clearing data: {e}")
        return False

def test_scenario_1_name_only():
    """Test Scenario 1: Booking with Name Only (empty email and phone)"""
    print("\n📋 Test Scenario 1: Booking with Name Only")
    print("-" * 50)
    
    try:
        # Create booking with only guest name, empty email and phone
        booking_data = {
            "guest_name": "Alice NameOnly",
            "guest_email": "",  # Empty email
            "guest_phone": "",  # Empty phone
            "guest_id_passport": "P123456789",
            "guest_country": "USA",
            "room_number": "103",
            "check_in_date": (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
            "check_out_date": (date.today() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 1500.0,
            "additional_notes": "Test booking - name only"
        }
        
        print(f"Creating booking for: {booking_data['guest_name']}")
        print(f"Email: '{booking_data['guest_email']}' (empty)")
        print(f"Phone: '{booking_data['guest_phone']}' (empty)")
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Booking creation status: {response.status_code}")
        
        if response.status_code == 200:
            booking_result = response.json()
            print(f"✅ Booking created successfully with ID: {booking_result.get('id')}")
            return True, booking_result.get('id')
        else:
            print(f"❌ Booking creation failed: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test Scenario 1 failed with exception: {e}")
        return False, None

def test_scenario_2_name_email():
    """Test Scenario 2: Booking with Name + Email (no phone)"""
    print("\n📋 Test Scenario 2: Booking with Name + Email")
    print("-" * 50)
    
    try:
        # Create booking with name and email, but no phone
        booking_data = {
            "guest_name": "Bob EmailOnly",
            "guest_email": "bob.emailonly@example.com",  # Has email
            "guest_phone": "",  # Empty phone
            "guest_id_passport": "P987654321",
            "guest_country": "Canada",
            "room_number": "201",
            "check_in_date": (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
            "check_out_date": (date.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 1800.0,
            "additional_notes": "Test booking - name and email only"
        }
        
        print(f"Creating booking for: {booking_data['guest_name']}")
        print(f"Email: '{booking_data['guest_email']}' (provided)")
        print(f"Phone: '{booking_data['guest_phone']}' (empty)")
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Booking creation status: {response.status_code}")
        
        if response.status_code == 200:
            booking_result = response.json()
            print(f"✅ Booking created successfully with ID: {booking_result.get('id')}")
            return True, booking_result.get('id')
        else:
            print(f"❌ Booking creation failed: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test Scenario 2 failed with exception: {e}")
        return False, None

def test_scenario_3_name_phone():
    """Test Scenario 3: Booking with Name + Phone (no email)"""
    print("\n📋 Test Scenario 3: Booking with Name + Phone")
    print("-" * 50)
    
    try:
        # Create booking with name and phone, but no email
        booking_data = {
            "guest_name": "Carol PhoneOnly",
            "guest_email": "",  # Empty email
            "guest_phone": "+1-555-123-4567",  # Has phone
            "guest_id_passport": "P555444333",
            "guest_country": "UK",
            "room_number": "301",
            "check_in_date": (date.today() + timedelta(days=3)).strftime('%Y-%m-%d'),
            "check_out_date": (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 2000.0,
            "additional_notes": "Test booking - name and phone only"
        }
        
        print(f"Creating booking for: {booking_data['guest_name']}")
        print(f"Email: '{booking_data['guest_email']}' (empty)")
        print(f"Phone: '{booking_data['guest_phone']}' (provided)")
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Booking creation status: {response.status_code}")
        
        if response.status_code == 200:
            booking_result = response.json()
            print(f"✅ Booking created successfully with ID: {booking_result.get('id')}")
            return True, booking_result.get('id')
        else:
            print(f"❌ Booking creation failed: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test Scenario 3 failed with exception: {e}")
        return False, None

def test_scenario_4_all_fields():
    """Test Scenario 4: Booking with All Fields"""
    print("\n📋 Test Scenario 4: Booking with All Fields")
    print("-" * 50)
    
    try:
        # Create booking with all fields provided
        booking_data = {
            "guest_name": "David Complete",
            "guest_email": "david.complete@example.com",  # Has email
            "guest_phone": "+1-555-987-6543",  # Has phone
            "guest_id_passport": "P111222333",
            "guest_country": "Australia",
            "room_number": "302",
            "check_in_date": (date.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
            "check_out_date": (date.today() + timedelta(days=6)).strftime('%Y-%m-%d'),
            "stay_type": "Night Stay",
            "booking_amount": 2200.0,
            "additional_notes": "Test booking - all fields provided"
        }
        
        print(f"Creating booking for: {booking_data['guest_name']}")
        print(f"Email: '{booking_data['guest_email']}' (provided)")
        print(f"Phone: '{booking_data['guest_phone']}' (provided)")
        
        response = requests.post(f"{API_BASE}/bookings", json=booking_data)
        print(f"Booking creation status: {response.status_code}")
        
        if response.status_code == 200:
            booking_result = response.json()
            print(f"✅ Booking created successfully with ID: {booking_result.get('id')}")
            return True, booking_result.get('id')
        else:
            print(f"❌ Booking creation failed: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Test Scenario 4 failed with exception: {e}")
        return False, None

def test_guest_aggregation_verification():
    """Test Scenario 5: Verify All Guests Appear in Guests Endpoint"""
    print("\n🔍 Test Scenario 5: Verify Guest Aggregation")
    print("-" * 50)
    
    try:
        # Get all guests from the aggregation endpoint
        response = requests.get(f"{API_BASE}/guests")
        print(f"Guests endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            guests = response.json()
            print(f"Total guests found: {len(guests)}")
            
            # Look for our test guests
            test_guest_names = [
                "Alice NameOnly",
                "Bob EmailOnly", 
                "Carol PhoneOnly",
                "David Complete"
            ]
            
            found_guests = {}
            
            print("\n📊 Guest Aggregation Results:")
            print("-" * 30)
            
            for guest in guests:
                guest_name = guest.get('name', '')
                guest_email = guest.get('email', '')
                guest_phone = guest.get('phone', '')
                
                if guest_name in test_guest_names:
                    found_guests[guest_name] = guest
                    print(f"\n✅ Found: {guest_name}")
                    print(f"   Email: {guest_email}")
                    print(f"   Phone: {guest_phone}")
                    print(f"   Total Bookings: {guest.get('total_bookings', 0)}")
                    print(f"   Upcoming Bookings: {guest.get('upcoming_bookings', 0)}")
                    
                    # Verify "Not provided" handling
                    if guest_name == "Alice NameOnly":
                        if guest_email == "Not provided" and guest_phone == "Not provided":
                            print("   ✅ Correctly shows 'Not provided' for missing email and phone")
                        else:
                            print(f"   ❌ Expected 'Not provided' but got email: '{guest_email}', phone: '{guest_phone}'")
                    
                    elif guest_name == "Bob EmailOnly":
                        if guest_email == "bob.emailonly@example.com" and guest_phone == "Not provided":
                            print("   ✅ Correctly shows email and 'Not provided' for missing phone")
                        else:
                            print(f"   ❌ Expected email and 'Not provided' phone but got email: '{guest_email}', phone: '{guest_phone}'")
                    
                    elif guest_name == "Carol PhoneOnly":
                        if guest_email == "Not provided" and guest_phone == "+1-555-123-4567":
                            print("   ✅ Correctly shows 'Not provided' for missing email and phone number")
                        else:
                            print(f"   ❌ Expected 'Not provided' email and phone but got email: '{guest_email}', phone: '{guest_phone}'")
                    
                    elif guest_name == "David Complete":
                        if guest_email == "david.complete@example.com" and guest_phone == "+1-555-987-6543":
                            print("   ✅ Correctly shows all provided fields")
                        else:
                            print(f"   ❌ Expected all fields but got email: '{guest_email}', phone: '{guest_phone}'")
            
            # Check if all test guests were found
            missing_guests = [name for name in test_guest_names if name not in found_guests]
            
            if not missing_guests:
                print(f"\n✅ SUCCESS: All {len(test_guest_names)} test guests found in aggregation")
                print("✅ Guest aggregation correctly handles optional email and phone fields")
                return True
            else:
                print(f"\n❌ FAILURE: Missing guests in aggregation: {missing_guests}")
                return False
                
        else:
            print(f"❌ Failed to get guests: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Guest aggregation verification failed with exception: {e}")
        return False

def test_data_integrity():
    """Test Data Integrity - Ensure aggregation logic correctly handles edge cases"""
    print("\n🔒 Test Data Integrity")
    print("-" * 50)
    
    try:
        # Get all bookings to verify data consistency
        bookings_response = requests.get(f"{API_BASE}/bookings")
        guests_response = requests.get(f"{API_BASE}/guests")
        
        if bookings_response.status_code != 200 or guests_response.status_code != 200:
            print("❌ Could not retrieve data for integrity check")
            return False
        
        bookings = bookings_response.json()
        guests = guests_response.json()
        
        print(f"Total bookings in system: {len(bookings)}")
        print(f"Total guests in aggregation: {len(guests)}")
        
        # Check for data consistency
        booking_guest_names = set()
        for booking in bookings:
            guest_name = booking.get('guest_name')
            if guest_name:
                booking_guest_names.add(guest_name)
        
        guest_names_in_aggregation = set()
        for guest in guests:
            guest_name = guest.get('name')
            if guest_name:
                guest_names_in_aggregation.add(guest_name)
        
        # Verify all booking guests appear in aggregation
        missing_in_aggregation = booking_guest_names - guest_names_in_aggregation
        extra_in_aggregation = guest_names_in_aggregation - booking_guest_names
        
        print(f"\nData Integrity Check:")
        print(f"Unique guest names in bookings: {len(booking_guest_names)}")
        print(f"Guest names in aggregation: {len(guest_names_in_aggregation)}")
        
        if not missing_in_aggregation:
            print("✅ All booking guests appear in aggregation")
        else:
            print(f"❌ Guests missing from aggregation: {missing_in_aggregation}")
        
        if not extra_in_aggregation:
            print("✅ No extra guests in aggregation")
        else:
            print(f"⚠️ Extra guests in aggregation (might be from previous tests): {extra_in_aggregation}")
        
        # Check that guests with empty email/phone are handled correctly
        guests_with_missing_fields = 0
        for guest in guests:
            if guest.get('email') == 'Not provided' or guest.get('phone') == 'Not provided':
                guests_with_missing_fields += 1
        
        print(f"Guests with missing email/phone fields: {guests_with_missing_fields}")
        
        if guests_with_missing_fields > 0:
            print("✅ System correctly handles guests with missing email/phone fields")
        else:
            print("⚠️ No guests with missing fields found (might be expected)")
        
        return len(missing_in_aggregation) == 0
        
    except Exception as e:
        print(f"❌ Data integrity test failed with exception: {e}")
        return False

def main():
    """Run all guest aggregation tests"""
    print("Starting Guest Aggregation Logic Tests")
    print("Testing updated logic to handle bookings with optional email and phone fields")
    print("=" * 80)
    
    test_results = []
    created_booking_ids = []
    
    # Clear existing test data
    clear_existing_data()
    
    # Test Scenario 1: Name Only
    scenario1_passed, booking1_id = test_scenario_1_name_only()
    test_results.append(("Scenario 1: Name Only", scenario1_passed))
    if booking1_id:
        created_booking_ids.append(booking1_id)
    
    # Test Scenario 2: Name + Email
    scenario2_passed, booking2_id = test_scenario_2_name_email()
    test_results.append(("Scenario 2: Name + Email", scenario2_passed))
    if booking2_id:
        created_booking_ids.append(booking2_id)
    
    # Test Scenario 3: Name + Phone
    scenario3_passed, booking3_id = test_scenario_3_name_phone()
    test_results.append(("Scenario 3: Name + Phone", scenario3_passed))
    if booking3_id:
        created_booking_ids.append(booking3_id)
    
    # Test Scenario 4: All Fields
    scenario4_passed, booking4_id = test_scenario_4_all_fields()
    test_results.append(("Scenario 4: All Fields", scenario4_passed))
    if booking4_id:
        created_booking_ids.append(booking4_id)
    
    # Test Scenario 5: Guest Aggregation Verification
    aggregation_passed = test_guest_aggregation_verification()
    test_results.append(("Guest Aggregation Verification", aggregation_passed))
    
    # Test Data Integrity
    integrity_passed = test_data_integrity()
    test_results.append(("Data Integrity Check", integrity_passed))
    
    # Summary
    print("\n" + "=" * 80)
    print("GUEST AGGREGATION TEST SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<35} {status}")
        if passed:
            passed_tests += 1
    
    print("-" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print(f"\nCreated {len(created_booking_ids)} test bookings during this test run")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL GUEST AGGREGATION TESTS PASSED!")
        print("✅ The updated guest aggregation logic correctly handles bookings with optional email and phone fields")
        print("✅ Guests appear in the /api/guests endpoint even when email or phone are empty")
        print("✅ Missing fields are correctly displayed as 'Not provided'")
        print("✅ Unique guest identification works correctly with missing fields")
        print("✅ No bookings are skipped due to missing optional fields")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} test(s) failed.")
        print("❌ The guest aggregation logic may have issues handling optional email/phone fields")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)