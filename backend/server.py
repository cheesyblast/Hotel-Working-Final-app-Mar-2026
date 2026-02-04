from fastapi import FastAPI, APIRouter, HTTPException, Query, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
import csv
import io
from passlib.context import CryptContext
import jwt
from jwt import PyJWTError
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import NoCredentialsError

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer for JWT
security = HTTPBearer()

# Authentication helpers
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_random_password(length: int = 8) -> str:
    """Generate a random password"""
    import random
    import string
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

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
    commission_amount: float = 0.0  # Commission payable to booking channel
    booking_channel_id: str = ""  # ID of the booking channel
    booking_channel_name: str = "Direct"  # Name of the booking channel for display
    status: str  # Upcoming, Checked-in, Completed, Cancelled
    additional_notes: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BookingChannel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    channel_name: str  # e.g., "Booking.com", "Expedia", "Direct", "Agoda"
    channel_type: str = "OTA"  # OTA (Online Travel Agency), Direct, Corporate, Walk-in
    commission_rate: float = 0.0  # Percentage commission (e.g., 15.5 for 15.5%)
    contact_email: str = ""
    contact_phone: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "Admin"

class BookingChannelCreate(BaseModel):
    channel_name: str
    channel_type: str = "OTA"
    commission_rate: float = 0.0
    contact_email: str = ""
    contact_phone: str = ""

class BookingChannelUpdate(BaseModel):
    channel_name: Optional[str] = None
    channel_type: Optional[str] = None
    commission_rate: Optional[float] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: Optional[bool] = None

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
    commission_amount: float = 0.0  # Commission payable to booking channel
    booking_channel_id: str = ""  # ID of the booking channel
    booking_channel_name: str = "Direct"  # Name of the booking channel for display
    additional_notes: str = ""
    booking_status: str = "Upcoming"  # "Upcoming" or "Checked In" - for past date bookings

class BookingUpdate(BaseModel):
    room_number: Optional[str] = None
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
    check_out_date: date  # Planned checkout date from booking
    advance_amount: float = 0.0
    notes: str = ""
    room_charges: float = 0.0
    restaurant_charges: float = 0.0  # Added for restaurant integration
    additional_charges: float = 0.0
    total_amount: float = 0.0
    is_checked_out: bool = False  # True when customer has checked out
    actual_checkout_date: Optional[date] = None  # Actual checkout date when checked out
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutRequest(BaseModel):
    customer_id: str
    additional_amount: float = 0.0
    discount_amount: float = 0.0
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer

class AdvancePaymentRequest(BaseModel):
    customer_id: str
    amount: float
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    notes: str = ""

class ExtendStayRequest(BaseModel):
    customer_id: str
    new_checkout_date: date
    
class EarlyCheckoutRequest(BaseModel):
    customer_id: str
    additional_amount: float = 0.0
    discount_amount: float = 0.0
    payment_method: str = "Cash"
    refund_excess: bool = False  # If True, refund excess amount to customer

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
    payment_method: str = "Cash"

class Expense(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str  # Food, Maintenance, Utilities, Staff, Marketing, etc.
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    expense_date: date
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    expense_date: date

class Income(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    amount: float
    category: str  # Restaurant, Events, Laundry, Spa, Other Services, etc.
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    income_date: date
    guest_name: str = ""  # Associated guest name if applicable
    created_by: str = "Admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class IncomeCreate(BaseModel):
    description: str
    amount: float
    category: str
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    income_date: date
    guest_name: str = ""  # Associated guest name if applicable

class FinancialSummary(BaseModel):
    total_revenue: float
    total_expenses: float
    net_profit: float
    revenue_breakdown: dict
    expense_breakdown: dict
    period_start: date
    period_end: date

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str  # Hashed password
    full_name: str
    role: str = "Staff"  # Admin, Manager, Staff, Restaurant Manager
    email: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str = "Staff"
    email: str = ""

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    full_name: str
    role: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SetupWizard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_completed: bool = False
    hotel_name: str = ""
    hotel_address: str = ""
    hotel_email: str = ""
    timezone: str = "UTC"
    cash_balance: float = 0.0  # Initial cash balance
    bank_balance: float = 0.0  # Initial bank balance
    admin_created: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SetupWizardRequest(BaseModel):
    hotel_name: str
    hotel_address: str
    hotel_email: str
    timezone: str = "UTC"  # Timezone for the hotel (e.g., "Asia/Colombo", "America/New_York")
    cash_balance: float = 0.0  # Initial cash balance
    bank_balance: float = 0.0  # Initial bank balance

class EmailSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    provider: str = "smtp"  # sendgrid, gmail, ses, smtp
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sendgrid_api_key: str = ""
    aws_access_key: str = ""
    aws_secret_key: str = ""
    aws_region: str = "us-east-1"
    from_email: str = ""
    from_name: str = ""
    is_configured: bool = False
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EmailSettingsUpdate(BaseModel):
    provider: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    aws_region: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    username_or_email: str

# Restaurant Management Models
class MenuCategory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MenuCategoryCreate(BaseModel):
    name: str
    description: str = ""
    display_order: int = 0

class MenuItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    price: float
    category_id: str
    is_available: bool = True
    is_vegetarian: bool = False
    is_spicy: bool = False
    prep_time: int = 15  # minutes
    image_url: str = ""
    image: str = ""  # base64 encoded image
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MenuItemCreate(BaseModel):
    name: str
    description: str = ""
    price: float
    category_id: str
    is_vegetarian: bool = False
    is_spicy: bool = False
    prep_time: int = 15

class RestaurantTable(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    table_number: str
    capacity: int
    status: str = "Available"  # Available, Occupied, Reserved, Cleaning
    position_x: int = 0  # For visual layout
    position_y: int = 0  # For visual layout
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RestaurantTableCreate(BaseModel):
    table_number: str
    capacity: int
    position_x: int = 0
    position_y: int = 0

class RestaurantStaff(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role: str = "Waiter"  # Waiter, Chef, Manager
    phone: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RestaurantStaffCreate(BaseModel):
    name: str
    role: str = "Waiter"
    phone: str = ""

class RestaurantOrderItem(BaseModel):
    menu_item_id: str
    menu_item_name: str
    quantity: int
    unit_price: float
    total_price: float
    special_notes: str = ""

class RestaurantOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    order_type: str  # "table" or "room_service"
    table_id: Optional[str] = None  # For table orders
    table_number: Optional[str] = None
    room_number: Optional[str] = None  # For room service
    customer_name: str = ""
    items: List[RestaurantOrderItem]
    subtotal: float
    tax_amount: float = 0.0
    service_charge: float = 0.0
    total_amount: float
    payment_method: str = "Cash"  # Cash, Card, Bank Transfer
    payment_status: str = "Pending"  # Pending, Paid, Cancelled
    order_status: str = "Pending"  # Pending, Preparing, Ready, Served, Cancelled
    waiter_id: Optional[str] = None
    waiter_name: str = ""
    notes: str = ""
    order_date: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "Restaurant"

class RestaurantOrderCreate(BaseModel):
    order_type: str  # "table" or "room_service"
    table_id: Optional[str] = None
    room_number: Optional[str] = None
    customer_name: str = ""
    items: List[RestaurantOrderItem]
    waiter_id: Optional[str] = None
    notes: str = ""
    service_charge_rate: float = 10.0  # Service charge percentage (default 10%)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    
    user = await db.users.find_one({"username": token_data.username})
    if user is None:
        raise credentials_exception
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return UserResponse(**user)

async def get_current_active_admin(current_user: UserResponse = Depends(get_current_user)):
    """Require admin role"""
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

# Email service functions
async def get_email_settings():
    """Get email settings from database"""
    settings = await db.email_settings.find_one()
    if not settings:
        return None
    return EmailSettings(**settings)

async def send_email_smtp(email_settings: EmailSettings, to_email: str, subject: str, body: str):
    """Send email via SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = f"{email_settings.from_name} <{email_settings.from_email}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(email_settings.smtp_host, email_settings.smtp_port)
        server.starttls()
        server.login(email_settings.smtp_username, email_settings.smtp_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"SMTP Error: {str(e)}")
        return False

async def send_email_sendgrid(email_settings: EmailSettings, to_email: str, subject: str, body: str):
    """Send email via SendGrid (would require sendgrid library)"""
    # Placeholder for SendGrid implementation
    print(f"SendGrid email would be sent to {to_email}")
    return True

async def send_email_ses(email_settings: EmailSettings, to_email: str, subject: str, body: str):
    """Send email via AWS SES"""
    try:
        ses_client = boto3.client(
            'ses',
            aws_access_key_id=email_settings.aws_access_key,
            aws_secret_access_key=email_settings.aws_secret_key,
            region_name=email_settings.aws_region
        )
        
        response = ses_client.send_email(
            Destination={'ToAddresses': [to_email]},
            Message={
                'Body': {'Text': {'Charset': 'UTF-8', 'Data': body}},
                'Subject': {'Charset': 'UTF-8', 'Data': subject},
            },
            Source=email_settings.from_email,
        )
        return True
    except NoCredentialsError:
        print("AWS credentials not found")
        return False
    except Exception as e:
        print(f"SES Error: {str(e)}")
        return False

async def send_email(to_email: str, subject: str, body: str):
    """Send email using configured provider"""
    email_settings = await get_email_settings()
    if not email_settings or not email_settings.is_configured:
        return False
    
    if email_settings.provider == "smtp":
        return await send_email_smtp(email_settings, to_email, subject, body)
    elif email_settings.provider == "sendgrid":
        return await send_email_sendgrid(email_settings, to_email, subject, body)
    elif email_settings.provider == "ses":
        return await send_email_ses(email_settings, to_email, subject, body)
    else:
        return False

class Settings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hotel_name: str = "Hotel Management System"
    hotel_logo: str = ""  # Base64 encoded logo
    hotel_contact: str = ""
    hotel_address: str = ""
    hotel_email: str = ""
    hotel_phone: str = ""
    currency: str = "LKR"
    timezone: str = "UTC"  # Hotel timezone for all timestamps
    check_in_time: str = "14:00"
    check_out_time: str = "12:00"
    default_room_rate: float = 5000.0
    tax_rate: float = 0.0
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = "Admin"

class SettingsUpdate(BaseModel):
    hotel_name: Optional[str] = None
    hotel_logo: Optional[str] = None
    hotel_contact: Optional[str] = None
    hotel_address: Optional[str] = None
    hotel_email: Optional[str] = None
    hotel_phone: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    default_room_rate: Optional[float] = None
    tax_rate: Optional[float] = None

class ActivityLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str  # "created_booking", "checked_in", "checked_out", "added_expense", etc.
    description: str
    user_name: str = "Admin"
    user_id: str = ""
    entity_type: str = ""  # "booking", "room", "expense", "income", etc.
    entity_id: str = ""
    details: dict = {}  # Additional context data
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: str = ""

class ActivityLogCreate(BaseModel):
    action: str
    description: str
    user_name: str = "Admin"
    user_id: str = ""
    entity_type: str = ""
    entity_id: str = ""
    details: dict = {}
    ip_address: str = ""

# Activity logging helper function
async def log_activity(action: str, description: str, user_name: str = "Admin", 
                      entity_type: str = "", entity_id: str = "", details: dict = {}):
    """Helper function to log user activities"""
    try:
        activity = ActivityLog(
            action=action,
            description=description,
            user_name=user_name,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        await db.activity_logs.insert_one(activity.dict())
    except Exception as e:
        # Log the error but don't fail the main operation
        print(f"Failed to log activity: {str(e)}")

# Room availability validation helper function
async def check_room_availability_for_booking(room_number: str, check_in_date: date, check_out_date: date, exclude_booking_id: str = None, skip_occupied_check: bool = False):
    """
    Check if a specific room is available for booking during the given date range
    Returns: (is_available: bool, error_message: str)
    skip_occupied_check: Set to True when extending stay for current occupant
    """
    try:
        # Convert dates to datetime for database queries
        check_in_datetime = datetime.combine(check_in_date, datetime.min.time())
        check_out_datetime = datetime.combine(check_out_date, datetime.min.time())
        
        # Check if room exists
        room = await db.rooms.find_one({"room_number": room_number})
        if not room:
            return False, f"Room {room_number} does not exist"
        
        # Build query to find conflicting bookings
        conflict_query = {
            "$and": [
                {"room_number": room_number},
                {"status": {"$in": ["Upcoming", "Checked-in", "Checked In"]}},
                {
                    "$or": [
                        # Booking starts during requested period
                        {
                            "$and": [
                                {"check_in_date": {"$gte": check_in_datetime}},
                                {"check_in_date": {"$lt": check_out_datetime}}
                            ]
                        },
                        # Booking ends during requested period
                        {
                            "$and": [
                                {"check_out_date": {"$gt": check_in_datetime}},
                                {"check_out_date": {"$lte": check_out_datetime}}
                            ]
                        },
                        # Booking encompasses requested period
                        {
                            "$and": [
                                {"check_in_date": {"$lte": check_in_datetime}},
                                {"check_out_date": {"$gte": check_out_datetime}}
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Exclude specific booking ID if provided (for booking updates)
        if exclude_booking_id:
            conflict_query["$and"].append({"id": {"$ne": exclude_booking_id}})
        
        # Find conflicting bookings
        conflicting_bookings = await db.bookings.find(conflict_query).to_list(10)
        
        if conflicting_bookings:
            # Get details of the first conflicting booking
            conflict = conflicting_bookings[0]
            conflict_guest = conflict.get('guest_name', 'Unknown Guest')
            conflict_checkin = conflict.get('check_in_date')
            conflict_checkout = conflict.get('check_out_date')
            
            # Convert datetime to date for display
            if isinstance(conflict_checkin, datetime):
                conflict_checkin = conflict_checkin.date()
            if isinstance(conflict_checkout, datetime):
                conflict_checkout = conflict_checkout.date()
                
            error_msg = f"Room {room_number} is already booked by {conflict_guest} from {conflict_checkin} to {conflict_checkout}"
            return False, error_msg
        
        # Check if room is currently occupied (status = "Occupied")
        if room.get('status') == 'Occupied':
            current_guest = room.get('current_guest', 'Unknown Guest')
            room_checkout = room.get('check_out_date')
            if isinstance(room_checkout, datetime):
                room_checkout = room_checkout.date()
            
            # Only block if the requested check-in is before room checkout
            if room_checkout and check_in_date < room_checkout:
                error_msg = f"Room {room_number} is currently occupied by {current_guest} until {room_checkout}"
                return False, error_msg
        
        return True, ""
        
    except Exception as e:
        return False, f"Error checking room availability: {str(e)}"

# Setup Wizard Routes
@api_router.get("/setup/status")
async def get_setup_status():
    """Check if initial setup has been completed"""
    setup = await db.setup_wizard.find_one()
    if setup:
        return {"is_completed": setup.get("is_completed", False)}
    return {"is_completed": False}

@api_router.post("/setup/complete")
async def complete_setup(setup_request: SetupWizardRequest):
    """Complete initial setup wizard"""
    # Check if setup is already completed
    existing_setup = await db.setup_wizard.find_one()
    if existing_setup and existing_setup.get("is_completed"):
        raise HTTPException(status_code=400, detail="Setup already completed")
    
    # Create/update hotel settings
    settings_update = {
        "hotel_name": setup_request.hotel_name,
        "hotel_address": setup_request.hotel_address,
        "hotel_email": setup_request.hotel_email,
        "timezone": setup_request.timezone,
        "updated_at": datetime.utcnow()
    }
    
    # Check if settings exist
    existing_settings = await db.settings.find_one()
    if existing_settings:
        await db.settings.update_one(
            {"id": existing_settings["id"]},
            {"$set": settings_update}
        )
    else:
        default_settings = Settings(**settings_update)
        await db.settings.insert_one(default_settings.dict())
    
    # Create admin user
    admin_user = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        full_name="System Administrator",
        role="Admin",
        email=setup_request.hotel_email
    )
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"username": "admin"})
    if existing_admin:
        # Update admin user
        await db.users.update_one(
            {"username": "admin"},
            {"$set": {
                "password_hash": get_password_hash("admin123"),
                "email": setup_request.hotel_email,
                "full_name": "System Administrator"
            }}
        )
    else:
        await db.users.insert_one(admin_user.dict())
    
    # Create initial balance records if any balance is provided
    setup_date = datetime.utcnow().date()
    
    if setup_request.cash_balance > 0:
        initial_cash_income = Income(
            description="Initial Cash Balance - Setup",
            amount=setup_request.cash_balance,
            category="Initial Setup",
            payment_method="Cash",
            income_date=setup_date,
            guest_name="",
            created_by="System"
        )
        # Convert date to datetime for MongoDB compatibility
        income_dict = initial_cash_income.dict()
        if isinstance(income_dict['income_date'], date):
            income_dict['income_date'] = datetime.combine(income_dict['income_date'], datetime.min.time())
        await db.incomes.insert_one(income_dict)
    
    if setup_request.bank_balance > 0:
        initial_bank_income = Income(
            description="Initial Bank Balance - Setup",
            amount=setup_request.bank_balance,
            category="Initial Setup",
            payment_method="Bank Transfer",
            income_date=setup_date,
            guest_name="",
            created_by="System"
        )
        # Convert date to datetime for MongoDB compatibility
        income_dict = initial_bank_income.dict()
        if isinstance(income_dict['income_date'], date):
            income_dict['income_date'] = datetime.combine(income_dict['income_date'], datetime.min.time())
        await db.incomes.insert_one(income_dict)

    # Mark setup as completed
    setup_wizard = SetupWizard(
        is_completed=True,
        hotel_name=setup_request.hotel_name,
        hotel_address=setup_request.hotel_address,
        hotel_email=setup_request.hotel_email,
        timezone=setup_request.timezone,
        cash_balance=setup_request.cash_balance,
        bank_balance=setup_request.bank_balance,
        admin_created=True,
        completed_at=datetime.utcnow()
    )
    
    if existing_setup:
        await db.setup_wizard.update_one(
            {"id": existing_setup["id"]},
            {"$set": setup_wizard.dict()}
        )
    else:
        await db.setup_wizard.insert_one(setup_wizard.dict())
    
    # Log activity
    balance_info = ""
    if setup_request.cash_balance > 0 or setup_request.bank_balance > 0:
        balance_info = f" with initial balances - Cash: {setup_request.cash_balance}, Bank: {setup_request.bank_balance}"
    
    await log_activity(
        action="setup_completed",
        description=f"Initial setup completed for {setup_request.hotel_name}{balance_info}",
        entity_type="setup"
    )
    
    return {"message": "Setup completed successfully"}

# Authentication Routes
@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """User login"""
    # Find user by username
    user = await db.users.find_one({"username": user_credentials.username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    # Update last login
    await db.users.update_one(
        {"username": user_credentials.username},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Log activity
    await log_activity(
        action="user_login",
        description=f"User {user['username']} logged in",
        user_name=user["username"],
        entity_type="auth"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/auth/logout")
async def logout(current_user: UserResponse = Depends(get_current_user)):
    """User logout (mainly for logging purposes)"""
    await log_activity(
        action="user_logout",
        description=f"User {current_user.username} logged out",
        user_name=current_user.username,
        entity_type="auth"
    )
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send new password to user's email"""
    # Find user by username or email
    user = await db.users.find_one({
        "$or": [
            {"username": request.username_or_email},
            {"email": request.username_or_email}
        ]
    })
    
    if not user:
        # Don't reveal if user exists or not for security
        return {"message": "If the account exists, a new password has been sent to the registered email"}
    
    if not user.get("email"):
        raise HTTPException(
            status_code=400,
            detail="No email associated with this account"
        )
    
    # Generate new password
    new_password = generate_random_password()
    hashed_password = get_password_hash(new_password)
    
    # Update user password
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password_hash": hashed_password}}
    )
    
    # Send email
    subject = "Password Reset - Hotel Management System"
    body = f"""
    Dear {user.get('full_name', user.get('username'))},

    Your password has been reset. Here are your new login credentials:

    Username: {user['username']}
    New Password: {new_password}

    Please login with these credentials and change your password immediately.

    Best regards,
    Hotel Management Team
    """
    
    email_sent = await send_email(user["email"], subject, body)
    
    if email_sent:
        # Log activity
        await log_activity(
            action="password_reset",
            description=f"Password reset for user {user['username']}",
            user_name=user["username"],
            entity_type="auth"
        )
        return {"message": "New password has been sent to your email"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send email. Please contact administrator."
        )

# Email Settings Routes
@api_router.get("/email-settings")
async def get_email_settings_api(current_user: UserResponse = Depends(get_current_active_admin)):
    """Get email settings (Admin only)"""
    settings = await get_email_settings()
    if not settings:
        return EmailSettings().dict()
    
    # Hide sensitive information
    settings_dict = settings.dict()
    if settings_dict.get("smtp_password"):
        settings_dict["smtp_password"] = "***"
    if settings_dict.get("sendgrid_api_key"):
        settings_dict["sendgrid_api_key"] = "***"
    if settings_dict.get("aws_secret_key"):
        settings_dict["aws_secret_key"] = "***"
    
    return settings_dict

@api_router.put("/email-settings")
async def update_email_settings(
    settings_update: EmailSettingsUpdate,
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Update email settings (Admin only)"""
    # Get current settings or create default
    current_settings = await get_email_settings()
    if not current_settings:
        current_settings = EmailSettings()
    
    # Update only provided fields
    update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
    update_data['updated_at'] = datetime.utcnow()
    
    # Check if configuration is complete
    if settings_update.provider == "smtp":
        is_configured = all([
            update_data.get("smtp_host") or current_settings.smtp_host,
            update_data.get("smtp_username") or current_settings.smtp_username,
            update_data.get("smtp_password") or current_settings.smtp_password,
            update_data.get("from_email") or current_settings.from_email
        ])
    elif settings_update.provider == "sendgrid":
        is_configured = all([
            update_data.get("sendgrid_api_key") or current_settings.sendgrid_api_key,
            update_data.get("from_email") or current_settings.from_email
        ])
    elif settings_update.provider == "ses":
        is_configured = all([
            update_data.get("aws_access_key") or current_settings.aws_access_key,
            update_data.get("aws_secret_key") or current_settings.aws_secret_key,
            update_data.get("from_email") or current_settings.from_email
        ])
    else:
        is_configured = current_settings.is_configured
    
    update_data['is_configured'] = is_configured
    
    # Update or create settings
    if current_settings.id:
        await db.email_settings.update_one(
            {"id": current_settings.id},
            {"$set": update_data}
        )
    else:
        new_settings = EmailSettings(**update_data)
        await db.email_settings.insert_one(new_settings.dict())
    
    # Log activity
    await log_activity(
        action="email_settings_updated",
        description=f"Email settings updated by {current_user.username}",
        user_name=current_user.username,
        entity_type="settings"
    )
    
    return {"message": "Email settings updated successfully"}

@api_router.post("/admin/complete-reset")
async def complete_database_reset(current_user: UserResponse = Depends(get_current_active_admin)):
    """Complete database reset - Admin only (DANGEROUS OPERATION)"""
    try:
        # Get all collection names in the database
        collection_names = await db.list_collection_names()
        
        # Collections to clear (all except setup_wizard)
        collections_to_clear = [
            'rooms', 'bookings', 'customers', 'expenses', 'incomes', 
            'activity_logs', 'daily_sales', 'email_settings', 'booking_channels'
        ]
        
        reset_results = {}
        
        # Clear specified collections completely
        for collection_name in collections_to_clear:
            if collection_name in collection_names:
                result = await db[collection_name].delete_many({})
                reset_results[collection_name] = result.deleted_count
            else:
                reset_results[collection_name] = 0
        
        # Clear users except current admin
        if 'users' in collection_names:
            users_result = await db.users.delete_many({"username": {"$ne": "admin"}})
            reset_results['users_except_admin'] = users_result.deleted_count
        else:
            reset_results['users_except_admin'] = 0
        
        # Reset hotel settings to default but keep hotel name
        current_settings = await db.settings.find_one()
        hotel_name = current_settings.get('hotel_name', 'Hotel Management System') if current_settings else 'Hotel Management System'
        
        await db.settings.delete_many({})
        default_settings = Settings(hotel_name=hotel_name)
        await db.settings.insert_one(default_settings.dict())
        reset_results['settings_reset'] = True
        
        # Reset setup_wizard to require re-initialization including balances
        await db.setup_wizard.delete_many({})
        reset_results['setup_wizard_reset'] = True
        
        # Log the reset activity
        await log_activity(
            action="complete_system_reset",
            description=f"Complete system reset performed by admin {current_user.username}",
            user_name=current_user.username,
            entity_type="system",
            details=reset_results
        )
        
        return {
            "message": "Complete system reset successful",
            "reset_summary": reset_results,
            "note": "Hotel settings preserved, admin account preserved. Setup wizard reset - you will need to reconfigure hotel including initial cash and bank balances.",
            "requires_setup": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Reset failed: {str(e)}"
        )

# Booking Channels Management Routes  
@api_router.get("/booking-channels", response_model=List[BookingChannel])
async def get_booking_channels(current_user: UserResponse = Depends(get_current_user)):
    """Get all booking channels"""
    channels = await db.booking_channels.find().to_list(1000)
    return [BookingChannel(**channel) for channel in channels]

@api_router.post("/booking-channels", response_model=BookingChannel)
async def create_booking_channel(
    channel: BookingChannelCreate, 
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Create a new booking channel (Admin only)"""
    # Check if channel name already exists
    existing_channel = await db.booking_channels.find_one({"channel_name": channel.channel_name})
    if existing_channel:
        raise HTTPException(status_code=400, detail="Booking channel with this name already exists")
    
    channel_obj = BookingChannel(**channel.dict(), created_by=current_user.username)
    channel_dict = channel_obj.dict()
    await db.booking_channels.insert_one(channel_dict)
    
    # Log activity
    await log_activity(
        action="booking_channel_created",
        description=f"New booking channel '{channel.channel_name}' created with {channel.commission_rate}% commission",
        user_name=current_user.username,
        entity_type="booking_channel",
        entity_id=channel_obj.id
    )
    
    return BookingChannel(**channel_dict)

@api_router.put("/booking-channels/{channel_id}", response_model=BookingChannel)
async def update_booking_channel(
    channel_id: str,
    channel_update: BookingChannelUpdate,
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Update a booking channel (Admin only)"""
    channel = await db.booking_channels.find_one({"id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Booking channel not found")
    
    # Update only provided fields
    update_data = {k: v for k, v in channel_update.dict().items() if v is not None}
    
    if update_data:
        result = await db.booking_channels.update_one(
            {"id": channel_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Booking channel not found")
        
        # Log activity
        await log_activity(
            action="booking_channel_updated",
            description=f"Booking channel '{channel.get('channel_name', 'Unknown')}' updated",
            user_name=current_user.username,
            entity_type="booking_channel",
            entity_id=channel_id
        )
    
    # Return updated channel
    updated_channel = await db.booking_channels.find_one({"id": channel_id})
    return BookingChannel(**updated_channel)

@api_router.delete("/booking-channels/{channel_id}")
async def delete_booking_channel(
    channel_id: str, 
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Delete a booking channel (Admin only)"""
    channel = await db.booking_channels.find_one({"id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Booking channel not found")
    
    # Check if channel is being used in bookings
    bookings_count = await db.bookings.count_documents({"booking_channel_id": channel_id})
    if bookings_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete channel. It is used in {bookings_count} booking(s). Deactivate instead.")
    
    result = await db.booking_channels.delete_one({"id": channel_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Booking channel not found")
    
    # Log activity
    await log_activity(
        action="booking_channel_deleted",
        description=f"Booking channel '{channel.get('channel_name', 'Unknown')}' deleted",
        user_name=current_user.username,
        entity_type="booking_channel",
        entity_id=channel_id
    )
    
    return {"message": "Booking channel deleted successfully"}

@api_router.put("/booking-channels/{channel_id}/toggle-status")
async def toggle_booking_channel_status(
    channel_id: str, 
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Toggle booking channel active/inactive status (Admin only)"""
    channel = await db.booking_channels.find_one({"id": channel_id})
    if not channel:
        raise HTTPException(status_code=404, detail="Booking channel not found")
    
    new_status = not channel.get('is_active', True)
    result = await db.booking_channels.update_one(
        {"id": channel_id},
        {"$set": {"is_active": new_status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking channel not found")
    
    # Log activity
    await log_activity(
        action="booking_channel_status_changed",
        description=f"Booking channel '{channel.get('channel_name', 'Unknown')}' {'activated' if new_status else 'deactivated'}",
        user_name=current_user.username,
        entity_type="booking_channel",
        entity_id=channel_id
    )
    
    return {"message": f"Booking channel {'activated' if new_status else 'deactivated'} successfully"}

# Commission Tracking Routes
@api_router.get("/commissions/summary")
async def get_commission_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get commission summary by booking channel
    Returns total commissions payable per channel, optionally filtered by year/month
    """
    # Default to current year/month if not specified
    now = datetime.now()
    target_year = year or now.year
    target_month = month  # None means all months for the year
    
    # Build date filter for bookings
    if target_month:
        # Filter for specific month
        start_date = datetime(target_year, target_month, 1)
        if target_month == 12:
            end_date = datetime(target_year + 1, 1, 1)
        else:
            end_date = datetime(target_year, target_month + 1, 1)
    else:
        # Filter for entire year
        start_date = datetime(target_year, 1, 1)
        end_date = datetime(target_year + 1, 1, 1)
    
    # Get all booking channels
    channels = await db.booking_channels.find().to_list(1000)
    channel_map = {ch['id']: ch for ch in channels}
    
    # Get bookings with commission for the period (exclude cancelled bookings)
    bookings = await db.bookings.find({
        "created_at": {"$gte": start_date, "$lt": end_date},
        "commission_amount": {"$gt": 0},
        "status": {"$ne": "Cancelled"}
    }).to_list(10000)
    
    # Aggregate commissions by channel
    channel_commissions = {}
    for booking in bookings:
        channel_id = booking.get('booking_channel_id', '')
        channel_name = booking.get('booking_channel_name', 'Direct')
        commission = booking.get('commission_amount', 0)
        
        if channel_name not in channel_commissions:
            channel_commissions[channel_name] = {
                'channel_id': channel_id,
                'channel_name': channel_name,
                'total_commission': 0,
                'booking_count': 0,
                'total_booking_amount': 0
            }
        
        channel_commissions[channel_name]['total_commission'] += commission
        channel_commissions[channel_name]['booking_count'] += 1
        channel_commissions[channel_name]['total_booking_amount'] += booking.get('booking_amount', 0)
    
    # Convert to list and sort by total commission
    summary = list(channel_commissions.values())
    summary.sort(key=lambda x: x['total_commission'], reverse=True)
    
    # Calculate grand total
    grand_total = sum(ch['total_commission'] for ch in summary)
    
    return {
        'year': target_year,
        'month': target_month,
        'channels': summary,
        'grand_total': grand_total,
        'total_bookings': sum(ch['booking_count'] for ch in summary)
    }

@api_router.get("/commissions/monthly-breakdown")
async def get_commission_monthly_breakdown(
    year: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get monthly commission breakdown for all channels for a given year
    """
    target_year = year or datetime.now().year
    
    # Get bookings for the year (exclude cancelled bookings)
    start_date = datetime(target_year, 1, 1)
    end_date = datetime(target_year + 1, 1, 1)
    
    bookings = await db.bookings.find({
        "created_at": {"$gte": start_date, "$lt": end_date},
        "commission_amount": {"$gt": 0},
        "status": {"$ne": "Cancelled"}
    }).to_list(10000)
    
    # Aggregate by month and channel
    monthly_data = {}
    for month in range(1, 13):
        monthly_data[month] = {}
    
    for booking in bookings:
        booking_month = booking['created_at'].month
        channel_name = booking.get('booking_channel_name', 'Direct')
        commission = booking.get('commission_amount', 0)
        
        if channel_name not in monthly_data[booking_month]:
            monthly_data[booking_month][channel_name] = 0
        monthly_data[booking_month][channel_name] += commission
    
    # Format response
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    result = []
    for month_num in range(1, 13):
        month_entry = {
            'month': month_num,
            'month_name': months[month_num - 1],
            'channels': monthly_data[month_num],
            'total': sum(monthly_data[month_num].values())
        }
        result.append(month_entry)
    
    return {
        'year': target_year,
        'monthly_breakdown': result,
        'year_total': sum(m['total'] for m in result)
    }

@api_router.get("/commissions/channel-details/{channel_id}")
async def get_channel_commission_details(
    channel_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get detailed commission bookings for a specific channel
    """
    target_year = year or datetime.now().year
    
    # Build date filter
    if month:
        start_date = datetime(target_year, month, 1)
        if month == 12:
            end_date = datetime(target_year + 1, 1, 1)
        else:
            end_date = datetime(target_year, month + 1, 1)
    else:
        start_date = datetime(target_year, 1, 1)
        end_date = datetime(target_year + 1, 1, 1)
    
    # Get channel info
    channel = await db.booking_channels.find_one({"id": channel_id}, {"_id": 0})
    
    # Get bookings for this channel (exclude cancelled bookings)
    bookings = await db.bookings.find({
        "booking_channel_id": channel_id,
        "created_at": {"$gte": start_date, "$lt": end_date},
        "commission_amount": {"$gt": 0},
        "status": {"$ne": "Cancelled"}
    }).sort("created_at", -1).to_list(1000)
    
    # Format bookings
    formatted_bookings = []
    total_commission = 0
    for booking in bookings:
        commission = booking.get('commission_amount', 0)
        total_commission += commission
        
        formatted_bookings.append({
            'id': booking['id'],
            'guest_name': booking['guest_name'],
            'room_number': booking['room_number'],
            'check_in_date': booking['check_in_date'].isoformat() if isinstance(booking['check_in_date'], (date, datetime)) else str(booking['check_in_date']),
            'check_out_date': booking['check_out_date'].isoformat() if isinstance(booking['check_out_date'], (date, datetime)) else str(booking['check_out_date']),
            'booking_amount': booking.get('booking_amount', 0),
            'commission_amount': commission,
            'status': booking.get('status', 'Unknown'),
            'created_at': booking['created_at'].isoformat() if isinstance(booking['created_at'], datetime) else str(booking['created_at'])
        })
    
    return {
        'channel': channel if channel else {'channel_name': 'Unknown'},
        'year': target_year,
        'month': month,
        'bookings': formatted_bookings,
        'total_commission': total_commission,
        'booking_count': len(formatted_bookings)
    }

# User Management Routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: UserResponse = Depends(get_current_active_admin)):
    """Get all users (Admin only)"""
    users = await db.users.find().to_list(1000)
    return [UserResponse(**user) for user in users]

@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: UserResponse = Depends(get_current_active_admin)):
    """Create a new user (Admin only)"""
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    hashed_password = get_password_hash(user.password)
    
    user_obj = User(
        username=user.username,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role,
        email=user.email
    )
    user_dict = user_obj.dict()
    await db.users.insert_one(user_dict)
    
    # Log activity
    await log_activity(
        action="user_created",
        description=f"New user '{user.username}' created with role '{user.role}'",
        user_name=current_user.username,
        entity_type="user",
        entity_id=user_obj.id
    )
    
    return UserResponse(**user_dict)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: UserResponse = Depends(get_current_active_admin)):
    """Delete a user (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting admin user
    if user.get("username") == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete admin user")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log activity
    await log_activity(
        action="user_deleted",
        description=f"User '{user.get('username', 'Unknown')}' deleted",
        user_name=current_user.username,
        entity_type="user",
        entity_id=user_id
    )
    
    return {"message": "User deleted successfully"}

@api_router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(user_id: str, current_user: UserResponse = Depends(get_current_active_admin)):
    """Toggle user active/inactive status (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deactivating admin user
    if user.get("username") == "admin":
        raise HTTPException(status_code=400, detail="Cannot deactivate admin user")
    
    new_status = not user.get('is_active', True)
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": new_status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log activity
    await log_activity(
        action="user_status_changed",
        description=f"User '{user.get('username', 'Unknown')}' {'activated' if new_status else 'deactivated'}",
        user_name=current_user.username,
        entity_type="user",
        entity_id=user_id
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}

# Settings Management Routes
@api_router.get("/settings")
async def get_settings(current_user: UserResponse = Depends(get_current_user)):
    """Get hotel settings"""
    settings = await db.settings.find_one()
    if not settings:
        # Create default settings if none exist
        default_settings = Settings()
        await db.settings.insert_one(default_settings.dict())
        return default_settings
    return Settings(**settings)

@api_router.put("/settings")
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Update hotel settings (Admin only)"""
    # Get current settings or create default
    current_settings = await db.settings.find_one()
    if not current_settings:
        current_settings = Settings().dict()
        await db.settings.insert_one(current_settings)
    
    # Update only provided fields
    update_data = {k: v for k, v in settings_update.dict().items() if v is not None}
    update_data['updated_at'] = datetime.utcnow()
    update_data['updated_by'] = current_user.username
    
    result = await db.settings.update_one(
        {"id": current_settings.get('id', current_settings.get('_id'))},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        # If no match, create new settings
        new_settings = Settings(**update_data)
        await db.settings.insert_one(new_settings.dict())
    
    # Log activity
    updated_fields = list(update_data.keys())
    await log_activity(
        action="settings_updated",
        description=f"Hotel settings updated: {', '.join(updated_fields)}",
        user_name=current_user.username,
        entity_type="settings",
        details=update_data
    )
    
    return {"message": "Settings updated successfully"}

# Activity Log Routes
@api_router.get("/activity-logs")
async def get_activity_logs(
    page: int = 1,
    limit: int = 50,
    action: str = "",
    user_name: str = "",
    entity_type: str = "",
    current_user: UserResponse = Depends(get_current_user)
):
    """Get activity logs with pagination and filtering"""
    skip = (page - 1) * limit
    
    # Build query
    query = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if user_name:
        query["user_name"] = {"$regex": user_name, "$options": "i"}
    if entity_type:
        query["entity_type"] = entity_type
    
    # Get total count for pagination
    total_count = await db.activity_logs.count_documents(query)
    
    # Get logs with pagination
    logs = await db.activity_logs.find(query).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "logs": [ActivityLog(**log) for log in logs],
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@api_router.post("/activity-logs")
async def create_activity_log(log: ActivityLogCreate, current_user: UserResponse = Depends(get_current_user)):
    """Create a new activity log entry"""
    activity = ActivityLog(**log.dict())
    await db.activity_logs.insert_one(activity.dict())
    return {"message": "Activity logged successfully"}

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

@api_router.get("/rooms/{room_id}")
async def get_room(room_id: str):
    room = await db.rooms.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Convert datetime back to date for response
    if isinstance(room.get('check_in_date'), datetime):
        room['check_in_date'] = room['check_in_date'].date()
    if isinstance(room.get('check_out_date'), datetime):
        room['check_out_date'] = room['check_out_date'].date()
    
    return Room(**room)

@api_router.get("/rooms/availability/check")
async def check_room_availability(
    check_in_date: str,
    check_out_date: str
):
    """
    Check room availability for specific date range
    Returns list of available rooms with their details
    """
    try:
        # Parse date strings
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d').date()
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d').date()
        
        # Validate dates
        if check_in >= check_out:
            raise HTTPException(status_code=400, detail="Check-out date must be after check-in date")
        
        if check_in < datetime.now().date():
            raise HTTPException(status_code=400, detail="Check-in date cannot be in the past")
        
        # Convert dates to datetime for database queries
        check_in_datetime = datetime.combine(check_in, datetime.min.time())
        check_out_datetime = datetime.combine(check_out, datetime.min.time())
        
        # Get all rooms
        all_rooms = await db.rooms.find().to_list(1000)
        
        # Find conflicting bookings (bookings that overlap with requested dates)
        conflicting_bookings = await db.bookings.find({
            "$and": [
                {"status": {"$in": ["Upcoming", "Checked-in", "Checked In"]}},
                {
                    "$or": [
                        # Booking starts during requested period
                        {
                            "$and": [
                                {"check_in_date": {"$gte": check_in_datetime}},
                                {"check_in_date": {"$lt": check_out_datetime}}
                            ]
                        },
                        # Booking ends during requested period
                        {
                            "$and": [
                                {"check_out_date": {"$gt": check_in_datetime}},
                                {"check_out_date": {"$lte": check_out_datetime}}
                            ]
                        },
                        # Booking encompasses requested period
                        {
                            "$and": [
                                {"check_in_date": {"$lte": check_in_datetime}},
                                {"check_out_date": {"$gte": check_out_datetime}}
                            ]
                        }
                    ]
                }
            ]
        }).to_list(1000)
        
        # Get room numbers that are booked during the requested period
        booked_room_numbers = {booking['room_number'] for booking in conflicting_bookings}
        
        # Filter available rooms
        available_rooms = []
        for room in all_rooms:
            if room['room_number'] not in booked_room_numbers:
                # Remove MongoDB ObjectId field and convert datetime to date
                room_data = {k: v for k, v in room.items() if k != '_id'}
                if isinstance(room_data.get('check_in_date'), datetime):
                    room_data['check_in_date'] = room_data['check_in_date'].date()
                if isinstance(room_data.get('check_out_date'), datetime):
                    room_data['check_out_date'] = room_data['check_out_date'].date()
                if isinstance(room_data.get('created_at'), datetime):
                    room_data['created_at'] = room_data['created_at'].isoformat()
                available_rooms.append(room_data)
        
        # Calculate stay duration for pricing
        stay_duration = (check_out - check_in).days
        
        return {
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "stay_duration": stay_duration,
            "total_rooms": len(all_rooms),
            "available_rooms": len(available_rooms),
            "rooms": available_rooms
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except HTTPException:
        raise  # Re-raise HTTPException as-is to preserve status codes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking availability: {str(e)}")

# Booking Management Routes
@api_router.get("/bookings")
async def get_bookings(
    page: int = 1,
    limit: int = 20,
    search: str = "",
    status: str = ""
):
    """
    Get bookings with pagination and search functionality
    """
    skip = (page - 1) * limit
    
    # Build search query
    query = {}
    
    if search:
        # Search in guest name, email, phone, or room number
        # Handle null values by also checking for field existence
        query["$or"] = [
            {"guest_name": {"$regex": search, "$options": "i"}},
            {"$and": [
                {"guest_email": {"$exists": True, "$ne": None, "$ne": ""}},
                {"guest_email": {"$regex": search, "$options": "i"}}
            ]},
            {"$and": [
                {"guest_phone": {"$exists": True, "$ne": None, "$ne": ""}},
                {"guest_phone": {"$regex": search, "$options": "i"}}
            ]},
            {"room_number": {"$regex": search, "$options": "i"}}
        ]
    
    if status:
        query["status"] = status
    
    # Get total count for pagination
    total_count = await db.bookings.count_documents(query)
    
    # Get bookings with pagination
    bookings = await db.bookings.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    # Convert datetime back to date for response
    for booking in bookings:
        if isinstance(booking.get('check_in_date'), datetime):
            booking['check_in_date'] = booking['check_in_date'].date()
        if isinstance(booking.get('check_out_date'), datetime):
            booking['check_out_date'] = booking['check_out_date'].date()
    
    return {
        "bookings": [Booking(**booking) for booking in bookings],
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit
    }

@api_router.get("/bookings/download")
async def download_bookings(
    start_date: str = "",
    end_date: str = "",
    status: str = ""
):
    """
    Download bookings data as CSV
    """
    query = {}
    
    # Filter by date range if provided
    if start_date and end_date:
        try:
            start_datetime = datetime.combine(datetime.strptime(start_date, '%Y-%m-%d').date(), datetime.min.time())
            end_datetime = datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), datetime.max.time())
            query["created_at"] = {"$gte": start_datetime, "$lte": end_datetime}
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Filter by status if provided
    if status:
        query["status"] = status
    
    # Get all bookings matching the criteria
    bookings = await db.bookings.find(query).sort("created_at", -1).to_list(None)
    
    # Convert to CSV format
    csv_data = []
    headers = [
        "Guest Name", "Email", "Phone", "ID/Passport", "Country", 
        "Room Number", "Check-in Date", "Check-out Date", "Stay Type",
        "Booking Amount", "Status", "Created At", "Additional Notes"
    ]
    csv_data.append(headers)
    
    for booking in bookings:
        # Convert datetime back to date for CSV
        check_in_date = booking.get('check_in_date')
        check_out_date = booking.get('check_out_date')
        created_at = booking.get('created_at')
        
        if isinstance(check_in_date, datetime):
            check_in_date = check_in_date.date()
        if isinstance(check_out_date, datetime):
            check_out_date = check_out_date.date()
        if isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        row = [
            booking.get('guest_name', ''),
            booking.get('guest_email', ''),
            booking.get('guest_phone', ''),
            booking.get('guest_id_passport', ''),
            booking.get('guest_country', ''),
            booking.get('room_number', ''),
            str(check_in_date) if check_in_date else '',
            str(check_out_date) if check_out_date else '',
            booking.get('stay_type', ''),
            booking.get('booking_amount', 0),
            booking.get('status', ''),
            created_at,
            booking.get('additional_notes', '')
        ]
        csv_data.append(row)
    
    return {
        "data": csv_data,
        "filename": f"bookings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    }

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
async def create_booking(booking: BookingCreate, current_user: UserResponse = Depends(get_current_user)):
    booking_dict = booking.dict()
    
    # Validate booking channel if provided
    if booking_dict.get('booking_channel_id'):
        channel = await db.booking_channels.find_one({"id": booking_dict['booking_channel_id']})
        if not channel:
            raise HTTPException(status_code=400, detail="Invalid booking channel")
        if not channel.get('is_active', True):
            raise HTTPException(status_code=400, detail="Booking channel is inactive")
        # Update channel name from database
        booking_dict['booking_channel_name'] = channel['channel_name']
    else:
        # Default to Direct booking if no channel specified
        booking_dict['booking_channel_name'] = "Direct"
    
    # Convert date strings to date objects for processing
    if isinstance(booking_dict.get('check_in_date'), str):
        booking_dict['check_in_date'] = datetime.strptime(booking_dict['check_in_date'], '%Y-%m-%d').date()
    
    # Handle short time stays - set checkout date to same day
    if booking_dict.get('stay_type') == 'Short Time':
        booking_dict['check_out_date'] = booking_dict['check_in_date']
    else:
        # Handle night stay checkout dates
        if booking_dict.get('check_out_date'):
            if isinstance(booking_dict.get('check_out_date'), str):
                booking_dict['check_out_date'] = datetime.strptime(booking_dict['check_out_date'], '%Y-%m-%d').date()
        else:
            # Default to same day if no checkout date provided
            booking_dict['check_out_date'] = booking_dict['check_in_date']
    
    # Validate room availability before creating booking
    is_available, availability_error = await check_room_availability_for_booking(
        room_number=booking.room_number,
        check_in_date=booking_dict['check_in_date'],
        check_out_date=booking_dict['check_out_date']
    )
    
    if not is_available:
        raise HTTPException(status_code=400, detail=availability_error)
    
    
    # Use the provided booking_status, default to "Upcoming"
    final_status = booking_dict.get('booking_status', 'Upcoming')
    booking_obj = Booking(**booking_dict, status=final_status)
    
    # Convert date objects to datetime for MongoDB storage
    booking_storage = booking_obj.dict()
    if booking_storage.get('check_in_date'):
        booking_storage['check_in_date'] = datetime.combine(booking_storage['check_in_date'], datetime.min.time())
    if booking_storage.get('check_out_date'):
        booking_storage['check_out_date'] = datetime.combine(booking_storage['check_out_date'], datetime.min.time())
    
    await db.bookings.insert_one(booking_storage)
    
    # If booking status is "Checked In", also create a customer record
    if final_status == "Checked In":
        customer_data = {
            "name": booking.guest_name,
            "email": booking.guest_email,
            "phone": booking.guest_phone,
            "current_room": booking.room_number,
            "check_in_date": booking_dict['check_in_date'],
            "check_out_date": booking_dict['check_out_date'],  # Keep planned checkout date
            "advance_amount": 0.0,  # No advance amount for past date check-ins
            "notes": booking.additional_notes,
            "room_charges": booking.booking_amount,
            "additional_charges": 0.0,
            "total_amount": booking.booking_amount,
            "is_checked_out": False,  # Currently checked in
            "actual_checkout_date": None  # No actual checkout yet
        }
        
        customer_obj = Customer(**customer_data)
        customer_storage = customer_obj.dict()
        
        # Convert date objects to datetime for MongoDB storage
        if customer_storage.get('check_in_date'):
            customer_storage['check_in_date'] = datetime.combine(customer_storage['check_in_date'], datetime.min.time())
        if customer_storage.get('check_out_date'):
            customer_storage['check_out_date'] = datetime.combine(customer_storage['check_out_date'], datetime.min.time())
        if customer_storage.get('actual_checkout_date'):
            customer_storage['actual_checkout_date'] = datetime.combine(customer_storage['actual_checkout_date'], datetime.min.time())
        
        await db.customers.insert_one(customer_storage)
        
        # Update room status to Occupied
        await db.rooms.update_one(
            {"room_number": booking.room_number},
            {"$set": {
                "status": "Occupied",
                "current_guest": booking.guest_name,
                "check_in_date": datetime.combine(booking_dict['check_in_date'], datetime.min.time()),
                "check_out_date": datetime.combine(booking_dict['check_out_date'], datetime.min.time())
            }}
        )
    
    # Log activity
    await log_activity(
        action="booking_created",
        description=f"New booking created for {booking.guest_name} in room {booking.room_number} via {booking_dict['booking_channel_name']} (Status: {final_status})",
        user_name=current_user.username,
        entity_type="booking",
        entity_id=booking_obj.id,
        details={
            "guest_name": booking.guest_name,
            "room_number": booking.room_number,
            "booking_amount": booking.booking_amount,
            "stay_type": booking.stay_type,
            "booking_channel": booking_dict['booking_channel_name'],
            "booking_status": final_status
        }
    )
    
    return booking_obj

@api_router.put("/bookings/{booking_id}")
async def update_booking(
    booking_id: str, 
    booking_update: BookingUpdate, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Update booking details - allows room changes only for upcoming bookings"""
    # Get the current booking
    current_booking = await db.bookings.find_one({"id": booking_id})
    if not current_booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if booking can be modified
    booking_status = current_booking.get('status', 'Upcoming')
    
    # Allow different types of modifications based on status
    if booking_status == 'Upcoming':
        # Upcoming bookings can be fully modified
        can_modify_room = True
        can_modify_dates = True
        can_modify_guest_info = True
    elif booking_status in ['Checked-in', 'Checked In']:
        # Checked-in bookings can only have dates extended (not shortened) and guest info updated
        can_modify_room = False  # Can't change room for checked-in guests
        can_modify_dates = True  # Can extend dates
        can_modify_guest_info = True  # Can update guest information
    else:
        # Other statuses (Cancelled, Completed) cannot be modified
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot modify booking with status '{booking_status}'. Only 'Upcoming' and 'Checked-in' bookings can be modified."
        )
    
    update_data = {}
    changes_made = []
    
    # Handle room number change with availability validation
    if booking_update.room_number is not None:
        if not can_modify_room:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot change room for booking with status '{booking_status}'. Room changes are only allowed for 'Upcoming' bookings."
            )
            
        new_room = booking_update.room_number
        current_room = current_booking.get('room_number')
        
        if new_room != current_room:
            # Check if new room is available for the booking dates
            check_in = current_booking.get('check_in_date')
            check_out = current_booking.get('check_out_date')
            
            if isinstance(check_in, datetime):
                check_in_date = check_in.date()
            else:
                check_in_date = check_in
                
            if isinstance(check_out, datetime):
                check_out_date = check_out.date()
            else:
                check_out_date = check_out
            
            # Check for conflicting bookings in the new room (excluding current booking)
            conflicting_bookings = await db.bookings.find({
                "room_number": new_room,
                "id": {"$ne": booking_id},  # Exclude current booking
                "status": {"$in": ["Upcoming", "Checked In"]},
                "$or": [
                    {
                        "check_in_date": {"$lte": datetime.combine(check_out_date, datetime.min.time())},
                        "check_out_date": {"$gte": datetime.combine(check_in_date, datetime.min.time())}
                    }
                ]
            }).to_list(100)
            
            if conflicting_bookings:
                conflicting_guest = conflicting_bookings[0].get('guest_name', 'Unknown')
                conflicting_dates = f"{conflicting_bookings[0].get('check_in_date', '').strftime('%Y-%m-%d') if conflicting_bookings[0].get('check_in_date') else 'N/A'} to {conflicting_bookings[0].get('check_out_date', '').strftime('%Y-%m-%d') if conflicting_bookings[0].get('check_out_date') else 'N/A'}"
                raise HTTPException(
                    status_code=400, 
                    detail=f"Room {new_room} is not available for the requested dates. Conflict with booking for {conflicting_guest} ({conflicting_dates})"
                )
            
            update_data['room_number'] = new_room
            changes_made.append(f"Room changed from {current_room} to {new_room}")
    
    # Handle other updates
    if booking_update.check_in_date is not None:
        update_data['check_in_date'] = datetime.combine(booking_update.check_in_date, datetime.min.time())
        changes_made.append(f"Check-in date updated to {booking_update.check_in_date}")
        
    if booking_update.check_out_date is not None:
        update_data['check_out_date'] = datetime.combine(booking_update.check_out_date, datetime.min.time())
        changes_made.append(f"Check-out date updated to {booking_update.check_out_date}")
        
    if booking_update.additional_notes is not None:
        update_data['additional_notes'] = booking_update.additional_notes
        changes_made.append("Notes updated")
    
    # Recalculate booking amount if dates have changed
    if booking_update.check_in_date is not None or booking_update.check_out_date is not None:
        if not can_modify_dates:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot modify dates for booking with status '{booking_status}'."
            )
        
        # Get current and new dates
        current_check_in = current_booking.get('check_in_date')
        current_check_out = current_booking.get('check_out_date')
        
        # Convert current dates to date objects if they're datetime
        if isinstance(current_check_in, datetime):
            current_check_in = current_check_in.date()
        if isinstance(current_check_out, datetime):
            current_check_out = current_check_out.date()
        
        # Use new dates if provided, otherwise use current ones
        new_check_in = booking_update.check_in_date if booking_update.check_in_date is not None else current_check_in
        new_check_out = booking_update.check_out_date if booking_update.check_out_date is not None else current_check_out
        
        # Special validation for checked-in bookings
        if booking_status in ['Checked-in', 'Checked In']:
            # For checked-in bookings, only allow extending checkout date
            if booking_update.check_in_date is not None and booking_update.check_in_date != current_check_in:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot change check-in date for checked-in bookings. Guest is already checked in."
                )
            
            # Only allow extending checkout date (not shortening)
            if booking_update.check_out_date is not None and booking_update.check_out_date < current_check_out:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot shorten checkout date for checked-in bookings. Only extensions are allowed."
                )
        
        # Get room information to calculate new amount
        room = await db.rooms.find_one({"room_number": current_booking.get('room_number')})
        if room:
            price_per_night = room.get('price_per_night', 0.0)
            
            # Recalculate stay_type based on new dates
            if new_check_in == new_check_out:
                # Same day = Short Time
                stay_type = 'Short Time'
                new_booking_amount = price_per_night * 0.5
            else:
                # Different days = Night Stay
                stay_type = 'Night Stay'
                nights = (new_check_out - new_check_in).days
                if nights <= 0:
                    nights = 1  # Minimum 1 night
                new_booking_amount = price_per_night * nights
            
            # Update stay_type if it has changed
            current_stay_type = current_booking.get('stay_type', 'Night Stay')
            if stay_type != current_stay_type:
                update_data['stay_type'] = stay_type
                changes_made.append(f"Stay type updated from {current_stay_type} to {stay_type}")
            
            # Update booking amount if it has changed
            current_amount = current_booking.get('booking_amount', 0.0)
            if abs(new_booking_amount - current_amount) > 0.01:  # Use small epsilon for float comparison
                update_data['booking_amount'] = new_booking_amount
                changes_made.append(f"Booking amount updated from {current_amount} to {new_booking_amount}")
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")
    
    # Update the booking
    result = await db.bookings.update_one({"id": booking_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # If the booking is checked in, also update the corresponding customer record
    if current_booking.get('status') == 'Checked In':
        customer_update_data = {}
        
        # Update customer record with new dates if they changed
        if 'check_in_date' in update_data:
            customer_update_data['check_in_date'] = update_data['check_in_date']
        if 'check_out_date' in update_data:
            customer_update_data['check_out_date'] = update_data['check_out_date']
        if 'booking_amount' in update_data:
            customer_update_data['room_charges'] = update_data['booking_amount']
            customer_update_data['total_amount'] = update_data['booking_amount']  # Recalculate total
        
        if customer_update_data:
            # Find and update customer record based on booking details
            await db.customers.update_one(
                {
                    "name": current_booking.get('guest_name'),
                    "current_room": current_booking.get('room_number')
                },
                {"$set": customer_update_data}
            )
            changes_made.append("Customer record updated")
    
    # Log activity
    await log_activity(
        action="booking_updated",
        description=f"Booking for {current_booking.get('guest_name', 'Unknown')} updated: {', '.join(changes_made)}",
        user_name=current_user.username,
        entity_type="booking",
        entity_id=booking_id,
        details={
            "changes": changes_made,
            "guest_name": current_booking.get('guest_name'),
            "old_room": current_booking.get('room_number'),
            "new_room": update_data.get('room_number', current_booking.get('room_number'))
        }
    )
    
    return {
        "message": "Booking updated successfully",
        "changes": changes_made
    }

# Customer Management Routes
@api_router.post("/migrate-customers")
async def migrate_customers():
    """Migrate existing customers to new schema"""
    # Update all customers to have is_checked_out = False if not present
    await db.customers.update_many(
        {"is_checked_out": {"$exists": False}},
        {"$set": {"is_checked_out": False, "actual_checkout_date": None}}
    )
    
    # Fix any customers that have check_out_date = None (from previous logic)
    customers_with_null_checkout = await db.customers.find({"check_out_date": None}).to_list(1000)
    
    for customer in customers_with_null_checkout:
        # Find the corresponding booking to get the planned checkout date
        booking = await db.bookings.find_one({
            "guest_name": customer["name"],
            "room_number": customer["current_room"]
        })
        
        if booking and booking.get("check_out_date"):
            planned_checkout = booking["check_out_date"]
            if isinstance(planned_checkout, datetime):
                planned_checkout = planned_checkout.date()
            
            await db.customers.update_one(
                {"id": customer["id"]},
                {"$set": {"check_out_date": datetime.combine(planned_checkout, datetime.min.time())}}
            )
    
    return {"message": "Customer migration completed"}

@api_router.get("/customers/checked-in", response_model=List[Customer])
async def get_checked_in_customers():
    # Get only customers who are currently checked in (is_checked_out = False)
    customers = await db.customers.find({
        "is_checked_out": False  # Only customers who haven't checked out
    }).to_list(1000)
    
    # Convert datetime back to date for response
    for customer in customers:
        if customer.get('check_in_date'):
            customer['check_in_date'] = customer['check_in_date'].date() if isinstance(customer['check_in_date'], datetime) else customer['check_in_date']
        if customer.get('check_out_date'):
            customer['check_out_date'] = customer['check_out_date'].date() if isinstance(customer['check_out_date'], datetime) else customer['check_out_date']
        if customer.get('actual_checkout_date'):
            customer['actual_checkout_date'] = customer['actual_checkout_date'].date() if isinstance(customer['actual_checkout_date'], datetime) else customer['actual_checkout_date']
    
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
    restaurant_charges = customer.get('restaurant_charges', 0.0)  # Restaurant charges
    advance_amount = customer.get('advance_amount', 0.0)
    additional_amount = checkout.additional_amount
    discount_amount = checkout.discount_amount
    total_amount = base_room_charges + restaurant_charges + additional_amount - advance_amount - discount_amount
    
    # Create daily sales record
    daily_sale = DailySale(
        date=datetime.now().date(),
        customer_name=customer.get('name', ''),
        room_number=customer.get('current_room', ''),
        room_charges=base_room_charges,
        additional_charges=restaurant_charges + additional_amount,  # Include restaurant charges
        discount_amount=discount_amount,
        advance_amount=advance_amount,
        total_amount=total_amount,
        payment_method=checkout.payment_method
    )
    
    # Store the daily sale record
    daily_sale_dict = daily_sale.dict()
    daily_sale_dict['date'] = datetime.combine(daily_sale_dict['date'], datetime.min.time())
    await db.daily_sales.insert_one(daily_sale_dict)
    
    # Update customer with final billing details and mark as checked out
    await db.customers.update_one(
        {"id": checkout.customer_id},
        {"$set": {
            "additional_charges": additional_amount,
            "restaurant_charges": restaurant_charges,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "is_checked_out": True,  # Mark as checked out
            "actual_checkout_date": datetime.now()  # Set actual checkout date
        }}
    )
    
    # Verify customer was updated
    result = await db.customers.find_one({"id": checkout.customer_id})
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update corresponding booking status to "Completed"
    await db.bookings.update_one(
        {
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "status": {"$in": ["Checked-in", "Checked In"]}
        },
        {"$set": {"status": "Completed"}}
    )
    
    # Update room status to available
    await db.rooms.update_one(
        {"room_number": customer["current_room"]},
        {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
    )
    
    # Log activity
    await log_activity(
        action="customer_checked_out",
        description=f"Customer {customer.get('name', 'Unknown')} checked out from room {customer['current_room']}",
        entity_type="checkout",
        entity_id=checkout.customer_id,
        details={
            "guest_name": customer.get("name"),
            "room_number": customer["current_room"],
            "total_amount": total_amount,
            "payment_method": checkout.payment_method
        }
    )
    
    # Mark all pending restaurant orders for this room as paid
    await db.restaurant_orders.update_many(
        {
            "room_number": customer.get('current_room'),
            "payment_status": "Pending"
        },
        {"$set": {
            "payment_status": "Paid",
            "payment_method": f"Room Bill - {checkout.payment_method}",
            "order_status": "Completed"
        }}
    )
    
    return {
        "message": "Customer checked out successfully",
        "billing_details": {
            "room_charges": base_room_charges,
            "restaurant_charges": restaurant_charges,
            "advance_amount": advance_amount,
            "additional_charges": additional_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "payment_method": checkout.payment_method
        }
    }

@api_router.post("/extend-stay")
async def extend_customer_stay(
    extend_request: ExtendStayRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Extend a checked-in customer's stay and update room charges accordingly"""
    # Find the customer
    customer = await db.customers.find_one({"id": extend_request.customer_id, "is_checked_out": False})
    if not customer:
        raise HTTPException(status_code=404, detail="Checked-in customer not found")
    
    current_checkout = customer.get('check_out_date')
    if isinstance(current_checkout, datetime):
        current_checkout = current_checkout.date()
    
    check_in_date = customer.get('check_in_date')
    if isinstance(check_in_date, datetime):
        check_in_date = check_in_date.date()
    
    new_checkout = extend_request.new_checkout_date
    
    # Validate new checkout date is after current checkout
    if new_checkout <= current_checkout:
        raise HTTPException(
            status_code=400, 
            detail=f"New checkout date must be after current checkout date ({current_checkout})"
        )
    
    room_number = customer.get('current_room')
    
    # Get room to calculate additional charges
    room = await db.rooms.find_one({"room_number": room_number})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check for booking conflicts before extending stay
    # Find the current booking for this customer to exclude it from conflict check
    current_booking = await db.bookings.find_one({
        "guest_name": customer.get('name'),
        "room_number": room_number,
        "status": {"$in": ["Checked-in", "Checked In"]}
    })
    
    exclude_booking_id = current_booking.get('id') if current_booking else None
    
    # Check if extending conflicts with other bookings
    is_available, conflict_error = await check_room_availability_for_booking(
        room_number=room_number,
        check_in_date=check_in_date,  # Use original check-in
        check_out_date=new_checkout,   # Use new checkout
        exclude_booking_id=exclude_booking_id
    )
    
    if not is_available:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot extend stay: {conflict_error}"
        )
    
    price_per_night = room.get('price_per_night', 0.0)
    
    # Calculate additional nights and charges
    additional_nights = (new_checkout - current_checkout).days
    additional_charges = price_per_night * additional_nights
    
    # Update customer record
    current_room_charges = customer.get('room_charges', 0.0)
    new_room_charges = current_room_charges + additional_charges
    
    await db.customers.update_one(
        {"id": extend_request.customer_id},
        {"$set": {
            "check_out_date": datetime.combine(new_checkout, datetime.min.time()),
            "room_charges": new_room_charges
        }}
    )
    
    # Update room checkout date
    await db.rooms.update_one(
        {"room_number": customer.get('current_room')},
        {"$set": {"check_out_date": datetime.combine(new_checkout, datetime.min.time())}}
    )
    
    # Update corresponding booking
    await db.bookings.update_one(
        {
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "status": {"$in": ["Checked-in", "Checked In"]}
        },
        {"$set": {
            "check_out_date": datetime.combine(new_checkout, datetime.min.time()),
            "booking_amount": new_room_charges
        }}
    )
    
    # Log activity
    await log_activity(
        action="stay_extended",
        description=f"Extended stay for {customer.get('name')} from {current_checkout} to {new_checkout}",
        user_name=current_user.username,
        entity_type="customer",
        entity_id=extend_request.customer_id,
        details={
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "old_checkout": str(current_checkout),
            "new_checkout": str(new_checkout),
            "additional_nights": additional_nights,
            "additional_charges": additional_charges
        }
    )
    
    return {
        "message": "Stay extended successfully",
        "details": {
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "old_checkout_date": str(current_checkout),
            "new_checkout_date": str(new_checkout),
            "additional_nights": additional_nights,
            "additional_charges": additional_charges,
            "previous_room_charges": current_room_charges,
            "new_room_charges": new_room_charges
        }
    }

@api_router.post("/early-checkout")
async def early_checkout_customer(
    checkout_request: EarlyCheckoutRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Handle early checkout with potential refund calculation"""
    # Find customer
    customer = await db.customers.find_one({"id": checkout_request.customer_id, "is_checked_out": False})
    if not customer:
        raise HTTPException(status_code=404, detail="Checked-in customer not found")
    
    planned_checkout = customer.get('check_out_date')
    if isinstance(planned_checkout, datetime):
        planned_checkout = planned_checkout.date()
    
    check_in_date = customer.get('check_in_date')
    if isinstance(check_in_date, datetime):
        check_in_date = check_in_date.date()
    
    actual_checkout = datetime.now().date()
    
    # Calculate planned nights to derive the customer's actual booked rate
    planned_nights = (planned_checkout - check_in_date).days
    if planned_nights < 1:
        planned_nights = 1
    
    original_room_charges = customer.get('room_charges', 0.0)
    
    # Use customer's actual booked rate per night (not room's default rate)
    # This ensures we use the rate the customer was charged, which may differ from room's current rate
    customer_rate_per_night = original_room_charges / planned_nights if planned_nights > 0 else 0.0
    
    # Calculate actual stay duration
    actual_nights = (actual_checkout - check_in_date).days
    if actual_nights < 1:
        actual_nights = 1  # Minimum 1 night charge
    
    # Calculate charges based on customer's booked rate, not room's default rate
    actual_room_charges = customer_rate_per_night * actual_nights
    
    # Calculate difference (positive = customer overpaid, negative = customer owes more)
    charge_difference = original_room_charges - actual_room_charges
    
    restaurant_charges = customer.get('restaurant_charges', 0.0)
    advance_amount = customer.get('advance_amount', 0.0)
    additional_amount = checkout_request.additional_amount
    discount_amount = checkout_request.discount_amount
    
    # Final room charges based on actual stay
    final_room_charges = actual_room_charges
    
    # Calculate total
    total_amount = final_room_charges + restaurant_charges + additional_amount - advance_amount - discount_amount
    
    # Handle refund logic
    refund_amount = 0.0
    if charge_difference > 0:  # Customer overpaid
        if checkout_request.refund_excess:
            refund_amount = charge_difference
            # If refunding, we use actual charges
        else:
            # Keep the excess - use original charges
            final_room_charges = original_room_charges
            total_amount = final_room_charges + restaurant_charges + additional_amount - advance_amount - discount_amount
    
    # Create daily sales record
    daily_sale = DailySale(
        date=datetime.now().date(),
        customer_name=customer.get('name', ''),
        room_number=customer.get('current_room', ''),
        room_charges=final_room_charges,
        additional_charges=restaurant_charges + additional_amount,
        discount_amount=discount_amount,
        advance_amount=advance_amount,
        total_amount=total_amount,
        payment_method=checkout_request.payment_method
    )
    
    daily_sale_dict = daily_sale.dict()
    daily_sale_dict['date'] = datetime.combine(daily_sale_dict['date'], datetime.min.time())
    await db.daily_sales.insert_one(daily_sale_dict)
    
    # If refunding, record as expense
    if refund_amount > 0:
        expense_id = str(uuid.uuid4())
        await db.expenses.insert_one({
            "id": expense_id,
            "date": datetime.combine(datetime.now().date(), datetime.min.time()),
            "category": "Refund",
            "description": f"Early checkout refund for {customer.get('name')} - Room {customer.get('current_room')}",
            "amount": refund_amount,
            "payment_method": checkout_request.payment_method,
            "created_by": current_user.username,
            "created_at": datetime.now()
        })
    
    # Update customer record
    await db.customers.update_one(
        {"id": checkout_request.customer_id},
        {"$set": {
            "room_charges": final_room_charges,
            "additional_charges": additional_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "is_checked_out": True,
            "actual_checkout_date": datetime.now()
        }}
    )
    
    # Update booking status
    await db.bookings.update_one(
        {
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "status": {"$in": ["Checked-in", "Checked In"]}
        },
        {"$set": {"status": "Completed"}}
    )
    
    # Update room status
    await db.rooms.update_one(
        {"room_number": customer.get('current_room')},
        {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
    )
    
    # Mark restaurant orders as paid
    await db.restaurant_orders.update_many(
        {
            "room_number": customer.get('current_room'),
            "payment_status": "Pending"
        },
        {"$set": {
            "payment_status": "Paid",
            "payment_method": f"Room Bill - {checkout_request.payment_method}",
            "order_status": "Completed"
        }}
    )
    
    # Log activity
    await log_activity(
        action="early_checkout",
        description=f"Early checkout for {customer.get('name')} from room {customer.get('current_room')}",
        user_name=current_user.username,
        entity_type="checkout",
        entity_id=checkout_request.customer_id,
        details={
            "guest_name": customer.get('name'),
            "room_number": customer.get('current_room'),
            "planned_checkout": str(planned_checkout),
            "actual_checkout": str(actual_checkout),
            "days_early": (planned_checkout - actual_checkout).days,
            "original_charges": original_room_charges,
            "actual_charges": actual_room_charges,
            "refund_amount": refund_amount,
            "refund_given": checkout_request.refund_excess
        }
    )
    
    return {
        "message": "Early checkout completed successfully",
        "billing_details": {
            "check_in_date": str(check_in_date),
            "planned_checkout_date": str(planned_checkout),
            "actual_checkout_date": str(actual_checkout),
            "days_early": (planned_checkout - actual_checkout).days,
            "planned_nights": planned_nights,
            "actual_nights": actual_nights,
            "rate_per_night": customer_rate_per_night,
            "original_room_charges": original_room_charges,
            "actual_room_charges": actual_room_charges,
            "charge_difference": charge_difference,
            "refund_given": checkout_request.refund_excess,
            "refund_amount": refund_amount if checkout_request.refund_excess else 0,
            "final_room_charges": final_room_charges,
            "restaurant_charges": restaurant_charges,
            "additional_charges": additional_amount,
            "discount_amount": discount_amount,
            "advance_amount": advance_amount,
            "total_amount": total_amount,
            "payment_method": checkout_request.payment_method
        }
    }

@api_router.get("/customer/{customer_id}/checkout-preview")
async def preview_checkout(
    customer_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Preview checkout details including early checkout calculations"""
    customer = await db.customers.find_one({"id": customer_id, "is_checked_out": False})
    if not customer:
        raise HTTPException(status_code=404, detail="Checked-in customer not found")
    
    planned_checkout = customer.get('check_out_date')
    if isinstance(planned_checkout, datetime):
        planned_checkout = planned_checkout.date()
    
    check_in_date = customer.get('check_in_date')
    if isinstance(check_in_date, datetime):
        check_in_date = check_in_date.date()
    
    actual_checkout = datetime.now().date()
    
    # Calculate planned stays first
    planned_nights = (planned_checkout - check_in_date).days
    if planned_nights < 1:
        planned_nights = 1
    
    # Calculate the customer's actual rate per night from their booking
    original_room_charges = customer.get('room_charges', 0.0)
    customer_rate_per_night = original_room_charges / planned_nights if planned_nights > 0 else 0
    
    # Calculate actual stays
    actual_nights = (actual_checkout - check_in_date).days
    if actual_nights < 1:
        actual_nights = 1
    
    # Calculate charges based on customer's rate, not room's default rate
    actual_room_charges = customer_rate_per_night * actual_nights
    
    is_early_checkout = actual_checkout < planned_checkout
    charge_difference = original_room_charges - actual_room_charges if is_early_checkout else 0
    
    return {
        "customer_name": customer.get('name'),
        "room_number": customer.get('current_room'),
        "check_in_date": str(check_in_date),
        "planned_checkout_date": str(planned_checkout),
        "actual_checkout_date": str(actual_checkout),
        "is_early_checkout": is_early_checkout,
        "planned_nights": planned_nights,
        "actual_nights": actual_nights,
        "days_early": (planned_checkout - actual_checkout).days if is_early_checkout else 0,
        "price_per_night": customer_rate_per_night,
        "original_room_charges": original_room_charges,
        "actual_room_charges": actual_room_charges,
        "potential_refund": charge_difference if charge_difference > 0 else 0,
        "restaurant_charges": customer.get('restaurant_charges', 0.0),
        "advance_amount": customer.get('advance_amount', 0.0)
    }

@api_router.post("/advance-payment")
async def collect_advance_payment(
    advance_request: AdvancePaymentRequest, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Collect advance payment from checked-in customer and record as income"""
    # Find the customer
    customer = await db.customers.find_one({"id": advance_request.customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Update customer's advance amount (increase it)
    current_advance = customer.get("advance_amount", 0.0)
    new_advance = current_advance + advance_request.amount
    
    await db.customers.update_one(
        {"id": advance_request.customer_id},
        {"$set": {"advance_amount": new_advance}}
    )
    
    # Record as income
    income = Income(
        description=f"Advance payment from {customer['name']} - Room {customer['current_room']}",
        amount=advance_request.amount,
        category="Advance Payment",
        payment_method=advance_request.payment_method,
        income_date=datetime.now().date(),
        guest_name=customer["name"],
        created_by=current_user.username
    )
    
    # Convert date to datetime for MongoDB storage
    income_dict = income.dict()
    income_dict['income_date'] = datetime.combine(income_dict['income_date'], datetime.min.time())
    await db.incomes.insert_one(income_dict)
    
    # Log activity
    await log_activity(
        action="advance_payment_collected",
        description=f"Advance payment of {advance_request.amount} collected from {customer['name']} in room {customer['current_room']}",
        user_name=current_user.username,
        entity_type="payment",
        entity_id=advance_request.customer_id,
        details={
            "guest_name": customer["name"],
            "room_number": customer["current_room"],
            "amount": advance_request.amount,
            "payment_method": advance_request.payment_method,
            "new_total_advance": new_advance
        }
    )
    
    return {
        "message": f"Advance payment of {advance_request.amount} collected successfully",
        "customer_name": customer["name"],
        "amount_collected": advance_request.amount,
        "new_total_advance": new_advance
    }

@api_router.post("/checkin")
async def checkin_customer(checkin: CheckinRequest):
    # Find the booking
    booking = await db.bookings.find_one({"id": checkin.booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if room is available or has a valid booking
    room = await db.rooms.find_one({"room_number": booking["room_number"]})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Allow check-in if room is Available or if it has a booking (not currently occupied)
    if room["status"] == "Occupied":
        # Check if the current guest is different (double booking scenario)
        if room.get("current_guest") and room.get("current_guest") != booking["guest_name"]:
            raise HTTPException(status_code=400, detail="Room is currently occupied by another guest")
    
    
    # Use the booking amount as room charges (actual amount customer agreed to pay)
    room_charges = booking.get("booking_amount", 500.0)
    
    # Ensure advance_amount is a valid number (handle None, empty string, etc.)
    advance_amount = checkin.advance_amount if checkin.advance_amount is not None else 0.0
    
    # Create customer record
    customer = Customer(
        name=booking["guest_name"],
        email=booking["guest_email"],
        phone=booking["guest_phone"],
        current_room=booking["room_number"],
        check_in_date=booking["check_in_date"] if isinstance(booking["check_in_date"], date) else booking["check_in_date"].date(),
        check_out_date=booking["check_out_date"] if isinstance(booking["check_out_date"], date) else booking["check_out_date"].date(),
        advance_amount=advance_amount,
        notes=checkin.notes,
        room_charges=room_charges,
        total_amount=room_charges - advance_amount,
        is_checked_out=False,  # Currently checked in
        actual_checkout_date=None  # No actual checkout yet
    )
    
    # Add customer to checked-in list
    customer_dict = customer.dict()
    customer_dict['check_in_date'] = datetime.combine(customer_dict['check_in_date'], datetime.min.time())
    customer_dict['check_out_date'] = datetime.combine(customer_dict['check_out_date'], datetime.min.time())
    # actual_checkout_date is None, so no conversion needed
    await db.customers.insert_one(customer_dict)
    
    # Record advance amount as daily sale if amount > 0
    if advance_amount > 0:
        advance_sale = DailySale(
            customer_name=booking["guest_name"],
            room_number=booking["room_number"],
            payment_method=checkin.payment_method,
            room_charges=0.0,  # This is advance, not room charge
            additional_charges=advance_amount,  # Record as additional charge
            discount_amount=0.0,
            advance_amount=0.0,  # Already being paid, so no advance for this sale
            total_amount=advance_amount,
            date=datetime.now().date()
        )
        
        # Convert date to datetime for MongoDB storage
        advance_sale_dict = advance_sale.dict()
        advance_sale_dict['date'] = datetime.combine(advance_sale_dict['date'], datetime.min.time())
        await db.daily_sales.insert_one(advance_sale_dict)
    
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
        {"$set": {"status": "Checked In"}}
    )
    
    # Log activity
    await log_activity(
        action="customer_checked_in",
        description=f"Customer {booking['guest_name']} checked in to room {booking['room_number']}",
        entity_type="checkin",
        entity_id=customer.id,
        details={
            "guest_name": booking["guest_name"],
            "room_number": booking["room_number"],
            "advance_amount": checkin.advance_amount,
            "payment_method": checkin.payment_method
        }
    )
    
    return {"message": "Customer checked in successfully", "customer": customer}

@api_router.post("/cancel/{booking_id}")
async def cancel_booking(
    booking_id: str, 
    current_user: UserResponse = Depends(get_current_active_admin)
):
    """Cancel a booking (Admin only) - handles both upcoming and checked-in bookings"""
    # Find the booking
    booking = await db.bookings.find_one({"id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking_status = booking.get("status", "")
    guest_name = booking.get("guest_name", "")
    room_number = booking.get("room_number", "")
    
    # Update booking status to cancelled
    result = await db.bookings.update_one(
        {"id": booking_id},
        {"$set": {"status": "Cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Handle different booking statuses
    if booking_status == "Upcoming":
        # If room was reserved for this booking, make it available
        await db.rooms.update_one(
            {"room_number": room_number, "status": "Reserved"},
            {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
        )
    elif booking_status in ["Checked-in", "Checked In"]:
        # If guest is currently checked in, remove from customers and free up room
        await db.customers.delete_one({
            "name": guest_name,
            "current_room": room_number
        })
        
        # Make room available
        await db.rooms.update_one(
            {"room_number": room_number},
            {"$set": {"status": "Available", "current_guest": None, "check_in_date": None, "check_out_date": None}}
        )
    
    # Log activity
    await log_activity(
        action="booking_cancelled",
        description=f"Booking for {guest_name} in room {room_number} cancelled by admin (was {booking_status})",
        user_name=current_user.username,
        entity_type="booking",
        entity_id=booking_id,
        details={
            "guest_name": guest_name,
            "room_number": room_number,
            "original_status": booking_status
        }
    )
    
    return {
        "message": f"Booking cancelled successfully. Guest {guest_name} removed from room {room_number}.",
        "original_status": booking_status
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
    
    # Create default admin user if no users exist
    existing_users = await db.users.count_documents({})
    if existing_users == 0:
        default_admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="System Administrator",
            role="Admin",
            email="admin@hotel.com"
        )
        await db.users.insert_one(default_admin.dict())
        
        # Create sample staff user
        sample_staff = User(
            username="staff1",
            password_hash=get_password_hash("staff123"),
            full_name="Hotel Staff",
            role="Staff",
            email="staff@hotel.com"
        )
        await db.users.insert_one(sample_staff.dict())
    
    # Create default settings if none exist
    existing_settings = await db.settings.count_documents({})
    if existing_settings == 0:
        default_settings = Settings(
            hotel_name="Grand Hotel Paradise",
            hotel_contact="+94 11 234 5678",
            hotel_address="123 Ocean View Road, Colombo 03, Sri Lanka",
            hotel_email="info@grandhotelparadise.com",
            hotel_phone="+94 11 234 5678",
            currency="LKR",
            check_in_time="14:00",
            check_out_time="12:00",
            default_room_rate=8000.0,
            tax_rate=10.0
        )
        await db.settings.insert_one(default_settings.dict())
    
    # Create default booking channels if none exist
    existing_channels = await db.booking_channels.count_documents({})
    if existing_channels == 0:
        default_channels = [
            BookingChannel(
                channel_name="Direct",
                channel_type="Direct",
                commission_rate=0.0,
                contact_email="",
                contact_phone="",
                is_active=True
            ),
            BookingChannel(
                channel_name="Booking.com",
                channel_type="OTA",
                commission_rate=15.0,
                contact_email="partners@booking.com",
                contact_phone="",
                is_active=True
            ),
            BookingChannel(
                channel_name="Expedia",
                channel_type="OTA", 
                commission_rate=18.0,
                contact_email="partners@expedia.com",
                contact_phone="",
                is_active=True
            ),
            BookingChannel(
                channel_name="Agoda",
                channel_type="OTA",
                commission_rate=16.5,
                contact_email="partners@agoda.com",
                contact_phone="",
                is_active=True
            ),
            BookingChannel(
                channel_name="Walk-in",
                channel_type="Direct",
                commission_rate=0.0,
                contact_email="",
                contact_phone="",
                is_active=True
            ),
            BookingChannel(
                channel_name="Corporate",
                channel_type="Corporate",
                commission_rate=5.0,
                contact_email="corporate@hotel.com",
                contact_phone="",
                is_active=True
            )
        ]
        
        for channel in default_channels:
            await db.booking_channels.insert_one(channel.dict())
    
    # Create restaurant manager user if not exists
    restaurant_manager = await db.users.find_one({"username": "restaurant"})
    if not restaurant_manager:
        restaurant_user = User(
            username="restaurant",
            password_hash=get_password_hash("restaurant123"),
            full_name="Restaurant Manager",
            role="Restaurant Manager",
            email="restaurant@hotel.com"
        )
        await db.users.insert_one(restaurant_user.dict())
    
    # Initialize default menu categories
    existing_categories = await db.menu_categories.count_documents({})
    if existing_categories == 0:
        default_categories = [
            MenuCategory(name="Appetizers", description="Start your meal right", display_order=1),
            MenuCategory(name="Main Course", description="Hearty main dishes", display_order=2),
            MenuCategory(name="Beverages", description="Refreshing drinks", display_order=3),
            MenuCategory(name="Desserts", description="Sweet endings", display_order=4),
        ]
        
        for category in default_categories:
            await db.menu_categories.insert_one(category.dict())
    
    # Initialize sample menu items
    existing_items = await db.menu_items.count_documents({})
    if existing_items == 0:
        # Get category IDs for menu items
        categories = await db.menu_categories.find({"is_active": True}).to_list(10)
        category_map = {cat["name"]: cat["id"] for cat in categories}
        
        if category_map:
            sample_items = [
                MenuItem(name="Spring Rolls", description="Crispy vegetable spring rolls with sweet chili sauce", 
                        price=850.0, category_id=category_map.get("Appetizers", ""), is_vegetarian=True),
                MenuItem(name="Chicken Wings", description="Buffalo chicken wings with blue cheese dip", 
                        price=1200.0, category_id=category_map.get("Appetizers", "")),
                MenuItem(name="Grilled Chicken", description="Herb marinated grilled chicken with vegetables", 
                        price=2200.0, category_id=category_map.get("Main Course", "")),
                MenuItem(name="Fish Curry", description="Traditional Sri Lankan fish curry with rice", 
                        price=1800.0, category_id=category_map.get("Main Course", ""), is_spicy=True),
                MenuItem(name="Vegetable Fried Rice", description="Wok-fried rice with fresh vegetables", 
                        price=1400.0, category_id=category_map.get("Main Course", ""), is_vegetarian=True),
                MenuItem(name="Fresh Lime Juice", description="Freshly squeezed lime juice", 
                        price=450.0, category_id=category_map.get("Beverages", "")),
                MenuItem(name="Coffee", description="Freshly brewed Ceylon coffee", 
                        price=350.0, category_id=category_map.get("Beverages", "")),
                MenuItem(name="Chocolate Cake", description="Rich chocolate cake with vanilla ice cream", 
                        price=800.0, category_id=category_map.get("Desserts", "")),
            ]
            
            for item in sample_items:
                await db.menu_items.insert_one(item.dict())
    
    # Initialize sample restaurant staff
    existing_staff = await db.restaurant_staff.count_documents({})
    if existing_staff == 0:
        sample_staff = [
            RestaurantStaff(name="John Silva", role="Waiter", phone="+94771234567"),
            RestaurantStaff(name="Mary Fernando", role="Waiter", phone="+94771234568"),
            RestaurantStaff(name="Chef Kumar", role="Chef", phone="+94771234569"),
        ]
        
        for staff in sample_staff:
            await db.restaurant_staff.insert_one(staff.dict())
    
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

class GuestUpdateRequest(BaseModel):
    original_email: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    id_passport: Optional[str] = None
    country: Optional[str] = None

@api_router.put("/guests/update")
async def update_guest_details(
    guest_update: GuestUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update guest details across all their bookings and customer records"""
    update_fields = {}
    
    if guest_update.name:
        update_fields['guest_name'] = guest_update.name
    if guest_update.email:
        update_fields['guest_email'] = guest_update.email
    if guest_update.phone:
        update_fields['guest_phone'] = guest_update.phone
    if guest_update.id_passport:
        update_fields['guest_id_passport'] = guest_update.id_passport
    if guest_update.country:
        update_fields['guest_country'] = guest_update.country
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Update all bookings for this guest
    booking_result = await db.bookings.update_many(
        {"guest_email": guest_update.original_email},
        {"$set": update_fields}
    )
    
    # Update customer records if name changed
    customer_update_fields = {}
    if guest_update.name:
        customer_update_fields['name'] = guest_update.name
    if guest_update.email:
        customer_update_fields['email'] = guest_update.email
    if guest_update.phone:
        customer_update_fields['phone'] = guest_update.phone
    
    if customer_update_fields:
        # Find customers by old name from bookings
        old_booking = await db.bookings.find_one({"guest_email": guest_update.email or guest_update.original_email})
        if old_booking:
            await db.customers.update_many(
                {"email": guest_update.original_email},
                {"$set": customer_update_fields}
            )
    
    return {
        "message": "Guest details updated successfully",
        "bookings_updated": booking_result.modified_count
    }

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
    
    # Log activity
    await log_activity(
        action="expense_added",
        description=f"New expense added: {expense.description} - LKR {expense.amount}",
        entity_type="expense",
        entity_id=expense_obj.id,
        details={
            "description": expense.description,
            "amount": expense.amount,
            "category": expense.category
        }
    )
    
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
    
    # Log activity
    await log_activity(
        action="income_added",
        description=f"New income added: {income.description} - LKR {income.amount}",
        entity_type="income",
        entity_id=income_obj.id,
        details={
            "description": income.description,
            "amount": income.amount,
            "category": income.category
        }
    )
    
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

@api_router.get("/daily-financial-summary")
async def get_daily_financial_summary():
    """Get current day financial summary with running cash and bank balances"""
    today = datetime.now().date()
    start_datetime = datetime.combine(today, datetime.min.time())
    end_datetime = datetime.combine(today, datetime.max.time())
    
    # Calculate today's revenue from daily sales
    daily_sales = await db.daily_sales.find({
        "date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    today_revenue = sum(sale.get("total_amount", 0) for sale in daily_sales)
    
    # Calculate today's additional income
    additional_incomes = await db.incomes.find({
        "income_date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    additional_income_total = sum(income.get("amount", 0) for income in additional_incomes)
    total_revenue = today_revenue + additional_income_total
    
    # Calculate today's expenses
    expenses = await db.expenses.find({
        "expense_date": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(1000)
    
    total_expenses = sum(expense.get("amount", 0) for expense in expenses)
    
    # Calculate running cash and bank balances (cumulative)
    # Get all sales and income (cash inflow)
    all_sales = await db.daily_sales.find().to_list(10000)
    all_incomes = await db.incomes.find().to_list(10000)
    
    cash_balance = 0
    bank_balance = 0
    
    # Add revenue to appropriate balances
    for sale in all_sales:
        amount = sale.get("total_amount", 0)
        payment_method = sale.get("payment_method", "Cash")
        if payment_method == "Cash":
            cash_balance += amount
        elif payment_method in ["Card", "Bank Transfer"]:
            bank_balance += amount
    
    # Add additional income to cash balance (assuming cash unless specified)
    for income in all_incomes:
        amount = income.get("amount", 0)
        payment_method = income.get("payment_method", "Cash")
        if payment_method == "Cash":
            cash_balance += amount
        elif payment_method in ["Card", "Bank Transfer"]:
            bank_balance += amount
    
    # Subtract expenses from appropriate balances
    all_expenses = await db.expenses.find().to_list(10000)
    for expense in all_expenses:
        amount = expense.get("amount", 0)
        payment_method = expense.get("payment_method", "Cash")
        if payment_method == "Cash":
            cash_balance -= amount
        elif payment_method in ["Card", "Bank Transfer"]:
            bank_balance -= amount
    
    return {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "cash_balance": cash_balance,
        "bank_balance": bank_balance,
        "date": today
    }

@api_router.get("/financial-reports/daily")
async def get_daily_financial_report(
    date: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate detailed daily financial report with Excel download"""
    try:
        # Parse the date or use today
        if date:
            target_date = datetime.strptime(date, '%Y-%m-%d').date()
        else:
            target_date = datetime.utcnow().date()
        
        # Date range for the day
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        # Get all income entries for the day
        incomes = await db.incomes.find({
            "income_date": {"$gte": start_datetime, "$lte": end_datetime}
        }).to_list(1000)
        
        # Get all expenses for the day
        expenses = await db.expenses.find({
            "expense_date": {"$gte": start_datetime, "$lte": end_datetime}
        }).to_list(1000)
        
        # Get all bookings checked in on this day
        daily_bookings = await db.bookings.find({
            "check_in_date": {"$gte": start_datetime, "$lte": end_datetime},
            "status": {"$in": ["Checked In", "Completed"]}
        }).to_list(1000)
        
        # Calculate balances
        total_cash_income = sum(income.get("amount", 0) for income in incomes if income.get("payment_method") == "Cash")
        total_bank_income = sum(income.get("amount", 0) for income in incomes if income.get("payment_method") in ["Card", "Bank Transfer"])
        
        total_cash_expenses = sum(expense.get("amount", 0) for expense in expenses if expense.get("payment_method") == "Cash")
        total_bank_expenses = sum(expense.get("amount", 0) for expense in expenses if expense.get("payment_method") in ["Card", "Bank Transfer"])
        
        # Room revenue from bookings
        room_revenue_cash = sum(booking.get("booking_amount", 0) for booking in daily_bookings if booking.get("payment_method", "Cash") == "Cash")
        room_revenue_bank = sum(booking.get("booking_amount", 0) for booking in daily_bookings if booking.get("payment_method", "Cash") in ["Card", "Bank Transfer"])
        
        # Prepare detailed data for Excel
        income_details = []
        for income in incomes:
            income_details.append({
                "Date": income.get("income_date", "").strftime("%Y-%m-%d %H:%M") if income.get("income_date") else "",
                "Guest Name": income.get("guest_name", "N/A"),
                "Category": income.get("category", "General"),
                "Description": income.get("description", ""),
                "Amount (LKR)": income.get("amount", 0),
                "Payment Method": income.get("payment_method", "Cash"),
                "Channel": "Direct",  # Income entries are typically direct
                "Added By": income.get("added_by", "N/A")
            })
        
        # Add booking revenue to income details
        for booking in daily_bookings:
            income_details.append({
                "Date": booking.get("check_in_date", "").strftime("%Y-%m-%d %H:%M") if booking.get("check_in_date") else "",
                "Guest Name": booking.get("guest_name", "N/A"),
                "Category": "Room Revenue",
                "Description": f"Room {booking.get('room_number', 'N/A')} - {booking.get('stay_type', 'N/A')}",
                "Amount (LKR)": booking.get("booking_amount", 0),
                "Payment Method": booking.get("payment_method", "Cash"),
                "Channel": booking.get("booking_channel_name", "Direct"),
                "Added By": "System (Check-in)"
            })
        
        expense_details = []
        for expense in expenses:
            expense_details.append({
                "Date": expense.get("expense_date", "").strftime("%Y-%m-%d %H:%M") if expense.get("expense_date") else "",
                "Category": expense.get("category", "General"),
                "Description": expense.get("description", ""),
                "Amount (LKR)": expense.get("amount", 0),
                "Payment Method": expense.get("payment_method", "Cash"),
                "Added By": expense.get("added_by", "N/A")
            })
        
        # Calculate running balances
        cash_balance = (total_cash_income + room_revenue_cash) - total_cash_expenses
        bank_balance = (total_bank_income + room_revenue_bank) - total_bank_expenses
        
        # Summary data
        summary_data = [{
            "Report Type": "Daily Financial Report",
            "Date": target_date.strftime("%Y-%m-%d"),
            "": "",
            "INCOME SUMMARY": "",
            "Cash Income (LKR)": total_cash_income + room_revenue_cash,
            "Bank Income (LKR)": total_bank_income + room_revenue_bank,
            "Total Income (LKR)": total_cash_income + total_bank_income + room_revenue_cash + room_revenue_bank,
            " ": "",
            "EXPENSE SUMMARY": "",
            "Cash Expenses (LKR)": total_cash_expenses,
            "Bank Expenses (LKR)": total_bank_expenses,
            "Total Expenses (LKR)": total_cash_expenses + total_bank_expenses,
            "  ": "",
            "BALANCE SUMMARY": "",
            "Net Cash Balance (LKR)": cash_balance,
            "Net Bank Balance (LKR)": bank_balance,
            "Total Net Balance (LKR)": cash_balance + bank_balance
        }]
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "summary": summary_data[0],
            "income_details": income_details,
            "expense_details": expense_details,
            "cash_balance": cash_balance,
            "bank_balance": bank_balance,
            "total_balance": cash_balance + bank_balance,
            "total_income": total_cash_income + total_bank_income + room_revenue_cash + room_revenue_bank,
            "total_expenses": total_cash_expenses + total_bank_expenses
        }
        
    except Exception as e:
        print(f"Daily report error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate daily report: {str(e)}")

@api_router.get("/financial-reports/monthly")
async def get_monthly_financial_report(
    year: int = None,
    month: int = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate detailed monthly financial report with Excel download"""
    try:
        # Use current month if not specified
        if year is None or month is None:
            today = datetime.utcnow().date()
            year = today.year
            month = today.month
        
        # First and last day of the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(seconds=1)
        
        # Get all income entries for the month
        incomes = await db.incomes.find({
            "income_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(10000)
        
        # Get all expenses for the month
        expenses = await db.expenses.find({
            "expense_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(10000)
        
        # Get all bookings checked in during the month
        monthly_bookings = await db.bookings.find({
            "check_in_date": {"$gte": start_date, "$lte": end_date},
            "status": {"$in": ["Checked In", "Completed"]}
        }).to_list(10000)
        
        # Calculate balances
        total_cash_income = sum(income.get("amount", 0) for income in incomes if income.get("payment_method") == "Cash")
        total_bank_income = sum(income.get("amount", 0) for income in incomes if income.get("payment_method") in ["Card", "Bank Transfer"])
        
        total_cash_expenses = sum(expense.get("amount", 0) for expense in expenses if expense.get("payment_method") == "Cash")
        total_bank_expenses = sum(expense.get("amount", 0) for expense in expenses if expense.get("payment_method") in ["Card", "Bank Transfer"])
        
        # Room revenue from bookings
        room_revenue_cash = sum(booking.get("booking_amount", 0) for booking in monthly_bookings if booking.get("payment_method", "Cash") == "Cash")
        room_revenue_bank = sum(booking.get("booking_amount", 0) for booking in monthly_bookings if booking.get("payment_method", "Cash") in ["Card", "Bank Transfer"])
        
        # Prepare detailed data for Excel
        income_details = []
        for income in incomes:
            income_details.append({
                "Date": income.get("income_date", "").strftime("%Y-%m-%d %H:%M") if income.get("income_date") else "",
                "Guest Name": income.get("guest_name", "N/A"),
                "Category": income.get("category", "General"),
                "Description": income.get("description", ""),
                "Amount (LKR)": income.get("amount", 0),
                "Payment Method": income.get("payment_method", "Cash"),
                "Channel": "Direct",  # Income entries are typically direct
                "Added By": income.get("added_by", "N/A")
            })
        
        # Add booking revenue to income details
        for booking in monthly_bookings:
            income_details.append({
                "Date": booking.get("check_in_date", "").strftime("%Y-%m-%d %H:%M") if booking.get("check_in_date") else "",
                "Guest Name": booking.get("guest_name", "N/A"),
                "Category": "Room Revenue",
                "Description": f"Room {booking.get('room_number', 'N/A')} - {booking.get('stay_type', 'N/A')}",
                "Amount (LKR)": booking.get("booking_amount", 0),
                "Payment Method": booking.get("payment_method", "Cash"),
                "Channel": booking.get("booking_channel_name", "Direct"),
                "Added By": "System (Check-in)"
            })
        
        expense_details = []
        for expense in expenses:
            expense_details.append({
                "Date": expense.get("expense_date", "").strftime("%Y-%m-%d %H:%M") if expense.get("expense_date") else "",
                "Category": expense.get("category", "General"),
                "Description": expense.get("description", ""),
                "Amount (LKR)": expense.get("amount", 0),
                "Payment Method": expense.get("payment_method", "Cash"),
                "Added By": expense.get("added_by", "N/A")
            })
        
        # Calculate running balances
        cash_balance = (total_cash_income + room_revenue_cash) - total_cash_expenses
        bank_balance = (total_bank_income + room_revenue_bank) - total_bank_expenses
        
        # Summary data
        month_names = ["", "January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"]
        
        summary_data = [{
            "Report Type": "Monthly Financial Report",
            "Month": f"{month_names[month]} {year}",
            "": "",
            "INCOME SUMMARY": "",
            "Cash Income (LKR)": total_cash_income + room_revenue_cash,
            "Bank Income (LKR)": total_bank_income + room_revenue_bank,
            "Total Income (LKR)": total_cash_income + total_bank_income + room_revenue_cash + room_revenue_bank,
            " ": "",
            "EXPENSE SUMMARY": "",
            "Cash Expenses (LKR)": total_cash_expenses,
            "Bank Expenses (LKR)": total_bank_expenses,
            "Total Expenses (LKR)": total_cash_expenses + total_bank_expenses,
            "  ": "",
            "BALANCE SUMMARY": "",
            "Net Cash Balance (LKR)": cash_balance,
            "Net Bank Balance (LKR)": bank_balance,
            "Total Net Balance (LKR)": cash_balance + bank_balance
        }]
        
        return {
            "month": f"{month_names[month]} {year}",
            "summary": summary_data[0],
            "income_details": income_details,
            "expense_details": expense_details,
            "cash_balance": cash_balance,
            "bank_balance": bank_balance,
            "total_balance": cash_balance + bank_balance,
            "total_income": total_cash_income + total_bank_income + room_revenue_cash + room_revenue_bank,
            "total_expenses": total_cash_expenses + total_bank_expenses
        }
        
    except Exception as e:
        print(f"Monthly report error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate monthly report: {str(e)}")

# Restaurant Management Routes

# Menu Categories
@api_router.get("/restaurant/categories")
async def get_menu_categories(current_user: UserResponse = Depends(get_current_user)):
    """Get all menu categories"""
    categories = await db.menu_categories.find({"is_active": True}).sort("display_order", 1).to_list(100)
    return [MenuCategory(**category) for category in categories]

@api_router.post("/restaurant/categories")
async def create_menu_category(
    category: MenuCategoryCreate, 
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new menu category"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied. Only Admin or Restaurant Manager can manage categories.")
    
    # Check if category name already exists
    existing = await db.menu_categories.find_one({"name": category.name, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    new_category = MenuCategory(**category.dict())
    await db.menu_categories.insert_one(new_category.dict())
    
    return new_category

@api_router.put("/restaurant/categories/{category_id}")
async def update_menu_category(
    category_id: str,
    category: MenuCategoryCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a menu category"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.menu_categories.update_one(
        {"id": category_id},
        {"$set": category.dict()}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category updated successfully"}

@api_router.delete("/restaurant/categories/{category_id}")
async def delete_menu_category(
    category_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a menu category"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    # Check if category has menu items
    items = await db.menu_items.find({"category_id": category_id, "is_available": True}).to_list(1)
    if items:
        raise HTTPException(status_code=400, detail="Cannot delete category with active menu items")
    
    # Check if category items are in active orders
    active_orders = await db.restaurant_orders.find({
        "payment_status": "Pending",
        "items.menu_item_id": {"$in": [item["id"] for item in items]}
    }).to_list(1)
    if active_orders:
        raise HTTPException(status_code=400, detail="Cannot delete category with items in active orders")
    
    result = await db.menu_categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted successfully"}

# Menu Items
@api_router.get("/restaurant/menu-items")
async def get_menu_items(category_id: Optional[str] = None, current_user: UserResponse = Depends(get_current_user)):
    """Get all menu items, optionally filtered by category"""
    query = {"is_available": True}
    if category_id:
        query["category_id"] = category_id
    
    items = await db.menu_items.find(query).to_list(1000)
    return [MenuItem(**item) for item in items]

@api_router.post("/restaurant/menu-items")
async def create_menu_item(
    item: MenuItemCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new menu item"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    # Verify category exists
    category = await db.menu_categories.find_one({"id": item.category_id, "is_active": True})
    if not category:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    new_item = MenuItem(**item.dict())
    await db.menu_items.insert_one(new_item.dict())
    
    return new_item

@api_router.put("/restaurant/menu-items/{item_id}")
async def update_menu_item(
    item_id: str,
    item: MenuItemCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a menu item"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.menu_items.update_one(
        {"id": item_id},
        {"$set": item.dict()}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return {"message": "Menu item updated successfully"}

@api_router.delete("/restaurant/menu-items/{item_id}")
async def delete_menu_item(
    item_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a menu item"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    # Check if item is in active orders
    active_orders = await db.restaurant_orders.find({
        "payment_status": "Pending",
        "items.menu_item_id": item_id
    }).to_list(1)
    if active_orders:
        raise HTTPException(status_code=400, detail="Cannot delete item that is in active orders")
    
    result = await db.menu_items.update_one(
        {"id": item_id},
        {"$set": {"is_available": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return {"message": "Menu item deleted successfully"}

# Restaurant Tables
@api_router.get("/restaurant/tables")
async def get_restaurant_tables(current_user: UserResponse = Depends(get_current_user)):
    """Get all restaurant tables"""
    tables = await db.restaurant_tables.find({"is_active": True}).sort("table_number", 1).to_list(1000)
    return [RestaurantTable(**table) for table in tables]

@api_router.post("/restaurant/tables")
async def create_restaurant_table(
    table: RestaurantTableCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new restaurant table"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    # Check if table number already exists
    existing = await db.restaurant_tables.find_one({"table_number": table.table_number, "is_active": True})
    if existing:
        raise HTTPException(status_code=400, detail="Table number already exists")
    
    new_table = RestaurantTable(**table.dict())
    await db.restaurant_tables.insert_one(new_table.dict())
    
    return new_table

@api_router.put("/restaurant/tables/{table_id}")
async def update_restaurant_table(
    table_id: str,
    table: RestaurantTableCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a restaurant table"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.restaurant_tables.update_one(
        {"id": table_id},
        {"$set": table.dict()}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Table not found")
    
    return {"message": "Table updated successfully"}

@api_router.delete("/restaurant/tables/{table_id}")
async def delete_restaurant_table(
    table_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a restaurant table"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.restaurant_tables.update_one(
        {"id": table_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Table not found")
    
    return {"message": "Table deleted successfully"}

# Restaurant Staff
@api_router.get("/restaurant/staff")
async def get_restaurant_staff(current_user: UserResponse = Depends(get_current_user)):
    """Get all restaurant staff"""
    staff = await db.restaurant_staff.find({"is_active": True}).sort("name", 1).to_list(1000)
    return [RestaurantStaff(**member) for member in staff]

@api_router.post("/restaurant/staff")
async def create_restaurant_staff(
    staff: RestaurantStaffCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new restaurant staff member"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    new_staff = RestaurantStaff(**staff.dict())
    await db.restaurant_staff.insert_one(new_staff.dict())
    
    return new_staff

@api_router.put("/restaurant/staff/{staff_id}")
async def update_restaurant_staff(
    staff_id: str,
    staff: RestaurantStaffCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update a restaurant staff member"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.restaurant_staff.update_one(
        {"id": staff_id},
        {"$set": staff.dict()}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return {"message": "Staff member updated successfully"}

@api_router.delete("/restaurant/staff/{staff_id}")
async def delete_restaurant_staff(
    staff_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a restaurant staff member"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    result = await db.restaurant_staff.update_one(
        {"id": staff_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    return {"message": "Staff member deleted successfully"}

# Restaurant Orders
@api_router.get("/restaurant/orders")
async def get_restaurant_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get restaurant orders with optional filtering"""
    query = {}
    if status:
        query["order_status"] = status
    if order_type:
        query["order_type"] = order_type
    
    orders = await db.restaurant_orders.find(query).sort("order_date", -1).to_list(1000)
    return [RestaurantOrder(**order) for order in orders]

@api_router.post("/restaurant/orders")
async def create_restaurant_order(
    order: RestaurantOrderCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new restaurant order"""
    # Generate order number
    order_count = await db.restaurant_orders.count_documents({})
    order_number = f"R{str(order_count + 1).zfill(4)}"
    
    # Get hotel settings for tax calculation
    settings = await db.settings.find_one({})
    if not settings:
        tax_rate = 0.0
    else:
        tax_rate = settings.get("tax_rate", 0.0)
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order.items)
    tax_amount = subtotal * (tax_rate / 100)  # Tax from hotel settings
    service_charge = subtotal * (order.service_charge_rate / 100)  # Configurable service charge rate
    total_amount = subtotal + tax_amount + service_charge
    
    # Get table/staff details
    table_number = None
    waiter_name = ""
    
    if order.table_id:
        table = await db.restaurant_tables.find_one({"id": order.table_id})
        if table:
            table_number = table["table_number"]
        
        # Update table status to Occupied
        await db.restaurant_tables.update_one(
            {"id": order.table_id},
            {"$set": {"status": "Occupied"}}
        )
    
    if order.waiter_id:
        waiter = await db.restaurant_staff.find_one({"id": order.waiter_id})
        if waiter:
            waiter_name = waiter["name"]
    
    # Create order
    new_order = RestaurantOrder(
        order_number=order_number,
        order_type=order.order_type,
        table_id=order.table_id,
        table_number=table_number,
        room_number=order.room_number,
        customer_name=order.customer_name,
        items=order.items,
        subtotal=subtotal,
        tax_amount=tax_amount,
        service_charge=service_charge,
        total_amount=total_amount,
        payment_method="Pending",  # Will be set during payment
        waiter_id=order.waiter_id,
        waiter_name=waiter_name,
        notes=order.notes,
        created_by=current_user.username
    )
    
    await db.restaurant_orders.insert_one(new_order.dict())
    
    # For room service orders, automatically add to customer's restaurant charges
    if order.order_type == "room_service" and order.room_number:
        customer = await db.customers.find_one({"current_room": order.room_number, "is_checked_out": False})
        if customer:
            current_charges = customer.get("restaurant_charges", 0.0)
            new_charges = current_charges + total_amount
            await db.customers.update_one(
                {"id": customer["id"]},
                {"$set": {"restaurant_charges": new_charges}}
            )
    
    return new_order

@api_router.put("/restaurant/orders/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update order status"""
    valid_statuses = ["Pending", "Preparing", "Ready", "Served", "Cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.restaurant_orders.update_one(
        {"id": order_id},
        {"$set": {"order_status": status}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": f"Order status updated to {status}"}

@api_router.post("/restaurant/orders/{order_id}/pay")
async def pay_restaurant_order(
    order_id: str,
    payment_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Process payment for restaurant order"""
    if current_user.role not in ["Admin", "Restaurant Manager"]:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    order = await db.restaurant_orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["payment_status"] != "Pending":
        raise HTTPException(status_code=400, detail="Order already paid")
    
    payment_method = payment_data.get("payment_method", "Cash")
    add_to_room_bill = payment_data.get("add_to_room_bill", False)
    
    # Update order payment status
    await db.restaurant_orders.update_one(
        {"id": order_id},
        {"$set": {
            "payment_status": "Paid",
            "payment_method": payment_method,
            "order_status": "Completed"
        }}
    )
    
    # Handle room service billing
    if order["order_type"] == "room_service" and add_to_room_bill:
        # Add to customer's room charges
        customer = await db.customers.find_one({"current_room": order["room_number"]})
        if customer:
            current_charges = customer.get("restaurant_charges", 0.0)
            new_charges = current_charges + order["total_amount"]
            await db.customers.update_one(
                {"current_room": order["room_number"]},
                {"$set": {"restaurant_charges": new_charges}}
            )
        
        # Log activity
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "restaurant_bill_added",
            "description": f"Added restaurant bill LKR {order['total_amount']:.2f} to Room {order['room_number']}",
            "user_name": current_user.username,
            "user_id": current_user.username,
            "entity_type": "restaurant_order",
            "entity_id": order_id,
            "details": {
                "order_number": order["order_number"],
                "room_number": order["room_number"],
                "amount": order["total_amount"],
                "customer_name": order["customer_name"]
            },
            "timestamp": datetime.utcnow()
        })
    else:
        # Process immediate payment - add to daily sales
        await db.daily_sales.insert_one({
            "id": str(uuid.uuid4()),
            "sale_date": datetime.utcnow().date(),
            "description": f"Restaurant Order {order['order_number']}",
            "amount": order["total_amount"],
            "category": "Restaurant",
            "payment_method": payment_method,
            "guest_name": order["customer_name"],
            "created_by": current_user.username,
            "created_at": datetime.utcnow()
        })
        
        # Add to income records
        await db.incomes.insert_one({
            "id": str(uuid.uuid4()),
            "description": f"Restaurant Order {order['order_number']}",
            "amount": order["total_amount"],
            "category": "Restaurant",
            "payment_method": payment_method,
            "income_date": datetime.utcnow().date(),
            "guest_name": order["customer_name"],
            "created_by": current_user.username,
            "created_at": datetime.utcnow()
        })
        
        # Log activity
        await db.activity_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "restaurant_payment_processed",
            "description": f"Processed restaurant payment LKR {order['total_amount']:.2f} for Order {order['order_number']}",
            "user_name": current_user.username,
            "user_id": current_user.username,
            "entity_type": "restaurant_order",
            "entity_id": order_id,
            "details": {
                "order_number": order["order_number"],
                "amount": order["total_amount"],
                "payment_method": payment_method,
                "customer_name": order["customer_name"]
            },
            "timestamp": datetime.utcnow()
        })
    
    # Free up table if it was a table order
    if order["table_id"]:
        await db.restaurant_tables.update_one(
            {"id": order["table_id"]},
            {"$set": {"status": "Available"}}
        )
    
    return {"message": "Payment processed successfully"}

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