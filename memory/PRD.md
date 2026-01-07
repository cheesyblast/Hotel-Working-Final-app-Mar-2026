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

### 2026-01-05 - Past Date Booking Bug Fix
**Issue Fixed**: Creating past-date bookings for already checked-in customers was failing with 401 Unauthorized error.

**Root Causes Identified & Fixed**:
1. **Login Race Condition** (Frontend): Axios Authorization header wasn't set before making `/api/auth/me` call after login. Fixed by setting header immediately in login function before subsequent requests.
2. **Status Inconsistency** (Backend): Booking status values were inconsistent - "Checked-in" (hyphen) vs "Checked In" (space) used interchangeably. Standardized all status checks to handle both variants.

**Files Modified**:
- `/app/frontend/src/App.js` - Login function now sets Authorization header immediately
- `/app/backend/server.py` - Status checks updated to handle both variants

**Tests**: All 6 backend tests pass (100% success rate)

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

### P0 - Verified/User Testing Pending
- [x] Past-date booking bug fix (COMPLETED & TESTED)
- [x] Restaurant charges appearing at checkout (COMPLETED & TESTED)
- [ ] Short-time booking checkout fix (USER VERIFICATION PENDING)
- [ ] Initial cash/bank balance in setup wizard (USER VERIFICATION PENDING)

### P1 - Upcoming Tasks
- [ ] Make application mobile responsive (starting with Restaurant component)

### P2 - Future Enhancements
- [ ] Email notifications for bookings
- [ ] Guest feedback/review system
- [ ] Room maintenance tracking
- [ ] Advanced reporting and analytics

---

## Key Technical Decisions
1. Using "Checked In" (with space) as the canonical checked-in status
2. JWT tokens expire after 30 minutes (configurable)
3. Past-date bookings can be created with either "Upcoming" or "Checked In" status
4. MongoDB ObjectIds are excluded from API responses to ensure JSON serialization
