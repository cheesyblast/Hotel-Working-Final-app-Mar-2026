#!/bin/bash

# Hotel Management System - Docker Deployment Script
# This script deploys a complete hotel management system using Docker containers
# Avoids all Node.js/Python dependency issues by using containerized services

set -e

echo "===================================================================================="
echo "                    Hotel Management System - Docker Deployment                     "
echo "===================================================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Get user input for domain/IP
echo -e "${BLUE}Enter your server domain or IP address:${NC}"
read -p "Domain/IP: " SERVER_DOMAIN
if [[ -z "$SERVER_DOMAIN" ]]; then
    print_error "Domain/IP cannot be empty"
    exit 1
fi

print_header "STEP 1: Installing Docker and Docker Compose"

# Update system
print_status "Updating system packages..."
apt-get update -y

# Install Docker
print_status "Installing Docker..."
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -

# Add Docker repository
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Update package database with Docker packages
apt-get update -y

# Install Docker CE
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
print_status "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

print_status "Docker installation completed successfully!"

print_header "STEP 2: Creating Application Directory Structure"

# Create app directory
APP_DIR="/opt/hotel-management"
mkdir -p $APP_DIR
cd $APP_DIR

# Create subdirectories
mkdir -p backend frontend nginx

print_status "Directory structure created at $APP_DIR"

print_header "STEP 3: Creating Backend Application"

# Create backend requirements.txt
cat > $APP_DIR/backend/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
python-dotenv==1.0.0
python-multipart==0.0.6
pydantic==2.5.0
starlette==0.27.0
pymongo==4.6.0
dnspython==2.4.2
EOF

# Create backend .env file
cat > $APP_DIR/backend/.env << EOF
MONGO_URL=mongodb://mongodb:27017
DB_NAME=hotel_management
EOF

# Create backend server.py (embedded from your current application)
cat > $APP_DIR/backend/server.py << 'EOF'
from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, date, timedelta
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    room_type: str  # Suite, Double, Triple
    status: str  # Available, Occupied, Reserved
    current_guest: Optional[str] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    price_per_night: float = 0.0
    max_occupancy: int = 2
    amenities: List[str] = []
    image_url: str = "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RoomCreate(BaseModel):
    room_number: str
    room_type: str
    price_per_night: float
    max_occupancy: int = 2
    amenities: List[str] = []

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_name: str
    guest_email: str = ""
    guest_phone: str = ""
    guest_id_passport: str = ""
    guest_country: str = ""
    room_number: str
    check_in_date: date
    check_out_date: date
    stay_type: str = "Night Stay"  # "Night Stay" or "Short Time"
    booking_amount: float = 0.0  # Custom amount entered by user
    status: str  # Upcoming, Checked-in, Completed, Cancelled
    additional_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookingCreate(BaseModel):
    guest_name: str
    guest_email: str = ""
    guest_phone: str = ""
    guest_id_passport: str = ""
    guest_country: str = ""
    room_number: str
    check_in_date: date
    check_out_date: Optional[date] = None
    stay_type: str = "Night Stay"
    booking_amount: float = 0.0
    additional_notes: str = ""

class BookingUpdate(BaseModel):
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    additional_notes: Optional[str] = None

class Customer(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    current_room: str
    check_in_date: date
    check_out_date: date
    advance_amount: float = 0.0
    notes: str = ""
    room_charges: float = 0.0
    additional_charges: float = 0.0
    total_amount: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutRequest(BaseModel):
    customer_id: str
    additional_amount: float = 0.0
    discount_amount: float = 0.0
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer

class DailySale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: date
    customer_name: str
    room_number: str
    room_charges: float
    additional_charges: float
    discount_amount: float
    advance_amount: float
    total_amount: float
    payment_method: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckinRequest(BaseModel):
    booking_id: str
    advance_amount: float = 0.0
    notes: str = ""

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str  # Food, Maintenance, Utilities, Staff, Marketing, etc.
    expense_date: date
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str
    expense_date: date

class Income(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str  # Restaurant, Events, Laundry, Spa, Other Services, etc.
    income_date: date
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IncomeCreate(BaseModel):
    description: str
    amount: float
    category: str
    income_date: date

class FinancialSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_profit: float
    revenue_breakdown: dict
    expense_breakdown: dict
    period_start: date
    period_end: date

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# Room Management Routes
@api_router.get("/rooms", response_model=List[Room])
async def get_rooms():
    rooms = await db.rooms.find().to_list(1000)
    
    # Convert datetime back to date for response
    for room in rooms:
        if isinstance(room.get('check_in_date'), datetime):
            room['check_in_date'] = room['check_in_date'].date()
        if isinstance(room.get('check_out_date'), datetime):
            room['check_out_date'] = room['check_out_date'].date()
    
    return [Room(**room) for room in rooms]

@api_router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate):
    room_dict = room.dict()
    room_obj = Room(**room_dict, status="Available")
    await db.rooms.insert_one(room_obj.dict())
    return room_obj

@api_router.put("/rooms/{room_id}")
async def update_room(room_id: str, room: RoomCreate):
    room_dict = room.dict()
    result = await db.rooms.update_one({"id": room_id}, {"$set": room_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room updated successfully"}

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    result = await db.rooms.delete_one({"id": room_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room deleted successfully"}

# Booking Management Routes
@api_router.get("/bookings", response_model=List[Booking])
async def get_bookings():
    bookings = await db.bookings.find().to_list(1000)
    
    # Convert datetime back to date for response
    for booking in bookings:
        if isinstance(booking.get('check_in_date'), datetime):
            booking['check_in_date'] = booking['check_in_date'].date()
        if isinstance(booking.get('check_out_date'), datetime):
            booking['check_out_date'] = booking['check_out_date'].date()
    
    return [Booking(**booking) for booking in bookings]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    booking_dict = booking.dict()
    
    # Convert date strings to datetime for MongoDB compatibility
    if isinstance(booking_dict.get('check_in_date'), str):
        booking_dict['check_in_date'] = datetime.strptime(booking_dict['check_in_date'], '%Y-%m-%d').date()
    
    # Handle short time stays - set checkout date to same day if not provided or if short time
    if booking_dict.get('stay_type') == 'Short Time' or not booking_dict.get('check_out_date'):
        if booking_dict.get('stay_type') == 'Short Time':
            booking_dict['check_out_date'] = booking_dict['check_in_date']
    else:
        if isinstance(booking_dict.get('check_out_date'), str):
            booking_dict['check_out_date'] = datetime.strptime(booking_dict['check_out_date'], '%Y-%m-%d').date()
    
    booking_obj = Booking(**booking_dict, status="Upcoming")
    
    # Convert date objects to datetime for MongoDB storage
    booking_storage = booking_obj.dict()
    if booking_storage.get('check_in_date'):
        booking_storage['check_in_date'] = datetime.combine(booking_storage['check_in_date'], datetime.min.time())
    if booking_storage.get('check_out_date'):
        booking_storage['check_out_date'] = datetime.combine(booking_storage['check_out_date'], datetime.min.time())
    
    await db.bookings.insert_one(booking_storage)
    return booking_obj

# Customer Management Routes
@api_router.get("/customers/checked-in", response_model=List[Customer])
async def get_checked_in_customers():
    customers = await db.customers.find().to_list(1000)
    
    # Convert datetime back to date for response
    for customer in customers:
        if isinstance(customer.get('check_in_date'), datetime):
            customer['check_in_date'] = customer['check_in_date'].date()
        if isinstance(customer.get('check_out_date'), datetime):
            customer['check_out_date'] = customer['check_out_date'].date()
    
    return [Customer(**customer) for customer in customers]

@api_router.post("/checkin")
async def checkin_customer(checkin: CheckinRequest):
    # Find the booking
    booking = await db.bookings.find_one({"id": checkin.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if room is available
    room = await db.rooms.find_one({"room_number": booking["room_number"]})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room["status"] != "Available":
        raise HTTPException(status_code=400, detail="Room is not available for check-in")
    
    # Use the booking amount as room charges (actual amount customer agreed to pay)
    room_charges = booking.get("booking_amount", 500.0)
    
    # Create customer record
    customer = Customer(
        name=booking["guest_name"],
        email=booking["guest_email"],
        phone=booking["guest_phone"],
        current_room=booking["room_number"],
        check_in_date=booking["check_in_date"] if isinstance(booking["check_in_date"], date) else booking["check_in_date"].date(),
        check_out_date=booking["check_out_date"] if isinstance(booking["check_out_date"], date) else booking["check_out_date"].date(),
        advance_amount=checkin.advance_amount,
        notes=checkin.notes,
        room_charges=room_charges,
        total_amount=room_charges - checkin.advance_amount
    )
    
    # Add customer to checked-in list
    customer_dict = customer.dict()
    customer_dict['check_in_date'] = datetime.combine(customer_dict['check_in_date'], datetime.min.time())
    customer_dict['check_out_date'] = datetime.combine(customer_dict['check_out_date'], datetime.min.time())
    await db.customers.insert_one(customer_dict)
    
    # Update room status to occupied
    await db.rooms.update_one(
        {"room_number": booking["room_number"]},
        {"$set": {
            "status": "Occupied",
            "current_guest": booking["guest_name"],
            "check_in_date": datetime.combine(booking["check_in_date"] if isinstance(booking["check_in_date"], date) else booking["check_in_date"].date(), datetime.min.time()),
            "check_out_date": datetime.combine(booking["check_out_date"] if isinstance(booking["check_out_date"], date) else booking["check_out_date"].date(), datetime.min.time())
        }}
    )
    
    # Update booking status to checked-in
    await db.bookings.update_one(
        {"id": checkin.booking_id},
        {"$set": {"status": "Checked-in"}}
    )
    
    return {"message": "Customer checked in successfully", "customer": customer}

@api_router.post("/checkout")
async def checkout_customer(checkout: CheckoutRequest):
    # Find customer first to get room info
    customer = await db.customers.find_one({"id": checkout.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate total amount
    base_room_charges = customer.get('room_charges', 500.0)  # Default room charge
    advance_amount = customer.get('advance_amount', 0.0)
    additional_amount = checkout.additional_amount
    discount_amount = checkout.discount_amount
    total_amount = base_room_charges + additional_amount - advance_amount - discount_amount
    
    # Create daily sales record
    daily_sale = DailySale(
        date=datetime.now().date(),
        customer_name=customer.get('name', ''),
        room_number=customer.get('current_room', ''),
        room_charges=base_room_charges,
        additional_charges=additional_amount,
        discount_amount=discount_amount,
        advance_amount=advance_amount,
        total_amount=total_amount,
        payment_method=checkout.payment_method
    )
    
    # Store the daily sale record
    daily_sale_dict = daily_sale.dict()
    daily_sale_dict['date'] = datetime.combine(daily_sale_dict['date'], datetime.min.time())
    await db.daily_sales.insert_one(daily_sale_dict)
    
    # Update customer with final billing details
    await db.customers.update_one(
        {"id": checkout.customer_id},
        {"$set": {
            "additional_charges": additional_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount
        }}
    )
    
    # Remove customer from checked-in list
    result = await db.customers.delete_one({"id": checkout.customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update room status to available
    await db.rooms.update_one(
        {"room_number": customer["current_room"]},
        {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
    )
    
    return {
        "message": "Customer checked out successfully",
        "billing_details": {
            "room_charges": base_room_charges,
            "advance_amount": advance_amount,
            "additional_charges": additional_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "payment_method": checkout.payment_method
        }
    }

# Guest Management Routes
@api_router.get("/guests")
async def get_guests():
    # Get all bookings to extract guest information
    bookings = await db.bookings.find().to_list(1000)
    
    # Create a dictionary to store unique guests with their booking history
    guests_dict = {}
    
    for booking in bookings:
        guest_name = booking.get('guest_name')
        guest_email = booking.get('guest_email', '')
        guest_phone = booking.get('guest_phone', '')
        
        # Skip bookings without at least a guest name
        if not guest_name:
            continue
            
        # Create a unique identifier - use email if available, otherwise use name + phone
        if guest_email:
            guest_key = guest_email
        else:
            guest_key = f"{guest_name}_{guest_phone}_{booking.get('id', '')}"
        
        if guest_key not in guests_dict:
            # Convert datetime back to date for response
            check_in_date = booking.get('check_in_date')
            check_out_date = booking.get('check_out_date')
            if isinstance(check_in_date, datetime):
                check_in_date = check_in_date.date()
            if isinstance(check_out_date, datetime):
                check_out_date = check_out_date.date()
            
            guests_dict[guest_key] = {
                'id': guest_key,  # Using unique key as identifier
                'name': guest_name,
                'email': guest_email or 'Not provided',
                'phone': guest_phone or 'Not provided',
                'total_bookings': 0,
                'total_stays': 0,
                'last_stay': None,
                'upcoming_bookings': 0,
                'bookings': []
            }
        
        # Add booking to guest's history
        check_in_date = booking.get('check_in_date')
        check_out_date = booking.get('check_out_date')
        if isinstance(check_in_date, datetime):
            check_in_date = check_in_date.date()
        if isinstance(check_out_date, datetime):
            check_out_date = check_out_date.date()
        
        booking_info = {
            'id': booking.get('id'),
            'room_number': booking.get('room_number'),
            'check_in_date': check_in_date,
            'check_out_date': check_out_date,
            'status': booking.get('status'),
            'created_at': booking.get('created_at')
        }
        
        guests_dict[guest_key]['bookings'].append(booking_info)
        guests_dict[guest_key]['total_bookings'] += 1
        
        # Update stats based on booking status
        if booking.get('status') == 'Completed':
            guests_dict[guest_key]['total_stays'] += 1
            if not guests_dict[guest_key]['last_stay'] or check_out_date > guests_dict[guest_key]['last_stay']:
                guests_dict[guest_key]['last_stay'] = check_out_date
        elif booking.get('status') == 'Upcoming':
            guests_dict[guest_key]['upcoming_bookings'] += 1
    
    # Convert dictionary to list and sort by name
    guests_list = list(guests_dict.values())
    guests_list.sort(key=lambda x: x['name'])
    
    return guests_list

# Expense Management Routes
@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses():
    expenses = await db.expenses.find().sort("expense_date", -1).to_list(1000)
    
    # Convert datetime back to date for response
    for expense in expenses:
        if isinstance(expense.get('expense_date'), datetime):
            expense['expense_date'] = expense['expense_date'].date()
    
    return [Expense(**expense) for expense in expenses]

@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    expense_dict = expense.dict()
    
    # Convert date string to date object if needed
    if isinstance(expense_dict.get('expense_date'), str):
        expense_dict['expense_date'] = datetime.strptime(expense_dict['expense_date'], '%Y-%m-%d').date()
    
    expense_obj = Expense(**expense_dict)
    
    # Convert date to datetime for MongoDB storage
    expense_storage = expense_obj.dict()
    if expense_storage.get('expense_date'):
        expense_storage['expense_date'] = datetime.combine(expense_storage['expense_date'], datetime.min.time())
    
    await db.expenses.insert_one(expense_storage)
    return expense_obj

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted successfully"}

# Income Management Routes
@api_router.get("/incomes", response_model=List[Income])
async def get_incomes():
    incomes = await db.incomes.find().sort("income_date", -1).to_list(1000)
    
    # Convert datetime back to date for response
    for income in incomes:
        if isinstance(income.get('income_date'), datetime):
            income['income_date'] = income['income_date'].date()
    
    return [Income(**income) for income in incomes]

@api_router.post("/incomes", response_model=Income)
async def create_income(income: IncomeCreate):
    income_dict = income.dict()
    
    # Convert date string to date object if needed
    if isinstance(income_dict.get('income_date'), str):
        income_dict['income_date'] = datetime.strptime(income_dict['income_date'], '%Y-%m-%d').date()
    
    income_obj = Income(**income_dict)
    
    # Convert date to datetime for MongoDB storage
    income_storage = income_obj.dict()
    if income_storage.get('income_date'):
        income_storage['income_date'] = datetime.combine(income_storage['income_date'], datetime.min.time())
    
    await db.incomes.insert_one(income_storage)
    return income_obj

@api_router.delete("/incomes/{income_id}")
async def delete_income(income_id: str):
    result = await db.incomes.delete_one({"id": income_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Income not found")
    return {"message": "Income deleted successfully"}

# Daily Sales Routes
@api_router.get("/daily-sales")
async def get_daily_sales(start_date: Optional[str] = None, end_date: Optional[str] = None):
    query = {}
    if start_date and end_date:
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        query["date"] = {"$gte": start_datetime, "$lt": end_datetime}
    
    sales = await db.daily_sales.find(query).sort("date", -1).to_list(1000)
    
    # Convert datetime back to date for response
    for sale in sales:
        if isinstance(sale.get('date'), datetime):
            sale['date'] = sale['date'].date()
    
    return [DailySale(**sale) for sale in sales]

# Financial Summary Routes
@api_router.get("/financial-summary")
async def get_financial_summary():
    # Calculate total revenue from actual daily sales (payment collected)
    total_revenue = 0
    daily_sales = await db.daily_sales.find().to_list(1000)
    
    for sale in daily_sales:
        total_revenue += sale.get("total_amount", 0)
    
    # Calculate additional income (non-room income)
    additional_income = 0
    incomes = await db.incomes.find().to_list(1000)
    
    for income in incomes:
        additional_income += income.get("amount", 0)
    
    # Total revenue = room revenue + additional income
    total_revenue += additional_income
    
    # Calculate total expenses
    total_expenses = 0
    expenses = await db.expenses.find().to_list(1000)
    
    for expense in expenses:
        total_expenses += expense.get("amount", 0)
    
    # Calculate net profit
    net_profit = total_revenue - total_expenses
    
    # Revenue breakdown
    revenue_breakdown = {
        "room_revenue": total_revenue - additional_income,
        "additional_income": additional_income,
        "total_revenue": total_revenue
    }
    
    # Expense breakdown by category
    expense_breakdown = {}
    for expense in expenses:
        category = expense.get("category", "Other")
        if category not in expense_breakdown:
            expense_breakdown[category] = 0
        expense_breakdown[category] += expense.get("amount", 0)
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "revenue_breakdown": revenue_breakdown,
        "expense_breakdown": expense_breakdown,
        "period_start": datetime.now().date() - timedelta(days=30),
        "period_end": datetime.now().date()
    }

# Initialize sample data
@api_router.post("/init-data")
async def initialize_sample_data():
    # Check if data already exists
    existing_rooms = await db.rooms.count_documents({})
    if existing_rooms > 0:
        return {"message": "Sample data already exists"}
    
    # Create sample rooms
    sample_rooms = [
        Room(room_number="101", room_type="Suite", status="Available", price_per_night=15000.0, max_occupancy=4, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service", "Balcony"]),
        Room(room_number="102", room_type="Double", status="Available", price_per_night=8500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="103", room_type="Double", status="Available", price_per_night=6500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="201", room_type="Double", status="Available", price_per_night=9000.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="202", room_type="Triple", status="Available", price_per_night=12000.0, max_occupancy=3, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="203", room_type="Double", status="Available", price_per_night=7500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge"]),
        Room(room_number="204", room_type="Triple", status="Available", price_per_night=11000.0, max_occupancy=3, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="205", room_type="Double", status="Available", price_per_night=8000.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="301", room_type="Double", status="Available", price_per_night=7000.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge"]),
        Room(room_number="302", room_type="Double", status="Available", price_per_night=7200.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge"]),
    ]
    
    for room in sample_rooms:
        room_dict = room.dict()
        # Convert date objects to datetime for MongoDB compatibility
        if room_dict.get('check_in_date'):
            room_dict['check_in_date'] = datetime.combine(room_dict['check_in_date'], datetime.min.time())
        if room_dict.get('check_out_date'):
            room_dict['check_out_date'] = datetime.combine(room_dict['check_out_date'], datetime.min.time())
        await db.rooms.insert_one(room_dict)
    
    return {"message": "Sample data initialized successfully"}

# Include the API router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

print_status "Backend application created successfully!"

print_header "STEP 4: Creating Frontend Application"

# Create frontend package.json
cat > $APP_DIR/frontend/package.json << 'EOF'
{
  "name": "hotel-management-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

# Create frontend directories
mkdir -p $APP_DIR/frontend/src
mkdir -p $APP_DIR/frontend/public

# Create frontend public/index.html
cat > $APP_DIR/frontend/public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Hotel Management System" />
    <title>Hotel Management System</title>
    <script src="https://cdn.tailwindcss.com"></script>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOF

# Create frontend src/index.js
cat > $APP_DIR/frontend/src/index.js << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
EOF

# Create frontend src/index.css
cat > $APP_DIR/frontend/src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOF

# Create frontend environment file
cat > $APP_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=http://$SERVER_DOMAIN:8000
EOF

# Create a simplified React application
cat > $APP_DIR/frontend/src/App.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

// Get API URL from environment variable
const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/rooms" element={<RoomsPage />} />
            <Route path="/bookings" element={<BookingsPage />} />
            <Route path="/guests" element={<GuestsPage />} />
            <Route path="/expenses" element={<ExpensesPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

const Navigation = () => {
  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center py-4">
          <Link to="/" className="text-xl font-bold">Hotel Management System</Link>
          <div className="flex space-x-6">
            <Link to="/" className="hover:text-blue-200">Dashboard</Link>
            <Link to="/rooms" className="hover:text-blue-200">Rooms</Link>
            <Link to="/bookings" className="hover:text-blue-200">Bookings</Link>
            <Link to="/guests" className="hover:text-blue-200">Guests</Link>
            <Link to="/expenses" className="hover:text-blue-200">Inc & Exp</Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

const Dashboard = () => {
  const [rooms, setRooms] = useState([]);
  const [checkedInCustomers, setCheckedInCustomers] = useState([]);
  const [upcomingBookings, setUpcomingBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [roomsResponse, customersResponse, bookingsResponse] = await Promise.all([
        axios.get(`${API}/api/rooms`),
        axios.get(`${API}/api/customers/checked-in`),
        axios.get(`${API}/api/bookings`)
      ]);
      
      setRooms(roomsResponse.data);
      setCheckedInCustomers(customersResponse.data);
      setUpcomingBookings(bookingsResponse.data.filter(b => b.status === 'Upcoming'));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/api/init-data`);
      alert('Sample data initialized successfully!');
      fetchDashboardData();
    } catch (error) {
      console.error('Error initializing sample data:', error);
      alert('Error initializing sample data');
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Hotel Dashboard</h1>
        <button
          onClick={initializeSampleData}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
        >
          Initialize Sample Data
        </button>
      </div>

      {/* Room Status Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Room Status Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {rooms.map((room) => (
            <div key={room.id} className={`p-4 rounded-lg border-2 ${
              room.status === 'Available' ? 'border-green-200 bg-green-50' : 
              room.status === 'Occupied' ? 'border-red-200 bg-red-50' : 
              'border-yellow-200 bg-yellow-50'
            }`}>
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">Room {room.room_number}</h3>
                  <p className="text-sm text-gray-600">{room.room_type}</p>
                  <p className="text-sm font-medium">LKR {room.price_per_night}/night</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  room.status === 'Available' ? 'bg-green-100 text-green-800' :
                  room.status === 'Occupied' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {room.status}
                </span>
              </div>
              {room.current_guest && (
                <div className="mt-2 text-sm text-gray-600">
                  Guest: {room.current_guest}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Rooms</h3>
          <p className="text-3xl font-bold text-blue-600">{rooms.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Checked In</h3>
          <p className="text-3xl font-bold text-green-600">{checkedInCustomers.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Upcoming Bookings</h3>
          <p className="text-3xl font-bold text-orange-600">{upcomingBookings.length}</p>
        </div>
      </div>

      {/* Recent Bookings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Bookings</h2>
        {upcomingBookings.length === 0 ? (
          <p className="text-gray-500">No upcoming bookings</p>
        ) : (
          <div className="space-y-3">
            {upcomingBookings.slice(0, 5).map((booking) => (
              <div key={booking.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{booking.guest_name}</p>
                  <p className="text-sm text-gray-600">Room {booking.room_number}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{booking.check_in_date}</p>
                  <p className="text-sm text-gray-600">{booking.status}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const RoomsPage = () => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      const response = await axios.get(`${API}/api/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error('Error fetching rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Rooms Management</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          Add New Room
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rooms.map((room) => (
          <div key={room.id} className="bg-white rounded-lg shadow overflow-hidden">
            <img 
              src={room.image_url} 
              alt={`Room ${room.room_number}`}
              className="w-full h-48 object-cover"
            />
            <div className="p-6">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-semibold">Room {room.room_number}</h3>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  room.status === 'Available' ? 'bg-green-100 text-green-800' :
                  room.status === 'Occupied' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {room.status}
                </span>
              </div>
              <p className="text-gray-600 mb-2">{room.room_type}</p>
              <p className="text-lg font-bold text-blue-600 mb-2">LKR {room.price_per_night}/night</p>
              <p className="text-sm text-gray-600 mb-4">Max {room.max_occupancy} guests</p>
              
              <div className="flex flex-wrap gap-1 mb-4">
                {room.amenities.map((amenity, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {amenity}
                  </span>
                ))}
              </div>
              
              <div className="flex space-x-2">
                <button className="flex-1 bg-blue-600 text-white py-2 rounded hover:bg-blue-700">
                  Edit
                </button>
                <button className="flex-1 bg-red-600 text-white py-2 rounded hover:bg-red-700">
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const BookingsPage = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBookings();
  }, []);

  const fetchBookings = async () => {
    try {
      const response = await axios.get(`${API}/api/bookings`);
      setBookings(response.data);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Bookings Management</h1>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
          New Booking
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Guest
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Room
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Check In
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Check Out
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {bookings.map((booking) => (
                <tr key={booking.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{booking.guest_name}</div>
                    <div className="text-sm text-gray-500">{booking.guest_email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{booking.room_number}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{booking.check_in_date}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{booking.check_out_date}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      booking.status === 'Upcoming' ? 'bg-blue-100 text-blue-800' :
                      booking.status === 'Checked-in' ? 'bg-green-100 text-green-800' :
                      booking.status === 'Completed' ? 'bg-gray-100 text-gray-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {booking.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">LKR {booking.booking_amount}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const GuestsPage = () => {
  const [guests, setGuests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuests();
  }, []);

  const fetchGuests = async () => {
    try {
      const response = await axios.get(`${API}/api/guests`);
      setGuests(response.data);
    } catch (error) {
      console.error('Error fetching guests:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Guests Management</h1>
        <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
          Download Guest Data
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Bookings
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Stay
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {guests.map((guest) => (
                <tr key={guest.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{guest.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.phone}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.total_bookings}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{guest.last_stay || 'N/A'}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

const ExpensesPage = () => {
  const [expenses, setExpenses] = useState([]);
  const [incomes, setIncomes] = useState([]);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExpensesData();
  }, []);

  const fetchExpensesData = async () => {
    try {
      const [expensesResponse, incomesResponse, summaryResponse] = await Promise.all([
        axios.get(`${API}/api/expenses`),
        axios.get(`${API}/api/incomes`),
        axios.get(`${API}/api/financial-summary`)
      ]);
      
      setExpenses(expensesResponse.data);
      setIncomes(incomesResponse.data);
      setFinancialSummary(summaryResponse.data);
    } catch (error) {
      console.error('Error fetching expenses data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-gray-900">Income & Expenses</h1>
        <div className="flex space-x-3">
          <button className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700">
            Add Income
          </button>
          <button className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">
            Add Expense
          </button>
        </div>
      </div>

      {/* Financial Summary */}
      {financialSummary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Revenue</h3>
            <p className="text-3xl font-bold text-green-600">
              {formatCurrency(financialSummary.total_revenue)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Expenses</h3>
            <p className="text-3xl font-bold text-red-600">
              {formatCurrency(financialSummary.total_expenses)}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Net Profit</h3>
            <p className={`text-3xl font-bold ${
              financialSummary.net_profit >= 0 ? 'text-blue-600' : 'text-orange-600'
            }`}>
              {formatCurrency(financialSummary.net_profit)}
            </p>
          </div>
        </div>
      )}

      {/* Recent Expenses */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Expenses</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {expenses.slice(0, 10).map((expense) => (
                <tr key={expense.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{expense.description}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{expense.category}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-bold text-red-600">{formatCurrency(expense.amount)}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{expense.expense_date}</div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default App;
EOF

print_status "Frontend application created successfully!"

print_header "STEP 5: Creating Docker Configuration"

# Create docker-compose.yml
cat > $APP_DIR/docker-compose.yml << EOF
version: '3.8'

services:
  # MongoDB Database
  mongodb:
    image: mongo:7.0
    container_name: hotel-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: hotel_management
    volumes:
      - mongodb_data:/data/db
    networks:
      - hotel-network

  # Backend API
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: hotel-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      - mongodb
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=hotel_management
    volumes:
      - ./backend:/app
    networks:
      - hotel-network

  # Frontend Application
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: hotel-frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_BACKEND_URL=http://$SERVER_DOMAIN:8000
    volumes:
      - ./frontend:/app
    networks:
      - hotel-network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: hotel-nginx
    restart: unless-stopped
    ports:
      - "80:80"
    depends_on:
      - frontend
      - backend
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    networks:
      - hotel-network

volumes:
  mongodb_data:

networks:
  hotel-network:
    driver: bridge
EOF

# Create backend Dockerfile
cat > $APP_DIR/backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# Create frontend Dockerfile
cat > $APP_DIR/frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
EOF

# Create nginx configuration
cat > $APP_DIR/nginx/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    upstream backend {
        server backend:8000;
    }
    
    upstream frontend {
        server frontend:3000;
    }
    
    server {
        listen 80;
        server_name $SERVER_DOMAIN;
        
        # Frontend routes
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # Backend API routes
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # WebSocket support for React dev server
        location /ws {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
        }
    }
}
EOF

print_status "Docker configuration created successfully!"

print_header "STEP 6: Building and Starting the Application"

# Build and start the application
print_status "Building Docker images..."
cd $APP_DIR
docker-compose build

print_status "Starting the application..."
docker-compose up -d

print_status "Waiting for services to start..."
sleep 30

print_header "STEP 7: Verifying Installation"

# Check if services are running
print_status "Checking service status..."
docker-compose ps

# Test backend health
print_status "Testing backend connectivity..."
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    print_status "✅ Backend is running successfully!"
else
    print_warning "⚠️  Backend health check failed, but this might be normal during startup"
fi

# Test frontend
print_status "Testing frontend connectivity..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_status "✅ Frontend is running successfully!"
else
    print_warning "⚠️  Frontend health check failed, but this might be normal during startup"
fi

print_header "DEPLOYMENT COMPLETE!"

echo ""
echo "===================================================================================="
echo "                          🎉 DEPLOYMENT SUCCESSFUL! 🎉"
echo "===================================================================================="
echo ""
echo -e "${GREEN}Your Hotel Management System is now running!${NC}"
echo ""
echo "📱 Application URLs:"
echo "   • Frontend: http://$SERVER_DOMAIN"
echo "   • Backend API: http://$SERVER_DOMAIN:8000"
echo "   • API Documentation: http://$SERVER_DOMAIN:8000/docs"
echo ""
echo "🔧 Management Commands:"
echo "   • View logs: cd $APP_DIR && docker-compose logs -f"
echo "   • Stop services: cd $APP_DIR && docker-compose down"
echo "   • Start services: cd $APP_DIR && docker-compose up -d"
echo "   • Restart services: cd $APP_DIR && docker-compose restart"
echo ""
echo "📁 Application files are located in: $APP_DIR"
echo ""
echo "🚀 Next Steps:"
echo "   1. Visit http://$SERVER_DOMAIN to access the application"
echo "   2. Click 'Initialize Sample Data' to populate the database"
echo "   3. Start managing your hotel bookings and operations!"
echo ""
echo "===================================================================================="

# Create a quick reference file
cat > $APP_DIR/README.md << EOF
# Hotel Management System - Docker Deployment

## Application URLs
- Frontend: http://$SERVER_DOMAIN
- Backend API: http://$SERVER_DOMAIN:8000
- API Documentation: http://$SERVER_DOMAIN:8000/docs

## Management Commands
- View logs: \`docker-compose logs -f\`
- Stop services: \`docker-compose down\`
- Start services: \`docker-compose up -d\`
- Restart services: \`docker-compose restart\`

## Features
- Room Management
- Booking Management
- Guest Management
- Check-in/Check-out
- Financial Reporting
- Income & Expense Tracking

## Support
If you encounter any issues, check the logs with:
\`docker-compose logs -f\`

## Customization
- Backend code: ./backend/server.py
- Frontend code: ./frontend/src/App.js
- Database: MongoDB running in Docker container
EOF

print_status "Deployment reference created at $APP_DIR/README.md"
print_status "🎉 Hotel Management System deployment completed successfully!"