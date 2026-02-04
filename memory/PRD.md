# Hotel Management System - Product Requirements Document

## Original Problem Statement
Build a comprehensive hotel management system for managing rooms, bookings, customers, restaurant orders, income/expenses, and reporting.

## Core Features Implemented
- Room management (availability, status, pricing)
- Booking management (upcoming, checked-in, completed)
- Customer check-in/check-out workflow
- Restaurant POS with service charge adjustment
- Income and expense tracking
- Financial reporting
- Setup wizard with initial cash/bank balance
- User authentication with JWT
- Commission tracking for booking channels
- Stay modification (extend stay, early checkout)

## User Personas
1. **Hotel Administrator** - Manages overall hotel operations, settings, user accounts
2. **Front Desk Staff** - Handles bookings, check-ins, check-outs
3. **Restaurant Manager** - Manages restaurant orders and menu

## Tech Stack
- **Frontend**: React.js with Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT with bcrypt

---

## Changelog

### 2026-02-04 - Stay Modification Bug Fixes
**Issues Fixed**: 4 bugs related to Extend Stay and Early Checkout features, plus Edit Booking conflict check

**Changes Implemented**:
1. **Booking Conflict Check for Extend Stay**:
   - Added conflict detection when extending stay
   - Uses `check_room_availability_for_booking()` with `skip_occupied_check=True` parameter
   - Prevents extending into periods where another booking exists

2. **Booking Conflict Check for Edit Booking** (NEW):
   - Added conflict detection when editing booking dates
   - Prevents changing dates that would overlap with other bookings for same room
   - Uses same `check_room_availability_for_booking()` function with `exclude_booking_id`

3. **Early Checkout Rate Fix**:
   - Now uses customer's booked rate per night (calculated from booking)
   - Previously was incorrectly using room's default rate
   - Rate is calculated as: `original_room_charges / planned_nights`

4. **UI Number Formatting**:
   - Applied `Math.round()` and `toLocaleString()` to monetary values
   - Numbers now display with thousand separators (e.g., "LKR 71,500")
   - Applied to Early Checkout modal: rate per night, charges, refund amounts

5. **Extend Stay Modal Enhancement**:
   - Added check-in date to the display
   - Current charges now formatted with thousand separators

**Files Modified**:
- `/app/backend/server.py`:
  - `check_room_availability_for_booking()` - Added `skip_occupied_check` parameter
  - `extend_customer_stay()` - Added conflict check before extending
  - `update_booking()` - Added conflict check when dates are changed
  - `early_checkout_customer()` - Now calculates rate from booking, not room
- `/app/frontend/src/App.js`:
  - Extend Stay modal - Added check-in date, formatted charges
  - Early Checkout modal - Applied `Math.round().toLocaleString()` to all amounts

**Tests**: All 9 tests pass (100% backend, 100% frontend)
**Test File**: `/app/backend/tests/test_stay_modifications.py`

### 2026-01-05 - Past Date Booking Bug Fix
**Issue Fixed**: Creating past-date bookings for already checked-in customers was failing with 401 Unauthorized error.

**Root Causes Identified & Fixed**:
1. **Login Race Condition** (Frontend): Axios Authorization header wasn't set before making `/api/auth/me` call after login. Fixed by setting header immediately in login function before subsequent requests.
2. **Status Inconsistency** (Backend): Booking status values were inconsistent - "Checked-in" (hyphen) vs "Checked In" (space) used interchangeably. Standardized all status checks to handle both variants.

**Files Modified**:
- `/app/frontend/src/App.js` - Login function now sets Authorization header immediately
- `/app/backend/server.py` - Status checks updated to handle both variants

**Tests**: All 6 backend tests pass (100% success rate)

### 2026-01-20 - Stay Extension & Early Checkout Feature
**Feature**: Added ability to extend stay or checkout early with proper billing adjustments

**Changes Implemented**:
1. **Extend Stay**: 
   - New "Extend Stay" option in customer Actions dropdown
   - Modal shows current guest info, checkout date, and charges
   - Calculates additional nights and charges automatically
   - Updates customer record, booking, and room checkout date

2. **Early Checkout**:
   - New "Early Checkout" option in customer Actions dropdown
   - Preview modal shows planned vs actual charges breakdown
   - Option to refund excess amount if customer overpaid
   - Records refund as expense if given
   - Automatically marks restaurant orders as paid

3. **Backend Endpoints**:
   - `POST /api/extend-stay` - Extend customer stay
   - `POST /api/early-checkout` - Process early checkout with refund handling
   - `GET /api/customer/{id}/checkout-preview` - Preview checkout calculations

**Files Modified**:
- `/app/backend/server.py`:
  - Added ExtendStayRequest and EarlyCheckoutRequest models
  - Added extend-stay, early-checkout, and checkout-preview endpoints
- `/app/frontend/src/App.js`:
  - Added state for extend stay and early checkout modals
  - Added handler functions for extend/early checkout
  - Added "Extend Stay" and "Early Checkout" buttons to customer dropdown
  - Created Extend Stay modal with date picker
  - Created Early Checkout modal with charges breakdown and refund option

### 2026-01-07 - Commission Tracking Feature
**Feature**: Added booking channel commission tracking system

**Changes Implemented**:
1. **Commission Field in Bookings**: Added `commission_amount` field to Booking model and booking form
2. **Commissions Page**: New page accessible from navigation bar (before Reports)
   - Channel commission summary with real-time totals
   - Monthly breakdown table for year-over-year tracking
   - Detailed view per channel showing individual bookings
3. **API Endpoints**:
   - `GET /api/commissions/summary` - Summary by channel with filters
   - `GET /api/commissions/monthly-breakdown` - Monthly totals for a year
   - `GET /api/commissions/channel-details/{channel_id}` - Booking details per channel

**Files Modified**:
- `/app/backend/server.py`:
  - Added `commission_amount` to Booking and BookingCreate models
  - Added 3 new API endpoints for commission tracking
- `/app/frontend/src/App.js`:
  - Added Commission field to new booking form
  - Created Commissions component with summary, breakdown, and details views
  - Added "Commissions" navigation tab before "Reports"

### 2026-01-05 - Restaurant Integration with Room Checkout
**Issue Fixed**: Restaurant room service bills were not showing up during customer checkout.

**Changes Implemented**:
1. **Auto-add restaurant charges**: Room service orders now automatically add to the customer's `restaurant_charges` when created
2. **Display in checkout**: Checkout modal now shows "Restaurant Charges" line item in billing details
3. **Auto-mark as paid**: After checkout, all pending restaurant orders for that room are automatically marked as "Paid" with payment method "Room Bill - [payment method]"
4. **Total calculation**: Updated `calculateTotal()` to include restaurant charges

**Files Modified**:
- `/app/backend/server.py`:
  - `create_restaurant_order` - Auto-adds charges to customer record for room service
  - `checkout_customer` - Auto-marks restaurant orders as paid, returns restaurant_charges in billing
- `/app/frontend/src/App.js`:
  - `calculateTotal` - Now includes restaurant_charges
  - Checkout modal - Added "Restaurant Charges" display line

---

## Prioritized Backlog

### P0 - Completed & Tested
- [x] Past-date booking bug fix (COMPLETED)
- [x] Restaurant charges appearing at checkout (COMPLETED)
- [x] Commission tracking feature (COMPLETED)
- [x] Extend Stay and Early Checkout features (COMPLETED)
- [x] Extend Stay conflict check bug fix (COMPLETED)
- [x] Early Checkout rate calculation fix (COMPLETED)
- [x] UI number formatting improvements (COMPLETED)

### P1 - Upcoming Tasks
- [ ] User verification of previously completed features
- [ ] Make application mobile responsive (starting with Restaurant component)
- [ ] Export commission reports to Excel/PDF
- [ ] Email notifications for commission due dates

### P2 - Future Enhancements
- [ ] Guest feedback/review system
- [ ] Room maintenance tracking
- [ ] Advanced reporting and analytics
- [ ] Refactor App.js into smaller components

---

## Key Technical Decisions
1. Using "Checked In" (with space) as the canonical checked-in status
2. JWT tokens expire after 30 minutes (configurable)
3. Past-date bookings can be created with either "Upcoming" or "Checked In" status
4. MongoDB ObjectIds are excluded from API responses to ensure JSON serialization
5. Stay extension uses `skip_occupied_check=True` to allow current occupant's room to be "occupied"
6. Early checkout rate is calculated from customer's booking, not room's default rate
