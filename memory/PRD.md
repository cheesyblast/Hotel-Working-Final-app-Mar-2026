# Hotel Management System - Product Requirements Document

## Original Problem Statement
Build a comprehensive hotel management system for managing rooms, bookings, customers, restaurant orders, income/expenses, and reporting.

## Core Features Implemented
- Room management (availability, status, pricing)
- Bulk room creation (create multiple rooms at once)
- Booking management (upcoming, checked-in, completed)
- Customer check-in/check-out workflow
- Room cleaning workflow (Pending Cleaning status, staff assignment)
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
4. **Housekeeping Staff** - Cleans rooms after guest checkout

## Tech Stack
- **Frontend**: React.js with Tailwind CSS
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Authentication**: JWT with bcrypt

---

## Changelog

### 2026-02-08 - SMS/Email Notification System Complete
**Features Implemented**:

1. **Automated SMS/Email Notifications on All Occasions**
   - **Reservation**: SMS + Email sent when booking is created
   - **Check-in**: SMS + Email sent when guest checks in
   - **Checkout**: SMS + Email sent when guest checks out
   - **Cleaning Assignment**: SMS sent to staff when room assigned for cleaning
   - Helper functions: `send_booking_notification_sms()`, `send_booking_notification_email()`, `send_notifications()`
   - Template variable substitution: {guest_name}, {hotel_name}, {room_number}, {check_in_date}, etc.

2. **Custom Message Sending (Guests Page)**
   - Actions dropdown menu for each guest: View Details, Edit, Send SMS, Send Email
   - SMS modal pre-fills phone number from guest data
   - Email modal pre-fills email address from guest data
   - Message logs stored in database

3. **Custom Message Sending (Settings > Templates)**
   - New "Send Custom Message" section with gradient header
   - "Send SMS" button opens modal to send to any phone number
   - "Send Email" button opens modal to send to any email address
   - Supports message logging for audit

**API Endpoints Added**:
- `POST /api/send-custom-sms` - Send SMS to any phone number
- `POST /api/send-custom-email` - Send email to any address
- `GET /api/message-logs` - View sent message history

**Files Modified**:
- `/app/backend/server.py`: Added notification helpers, custom message endpoints, integrated SMS/Email triggers into booking, checkin, checkout, cleaning assignment
- `/app/frontend/src/App.js`: Updated Guests component with Actions dropdown and modals, updated Settings Templates tab with custom message section

**Tests**: All 13 backend tests pass, 7 frontend features verified - `/app/test_reports/iteration_6.json`

---

### 2026-02-08 - P1 Features Implementation
**Features Implemented**:

1. **UI Gradient Headers on All Pages**
   - Dashboard: Blue-Cyan gradient (`from-blue-800 to-cyan-700`)
   - Rooms: Slate-Blue gradient (`from-slate-800 to-blue-800`)
   - Guests: Purple-Pink gradient (`from-purple-800 to-pink-700`)
   - Bookings: Teal-Cyan gradient (`from-teal-800 to-cyan-600`)
   - Settings: Gray-Zinc gradient (`from-gray-800 to-zinc-700`)
   - Reports: Indigo-Violet gradient (`from-indigo-800 to-violet-700`)
   - Income & Expenses: Green-Emerald gradient (`from-green-800 to-emerald-600`)

2. **Brevo Email Integration (User Configurable)**
   - Added Brevo as email provider option in Settings → Email Settings
   - Users enter their own Brevo API key
   - Uses Brevo's v3 SMTP API for sending
   - Backend function: `send_email_brevo()` in server.py

3. **Notify.lk SMS Gateway (User Configurable)**
   - Added Notify.lk as SMS provider option in Settings → SMS Settings
   - Fields: User ID, API Key, Sender ID
   - Backend function: `send_sms_notify_lk()` in server.py
   - Test SMS endpoint now actually sends SMS

4. **Taxes & Levies Configuration (NEW)**
   - New "Taxes & Levies" tab in Settings
   - Create custom taxes/levies with name, rate (% or fixed), description
   - Toggle "Apply to Bookings" - Tax added to room charges during checkout
   - Toggle "Apply to Restaurant" - Tax added to restaurant order totals
   - Toggle "None" (both off) - For hotels that don't collect taxes separately
   - Tax breakdown shown in billing details
   - Taxes recorded in daily_sales and financial statements

5. **Payroll Processing with PayrollSettings**
   - EPF/ETF rates now configurable via PayrollSettings
   - Process Payroll uses database settings for calculations
   - Tax deduction support (optional, configurable)
   - Automatic loan installment processing

**API Endpoints Added/Modified**:
- `/api/taxes` - CRUD for tax configurations
- `/api/taxes/calculate-booking` - Preview booking tax calculation
- `/api/taxes/calculate-restaurant` - Preview restaurant tax calculation
- `/api/checkout` - Now includes tax calculation and breakdown
- `/api/restaurant/orders` - Now applies restaurant taxes automatically
- `/api/sms-settings/test` - Now sends actual SMS via configured provider

**Files Modified**:
- `/app/backend/server.py`: Added TaxConfig model with apply_to_bookings/apply_to_restaurant flags, calculate_booking_taxes(), calculate_restaurant_taxes() helpers
- `/app/frontend/src/App.js`: Added Taxes & Levies tab in Settings with full CRUD UI

**Tests**: All tests pass - `/app/test_reports/iteration_5.json`

### 2026-02-05 - Major Features Addition
**Features Implemented**:

1. **Commission Export (CSV)**
   - Export button added to Commissions page header
   - Exports all commission data with booking details
   - Filters by year and month

2. **SMS Settings & Gateway Integration**
   - Support for Twilio (international)
   - Support for Notify.lk (Sri Lanka)
   - Support for Custom HTTP API
   - Configurable in Settings → SMS Settings

3. **Email & SMS Templates**
   - Default templates for: Reservation, Check-in, Check-out
   - SMS template for Cleaning Assignment
   - Create custom templates with variables
   - Settings → Templates tab

4. **Room Maintenance Tracking**
   - Track maintenance purchases/items
   - Track maintenance tasks with priority
   - Expense auto-recorded
   - Summary with category breakdown
   - New /maintenance route

5. **Payroll System (Sri Lanka Specific)**
   - Employee management
   - Salary components (allowances/deductions)
   - EPF/ETF calculations (8%/12%/3%)
   - Loan management
   - Payroll processing
   - Payslip generation
   - New /payroll route

6. **Navigation Consolidation**
   - Financial dropdown menu containing:
     - Inc & Exp
     - Commissions
     - Reports

**New Backend Endpoints**:
- Email Templates: GET/POST/PUT/DELETE `/api/email-templates`
- SMS Settings: GET/PUT `/api/sms-settings`
- SMS Templates: GET/POST/PUT/DELETE `/api/sms-templates`
- Maintenance Items: GET/POST/DELETE `/api/maintenance/items`
- Maintenance Tasks: GET/POST/PUT/DELETE `/api/maintenance/tasks`
- Payroll: `/api/payroll/employees`, `/api/payroll/salary-components`, `/api/payroll/loans`, `/api/payroll/process`, `/api/payroll/runs`, `/api/payroll/payslips`
- Commission Export: GET `/api/commissions/export`

**Files Modified**:
- `/app/backend/server.py`: Added 30+ new endpoints and models
- `/app/frontend/src/App.js`: Added Payroll & Maintenance components, updated Navigation, Settings tabs

### 2026-02-05 - Bulk Room Creation & Room Cleaning Workflow
**Features Added**:
1. **Bulk Room Creation**: Create multiple rooms at once from the Rooms page
   - Set floor/prefix, start number, end number
   - Configure room type, price, max occupancy, amenities
   - Preview shows room numbers to be created
   - Skips rooms that already exist

2. **Room Cleaning Workflow**: 
   - After checkout, rooms go to "Pending Cleaning" status (light maroon color)
   - New "Rooms to be Cleaned" collapsible section on Dashboard (min-height 400px)
   - Add/manage cleaning staff
   - Assign staff to rooms for cleaning
   - Mark rooms as cleaned to make them available

**API Endpoints Added**:
- `POST /api/rooms/bulk` - Create multiple rooms
- `GET /api/cleaning/staff` - Get all cleaning staff
- `POST /api/cleaning/staff` - Add cleaning staff
- `DELETE /api/cleaning/staff/{staff_id}` - Remove staff
- `GET /api/cleaning/pending` - Get rooms needing cleaning
- `POST /api/cleaning/assign` - Assign staff to room
- `POST /api/cleaning/complete/{room_number}` - Mark room as cleaned

**Files Modified**:
- `/app/backend/server.py`:
  - Added `BulkRoomCreate`, `CleaningStaff`, `CleaningAssignment` models
  - Updated checkout/early checkout to set "Pending Cleaning" status
  - Added cleaning management endpoints
- `/app/frontend/src/App.js`:
  - Added Bulk Add modal to Rooms component
  - Added "Rooms to be Cleaned" section to Dashboard
  - Added staff assignment and room cleaning modals

### 2026-02-05 - Financial Double-Counting Bug Fix
**Bug Fixed**: Advance payment during check-in was double-counted in Income & Expense page (2000 advance caused 4000 balance increase)

**Root Cause**:
- Check-in endpoint was creating BOTH `daily_sales` record AND `incomes` record for advance payments
- Checkout endpoint was creating BOTH `daily_sales` record AND `incomes` record
- Early checkout collection was creating additional `incomes` record when `daily_sales` already captured it
- `/api/daily-financial-summary` endpoint sums both `daily_sales` and `incomes`, causing double-counting

**Solution Implemented - Single Source of Truth**:
1. **Check-in with advance**: Now creates ONLY `Income` record (not DailySale)
2. **Get Advance (for checked-in customer)**: Creates ONLY `Income` record (unchanged)
3. **Regular Checkout**: Creates ONLY `DailySale` record (removed Income record creation)
4. **Early Checkout with collection**: Creates ONLY `DailySale` record (removed Income record for collection)
5. **Early Checkout with refund**: Creates `DailySale` + `Expense` record (correct behavior)
6. **Removed redundant** `settings.cash_balance/bank_balance` updates since balances are computed dynamically

**Files Modified**:
- `/app/backend/server.py`:
  - `checkin_customer()` - Now only creates Income record for advance payments
  - `checkout_customer()` - Now only creates DailySale record (no Income)
  - `early_checkout()` - Fixed to not create Income for collection (already in DailySale)
  - `collect_advance_payment()` - Removed redundant settings balance update
  - `get_incomes()` - Fixed to exclude MongoDB `_id` field

**Tests**: All 16 backend tests pass (7 new + 9 existing)
- Test file: `/app/backend/tests/test_double_counting_fix.py`

### 2026-02-04 - Early Checkout Enhancement
**Feature**: Improved Early Checkout with proper collection/refund handling

**Changes Implemented**:
1. **Potential Collection vs Refund Logic**:
   - Shows "Amount to Collect" (blue) if customer owes money
   - Shows "Refund Due" (green) if customer has overpaid
   - Shows "Balance: LKR 0" if exact balance

2. **Real-time Calculation**:
   - Additional charges and discounts update the final balance in real-time
   - Final balance displayed prominently below all charges

3. **Payment Collection Modal**:
   - When customer owes money, clicking "Confirm Early Checkout" shows a collection popup
   - User selects payment method (Cash/Card/Bank Transfer) for the collection
   - Collected amount is added to Cash or Bank balance

4. **Refund Handling**:
   - Refunds always happen automatically (removed checkbox)
   - Refund method dropdown shown when applicable
   - Refund amount is deducted from Cash or Bank balance

5. **Cash/Bank Balance Updates**:
   - Collections: Added to `cash_balance` or `bank_balance` in settings
   - Refunds: Deducted from `cash_balance` or `bank_balance` in settings
   - Also recorded as Income (collection) or Expense (refund)

**Files Modified**:
- `/app/backend/server.py`:
  - Updated `EarlyCheckoutRequest` model with collection/refund amounts
  - Modified `/api/early-checkout` to handle cash/bank balance updates
- `/app/frontend/src/App.js`:
  - Redesigned Early Checkout modal with real-time balance calculation
  - Added Payment Collection modal for when customer owes money
  - Removed refund_excess checkbox (always refunds now)

### 2026-02-04 - Stay Modification Bug Fixes
**Issues Fixed**: 5 bugs/enhancements related to booking rates and stay modifications

**Changes Implemented**:
1. **Booking Conflict Check for Extend Stay**:
   - Added conflict detection when extending stay
   - Uses `check_room_availability_for_booking()` with `skip_occupied_check=True` parameter
   - Prevents extending into periods where another booking exists

2. **Booking Conflict Check for Edit Booking**:
   - Added conflict detection when editing booking dates
   - Prevents changing dates that would overlap with other bookings for same room
   - Uses same `check_room_availability_for_booking()` function with `exclude_booking_id`

3. **Customer's Booked Rate for Calculations** (NEW):
   - **Extend Stay**: Now uses customer's booked rate per night (calculated from original booking)
   - **Edit Booking**: When dates change, recalculates amount using booking's original rate per night
   - **Early Checkout**: Already uses customer's booked rate (fixed earlier)
   - This ensures customers are charged consistently at their negotiated rate, not room's default rate

4. **Rate Display in Modals** (NEW):
   - **Extend Stay Modal**: Shows "Rate per Night: LKR X" and helper text about charges
   - **Get Advance Modal**: Shows "Rate per Night: LKR X" for clarity
   - **Edit Booking Modal**: Shows "Rate per Night: LKR X" and "Current Amount"
   - **Early Checkout Modal**: Already shows rate per night

5. **API Enhancement**:
   - `GET /api/customers/checked-in` now returns `rate_per_night` field
   - Rate is calculated as: `room_charges / nights`

**Files Modified**:
- `/app/backend/server.py`:
  - `get_checked_in_customers()` - Now returns `rate_per_night` for each customer
  - `extend_customer_stay()` - Uses customer's booked rate instead of room's default
  - `update_booking()` - Uses booking's rate per night when dates change
- `/app/frontend/src/App.js`:
  - Extend Stay modal - Added rate per night display and helper text
  - Get Advance modal - Added rate per night display
  - Edit Booking modal - Added rate per night and current amount display

**Tests**: All features verified working via API and UI screenshots
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
- [x] Financial double-counting bug fix (COMPLETED - 2026-02-05)
- [x] Bulk room creation (COMPLETED - 2026-02-05)
- [x] Room cleaning workflow (COMPLETED - 2026-02-05)
- [x] UI Gradient Headers on all pages (COMPLETED - 2026-02-08)
- [x] Brevo Email Integration - User Configurable (COMPLETED - 2026-02-08)
- [x] Notify.lk SMS Gateway - User Configurable (COMPLETED - 2026-02-08)
- [x] Custom Tax Calculation in Bookings (COMPLETED - 2026-02-08)
- [x] Payroll Processing with PayrollSettings (COMPLETED - 2026-02-08)

### P1 - Upcoming Tasks
- [ ] Export commission reports to PDF (CSV done)
- [ ] Automated email/SMS sending using templates on events (check-in, checkout, cleaning assignment)
- [ ] User verification of previously completed features
- [ ] Make application mobile responsive (starting with Restaurant component)

### P2 - Future Enhancements
- [ ] Guest feedback/review system
- [ ] Email notifications for commission due dates
- [ ] Advanced reporting and analytics
- [ ] Refactor App.js into smaller components (11,000+ lines)
- [ ] Refactor server.py into smaller routers (6,500+ lines)

---

## Key Technical Decisions
1. Using "Checked In" (with space) as the canonical checked-in status
2. JWT tokens expire after 30 minutes (configurable)
3. Past-date bookings can be created with either "Upcoming" or "Checked In" status
4. MongoDB ObjectIds are excluded from API responses to ensure JSON serialization
5. Stay extension uses `skip_occupied_check=True` to allow current occupant's room to be "occupied"
6. Early checkout rate is calculated from customer's booking, not room's default rate
7. **Financial Single Source of Truth**: Each financial transaction is recorded in only ONE collection:
   - Advance payments → `incomes` collection
   - Room checkout → `daily_sales` collection
   - Refunds → `expenses` collection
   - This prevents double-counting in financial summaries
