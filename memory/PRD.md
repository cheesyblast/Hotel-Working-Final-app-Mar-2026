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
- `/app/backend/server.py` - Status checks updated to handle both variants:
  - `check_room_availability_for_booking` (line 664)
  - `check_room_availability` (line 1551)  
  - `checkout_customer` booking update (line 2208)
  - `checkin_customer` (line 2385)
  - `cancel_booking` (line 2435)

**Tests**: All 6 backend tests pass (100% success rate)

---

## Prioritized Backlog

### P0 - Verified/User Testing Pending
- [x] Past-date booking bug fix (COMPLETED & TESTED)
- [ ] Restaurant charges appearing at checkout (USER VERIFICATION PENDING)
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
