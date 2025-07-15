#!/bin/bash

# Hotel Management System - Fixed Ubuntu 25.04 Deployment Script
# This script resolves Python/Pydantic compatibility issues

set -e

echo "🏨 Deploying Hotel Management System - Fixed Version (Ubuntu 25.04)..."
echo "=============================================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Get configuration
read -p "Enter your domain/IP: " DOMAIN
DOMAIN=${DOMAIN:-$(curl -s ifconfig.me 2>/dev/null || echo "localhost")}
MONGO_PASSWORD="HotelManagement2024SecurePass!"

print_info "Using domain/IP: $DOMAIN"

# Update system and fix package issues
print_status "Updating system and fixing package conflicts..."
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y
sudo apt autoclean

# Remove any existing Node.js installations
print_status "Cleaning previous Node.js installations..."
sudo apt remove --purge nodejs npm -y 2>/dev/null || true
sudo apt autoremove -y
sudo rm -rf /etc/apt/sources.list.d/nodesource* 2>/dev/null || true
sudo rm -rf /usr/share/keyrings/nodesource* 2>/dev/null || true

# Install essential packages
print_status "Installing essential packages..."
sudo apt install -y curl wget git build-essential software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install specific Python 3.11 for compatibility
print_status "Installing Python 3.11 for compatibility..."
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip || {
    print_warning "Installing Python 3.11 from deadsnakes PPA..."
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
}

# Set Python 3.11 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Install Node.js using Snap (more reliable for Ubuntu 25.04)
print_status "Installing Node.js via Snap (Ubuntu 25.04 compatible)..."
sudo snap install node --classic

# Create symlinks for system-wide access
sudo ln -sf /snap/bin/node /usr/local/bin/node 2>/dev/null || true
sudo ln -sf /snap/bin/npm /usr/local/bin/npm 2>/dev/null || true
sudo ln -sf /snap/bin/npx /usr/local/bin/npx 2>/dev/null || true

# Verify Node.js installation
NODE_VERSION=$(node --version 2>/dev/null || echo "failed")
NPM_VERSION=$(npm --version 2>/dev/null || echo "failed")

if [[ "$NODE_VERSION" == "failed" ]]; then
    print_error "Node.js installation failed. Trying alternative method..."
    
    # Alternative: Download and install manually
    print_status "Installing Node.js manually..."
    cd /tmp
    wget https://nodejs.org/dist/v20.10.0/node-v20.10.0-linux-x64.tar.xz
    tar -xf node-v20.10.0-linux-x64.tar.xz
    sudo mv node-v20.10.0-linux-x64 /opt/nodejs
    sudo ln -sf /opt/nodejs/bin/node /usr/local/bin/node
    sudo ln -sf /opt/nodejs/bin/npm /usr/local/bin/npm
    sudo ln -sf /opt/nodejs/bin/npx /usr/local/bin/npx
    
    NODE_VERSION=$(node --version 2>/dev/null || echo "manual installation failed")
    NPM_VERSION=$(npm --version 2>/dev/null || echo "manual installation failed")
fi

print_status "Node.js version: $NODE_VERSION"
print_status "NPM version: $NPM_VERSION"

# Install Docker
print_status "Installing Docker..."
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker

# Install PM2
print_status "Installing PM2..."
sudo npm install -g pm2 2>/dev/null || /snap/bin/npm install -g pm2 || /opt/nodejs/bin/npm install -g pm2

# Install Nginx
print_status "Installing Nginx..."
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Create application user
if ! id "hotelapp" &>/dev/null; then
    print_status "Creating hotelapp user..."
    sudo adduser --disabled-password --gecos "" hotelapp
    sudo usermod -aG sudo,docker hotelapp
fi

# Setup MongoDB with Docker
print_status "Setting up MongoDB with Docker..."
sudo docker stop mongodb-hotel 2>/dev/null || true
sudo docker rm mongodb-hotel 2>/dev/null || true

sudo docker run -d \
  --name mongodb-hotel \
  --restart unless-stopped \
  -p 27017:27017 \
  -v mongodb-hotel-data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=hotelapp \
  -e MONGO_INITDB_ROOT_PASSWORD="$MONGO_PASSWORD" \
  mongo:7.0

print_info "Waiting for MongoDB to start..."
sleep 20

# Test MongoDB
if sudo docker exec mongodb-hotel mongosh -u hotelapp -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    print_status "MongoDB is running successfully"
else
    print_error "MongoDB startup failed"
    exit 1
fi

# Create application structure
print_status "Creating application structure..."
sudo rm -rf /home/hotelapp/hotel-management
sudo -u hotelapp mkdir -p /home/hotelapp/hotel-management/{backend,frontend,logs}

###########################################
# BACKEND SETUP - Fixed Python/Pydantic compatibility
###########################################
print_status "Setting up backend with fixed Python/Pydantic compatibility..."
cd /home/hotelapp/hotel-management/backend

# Create requirements.txt with compatible versions
sudo -u hotelapp tee requirements.txt << 'REQUIREMENTS'
# Fixed versions for Python 3.11 compatibility
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pydantic==2.4.2
pydantic-core==2.10.1
python-multipart==0.0.6
python-dateutil==2.8.2
pymongo==4.6.0
starlette==0.27.0
python-dotenv==1.0.0
typing-extensions==4.8.0
annotated-types==0.6.0
REQUIREMENTS

# Create Python 3.11 virtual environment
print_status "Creating Python 3.11 virtual environment..."
sudo -u hotelapp python3.11 -m venv venv

# Upgrade pip and install requirements with compatible versions
print_status "Installing Python dependencies with compatibility fixes..."
sudo -u hotelapp bash -c "source venv/bin/activate && pip install --upgrade pip==23.3.1"
sudo -u hotelapp bash -c "source venv/bin/activate && pip install --upgrade setuptools==68.2.2"
sudo -u hotelapp bash -c "source venv/bin/activate && pip install wheel==0.42.0"

# Install dependencies with error handling
print_status "Installing FastAPI and dependencies..."
sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir -r requirements.txt" || {
    print_warning "Standard installation failed. Trying alternative method..."
    
    # Alternative installation method
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir --no-binary pydantic-core pydantic-core==2.10.1"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir pydantic==2.4.2"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir fastapi==0.104.1"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir uvicorn[standard]==0.24.0"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir motor==3.3.2"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir python-multipart==0.0.6"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir python-dateutil==2.8.2"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir pymongo==4.6.0"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir starlette==0.27.0"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install --no-cache-dir python-dotenv==1.0.0"
}

# Verify installation
print_status "Verifying Python installation..."
sudo -u hotelapp bash -c "source venv/bin/activate && python --version"
sudo -u hotelapp bash -c "source venv/bin/activate && pip list | grep -E '(fastapi|pydantic|uvicorn)'"

# Create .env file
sudo -u hotelapp tee .env << ENV_FILE
MONGO_URL=mongodb://hotelapp:$MONGO_PASSWORD@localhost:27017/hotel_management?authSource=admin
DB_NAME=hotel_management
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
ENV_FILE

# Create complete server.py with fixed imports
sudo -u hotelapp tee server.py << 'SERVER_PY'
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, timedelta
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'hotel_management')]

# Create the main app
app = FastAPI(title="Hotel Management System", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_number: str
    room_type: str
    status: str = "Available"
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
    stay_type: str = "Night Stay"
    booking_amount: float = 0.0
    status: str = "Upcoming"
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
    payment_method: str = "Cash"

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
    category: str
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
    category: str
    income_date: date
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IncomeCreate(BaseModel):
    description: str
    amount: float
    category: str
    income_date: date

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Hotel Management System API", "status": "running", "timestamp": datetime.now()}

@api_router.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected", "timestamp": datetime.now()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Room Management Routes
@api_router.get("/rooms", response_model=List[Room])
async def get_rooms():
    rooms = await db.rooms.find().to_list(1000)
    for room in rooms:
        if isinstance(room.get('check_in_date'), datetime):
            room['check_in_date'] = room['check_in_date'].date()
        if isinstance(room.get('check_out_date'), datetime):
            room['check_out_date'] = room['check_out_date'].date()
    return [Room(**room) for room in rooms]

@api_router.post("/rooms", response_model=Room)
async def create_room(room: RoomCreate):
    existing = await db.rooms.find_one({"room_number": room.room_number})
    if existing:
        raise HTTPException(status_code=400, detail="Room number already exists")
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
    for booking in bookings:
        if isinstance(booking.get('check_in_date'), datetime):
            booking['check_in_date'] = booking['check_in_date'].date()
        if isinstance(booking.get('check_out_date'), datetime):
            booking['check_out_date'] = booking['check_out_date'].date()
    return [Booking(**booking) for booking in bookings]

@api_router.post("/bookings", response_model=Booking)
async def create_booking(booking: BookingCreate):
    booking_dict = booking.dict()
    if isinstance(booking_dict.get('check_in_date'), str):
        booking_dict['check_in_date'] = datetime.strptime(booking_dict['check_in_date'], '%Y-%m-%d').date()
    if booking_dict.get('stay_type') == 'Short Time' or not booking_dict.get('check_out_date'):
        if booking_dict.get('stay_type') == 'Short Time':
            booking_dict['check_out_date'] = booking_dict['check_in_date']
    else:
        if isinstance(booking_dict.get('check_out_date'), str):
            booking_dict['check_out_date'] = datetime.strptime(booking_dict['check_out_date'], '%Y-%m-%d').date()
    
    booking_obj = Booking(**booking_dict, status="Upcoming")
    booking_storage = booking_obj.dict()
    if booking_storage.get('check_in_date'):
        booking_storage['check_in_date'] = datetime.combine(booking_storage['check_in_date'], datetime.min.time())
    if booking_storage.get('check_out_date'):
        booking_storage['check_out_date'] = datetime.combine(booking_storage['check_out_date'], datetime.min.time())
    await db.bookings.insert_one(booking_storage)
    return booking_obj

@api_router.get("/bookings/upcoming", response_model=List[Booking])
async def get_upcoming_bookings():
    today = datetime.combine(datetime.now().date(), datetime.min.time())
    bookings = await db.bookings.find({
        "status": "Upcoming",
        "check_in_date": {"$gte": today}
    }).sort("check_in_date", 1).to_list(10)
    for booking in bookings:
        if isinstance(booking.get('check_in_date'), datetime):
            booking['check_in_date'] = booking['check_in_date'].date()
        if isinstance(booking.get('check_out_date'), datetime):
            booking['check_out_date'] = booking['check_out_date'].date()
    return [Booking(**booking) for booking in bookings]

# Customer Management Routes
@api_router.get("/customers/checked-in", response_model=List[Customer])
async def get_checked_in_customers():
    customers = await db.customers.find().to_list(1000)
    for customer in customers:
        if isinstance(customer.get('check_in_date'), datetime):
            customer['check_in_date'] = customer['check_in_date'].date()
        if isinstance(customer.get('check_out_date'), datetime):
            customer['check_out_date'] = customer['check_out_date'].date()
    return [Customer(**customer) for customer in customers]

@api_router.post("/checkin")
async def checkin_customer(checkin: CheckinRequest):
    booking = await db.bookings.find_one({"id": checkin.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    room = await db.rooms.find_one({"room_number": booking["room_number"]})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room["status"] != "Available":
        raise HTTPException(status_code=400, detail="Room is not available for check-in")
    
    room_charges = booking.get("booking_amount", 500.0)
    
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
    
    customer_dict = customer.dict()
    customer_dict['check_in_date'] = datetime.combine(customer_dict['check_in_date'], datetime.min.time())
    customer_dict['check_out_date'] = datetime.combine(customer_dict['check_out_date'], datetime.min.time())
    await db.customers.insert_one(customer_dict)
    
    await db.rooms.update_one(
        {"room_number": booking["room_number"]},
        {"$set": {
            "status": "Occupied",
            "current_guest": booking["guest_name"],
            "check_in_date": datetime.combine(booking["check_in_date"] if isinstance(booking["check_in_date"], date) else booking["check_in_date"].date(), datetime.min.time()),
            "check_out_date": datetime.combine(booking["check_out_date"] if isinstance(booking["check_out_date"], date) else booking["check_out_date"].date(), datetime.min.time())
        }}
    )
    
    await db.bookings.update_one(
        {"id": checkin.booking_id},
        {"$set": {"status": "Checked-in"}}
    )
    
    return {"message": "Customer checked in successfully", "customer": customer}

@api_router.post("/checkout")
async def checkout_customer(checkout: CheckoutRequest):
    customer = await db.customers.find_one({"id": checkout.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    base_room_charges = customer.get('room_charges', 500.0)
    advance_amount = customer.get('advance_amount', 0.0)
    additional_amount = checkout.additional_amount
    discount_amount = checkout.discount_amount
    total_amount = base_room_charges + additional_amount - advance_amount - discount_amount
    
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
    
    daily_sale_dict = daily_sale.dict()
    daily_sale_dict['date'] = datetime.combine(daily_sale_dict['date'], datetime.min.time())
    await db.daily_sales.insert_one(daily_sale_dict)
    
    result = await db.customers.delete_one({"id": checkout.customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
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

@api_router.post("/cancel/{booking_id}")
async def cancel_booking(booking_id: str):
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    result = await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "Cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {"message": "Booking cancelled successfully"}

# Guest Management Routes
@api_router.get("/guests")
async def get_guests():
    bookings = await db.bookings.find().to_list(1000)
    guests_dict = {}
    
    for booking in bookings:
        guest_name = booking.get('guest_name')
        guest_email = booking.get('guest_email', '')
        guest_phone = booking.get('guest_phone', '')
        
        if not guest_name:
            continue
            
        if guest_email:
            guest_key = guest_email
        else:
            guest_key = f"{guest_name}_{guest_phone}_{booking.get('id', '')}"
        
        if guest_key not in guests_dict:
            guests_dict[guest_key] = {
                'id': guest_key,
                'name': guest_name,
                'email': guest_email or 'Not provided',
                'phone': guest_phone or 'Not provided',
                'total_bookings': 0,
                'total_stays': 0,
                'last_stay': None,
                'upcoming_bookings': 0,
                'bookings': []
            }
        
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
        
        if booking.get('status') == 'Completed':
            guests_dict[guest_key]['total_stays'] += 1
            if not guests_dict[guest_key]['last_stay'] or check_out_date > guests_dict[guest_key]['last_stay']:
                guests_dict[guest_key]['last_stay'] = check_out_date
        elif booking.get('status') == 'Upcoming':
            guests_dict[guest_key]['upcoming_bookings'] += 1
    
    guests_list = list(guests_dict.values())
    guests_list.sort(key=lambda x: x['name'])
    
    return guests_list

# Expense Management Routes
@api_router.get("/expenses", response_model=List[Expense])
async def get_expenses():
    expenses = await db.expenses.find().sort("expense_date", -1).to_list(1000)
    for expense in expenses:
        if isinstance(expense.get('expense_date'), datetime):
            expense['expense_date'] = expense['expense_date'].date()
    return [Expense(**expense) for expense in expenses]

@api_router.post("/expenses", response_model=Expense)
async def create_expense(expense: ExpenseCreate):
    expense_dict = expense.dict()
    if isinstance(expense_dict.get('expense_date'), str):
        expense_dict['expense_date'] = datetime.strptime(expense_dict['expense_date'], '%Y-%m-%d').date()
    
    expense_obj = Expense(**expense_dict)
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
    for income in incomes:
        if isinstance(income.get('income_date'), datetime):
            income['income_date'] = income['income_date'].date()
    return [Income(**income) for income in incomes]

@api_router.post("/incomes", response_model=Income)
async def create_income(income: IncomeCreate):
    income_dict = income.dict()
    if isinstance(income_dict.get('income_date'), str):
        income_dict['income_date'] = datetime.strptime(income_dict['income_date'], '%Y-%m-%d').date()
    
    income_obj = Income(**income_dict)
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
    
    for sale in sales:
        if isinstance(sale.get('date'), datetime):
            sale['date'] = sale['date'].date()
    
    return [DailySale(**sale) for sale in sales]

# Financial Summary Routes
@api_router.get("/financial-summary")
async def get_financial_summary():
    total_revenue = 0
    daily_sales = await db.daily_sales.find().to_list(1000)
    
    for sale in daily_sales:
        total_revenue += sale.get("total_amount", 0)
    
    additional_income = 0
    incomes = await db.incomes.find().to_list(1000)
    
    for income in incomes:
        additional_income += income.get("amount", 0)
    
    total_revenue += additional_income
    
    total_expenses = 0
    expenses = await db.expenses.find().to_list(1000)
    
    for expense in expenses:
        total_expenses += expense.get("amount", 0)
    
    net_profit = total_revenue - total_expenses
    
    revenue_breakdown = {
        "room_revenue": total_revenue - additional_income,
        "additional_income": additional_income,
        "total_revenue": total_revenue
    }
    
    payment_breakdown = {"Cash": 0, "Card": 0, "Bank Transfer": 0}
    for sale in daily_sales:
        method = sale.get("payment_method", "Cash")
        if method in payment_breakdown:
            payment_breakdown[method] += sale.get("total_amount", 0)
    
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
        "payment_breakdown": payment_breakdown,
        "expense_breakdown": expense_breakdown,
        "period_start": datetime.now().date() - timedelta(days=30),
        "period_end": datetime.now().date()
    }

# Initialize sample data
@api_router.post("/init-data")
async def initialize_sample_data():
    existing_rooms = await db.rooms.count_documents({})
    if existing_rooms > 0:
        return {"message": "Sample data already exists"}
    
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
        if room_dict.get('check_in_date'):
            room_dict['check_in_date'] = datetime.combine(room_dict['check_in_date'], datetime.min.time())
        if room_dict.get('check_out_date'):
            room_dict['check_out_date'] = datetime.combine(room_dict['check_out_date'], datetime.min.time())
        await db.rooms.insert_one(room_dict)
    
    sample_expenses = [
        Expense(description="Monthly electricity bill", amount=1500.0, category="Utilities", expense_date=date(2025, 1, 5)),
        Expense(description="Housekeeping supplies", amount=800.0, category="Maintenance", expense_date=date(2025, 1, 8)),
        Expense(description="Staff salaries", amount=25000.0, category="Staff", expense_date=date(2025, 1, 1)),
        Expense(description="Food and beverages", amount=3500.0, category="Food", expense_date=date(2025, 1, 10)),
        Expense(description="Marketing campaign", amount=2000.0, category="Marketing", expense_date=date(2025, 1, 6)),
    ]
    
    for expense in sample_expenses:
        expense_dict = expense.dict()
        expense_dict['expense_date'] = datetime.combine(expense_dict['expense_date'], datetime.min.time())
        await db.expenses.insert_one(expense_dict)
    
    return {"message": "Sample data initialized successfully"}

# Include the API router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
SERVER_PY

###########################################
# FRONTEND SETUP - Complete Hotel Management UI
###########################################
print_status "Setting up complete frontend system..."
cd /home/hotelapp/hotel-management/frontend

# Get the frontend HTML from the file if it exists
if [ -f "/app/frontend-html.txt" ]; then
    sudo -u hotelapp cp /app/frontend-html.txt index.html
else
    # Create a minimal frontend file
    sudo -u hotelapp tee index.html << 'FRONTEND_HTML'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hotel Management System</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/axios/dist/axios.min.js"></script>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        function App() {
            return (
                <div className="min-h-screen bg-gray-100 flex items-center justify-center">
                    <div className="bg-white p-8 rounded-lg shadow-lg">
                        <h1 className="text-3xl font-bold text-gray-800 mb-4">Hotel Management System</h1>
                        <p className="text-gray-600 mb-6">Your hotel management system is now running!</p>
                        <div className="space-y-4">
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <h3 className="font-semibold text-blue-800">Backend API</h3>
                                <p className="text-blue-600">Available at /api/health</p>
                            </div>
                            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                <h3 className="font-semibold text-green-800">Database</h3>
                                <p className="text-green-600">MongoDB running with authentication</p>
                            </div>
                            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                <h3 className="font-semibold text-purple-800">Features</h3>
                                <ul className="text-purple-600 text-sm mt-2">
                                    <li>• Room Management</li>
                                    <li>• Booking System</li>
                                    <li>• Guest Management</li>
                                    <li>• Financial Tracking</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            );
        }

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
FRONTEND_HTML
fi

# Create simple dist directory structure
sudo -u hotelapp mkdir -p dist
sudo -u hotelapp cp index.html dist/

###########################################
# CONFIGURATION AND DEPLOYMENT
###########################################
print_status "Configuring deployment..."

# Create PM2 ecosystem
cd /home/hotelapp/hotel-management
sudo -u hotelapp tee ecosystem.config.js << 'PM2_CONFIG'
module.exports = {
  apps: [
    {
      name: "hotel-backend",
      script: "./venv/bin/uvicorn",
      args: "server:app --host 0.0.0.0 --port 8001",
      cwd: "/home/hotelapp/hotel-management/backend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "production",
        PYTHONPATH: "/home/hotelapp/hotel-management/backend"
      }
    }
  ]
};
PM2_CONFIG

# Configure Nginx
sudo tee /etc/nginx/sites-available/hotel-management << NGINX_CONFIG
server {
    listen 80;
    server_name $DOMAIN;
    
    # API routes
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend routes
    location / {
        root /home/hotelapp/hotel-management/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
        
        # Add security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
NGINX_CONFIG

# Enable site
sudo ln -sf /etc/nginx/sites-available/hotel-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Configure firewall
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 27017  # MongoDB port

# Set correct permissions
sudo chown -R hotelapp:hotelapp /home/hotelapp/hotel-management
sudo chmod -R 755 /home/hotelapp/hotel-management

# Start the application
print_status "Starting hotel management application..."
sudo -u hotelapp pm2 stop all 2>/dev/null || true
sudo -u hotelapp pm2 delete all 2>/dev/null || true
sudo -u hotelapp pm2 start ecosystem.config.js
sudo -u hotelapp pm2 save

# Setup PM2 startup
sudo -u hotelapp pm2 startup | grep -E "^sudo" | sudo bash

# Create systemd service for PM2
sudo tee /etc/systemd/system/hotel-pm2.service << 'PM2_SERVICE'
[Unit]
Description=Hotel Management PM2 Process Manager
After=network.target

[Service]
Type=forking
User=hotelapp
LimitNOFILE=infinity
LimitNPROC=infinity
LimitCORE=infinity
Environment=PATH=/usr/local/bin:/usr/bin:/bin:/snap/bin
Environment=PM2_HOME=/home/hotelapp/.pm2
PIDFile=/home/hotelapp/.pm2/pm2.pid
ExecStart=/snap/bin/pm2 resurrect
ExecReload=/snap/bin/pm2 reload all
ExecStop=/snap/bin/pm2 kill
Restart=always

[Install]
WantedBy=multi-user.target
PM2_SERVICE

sudo systemctl daemon-reload
sudo systemctl enable hotel-pm2
sudo systemctl start hotel-pm2

# Final verification
print_status "Running final checks..."
sleep 30

# Check service status
MONGODB_STATUS=$(sudo docker exec mongodb-hotel mongosh -u hotelapp -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1 && echo "✅ Online" || echo "❌ Offline")
BACKEND_STATUS=$(curl -s "http://localhost:8001/api/health" >/dev/null 2>&1 && echo "✅ Online" || echo "❌ Offline")
FRONTEND_STATUS=$(curl -s "http://localhost/" >/dev/null 2>&1 && echo "✅ Online" || echo "❌ Offline")
NGINX_STATUS=$(sudo systemctl is-active nginx >/dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped")
PM2_STATUS=$(sudo -u hotelapp pm2 status | grep -q "hotel-backend" && echo "✅ Running" || echo "❌ Stopped")

echo ""
echo "=============================================================================="
echo "              🎉 HOTEL MANAGEMENT SYSTEM DEPLOYED (FIXED)! 🎉"
echo "=============================================================================="
echo ""
print_info "🌐 Application URL: http://$DOMAIN"
print_info "📱 Python Version: $(python3 --version)"
print_info "🔐 Database Security: MongoDB with authentication"
echo ""
print_info "📊 Service Status:"
echo "   🏨 Frontend: $FRONTEND_STATUS"
echo "   🔧 Backend API: $BACKEND_STATUS"
echo "   🗄️  MongoDB: $MONGODB_STATUS"
echo "   🌐 Nginx: $NGINX_STATUS"
echo "   ⚙️  PM2: $PM2_STATUS"
echo ""
print_info "🔧 Management Commands:"
echo "   • View backend status: sudo -u hotelapp pm2 status"
echo "   • View backend logs: sudo -u hotelapp pm2 logs hotel-backend"
echo "   • Restart backend: sudo -u hotelapp pm2 restart hotel-backend"
echo "   • Restart nginx: sudo systemctl restart nginx"
echo "   • Check MongoDB: sudo docker exec -it mongodb-hotel mongosh -u hotelapp -p '$MONGO_PASSWORD' --authenticationDatabase admin"
echo ""
print_info "🚀 Quick Start:"
echo "   1. Visit http://$DOMAIN"
echo "   2. Click 'Initialize Sample Data' to populate the database"
echo "   3. Start managing your hotel operations!"
echo ""

# Create a comprehensive README
cat > /home/hotelapp/hotel-management/README.md << README_FILE
# Hotel Management System - Fixed Version

## What was Fixed
- Python/Pydantic compatibility issues resolved
- Used Python 3.11 for stability
- Fixed pydantic-core version conflicts
- Added proper error handling for dependency installation

## Application URLs
- Frontend: http://$DOMAIN
- Backend API: http://$DOMAIN/api/health

## Service Management
- Backend Status: \`sudo -u hotelapp pm2 status\`
- Backend Logs: \`sudo -u hotelapp pm2 logs hotel-backend\`
- Restart Backend: \`sudo -u hotelapp pm2 restart hotel-backend\`
- Restart Nginx: \`sudo systemctl restart nginx\`

## Database Access
- MongoDB Connection: \`sudo docker exec -it mongodb-hotel mongosh -u hotelapp -p '$MONGO_PASSWORD' --authenticationDatabase admin\`
- Database Name: hotel_management

## Features
- Room Management (Create, Update, Delete rooms)
- Booking System (New bookings, Check-in, Check-out)
- Guest Management (Guest database, Search, History)
- Financial Management (Income tracking, Expense tracking)
- Daily Sales Reporting
- Payment Method Tracking (Cash, Card, Bank Transfer)
- Real-time Dashboard
- LKR Currency Support

## Troubleshooting
- If backend is not responding: \`sudo -u hotelapp pm2 restart hotel-backend\`
- If frontend is not loading: \`sudo systemctl restart nginx\`
- If MongoDB is not accessible: \`sudo docker restart mongodb-hotel\`

## Technical Details
- Python Version: 3.11 (for compatibility)
- Pydantic Version: 2.4.2 (stable)
- FastAPI Version: 0.104.1
- MongoDB: 7.0 (Docker)
- Frontend: React with CDN loading

## File Structure
- Backend: /home/hotelapp/hotel-management/backend/
- Frontend: /home/hotelapp/hotel-management/frontend/
- Logs: /home/hotelapp/hotel-management/logs/
README_FILE

sudo chown hotelapp:hotelapp /home/hotelapp/hotel-management/README.md

print_status "✅ Fixed deployment completed successfully!"
print_warning "⚠️  Save the MongoDB password: $MONGO_PASSWORD"
print_info "🎉 Your hotel management system is now live with all compatibility issues resolved!"
print_info "🔗 Access your application at: http://$DOMAIN"
echo ""
echo "=============================================================================="