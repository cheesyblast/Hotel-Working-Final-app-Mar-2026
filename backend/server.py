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

@api_router.put("/rooms/{room_id}/status")
async def update_room_status(room_id: str, status: str, guest_name: Optional[str] = None, check_in_date: Optional[date] = None, check_out_date: Optional[date] = None):
    update_data = {"status": status}
    if guest_name:
        update_data["current_guest"] = guest_name
    if check_in_date:
        update_data["check_in_date"] = check_in_date
    if check_out_date:
        update_data["check_out_date"] = check_out_date
    
    result = await db.rooms.update_one({"id": room_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"message": "Room status updated successfully"}

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

@api_router.get("/bookings/upcoming", response_model=List[Booking])
async def get_upcoming_bookings():
    today = datetime.combine(datetime.now().date(), datetime.min.time())
    bookings = await db.bookings.find({
        "status": "Upcoming",
        "check_in_date": {"$gte": today}
    }).sort("check_in_date", 1).to_list(10)
    
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

@api_router.put("/bookings/{booking_id}")
async def update_booking(booking_id: str, booking_update: BookingUpdate):
    update_data = {}
    
    # Only update fields that are provided
    if booking_update.check_in_date is not None:
        update_data['check_in_date'] = datetime.combine(booking_update.check_in_date, datetime.min.time())
    if booking_update.check_out_date is not None:
        update_data['check_out_date'] = datetime.combine(booking_update.check_out_date, datetime.min.time())
    if booking_update.additional_notes is not None:
        update_data['additional_notes'] = booking_update.additional_notes
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    result = await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking updated successfully"}

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

@api_router.post("/customers", response_model=Customer)
async def create_customer(customer: Customer):
    await db.customers.insert_one(customer.dict())
    return customer

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

@api_router.post("/cancel/{booking_id}")
async def cancel_booking(booking_id: str):
    # Find the booking
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Update booking status to cancelled
    result = await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "Cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # If room was reserved for this booking, make it available
    if booking["status"] == "Upcoming":
        await db.rooms.update_one(
            {"room_number": booking["room_number"], "status": "Reserved"},
            {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
        )
    
    return {"message": "Booking cancelled successfully"}

# Initialize sample data
@api_router.post("/init-data")
async def initialize_sample_data():
    # Check if data already exists
    existing_rooms = await db.rooms.count_documents({})
    if existing_rooms > 0:
        return {"message": "Sample data already exists"}
    
    # Create sample rooms
    sample_rooms = [
        Room(room_number="101", room_type="Suite", status="Available", price_per_night=1500.0, max_occupancy=4, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service", "Balcony"]),
        Room(room_number="102", room_type="Double", status="Occupied", current_guest="John Doe", check_in_date=date.today(), check_out_date=date(2025, 7, 15), price_per_night=8500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="103", room_type="Double", status="Available", price_per_night=6500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="201", room_type="Double", status="Available", price_per_night=9000.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="202", room_type="Triple", status="Available", price_per_night=12000.0, max_occupancy=3, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="203", room_type="Double", status="Available", price_per_night=7500.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge"]),
        Room(room_number="204", room_type="Triple", status="Available", price_per_night=11000.0, max_occupancy=3, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
        Room(room_number="205", room_type="Double", status="Reserved", price_per_night=8000.0, max_occupancy=2, amenities=["WiFi", "TV", "AC", "Mini Fridge", "Room Service"]),
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
    
    # Create sample bookings
    sample_bookings = [
        Booking(guest_name="Alice Johnson", guest_email="alice@example.com", guest_phone="123-456-7890", 
                guest_id_passport="P123456789", guest_country="USA",
                room_number="103", check_in_date=date(2025, 7, 16), check_out_date=date(2025, 7, 20), 
                stay_type="Night Stay", booking_amount=2000.0, status="Upcoming", additional_notes="Early check-in requested"),
        Booking(guest_name="Bob Smith", guest_email="bob@example.com", guest_phone="098-765-4321", 
                guest_id_passport="P987654321", guest_country="Canada",
                room_number="201", check_in_date=date(2025, 7, 18), check_out_date=date(2025, 7, 22), 
                stay_type="Night Stay", booking_amount=1800.0, status="Upcoming", additional_notes="Business traveler"),
        Booking(guest_name="Carol Davis", guest_email="carol@example.com", guest_phone="555-123-4567", 
                guest_id_passport="P555444333", guest_country="UK",
                room_number="301", check_in_date=date(2025, 7, 20), check_out_date=date(2025, 7, 25), 
                stay_type="Night Stay", booking_amount=2500.0, status="Upcoming", additional_notes="Celebrating anniversary"),
    ]
    
    for booking in sample_bookings:
        booking_dict = booking.dict()
        # Convert date objects to datetime for MongoDB compatibility
        booking_dict['check_in_date'] = datetime.combine(booking_dict['check_in_date'], datetime.min.time())
        booking_dict['check_out_date'] = datetime.combine(booking_dict['check_out_date'], datetime.min.time())
        await db.bookings.insert_one(booking_dict)
    
    # Create sample checked-in customers
    sample_customers = [
        Customer(name="John Doe", email="john@example.com", phone="111-222-3333", 
                current_room="102", check_in_date=date.today(), check_out_date=date(2025, 7, 15),
                advance_amount=200.0, notes="VIP guest", room_charges=500.0, total_amount=300.0),
        Customer(name="Jane Wilson", email="jane@example.com", phone="444-555-6666", 
                current_room="205", check_in_date=date(2025, 7, 10), check_out_date=date(2025, 7, 14),
                advance_amount=150.0, notes="Early check-in requested", room_charges=750.0, total_amount=600.0),
    ]
    
    for customer in sample_customers:
        customer_dict = customer.dict()
        # Convert date objects to datetime for MongoDB compatibility
        customer_dict['check_in_date'] = datetime.combine(customer_dict['check_in_date'], datetime.min.time())
        customer_dict['check_out_date'] = datetime.combine(customer_dict['check_out_date'], datetime.min.time())
        await db.customers.insert_one(customer_dict)
    
    # Create sample expenses
    sample_expenses = [
        Expense(description="Monthly electricity bill", amount=1500.0, category="Utilities", expense_date=date(2025, 7, 5)),
        Expense(description="Housekeeping supplies", amount=800.0, category="Maintenance", expense_date=date(2025, 7, 8)),
        Expense(description="Staff salaries", amount=25000.0, category="Staff", expense_date=date(2025, 7, 1)),
        Expense(description="Food and beverages", amount=3500.0, category="Food", expense_date=date(2025, 7, 10)),
        Expense(description="Marketing campaign", amount=2000.0, category="Marketing", expense_date=date(2025, 7, 6)),
        Expense(description="Internet and phone bills", amount=500.0, category="Utilities", expense_date=date(2025, 7, 7)),
        Expense(description="Room maintenance", amount=1200.0, category="Maintenance", expense_date=date(2025, 7, 9)),
    ]
    
    for expense in sample_expenses:
        expense_dict = expense.dict()
        # Convert date to datetime for MongoDB compatibility
        expense_dict['expense_date'] = datetime.combine(expense_dict['expense_date'], datetime.min.time())
        await db.expenses.insert_one(expense_dict)
    
    return {"message": "Sample data initialized successfully"}

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
            
            guests_dict[guest_email]['bookings'].append(booking_info)
            guests_dict[guest_email]['total_bookings'] += 1
            
            # Update stats based on booking status
            if booking.get('status') == 'Completed':
                guests_dict[guest_email]['total_stays'] += 1
                if not guests_dict[guest_email]['last_stay'] or check_out_date > guests_dict[guest_email]['last_stay']:
                    guests_dict[guest_email]['last_stay'] = check_out_date
            elif booking.get('status') == 'Upcoming':
                guests_dict[guest_email]['upcoming_bookings'] += 1
    
    # Convert dictionary to list and sort by name
    guests_list = list(guests_dict.values())
    guests_list.sort(key=lambda x: x['name'])
    
    return guests_list

@api_router.get("/guests/{guest_email}")
async def get_guest_details(guest_email: str):
    # Get all bookings for this guest
    bookings = await db.bookings.find({"guest_email": guest_email}).to_list(1000)
    
    if not bookings:
        raise HTTPException(status_code=404, detail="Guest not found")
    
    # Convert datetime back to date for response
    for booking in bookings:
        if isinstance(booking.get('check_in_date'), datetime):
            booking['check_in_date'] = booking['check_in_date'].date()
        if isinstance(booking.get('check_out_date'), datetime):
            booking['check_out_date'] = booking['check_out_date'].date()
    
    guest_info = {
        'name': bookings[0].get('guest_name'),
        'email': guest_email,
        'phone': bookings[0].get('guest_phone'),
        'bookings': [Booking(**booking) for booking in bookings]
    }
    
    return guest_info

# Reports and Analytics Routes
@api_router.get("/reports/daily")
async def get_daily_reports(start_date: Optional[str] = None, end_date: Optional[str] = None):
    # Default to last 30 days if no dates provided
    if not start_date or not end_date:
        end_date_obj = datetime.now().date()
        start_date_obj = end_date_obj - timedelta(days=30)
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    daily_data = []
    current_date = start_date_obj
    
    while current_date <= end_date_obj:
        start_datetime = datetime.combine(current_date, datetime.min.time())
        end_datetime = datetime.combine(current_date, datetime.max.time())
        
        # Calculate daily revenue from actual daily sales (payment collected)
        room_revenue = 0
        daily_sales = await db.daily_sales.find({
            "date": {"$gte": start_datetime, "$lte": end_datetime}
        }).to_list(1000)
        
        for sale in daily_sales:
            room_revenue += sale.get("total_amount", 0)
        
        # Calculate additional income (non-room income)
        additional_income = 0
        incomes = await db.incomes.find({
            "income_date": {"$gte": start_datetime, "$lte": end_datetime}
        }).to_list(1000)
        
        for income in incomes:
            additional_income += income.get("amount", 0)
        
        # Total daily revenue = room revenue + additional income
        daily_revenue = room_revenue + additional_income
        
        # Calculate daily expenses
        daily_expenses = 0
        expenses = await db.expenses.find({
            "expense_date": {"$gte": start_datetime, "$lte": end_datetime}
        }).to_list(1000)
        
        for expense in expenses:
            daily_expenses += expense.get("amount", 0)
        
        daily_profit = daily_revenue - daily_expenses
        
        daily_data.append({
            "date": current_date.strftime('%Y-%m-%d'),
            "revenue": daily_revenue,
            "room_revenue": room_revenue,
            "additional_income": additional_income,
            "expenses": daily_expenses,
            "profit": daily_profit,
            "sales_count": len(daily_sales),
            "expenses_count": len(expenses)
        })
        
        current_date += timedelta(days=1)
    
    return daily_data

@api_router.get("/reports/monthly")
async def get_monthly_reports(year: Optional[int] = None):
    if not year:
        year = datetime.now().year
    
    monthly_data = []
    
    for month in range(1, 13):
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Calculate monthly revenue from actual daily sales (payment collected)
        monthly_revenue = 0
        daily_sales = await db.daily_sales.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        for sale in daily_sales:
            monthly_revenue += sale.get("total_amount", 0)
        
        # Calculate monthly expenses
        monthly_expenses = 0
        expenses = await db.expenses.find({
            "expense_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        for expense in expenses:
            monthly_expenses += expense.get("amount", 0)
        
        monthly_profit = monthly_revenue - monthly_expenses
        
        # Calculate occupancy rate based on bookings
        total_rooms = await db.rooms.count_documents({})
        completed_bookings = await db.bookings.find({
            "status": "Completed",
            "check_out_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        occupied_days = len(completed_bookings)
        days_in_month = (end_date - start_date).days + 1
        occupancy_rate = (occupied_days / (total_rooms * days_in_month)) * 100 if total_rooms > 0 else 0
        
        monthly_data.append({
            "month": month,
            "month_name": start_date.strftime('%B'),
            "revenue": monthly_revenue,
            "expenses": monthly_expenses,
            "profit": monthly_profit,
            "sales_count": len(daily_sales),
            "occupancy_rate": round(occupancy_rate, 2)
        })
    
    return monthly_data

@api_router.get("/reports/comparison")
async def get_month_comparison():
    current_date = datetime.now()
    current_month_start = datetime(current_date.year, current_date.month, 1)
    
    # Last month calculation
    if current_date.month == 1:
        last_month_start = datetime(current_date.year - 1, 12, 1)
        last_month_end = datetime(current_date.year, 1, 1) - timedelta(days=1)
    else:
        last_month_start = datetime(current_date.year, current_date.month - 1, 1)
        last_month_end = datetime(current_date.year, current_date.month, 1) - timedelta(days=1)
    
    current_month_end = current_date
    
    async def get_month_data(start_date, end_date, label):
        # Revenue calculation from actual daily sales (payment collected)
        revenue = 0
        daily_sales = await db.daily_sales.find({
            "date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        for sale in daily_sales:
            revenue += sale.get("total_amount", 0)
        
        # Expenses calculation
        expenses = 0
        expense_records = await db.expenses.find({
            "expense_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(1000)
        
        for expense in expense_records:
            expenses += expense.get("amount", 0)
        
        profit = revenue - expenses
        
        return {
            "period": label,
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit,
            "sales_count": len(daily_sales),
            "expenses_count": len(expense_records)
        }
    
    last_month_data = await get_month_data(last_month_start, last_month_end, "Last Month")
    current_month_data = await get_month_data(current_month_start, current_month_end, "Current Month")
    
    # Calculate percentage changes
    def calculate_change(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return round(((current - previous) / previous) * 100, 2)
    
    comparison = {
        "last_month": last_month_data,
        "current_month": current_month_data,
        "changes": {
            "revenue_change": calculate_change(current_month_data["revenue"], last_month_data["revenue"]),
            "expenses_change": calculate_change(current_month_data["expenses"], last_month_data["expenses"]),
            "profit_change": calculate_change(current_month_data["profit"], last_month_data["profit"]),
            "sales_change": calculate_change(current_month_data["sales_count"], last_month_data["sales_count"])
        }
    }
    
    return comparison

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

@api_router.get("/daily-sales")
async def get_daily_sales(start_date: Optional[str] = None, end_date: Optional[str] = None):
    # Default to current month if no dates provided
    if not start_date or not end_date:
        today = datetime.now().date()
        start_date_obj = today.replace(day=1)
        end_date_obj = today
    else:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Convert dates to datetime for MongoDB query
    start_datetime = datetime.combine(start_date_obj, datetime.min.time())
    end_datetime = datetime.combine(end_date_obj, datetime.max.time())
    
    daily_sales = await db.daily_sales.find({
        "date": {"$gte": start_datetime, "$lte": end_datetime}
    }).sort("date", -1).to_list(1000)
    
    # Convert datetime back to date for response
    for sale in daily_sales:
        if isinstance(sale.get('date'), datetime):
            sale['date'] = sale['date'].date()
    
    return [DailySale(**sale) for sale in daily_sales]

@api_router.get("/financial-summary")
async def get_financial_summary(start_date: Optional[str] = None, end_date: Optional[str] = None):
    # Default to current month if no dates provided
    if not start_date or not end_date:
        today = datetime.now().date()
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Convert dates to datetime for MongoDB query
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = datetime.combine(end_date, datetime.max.time())
    
    # Calculate revenue from actual daily sales (payment collected)
    daily_sales = await db.daily_sales.find({
        "date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    room_revenue = 0
    revenue_breakdown = {}
    payment_method_breakdown = {}
    
    for sale in daily_sales:
        # Total revenue from actual payments collected
        sale_amount = sale.get("total_amount", 0)
        room_revenue += sale_amount
        
        # Revenue breakdown by room type (get room info for breakdown)
        room_number = sale.get("room_number", "")
        if room_number:
            room = await db.rooms.find_one({"room_number": room_number})
            if room:
                room_type = room.get("room_type", "Unknown")
                if room_type not in revenue_breakdown:
                    revenue_breakdown[room_type] = 0
                revenue_breakdown[room_type] += sale_amount
        
        # Payment method breakdown
        payment_method = sale.get("payment_method", "Unknown")
        if payment_method not in payment_method_breakdown:
            payment_method_breakdown[payment_method] = 0
        payment_method_breakdown[payment_method] += sale_amount
    
    # Calculate additional income (non-room income)
    additional_incomes = await db.incomes.find({
        "income_date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    additional_income_total = 0
    income_breakdown = {}
    
    for income in additional_incomes:
        amount = income.get("amount", 0)
        additional_income_total += amount
        
        category = income.get("category", "Other")
        if category not in income_breakdown:
            income_breakdown[category] = 0
        income_breakdown[category] += amount
    
    # Total revenue = room revenue + additional income
    total_revenue = room_revenue + additional_income_total
    
    # Calculate expenses
    expenses = await db.expenses.find({
        "expense_date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    total_expenses = 0
    expense_breakdown = {}
    
    for expense in expenses:
        amount = expense.get("amount", 0)
        total_expenses += amount
        
        category = expense.get("category", "Other")
        if category not in expense_breakdown:
            expense_breakdown[category] = 0
        expense_breakdown[category] += amount
    
    net_profit = total_revenue - total_expenses
    
    return {
        "total_revenue": total_revenue,
        "room_revenue": room_revenue,
        "additional_income": additional_income_total,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "revenue_breakdown": revenue_breakdown,
        "income_breakdown": income_breakdown,
        "expense_breakdown": expense_breakdown,
        "payment_method_breakdown": payment_method_breakdown,
        "period_start": start_date,
        "period_end": end_date
    }

# Test route
@api_router.get("/")
async def root():
    return {"message": "Hotel Management API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()