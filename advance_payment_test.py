#!/usr/bin/env python3
"""
Focused test for advance payment real-time balance updates
"""

import requests
import json
from datetime import date, datetime, timedelta
import sys

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
API_BASE = f"{BASE_URL}/api"

# Global variables for authentication
auth_token = None
auth_headers = {}

def authenticate_admin():
    """Authenticate as admin user"""
    global auth_token, auth_headers
    
    try:
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        
        if response.status_code == 200:
            token_data = response.json()
            auth_token = token_data.get("access_token")
            auth_headers = {"Authorization": f"Bearer {auth_token}"}
            return True
        else:
            print(f"❌ Admin authentication failed - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Admin authentication failed - Exception: {e}")
        return False

def test_advance_payment_flow():
    """Test the complete advance payment flow"""
    print("🔍 TESTING ADVANCE PAYMENT REAL-TIME BALANCE UPDATE")
    print("=" * 60)
    
    # Step 1: Get initial balance
    print("\n📊 Step 1: Getting initial daily financial summary...")
    initial_response = requests.get(f"{API_BASE}/daily-financial-summary", headers=auth_headers)
    if initial_response.status_code != 200:
        print(f"❌ Failed to get initial balance - Status: {initial_response.status_code}")
        return False
    
    initial_data = initial_response.json()
    initial_cash = initial_data.get('cash_balance', 0)
    initial_bank = initial_data.get('bank_balance', 0)
    print(f"Initial Cash Balance: {initial_cash}")
    print(f"Initial Bank Balance: {initial_bank}")
    
    # Step 2: Create a test room
    print("\n🏗️ Step 2: Creating test room...")
    room_data = {
        "room_number": "ADVANCE_TEST",
        "room_type": "Double",
        "price_per_night": 8500.0,
        "max_occupancy": 2,
        "amenities": ["WiFi", "AC"]
    }
    
    room_response = requests.post(f"{API_BASE}/rooms", json=room_data, headers=auth_headers)
    if room_response.status_code != 200:
        print(f"❌ Failed to create test room - Status: {room_response.status_code}")
        return False
    
    print("✅ Test room created")
    
    # Step 3: Create booking
    print("\n📝 Step 3: Creating test booking...")
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    booking_data = {
        "guest_name": "Advance Test Guest",
        "guest_email": "advance@test.com",
        "guest_phone": "+1111111111",
        "room_number": "ADVANCE_TEST",
        "check_in_date": today.isoformat(),
        "check_out_date": tomorrow.isoformat(),
        "stay_type": "Night Stay",
        "booking_amount": 8500.0,
        "additional_notes": "Advance payment test"
    }
    
    booking_response = requests.post(f"{API_BASE}/bookings", json=booking_data, headers=auth_headers)
    if booking_response.status_code != 200:
        print(f"❌ Failed to create booking - Status: {booking_response.status_code}")
        print(f"Response: {booking_response.text}")
        return False
    
    booking = booking_response.json()
    print(f"✅ Booking created: {booking['id']}")
    
    # Step 4: Check-in with cash advance
    print("\n🏨 Step 4: Checking in with cash advance...")
    checkin_data = {
        "booking_id": booking['id'],
        "advance_amount": 1500.0,
        "payment_method": "Cash",
        "notes": "Cash advance payment test"
    }
    
    checkin_response = requests.post(f"{API_BASE}/checkin", json=checkin_data, headers=auth_headers)
    if checkin_response.status_code != 200:
        print(f"❌ Check-in failed - Status: {checkin_response.status_code}")
        print(f"Response: {checkin_response.text}")
        return False
    
    print("✅ Check-in successful")
    
    # Step 5: Check balance after check-in
    print("\n💰 Step 5: Checking balance after check-in...")
    after_checkin_response = requests.get(f"{API_BASE}/daily-financial-summary", headers=auth_headers)
    if after_checkin_response.status_code != 200:
        print(f"❌ Failed to get balance after check-in")
        return False
    
    after_checkin_data = after_checkin_response.json()
    after_checkin_cash = after_checkin_data.get('cash_balance', 0)
    after_checkin_bank = after_checkin_data.get('bank_balance', 0)
    print(f"After Check-in Cash Balance: {after_checkin_cash}")
    print(f"After Check-in Bank Balance: {after_checkin_bank}")
    
    # Verify cash increase
    cash_increase = after_checkin_cash - initial_cash
    print(f"Cash Balance Increase: {cash_increase} (Expected: 1500.0)")
    
    if abs(cash_increase - 1500.0) < 0.01:
        print("✅ Cash balance correctly increased after check-in")
    else:
        print("❌ Cash balance increase mismatch after check-in")
        return False
    
    # Step 6: Get checked-in customer
    print("\n👥 Step 6: Getting checked-in customer...")
    customers_response = requests.get(f"{API_BASE}/customers/checked-in", headers=auth_headers)
    if customers_response.status_code != 200:
        print(f"❌ Failed to get customers")
        return False
    
    customers = customers_response.json()
    test_customer = None
    for customer in customers:
        if customer.get('name') == 'Advance Test Guest':
            test_customer = customer
            break
    
    if not test_customer:
        print("❌ Test customer not found")
        return False
    
    print(f"✅ Found customer: {test_customer['name']} (ID: {test_customer['id']})")
    
    # Step 7: Collect additional advance via Card
    print("\n💳 Step 7: Collecting additional advance via Card...")
    advance_data = {
        "customer_id": test_customer['id'],
        "amount": 750.0,
        "payment_method": "Card",
        "notes": "Additional advance via card"
    }
    
    advance_response = requests.post(f"{API_BASE}/advance-payment", json=advance_data, headers=auth_headers)
    if advance_response.status_code != 200:
        print(f"❌ Advance payment failed - Status: {advance_response.status_code}")
        print(f"Response: {advance_response.text}")
        return False
    
    print("✅ Additional advance payment collected")
    
    # Step 8: Check final balance
    print("\n📈 Step 8: Checking final balance...")
    final_response = requests.get(f"{API_BASE}/daily-financial-summary", headers=auth_headers)
    if final_response.status_code != 200:
        print(f"❌ Failed to get final balance")
        return False
    
    final_data = final_response.json()
    final_cash = final_data.get('cash_balance', 0)
    final_bank = final_data.get('bank_balance', 0)
    print(f"Final Cash Balance: {final_cash}")
    print(f"Final Bank Balance: {final_bank}")
    
    # Verify bank increase
    bank_increase = final_bank - initial_bank
    print(f"Bank Balance Increase: {bank_increase} (Expected: 750.0)")
    
    if abs(bank_increase - 750.0) < 0.01:
        print("✅ Bank balance correctly increased after card advance")
    else:
        print("❌ Bank balance increase mismatch after card advance")
        return False
    
    # Verify cash remained the same
    cash_change_after_card = final_cash - after_checkin_cash
    print(f"Cash Balance Change After Card: {cash_change_after_card} (Expected: 0.0)")
    
    if abs(cash_change_after_card) < 0.01:
        print("✅ Cash balance correctly unchanged after card payment")
    else:
        print("❌ Cash balance unexpectedly changed after card payment")
        return False
    
    print("\n🎉 ADVANCE PAYMENT TEST PASSED!")
    print("✅ Check-in advance payment correctly updates cash balance")
    print("✅ Additional advance payment correctly updates bank balance")
    print("✅ Payment methods correctly route to cash vs bank balances")
    return True

def main():
    print("ADVANCE PAYMENT REAL-TIME BALANCE TEST")
    print("=" * 50)
    
    if not authenticate_admin():
        return False
    
    return test_advance_payment_flow()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)