#!/usr/bin/env python3
"""
Detailed Status Investigation Test
Investigates the exact status values used in the system to identify inconsistencies.
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

print(f"Investigating Status Values at: {API_BASE}")
print("=" * 80)

def authenticate():
    """Authenticate as admin user"""
    print("\n🔐 Authenticating as admin user...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ Authentication successful")
                return f"Bearer {token}"
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Authentication failed - Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication failed - Exception: {e}")
        return None

def investigate_booking_statuses():
    """Investigate all booking statuses in the system"""
    print("\n🔍 Investigating booking statuses...")
    
    try:
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/bookings", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            bookings = data.get("bookings", [])
            
            print(f"Total bookings found: {len(bookings)}")
            
            # Collect all unique statuses
            statuses = set()
            status_examples = {}
            
            for booking in bookings:
                status = booking.get('status', 'Unknown')
                statuses.add(status)
                
                if status not in status_examples:
                    status_examples[status] = {
                        'id': booking.get('id'),
                        'guest': booking.get('guest_name'),
                        'room': booking.get('room_number')
                    }
            
            print(f"\nUnique booking statuses found:")
            for status in sorted(statuses):
                example = status_examples[status]
                print(f"  '{status}' - Example: {example['guest']} in room {example['room']} (ID: {example['id'][:8]}...)")
            
            return statuses, bookings
        else:
            print(f"❌ Failed to get bookings - Status code: {response.status_code}")
            return set(), []
    except Exception as e:
        print(f"❌ Investigation failed - Exception: {e}")
        return set(), []

def test_edit_with_different_statuses(bookings):
    """Test editing bookings with different statuses"""
    print("\n🧪 Testing edit functionality with different statuses...")
    
    headers = {"Authorization": auth_token}
    
    # Group bookings by status
    status_groups = {}
    for booking in bookings:
        status = booking.get('status', 'Unknown')
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(booking)
    
    for status, booking_list in status_groups.items():
        if not booking_list:
            continue
            
        test_booking = booking_list[0]  # Use first booking of this status
        booking_id = test_booking.get('id')
        
        print(f"\nTesting edit for status '{status}':")
        print(f"  Booking ID: {booking_id}")
        print(f"  Guest: {test_booking.get('guest_name')}")
        print(f"  Room: {test_booking.get('room_number')}")
        
        # Try to edit the booking
        update_data = {
            "additional_notes": f"Test edit for {status} status - {datetime.now().isoformat()}"
        }
        
        try:
            response = requests.put(f"{API_BASE}/bookings/{booking_id}", json=update_data, headers=headers)
            print(f"  Edit Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Edit successful: {result.get('message')}")
            elif response.status_code == 400:
                error_data = response.json()
                error_detail = error_data.get("detail", "")
                print(f"  ⚠️ Edit blocked (expected): {error_detail}")
            elif response.status_code == 404:
                print(f"  ❌ Booking not found error (BUG!)")
            else:
                print(f"  ❌ Unexpected status code: {response.status_code}")
                print(f"  Response: {response.text}")
        except Exception as e:
            print(f"  ❌ Edit test failed - Exception: {e}")

def investigate_customers():
    """Investigate customer records"""
    print("\n👥 Investigating customer records...")
    
    try:
        headers = {"Authorization": auth_token}
        response = requests.get(f"{API_BASE}/customers/checked-in", headers=headers)
        
        if response.status_code == 200:
            customers = response.json()
            print(f"Total checked-in customers: {len(customers)}")
            
            for i, customer in enumerate(customers[:5]):  # Show first 5
                print(f"  Customer {i+1}: {customer.get('name')} in room {customer.get('current_room')}")
            
            return customers
        else:
            print(f"❌ Failed to get customers - Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Customer investigation failed - Exception: {e}")
        return []

def main():
    """Run the status investigation"""
    print("🔍 STATUS VALUES INVESTIGATION")
    print("=" * 50)
    
    global auth_token
    
    # Authenticate first
    auth_token = authenticate()
    if not auth_token:
        print("❌ Cannot proceed without authentication")
        return False
    
    # Investigate booking statuses
    statuses, bookings = investigate_booking_statuses()
    
    # Test editing with different statuses
    if bookings:
        test_edit_with_different_statuses(bookings)
    
    # Investigate customer records
    customers = investigate_customers()
    
    print("\n" + "=" * 70)
    print("🔍 INVESTIGATION SUMMARY")
    print("=" * 70)
    print(f"Unique booking statuses found: {sorted(statuses)}")
    print(f"Total bookings: {len(bookings)}")
    print(f"Total checked-in customers: {len(customers)}")
    
    # Check for status inconsistencies
    print("\n🚨 POTENTIAL ISSUES:")
    if 'Checked In' in statuses and 'Checked-in' in statuses:
        print("❌ Status inconsistency: Both 'Checked In' and 'Checked-in' found!")
    elif 'Checked-in' in statuses:
        print("⚠️ Using 'Checked-in' (with hyphen) status")
    elif 'Checked In' in statuses:
        print("⚠️ Using 'Checked In' (with space) status")
    else:
        print("✅ No obvious status inconsistencies found")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)