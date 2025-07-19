import React, { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import axios from "axios";
import * as XLSX from 'xlsx';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Dashboard Component
const Dashboard = () => {
  const [rooms, setRooms] = useState([]);
  const [upcomingBookings, setUpcomingBookings] = useState([]);
  const [checkedInCustomers, setCheckedInCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modal states
  const [showCheckinModal, setShowCheckinModal] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [showNewBookingModal, setShowNewBookingModal] = useState(false);
  const [showEditBookingModal, setShowEditBookingModal] = useState(false);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  
  // Dropdown state for booking actions
  const [openDropdowns, setOpenDropdowns] = useState({});
  
  // Room availability checker state
  const [availabilityData, setAvailabilityData] = useState(null);
  const [availabilityDates, setAvailabilityDates] = useState({
    check_in_date: '',
    check_out_date: ''
  });
  const [checkingAvailability, setCheckingAvailability] = useState(false);
  
  // Form states
  const [checkinData, setCheckinData] = useState({
    advance_amount: 0,
    notes: '',
    payment_method: 'Cash'
  });
  const [checkoutData, setCheckoutData] = useState({
    additional_amount: '',
    discount_amount: '',
    payment_method: 'Cash'
  });
  const [newBookingData, setNewBookingData] = useState({
    guest_name: '',
    guest_email: '',
    guest_phone: '',
    country: '',
    guest_id_passport: '',
    room_number: '',
    check_in_date: '',
    check_out_date: '',
    stay_type: 'Night Stay',
    rate_per_night: '',
    booking_amount: 0,
    additional_notes: ''
  });
  const [editBookingData, setEditBookingData] = useState({
    check_in_date: '',
    check_out_date: '',
    additional_notes: ''
  });

  useEffect(() => {
    initializeData();
    
    // Add click outside handler for dropdowns
    const handleClickOutside = (event) => {
      // Close dropdowns when clicking outside
      if (!event.target.closest('.relative')) {
        closeAllDropdowns();
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  const initializeData = async () => {
    try {
      // Initialize sample data
      await axios.post(`${API}/init-data`);
      
      // Fetch all data
      await Promise.all([
        fetchRooms(),
        fetchUpcomingBookings(),
        fetchCheckedInCustomers()
      ]);
    } catch (error) {
      console.error('Error initializing data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Check room availability function
  const checkRoomAvailability = async () => {
    if (!availabilityDates.check_in_date || !availabilityDates.check_out_date) {
      alert('Please select both check-in and check-out dates');
      return;
    }

    setCheckingAvailability(true);
    try {
      const params = new URLSearchParams({
        check_in_date: availabilityDates.check_in_date,
        check_out_date: availabilityDates.check_out_date
      });
      
      const response = await axios.get(`${API}/rooms/availability/check?${params}`);
      setAvailabilityData(response.data);
      setShowAvailabilityModal(true);
    } catch (error) {
      console.error('Error checking availability:', error);
      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert('Error checking room availability. Please try again.');
      }
    } finally {
      setCheckingAvailability(false);
    }
  };

  // Clear availability data when dates change
  const handleDateChange = (field, value) => {
    setAvailabilityDates({
      ...availabilityDates,
      [field]: value
    });
    // Clear previous results when dates change
    if (availabilityData) {
      setAvailabilityData(null);
    }
  };

  // Handle dropdown toggle for booking actions
  const toggleDropdown = (bookingId) => {
    setOpenDropdowns(prev => ({
      ...prev,
      [bookingId]: !prev[bookingId]
    }));
  };

  const closeAllDropdowns = () => {
    setOpenDropdowns({});
  };

  // Handle booking field changes with total calculation
  const handleBookingFieldChange = (field, value) => {
    const updatedData = { ...newBookingData, [field]: value };
    
    // Calculate total booking amount when rate, dates, or stay type changes
    if (['rate_per_night', 'check_in_date', 'check_out_date', 'stay_type'].includes(field)) {
      const ratePerNight = parseFloat(updatedData.rate_per_night) || 0;
      
      if (updatedData.stay_type === 'Short Time') {
        // For short time, use the rate as-is (single charge)
        updatedData.booking_amount = ratePerNight;
      } else if (updatedData.stay_type === 'Night Stay' && updatedData.check_in_date && updatedData.check_out_date) {
        // For night stay, calculate based on number of nights
        const checkIn = new Date(updatedData.check_in_date);
        const checkOut = new Date(updatedData.check_out_date);
        const nights = Math.max(1, Math.ceil((checkOut - checkIn) / (1000 * 60 * 60 * 24)));
        updatedData.booking_amount = ratePerNight * nights;
      } else {
        // Default to single night if dates not set
        updatedData.booking_amount = ratePerNight;
      }
    }
    
    setNewBookingData(updatedData);
  };

  const fetchRooms = async () => {
    try {
      const response = await axios.get(`${API}/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error('Error fetching rooms:', error);
    }
  };

  const fetchUpcomingBookings = async () => {
    try {
      const response = await axios.get(`${API}/bookings/upcoming`);
      setUpcomingBookings(response.data);
    } catch (error) {
      console.error('Error fetching upcoming bookings:', error);
    }
  };

  const fetchCheckedInCustomers = async () => {
    try {
      const response = await axios.get(`${API}/customers/checked-in`);
      setCheckedInCustomers(response.data);
    } catch (error) {
      console.error('Error fetching checked-in customers:', error);
    }
  };

  const handleCheckout = async (customer) => {
    setSelectedCustomer(customer);
    setCheckoutData({ additional_amount: '', discount_amount: '', payment_method: 'Cash' });
    setShowCheckoutModal(true);
  };

  const confirmCheckout = async () => {
    try {
      await axios.post(`${API}/checkout`, {
        customer_id: selectedCustomer.id,
        additional_amount: parseFloat(checkoutData.additional_amount) || 0,
        discount_amount: parseFloat(checkoutData.discount_amount) || 0,
        payment_method: checkoutData.payment_method
      });
      
      setShowCheckoutModal(false);
      setSelectedCustomer(null);
      
      // Refresh data after checkout
      await Promise.all([
        fetchRooms(),
        fetchCheckedInCustomers()
      ]);
    } catch (error) {
      console.error('Error during checkout:', error);
    }
  };

  const handleCheckin = async (booking) => {
    setSelectedBooking(booking);
    setCheckinData({ advance_amount: 0, notes: '', payment_method: 'Cash' });
    setShowCheckinModal(true);
  };

  const confirmCheckin = async () => {
    try {
      await axios.post(`${API}/checkin`, {
        booking_id: selectedBooking.id,
        advance_amount: checkinData.advance_amount,
        notes: checkinData.notes,
        payment_method: checkinData.payment_method
      });
      
      setShowCheckinModal(false);
      setSelectedBooking(null);
      
      // Refresh all data after check-in
      await Promise.all([
        fetchRooms(),
        fetchUpcomingBookings(),
        fetchCheckedInCustomers()
      ]);
    } catch (error) {
      console.error('Error during check-in:', error);
      alert('Error during check-in. Please ensure the room is available.');
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (window.confirm('Are you sure you want to cancel this booking?')) {
      try {
        await axios.post(`${API}/cancel/${bookingId}`);
        
        // Refresh data after cancellation
        await Promise.all([
          fetchRooms(),
          fetchUpcomingBookings()
        ]);
      } catch (error) {
        console.error('Error cancelling booking:', error);
        alert('Error cancelling booking. Please try again.');
      }
    }
  };

  const calculateTotal = () => {
    if (!selectedCustomer) return 0;
    const roomCharges = selectedCustomer.room_charges || 500;
    const advanceAmount = selectedCustomer.advance_amount || 0;
    const additionalAmount = parseFloat(checkoutData.additional_amount) || 0;
    const discountAmount = parseFloat(checkoutData.discount_amount) || 0;
    return roomCharges + additionalAmount - advanceAmount - discountAmount;
  };

  const handleNewBooking = async () => {
    try {
      // Validate required fields - only name, room, check-in date, and rate per night are required
      const requiredFields = ['guest_name', 'room_number', 'check_in_date'];
      const missingFields = requiredFields.filter(field => !newBookingData[field]);
      
      // For night stay, checkout date is required
      if (newBookingData.stay_type === 'Night Stay' && !newBookingData.check_out_date) {
        missingFields.push('check_out_date');
      }

      // Rate per night is required
      if (!newBookingData.rate_per_night || parseFloat(newBookingData.rate_per_night) <= 0) {
        missingFields.push('rate_per_night');
      }
      
      if (missingFields.length > 0) {
        alert('Please fill in all required fields (Name, Room, Dates, and Rate per Night)');
        return;
      }

      // Prepare booking data - send the calculated booking_amount to backend
      const bookingData = {
        ...newBookingData,
        booking_amount: newBookingData.booking_amount // This is the calculated total
      };

      await axios.post(`${API}/bookings`, bookingData);
      
      setShowNewBookingModal(false);
      setNewBookingData({
        guest_name: '',
        guest_email: '',
        guest_phone: '',
        country: '',
        guest_id_passport: '',
        room_number: '',
        check_in_date: '',
        check_out_date: '',
        stay_type: 'Night Stay',
        rate_per_night: '',
        booking_amount: 0,
        additional_notes: ''
      });
      
      // Refresh data after adding booking
      await Promise.all([
        fetchRooms(),
        fetchUpcomingBookings()
      ]);
      alert('Booking added successfully!');
    } catch (error) {
      console.error('Error creating booking:', error);
      alert('Error creating booking. Please try again.');
    }
  };

  const handleEditBooking = async () => {
    try {
      await axios.put(`${API}/bookings/${selectedBooking.id}`, editBookingData);
      
      setShowEditBookingModal(false);
      setSelectedBooking(null);
      
      // Refresh data after editing booking
      await Promise.all([
        fetchUpcomingBookings(),
        fetchCheckedInCustomers()
      ]);
      alert('Booking updated successfully!');
    } catch (error) {
      console.error('Error updating booking:', error);
      alert('Error updating booking. Please try again.');
    }
  };

  const openEditBookingModal = (booking) => {
    setSelectedBooking(booking);
    setEditBookingData({
      check_in_date: booking.check_in_date,
      check_out_date: booking.check_out_date,
      additional_notes: booking.additional_notes || ''
    });
    setShowEditBookingModal(true);
  };

  const getAvailableRooms = () => {
    // If dates are selected, we should check availability for those specific dates
    // For now, return all rooms except occupied ones
    // TODO: This should check against the room availability API for the selected dates
    return rooms.filter(room => room.status !== 'Occupied');
  };

  // Function to get available rooms for specific dates
  const getAvailableRoomsForDates = async (checkInDate, checkOutDate) => {
    if (!checkInDate || (newBookingData.stay_type === 'Night Stay' && !checkOutDate)) {
      return rooms.filter(room => room.status !== 'Occupied');
    }

    try {
      const params = new URLSearchParams({
        check_in_date: checkInDate,
        check_out_date: checkOutDate || checkInDate
      });
      
      const response = await axios.get(`${API}/rooms/availability/check?${params}`);
      return response.data.rooms || [];
    } catch (error) {
      console.error('Error checking room availability:', error);
      // Fallback to showing all non-occupied rooms
      return rooms.filter(room => room.status !== 'Occupied');
    }
  };

  const getRoomStatusColor = (status) => {
    switch (status) {
      case 'Available':
        return 'bg-green-100 border-green-500';
      case 'Occupied':
        return 'bg-red-100 border-red-500';
      case 'Booked':
        return 'bg-orange-100 border-orange-500';
      case 'Reserved':
        return 'bg-yellow-100 border-yellow-500';
      default:
        return 'bg-gray-100 border-gray-500';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'Available':
        return '🟢';
      case 'Occupied':
        return '🔴';
      case 'Booked':
        return '🟠';
      case 'Reserved':
        return '🟡';
      default:
        return '⚪';
    }
  };

  // Function to get room status including booked status
  const getRoomDisplayStatus = (room) => {
    // If room is already Occupied, return Occupied
    if (room.status === 'Occupied') {
      return 'Occupied';
    }
    
    // Check if room has bookings for today
    const today = new Date().toISOString().split('T')[0];
    const roomBookings = upcomingBookings.filter(booking => 
      booking.room_number === room.room_number &&
      booking.check_in_date === today
    );
    
    // If there are bookings for today and room is available, mark as Booked
    if (roomBookings.length > 0 && room.status === 'Available') {
      return 'Booked';
    }
    
    // Otherwise return the original status
    return room.status;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-gray-600">Overview of hotel operations and current status</p>
        </div>
        <button 
          onClick={() => setShowNewBookingModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 flex items-center space-x-2"
        >
          <span>+</span>
          <span>New Booking</span>
        </button>
      </div>

      {/* Room Status - Quick View */}
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Room Status - Quick View</h3>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {rooms.map((room) => {
            const displayStatus = getRoomDisplayStatus(room);
            return (
              <div
                key={room.id}
                className={`p-4 rounded-lg border-2 ${getRoomStatusColor(displayStatus)} shadow-sm hover:shadow-md transition-shadow`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-lg font-bold text-gray-900">{room.room_number}</h4>
                  <span className="text-lg">{getStatusIcon(displayStatus)}</span>
                </div>
                <p className="text-sm text-gray-600 mb-1">{room.room_type}</p>
                <p className={`text-sm font-medium ${
                  displayStatus === 'Available' ? 'text-green-700' :
                  displayStatus === 'Occupied' ? 'text-red-700' :
                  displayStatus === 'Booked' ? 'text-orange-700' :
                  'text-yellow-700'
                }`}>
                  {displayStatus}
                </p>
                {room.current_guest && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500">Guest: {room.current_guest}</p>
                    {room.check_out_date && (
                      <p className="text-xs text-gray-500">Out: {room.check_out_date}</p>
                    )}
                  </div>
                )}
                {displayStatus === 'Booked' && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-orange-600 font-medium">Check-in today</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Room Availability Checker */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h3 className="text-lg font-semibold mb-4">🔍 Check Room Availability</h3>
        <p className="text-gray-600 mb-4">Select dates to check which rooms are available for booking</p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Check-in Date</label>
            <input
              type="date"
              value={availabilityDates.check_in_date}
              onChange={(e) => handleDateChange('check_in_date', e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Check-out Date</label>
            <input
              type="date"
              value={availabilityDates.check_out_date}
              onChange={(e) => handleDateChange('check_out_date', e.target.value)}
              min={availabilityDates.check_in_date || new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={checkRoomAvailability}
              disabled={checkingAvailability || !availabilityDates.check_in_date || !availabilityDates.check_out_date}
              className={`w-full px-4 py-2 rounded-md font-medium ${
                checkingAvailability || !availabilityDates.check_in_date || !availabilityDates.check_out_date
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {checkingAvailability ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Checking...
                </div>
              ) : (
                'Check Availability'
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Upcoming Bookings */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Upcoming Bookings</h3>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {upcomingBookings.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No upcoming bookings
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Guest Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Room
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-in
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-out
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {upcomingBookings.map((booking) => (
                    <tr key={booking.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{booking.guest_name}</div>
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
                        <div className="text-sm text-gray-900">{booking.guest_phone}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right relative">
                        <button
                          onClick={() => toggleDropdown(booking.id)}
                          className="inline-flex items-center p-2 text-gray-400 bg-white rounded-full hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                          </svg>
                        </button>
                        
                        {openDropdowns[booking.id] && (
                          <div className="absolute right-0 z-10 mt-2 w-48 origin-top-right bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5">
                            <div className="py-1">
                              <button
                                onClick={() => {
                                  handleCheckin(booking);
                                  closeAllDropdowns();
                                }}
                                className="flex w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                              >
                                <svg className="w-4 h-4 mr-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                                </svg>
                                Check In
                              </button>
                              <button
                                onClick={() => {
                                  openEditBookingModal(booking);
                                  closeAllDropdowns();
                                }}
                                className="flex w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                              >
                                <svg className="w-4 h-4 mr-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                                </svg>
                                Edit
                              </button>
                              <button
                                onClick={() => {
                                  handleCancelBooking(booking.id);
                                  closeAllDropdowns();
                                }}
                                className="flex w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                              >
                                <svg className="w-4 h-4 mr-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
                                </svg>
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Checked-in Customers */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Checked-in Customers</h3>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          {checkedInCustomers.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No customers currently checked in
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Room
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-in Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-out Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Action
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Edit Booking
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {checkedInCustomers.map((customer) => (
                    <tr key={customer.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{customer.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{customer.current_room}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{customer.check_in_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{customer.check_out_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{customer.phone}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleCheckout(customer)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
                        >
                          Checkout
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => {
                            // Find the booking for this customer
                            const booking = upcomingBookings.find(b => 
                              b.guest_name === customer.name && 
                              b.room_number === customer.current_room
                            );
                            if (booking) {
                              openEditBookingModal(booking);
                            } else {
                              // Create a mock booking object for checked-in customers
                              const mockBooking = {
                                id: customer.id,
                                guest_name: customer.name,
                                room_number: customer.current_room,
                                check_in_date: customer.check_in_date,
                                check_out_date: customer.check_out_date,
                                additional_notes: customer.notes || ''
                              };
                              openEditBookingModal(mockBooking);
                            }
                          }}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                        >
                          Edit Booking
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Check-in Modal */}
      {showCheckinModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Check In Customer</h3>
            {selectedBooking && (
              <div className="mb-4">
                <p className="text-sm text-gray-600">Guest: {selectedBooking.guest_name}</p>
                <p className="text-sm text-gray-600">Room: {selectedBooking.room_number}</p>
                <p className="text-sm text-gray-600">Phone: {selectedBooking.guest_phone}</p>
              </div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Advance Amount (LKR)
                </label>
                <input
                  type="number"
                  value={checkinData.advance_amount}
                  onChange={(e) => setCheckinData({...checkinData, advance_amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  value={checkinData.payment_method}
                  onChange={(e) => setCheckinData({...checkinData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  value={checkinData.notes}
                  onChange={(e) => setCheckinData({...checkinData, notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Any special notes..."
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCheckinModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmCheckin}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Confirm Check In
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Checkout Modal */}
      {showCheckoutModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Checkout Customer</h3>
            {selectedCustomer && (
              <div className="mb-4">
                <p className="text-sm text-gray-600">Guest: {selectedCustomer.name}</p>
                <p className="text-sm text-gray-600">Room: {selectedCustomer.current_room}</p>
                <p className="text-sm text-gray-600">Phone: {selectedCustomer.phone}</p>
              </div>
            )}
            
            <div className="space-y-4">
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="font-medium text-gray-800 mb-2">Billing Details</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span>Room Charges:</span>
                    <span>LKR {selectedCustomer?.room_charges || 500}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Advance Paid:</span>
                    <span>-LKR {selectedCustomer?.advance_amount || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Additional Charges:</span>
                    <span>LKR {parseFloat(checkoutData.additional_amount) || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Discount:</span>
                    <span>-LKR {parseFloat(checkoutData.discount_amount) || 0}</span>
                  </div>
                  <hr className="my-2" />
                  <div className="flex justify-between font-semibold">
                    <span>Subtotal:</span>
                    <span>LKR {calculateTotal()}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Amount (LKR)
                </label>
                <input
                  type="number"
                  value={checkoutData.additional_amount}
                  onChange={(e) => setCheckoutData({...checkoutData, additional_amount: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Discount Amount (LKR)
                </label>
                <input
                  type="number"
                  value={checkoutData.discount_amount}
                  onChange={(e) => setCheckoutData({...checkoutData, discount_amount: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  value={checkoutData.payment_method}
                  onChange={(e) => setCheckoutData({...checkoutData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>

              {/* Balance Payable - Real-time Display */}
              <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                <div className="flex items-center justify-center">
                  <div className="text-center">
                    <p className="text-sm font-medium text-green-700 mb-1">Balance Payable</p>
                    <p className={`text-3xl font-bold ${
                      calculateTotal() >= 0 ? 'text-green-800' : 'text-red-600'
                    }`}>
                      LKR {Math.abs(calculateTotal()).toFixed(2)}
                    </p>
                    {calculateTotal() < 0 && (
                      <p className="text-xs text-red-600 mt-1">Refund Due to Customer</p>
                    )}
                    {calculateTotal() >= 0 && (
                      <p className="text-xs text-green-600 mt-1">Amount to Collect</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCheckoutModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmCheckout}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Confirm Checkout
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New Booking Modal */}
      {showNewBookingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Create New Booking</h3>
            
            <div className="grid grid-cols-2 gap-6">
              {/* Left Column - Guest Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-800 border-b pb-2">Guest Information</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Guest Name *
                  </label>
                  <input
                    type="text"
                    value={newBookingData.guest_name}
                    onChange={(e) => setNewBookingData({...newBookingData, guest_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter guest name"
                    required
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={newBookingData.guest_email}
                    onChange={(e) => setNewBookingData({...newBookingData, guest_email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter email address (optional)"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone
                  </label>
                  <input
                    type="tel"
                    value={newBookingData.guest_phone}
                    onChange={(e) => setNewBookingData({...newBookingData, guest_phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter phone number (optional)"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ID/Passport Number
                  </label>
                  <input
                    type="text"
                    value={newBookingData.guest_id_passport}
                    onChange={(e) => setNewBookingData({...newBookingData, guest_id_passport: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter ID or passport number"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <input
                    type="text"
                    value={newBookingData.guest_country}
                    onChange={(e) => setNewBookingData({...newBookingData, guest_country: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter country"
                  />
                </div>
              </div>
              
              {/* Right Column - Booking Details */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-800 border-b pb-2">Booking Details</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Room *
                    </label>
                    <select
                      value={newBookingData.room_number}
                      onChange={(e) => handleBookingFieldChange('room_number', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    >
                      <option value="">Select a room</option>
                      {getAvailableRooms().map((room) => (
                        <option key={room.id} value={room.room_number}>
                          {room.room_number}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Rate per Night (LKR) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={newBookingData.rate_per_night}
                      onChange={(e) => handleBookingFieldChange('rate_per_night', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Enter rate per night"
                      required
                    />
                  </div>
                  
                  {/* Show calculated total */}
                  {newBookingData.booking_amount > 0 && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="text-sm font-medium text-blue-800">
                        Total Booking Amount: LKR {newBookingData.booking_amount.toFixed(2)}
                      </div>
                      {newBookingData.stay_type === 'Night Stay' && newBookingData.check_in_date && newBookingData.check_out_date && (
                        <div className="text-xs text-blue-600 mt-1">
                          {Math.max(1, Math.ceil((new Date(newBookingData.check_out_date) - new Date(newBookingData.check_in_date)) / (1000 * 60 * 60 * 24)))} night(s) × LKR {parseFloat(newBookingData.rate_per_night || 0).toFixed(2)}
                        </div>
                      )}
                      {newBookingData.stay_type === 'Short Time' && (
                        <div className="text-xs text-blue-600 mt-1">
                          Short time rate
                        </div>
                      )}
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Stay Type *
                  </label>
                  <select
                    value={newBookingData.stay_type}
                    onChange={(e) => handleBookingFieldChange('stay_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="Night Stay">Night Stay</option>
                    <option value="Short Time">Short Time</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    {newBookingData.stay_type === 'Short Time' 
                      ? 'Customer will checkout on the same day' 
                      : 'Customer will stay overnight'}
                  </p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Check-in Date *
                    </label>
                    <input
                      type="date"
                      value={newBookingData.check_in_date}
                      onChange={(e) => handleBookingFieldChange('check_in_date', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>
                  
                  {newBookingData.stay_type === 'Night Stay' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Check-out Date *
                      </label>
                      <input
                        type="date"
                        value={newBookingData.check_out_date}
                        onChange={(e) => handleBookingFieldChange('check_out_date', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required={newBookingData.stay_type === 'Night Stay'}
                      />
                    </div>
                  )}
                  
                  {newBookingData.stay_type === 'Short Time' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Check-out Date
                      </label>
                      <input
                        type="text"
                        value="Same day checkout"
                        disabled
                        className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500"
                      />
                    </div>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Additional Notes
                  </label>
                  <textarea
                    value={newBookingData.additional_notes}
                    onChange={(e) => setNewBookingData({...newBookingData, additional_notes: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows="4"
                    placeholder="Any special requests or notes..."
                  />
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-8">
              <button
                onClick={() => setShowNewBookingModal(false)}
                className="px-6 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleNewBooking}
                disabled={
                  !newBookingData.guest_name || 
                  !newBookingData.room_number || 
                  !newBookingData.check_in_date ||
                  !newBookingData.booking_amount ||
                  parseFloat(newBookingData.booking_amount) <= 0 ||
                  (newBookingData.stay_type === 'Night Stay' && !newBookingData.check_out_date)
                }
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                Create Booking
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Booking Modal */}
      {showEditBookingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Edit Booking</h3>
            {selectedBooking && (
              <div className="mb-4">
                <p className="text-sm text-gray-600">Guest: {selectedBooking.guest_name}</p>
                <p className="text-sm text-gray-600">Room: {selectedBooking.room_number}</p>
              </div>
            )}
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Check-in Date
                  </label>
                  <input
                    type="date"
                    value={editBookingData.check_in_date}
                    onChange={(e) => setEditBookingData({...editBookingData, check_in_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Check-out Date
                  </label>
                  <input
                    type="date"
                    value={editBookingData.check_out_date}
                    onChange={(e) => setEditBookingData({...editBookingData, check_out_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Additional Notes
                </label>
                <textarea
                  value={editBookingData.additional_notes}
                  onChange={(e) => setEditBookingData({...editBookingData, additional_notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows="3"
                  placeholder="Any special notes or changes..."
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowEditBookingModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleEditBooking}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Update Booking
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Room Availability Modal */}
      {showAvailabilityModal && availabilityData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Room Availability Results</h3>
              <button
                onClick={() => setShowAvailabilityModal(false)}
                className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ×
              </button>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <h4 className="font-semibold text-blue-800 mb-2">
                Availability for {availabilityData.check_in_date} to {availabilityData.check_out_date}
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-blue-600 font-medium">Stay Duration:</span>
                  <span className="text-blue-800 ml-1">{availabilityData.stay_duration} night{availabilityData.stay_duration !== 1 ? 's' : ''}</span>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Total Rooms:</span>
                  <span className="text-blue-800 ml-1">{availabilityData.total_rooms}</span>
                </div>
                <div>
                  <span className="text-green-600 font-medium">Available Rooms:</span>
                  <span className="text-green-800 ml-1">{availabilityData.available_rooms}</span>
                </div>
              </div>
            </div>

            {availabilityData.rooms.length > 0 ? (
              <div>
                <h5 className="font-medium text-gray-900 mb-4">Available Rooms:</h5>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {availabilityData.rooms.map(room => (
                    <div key={room.id} className="border border-green-300 bg-green-50 p-4 rounded-lg">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h6 className="font-semibold text-green-800 text-lg">{room.room_number}</h6>
                          <p className="text-sm text-green-600">{room.room_type}</p>
                        </div>
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full font-medium">
                          Available
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          setNewBookingData({
                            ...newBookingData,
                            room_number: room.room_number,
                            check_in_date: availabilityData.check_in_date,
                            check_out_date: availabilityData.check_out_date,
                            booking_amount: room.price_per_night * availabilityData.stay_duration
                          });
                          setShowAvailabilityModal(false);
                          setShowNewBookingModal(true);
                        }}
                        className="w-full mt-3 px-4 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors font-medium"
                      >
                        Book This Room
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h5 className="font-medium text-red-800 mb-2">No Rooms Available</h5>
                <p className="text-red-600 text-sm">
                  Sorry, no rooms are available for the selected dates. Please try different dates or contact us for assistance.
                </p>
              </div>
            )}
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowAvailabilityModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Reports Component
const Reports = () => {
  const [dailyReports, setDailyReports] = useState([]);
  const [monthlyReports, setMonthlyReports] = useState([]);
  const [monthComparison, setMonthComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedView, setSelectedView] = useState('daily'); // daily, monthly, comparison

  useEffect(() => {
    fetchReportsData();
  }, []);

  const fetchReportsData = async () => {
    try {
      const [dailyResponse, monthlyResponse, comparisonResponse] = await Promise.all([
        axios.get(`${API}/reports/daily`),
        axios.get(`${API}/reports/monthly`),
        axios.get(`${API}/reports/comparison`)
      ]);
      
      setDailyReports(dailyResponse.data);
      setMonthlyReports(monthlyResponse.data);
      setMonthComparison(comparisonResponse.data);
    } catch (error) {
      console.error('Error fetching reports data:', error);
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

  const getChangeIndicator = (change) => {
    if (change > 0) {
      return <span className="text-green-600 font-medium">+{change}%</span>;
    } else if (change < 0) {
      return <span className="text-red-600 font-medium">{change}%</span>;
    } else {
      return <span className="text-gray-600 font-medium">0%</span>;
    }
  };

  const getRecentDailyData = () => {
    return dailyReports.slice(-7); // Last 7 days
  };

  const getCurrentMonthData = () => {
    const currentMonth = new Date().getMonth() + 1;
    return monthlyReports.find(m => m.month === currentMonth) || {};
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Reports & Analytics</h2>
          <p className="text-gray-600">Financial performance and business insights</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setSelectedView('daily')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              selectedView === 'daily' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Daily View
          </button>
          <button
            onClick={() => setSelectedView('monthly')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              selectedView === 'monthly' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Monthly View
          </button>
          <button
            onClick={() => setSelectedView('comparison')}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              selectedView === 'comparison' 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Comparison
          </button>
        </div>
      </div>

      {/* Month-to-Month Comparison */}
      {monthComparison && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Last Month vs Current Month</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Revenue</h4>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(monthComparison.current_month.revenue)}
                  </p>
                  <p className="text-sm text-gray-500">
                    Last: {formatCurrency(monthComparison.last_month.revenue)}
                  </p>
                </div>
                <div className="text-right">
                  {getChangeIndicator(monthComparison.changes.revenue_change)}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Expenses</h4>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatCurrency(monthComparison.current_month.expenses)}
                  </p>
                  <p className="text-sm text-gray-500">
                    Last: {formatCurrency(monthComparison.last_month.expenses)}
                  </p>
                </div>
                <div className="text-right">
                  {getChangeIndicator(monthComparison.changes.expenses_change)}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Net Profit</h4>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-2xl font-bold ${
                    monthComparison.current_month.profit >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {formatCurrency(monthComparison.current_month.profit)}
                  </p>
                  <p className="text-sm text-gray-500">
                    Last: {formatCurrency(monthComparison.last_month.profit)}
                  </p>
                </div>
                <div className="text-right">
                  {getChangeIndicator(monthComparison.changes.profit_change)}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h4 className="text-sm font-medium text-gray-500 mb-2">Bookings</h4>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-2xl font-bold text-gray-900">
                    {monthComparison.current_month.bookings_count}
                  </p>
                  <p className="text-sm text-gray-500">
                    Last: {monthComparison.last_month.bookings_count}
                  </p>
                </div>
                <div className="text-right">
                  {getChangeIndicator(monthComparison.changes.bookings_change)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Daily Reports View */}
      {selectedView === 'daily' && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Income & Expenses (Last 7 Days)</h3>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Revenue
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expenses
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Net Profit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bookings
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expense Items
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {getRecentDailyData().map((day) => (
                    <tr key={day.date} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {new Date(day.date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-green-600">
                          {formatCurrency(day.revenue)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-red-600">
                          {formatCurrency(day.expenses)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-bold ${
                          day.profit >= 0 ? 'text-blue-600' : 'text-orange-600'
                        }`}>
                          {formatCurrency(day.profit)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{day.bookings_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{day.expenses_count}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Monthly Reports View */}
      {selectedView === 'monthly' && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Monthly Performance Data</h3>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Month
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Revenue
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Expenses
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Net Profit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Bookings
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Occupancy Rate
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {monthlyReports.map((month) => (
                    <tr key={month.month} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{month.month_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-green-600">
                          {formatCurrency(month.revenue)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-red-600">
                          {formatCurrency(month.expenses)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-bold ${
                          month.profit >= 0 ? 'text-blue-600' : 'text-orange-600'
                        }`}>
                          {formatCurrency(month.profit)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{month.bookings_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{month.occupancy_rate}%</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Comparison View */}
      {selectedView === 'comparison' && monthComparison && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Month Comparison</h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Last Month */}
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Last Month Performance</h4>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Revenue:</span>
                  <span className="font-bold text-green-600">
                    {formatCurrency(monthComparison.last_month.revenue)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Expenses:</span>
                  <span className="font-bold text-red-600">
                    {formatCurrency(monthComparison.last_month.expenses)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Net Profit:</span>
                  <span className={`font-bold ${
                    monthComparison.last_month.profit >= 0 ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    {formatCurrency(monthComparison.last_month.profit)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Bookings:</span>
                  <span className="font-bold text-gray-900">
                    {monthComparison.last_month.bookings_count}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Expense Items:</span>
                  <span className="font-bold text-gray-900">
                    {monthComparison.last_month.expenses_count}
                  </span>
                </div>
              </div>
            </div>

            {/* Current Month */}
            <div className="bg-blue-50 rounded-lg p-6">
              <h4 className="text-lg font-medium text-gray-900 mb-4">Current Month Performance</h4>
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Revenue:</span>
                  <span className="font-bold text-green-600">
                    {formatCurrency(monthComparison.current_month.revenue)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Expenses:</span>
                  <span className="font-bold text-red-600">
                    {formatCurrency(monthComparison.current_month.expenses)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Net Profit:</span>
                  <span className={`font-bold ${
                    monthComparison.current_month.profit >= 0 ? 'text-blue-600' : 'text-orange-600'
                  }`}>
                    {formatCurrency(monthComparison.current_month.profit)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Total Bookings:</span>
                  <span className="font-bold text-gray-900">
                    {monthComparison.current_month.bookings_count}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Expense Items:</span>
                  <span className="font-bold text-gray-900">
                    {monthComparison.current_month.expenses_count}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Expenses Component
const Expenses = () => {
  const [expenses, setExpenses] = useState([]);
  const [incomes, setIncomes] = useState([]);
  const [dailySales, setDailySales] = useState([]);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [dailyFinancialSummary, setDailyFinancialSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddExpenseModal, setShowAddExpenseModal] = useState(false);
  const [showAddIncomeModal, setShowAddIncomeModal] = useState(false);
  
  // Pagination state
  const [roomBookingsPage, setRoomBookingsPage] = useState(1);
  const [additionalIncomePage, setAdditionalIncomePage] = useState(1);
  const [expensePage, setExpensePage] = useState(1);
  const itemsPerPage = 10;
  
  const [expenseData, setExpenseData] = useState({
    description: '',
    amount: 0,
    category: '',
    expense_date: ''
  });
  const [incomeData, setIncomeData] = useState({
    description: '',
    amount: 0,
    category: '',
    income_date: ''
  });

  const expenseCategories = [
    'Utilities',
    'Maintenance', 
    'Staff',
    'Food',
    'Marketing',
    'Other'
  ];

  const incomeCategories = [
    'Restaurant',
    'Laundry',
    'Spa Services',
    'Events',
    'Conference Room',
    'Parking',
    'Internet Services',
    'Other Services'
  ];

  useEffect(() => {
    fetchExpenses();
    fetchIncomes();
    fetchDailySales();
    fetchFinancialSummary();
    fetchDailyFinancialSummary();
  }, []);

  const fetchExpenses = async () => {
    try {
      const response = await axios.get(`${API}/expenses`);
      setExpenses(response.data);
    } catch (error) {
      console.error('Error fetching expenses:', error);
    }
  };

  const fetchIncomes = async () => {
    try {
      const response = await axios.get(`${API}/incomes`);
      setIncomes(response.data);
    } catch (error) {
      console.error('Error fetching incomes:', error);
    }
  };

  const fetchDailySales = async () => {
    try {
      const response = await axios.get(`${API}/daily-sales`);
      setDailySales(response.data);
    } catch (error) {
      console.error('Error fetching daily sales:', error);
    }
  };

  const fetchFinancialSummary = async () => {
    try {
      const response = await axios.get(`${API}/financial-summary`);
      setFinancialSummary(response.data);
    } catch (error) {
      console.error('Error fetching financial summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDailyFinancialSummary = async () => {
    try {
      const response = await axios.get(`${API}/daily-financial-summary`);
      setDailyFinancialSummary(response.data);
    } catch (error) {
      console.error('Error fetching daily financial summary:', error);
    }
  };

  const handleAddExpense = async () => {
    try {
      if (!expenseData.description || !expenseData.amount || !expenseData.category || !expenseData.expense_date) {
        alert('Please fill in all required fields');
        return;
      }

      await axios.post(`${API}/expenses`, expenseData);
      
      setShowAddExpenseModal(false);
      setExpenseData({
        description: '',
        amount: 0,
        category: '',
        expense_date: ''
      });
      
      // Refresh data after adding expense
      await fetchExpenses();
      await fetchFinancialSummary();
      await fetchDailyFinancialSummary();
      alert('Expense added successfully!');
    } catch (error) {
      console.error('Error adding expense:', error);
      alert('Error adding expense. Please try again.');
    }
  };

  // Pagination helper functions
  const getPaginatedData = (data, currentPage) => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return data.slice(startIndex, endIndex);
  };

  const getTotalPages = (data) => {
    return Math.ceil(data.length / itemsPerPage);
  };

  const renderPagination = (data, currentPage, setCurrentPage) => {
    const totalPages = getTotalPages(data);
    if (totalPages <= 1) return null;

    const pageNumbers = [];
    for (let i = 1; i <= totalPages; i++) {
      pageNumbers.push(i);
    }

    return (
      <div className="flex justify-center items-center space-x-2 mt-4">
        <button
          onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
          className={`px-3 py-1 rounded ${
            currentPage === 1
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          Previous
        </button>
        
        {pageNumbers.map((pageNum) => (
          <button
            key={pageNum}
            onClick={() => setCurrentPage(pageNum)}
            className={`px-3 py-1 rounded ${
              currentPage === pageNum
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {pageNum}
          </button>
        ))}
        
        <button
          onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
          className={`px-3 py-1 rounded ${
            currentPage === totalPages
              ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
              : 'bg-blue-500 text-white hover:bg-blue-600'
          }`}
        >
          Next
        </button>
      </div>
    );
  };

  const handleAddIncome = async () => {
    try {
      if (!incomeData.description || !incomeData.amount || !incomeData.category || !incomeData.income_date) {
        alert('Please fill in all required fields');
        return;
      }

      await axios.post(`${API}/incomes`, incomeData);
      
      setShowAddIncomeModal(false);
      setIncomeData({
        description: '',
        amount: 0,
        category: '',
        income_date: ''
      });
      
      // Refresh data after adding income
      await fetchIncomes();
      await fetchDailySales();
      await fetchFinancialSummary();
      await fetchDailyFinancialSummary();
      alert('Income added successfully!');
    } catch (error) {
      console.error('Error adding income:', error);
      alert('Error adding income. Please try again.');
    }
  };

  const handleDeleteExpense = async (expenseId) => {
    if (window.confirm('Are you sure you want to delete this expense?')) {
      try {
        await axios.delete(`${API}/expenses/${expenseId}`);
        await fetchExpenses();
        await fetchFinancialSummary();
        await fetchDailyFinancialSummary();
        alert('Expense deleted successfully!');
      } catch (error) {
        console.error('Error deleting expense:', error);
        alert('Error deleting expense. Please try again.');
      }
    }
  };

  const handleDeleteIncome = async (id) => {
    if (window.confirm('Are you sure you want to delete this income record?')) {
      try {
        await axios.delete(`${API}/incomes/${id}`);
        await fetchIncomes();
        await fetchDailySales();
        await fetchFinancialSummary();
        await fetchDailyFinancialSummary();
        alert('Income record deleted successfully!');
      } catch (error) {
        console.error('Error deleting income:', error);
        alert('Error deleting income record. Please try again.');
      }
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Utilities': 'bg-blue-100 text-blue-800',
      'Maintenance': 'bg-orange-100 text-orange-800',
      'Staff': 'bg-green-100 text-green-800',
      'Food': 'bg-purple-100 text-purple-800',
      'Marketing': 'bg-pink-100 text-pink-800',
      'Supplies': 'bg-yellow-100 text-yellow-800',
      'Insurance': 'bg-indigo-100 text-indigo-800',
      'Other': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Inc & Exp Management</h2>
          <p className="text-gray-600">Track income, expenses and monitor financial performance</p>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={() => setShowAddIncomeModal(true)}
            className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 flex items-center space-x-2"
          >
            <span>+</span>
            <span>Add Income</span>
          </button>
          <button 
            onClick={() => setShowAddExpenseModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 flex items-center space-x-2"
          >
            <span>+</span>
            <span>Add Expense</span>
          </button>
        </div>
      </div>

      {/* Financial Summary Cards */}
      {dailyFinancialSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-800 mb-2">Total Revenue</h3>
            <p className="text-3xl font-bold text-green-900">LKR {dailyFinancialSummary.total_revenue.toFixed(2)}</p>
            <p className="text-sm text-green-600">Today ({new Date(dailyFinancialSummary.date).toLocaleDateString()})</p>
          </div>
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Total Expenses</h3>
            <p className="text-3xl font-bold text-red-900">LKR {dailyFinancialSummary.total_expenses.toFixed(2)}</p>
            <p className="text-sm text-red-600">Today ({new Date(dailyFinancialSummary.date).toLocaleDateString()})</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-2">Cash Balance</h3>
            <p className="text-3xl font-bold text-blue-900">LKR {dailyFinancialSummary.cash_balance.toFixed(2)}</p>
            <p className="text-sm text-blue-600">Cash payments today</p>
          </div>
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-2">Bank Balance</h3>
            <p className="text-3xl font-bold text-purple-900">LKR {dailyFinancialSummary.bank_balance.toFixed(2)}</p>
            <p className="text-sm text-purple-600">Card + Bank Transfer</p>
          </div>
        </div>
      )}

      {/* Expenses Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Expense Records</h3>
        </div>
        {expenses.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No expenses recorded
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created By
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {getPaginatedData(expenses, expensePage).map((expense) => (
                    <tr key={expense.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{expense.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-red-600">LKR {expense.amount.toFixed(2)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(expense.category)}`}>
                          {expense.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{expense.expense_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{expense.created_by}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleDeleteExpense(expense.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {renderPagination(expenses, expensePage, setExpensePage)}
          </div>
        )}
      </div>

      {/* Income Records Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Income Records</h3>
        
        {/* Room Bookings Income */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-green-800 mb-3">Room Bookings</h4>
          {dailySales && dailySales.length > 0 ? (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-green-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Guest</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Room</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Payment Method</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 uppercase tracking-wider">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getPaginatedData(dailySales, roomBookingsPage).map((sale, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(sale.date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{sale.customer_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{sale.room_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{sale.payment_method}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-green-600">LKR {sale.total_amount.toFixed(2)}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {renderPagination(dailySales, roomBookingsPage, setRoomBookingsPage)}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No room booking income recorded
            </div>
          )}
        </div>

        {/* Additional Income */}
        <div>
          <h4 className="text-md font-medium text-blue-800 mb-3">Additional Income</h4>
          {incomes && incomes.length > 0 ? (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-blue-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {getPaginatedData(incomes, additionalIncomePage).map((income, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(income.income_date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{income.description}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-600">{income.category}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-blue-600">LKR {income.amount.toFixed(2)}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <button
                            onClick={() => handleDeleteIncome(income.id)}
                            className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700 transition-colors"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {renderPagination(incomes, additionalIncomePage, setAdditionalIncomePage)}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No additional income recorded
            </div>
          )}
        </div>
      </div>

      {/* Add Expense Modal */}
      {showAddExpenseModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add New Expense</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <input
                  type="text"
                  value={expenseData.description}
                  onChange={(e) => setExpenseData({...expenseData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter expense description"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (LKR) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={expenseData.amount}
                  onChange={(e) => setExpenseData({...expenseData, amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  value={expenseData.category}
                  onChange={(e) => setExpenseData({...expenseData, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select category</option>
                  {expenseCategories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date *
                </label>
                <input
                  type="date"
                  value={expenseData.expense_date}
                  onChange={(e) => setExpenseData({...expenseData, expense_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddExpenseModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddExpense}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Expense
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Income Modal */}
      {showAddIncomeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Add New Income</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description *
                </label>
                <input
                  type="text"
                  value={incomeData.description}
                  onChange={(e) => setIncomeData({...incomeData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter income description"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount (LKR) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={incomeData.amount}
                  onChange={(e) => setIncomeData({...incomeData, amount: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="0.00"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Category *
                </label>
                <select
                  value={incomeData.category}
                  onChange={(e) => setIncomeData({...incomeData, category: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="">Select category</option>
                  {incomeCategories.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Date *
                </label>
                <input
                  type="date"
                  value={incomeData.income_date}
                  onChange={(e) => setIncomeData({...incomeData, income_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddIncomeModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddIncome}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Add Income
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Guests Component
const Guests = () => {
  const [guests, setGuests] = useState([]);
  const [filteredGuests, setFilteredGuests] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedGuest, setSelectedGuest] = useState(null);
  const [showGuestDetails, setShowGuestDetails] = useState(false);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [downloadDateRange, setDownloadDateRange] = useState({
    startDate: '',
    endDate: ''
  });

  useEffect(() => {
    fetchGuests();
  }, []);

  useEffect(() => {
    // Filter guests based on search query
    if (searchQuery.trim() === '') {
      setFilteredGuests(guests);
    } else {
      const filtered = guests.filter(guest =>
        guest.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        guest.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        guest.phone.includes(searchQuery)
      );
      setFilteredGuests(filtered);
    }
  }, [guests, searchQuery]);

  const fetchGuests = async () => {
    try {
      const response = await axios.get(`${API}/guests`);
      setGuests(response.data);
      setFilteredGuests(response.data);
    } catch (error) {
      console.error('Error fetching guests:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGuestDetails = async (guestEmail) => {
    try {
      const response = await axios.get(`${API}/guests/${guestEmail}`);
      setSelectedGuest(response.data);
      setShowGuestDetails(true);
    } catch (error) {
      console.error('Error fetching guest details:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Upcoming':
        return 'bg-blue-100 text-blue-800';
      case 'Checked-in':
        return 'bg-green-100 text-green-800';
      case 'Completed':
        return 'bg-gray-100 text-gray-800';
      case 'Cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleDownloadGuests = async () => {
    try {
      if (!downloadDateRange.startDate || !downloadDateRange.endDate) {
        alert('Please select both start and end dates');
        return;
      }

      // Get all bookings and filter by date range
      const response = await axios.get(`${API}/bookings`);
      const allBookings = response.data.bookings || response.data;
      
      if (!allBookings || allBookings.length === 0) {
        alert('No booking data found.');
        return;
      }
      
      // Filter bookings based on date range (check-in dates within the selected range)
      const startDate = new Date(downloadDateRange.startDate);
      const endDate = new Date(downloadDateRange.endDate);
      
      const filteredBookings = allBookings.filter(booking => {
        if (booking.check_in_date) {
          const checkInDate = new Date(booking.check_in_date);
          return checkInDate >= startDate && checkInDate <= endDate;
        }
        return false;
      });

      // If no bookings found with date filtering, offer to download all
      let dataToDownload = filteredBookings;
      if (filteredBookings.length === 0) {
        const downloadAll = window.confirm(
          `No guest bookings found in the selected date range (${downloadDateRange.startDate} to ${downloadDateRange.endDate}). Would you like to download all ${allBookings.length} guest records instead?`
        );
        
        if (downloadAll) {
          dataToDownload = allBookings;
        } else {
          alert('No guest data downloaded.');
          return;
        }
      }

      // Prepare data for Excel export - extract guest information from bookings
      const excelData = dataToDownload.map(booking => ({
        'Guest Name': booking.guest_name || '',
        'Email': booking.guest_email || '',
        'Phone': booking.guest_phone || '',
        'Country': booking.country || '',
        'Guest ID/Passport': booking.guest_id_passport || '',
        'Room Number': booking.room_number || '',
        'Check-in Date': booking.check_in_date ? new Date(booking.check_in_date).toLocaleDateString() : '',
        'Check-out Date': booking.check_out_date ? new Date(booking.check_out_date).toLocaleDateString() : '',
        'Stay Type': booking.stay_type || '',
        'Booking Amount (LKR)': booking.booking_amount || 0,
        'Booking Status': booking.status || '',
        'Additional Notes': booking.additional_notes || '',
        'Booking Created': booking.created_at ? new Date(booking.created_at).toLocaleDateString() : ''
      }));

      // Create Excel workbook and worksheet
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.json_to_sheet(excelData);
      
      // Add the worksheet to the workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Guest Data');
      
      // Generate filename
      const filename = `guest_data_${downloadDateRange.startDate}_to_${downloadDateRange.endDate}.xlsx`;
      
      // Download the Excel file
      XLSX.writeFile(wb, filename);

      setShowDownloadModal(false);
      alert(`Downloaded ${dataToDownload.length} guest records to Excel file`);
    } catch (error) {
      console.error('Error downloading guest data:', error);
      alert('Error downloading guest data: ' + (error.response?.data?.detail || error.message || 'Please try again.'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Guests</h2>
          <p className="text-gray-600">Manage guest information and booking history</p>
        </div>
        <button
          onClick={() => setShowDownloadModal(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 flex items-center space-x-2"
        >
          <span>📥</span>
          <span>Download Guest Data</span>
        </button>
      </div>

      {/* Search Section */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Search guests by name, email, or phone..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400">🔍</span>
          </div>
        </div>
        {searchQuery && (
          <p className="mt-2 text-sm text-gray-600">
            Showing {filteredGuests.length} result(s) for "{searchQuery}"
          </p>
        )}
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {filteredGuests.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {searchQuery ? `No guests found matching "${searchQuery}"` : 'No guests found'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Guest Name
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
                    Completed Stays
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Upcoming Bookings
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Stay
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredGuests.map((guest) => (
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
                      <div className="text-sm text-gray-900">{guest.total_stays}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{guest.upcoming_bookings}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {guest.last_stay ? guest.last_stay : 'Never'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => fetchGuestDetails(guest.email)}
                        className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Guest Details Modal */}
      {showGuestDetails && selectedGuest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold">Guest Details</h3>
              <button
                onClick={() => setShowGuestDetails(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>
            
            <div className="mb-6">
              <h4 className="text-lg font-medium text-gray-900 mb-2">{selectedGuest.name}</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Email:</span>
                  <span className="ml-2 text-gray-900">{selectedGuest.email}</span>
                </div>
                <div>
                  <span className="text-gray-500">Phone:</span>
                  <span className="ml-2 text-gray-900">{selectedGuest.phone}</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">Booking History</h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Room
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Check-in
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Check-out
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Booked On
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {selectedGuest.bookings.map((booking) => (
                      <tr key={booking.id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{booking.room_number}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{booking.check_in_date}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{booking.check_out_date}</div>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(booking.status)}`}>
                            {booking.status}
                          </span>
                        </td>
                        <td className="px-4 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(booking.created_at).toLocaleDateString()}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="flex justify-end mt-6">
              <button
                onClick={() => setShowGuestDetails(false)}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Download Modal */}
      {showDownloadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Download Guest Data</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date *
                </label>
                <input
                  type="date"
                  value={downloadDateRange.startDate}
                  onChange={(e) => setDownloadDateRange({...downloadDateRange, startDate: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date *
                </label>
                <input
                  type="date"
                  value={downloadDateRange.endDate}
                  onChange={(e) => setDownloadDateRange({...downloadDateRange, endDate: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>

              <div className="text-sm text-gray-600">
                <p>Download guest data based on the selected date range. If no guests have completed stays in the date range, you'll be offered to download all guests.</p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowDownloadModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDownloadGuests}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Download Excel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Bookings Component
const Bookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showDownloadModal, setShowDownloadModal] = useState(false);
  const [downloadDateRange, setDownloadDateRange] = useState({
    start_date: '',
    end_date: '',
    status: ''
  });

  useEffect(() => {
    fetchBookings();
  }, [currentPage, searchTerm, statusFilter]);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: currentPage,
        limit: 20,
        search: searchTerm,
        status: statusFilter
      });
      
      const response = await axios.get(`${API}/bookings?${params}`);
      setBookings(response.data.bookings);
      setTotalPages(response.data.total_pages);
      setTotalCount(response.data.total_count);
    } catch (error) {
      console.error('Error fetching bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (value) => {
    setSearchTerm(value);
    setCurrentPage(1); // Reset to first page when searching
  };

  const handleStatusChange = (value) => {
    setStatusFilter(value);
    setCurrentPage(1); // Reset to first page when filtering
  };

  const handleDownload = async () => {
    try {
      // Fetch all bookings first, then filter on frontend if needed
      let apiUrl = `${API}/bookings`;
      let queryParams = [];
      
      // Add pagination parameter to get all bookings
      queryParams.push('page=1');
      queryParams.push('limit=1000'); // Get a large number of bookings
      
      if (queryParams.length > 0) {
        apiUrl += '?' + queryParams.join('&');
      }
      
      const response = await axios.get(apiUrl);
      let bookingsData = response.data.bookings || response.data;
      
      if (!bookingsData || bookingsData.length === 0) {
        alert('No bookings found.');
        return;
      }

      // Apply date filtering on frontend
      if (downloadDateRange.start_date || downloadDateRange.end_date) {
        bookingsData = bookingsData.filter(booking => {
          const bookingDate = new Date(booking.check_in_date);
          let matchesDateRange = true;
          
          if (downloadDateRange.start_date) {
            const startDate = new Date(downloadDateRange.start_date);
            matchesDateRange = matchesDateRange && bookingDate >= startDate;
          }
          
          if (downloadDateRange.end_date) {
            const endDate = new Date(downloadDateRange.end_date);
            matchesDateRange = matchesDateRange && bookingDate <= endDate;
          }
          
          return matchesDateRange;
        });
      }

      // Apply status filtering on frontend
      if (downloadDateRange.status && downloadDateRange.status !== 'All') {
        bookingsData = bookingsData.filter(booking => 
          booking.status && booking.status.toLowerCase() === downloadDateRange.status.toLowerCase()
        );
      }
      
      if (bookingsData.length === 0) {
        alert('No bookings found for the selected criteria.');
        return;
      }

      // Prepare data for Excel export
      const excelData = bookingsData.map(booking => ({
        'Booking ID': booking.id || '',
        'Guest Name': booking.guest_name || '',
        'Guest Email': booking.guest_email || '',
        'Guest Phone': booking.guest_phone || '',
        'Country': booking.country || '',
        'Guest ID/Passport': booking.guest_id_passport || '',
        'Room Number': booking.room_number || '',
        'Check-in Date': booking.check_in_date ? new Date(booking.check_in_date).toLocaleDateString() : '',
        'Check-out Date': booking.check_out_date ? new Date(booking.check_out_date).toLocaleDateString() : '',
        'Stay Type': booking.stay_type || '',
        'Booking Amount (LKR)': booking.booking_amount || 0,
        'Status': booking.status || '',
        'Additional Notes': booking.additional_notes || '',
        'Created At': booking.created_at ? new Date(booking.created_at).toLocaleDateString() : ''
      }));

      // Create Excel workbook and worksheet
      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.json_to_sheet(excelData);
      
      // Add the worksheet to the workbook
      XLSX.utils.book_append_sheet(wb, ws, 'Bookings Data');
      
      // Generate filename with filters applied
      let filename = 'bookings';
      if (downloadDateRange.start_date && downloadDateRange.end_date) {
        filename += `_${downloadDateRange.start_date}_to_${downloadDateRange.end_date}`;
      } else if (downloadDateRange.start_date) {
        filename += `_from_${downloadDateRange.start_date}`;
      } else if (downloadDateRange.end_date) {
        filename += `_until_${downloadDateRange.end_date}`;
      }
      if (downloadDateRange.status && downloadDateRange.status !== 'All') {
        filename += `_${downloadDateRange.status.toLowerCase()}`;
      }
      filename += '.xlsx';
      
      // Download the Excel file
      XLSX.writeFile(wb, filename);
      
      setShowDownloadModal(false);
      alert(`Downloaded ${bookingsData.length} booking records to Excel file`);
    } catch (error) {
      console.error('Error downloading bookings:', error);
      alert('Error downloading bookings data: ' + (error.response?.data?.detail || error.message || 'Please try again.'));
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Upcoming':
        return 'bg-blue-100 text-blue-800';
      case 'Checked-in':
        return 'bg-green-100 text-green-800';
      case 'Completed':
        return 'bg-gray-100 text-gray-800';
      case 'Cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderPagination = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    // Previous button
    if (currentPage > 1) {
      pages.push(
        <button
          key="prev"
          onClick={() => setCurrentPage(currentPage - 1)}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Previous
        </button>
      );
    }

    // Page numbers
    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => setCurrentPage(i)}
          className={`px-3 py-2 text-sm font-medium border rounded-md ${
            i === currentPage
              ? 'bg-blue-600 text-white border-blue-600'
              : 'text-gray-500 bg-white border-gray-300 hover:bg-gray-50'
          }`}
        >
          {i}
        </button>
      );
    }

    // Next button
    if (currentPage < totalPages) {
      pages.push(
        <button
          key="next"
          onClick={() => setCurrentPage(currentPage + 1)}
          className="px-3 py-2 text-sm font-medium text-gray-500 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Next
        </button>
      );
    }

    return (
      <div className="flex items-center justify-between px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-700">
          Showing {((currentPage - 1) * 20) + 1} to {Math.min(currentPage * 20, totalCount)} of {totalCount} bookings
        </div>
        <div className="flex space-x-1">
          {pages}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">All Bookings</h2>
          <p className="text-gray-600">Manage all hotel bookings and reservations</p>
        </div>
        <button
          onClick={() => setShowDownloadModal(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>Download CSV</span>
        </button>
      </div>

      {/* Search and Filter Controls */}
      <div className="mb-6 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search by guest name, email, phone, or room number..."
            value={searchTerm}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="sm:w-48">
          <select
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="Upcoming">Upcoming</option>
            <option value="Checked-in">Checked-in</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {bookings.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {searchTerm || statusFilter ? 'No bookings found matching your criteria' : 'No bookings found'}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Guest Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Phone
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Room
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-in
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Check-out
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {bookings.map((booking) => (
                    <tr key={booking.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{booking.guest_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{booking.guest_email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{booking.guest_phone || 'N/A'}</div>
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
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'LKR'
                          }).format(booking.booking_amount || 0)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(booking.created_at).toLocaleDateString()}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {totalPages > 1 && renderPagination()}
          </>
        )}
      </div>

      {/* Download Modal */}
      {showDownloadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-lg font-semibold mb-4">Download Bookings Data</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Start Date (Optional)
                </label>
                <input
                  type="date"
                  value={downloadDateRange.start_date}
                  onChange={(e) => setDownloadDateRange({...downloadDateRange, start_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  End Date (Optional)
                </label>
                <input
                  type="date"
                  value={downloadDateRange.end_date}
                  onChange={(e) => setDownloadDateRange({...downloadDateRange, end_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Status Filter (Optional)
                </label>
                <select
                  value={downloadDateRange.status}
                  onChange={(e) => setDownloadDateRange({...downloadDateRange, status: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Status</option>
                  <option value="Upcoming">Upcoming</option>
                  <option value="Checked-in">Checked-in</option>
                  <option value="Completed">Completed</option>
                  <option value="Cancelled">Cancelled</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-4 mt-6">
              <button
                onClick={() => setShowDownloadModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDownload}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Download Excel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Rooms Component
const Rooms = () => {
  const [rooms, setRooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddRoomModal, setShowAddRoomModal] = useState(false);
  const [showEditRoomModal, setShowEditRoomModal] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [roomData, setRoomData] = useState({
    room_number: '',
    room_type: '',
    price_per_night: 0,
    max_occupancy: 2,
    amenities: []
  });

  useEffect(() => {
    fetchRooms();
  }, []);

  const fetchRooms = async () => {
    try {
      const response = await axios.get(`${API}/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error('Error fetching rooms:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddRoom = async () => {
    try {
      await axios.post(`${API}/rooms`, roomData);
      setShowAddRoomModal(false);
      setRoomData({
        room_number: '',
        room_type: '',
        price_per_night: 0,
        max_occupancy: 2,
        amenities: []
      });
      await fetchRooms();
    } catch (error) {
      console.error('Error adding room:', error);
      alert('Error adding room. Please try again.');
    }
  };

  const handleEditRoom = async () => {
    try {
      await axios.put(`${API}/rooms/${selectedRoom.id}`, roomData);
      setShowEditRoomModal(false);
      setSelectedRoom(null);
      await fetchRooms();
    } catch (error) {
      console.error('Error updating room:', error);
      alert('Error updating room. Please try again.');
    }
  };

  const handleDeleteRoom = async (roomId) => {
    if (window.confirm('Are you sure you want to delete this room?')) {
      try {
        await axios.delete(`${API}/rooms/${roomId}`);
        await fetchRooms();
      } catch (error) {
        console.error('Error deleting room:', error);
        alert('Error deleting room. Please try again.');
      }
    }
  };

  const openEditModal = (room) => {
    setSelectedRoom(room);
    setRoomData({
      room_number: room.room_number,
      room_type: room.room_type,
      price_per_night: room.price_per_night,
      max_occupancy: room.max_occupancy,
      amenities: room.amenities || []
    });
    setShowEditRoomModal(true);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'Available':
        return 'bg-green-100 text-green-800';
      case 'Occupied':
        return 'bg-red-100 text-red-800';
      case 'Reserved':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleAmenityChange = (amenity) => {
    const currentAmenities = roomData.amenities || [];
    if (currentAmenities.includes(amenity)) {
      setRoomData({
        ...roomData,
        amenities: currentAmenities.filter(a => a !== amenity)
      });
    } else {
      setRoomData({
        ...roomData,
        amenities: [...currentAmenities, amenity]
      });
    }
  };

  const commonAmenities = ["WiFi", "TV", "AC", "Mini Fridge", "Room Service", "Balcony", "Bathtub", "Safe"];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Rooms</h2>
          <p className="text-gray-600">Manage hotel rooms and their details</p>
        </div>
        <button 
          onClick={() => setShowAddRoomModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 flex items-center space-x-2"
        >
          <span>Add Room</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {rooms.map((room) => (
          <div key={room.id} className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="relative">
              <img 
                src={room.image_url} 
                alt={`Room ${room.room_number}`}
                className="w-full h-48 object-cover"
              />
              <div className={`absolute top-4 right-4 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(room.status)}`}>
                {room.status}
              </div>
            </div>
            <div className="p-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">Room {room.room_number}</h3>
              <p className="text-sm text-gray-600 mb-2">{room.room_type}</p>
              <p className="text-lg font-bold text-gray-900 mb-2">LKR {room.price_per_night}/night</p>
              <p className="text-sm text-gray-600 mb-2">Max Occupancy: {room.max_occupancy}</p>
              <div className="mb-4">
                <p className="text-sm text-gray-600">Amenities: {room.amenities?.join(', ')}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => openEditModal(room)}
                  className="flex-1 bg-blue-600 text-white px-3 py-2 rounded text-sm hover:bg-blue-700 transition-colors"
                >
                  Edit Room
                </button>
                <button
                  onClick={() => handleDeleteRoom(room.id)}
                  className="flex-1 bg-red-600 text-white px-3 py-2 rounded text-sm hover:bg-red-700 transition-colors"
                >
                  Remove Room
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Add Room Modal */}
      {showAddRoomModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Add New Room</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room Number *</label>
                <input
                  type="text"
                  value={roomData.room_number}
                  onChange={(e) => setRoomData({...roomData, room_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter room number"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room Type *</label>
                <select
                  value={roomData.room_type}
                  onChange={(e) => setRoomData({...roomData, room_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select room type</option>
                  <option value="Single">Single</option>
                  <option value="Double">Double</option>
                  <option value="Triple">Triple</option>
                  <option value="Suite">Suite</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price per Night (LKR) *</label>
                <input
                  type="number"
                  value={roomData.price_per_night}
                  onChange={(e) => setRoomData({...roomData, price_per_night: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter price"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Occupancy *</label>
                <input
                  type="number"
                  value={roomData.max_occupancy}
                  onChange={(e) => setRoomData({...roomData, max_occupancy: parseInt(e.target.value) || 2})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="10"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Amenities</label>
                <div className="grid grid-cols-2 gap-2">
                  {commonAmenities.map((amenity) => (
                    <label key={amenity} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={roomData.amenities?.includes(amenity)}
                        onChange={() => handleAmenityChange(amenity)}
                        className="mr-2"
                      />
                      <span className="text-sm">{amenity}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddRoomModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddRoom}
                disabled={!roomData.room_number || !roomData.room_type || !roomData.price_per_night}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                Add Room
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Room Modal */}
      {showEditRoomModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Edit Room</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room Number *</label>
                <input
                  type="text"
                  value={roomData.room_number}
                  onChange={(e) => setRoomData({...roomData, room_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Room Type *</label>
                <select
                  value={roomData.room_type}
                  onChange={(e) => setRoomData({...roomData, room_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Single">Single</option>
                  <option value="Double">Double</option>
                  <option value="Triple">Triple</option>
                  <option value="Suite">Suite</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price per Night (LKR) *</label>
                <input
                  type="number"
                  value={roomData.price_per_night}
                  onChange={(e) => setRoomData({...roomData, price_per_night: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Max Occupancy *</label>
                <input
                  type="number"
                  value={roomData.max_occupancy}
                  onChange={(e) => setRoomData({...roomData, max_occupancy: parseInt(e.target.value) || 2})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1"
                  max="10"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Amenities</label>
                <div className="grid grid-cols-2 gap-2">
                  {commonAmenities.map((amenity) => (
                    <label key={amenity} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={roomData.amenities?.includes(amenity)}
                        onChange={() => handleAmenityChange(amenity)}
                        className="mr-2"
                      />
                      <span className="text-sm">{amenity}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowEditRoomModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleEditRoom}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Update Room
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          <Link 
            to="/" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Dashboard
          </Link>
          <Link 
            to="/rooms" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/rooms') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Rooms
          </Link>
          <Link 
            to="/guests" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/guests') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Guests
          </Link>
          <Link 
            to="/bookings" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/bookings') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Bookings
          </Link>
          <Link 
            to="/expenses" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/expenses') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Inc & Exp
          </Link>
          <Link 
            to="/reports" 
            className={`px-3 py-2 rounded-md text-sm font-medium ${
              isActive('/reports') 
                ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Reports
          </Link>
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <BrowserRouter>
        {/* Header */}
        <header className="bg-white shadow-md border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-xl font-bold text-gray-900 flex items-center">
                    🏨 Hotel Management System
                  </h1>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">Welcome, Admin</span>
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/rooms" element={<Rooms />} />
            <Route path="/guests" element={<Guests />} />
            <Route path="/bookings" element={<Bookings />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/reports" element={<Reports />} />
          </Routes>
        </main>
      </BrowserRouter>
    </div>
  );
}

export default App;