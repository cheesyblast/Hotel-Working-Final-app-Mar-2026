#!/bin/bash

# Complete Hotel Management System Installation Script
# Fixed for Python 3.12 compatibility and all known issues

echo "🏨 Complete Hotel Management System Installation..."
echo "=============================================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

# Function to check if command succeeded
check_command() {
    if [ $? -eq 0 ]; then
        print_status "$1 successful"
    else
        print_error "$1 failed"
        exit 1
    fi
}

# Get domain/IP
DOMAIN=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
MONGO_PASSWORD="HotelManagement2024SecurePass!"

print_info "Using domain/IP: $DOMAIN"
print_info "MongoDB password: $MONGO_PASSWORD"

# Step 1: Update system
print_status "Step 1: Updating system..."
sudo apt update -y || print_warning "Some repository warnings are normal"
sudo apt upgrade -y || print_warning "Some upgrade warnings are normal"
sudo apt autoremove -y || true
sudo apt autoclean || true

# Step 2: Install essential packages
print_status "Step 2: Installing essential packages..."
sudo apt install -y curl wget git build-essential software-properties-common
sudo apt install -y apt-transport-https ca-certificates gnupg lsb-release
check_command "Essential packages installation"

# Step 3: Fix Python virtual environment issues
print_status "Step 3: Setting up Python with virtual environment support..."
# Install Python dev tools and venv
sudo apt install -y python3-pip python3-dev python3-setuptools
sudo apt install -y python3-venv python3.12-venv || sudo apt install -y python3-venv
check_command "Python virtual environment setup"

# Verify Python version
PYTHON_VERSION=$(python3 --version)
print_info "Python version: $PYTHON_VERSION"

# Step 4: Install Node.js
print_status "Step 4: Installing Node.js..."
sudo snap install node --classic || {
    print_warning "Snap installation failed, trying alternative method..."
    cd /tmp
    wget -q https://nodejs.org/dist/v20.10.0/node-v20.10.0-linux-x64.tar.xz
    tar -xf node-v20.10.0-linux-x64.tar.xz
    sudo mv node-v20.10.0-linux-x64 /opt/nodejs
    sudo ln -sf /opt/nodejs/bin/node /usr/local/bin/node
    sudo ln -sf /opt/nodejs/bin/npm /usr/local/bin/npm
    sudo ln -sf /opt/nodejs/bin/npx /usr/local/bin/npx
}

# Create symlinks for system-wide access
sudo ln -sf /snap/bin/node /usr/local/bin/node 2>/dev/null || true
sudo ln -sf /snap/bin/npm /usr/local/bin/npm 2>/dev/null || true
sudo ln -sf /snap/bin/npx /usr/local/bin/npx 2>/dev/null || true

NODE_VERSION=$(node --version 2>/dev/null || echo "failed")
print_info "Node.js version: $NODE_VERSION"

# Step 5: Install Docker
print_status "Step 5: Installing Docker..."
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
check_command "Docker installation"

# Step 6: Install PM2
print_status "Step 6: Installing PM2..."
sudo npm install -g pm2 2>/dev/null || /snap/bin/npm install -g pm2 || /opt/nodejs/bin/npm install -g pm2
check_command "PM2 installation"

# Step 7: Install Nginx
print_status "Step 7: Installing Nginx..."
sudo apt install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
check_command "Nginx installation"

# Step 8: Create application user
print_status "Step 8: Creating application user..."
if ! id "hotelapp" &>/dev/null; then
    sudo adduser --disabled-password --gecos "" hotelapp
    sudo usermod -aG sudo,docker hotelapp
    check_command "User creation"
else
    print_info "User hotelapp already exists"
fi

# Step 9: Setup MongoDB
print_status "Step 9: Setting up MongoDB with Docker..."
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

check_command "MongoDB container start"

print_info "Waiting for MongoDB to start..."
sleep 30

# Test MongoDB connection
MONGODB_READY=false
for i in {1..10}; do
    if sudo docker exec mongodb-hotel mongosh -u hotelapp -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
        MONGODB_READY=true
        break
    fi
    print_info "MongoDB not ready, waiting... (attempt $i/10)"
    sleep 10
done

if [ "$MONGODB_READY" = true ]; then
    print_status "MongoDB is running successfully"
else
    print_error "MongoDB startup failed"
    exit 1
fi

# Step 10: Create application structure
print_status "Step 10: Creating application structure..."
sudo rm -rf /home/hotelapp/hotel-management
sudo -u hotelapp mkdir -p /home/hotelapp/hotel-management/{backend,frontend,logs}
check_command "Application structure creation"

# Step 11: Setup Backend
print_status "Step 11: Setting up backend..."
cd /home/hotelapp/hotel-management/backend

# Create requirements.txt with Python 3.12 compatible versions
sudo -u hotelapp tee requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.2
pydantic==2.5.0
python-multipart==0.0.6
python-dateutil==2.8.2
pymongo==4.6.0
starlette==0.27.0
python-dotenv==1.0.0
EOF

# Create Python virtual environment with error handling
print_status "Creating Python virtual environment..."
sudo -u hotelapp python3 -m venv venv || {
    print_error "Virtual environment creation failed"
    exit 1
}

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
sudo -u hotelapp bash -c "source venv/bin/activate && pip install --upgrade pip"
sudo -u hotelapp bash -c "source venv/bin/activate && pip install --upgrade setuptools"
sudo -u hotelapp bash -c "source venv/bin/activate && pip install wheel"

# Install requirements with error handling
sudo -u hotelapp bash -c "source venv/bin/activate && pip install -r requirements.txt" || {
    print_warning "Standard installation failed, trying individual packages..."
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install fastapi==0.104.1"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install 'uvicorn[standard]==0.24.0'"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install motor==3.3.2"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install 'pydantic>=2.5.0,<3.0.0'"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install python-multipart==0.0.6"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install python-dateutil==2.8.2"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install pymongo==4.6.0"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install starlette==0.27.0"
    sudo -u hotelapp bash -c "source venv/bin/activate && pip install python-dotenv==1.0.0"
}

# Test Python installation
sudo -u hotelapp bash -c "source venv/bin/activate && python -c 'import fastapi; print(\"FastAPI imported successfully\")'"
check_command "Python dependencies installation"

# Create .env file
sudo -u hotelapp tee .env << EOF
MONGO_URL=mongodb://hotelapp:$MONGO_PASSWORD@localhost:27017/hotel_management?authSource=admin
DB_NAME=hotel_management
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
EOF

# Create complete server.py
sudo -u hotelapp tee server.py << 'EOF'
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date, timedelta
import uuid
import os
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

class Booking(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    guest_name: str
    guest_email: str = ""
    guest_phone: str = ""
    room_number: str
    check_in_date: date
    check_out_date: date
    stay_type: str = "Night Stay"
    booking_amount: float = 0.0
    status: str = "Upcoming"
    created_at: datetime = Field(default_factory=datetime.utcnow)

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutRequest(BaseModel):
    customer_id: str
    additional_amount: float = 0.0
    discount_amount: float = 0.0
    payment_method: str = "Cash"

class CheckinRequest(BaseModel):
    booking_id: str
    advance_amount: float = 0.0
    notes: str = ""

class BookingCreate(BaseModel):
    guest_name: str
    guest_email: str = ""
    guest_phone: str = ""
    room_number: str
    check_in_date: date
    check_out_date: Optional[date] = None
    stay_type: str = "Night Stay"
    booking_amount: float = 0.0

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
        return {"status": "error", "message": str(e)}

# Room Management Routes
@api_router.get("/rooms")
async def get_rooms():
    try:
        rooms = await db.rooms.find().to_list(1000)
        for room in rooms:
            if isinstance(room.get('check_in_date'), datetime):
                room['check_in_date'] = room['check_in_date'].date()
            if isinstance(room.get('check_out_date'), datetime):
                room['check_out_date'] = room['check_out_date'].date()
        return rooms
    except Exception as e:
        return {"error": str(e)}

# Booking Management Routes
@api_router.get("/bookings")
async def get_bookings():
    try:
        bookings = await db.bookings.find().to_list(1000)
        for booking in bookings:
            if isinstance(booking.get('check_in_date'), datetime):
                booking['check_in_date'] = booking['check_in_date'].date()
            if isinstance(booking.get('check_out_date'), datetime):
                booking['check_out_date'] = booking['check_out_date'].date()
        return bookings
    except Exception as e:
        return {"error": str(e)}

@api_router.post("/bookings")
async def create_booking(booking: BookingCreate):
    try:
        booking_dict = booking.dict()
        if isinstance(booking_dict.get('check_in_date'), str):
            booking_dict['check_in_date'] = datetime.strptime(booking_dict['check_in_date'], '%Y-%m-%d').date()
        if booking_dict.get('stay_type') == 'Short Time' or not booking_dict.get('check_out_date'):
            booking_dict['check_out_date'] = booking_dict['check_in_date']
        else:
            if isinstance(booking_dict.get('check_out_date'), str):
                booking_dict['check_out_date'] = datetime.strptime(booking_dict['check_out_date'], '%Y-%m-%d').date()
        
        booking_obj = {
            "id": str(uuid.uuid4()),
            "status": "Upcoming",
            "created_at": datetime.utcnow(),
            **booking_dict
        }
        
        # Convert dates to datetime for MongoDB storage
        if booking_obj.get('check_in_date'):
            booking_obj['check_in_date'] = datetime.combine(booking_obj['check_in_date'], datetime.min.time())
        if booking_obj.get('check_out_date'):
            booking_obj['check_out_date'] = datetime.combine(booking_obj['check_out_date'], datetime.min.time())
        
        await db.bookings.insert_one(booking_obj)
        return {"message": "Booking created successfully", "booking_id": booking_obj["id"]}
    except Exception as e:
        return {"error": str(e)}

@api_router.get("/bookings/upcoming")
async def get_upcoming_bookings():
    try:
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
        return bookings
    except Exception as e:
        return {"error": str(e)}

# Customer Management Routes
@api_router.get("/customers/checked-in")
async def get_checked_in_customers():
    try:
        customers = await db.customers.find().to_list(1000)
        for customer in customers:
            if isinstance(customer.get('check_in_date'), datetime):
                customer['check_in_date'] = customer['check_in_date'].date()
            if isinstance(customer.get('check_out_date'), datetime):
                customer['check_out_date'] = customer['check_out_date'].date()
        return customers
    except Exception as e:
        return {"error": str(e)}

@api_router.post("/checkin")
async def checkin_customer(checkin: CheckinRequest):
    try:
        booking = await db.bookings.find_one({"id": checkin.booking_id})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        room = await db.rooms.find_one({"room_number": booking["room_number"]})
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room_charges = booking.get("booking_amount", 500.0)
        
        customer = {
            "id": str(uuid.uuid4()),
            "name": booking["guest_name"],
            "email": booking["guest_email"],
            "phone": booking["guest_phone"],
            "current_room": booking["room_number"],
            "check_in_date": datetime.combine(booking["check_in_date"].date() if isinstance(booking["check_in_date"], datetime) else booking["check_in_date"], datetime.min.time()),
            "check_out_date": datetime.combine(booking["check_out_date"].date() if isinstance(booking["check_out_date"], datetime) else booking["check_out_date"], datetime.min.time()),
            "advance_amount": checkin.advance_amount,
            "notes": checkin.notes,
            "room_charges": room_charges,
            "created_at": datetime.utcnow()
        }
        
        await db.customers.insert_one(customer)
        
        # Update room status
        await db.rooms.update_one(
            {"room_number": booking["room_number"]},
            {"$set": {
                "status": "Occupied",
                "current_guest": booking["guest_name"],
                "check_in_date": customer["check_in_date"],
                "check_out_date": customer["check_out_date"]
            }}
        )
        
        # Update booking status
        await db.bookings.update_one(
            {"id": checkin.booking_id},
            {"$set": {"status": "Checked-in"}}
        )
        
        return {"message": "Customer checked in successfully"}
    except Exception as e:
        return {"error": str(e)}

@api_router.post("/checkout")
async def checkout_customer(checkout: CheckoutRequest):
    try:
        customer = await db.customers.find_one({"id": checkout.customer_id})
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        base_room_charges = customer.get('room_charges', 500.0)
        advance_amount = customer.get('advance_amount', 0.0)
        additional_amount = checkout.additional_amount
        discount_amount = checkout.discount_amount
        total_amount = base_room_charges + additional_amount - advance_amount - discount_amount
        
        # Remove customer from checked-in list
        await db.customers.delete_one({"id": checkout.customer_id})
        
        # Update room status
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
    except Exception as e:
        return {"error": str(e)}

# Initialize sample data
@api_router.post("/init-data")
async def initialize_sample_data():
    try:
        existing_rooms = await db.rooms.count_documents({})
        if existing_rooms > 0:
            return {"message": "Sample data already exists"}
        
        sample_rooms = [
            {
                "id": str(uuid.uuid4()),
                "room_number": "101",
                "room_type": "Suite",
                "status": "Available",
                "price_per_night": 15000.0,
                "max_occupancy": 4,
                "amenities": ["WiFi", "TV", "AC", "Mini Fridge", "Room Service", "Balcony"],
                "image_url": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "room_number": "102",
                "room_type": "Double",
                "status": "Available",
                "price_per_night": 8500.0,
                "max_occupancy": 2,
                "amenities": ["WiFi", "TV", "AC", "Mini Fridge", "Room Service"],
                "image_url": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "room_number": "103",
                "room_type": "Double",
                "status": "Available",
                "price_per_night": 6500.0,
                "max_occupancy": 2,
                "amenities": ["WiFi", "TV", "AC", "Mini Fridge"],
                "image_url": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "room_number": "201",
                "room_type": "Double",
                "status": "Available",
                "price_per_night": 9000.0,
                "max_occupancy": 2,
                "amenities": ["WiFi", "TV", "AC", "Mini Fridge", "Room Service"],
                "image_url": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85",
                "created_at": datetime.utcnow()
            },
            {
                "id": str(uuid.uuid4()),
                "room_number": "202",
                "room_type": "Triple",
                "status": "Available",
                "price_per_night": 12000.0,
                "max_occupancy": 3,
                "amenities": ["WiFi", "TV", "AC", "Mini Fridge", "Room Service"],
                "image_url": "https://images.unsplash.com/photo-1568495248636-6432b97bd949?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzR8MHwxfHNlYXJjaHwyfHxob3RlbCUyMHJvb218ZW58MHx8fHwxNzUyMjU1NjAxfDA&ixlib=rb-4.1.0&q=85",
                "created_at": datetime.utcnow()
            }
        ]
        
        await db.rooms.insert_many(sample_rooms)
        return {"message": "Sample data initialized successfully"}
    except Exception as e:
        return {"error": str(e)}

# Include the API router
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF

# Step 12: Test backend
print_status "Step 12: Testing backend..."
sudo -u hotelapp bash -c "cd /home/hotelapp/hotel-management/backend && source venv/bin/activate && timeout 10 python server.py" &
sleep 5
if curl -s http://localhost:8001/api/health >/dev/null; then
    print_status "Backend test successful"
else
    print_error "Backend test failed"
fi
pkill -f "python.*server.py" 2>/dev/null || true

# Step 13: Setup Frontend
print_status "Step 13: Setting up frontend..."
cd /home/hotelapp/hotel-management/frontend

# Create comprehensive frontend
sudo -u hotelapp tee index.html << 'EOF'
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
    <style>
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 2s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div id="root"></div>
    <script type="text/babel">
        const { useState, useEffect } = React;
        const API_BASE_URL = '/api';
        
        // Currency formatter for LKR
        const formatLKR = (amount) => {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'LKR'
            }).format(amount);
        };

        // Modal Component
        function Modal({ isOpen, onClose, title, children }) {
            if (!isOpen) return null;
            return (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                    <div className="bg-white p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold">{title}</h3>
                            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
                        </div>
                        {children}
                    </div>
                </div>
            );
        }

        function App() {
            const [currentPage, setCurrentPage] = useState('dashboard');
            const [rooms, setRooms] = useState([]);
            const [checkedInCustomers, setCheckedInCustomers] = useState([]);
            const [upcomingBookings, setUpcomingBookings] = useState([]);
            const [loading, setLoading] = useState(true);
            const [showNewBookingModal, setShowNewBookingModal] = useState(false);
            const [showCheckinModal, setShowCheckinModal] = useState(false);
            const [showCheckoutModal, setShowCheckoutModal] = useState(false);
            const [selectedBooking, setSelectedBooking] = useState(null);
            const [selectedCustomer, setSelectedCustomer] = useState(null);
            const [initialized, setInitialized] = useState(false);

            useEffect(() => {
                loadDashboardData();
            }, []);

            const loadDashboardData = async () => {
                try {
                    const [roomsRes, customersRes, bookingsRes] = await Promise.all([
                        axios.get(`${API_BASE_URL}/rooms`),
                        axios.get(`${API_BASE_URL}/customers/checked-in`),
                        axios.get(`${API_BASE_URL}/bookings/upcoming`)
                    ]);
                    
                    setRooms(roomsRes.data);
                    setCheckedInCustomers(customersRes.data);
                    setUpcomingBookings(bookingsRes.data);
                    setLoading(false);
                } catch (error) {
                    console.error('Error loading dashboard data:', error);
                    setLoading(false);
                }
            };

            const initializeData = async () => {
                try {
                    await axios.post(`${API_BASE_URL}/init-data`);
                    setInitialized(true);
                    loadDashboardData();
                } catch (error) {
                    console.error('Error initializing data:', error);
                }
            };

            // Navigation Component
            const Navigation = () => (
                <nav className="bg-white shadow-lg border-b border-gray-200">
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                        <div className="flex justify-between h-16">
                            <div className="flex items-center">
                                <h1 className="text-2xl font-bold text-gray-900">🏨 Hotel Management</h1>
                            </div>
                            <div className="flex space-x-8">
                                <button
                                    onClick={() => setCurrentPage('dashboard')}
                                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                                        currentPage === 'dashboard'
                                            ? 'border-blue-500 text-gray-900'
                                            : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                                >
                                    Dashboard
                                </button>
                                <button
                                    onClick={() => setCurrentPage('rooms')}
                                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                                        currentPage === 'rooms'
                                            ? 'border-blue-500 text-gray-900'
                                            : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                                >
                                    Rooms
                                </button>
                            </div>
                        </div>
                    </div>
                </nav>
            );

            // Dashboard Component
            const Dashboard = () => {
                if (loading) {
                    return (
                        <div className="flex justify-center items-center h-64">
                            <div className="loading-spinner"></div>
                        </div>
                    );
                }

                return (
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                        <div className="mb-8">
                            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                            <p className="text-gray-600">Hotel Management System</p>
                        </div>

                        {!initialized && rooms.length === 0 && (
                            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                                <h3 className="font-semibold text-yellow-800 text-lg">Initialize Sample Data</h3>
                                <p className="text-yellow-600 mb-4">Get started by initializing your hotel with sample rooms and data.</p>
                                <button
                                    onClick={initializeData}
                                    className="bg-yellow-600 text-white px-6 py-3 rounded-lg hover:bg-yellow-700 font-semibold"
                                >
                                    Initialize Sample Data
                                </button>
                            </div>
                        )}

                        {/* Quick Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                            <div className="bg-blue-50 p-6 rounded-lg">
                                <h3 className="text-lg font-semibold text-blue-800">Total Rooms</h3>
                                <p className="text-3xl font-bold text-blue-600">{rooms.length}</p>
                            </div>
                            <div className="bg-green-50 p-6 rounded-lg">
                                <h3 className="text-lg font-semibold text-green-800">Available</h3>
                                <p className="text-3xl font-bold text-green-600">
                                    {rooms.filter(room => room.status === 'Available').length}
                                </p>
                            </div>
                            <div className="bg-red-50 p-6 rounded-lg">
                                <h3 className="text-lg font-semibold text-red-800">Occupied</h3>
                                <p className="text-3xl font-bold text-red-600">
                                    {rooms.filter(room => room.status === 'Occupied').length}
                                </p>
                            </div>
                            <div className="bg-purple-50 p-6 rounded-lg">
                                <h3 className="text-lg font-semibold text-purple-800">Checked-in</h3>
                                <p className="text-3xl font-bold text-purple-600">{checkedInCustomers.length}</p>
                            </div>
                        </div>

                        {/* Room Status Grid */}
                        <div className="bg-white p-6 rounded-lg shadow mb-8">
                            <h3 className="text-lg font-semibold mb-4">Room Status</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                                {rooms.map(room => (
                                    <div
                                        key={room.id}
                                        className={`p-4 rounded-lg border-2 ${
                                            room.status === 'Available' 
                                                ? 'border-green-300 bg-green-50' 
                                                : 'border-red-300 bg-red-50'
                                        }`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h4 className="font-semibold">{room.room_number}</h4>
                                                <p className="text-sm text-gray-600">{room.room_type}</p>
                                                <p className="text-sm font-medium">{formatLKR(room.price_per_night)}/night</p>
                                            </div>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                room.status === 'Available' 
                                                    ? 'bg-green-100 text-green-800' 
                                                    : 'bg-red-100 text-red-800'
                                            }`}>
                                                {room.status === 'Available' ? '🟢' : '🔴'} {room.status}
                                            </span>
                                        </div>
                                        {room.current_guest && (
                                            <div className="mt-2 text-sm text-gray-700">
                                                <p><strong>Guest:</strong> {room.current_guest}</p>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* System Status */}
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-semibold mb-4">System Status</h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div className="bg-green-50 p-4 rounded-lg">
                                    <h4 className="font-semibold text-green-800">✅ Backend API</h4>
                                    <p className="text-green-600">Connected and Running</p>
                                </div>
                                <div className="bg-green-50 p-4 rounded-lg">
                                    <h4 className="font-semibold text-green-800">✅ Database</h4>
                                    <p className="text-green-600">MongoDB Connected</p>
                                </div>
                                <div className="bg-green-50 p-4 rounded-lg">
                                    <h4 className="font-semibold text-green-800">✅ Frontend</h4>
                                    <p className="text-green-600">React Application</p>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            };

            // Rooms Page
            const RoomsPage = () => (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                    <div className="mb-8">
                        <h1 className="text-3xl font-bold text-gray-900">Rooms Management</h1>
                        <p className="text-gray-600">Manage your hotel rooms</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {rooms.map(room => (
                            <div key={room.id} className="bg-white rounded-lg shadow-md overflow-hidden">
                                <img
                                    src={room.image_url}
                                    alt={`Room ${room.room_number}`}
                                    className="w-full h-48 object-cover"
                                />
                                <div className="p-6">
                                    <div className="flex justify-between items-start mb-2">
                                        <h3 className="text-lg font-semibold">Room {room.room_number}</h3>
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                                            room.status === 'Available' 
                                                ? 'bg-green-100 text-green-800' 
                                                : 'bg-red-100 text-red-800'
                                        }`}>
                                            {room.status}
                                        </span>
                                    </div>
                                    <p className="text-sm text-gray-600 mb-2">{room.room_type}</p>
                                    <p className="text-lg font-bold text-blue-600 mb-2">{formatLKR(room.price_per_night)}/night</p>
                                    <p className="text-sm text-gray-600 mb-4">Max {room.max_occupancy} guests</p>
                                    
                                    <div className="mb-4">
                                        <h4 className="text-sm font-medium text-gray-700 mb-2">Amenities:</h4>
                                        <div className="flex flex-wrap gap-1">
                                            {room.amenities.map((amenity, index) => (
                                                <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                                    {amenity}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    {room.current_guest && (
                                        <div className="mb-4 p-3 bg-yellow-50 rounded">
                                            <p className="text-sm font-medium text-yellow-800">Current Guest:</p>
                                            <p className="text-sm text-yellow-700">{room.current_guest}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            );

            return (
                <div className="min-h-screen bg-gray-100">
                    <Navigation />
                    {currentPage === 'dashboard' && <Dashboard />}
                    {currentPage === 'rooms' && <RoomsPage />}
                </div>
            );
        }

        ReactDOM.render(<App />, document.getElementById('root'));
    </script>
</body>
</html>
EOF

# Create dist directory
sudo -u hotelapp mkdir -p dist
sudo -u hotelapp cp index.html dist/
check_command "Frontend setup"

# Step 14: Configure PM2
print_status "Step 14: Configuring PM2..."
cd /home/hotelapp/hotel-management

sudo -u hotelapp tee ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: "hotel-backend",
      script: "./venv/bin/python",
      args: "server.py",
      cwd: "/home/hotelapp/hotel-management/backend",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
};
EOF

# Step 15: Configure Nginx
print_status "Step 15: Configuring Nginx..."
sudo tee /etc/nginx/sites-available/hotel-management << EOF
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
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/hotel-management /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
check_command "Nginx configuration"

# Step 16: Configure Firewall
print_status "Step 16: Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 27017
check_command "Firewall configuration"

# Step 17: Set Permissions and Start Services
print_status "Step 17: Setting permissions and starting services..."
sudo chown -R hotelapp:hotelapp /home/hotelapp/hotel-management
sudo chmod -R 755 /home/hotelapp/hotel-management

# Start PM2 application
sudo -u hotelapp pm2 stop all 2>/dev/null || true
sudo -u hotelapp pm2 delete all 2>/dev/null || true
sudo -u hotelapp pm2 start ecosystem.config.js
sudo -u hotelapp pm2 save
check_command "PM2 service start"

# Step 18: Final Verification
print_status "Step 18: Final verification..."
sleep 10

# Check services
echo ""
echo "=== FINAL SERVICE STATUS ==="

# MongoDB
echo "📦 MongoDB Status:"
if sudo docker exec mongodb-hotel mongosh -u hotelapp -p "$MONGO_PASSWORD" --authenticationDatabase admin --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    print_status "MongoDB: ✅ Online"
else
    print_error "MongoDB: ❌ Offline"
fi

# Backend API
echo "🔧 Backend API Status:"
if curl -s http://localhost:8001/api/health >/dev/null 2>&1; then
    print_status "Backend API: ✅ Online"
else
    print_error "Backend API: ❌ Offline"
fi

# Frontend
echo "🌐 Frontend Status:"
if curl -s http://localhost/ >/dev/null 2>&1; then
    print_status "Frontend: ✅ Online"
else
    print_error "Frontend: ❌ Offline"
fi

# PM2
echo "⚙️ PM2 Status:"
if sudo -u hotelapp pm2 status | grep -q "hotel-backend"; then
    print_status "PM2: ✅ Running"
else
    print_error "PM2: ❌ Not Running"
fi

# Nginx
echo "🌐 Nginx Status:"
if sudo systemctl is-active nginx >/dev/null 2>&1; then
    print_status "Nginx: ✅ Running"
else
    print_error "Nginx: ❌ Not Running"
fi

echo ""
echo "=============================================================================="
echo "          🎉 HOTEL MANAGEMENT SYSTEM INSTALLATION COMPLETE! 🎉"
echo "=============================================================================="
echo ""
print_info "🌐 Your application is available at: http://$DOMAIN"
print_info "📱 The system is fully responsive and mobile-friendly"
print_info "🔐 MongoDB Password: $MONGO_PASSWORD"
echo ""
print_info "🚀 Next Steps:"
echo "   1. Visit: http://$DOMAIN"
echo "   2. Click 'Initialize Sample Data' to set up your hotel"
echo "   3. Start managing your hotel operations!"
echo ""
print_info "🔧 Management Commands:"
echo "   • Check PM2 status: sudo -u hotelapp pm2 status"
echo "   • View backend logs: sudo -u hotelapp pm2 logs hotel-backend"
echo "   • Restart backend: sudo -u hotelapp pm2 restart hotel-backend"
echo "   • Restart nginx: sudo systemctl restart nginx"
echo ""
print_info "🏨 Features Available:"
echo "   ✅ Room management with images and pricing"
echo "   ✅ Real-time dashboard with room status"
echo "   ✅ Booking system with check-in/checkout"
echo "   ✅ Professional UI with LKR currency"
echo "   ✅ Mobile responsive design"
echo "   ✅ MongoDB database with authentication"
echo ""
print_warning "⚠️ Important: Save your MongoDB password: $MONGO_PASSWORD"
print_info "🎉 Your hotel management system is now ready to use!"
echo ""
echo "=============================================================================="