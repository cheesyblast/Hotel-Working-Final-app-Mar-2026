import React, { useState, useEffect, useContext, createContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link, useLocation, Navigate } from "react-router-dom";
import axios from "axios";
import * as XLSX from 'xlsx';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Authentication Context
const AuthContext = createContext();

// Financial Context for cross-component data refresh
const FinancialContext = createContext();

// Financial Provider
const FinancialProvider = ({ children }) => {
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  const triggerFinancialRefresh = () => {
    setRefreshTrigger(prev => prev + 1);
  };
  
  return (
    <FinancialContext.Provider value={{ refreshTrigger, triggerFinancialRefresh }}>
      {children}
    </FinancialContext.Provider>
  );
};

// Hook to use financial context
const useFinancial = () => {
  const context = useContext(FinancialContext);
  if (!context) {
    throw new Error('useFinancial must be used within a FinancialProvider');
  }
  return context;
};

// Authentication Provider
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);
  const [isSetupCompleted, setIsSetupCompleted] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);

  // Set axios default authorization header
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  // Check setup status on app load
  useEffect(() => {
    const checkSetupStatus = async () => {
      try {
        const response = await axios.get(`${API}/setup/status`);
        setIsSetupCompleted(response.data.is_completed);
      } catch (error) {
        console.error('Error checking setup status:', error);
      } finally {
        setCheckingSetup(false);
      }
    };
    checkSetupStatus();
  }, []);

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      if (token && isSetupCompleted) {
        try {
          const response = await axios.get(`${API}/auth/me`);
          setUser(response.data);
        } catch (error) {
          console.error('Token invalid:', error);
          logout();
        }
      }
      setLoading(false);
    };
    
    if (!checkingSetup) {
      checkAuth();
    }
  }, [token, isSetupCompleted, checkingSetup]);

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password
      });
      
      const { access_token } = response.data;
      localStorage.setItem('token', access_token);
      
      // Set authorization header immediately before making the next request
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setToken(access_token);
      
      // Get user info
      const userResponse = await axios.get(`${API}/auth/me`);
      setUser(userResponse.data);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API}/auth/logout`);
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      setToken(null);
      setUser(null);
      delete axios.defaults.headers.common['Authorization'];
    }
  };

  const completeSetup = async (setupData) => {
    try {
      await axios.post(`${API}/setup/complete`, setupData);
      setIsSetupCompleted(true);
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Setup failed' 
      };
    }
  };

  const value = {
    user,
    token,
    loading,
    isSetupCompleted,
    checkingSetup,
    login,
    logout,
    completeSetup
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  return useContext(AuthContext);
};

// Setup Wizard Component
const SetupWizard = () => {
  const [formData, setFormData] = useState({
    hotel_name: '',
    hotel_address: '',
    hotel_email: '',
    timezone: 'Asia/Colombo',  // Default to Sri Lanka timezone
    cash_balance: 0,
    bank_balance: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isPostReset, setIsPostReset] = useState(false);
  const { completeSetup } = useAuth();

  // Check if this is a post-reset setup and pre-fill data
  useEffect(() => {
    const checkPostResetSetup = async () => {
      try {
        // Check if hotel settings exist (indicating post-reset scenario)
        const settingsResponse = await axios.get(`${API}/settings`);
        if (settingsResponse.data && settingsResponse.data.hotel_name) {
          setIsPostReset(true);
          setFormData(prev => ({
            ...prev,
            hotel_name: settingsResponse.data.hotel_name || '',
            hotel_address: settingsResponse.data.hotel_address || '',
            hotel_email: settingsResponse.data.hotel_email || '',
            timezone: settingsResponse.data.timezone || 'Asia/Colombo'
          }));
        }
      } catch (error) {
        // If settings don't exist, this is a fresh setup
        console.log('Fresh setup - no existing settings');
      }
    };
    checkPostResetSetup();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await completeSetup(formData);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name === 'cash_balance' || name === 'bank_balance' 
        ? parseFloat(value) || 0 
        : value
    });
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">
            {isPostReset ? 'Re-initialize Your Hotel' : 'Welcome!'}
          </h1>
          <p className="text-gray-400">
            {isPostReset 
              ? 'After the complete reset, please set your initial cash and bank balances to restart your financial tracking'
              : "Let's set up your hotel management system"
            }
          </p>
        </div>

        {error && (
          <div className="bg-red-600 text-white p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Hotel Name
            </label>
            <input
              type="text"
              name="hotel_name"
              value={formData.hotel_name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="Enter your hotel name"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Hotel Address
            </label>
            <textarea
              name="hotel_address"
              value={formData.hotel_address}
              onChange={handleChange}
              required
              rows={3}
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="Enter your hotel address"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Hotel Email
            </label>
            <input
              type="email"
              name="hotel_email"
              value={formData.hotel_email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="Enter hotel email address"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Hotel Timezone
            </label>
            <select
              name="timezone"
              value={formData.timezone}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
            >
              <option value="Asia/Colombo">Asia/Colombo (Sri Lanka)</option>
              <option value="Asia/Kolkata">Asia/Kolkata (India)</option>
              <option value="Asia/Dubai">Asia/Dubai (UAE)</option>
              <option value="Asia/Singapore">Asia/Singapore</option>
              <option value="America/New_York">America/New_York (EST)</option>
              <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
              <option value="Europe/London">Europe/London (GMT)</option>
              <option value="Europe/Paris">Europe/Paris (CET)</option>
              <option value="Australia/Sydney">Australia/Sydney</option>
              <option value="Asia/Tokyo">Asia/Tokyo (Japan)</option>
              <option value="UTC">UTC</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              All timestamps in the application will use this timezone
            </p>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Initial Cash Balance {isPostReset ? '(Post-Reset)' : ''}
            </label>
            <input
              type="number"
              name="cash_balance"
              value={formData.cash_balance}
              onChange={handleChange}
              min="0"
              step="0.01"
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="0.00"
            />
            <p className="text-xs text-gray-500 mt-1">
              {isPostReset 
                ? 'Enter your current cash balance to restart financial tracking'
                : 'Starting cash balance for your hotel'
              }
            </p>
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Initial Bank Balance {isPostReset ? '(Post-Reset)' : ''}
            </label>
            <input
              type="number"
              name="bank_balance"
              value={formData.bank_balance}
              onChange={handleChange}
              min="0"
              step="0.01"
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="0.00"
            />
            <p className="text-xs text-gray-500 mt-1">
              {isPostReset 
                ? 'Enter your current bank balance to restart financial tracking'
                : 'Starting bank balance for your hotel'
              }
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading 
              ? (isPostReset ? 'Re-initializing...' : 'Setting up...') 
              : (isPostReset ? 'Complete Re-initialization' : 'Complete Setup')
            }
          </button>
        </form>

        <div className="mt-6 p-4 bg-gray-700 rounded-lg">
          <p className="text-sm text-gray-300 mb-2">Default admin credentials:</p>
          <p className="text-xs text-gray-400">Username: <strong className="text-white">admin</strong></p>
          <p className="text-xs text-gray-400">Password: <strong className="text-white">admin123</strong></p>
          <p className="text-xs text-gray-500 mt-2">You can change these after logging in.</p>
        </div>
      </div>
    </div>
  );
};

// Login Component
const LoginPage = () => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
  const [forgotPasswordMessage, setForgotPasswordMessage] = useState('');
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const result = await login(credentials.username, credentials.password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setForgotPasswordMessage('');

    try {
      await axios.post(`${API}/auth/forgot-password`, {
        username_or_email: forgotPasswordEmail
      });
      setForgotPasswordMessage('If the account exists, a new password has been sent to the registered email.');
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to send reset email');
    }
    
    setLoading(false);
  };

  const handleChange = (e) => {
    setCredentials({
      ...credentials,
      [e.target.name]: e.target.value
    });
  };

  if (showForgotPassword) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md">
          <div className="text-center mb-6">
            <h1 className="text-3xl font-bold text-white mb-2">Forgot Password</h1>
            <p className="text-gray-400">Enter your username or email to reset your password</p>
          </div>

          {error && (
            <div className="bg-red-600 text-white p-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          {forgotPasswordMessage && (
            <div className="bg-green-600 text-white p-3 rounded-lg mb-4">
              {forgotPasswordMessage}
            </div>
          )}

          <form onSubmit={handleForgotPassword} className="space-y-4">
            <div>
              <label className="block text-gray-300 text-sm font-medium mb-2">
                Username or Email
              </label>
              <input
                type="text"
                value={forgotPasswordEmail}
                onChange={(e) => setForgotPasswordEmail(e.target.value)}
                required
                className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="Enter username or email"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Sending...' : 'Send New Password'}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              onClick={() => {
                setShowForgotPassword(false);
                setError('');
                setForgotPasswordMessage('');
              }}
              className="text-blue-400 hover:text-blue-300 text-sm"
            >
              Back to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Hotel Management</h1>
          <p className="text-gray-400">Sign in to your account</p>
        </div>

        {error && (
          <div className="bg-red-600 text-white p-3 rounded-lg mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Username
            </label>
            <input
              type="text"
              name="username"
              value={credentials.username}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="Enter your username"
            />
          </div>

          <div>
            <label className="block text-gray-300 text-sm font-medium mb-2">
              Password
            </label>
            <input
              type="password"
              name="password"
              value={credentials.password}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 bg-gray-700 text-white border border-gray-600 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => setShowForgotPassword(true)}
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            Forgot Password?
          </button>
        </div>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading, isSetupCompleted, checkingSetup } = useAuth();

  if (checkingSetup || loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!isSetupCompleted) {
    return <SetupWizard />;
  }

  if (!user) {
    return <LoginPage />;
  }

  return children;
};

// Real-time clock component
const RealTimeClock = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const { user, logout } = useAuth();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const handleLogout = async () => {
    if (window.confirm('Are you sure you want to logout?')) {
      await logout();
    }
  };

  return (
    <div className="flex items-center space-x-2 sm:space-x-4">
      <div className="text-xs sm:text-sm text-gray-400 text-right">
        <div className="hidden sm:block">Welcome, {user?.full_name || user?.username || 'User'}</div>
        <div className="text-xs">
          <span className="hidden sm:inline">{currentTime.toLocaleDateString()} | </span>
          {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="text-xs sm:text-sm text-red-400 hover:text-red-300 bg-red-900 px-2 py-1 rounded flex-shrink-0"
      >
        Logout
      </button>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const [rooms, setRooms] = useState([]);
  const [upcomingBookings, setUpcomingBookings] = useState([]);
  const [checkedInCustomers, setCheckedInCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Get current user context
  const { user } = useAuth();
  
  // Get financial context to trigger refreshes across components
  const { triggerFinancialRefresh } = useFinancial();
  
  // Modal states
  const [showCheckinModal, setShowCheckinModal] = useState(false);
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [showNewBookingModal, setShowNewBookingModal] = useState(false);
  const [showEditBookingModal, setShowEditBookingModal] = useState(false);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [showStatusSelectionModal, setShowStatusSelectionModal] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  
  // Dropdown state for booking actions and customer actions
  const [openDropdowns, setOpenDropdowns] = useState({});
  const [openCustomerDropdowns, setOpenCustomerDropdowns] = useState({});
  
  // Advance payment modal state
  const [showAdvancePaymentModal, setShowAdvancePaymentModal] = useState(false);
  const [advancePaymentData, setAdvancePaymentData] = useState({
    amount: '',
    payment_method: 'Cash',
    notes: ''
  });
  
  // Extend stay modal state
  const [showExtendStayModal, setShowExtendStayModal] = useState(false);
  const [extendStayData, setExtendStayData] = useState({
    new_checkout_date: ''
  });
  
  // Early checkout modal state  
  const [showEarlyCheckoutModal, setShowEarlyCheckoutModal] = useState(false);
  const [earlyCheckoutPreview, setEarlyCheckoutPreview] = useState(null);
  const [earlyCheckoutData, setEarlyCheckoutData] = useState({
    additional_amount: 0,
    discount_amount: 0,
    payment_method: 'Cash'
  });
  const [showPaymentCollectionModal, setShowPaymentCollectionModal] = useState(false);
  const [paymentCollectionData, setPaymentCollectionData] = useState({
    amount: 0,
    payment_method: 'Cash'
  });
  
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
  const [showPrintInvoiceDialog, setShowPrintInvoiceDialog] = useState(false);
  const [invoiceData, setInvoiceData] = useState(null);
  const [availableRoomsForBooking, setAvailableRoomsForBooking] = useState([]);
  const [availableChannels, setAvailableChannels] = useState([]);
  const [selectedBookingStatus, setSelectedBookingStatus] = useState('Upcoming');
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
    commission_amount: 0,
    booking_channel_id: '',
    booking_channel_name: 'Direct',
    additional_notes: ''
  });
  const [editBookingData, setEditBookingData] = useState({
    room_number: '',
    check_in_date: '',
    check_out_date: '',
    additional_notes: ''
  });
  const [hotelSettings, setHotelSettings] = useState({
    hotel_name: 'Hotel Management System',
    hotel_logo: '',
    hotel_address: '',
    hotel_phone: '',
    hotel_contact: '',
    hotel_email: '',
    currency: 'LKR'
  });

  useEffect(() => {
    initializeData();
    
    // Add click outside handler for dropdowns
    const handleClickOutside = (event) => {
      // Close dropdowns when clicking outside
      if (!event.target.closest('.relative')) {
        closeAllDropdowns();
        closeAllCustomerDropdowns();
      }
    };
    
    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  const initializeData = async () => {
    try {
      // No longer auto-initialize sample data - let admin manage via reset feature
      // await axios.post(`${API}/init-data`);
      
      // Fetch all data
      await Promise.all([
        fetchRooms(),
        fetchUpcomingBookings(),
        fetchCheckedInCustomers(),
        fetchHotelSettings(),
        fetchAvailableChannels()
      ]);
    } catch (error) {
      console.error('Error initializing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHotelSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setHotelSettings({
        hotel_name: response.data.hotel_name || 'Hotel Management System',
        hotel_logo: response.data.hotel_logo || '',
        hotel_address: response.data.hotel_address || '',
        hotel_phone: response.data.hotel_phone || '',
        hotel_contact: response.data.hotel_contact || '',
        hotel_email: response.data.hotel_email || '',
        currency: response.data.currency || 'LKR'
      });
    } catch (error) {
      console.error('Error fetching hotel settings:', error);
    }
  };

  const fetchAvailableChannels = async () => {
    try {
      const response = await axios.get(`${API}/booking-channels`);
      setAvailableChannels(response.data.filter(channel => channel.is_active));
    } catch (error) {
      console.error('Error fetching booking channels:', error);
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
  const handleBookingFieldChange = async (field, value) => {
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
    
    // Update available rooms when dates change
    if (['check_in_date', 'check_out_date', 'stay_type'].includes(field)) {
      try {
        const availableRooms = await getAvailableRoomsForDates(
          updatedData.check_in_date,
          updatedData.check_out_date
        );
        setAvailableRoomsForBooking(availableRooms);
      } catch (error) {
        console.error('Error updating available rooms:', error);
        // Fallback to all non-occupied rooms
        setAvailableRoomsForBooking(getAvailableRooms());
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
      // Fetch latest hotel settings for invoice
      const settingsResponse = await axios.get(`${API}/settings`);
      const latestSettings = settingsResponse.data;
      
      const response = await axios.post(`${API}/checkout`, {
        customer_id: selectedCustomer.id,
        additional_amount: parseFloat(checkoutData.additional_amount) || 0,
        discount_amount: parseFloat(checkoutData.discount_amount) || 0,
        payment_method: checkoutData.payment_method
      });
      
      // Store invoice data for printing with latest settings
      setInvoiceData({
        customer: selectedCustomer,
        billing: response.data.billing_details,
        checkout_data: checkoutData,
        hotel_settings: latestSettings  // Include latest settings
      });
      
      setShowCheckoutModal(false);
      setShowPrintInvoiceDialog(true);
      
      // Refresh data after checkout
      await Promise.all([
        fetchRooms(),
        fetchCheckedInCustomers()
      ]);
    } catch (error) {
      console.error('Error during checkout:', error);
      alert('Error during checkout: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle advance payment
  const handleAdvancePayment = (customer) => {
    setSelectedCustomer(customer);
    setAdvancePaymentData({ amount: '', payment_method: 'Cash', notes: '' });
    setShowAdvancePaymentModal(true);
  };

  const confirmAdvancePayment = async () => {
    try {
      await axios.post(`${API}/advance-payment`, {
        customer_id: selectedCustomer.id,
        amount: parseFloat(advancePaymentData.amount) || 0,
        payment_method: advancePaymentData.payment_method,
        notes: advancePaymentData.notes
      });
      
      setShowAdvancePaymentModal(false);
      setSelectedCustomer(null);
      
      // Refresh data after advance payment
      await Promise.all([
        fetchCheckedInCustomers()
      ]);
      
      // Trigger financial refresh across all components
      triggerFinancialRefresh();
      
      alert(`Advance payment of LKR ${advancePaymentData.amount} collected successfully!`);
    } catch (error) {
      console.error('Error collecting advance payment:', error);
      alert('Error collecting advance payment: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle extend stay
  const handleExtendStay = (customer) => {
    setSelectedCustomer(customer);
    // Set default to current checkout date + 1 day
    const currentCheckout = new Date(customer.check_out_date);
    currentCheckout.setDate(currentCheckout.getDate() + 1);
    setExtendStayData({ 
      new_checkout_date: currentCheckout.toISOString().split('T')[0]
    });
    setShowExtendStayModal(true);
  };

  const confirmExtendStay = async () => {
    try {
      const response = await axios.post(`${API}/extend-stay`, {
        customer_id: selectedCustomer.id,
        new_checkout_date: extendStayData.new_checkout_date
      });
      
      setShowExtendStayModal(false);
      setSelectedCustomer(null);
      
      // Refresh data
      await Promise.all([
        fetchCheckedInCustomers(),
        fetchRooms()
      ]);
      
      const details = response.data.details;
      alert(`Stay extended successfully!\n\nAdditional nights: ${details.additional_nights}\nAdditional charges: LKR ${details.additional_charges}\nNew total: LKR ${details.new_room_charges}`);
    } catch (error) {
      console.error('Error extending stay:', error);
      alert('Error extending stay: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle early checkout
  const handleEarlyCheckout = async (customer) => {
    setSelectedCustomer(customer);
    try {
      // Get checkout preview
      const response = await axios.get(`${API}/customer/${customer.id}/checkout-preview`);
      setEarlyCheckoutPreview(response.data);
      setEarlyCheckoutData({
        additional_amount: 0,
        discount_amount: 0,
        payment_method: 'Cash',
        refund_excess: false
      });
      setShowEarlyCheckoutModal(true);
    } catch (error) {
      console.error('Error getting checkout preview:', error);
      alert('Error getting checkout details: ' + (error.response?.data?.detail || error.message));
    }
  };

  const confirmEarlyCheckout = async () => {
    // Calculate the final balance to determine if collection or refund
    const actualRoomCharges = earlyCheckoutPreview.actual_room_charges;
    const restaurantCharges = earlyCheckoutPreview.restaurant_charges || 0;
    const advanceAmount = earlyCheckoutPreview.advance_amount || 0;
    const additionalAmount = parseFloat(earlyCheckoutData.additional_amount) || 0;
    const discountAmount = parseFloat(earlyCheckoutData.discount_amount) || 0;
    
    const totalDue = actualRoomCharges + restaurantCharges + additionalAmount - discountAmount;
    const finalBalance = totalDue - advanceAmount;
    
    // If customer owes money (finalBalance > 0), show payment collection modal
    if (finalBalance > 0) {
      setPaymentCollectionData({
        amount: Math.round(finalBalance),
        payment_method: 'Cash'
      });
      setShowPaymentCollectionModal(true);
      return;
    }
    
    // If customer is owed a refund (finalBalance < 0), proceed with refund
    await processEarlyCheckout(earlyCheckoutData.payment_method, Math.abs(finalBalance));
  };
  
  const processEarlyCheckout = async (paymentMethod, collectionOrRefundAmount) => {
    try {
      const actualRoomCharges = earlyCheckoutPreview.actual_room_charges;
      const restaurantCharges = earlyCheckoutPreview.restaurant_charges || 0;
      const advanceAmount = earlyCheckoutPreview.advance_amount || 0;
      const additionalAmount = parseFloat(earlyCheckoutData.additional_amount) || 0;
      const discountAmount = parseFloat(earlyCheckoutData.discount_amount) || 0;
      
      const totalDue = actualRoomCharges + restaurantCharges + additionalAmount - discountAmount;
      const finalBalance = totalDue - advanceAmount;
      
      const response = await axios.post(`${API}/early-checkout`, {
        customer_id: selectedCustomer.id,
        additional_amount: additionalAmount,
        discount_amount: discountAmount,
        payment_method: paymentMethod,
        refund_excess: true,  // Always refund if applicable
        final_balance: finalBalance,
        collection_amount: finalBalance > 0 ? collectionOrRefundAmount : 0,
        refund_amount: finalBalance < 0 ? Math.abs(finalBalance) : 0
      });
      
      setShowEarlyCheckoutModal(false);
      setShowPaymentCollectionModal(false);
      setSelectedCustomer(null);
      setEarlyCheckoutPreview(null);
      setEarlyCheckoutData({ additional_amount: 0, discount_amount: 0, payment_method: 'Cash' });
      
      // Refresh data
      await Promise.all([
        fetchCheckedInCustomers(),
        fetchRooms()
      ]);
      
      triggerFinancialRefresh();
      
      const billing = response.data.billing_details;
      let message = `Early checkout completed!\n\n`;
      message += `Days early: ${billing.days_early}\n`;
      message += `Final charges: LKR ${Math.round(billing.final_room_charges).toLocaleString()}\n`;
      message += `Total amount: LKR ${Math.round(billing.total_amount).toLocaleString()}`;
      
      if (finalBalance > 0) {
        message += `\n\nCollected: LKR ${Math.round(collectionOrRefundAmount).toLocaleString()} (${paymentMethod})`;
      } else if (finalBalance < 0) {
        message += `\n\nRefund given: LKR ${Math.round(Math.abs(finalBalance)).toLocaleString()} (${paymentMethod})`;
      }
      alert(message);
    } catch (error) {
      console.error('Error processing early checkout:', error);
      alert('Error processing early checkout: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle booking cancellation (admin only)
  const handleCancelBookingForCustomer = async (customer) => {
    if (!window.confirm(`Are you sure you want to cancel the booking for ${customer.name}? This will remove the guest from the room and cannot be undone.`)) {
      return;
    }

    try {
      // Find the booking for this customer
      const allBookingsResponse = await axios.get(`${API}/bookings`);
      const allBookings = allBookingsResponse.data.bookings || [];
      
      const booking = allBookings.find(b => 
        b.guest_name === customer.name && 
        b.room_number === customer.current_room &&
        (b.status === 'Checked-in' || b.status === 'Checked In')
      );
      
      if (booking) {
        await axios.post(`${API}/cancel/${booking.id}`);
        
        // Refresh data after cancellation
        await Promise.all([
          fetchRooms(),
          fetchCheckedInCustomers(),
          fetchUpcomingBookings()
        ]);
        
        alert(`Booking for ${customer.name} has been cancelled successfully.`);
      } else {
        alert('Unable to find the booking record for this customer.');
      }
    } catch (error) {
      console.error('Error cancelling booking:', error);
      alert('Error cancelling booking: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Dropdown toggle functions
  const closeAllCustomerDropdowns = () => {
    setOpenCustomerDropdowns({});
  };

  const toggleCustomerDropdown = (customerId) => {
    setOpenCustomerDropdowns(prev => ({
      ...prev,
      [customerId]: !prev[customerId]
    }));
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
    const restaurantCharges = selectedCustomer.restaurant_charges || 0;
    const advanceAmount = selectedCustomer.advance_amount || 0;
    const additionalAmount = parseFloat(checkoutData.additional_amount) || 0;
    const discountAmount = parseFloat(checkoutData.discount_amount) || 0;
    return roomCharges + restaurantCharges + additionalAmount - advanceAmount - discountAmount;
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

      // Check if check-in date is in the past
      const today = new Date().toISOString().split('T')[0];
      const checkInDate = newBookingData.check_in_date;
      
      if (checkInDate < today) {
        // Past date detected - show status selection dialog
        setShowStatusSelectionModal(true);
        return;
      }

      // Future date - proceed with normal booking creation
      await createBookingWithStatus('Upcoming');
    } catch (error) {
      console.error('Error creating booking:', error);
      alert('Error creating booking. Please try again.');
    }
  };

  const createBookingWithStatus = async (status) => {
    try {
      // Prepare booking data - send the calculated booking_amount to backend
      const bookingData = {
        ...newBookingData,
        booking_amount: newBookingData.booking_amount, // This is the calculated total
        commission_amount: parseFloat(newBookingData.commission_amount) || 0,
        booking_status: status
      };

      // For Short Time bookings, ensure check_out_date is handled correctly
      if (newBookingData.stay_type === 'Short Time') {
        // For short time, don't send check_out_date - let backend handle it
        delete bookingData.check_out_date;
      } else if (bookingData.check_out_date === '') {
        // Convert empty string to null for proper backend handling
        bookingData.check_out_date = null;
      }

      await axios.post(`${API}/bookings`, bookingData);
      
      setShowNewBookingModal(false);
      setShowStatusSelectionModal(false);
      setSelectedBookingStatus('Upcoming');
      setNewBookingData({
        guest_name: '',
        guest_email: '',
        guest_phone: '',
        guest_country: '',
        guest_id_passport: '',
        room_number: '',
        check_in_date: '',
        check_out_date: '',
        stay_type: 'Night Stay',
        rate_per_night: '',
        booking_amount: 0,
        commission_amount: 0,
        booking_channel_id: '',
        booking_channel_name: 'Direct',
        additional_notes: ''
      });
      
      // Refresh data after adding booking
      await Promise.all([
        fetchRooms(),
        fetchUpcomingBookings(),
        fetchCheckedInCustomers() // Also refresh checked-in customers if status was "Checked In"
      ]);
      
      if (status === 'Checked In') {
        alert('Booking created and guest checked in successfully!');
      } else {
        alert('Booking added successfully!');
      }
    } catch (error) {
      console.error('Error creating booking:', error);
      alert('Error creating booking. Please try again.');
    }
  };

  const handleEditBooking = async () => {
    try {
      const response = await axios.put(`${API}/bookings/${selectedBooking.id}`, editBookingData);
      
      setShowEditBookingModal(false);
      setSelectedBooking(null);
      
      // Refresh data after editing booking
      await Promise.all([
        fetchUpcomingBookings(),
        fetchCheckedInCustomers(),
        fetchRooms() // Refresh rooms to update availability
      ]);
      
      // Show specific success message with changes made
      if (response.data.changes && response.data.changes.length > 0) {
        alert(`Booking updated successfully!\n\nChanges made:\n• ${response.data.changes.join('\n• ')}`);
      } else {
        alert('Booking updated successfully!');
      }
    } catch (error) {
      console.error('Error updating booking:', error);
      const errorMessage = error.response?.data?.detail || 'Error updating booking. Please try again.';
      alert(`Failed to update booking:\n\n${errorMessage}`);
    }
  };

  const openEditBookingModal = (booking) => {
    setSelectedBooking(booking);
    setEditBookingData({
      room_number: booking.room_number || '',
      check_in_date: booking.check_in_date,
      check_out_date: booking.check_out_date,
      additional_notes: booking.additional_notes || ''
    });
    
    // Get available rooms for the selected dates (excluding current room)
    const availableRooms = rooms.filter(room => 
      room.status !== 'Occupied' || room.room_number === booking.room_number
    );
    setAvailableRoomsForBooking(availableRooms);
    
    setShowEditBookingModal(true);
  };

  const openNewBookingModal = () => {
    // Initialize with all non-occupied rooms
    setAvailableRoomsForBooking(getAvailableRooms());
    
    // Set default dates: today for check-in, tomorrow for check-out
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const todayStr = today.toISOString().split('T')[0];
    const tomorrowStr = tomorrow.toISOString().split('T')[0];
    
    setNewBookingData(prev => ({
      ...prev,
      check_in_date: todayStr,
      check_out_date: tomorrowStr
    }));
    
    setShowNewBookingModal(true);
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

  const handlePrintInvoice = () => {
    const printWindow = window.open('', '_blank');
    const invoiceHTML = generateInvoiceHTML();
    printWindow.document.write(invoiceHTML);
    printWindow.document.close();
    printWindow.print();
    printWindow.close();
    setShowPrintInvoiceDialog(false);
    setSelectedCustomer(null);
  };

  const generateInvoiceHTML = () => {
    if (!invoiceData) return '';
    
    const { customer, billing, hotel_settings } = invoiceData;
    const settings = hotel_settings || hotelSettings; // Fallback to component settings
    const currentDate = new Date().toLocaleString();
    
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Invoice - ${customer.name}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; color: #333; }
          .header { display: flex; align-items: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }
          .logo { width: 80px; height: 80px; margin-right: 20px; object-fit: contain; }
          .hotel-info h1 { margin: 0; font-size: 24px; color: #2563eb; }
          .hotel-info p { margin: 2px 0; font-size: 14px; color: #666; }
          .invoice-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
          .section { background: #f8f9fa; padding: 15px; border-radius: 8px; }
          .section h3 { margin: 0 0 10px 0; color: #1f2937; font-size: 16px; }
          .billing-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
          .billing-table th, .billing-table td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
          .billing-table th { background: #f3f4f6; font-weight: 600; }
          .total-row { font-weight: bold; background: #dbeafe; }
          .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <div class="header">
          ${settings.hotel_logo ? `<img src="${settings.hotel_logo}" alt="Hotel Logo" class="logo" />` : ''}
          <div class="hotel-info">
            <h1>${settings.hotel_name || 'Hotel Management System'}</h1>
            <p><strong>Address:</strong> ${settings.hotel_address || 'Hotel Address'}</p>
            <p><strong>Phone:</strong> ${settings.hotel_phone || settings.hotel_contact || 'Contact Number'}</p>
            <p><strong>Email:</strong> ${settings.hotel_email || 'hotel@email.com'}</p>
          </div>
        </div>

        <h2 style="text-align: center; color: #1f2937; margin: 20px 0;">CHECKOUT INVOICE</h2>

        <div class="invoice-details">
          <div class="section">
            <h3>Guest Information</h3>
            <p><strong>Name:</strong> ${customer.name}</p>
            <p><strong>Phone:</strong> ${customer.phone || 'N/A'}</p>
            <p><strong>Room:</strong> ${customer.current_room}</p>
            <p><strong>Check-in:</strong> ${customer.check_in_date}</p>
            <p><strong>Check-out:</strong> ${customer.check_out_date}</p>
          </div>
          
          <div class="section">
            <h3>Invoice Details</h3>
            <p><strong>Invoice Date:</strong> ${currentDate}</p>
            <p><strong>Payment Method:</strong> ${billing.payment_method}</p>
            <p><strong>Currency:</strong> ${settings.currency || 'LKR'}</p>
          </div>
        </div>

        <table class="billing-table">
          <thead>
            <tr>
              <th>Description</th>
              <th>Amount (${settings.currency || 'LKR'})</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Room Charges</td>
              <td>${billing.room_charges.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Additional Charges</td>
              <td>${billing.additional_charges.toFixed(2)}</td>
            </tr>
            <tr>
              <td>Advance Amount (Paid)</td>
              <td>(${billing.advance_amount.toFixed(2)})</td>
            </tr>
            <tr>
              <td>Discount</td>
              <td>(${billing.discount_amount.toFixed(2)})</td>
            </tr>
            <tr class="total-row">
              <td><strong>Total Amount</strong></td>
              <td><strong>${billing.total_amount.toFixed(2)}</strong></td>
            </tr>
          </tbody>
        </table>

        <div class="footer">
          <p>Thank you for choosing ${settings.hotel_name || 'our hotel'}!</p>
          <p>This is a computer-generated invoice.</p>
        </div>
      </body>
      </html>
    `;
  };

  const closePrintInvoiceDialog = () => {
    setShowPrintInvoiceDialog(false);
    setSelectedCustomer(null);
    setInvoiceData(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
      <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 sm:mb-8">
        <div className="mb-4 sm:mb-0">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-2">Dashboard</h2>
          <p className="text-sm sm:text-base text-gray-600">Overview of hotel operations and current status</p>
        </div>
        <button
          onClick={openNewBookingModal}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm sm:text-base"
        >
          New Booking
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
      <div className="bg-gray-800 p-4 sm:p-6 rounded-lg shadow mb-6 sm:mb-8">
        <h3 className="text-base sm:text-lg font-semibold text-white mb-4">🔍 Check Room Availability</h3>
        <p className="text-sm text-gray-300 mb-4">Select dates to check which rooms are available for booking</p>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Check-in Date</label>
            <input
              type="date"
              value={availabilityDates.check_in_date}
              onChange={(e) => handleDateChange('check_in_date', e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Check-out Date</label>
            <input
              type="date"
              value={availabilityDates.check_out_date}
              onChange={(e) => handleDateChange('check_out_date', e.target.value)}
              min={availabilityDates.check_in_date || new Date().toISOString().split('T')[0]}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
            />
          </div>
          <div className="flex items-end sm:col-span-2 lg:col-span-1">
            <button
              onClick={checkRoomAvailability}
              disabled={checkingAvailability || !availabilityDates.check_in_date || !availabilityDates.check_out_date}
              className={`w-full px-4 py-2 rounded-md font-medium text-sm ${
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
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Upcoming Bookings</h3>
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 overflow-x-auto" style={{minHeight: '300px'}}>
          {upcomingBookings.length === 0 ? (
            <div className="p-6 text-center text-gray-400">
              No upcoming bookings
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Guest</th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Room</th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider hidden sm:table-cell">Check-in</th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider hidden sm:table-cell">Check-out</th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider hidden md:table-cell">Contact</th>
                  <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {upcomingBookings.map((booking) => (
                  <tr key={booking.id} className="hover:bg-gray-700">
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <div className="text-xs sm:text-sm font-medium text-white">{booking.guest_name}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap">
                      <div className="text-xs sm:text-sm text-white">{booking.room_number}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap hidden sm:table-cell">
                      <div className="text-sm text-white">{booking.check_in_date}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap hidden sm:table-cell">
                      <div className="text-sm text-white">{booking.check_out_date}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap hidden md:table-cell">
                      <div className="text-sm text-white">{booking.guest_phone}</div>
                    </td>
                    <td className="px-3 sm:px-6 py-3 sm:py-4 whitespace-nowrap relative">
                      <button
                        onClick={() => toggleDropdown(booking.id)}
                        className="inline-flex items-center p-1.5 sm:p-2 text-gray-400 bg-gray-700 rounded-full hover:text-gray-200 hover:bg-gray-600"
                      >
                        <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"/>
                        </svg>
                      </button>
                      {openDropdowns[booking.id] && (
                        <div className="absolute right-0 z-50 mt-2 w-48 bg-gray-700 rounded-md shadow-lg ring-1 ring-black ring-opacity-5">
                          <div className="py-1">
                            <button
                              onClick={() => { handleCheckin(booking); closeAllDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                              </svg>
                              Check In
                            </button>
                            <button
                              onClick={() => { openEditBookingModal(booking); closeAllDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                              </svg>
                              Edit
                            </button>
                            <button
                              onClick={() => { handleCancelBooking(booking.id); closeAllDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
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
          )}
        </div>
      </div>

      {/* Checked-in Customers */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-white mb-4">Checked-in Customers</h3>
        <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700">
          {checkedInCustomers.length === 0 ? (
            <div className="p-6 text-center text-gray-400">
              No customers currently checked in
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Customer Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Room</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Check-in Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Check-out Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Contact</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {checkedInCustomers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{customer.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{customer.current_room}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{customer.check_in_date}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{customer.check_out_date}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{customer.phone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap relative">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => handleCheckout(customer)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Checkout
                        </button>
                        <button
                          onClick={() => toggleCustomerDropdown(customer.id)}
                          className="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700 flex items-center"
                        >
                          Actions
                          <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      </div>
                      {openCustomerDropdowns[customer.id] && (
                        <div className="absolute right-0 z-50 mt-2 w-52 bg-gray-700 rounded-md shadow-lg border border-gray-600">
                          <div className="py-1">
                            <button
                              onClick={async () => {
                                try {
                                  const allBookingsResponse = await axios.get(`${API}/bookings`);
                                  const allBookings = allBookingsResponse.data.bookings || [];
                                  const booking = allBookings.find(b => 
                                    b.guest_name === customer.name && 
                                    b.room_number === customer.current_room &&
                                    (b.status === 'Checked-in' || b.status === 'Checked In')
                                  );
                                  if (booking) {
                                    openEditBookingModal(booking);
                                  } else {
                                    alert('Unable to find booking record.');
                                  }
                                  closeAllCustomerDropdowns();
                                } catch (error) {
                                  alert('Error finding booking record.');
                                  closeAllCustomerDropdowns();
                                }
                              }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                              </svg>
                              Edit Booking
                            </button>
                            <button
                              onClick={() => { handleAdvancePayment(customer); closeAllCustomerDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"/>
                              </svg>
                              Get Advance
                            </button>
                            <button
                              onClick={() => { handleExtendStay(customer); closeAllCustomerDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                              </svg>
                              Extend Stay
                            </button>
                            <button
                              onClick={() => { handleEarlyCheckout(customer); closeAllCustomerDropdowns(); }}
                              className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                            >
                              <svg className="w-4 h-4 mr-3 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                              </svg>
                              Early Checkout
                            </button>
                            {user?.role === 'Admin' && (
                              <button
                                onClick={() => { handleCancelBookingForCustomer(customer); closeAllCustomerDropdowns(); }}
                                className="flex w-full px-4 py-2 text-sm text-gray-200 hover:bg-gray-600"
                              >
                                <svg className="w-4 h-4 mr-3 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                </svg>
                                Cancel Booking
                              </button>
                            )}
                          </div>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
                    <span>Restaurant Charges:</span>
                    <span>LKR {selectedCustomer?.restaurant_charges || 0}</span>
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

      {/* Advance Payment Modal */}
      {showAdvancePaymentModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Collect Advance Payment</h3>
            {selectedCustomer && (
              <div className="mb-4 bg-gray-50 p-3 rounded-md">
                <p className="text-sm text-gray-600"><strong>Guest:</strong> {selectedCustomer.name}</p>
                <p className="text-sm text-gray-600"><strong>Room:</strong> {selectedCustomer.current_room}</p>
                <p className="text-sm text-gray-600"><strong>Rate per Night:</strong> LKR {Math.round(selectedCustomer.rate_per_night || 0).toLocaleString()}</p>
                <hr className="my-2" />
                <p className="text-sm text-gray-700"><strong>Room Charges:</strong> LKR {(selectedCustomer.room_charges || 0).toLocaleString()}</p>
                <p className="text-sm text-gray-700"><strong>Restaurant Charges:</strong> LKR {(selectedCustomer.restaurant_charges || 0).toLocaleString()}</p>
                <p className="text-sm text-gray-700"><strong>Total Balance:</strong> LKR {((selectedCustomer.room_charges || 0) + (selectedCustomer.restaurant_charges || 0)).toLocaleString()}</p>
                <hr className="my-2" />
                <p className="text-sm text-green-600"><strong>Advance Paid:</strong> LKR {(selectedCustomer.advance_amount || 0).toLocaleString()}</p>
                <p className="text-sm font-semibold text-blue-700"><strong>Balance Due:</strong> LKR {((selectedCustomer.room_charges || 0) + (selectedCustomer.restaurant_charges || 0) - (selectedCustomer.advance_amount || 0)).toLocaleString()}</p>
              </div>
            )}
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount to Collect *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={advancePaymentData.amount}
                  onChange={(e) => setAdvancePaymentData({...advancePaymentData, amount: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter amount"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Payment Method
                </label>
                <select
                  value={advancePaymentData.payment_method}
                  onChange={(e) => setAdvancePaymentData({...advancePaymentData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Notes (Optional)
                </label>
                <textarea
                  value={advancePaymentData.notes}
                  onChange={(e) => setAdvancePaymentData({...advancePaymentData, notes: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Add any notes about this advance payment"
                  rows="3"
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAdvancePaymentModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmAdvancePayment}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Collect Payment
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Extend Stay Modal */}
      {showExtendStayModal && selectedCustomer && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-purple-700">Extend Stay</h3>
            <div className="mb-4 bg-gray-50 p-3 rounded-md">
              <p className="text-sm text-gray-600"><strong>Guest:</strong> {selectedCustomer.name}</p>
              <p className="text-sm text-gray-600"><strong>Room:</strong> {selectedCustomer.current_room}</p>
              <p className="text-sm text-gray-600"><strong>Check-in:</strong> {selectedCustomer.check_in_date}</p>
              <p className="text-sm text-gray-600"><strong>Current Checkout:</strong> {selectedCustomer.check_out_date}</p>
              <hr className="my-2" />
              <p className="text-sm text-purple-700"><strong>Rate per Night:</strong> LKR {Math.round(selectedCustomer.rate_per_night || 0).toLocaleString()}</p>
              <p className="text-sm text-gray-600"><strong>Current Charges:</strong> LKR {(selectedCustomer.room_charges || 0).toLocaleString()}</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  New Checkout Date *
                </label>
                <input
                  type="date"
                  value={extendStayData.new_checkout_date}
                  min={new Date(new Date(selectedCustomer.check_out_date).getTime() + 86400000).toISOString().split('T')[0]}
                  onChange={(e) => setExtendStayData({...extendStayData, new_checkout_date: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Additional charges will be calculated at LKR {Math.round(selectedCustomer.rate_per_night || 0).toLocaleString()} per night</p>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => { setShowExtendStayModal(false); setSelectedCustomer(null); }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmExtendStay}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
              >
                Extend Stay
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Early Checkout Modal */}
      {showEarlyCheckoutModal && selectedCustomer && earlyCheckoutPreview && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4 text-yellow-700">Early Checkout</h3>
            
            {/* Guest Info */}
            <div className="mb-4 bg-yellow-50 p-3 rounded-md border border-yellow-200">
              <p className="text-sm"><strong>Guest:</strong> {earlyCheckoutPreview.customer_name}</p>
              <p className="text-sm"><strong>Room:</strong> {earlyCheckoutPreview.room_number}</p>
              <p className="text-sm"><strong>Check-in:</strong> {earlyCheckoutPreview.check_in_date}</p>
              <p className="text-sm"><strong>Planned Checkout:</strong> {earlyCheckoutPreview.planned_checkout_date}</p>
              <p className="text-sm"><strong>Actual Checkout:</strong> {earlyCheckoutPreview.actual_checkout_date} <span className="text-yellow-600 font-medium">({earlyCheckoutPreview.days_early} days early)</span></p>
            </div>
            
            {/* Charges Breakdown */}
            <div className="mb-4 bg-gray-50 p-3 rounded-md">
              <h4 className="font-medium mb-2">Charges Breakdown</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Actual nights stayed:</span>
                  <span>{earlyCheckoutPreview.actual_nights} nights × LKR {Math.round(earlyCheckoutPreview.price_per_night).toLocaleString()}</span>
                </div>
                <div className="flex justify-between font-medium">
                  <span>Room charges:</span>
                  <span>LKR {Math.round(earlyCheckoutPreview.actual_room_charges).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Restaurant charges:</span>
                  <span>LKR {Math.round(earlyCheckoutPreview.restaurant_charges || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Additional charges:</span>
                  <span>LKR {Math.round(parseFloat(earlyCheckoutData.additional_amount) || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-red-600">
                  <span>Discount:</span>
                  <span>-LKR {Math.round(parseFloat(earlyCheckoutData.discount_amount) || 0).toLocaleString()}</span>
                </div>
                <hr className="my-2" />
                <div className="flex justify-between font-medium">
                  <span>Total Due:</span>
                  <span>LKR {Math.round(
                    earlyCheckoutPreview.actual_room_charges + 
                    (earlyCheckoutPreview.restaurant_charges || 0) + 
                    (parseFloat(earlyCheckoutData.additional_amount) || 0) - 
                    (parseFloat(earlyCheckoutData.discount_amount) || 0)
                  ).toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-green-600">
                  <span>Advance paid:</span>
                  <span>-LKR {Math.round(earlyCheckoutPreview.advance_amount || 0).toLocaleString()}</span>
                </div>
              </div>
            </div>
            
            {/* Final Balance - Collection or Refund */}
            {(() => {
              const totalDue = earlyCheckoutPreview.actual_room_charges + 
                (earlyCheckoutPreview.restaurant_charges || 0) + 
                (parseFloat(earlyCheckoutData.additional_amount) || 0) - 
                (parseFloat(earlyCheckoutData.discount_amount) || 0);
              const advancePaid = earlyCheckoutPreview.advance_amount || 0;
              const finalBalance = totalDue - advancePaid;
              
              if (finalBalance > 0) {
                return (
                  <div className="mb-4 bg-blue-50 p-4 rounded-md border border-blue-200">
                    <div className="text-center">
                      <p className="text-sm text-blue-600 mb-1">Amount to Collect</p>
                      <p className="text-2xl font-bold text-blue-700">LKR {Math.round(finalBalance).toLocaleString()}</p>
                      <p className="text-xs text-gray-500 mt-1">Customer owes this amount</p>
                    </div>
                  </div>
                );
              } else if (finalBalance < 0) {
                return (
                  <div className="mb-4 bg-green-50 p-4 rounded-md border border-green-200">
                    <div className="text-center">
                      <p className="text-sm text-green-600 mb-1">Refund Due</p>
                      <p className="text-2xl font-bold text-green-700">LKR {Math.round(Math.abs(finalBalance)).toLocaleString()}</p>
                      <p className="text-xs text-gray-500 mt-1">Customer has overpaid</p>
                    </div>
                  </div>
                );
              } else {
                return (
                  <div className="mb-4 bg-gray-100 p-4 rounded-md border border-gray-200">
                    <div className="text-center">
                      <p className="text-sm text-gray-600 mb-1">Balance</p>
                      <p className="text-2xl font-bold text-gray-700">LKR 0</p>
                      <p className="text-xs text-gray-500 mt-1">No collection or refund needed</p>
                    </div>
                  </div>
                );
              }
            })()}
            
            {/* Additional Options */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Additional Charges</label>
                  <input
                    type="number"
                    step="0.01"
                    value={earlyCheckoutData.additional_amount}
                    onChange={(e) => setEarlyCheckoutData({...earlyCheckoutData, additional_amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="0.00"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Discount</label>
                  <input
                    type="number"
                    step="0.01"
                    value={earlyCheckoutData.discount_amount}
                    onChange={(e) => setEarlyCheckoutData({...earlyCheckoutData, discount_amount: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    placeholder="0.00"
                  />
                </div>
              </div>
              
              {/* Payment method - only show for refunds */}
              {(() => {
                const totalDue = earlyCheckoutPreview.actual_room_charges + 
                  (earlyCheckoutPreview.restaurant_charges || 0) + 
                  (parseFloat(earlyCheckoutData.additional_amount) || 0) - 
                  (parseFloat(earlyCheckoutData.discount_amount) || 0);
                const advancePaid = earlyCheckoutPreview.advance_amount || 0;
                const finalBalance = totalDue - advancePaid;
                
                if (finalBalance < 0) {
                  return (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Refund Method</label>
                      <select
                        value={earlyCheckoutData.payment_method}
                        onChange={(e) => setEarlyCheckoutData({...earlyCheckoutData, payment_method: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md"
                      >
                        <option value="Cash">Cash</option>
                        <option value="Bank Transfer">Bank Transfer</option>
                      </select>
                    </div>
                  );
                }
                return null;
              })()}
            </div>
            
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => { setShowEarlyCheckoutModal(false); setSelectedCustomer(null); setEarlyCheckoutPreview(null); }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={confirmEarlyCheckout}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
              >
                Confirm Early Checkout
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Payment Collection Modal (for early checkout when customer owes money) */}
      {showPaymentCollectionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-sm">
            <h3 className="text-lg font-semibold mb-4 text-blue-700">Collect Payment</h3>
            <div className="mb-4 bg-blue-50 p-4 rounded-md border border-blue-200">
              <p className="text-center">
                <span className="text-sm text-blue-600">Amount to Collect</span><br />
                <span className="text-2xl font-bold text-blue-700">LKR {paymentCollectionData.amount.toLocaleString()}</span>
              </p>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                <select
                  value={paymentCollectionData.payment_method}
                  onChange={(e) => setPaymentCollectionData({...paymentCollectionData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                >
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowPaymentCollectionModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => processEarlyCheckout(paymentCollectionData.payment_method, paymentCollectionData.amount)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Confirm Collection
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
                
                {/* Booking Channel Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Booking Channel *
                  </label>
                  <select
                    value={newBookingData.booking_channel_id}
                    onChange={(e) => {
                      const selectedChannel = availableChannels.find(ch => ch.id === e.target.value);
                      setNewBookingData({
                        ...newBookingData, 
                        booking_channel_id: e.target.value,
                        booking_channel_name: selectedChannel ? selectedChannel.channel_name : 'Direct'
                      });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Direct</option>
                    {availableChannels.map((channel) => (
                      <option key={channel.id} value={channel.id}>
                        {channel.channel_name} {channel.commission_rate > 0 && `(${channel.commission_rate}% commission)`}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Select the booking source (Direct, OTA, Corporate, etc.)
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
                      {(availableRoomsForBooking.length > 0 ? availableRoomsForBooking : getAvailableRooms()).map((room) => (
                        <option key={room.id} value={room.room_number}>
                          {room.room_number}
                        </option>
                      ))}
                    </select>
                    {newBookingData.check_in_date && availableRoomsForBooking.length === 0 && (
                      <p className="text-xs text-orange-600 mt-1">
                        Select dates first to see available rooms for those dates
                      </p>
                    )}
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
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Commission (LKR)
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={newBookingData.commission_amount}
                      onChange={(e) => setNewBookingData({...newBookingData, commission_amount: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="Commission payable to channel"
                    />
                    <p className="text-xs text-gray-500 mt-1">Commission payable to booking channel</p>
                  </div>
                  
                  {/* Show calculated total */}
                  {newBookingData.booking_amount > 0 && (
                    <div className="col-span-2 bg-blue-50 border border-blue-200 rounded-lg p-3">
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
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600">Guest: <strong>{selectedBooking.guest_name}</strong></p>
                <p className="text-sm text-gray-600">Current Room: <strong>{selectedBooking.room_number}</strong></p>
                <p className="text-sm text-gray-500">Status: <strong>{selectedBooking.status}</strong></p>
                <hr className="my-2" />
                <p className="text-sm text-blue-700">
                  <strong>Rate per Night:</strong> LKR {(() => {
                    const checkin = new Date(selectedBooking.check_in_date);
                    const checkout = new Date(selectedBooking.check_out_date);
                    const nights = Math.max(1, Math.ceil((checkout - checkin) / (1000 * 60 * 60 * 24)));
                    const rate = (selectedBooking.booking_amount || 0) / nights;
                    return Math.round(rate).toLocaleString();
                  })()}
                </p>
                <p className="text-sm text-gray-600"><strong>Current Amount:</strong> LKR {(selectedBooking.booking_amount || 0).toLocaleString()}</p>
              </div>
            )}
            
            <div className="space-y-4">
              {/* Room Selection - Only for Upcoming bookings */}
              {selectedBooking && selectedBooking.status === 'Upcoming' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    🏠 Change Room Number
                  </label>
                  <select
                    value={editBookingData.room_number}
                    onChange={(e) => setEditBookingData({...editBookingData, room_number: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a room</option>
                    {availableRoomsForBooking.map((room) => (
                      <option key={room.room_number} value={room.room_number}>
                        Room {room.room_number} - {room.room_type} ({room.status})
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-green-600 mt-1">
                    ℹ️ Room can only be changed for upcoming bookings
                  </p>
                </div>
              )}
              
              {/* Show warning for non-upcoming bookings */}
              {selectedBooking && selectedBooking.status !== 'Upcoming' && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    ⚠️ Room number cannot be changed for bookings with status: <strong>{selectedBooking.status}</strong>
                  </p>
                  <p className="text-xs text-yellow-600 mt-1">
                    Only upcoming bookings can have room changes.
                  </p>
                </div>
              )}
              
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
                {selectedBooking && selectedBooking.status === 'Upcoming' ? '💾 Save Changes' : '💾 Update Details'}
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
                          openNewBookingModal();
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

      {/* Status Selection Modal for Past Date Bookings */}
      {showStatusSelectionModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Past Date Booking Detected</h3>
            <p className="text-gray-700 mb-4">
              You're creating a booking with a past check-in date. Please choose how you'd like to add this booking:
            </p>
            
            <div className="space-y-3 mb-6">
              <div className="flex items-start space-x-3">
                <input
                  type="radio"
                  id="upcoming"
                  name="booking_status"
                  value="Upcoming"
                  checked={selectedBookingStatus === 'Upcoming'}
                  onChange={(e) => setSelectedBookingStatus(e.target.value)}
                  className="mt-1"
                />
                <div>
                  <label htmlFor="upcoming" className="font-medium text-gray-900 cursor-pointer">
                    Add as Upcoming Booking
                  </label>
                  <p className="text-sm text-gray-600">
                    The booking will appear in the "Upcoming Bookings" section and you can check the guest in later.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <input
                  type="radio"
                  id="checked_in"
                  name="booking_status"
                  value="Checked In"
                  checked={selectedBookingStatus === 'Checked In'}
                  onChange={(e) => setSelectedBookingStatus(e.target.value)}
                  className="mt-1"
                />
                <div>
                  <label htmlFor="checked_in" className="font-medium text-gray-900 cursor-pointer">
                    Add as Checked In Customer
                  </label>
                  <p className="text-sm text-gray-600">
                    The guest will immediately appear in the "Checked In Customers" section and the room will be marked as occupied.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowStatusSelectionModal(false);
                  setSelectedBookingStatus('Upcoming');
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => createBookingWithStatus(selectedBookingStatus)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Create Booking
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Print Invoice Dialog */}
      {showPrintInvoiceDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-white">Checkout Complete!</h3>
            
            <p className="text-gray-300 mb-6">
              Customer has been successfully checked out. Would you like to print the invoice?
            </p>
            
            <div className="flex justify-end space-x-3">
              <button
                onClick={closePrintInvoiceDialog}
                className="px-4 py-2 text-gray-300 border border-gray-600 rounded-md hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handlePrintInvoice}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors flex items-center space-x-2"
              >
                <span>🖨️</span>
                <span>Print Invoice</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Commissions Component
const Commissions = () => {
  const [commissionSummary, setCommissionSummary] = useState(null);
  const [monthlyBreakdown, setMonthlyBreakdown] = useState(null);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedChannel, setSelectedChannel] = useState(null);
  const [channelDetails, setChannelDetails] = useState(null);

  const months = [
    { value: null, label: 'All Months' },
    { value: 1, label: 'January' },
    { value: 2, label: 'February' },
    { value: 3, label: 'March' },
    { value: 4, label: 'April' },
    { value: 5, label: 'May' },
    { value: 6, label: 'June' },
    { value: 7, label: 'July' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'October' },
    { value: 11, label: 'November' },
    { value: 12, label: 'December' }
  ];

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - i);

  useEffect(() => {
    fetchCommissionData();
  }, [selectedYear, selectedMonth]);

  const fetchCommissionData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('year', selectedYear);
      if (selectedMonth) params.append('month', selectedMonth);

      const [summaryRes, breakdownRes] = await Promise.all([
        axios.get(`${API}/commissions/summary?${params.toString()}`),
        axios.get(`${API}/commissions/monthly-breakdown?year=${selectedYear}`)
      ]);

      setCommissionSummary(summaryRes.data);
      setMonthlyBreakdown(breakdownRes.data);
    } catch (error) {
      console.error('Error fetching commission data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchChannelDetails = async (channelId, channelName) => {
    try {
      const params = new URLSearchParams();
      params.append('year', selectedYear);
      if (selectedMonth) params.append('month', selectedMonth);

      const response = await axios.get(`${API}/commissions/channel-details/${channelId}?${params.toString()}`);
      setChannelDetails(response.data);
      setSelectedChannel(channelName);
    } catch (error) {
      console.error('Error fetching channel details:', error);
    }
  };

  const formatCurrency = (amount) => {
    return `LKR ${(amount || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  if (loading) {
    return (
      <div className="p-6 min-h-screen bg-gray-900">
        <div className="flex justify-center items-center h-64">
          <div className="text-white">Loading commission data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 min-h-screen bg-gray-900">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-800 to-indigo-800 rounded-lg p-6 mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">Commission Tracking</h2>
        <p className="text-purple-200">Track and manage booking channel commissions</p>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Year</label>
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="bg-gray-700 text-white px-4 py-2 rounded-md border border-gray-600 focus:ring-2 focus:ring-purple-500"
            >
              {years.map(year => (
                <option key={year} value={year}>{year}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Month</label>
            <select
              value={selectedMonth || ''}
              onChange={(e) => setSelectedMonth(e.target.value ? parseInt(e.target.value) : null)}
              className="bg-gray-700 text-white px-4 py-2 rounded-md border border-gray-600 focus:ring-2 focus:ring-purple-500"
            >
              {months.map(month => (
                <option key={month.value || 'all'} value={month.value || ''}>{month.label}</option>
              ))}
            </select>
          </div>
          <div className="ml-auto">
            <div className="text-sm text-gray-400">Grand Total Payable</div>
            <div className="text-2xl font-bold text-purple-400">
              {formatCurrency(commissionSummary?.grand_total)}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channel Summary */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Commission by Channel</h3>
          {commissionSummary?.channels?.length > 0 ? (
            <div className="space-y-3">
              {commissionSummary.channels.map((channel, index) => (
                <div 
                  key={index}
                  onClick={() => channel.channel_id && fetchChannelDetails(channel.channel_id, channel.channel_name)}
                  className={`bg-gray-700 rounded-lg p-4 ${channel.channel_id ? 'cursor-pointer hover:bg-gray-600 transition-colors' : ''}`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="text-white font-medium">{channel.channel_name}</div>
                      <div className="text-sm text-gray-400">{channel.booking_count} booking(s)</div>
                    </div>
                    <div className="text-right">
                      <div className="text-purple-400 font-semibold">{formatCurrency(channel.total_commission)}</div>
                      <div className="text-xs text-gray-500">from {formatCurrency(channel.total_booking_amount)}</div>
                    </div>
                  </div>
                  {/* Progress bar showing percentage of total */}
                  <div className="mt-2 bg-gray-600 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(channel.total_commission / (commissionSummary.grand_total || 1)) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-400 text-center py-8">
              No commission data for selected period
            </div>
          )}
        </div>

        {/* Monthly Breakdown */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Monthly Breakdown - {selectedYear}</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 text-gray-400 font-medium">Month</th>
                  <th className="text-right py-2 text-gray-400 font-medium">Commission</th>
                </tr>
              </thead>
              <tbody>
                {monthlyBreakdown?.monthly_breakdown?.map((month) => (
                  <tr 
                    key={month.month} 
                    className={`border-b border-gray-700 hover:bg-gray-700 cursor-pointer ${
                      month.total > 0 ? '' : 'opacity-50'
                    }`}
                    onClick={() => setSelectedMonth(month.month)}
                  >
                    <td className="py-3 text-white">{month.month_name}</td>
                    <td className="py-3 text-right">
                      <span className={month.total > 0 ? 'text-purple-400 font-medium' : 'text-gray-500'}>
                        {formatCurrency(month.total)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="border-t-2 border-gray-600">
                  <td className="py-3 text-white font-semibold">Year Total</td>
                  <td className="py-3 text-right text-purple-400 font-bold">
                    {formatCurrency(monthlyBreakdown?.year_total)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      {/* Channel Details Modal */}
      {selectedChannel && channelDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-xl font-semibold text-white">{selectedChannel} - Commission Details</h3>
                <p className="text-sm text-gray-400">
                  {selectedMonth ? months.find(m => m.value === selectedMonth)?.label : 'All Months'} {selectedYear}
                </p>
              </div>
              <button
                onClick={() => { setSelectedChannel(null); setChannelDetails(null); }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400">Total Bookings</div>
                <div className="text-2xl font-bold text-white">{channelDetails.booking_count}</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400">Total Commission</div>
                <div className="text-2xl font-bold text-purple-400">{formatCurrency(channelDetails.total_commission)}</div>
              </div>
              <div className="bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-400">Status</div>
                <div className="text-xl font-bold text-yellow-400">Payable</div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-2 text-gray-400 font-medium">Guest</th>
                    <th className="text-left py-2 text-gray-400 font-medium">Room</th>
                    <th className="text-left py-2 text-gray-400 font-medium">Check-in</th>
                    <th className="text-right py-2 text-gray-400 font-medium">Booking Amt</th>
                    <th className="text-right py-2 text-gray-400 font-medium">Commission</th>
                    <th className="text-center py-2 text-gray-400 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {channelDetails.bookings?.map((booking) => (
                    <tr key={booking.id} className="border-b border-gray-700 hover:bg-gray-700">
                      <td className="py-3 text-white">{booking.guest_name}</td>
                      <td className="py-3 text-gray-300">{booking.room_number}</td>
                      <td className="py-3 text-gray-300">{booking.check_in_date}</td>
                      <td className="py-3 text-right text-gray-300">{formatCurrency(booking.booking_amount)}</td>
                      <td className="py-3 text-right text-purple-400 font-medium">{formatCurrency(booking.commission_amount)}</td>
                      <td className="py-3 text-center">
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          booking.status === 'Completed' ? 'bg-green-900 text-green-300' :
                          booking.status === 'Checked In' ? 'bg-blue-900 text-blue-300' :
                          booking.status === 'Cancelled' ? 'bg-red-900 text-red-300' :
                          'bg-yellow-900 text-yellow-300'
                        }`}>
                          {booking.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex justify-end mt-6">
              <button
                onClick={() => { setSelectedChannel(null); setChannelDetails(null); }}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-500"
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

  const handleDownloadDailyReport = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      const response = await axios.get(`${API}/financial-reports/daily?date=${today}`);
      const reportData = response.data;
      
      // Create workbook with multiple sheets
      const wb = XLSX.utils.book_new();
      
      // Summary Sheet
      const summaryData = [
        { "DAILY FINANCIAL REPORT": `Date: ${reportData.date}`, "": "" },
        { "DAILY FINANCIAL REPORT": "", "": "" },
        { "DAILY FINANCIAL REPORT": "INCOME SUMMARY", "": "" },
        { "DAILY FINANCIAL REPORT": "Cash Income (LKR)", "": reportData.summary["Cash Income (LKR)"] },
        { "DAILY FINANCIAL REPORT": "Bank Income (LKR)", "": reportData.summary["Bank Income (LKR)"] },
        { "DAILY FINANCIAL REPORT": "Total Income (LKR)", "": reportData.summary["Total Income (LKR)"] },
        { "DAILY FINANCIAL REPORT": "", "": "" },
        { "DAILY FINANCIAL REPORT": "EXPENSE SUMMARY", "": "" },
        { "DAILY FINANCIAL REPORT": "Cash Expenses (LKR)", "": reportData.summary["Cash Expenses (LKR)"] },
        { "DAILY FINANCIAL REPORT": "Bank Expenses (LKR)", "": reportData.summary["Bank Expenses (LKR)"] },
        { "DAILY FINANCIAL REPORT": "Total Expenses (LKR)", "": reportData.summary["Total Expenses (LKR)"] },
        { "DAILY FINANCIAL REPORT": "", "": "" },
        { "DAILY FINANCIAL REPORT": "BALANCE SUMMARY", "": "" },
        { "DAILY FINANCIAL REPORT": "Net Cash Balance (LKR)", "": reportData.cash_balance },
        { "DAILY FINANCIAL REPORT": "Net Bank Balance (LKR)", "": reportData.bank_balance },
        { "DAILY FINANCIAL REPORT": "Total Net Balance (LKR)", "": reportData.total_balance }
      ];
      
      const summaryWs = XLSX.utils.json_to_sheet(summaryData);
      
      // Style the summary sheet
      summaryWs['!cols'] = [
        { width: 30 }, // Column A
        { width: 20 }  // Column B
      ];
      
      XLSX.utils.book_append_sheet(wb, summaryWs, '📊 Summary');
      
      // Income Details Sheet
      if (reportData.income_details && reportData.income_details.length > 0) {
        const incomeWs = XLSX.utils.json_to_sheet(reportData.income_details);
        incomeWs['!cols'] = [
          { width: 18 }, // Date
          { width: 25 }, // Guest Name
          { width: 15 }, // Category
          { width: 35 }, // Description
          { width: 15 }, // Amount
          { width: 15 }, // Payment Method
          { width: 18 }, // Channel
          { width: 20 }  // Added By
        ];
        XLSX.utils.book_append_sheet(wb, incomeWs, '💰 Income Details');
      }
      
      // Expense Details Sheet
      if (reportData.expense_details && reportData.expense_details.length > 0) {
        const expenseWs = XLSX.utils.json_to_sheet(reportData.expense_details);
        expenseWs['!cols'] = [
          { width: 18 }, // Date
          { width: 15 }, // Category
          { width: 35 }, // Description
          { width: 15 }, // Amount
          { width: 15 }, // Payment Method
          { width: 20 }  // Added By
        ];
        XLSX.utils.book_append_sheet(wb, expenseWs, '💸 Expense Details');
      }
      
      // Download the file
      XLSX.writeFile(wb, `Daily_Financial_Report_${reportData.date}.xlsx`);
      
    } catch (error) {
      console.error('Error downloading daily report:', error);
      alert('Error downloading daily report: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDownloadMonthlyReport = async () => {
    try {
      const today = new Date();
      const year = today.getFullYear();
      const month = today.getMonth() + 1;
      
      const response = await axios.get(`${API}/financial-reports/monthly?year=${year}&month=${month}`);
      const reportData = response.data;
      
      // Create workbook with multiple sheets
      const wb = XLSX.utils.book_new();
      
      // Summary Sheet
      const summaryData = [
        { "MONTHLY FINANCIAL REPORT": `Month: ${reportData.month}`, "": "" },
        { "MONTHLY FINANCIAL REPORT": "", "": "" },
        { "MONTHLY FINANCIAL REPORT": "INCOME SUMMARY", "": "" },
        { "MONTHLY FINANCIAL REPORT": "Cash Income (LKR)", "": reportData.summary["Cash Income (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "Bank Income (LKR)", "": reportData.summary["Bank Income (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "Total Income (LKR)", "": reportData.summary["Total Income (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "", "": "" },
        { "MONTHLY FINANCIAL REPORT": "EXPENSE SUMMARY", "": "" },
        { "MONTHLY FINANCIAL REPORT": "Cash Expenses (LKR)", "": reportData.summary["Cash Expenses (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "Bank Expenses (LKR)", "": reportData.summary["Bank Expenses (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "Total Expenses (LKR)", "": reportData.summary["Total Expenses (LKR)"] },
        { "MONTHLY FINANCIAL REPORT": "", "": "" },
        { "MONTHLY FINANCIAL REPORT": "BALANCE SUMMARY", "": "" },
        { "MONTHLY FINANCIAL REPORT": "Net Cash Balance (LKR)", "": reportData.cash_balance },
        { "MONTHLY FINANCIAL REPORT": "Net Bank Balance (LKR)", "": reportData.bank_balance },
        { "MONTHLY FINANCIAL REPORT": "Total Net Balance (LKR)", "": reportData.total_balance }
      ];
      
      const summaryWs = XLSX.utils.json_to_sheet(summaryData);
      
      // Style the summary sheet
      summaryWs['!cols'] = [
        { width: 30 }, // Column A
        { width: 20 }  // Column B
      ];
      
      XLSX.utils.book_append_sheet(wb, summaryWs, '📊 Summary');
      
      // Income Details Sheet
      if (reportData.income_details && reportData.income_details.length > 0) {
        const incomeWs = XLSX.utils.json_to_sheet(reportData.income_details);
        incomeWs['!cols'] = [
          { width: 18 }, // Date
          { width: 25 }, // Guest Name
          { width: 15 }, // Category
          { width: 35 }, // Description
          { width: 15 }, // Amount
          { width: 15 }, // Payment Method
          { width: 18 }, // Channel
          { width: 20 }  // Added By
        ];
        XLSX.utils.book_append_sheet(wb, incomeWs, '💰 Income Details');
      }
      
      // Expense Details Sheet
      if (reportData.expense_details && reportData.expense_details.length > 0) {
        const expenseWs = XLSX.utils.json_to_sheet(reportData.expense_details);
        expenseWs['!cols'] = [
          { width: 18 }, // Date
          { width: 15 }, // Category
          { width: 35 }, // Description
          { width: 15 }, // Amount
          { width: 15 }, // Payment Method
          { width: 20 }  // Added By
        ];
        XLSX.utils.book_append_sheet(wb, expenseWs, '💸 Expense Details');
      }
      
      // Download the file
      const monthName = reportData.month.replace(' ', '_');
      XLSX.writeFile(wb, `Monthly_Financial_Report_${monthName}.xlsx`);
      
    } catch (error) {
      console.error('Error downloading monthly report:', error);
      alert('Error downloading monthly report: ' + (error.response?.data?.detail || error.message));
    }
  };

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
          <h2 className="text-2xl font-bold text-white mb-2">Reports & Analytics</h2>
          <p className="text-gray-300">Financial performance and business insights</p>
        </div>
        <div className="flex items-center space-x-4">
          {/* View Toggle */}
          <div className="flex space-x-2">
            <button
              onClick={() => setSelectedView('daily')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                selectedView === 'daily' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Daily View
            </button>
            <button
              onClick={() => setSelectedView('monthly')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                selectedView === 'monthly' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Monthly View
            </button>
            <button
              onClick={() => setSelectedView('comparison')}
              className={`px-4 py-2 rounded-md text-sm font-medium ${
                selectedView === 'comparison' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              Comparison
            </button>
          </div>
          
          {/* Download Buttons */}
          <div className="flex space-x-2">
            <button
              onClick={handleDownloadDailyReport}
              className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 flex items-center space-x-2"
            >
              <span>📊</span>
              <span>Daily Report</span>
            </button>
            <button
              onClick={handleDownloadMonthlyReport}
              className="bg-purple-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-purple-700 flex items-center space-x-2"
            >
              <span>📈</span>
              <span>Monthly Report</span>
            </button>
          </div>
        </div>
      </div>

      {selectedView === 'daily' && (
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-white mb-4">Daily Income & Expenses (Last 7 Days)</h3>
          <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Revenue
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Expenses
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Net Profit
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Bookings
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Expense Items
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {getRecentDailyData().map((day) => (
                    <tr key={day.date} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">
                          {new Date(day.date).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-green-400">
                          {formatCurrency(day.revenue)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-red-400">
                          {formatCurrency(day.expenses)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className={`text-sm font-bold ${
                          day.profit >= 0 ? 'text-blue-400' : 'text-orange-400'
                        }`}>
                          {formatCurrency(day.profit)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{day.bookings_count}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{day.expenses_count}</div>
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
          <h3 className="text-lg font-semibold text-white mb-4">Monthly Performance Data</h3>
          <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700">
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
  const [viewMode, setViewMode] = useState('daily'); // 'daily' or 'monthly'
  
  // Get financial context for cross-component refresh
  const { refreshTrigger } = useFinancial();
  
  // Pagination state
  const [roomBookingsPage, setRoomBookingsPage] = useState(1);
  const [additionalIncomePage, setAdditionalIncomePage] = useState(1);
  const [expensePage, setExpensePage] = useState(1);
  const itemsPerPage = 10;
  
  const [expenseData, setExpenseData] = useState({
    description: '',
    amount: 0,
    category: '',
    payment_method: 'Cash',
    expense_date: ''
  });
  const [incomeData, setIncomeData] = useState({
    description: '',
    amount: 0,
    category: '',
    payment_method: 'Cash',
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

  const paymentMethods = ['Cash', 'Card', 'Bank Transfer'];

  useEffect(() => {
    fetchExpenses();
    fetchIncomes();
    fetchDailySales();
    fetchFinancialSummary();
    fetchDailyFinancialSummary();
  }, []);

  // Listen for financial refresh triggers from other components
  useEffect(() => {
    if (refreshTrigger > 0) {
      fetchDailyFinancialSummary();
      fetchFinancialSummary();
    }
  }, [refreshTrigger]);

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
        payment_method: 'Cash',
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
        payment_method: 'Cash',
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
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Income & Expenses</h2>
          <p className="text-gray-300">Financial management and balance tracking</p>
        </div>
      </div>

      {/* Financial Summary Cards */}
      {dailyFinancialSummary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-green-900 border border-green-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-300 mb-2">Total Revenue</h3>
            <p className="text-3xl font-bold text-green-100">LKR {dailyFinancialSummary.total_revenue.toFixed(2)}</p>
            <p className="text-sm text-green-400">Today ({new Date(dailyFinancialSummary.date).toLocaleDateString()})</p>
          </div>
          <div className="bg-red-900 border border-red-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-300 mb-2">Total Expenses</h3>
            <p className="text-3xl font-bold text-red-100">LKR {dailyFinancialSummary.total_expenses.toFixed(2)}</p>
            <p className="text-sm text-red-400">Today ({new Date(dailyFinancialSummary.date).toLocaleDateString()})</p>
          </div>
          <div className="bg-blue-900 border border-blue-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-300 mb-2">Cash Balance</h3>
            <p className="text-3xl font-bold text-blue-100">LKR {dailyFinancialSummary.cash_balance.toFixed(2)}</p>
            <p className="text-sm text-blue-400">Running balance</p>
          </div>
          <div className="bg-purple-900 border border-purple-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-300 mb-2">Bank Balance</h3>
            <p className="text-3xl font-bold text-purple-100">LKR {dailyFinancialSummary.bank_balance.toFixed(2)}</p>
            <p className="text-sm text-purple-400">Card + Bank Transfer</p>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4 mb-8">
        <button 
          onClick={() => setShowAddIncomeModal(true)}
          className="bg-green-600 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-green-700 flex items-center space-x-2"
        >
          <span>+</span>
          <span>Add Income</span>
        </button>
        <button 
          onClick={() => setShowAddExpenseModal(true)}
          className="bg-red-600 text-white px-6 py-3 rounded-md text-sm font-medium hover:bg-red-700 flex items-center space-x-2"
        >
          <span>+</span>
          <span>Add Expense</span>
        </button>
      </div>

      {/* Expenses Table */}
      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700 mb-8">
        <div className="px-6 py-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">Expense Records</h3>
        </div>
        {expenses.length === 0 ? (
          <div className="p-6 text-center text-gray-400">
            No expenses recorded
          </div>
        ) : (
          <div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Category
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Created By
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {getPaginatedData(expenses, expensePage).map((expense) => (
                    <tr key={expense.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{expense.description}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-bold text-red-400">LKR {expense.amount.toFixed(2)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(expense.category)}`}>
                          {expense.category}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{expense.expense_date}</div>
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Income Records</h3>
        
        {/* Room Bookings Income */}
        <div className="mb-6">
          <h4 className="text-md font-medium text-green-800 dark:text-green-400 mb-3">Room Bookings</h4>
          {dailySales && dailySales.length > 0 ? (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-green-50 dark:bg-green-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 dark:text-green-300 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 dark:text-green-300 uppercase tracking-wider">Guest</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 dark:text-green-300 uppercase tracking-wider">Room</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 dark:text-green-300 uppercase tracking-wider">Payment Method</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-green-800 dark:text-green-300 uppercase tracking-wider">Amount</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {getPaginatedData(dailySales, roomBookingsPage).map((sale, index) => (
                      <tr key={index}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">
                            {new Date(sale.date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">{sale.customer_name}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">{sale.room_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">{sale.payment_method}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-green-600 dark:text-green-400">LKR {sale.total_amount.toFixed(2)}</div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {renderPagination(dailySales, roomBookingsPage, setRoomBookingsPage)}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              No room booking income recorded
            </div>
          )}
        </div>

        {/* Additional Income */}
        <div>
          <h4 className="text-md font-medium text-blue-800 dark:text-blue-400 mb-3">Additional Income</h4>
          {incomes && incomes.length > 0 ? (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-blue-50 dark:bg-blue-900">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 dark:text-blue-300 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 dark:text-blue-300 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 dark:text-blue-300 uppercase tracking-wider">Category</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 dark:text-blue-300 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-blue-800 dark:text-blue-300 uppercase tracking-wider">Action</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {getPaginatedData(incomes, additionalIncomePage).map((income, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">
                            {new Date(income.income_date).toLocaleDateString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900 dark:text-gray-300">{income.description}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-700 dark:text-gray-400">{income.category}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-bold text-green-600 dark:text-green-400">LKR {income.amount.toFixed(2)}</div>
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
            <div className="text-center py-8 text-gray-400">
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
                  required
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
                  Payment Method *
                </label>
                <select
                  value={expenseData.payment_method}
                  onChange={(e) => setExpenseData({...expenseData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  {paymentMethods.map(method => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  This will deduct from {expenseData.payment_method === 'Cash' ? 'Cash Balance' : 'Bank Balance'}
                </p>
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
                  required
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
                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method *</label>
                <select
                  value={incomeData.payment_method}
                  onChange={(e) => setIncomeData({...incomeData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                >
                  {paymentMethods.map(method => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  This will add to {incomeData.payment_method === 'Cash' ? 'Cash Balance' : 'Bank Balance'}
                </p>
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
  const [showEditGuestModal, setShowEditGuestModal] = useState(false);
  const [editGuestData, setEditGuestData] = useState({
    guest_id: '',
    name: '',
    email: '',
    phone: '',
    id_passport: '',
    country: ''
  });
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
      const filtered = guests.filter(guest => {
        const searchLower = searchQuery.toLowerCase();
        const name = guest.name ? guest.name.toLowerCase() : '';
        const email = guest.email ? guest.email.toLowerCase() : '';
        const phone = guest.phone ? guest.phone.toString() : '';
        
        return name.includes(searchLower) ||
               email.includes(searchLower) ||
               phone.includes(searchQuery);
      });
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

  const openEditGuestModal = (guest) => {
    // Remove "Not provided" placeholder values when editing
    const cleanValue = (value) => (value === 'Not provided' ? '' : (value || ''));
    
    setEditGuestData({
      guest_id: guest.id,  // Use the unique guest identifier
      name: guest.name || '',
      email: cleanValue(guest.email),
      phone: cleanValue(guest.phone),
      id_passport: guest.id_passport || '',
      country: guest.country || ''
    });
    setShowEditGuestModal(true);
  };

  const handleUpdateGuest = async () => {
    try {
      await axios.put(`${API}/guests/update`, editGuestData);
      setShowEditGuestModal(false);
      fetchGuests(); // Refresh the list
      alert('Guest details updated successfully!');
    } catch (error) {
      console.error('Error updating guest:', error);
      alert('Error updating guest: ' + (error.response?.data?.detail || error.message));
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
          <h2 className="text-2xl font-bold text-white mb-2">Guests</h2>
          <p className="text-gray-300">Manage guest information and booking history</p>
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
            className="w-full px-4 py-2 pl-10 bg-gray-800 border border-gray-600 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
          />
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <span className="text-gray-400">🔍</span>
          </div>
        </div>
        {searchQuery && (
          <p className="mt-2 text-sm text-gray-300">
            Showing {filteredGuests.length} result(s) for "{searchQuery}"
          </p>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700">
        {filteredGuests.length === 0 ? (
          <div className="p-6 text-center text-gray-400">
            {searchQuery ? `No guests found matching "${searchQuery}"` : 'No guests found'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-700">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Guest Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Phone
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Total Bookings
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Completed Stays
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Upcoming Bookings
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Last Stay
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-gray-800 divide-y divide-gray-700">
                {filteredGuests.map((guest) => (
                  <tr key={guest.id} className="hover:bg-gray-700">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{guest.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{guest.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{guest.phone}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{guest.total_bookings}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{guest.total_stays}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{guest.upcoming_bookings}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">
                        {guest.last_stay ? guest.last_stay : 'Never'}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => fetchGuestDetails(guest.email)}
                          className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 transition-colors"
                        >
                          View Details
                        </button>
                        <button
                          onClick={() => openEditGuestModal(guest)}
                          className="bg-yellow-600 text-white px-3 py-1 rounded text-sm hover:bg-yellow-700 transition-colors"
                        >
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Edit Guest Modal */}
      {showEditGuestModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Edit Guest Details</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editGuestData.name}
                  onChange={(e) => setEditGuestData({...editGuestData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={editGuestData.email}
                  onChange={(e) => setEditGuestData({...editGuestData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="text"
                  value={editGuestData.phone}
                  onChange={(e) => setEditGuestData({...editGuestData, phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">ID/Passport</label>
                <input
                  type="text"
                  value={editGuestData.id_passport}
                  onChange={(e) => setEditGuestData({...editGuestData, id_passport: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Country</label>
                <input
                  type="text"
                  value={editGuestData.country}
                  onChange={(e) => setEditGuestData({...editGuestData, country: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowEditGuestModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdateGuest}
                className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700"
              >
                Update Guest
              </button>
            </div>
          </div>
        </div>
      )}

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
  }, []); // Initial load only

  useEffect(() => {
    if (currentPage !== 1 || statusFilter !== '') {
      fetchBookings();
    }
  }, [currentPage, statusFilter]);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      fetchBookings(1, '', statusFilter); // Reset search
    } else {
      const delayedSearch = setTimeout(() => {
        fetchBookings(1, searchTerm, statusFilter); // Search with reset to page 1
      }, 300);
      return () => clearTimeout(delayedSearch);
    }
  }, [searchTerm]);

  const fetchBookings = async (pageParam = currentPage, searchParam = searchTerm, statusParam = statusFilter) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pageParam.toString(),
        limit: '20',
        search: searchParam || '', 
        status: statusParam || ''
      });
      
      const response = await axios.get(`${API}/bookings?${params}`);
      
      setBookings(response.data.bookings || []);
      setTotalPages(response.data.total_pages || 1);
      setTotalCount(response.data.total_count || 0);
    } catch (error) {
      console.error('Error fetching bookings:', error);
      setBookings([]);
      setTotalPages(1);
      setTotalCount(0);
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
          <h2 className="text-2xl font-bold text-white mb-2">All Bookings</h2>
          <p className="text-gray-300">Manage all hotel bookings and reservations</p>
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
            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
          />
        </div>
        <div className="sm:w-48">
          <select
            value={statusFilter}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-600 text-white rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Status</option>
            <option value="Upcoming">Upcoming</option>
            <option value="Checked-in">Checked-in</option>
            <option value="Completed">Completed</option>
            <option value="Cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <div className="bg-gray-800 rounded-lg shadow-sm border border-gray-700">
        {bookings.length === 0 ? (
          <div className="p-6 text-center text-gray-400">
            {searchTerm || statusFilter ? 'No bookings found matching your criteria' : 'No bookings found'}
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-700">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Guest Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Phone
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Room
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Check-in
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Check-out
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Amount
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-700">
                  {bookings.map((booking) => (
                    <tr key={booking.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{booking.guest_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{booking.guest_email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{booking.guest_phone || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{booking.room_number}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{booking.check_in_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{booking.check_out_date}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(booking.status)}`}>
                          {booking.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">
                          {new Intl.NumberFormat('en-US', {
                            style: 'currency',
                            currency: 'LKR'
                          }).format(booking.booking_amount || 0)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">
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
          <h2 className="text-2xl font-bold text-white mb-2">Rooms</h2>
          <p className="text-gray-300">Manage hotel rooms and their details</p>
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
          <div key={room.id} className="bg-gray-800 rounded-lg shadow-md overflow-hidden">
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
              <h3 className="text-lg font-semibold text-white mb-1">Room {room.room_number}</h3>
              <p className="text-sm text-gray-300 mb-2">{room.room_type}</p>
              <p className="text-lg font-bold text-white mb-2">LKR {room.price_per_night}/night</p>
              <p className="text-sm text-gray-300 mb-2">Max Occupancy: {room.max_occupancy}</p>
              <div className="mb-4">
                <p className="text-sm text-gray-300">Amenities: {room.amenities?.join(', ')}</p>
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const isActive = (path) => {
    return location.pathname === path;
  };

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/restaurant', label: 'Restaurant' },
    { path: '/rooms', label: 'Rooms' },
    { path: '/guests', label: 'Guests' },
    { path: '/bookings', label: 'Bookings' },
    { path: '/expenses', label: 'Inc & Exp' },
    { path: '/commissions', label: 'Commissions' },
    { path: '/reports', label: 'Reports' },
    { path: '/settings', label: 'Settings' }
  ];

  return (
    <nav className="bg-gray-800 shadow-sm border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Desktop Navigation */}
        <div className="hidden md:flex space-x-8">
          {navItems.map((item) => (
            <Link 
              key={item.path}
              to={item.path} 
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                isActive(item.path) 
                  ? 'bg-blue-900 text-blue-300 border-b-2 border-blue-400' 
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <div className="flex items-center justify-between py-2">
            <span className="text-white font-medium">Hotel Management</span>
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-400 hover:text-white focus:outline-none focus:text-white"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                {isMobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
          
          {/* Mobile Menu */}
          {isMobileMenuOpen && (
            <div className="pb-3 space-y-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`block px-3 py-2 rounded-md text-base font-medium ${
                    isActive(item.path)
                      ? 'bg-blue-900 text-blue-300'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

// Restaurant Component  
const Restaurant = () => {
  // State management
  const [categories, setCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [tables, setTables] = useState([]);
  const [staff, setStaff] = useState([]);
  const [orders, setOrders] = useState([]);
  const [checkedInCustomers, setCheckedInCustomers] = useState([]);
  const [hotelSettings, setHotelSettings] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Get current user context
  const { user } = useAuth();
  
  // Get financial context for cross-component refresh
  const { triggerFinancialRefresh } = useFinancial();
  
  // UI state
  const [activeTab, setActiveTab] = useState('menu'); // menu, tables, orders, staff
  const [showAddCategoryModal, setShowAddCategoryModal] = useState(false);
  const [showAddItemModal, setShowAddItemModal] = useState(false);
  const [showAddTableModal, setShowAddTableModal] = useState(false);
  const [showAddStaffModal, setShowAddStaffModal] = useState(false);
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [selectedOrderForPayment, setSelectedOrderForPayment] = useState(null);
  
  // Form states
  const [newCategory, setNewCategory] = useState({ name: '', description: '', display_order: 0 });
  const [newItem, setNewItem] = useState({
    name: '', description: '', price: 0, category_id: '', 
    is_vegetarian: false, is_spicy: false, prep_time: 15, image: ''
  });
  const [newTable, setNewTable] = useState({ table_number: '', capacity: 4, position_x: 0, position_y: 0 });
  const [newStaff, setNewStaff] = useState({ name: '', role: 'Waiter', phone: '' });
  const [newOrder, setNewOrder] = useState({
    order_type: 'table', table_id: '', room_number: '', customer_name: '',
    items: [], waiter_id: '', notes: '', service_charge_rate: 10
  });
  const [orderItems, setOrderItems] = useState([]);
  const [paymentData, setPaymentData] = useState({
    payment_method: 'Cash',
    add_to_room_bill: false
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      await Promise.all([
        fetchCategories(),
        fetchMenuItems(),
        fetchTables(),
        fetchStaff(),
        fetchOrders(),
        fetchCheckedInCustomers(),
        fetchHotelSettings()
      ]);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHotelSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setHotelSettings(response.data);
    } catch (error) {
      console.error('Error fetching hotel settings:', error);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await axios.get(`${API}/restaurant/categories`);
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchMenuItems = async () => {
    try {
      const response = await axios.get(`${API}/restaurant/menu-items`);
      setMenuItems(response.data);
    } catch (error) {
      console.error('Error fetching menu items:', error);
    }
  };

  const fetchTables = async () => {
    try {
      const response = await axios.get(`${API}/restaurant/tables`);
      setTables(response.data);
    } catch (error) {
      console.error('Error fetching tables:', error);
    }
  };

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/restaurant/staff`);
      setStaff(response.data);
    } catch (error) {
      console.error('Error fetching staff:', error);
    }
  };

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/restaurant/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
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

  // Category management
  const handleAddCategory = async () => {
    try {
      await axios.post(`${API}/restaurant/categories`, newCategory);
      setShowAddCategoryModal(false);
      setNewCategory({ name: '', description: '', display_order: 0 });
      await fetchCategories();
      alert('Category added successfully!');
    } catch (error) {
      console.error('Error adding category:', error);
      alert('Error adding category: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Menu item management  
  const handleAddItem = async () => {
    try {
      await axios.post(`${API}/restaurant/menu-items`, newItem);
      setShowAddItemModal(false);
      setNewItem({
        name: '', description: '', price: 0, category_id: '', 
        is_vegetarian: false, is_spicy: false, prep_time: 15, image: ''
      });
      await fetchMenuItems();
      alert('Menu item added successfully!');
    } catch (error) {
      console.error('Error adding menu item:', error);
      alert('Error adding menu item: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Handle image upload
  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check file size (2MB limit)
      if (file.size > 2 * 1024 * 1024) {
        alert('File size must be less than 2MB');
        event.target.value = '';
        return;
      }
      
      // Check file type
      if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        event.target.value = '';
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setNewItem({...newItem, image: e.target.result});
      };
      reader.readAsDataURL(file);
    }
  };

  // Table management
  const handleAddTable = async () => {
    try {
      await axios.post(`${API}/restaurant/tables`, newTable);
      setShowAddTableModal(false);
      setNewTable({ table_number: '', capacity: 4, position_x: 0, position_y: 0 });
      await fetchTables();
      alert('Table added successfully!');
    } catch (error) {
      console.error('Error adding table:', error);
      alert('Error adding table: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Staff management
  const handleAddStaff = async () => {
    try {
      await axios.post(`${API}/restaurant/staff`, newStaff);
      setShowAddStaffModal(false);
      setNewStaff({ name: '', role: 'Waiter', phone: '' });
      await fetchStaff();
      alert('Staff member added successfully!');
    } catch (error) {
      console.error('Error adding staff:', error);
      alert('Error adding staff: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Delete functions
  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this category?')) return;
    
    try {
      await axios.delete(`${API}/restaurant/categories/${categoryId}`);
      await fetchCategories();
      await fetchMenuItems(); // Refresh menu items as well
      alert('Category deleted successfully!');
    } catch (error) {
      console.error('Error deleting category:', error);
      alert('Error deleting category: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteMenuItem = async (itemId) => {
    if (!window.confirm('Are you sure you want to delete this menu item?')) return;
    
    try {
      await axios.delete(`${API}/restaurant/menu-items/${itemId}`);
      await fetchMenuItems();
      alert('Menu item deleted successfully!');
    } catch (error) {
      console.error('Error deleting menu item:', error);
      alert('Error deleting menu item: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteTable = async (tableId) => {
    if (!window.confirm('Are you sure you want to delete this table?')) return;
    
    try {
      await axios.delete(`${API}/restaurant/tables/${tableId}`);
      await fetchTables();
      alert('Table deleted successfully!');
    } catch (error) {
      console.error('Error deleting table:', error);
      alert('Error deleting table: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteStaff = async (staffId) => {
    if (!window.confirm('Are you sure you want to delete this staff member?')) return;
    
    try {
      await axios.delete(`${API}/restaurant/staff/${staffId}`);
      await fetchStaff();
      alert('Staff member deleted successfully!');
    } catch (error) {
      console.error('Error deleting staff:', error);
      alert('Error deleting staff: ' + (error.response?.data?.detail || error.message));
    }
  };

  // Order management
  const addItemToOrder = (item) => {
    const existingItem = orderItems.find(orderItem => orderItem.menu_item_id === item.id);
    if (existingItem) {
      setOrderItems(orderItems.map(orderItem => 
        orderItem.menu_item_id === item.id 
          ? { ...orderItem, quantity: orderItem.quantity + 1, total_price: (orderItem.quantity + 1) * item.price }
          : orderItem
      ));
    } else {
      setOrderItems([...orderItems, {
        menu_item_id: item.id,
        menu_item_name: item.name,
        quantity: 1,
        unit_price: item.price,
        total_price: item.price,
        special_notes: ''
      }]);
    }
  };

  const removeItemFromOrder = (menuItemId) => {
    setOrderItems(orderItems.filter(item => item.menu_item_id !== menuItemId));
  };

  const updateItemQuantity = (menuItemId, quantity) => {
    if (quantity <= 0) {
      removeItemFromOrder(menuItemId);
      return;
    }
    setOrderItems(orderItems.map(item => 
      item.menu_item_id === menuItemId 
        ? { ...item, quantity: quantity, total_price: quantity * item.unit_price }
        : item
    ));
  };

  const handleAddItemToOrder = addItemToOrder;
  const handleRemoveItemFromOrder = removeItemFromOrder;
  const handleUpdateItemQuantity = updateItemQuantity;

  const handleCreateOrder = async () => {
    try {
      const orderData = { ...newOrder, items: orderItems };
      await axios.post(`${API}/restaurant/orders`, orderData);
      setShowOrderModal(false);
      setNewOrder({
        order_type: 'table', table_id: '', room_number: '', customer_name: '',
        items: [], waiter_id: '', notes: '', service_charge_rate: 10
      });
      setOrderItems([]);
      await Promise.all([fetchOrders(), fetchTables()]);
      alert('Order created successfully!');
    } catch (error) {
      console.error('Error creating order:', error);
      alert('Error creating order: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePayOrder = async (orderId) => {
    const order = orders.find(o => o.id === orderId);
    setSelectedOrderForPayment(order);
    setShowPaymentModal(true);
  };

  const handleProcessPayment = async () => {
    if (!selectedOrderForPayment) return;
    
    try {
      const paymentRequest = {
        payment_method: paymentData.payment_method,
        add_to_room_bill: paymentData.add_to_room_bill && selectedOrderForPayment.order_type === 'room_service'
      };
      
      await axios.post(`${API}/restaurant/orders/${selectedOrderForPayment.id}/pay`, paymentRequest);
      
      // Reset states
      setShowPaymentModal(false);
      setSelectedOrderForPayment(null);
      setPaymentData({
        payment_method: 'Cash',
        add_to_room_bill: false
      });
      
      // Refresh data
      await Promise.all([fetchOrders(), fetchTables()]);
      
      // Trigger financial refresh for real-time balance updates
      triggerFinancialRefresh();
      
      alert('Payment processed successfully!');
    } catch (error) {
      console.error('Error processing payment:', error);
      alert('Error processing payment: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading restaurant data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 sm:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-6 sm:mb-8">
          <div className="mb-4 sm:mb-0">
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white mb-2">Restaurant Management</h1>
            <p className="text-sm sm:text-base text-gray-300">Manage your restaurant operations</p>
          </div>
          {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
            <div className="flex space-x-2 sm:space-x-4">
              <button
                onClick={() => setShowOrderModal(true)}
                className="bg-green-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-md hover:bg-green-700 transition-colors text-sm sm:text-base"
              >
                New Order
              </button>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap gap-1 sm:gap-2 mb-6 sm:mb-8">
          {['menu', 'tables', 'orders', 'staff'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-2 sm:px-6 sm:py-3 font-medium rounded-lg transition-colors text-sm sm:text-base ${
                activeTab === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Menu Tab */}
        {activeTab === 'menu' && (
          <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
              <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">Menu Management</h2>
              {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                <div className="flex flex-wrap gap-2 sm:gap-4">
                  <button
                    onClick={() => setShowAddCategoryModal(true)}
                    className="bg-blue-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-md hover:bg-blue-700 text-sm sm:text-base"
                  >
                    Add Category
                  </button>
                  <button
                    onClick={() => setShowAddItemModal(true)}
                    className="bg-green-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-md hover:bg-green-700 text-sm sm:text-base"
                  >
                    Add Item
                  </button>
                </div>
              )}
            </div>

            {/* Menu Categories and Items */}
            <div className="space-y-6 sm:space-y-8">
              {categories.map(category => (
                <div key={category.id} className="bg-gray-800 rounded-lg p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4">
                    <h3 className="text-lg sm:text-xl font-semibold text-blue-400">{category.name}</h3>
                    {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                      <button
                        onClick={() => handleDeleteCategory(category.id)}
                        className="mt-2 sm:mt-0 bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                      >
                        Delete Category
                      </button>
                    )}
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                    {menuItems
                      .filter(item => item.category_id === category.id)
                      .map(item => (
                        <div key={item.id} className="bg-gray-700 rounded-lg p-3 sm:p-4">
                          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-2">
                            <h4 className="font-medium text-white text-sm sm:text-base mb-1 sm:mb-0">{item.name}</h4>
                            <span className="text-green-400 font-bold text-sm sm:text-base">LKR {item.price}</span>
                          </div>
                          <p className="text-gray-300 text-sm mb-2">{item.description}</p>
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2 text-xs">
                              {item.is_vegetarian && (
                                <span className="bg-green-600 text-white px-2 py-1 rounded">Veg</span>
                              )}
                              {item.is_spicy && (
                                <span className="bg-red-600 text-white px-2 py-1 rounded">Spicy</span>
                              )}
                              <span className="text-gray-400">{item.prep_time}min</span>
                            </div>
                            {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                              <button
                                onClick={() => handleDeleteMenuItem(item.id)}
                                className="bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                              >
                                Delete
                              </button>
                            )}
                          </div>
                        </div>
                      ))
                    }
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tables Tab */}
        {activeTab === 'tables' && (
          <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
              <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">Table Management</h2>
              {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                <button
                  onClick={() => setShowAddTableModal(true)}
                  className="bg-blue-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-md hover:bg-blue-700 text-sm sm:text-base"
                >
                  Add Table
                </button>
              )}
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4">
              {tables.map(table => (
                <div
                  key={table.id}
                  className={`p-3 sm:p-4 rounded-lg border-2 ${
                    table.status === 'Available' ? 'bg-green-800 border-green-600' :
                    table.status === 'Occupied' ? 'bg-red-800 border-red-600' :
                    table.status === 'Reserved' ? 'bg-yellow-800 border-yellow-600' :
                    'bg-gray-800 border-gray-600'
                  }`}
                >
                  <div className="text-center">
                    <div className="text-lg sm:text-xl lg:text-2xl font-bold">T{table.table_number}</div>
                    <div className="text-xs sm:text-sm">{table.capacity} seats</div>
                    <div className="text-xs mt-1 capitalize">{table.status}</div>
                    {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                      <button
                        onClick={() => handleDeleteTable(table.id)}
                        className="mt-2 bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === 'orders' && (
          <div className="space-y-4 sm:space-y-6">
            <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">Order Management</h2>
            
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Order #</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Type</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase hidden sm:table-cell">Table/Room</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase hidden lg:table-cell">Customer</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Amount</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Status</th>
                      <th className="px-3 sm:px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-gray-800 divide-y divide-gray-700">
                    {orders.map(order => (
                      <tr key={order.id}>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-white">{order.order_number}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded ${
                            order.order_type === 'table' ? 'bg-blue-600' : 'bg-purple-600'
                          }`}>
                            {order.order_type === 'table' ? 'Table' : 'Room'}
                          </span>
                        </td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-white hidden sm:table-cell">
                          {order.order_type === 'table' ? `Table ${order.table_number}` : `Room ${order.room_number}`}
                        </td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-white hidden lg:table-cell">{order.customer_name}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap text-xs sm:text-sm text-green-400">LKR {order.total_amount}</td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs rounded ${
                            order.payment_status === 'Paid' ? 'bg-green-600' : 'bg-yellow-600'
                          }`}>
                            {order.payment_status}
                          </span>
                        </td>
                        <td className="px-3 sm:px-6 py-4 whitespace-nowrap">
                          {order.payment_status === 'Pending' && (
                            <button
                              onClick={() => handlePayOrder(order.id)}
                              className="bg-green-600 text-white px-2 py-1 sm:px-3 sm:py-1 rounded text-xs sm:text-sm hover:bg-green-700"
                            >
                              Pay
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Staff Tab */}
        {activeTab === 'staff' && (
          <div className="space-y-4 sm:space-y-6">
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
              <h2 className="text-lg sm:text-xl lg:text-2xl font-bold">Staff Management</h2>
              {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                <button
                  onClick={() => setShowAddStaffModal(true)}
                  className="bg-blue-600 text-white px-3 py-2 sm:px-4 sm:py-2 rounded-md hover:bg-blue-700 text-sm sm:text-base"
                >
                  Add Staff
                </button>
              )}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              {staff.map(member => (
                <div key={member.id} className="bg-gray-800 rounded-lg p-3 sm:p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h3 className="font-semibold text-white text-sm sm:text-base">{member.name}</h3>
                      <p className="text-blue-400 text-sm">{member.role}</p>
                      <p className="text-gray-300 text-xs sm:text-sm">{member.phone}</p>
                    </div>
                    {(user?.role === 'Admin' || user?.role === 'Restaurant Manager') && (
                      <button
                        onClick={() => handleDeleteStaff(member.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-xs hover:bg-red-700"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* All Modals will be added in the next part */}

      {/* Add Category Modal */}
      {showAddCategoryModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Add Menu Category</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newCategory.name}
                  onChange={(e) => setNewCategory({...newCategory, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newCategory.description}
                  onChange={(e) => setNewCategory({...newCategory, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  rows="3"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddCategoryModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddCategory}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Category
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Menu Item Modal */}
      {showAddItemModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Add Menu Item</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newItem.name}
                  onChange={(e) => setNewItem({...newItem, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={newItem.category_id}
                  onChange={(e) => setNewItem({...newItem, category_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                >
                  <option value="">Select Category</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price (LKR)</label>
                <input
                  type="number"
                  step="0.01"
                  value={newItem.price}
                  onChange={(e) => setNewItem({...newItem, price: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={newItem.description}
                  onChange={(e) => setNewItem({...newItem, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  rows="3"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Preparation Time (minutes)</label>
                <input
                  type="number"
                  value={newItem.prep_time}
                  onChange={(e) => setNewItem({...newItem, prep_time: parseInt(e.target.value) || 15})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Image (Max 2MB)</label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
                {newItem.image && (
                  <div className="mt-2">
                    <img 
                      src={newItem.image} 
                      alt="Preview" 
                      className="w-20 h-20 object-cover rounded-md border"
                    />
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newItem.is_vegetarian}
                    onChange={(e) => setNewItem({...newItem, is_vegetarian: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Vegetarian</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={newItem.is_spicy}
                    onChange={(e) => setNewItem({...newItem, is_spicy: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">Spicy</span>
                </label>
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddItemModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddItem}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Add Item
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Table Modal */}
      {showAddTableModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Add Table</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Table Number</label>
                <input
                  type="text"
                  value={newTable.table_number}
                  onChange={(e) => setNewTable({...newTable, table_number: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Capacity</label>
                <input
                  type="number"
                  value={newTable.capacity}
                  onChange={(e) => setNewTable({...newTable, capacity: parseInt(e.target.value) || 4})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddTableModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddTable}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Table
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Staff Modal */}
      {showAddStaffModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Add Staff Member</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={newStaff.name}
                  onChange={(e) => setNewStaff({...newStaff, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={newStaff.role}
                  onChange={(e) => setNewStaff({...newStaff, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                >
                  <option value="Waiter">Waiter</option>
                  <option value="Chef">Chef</option>
                  <option value="Manager">Manager</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="text"
                  value={newStaff.phone}
                  onChange={(e) => setNewStaff({...newStaff, phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowAddStaffModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleAddStaff}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Staff
              </button>
            </div>
          </div>
        </div>
      )}

      {/* POS Style Order Interface */}
      {showOrderModal && (
        <div className="fixed inset-0 bg-gray-900 z-50 flex">
          {/* Left Panel - Menu Items */}
          <div className="w-2/3 bg-gray-800 p-4 overflow-y-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Menu</h2>
              <button
                onClick={() => {
                  setShowOrderModal(false);
                  setNewOrder({
                    order_type: 'table', table_id: '', room_number: '', customer_name: '',
                    items: [], waiter_id: '', notes: '', service_charge_rate: 10
                  });
                  setOrderItems([]);
                }}
                className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                ✕ Close
              </button>
            </div>

            {/* Order Type Selection */}
            <div className="mb-6">
              <div className="flex space-x-2">
                <button
                  onClick={() => setNewOrder({...newOrder, order_type: 'table'})}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    newOrder.order_type === 'table' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Table Order
                </button>
                <button
                  onClick={() => setNewOrder({...newOrder, order_type: 'room_service'})}
                  className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                    newOrder.order_type === 'room_service' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Room Service
                </button>
              </div>
            </div>

            {/* Table/Room Selection */}
            {newOrder.order_type === 'table' && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-white">Select Table</h3>
                <div className="grid grid-cols-4 gap-3">
                  {tables.filter(table => table.status === 'Available').map(table => (
                    <button
                      key={table.id}
                      onClick={() => setNewOrder({...newOrder, table_id: table.id})}
                      className={`p-4 rounded-lg text-center transition-colors ${
                        newOrder.table_id === table.id
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                      }`}
                    >
                      <div className="font-bold text-lg">T{table.table_number}</div>
                      <div className="text-sm">{table.capacity} seats</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {newOrder.order_type === 'room_service' && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-3 text-white">Select Room (Live Check-in)</h3>
                <div className="grid grid-cols-3 gap-3">
                  {checkedInCustomers.map(customer => (
                    <button
                      key={customer.id}
                      onClick={() => setNewOrder({
                        ...newOrder, 
                        room_number: customer.current_room, 
                        customer_name: customer.name
                      })}
                      className={`p-4 rounded-lg text-left transition-colors ${
                        newOrder.room_number === customer.current_room
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600 border border-gray-600'
                      }`}
                    >
                      <div className="font-bold text-lg">Room {customer.current_room}</div>
                      <div className="text-sm">{customer.name}</div>
                      <div className="text-xs text-green-400">
                        ● Live Check-in
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Menu Categories */}
            <div className="space-y-6">
              {categories.map(category => (
                <div key={category.id} className="bg-gray-700 rounded-lg p-4 shadow-sm">
                  <h3 className="text-xl font-semibold text-white mb-4 border-b border-gray-600 pb-2">
                    {category.name}
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {menuItems.filter(item => item.category_id === category.id).map(item => (
                      <button
                        key={item.id}
                        onClick={() => handleAddItemToOrder(item)}
                        className="bg-gray-600 rounded-lg hover:bg-gray-500 transition-colors text-left"
                      >
                        {item.image && (
                          <img 
                            src={item.image} 
                            alt={item.name}
                            className="w-full h-32 object-cover rounded-t-lg"
                          />
                        )}
                        <div className="p-4">
                          <div className="font-medium text-white">{item.name}</div>
                          <div className="text-sm text-gray-300 mt-1">{item.description}</div>
                          <div className="text-lg font-bold text-blue-400 mt-2">
                            LKR {item.price}
                          </div>
                          <div className="flex items-center space-x-2 mt-2">
                            {item.is_vegetarian && (
                              <span className="bg-green-600 text-green-100 px-2 py-1 rounded text-xs">Veg</span>
                            )}
                            {item.is_spicy && (
                              <span className="bg-red-600 text-red-100 px-2 py-1 rounded text-xs">Spicy</span>
                            )}
                            <span className="text-gray-400 text-xs">{item.prep_time}min</span>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right Panel - Order Summary */}
          <div className="w-1/3 bg-gray-900 p-6 overflow-y-auto max-h-[calc(100vh-120px)]">
            <div className="mb-4">
              <h3 className="text-xl font-bold text-white mb-4">Order Summary</h3>
              
              {/* Order Details */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Type:</span>
                  <span className="font-medium text-white">{newOrder.order_type === 'table' ? 'Table Order' : 'Room Service'}</span>
                </div>
                
                {newOrder.order_type === 'table' && newOrder.table_id && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Table:</span>
                    <span className="font-medium text-white">
                      {tables.find(t => t.id === newOrder.table_id)?.table_number || 'N/A'}
                    </span>
                  </div>
                )}
                
                {newOrder.order_type === 'room_service' && newOrder.room_number && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Room:</span>
                    <span className="font-medium text-white">{newOrder.room_number}</span>
                  </div>
                )}
                
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Customer Name</label>
                  <input
                    type="text"
                    value={newOrder.customer_name}
                    onChange={(e) => setNewOrder({...newOrder, customer_name: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                    placeholder="Enter customer name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Waiter</label>
                  <select
                    value={newOrder.waiter_id}
                    onChange={(e) => setNewOrder({...newOrder, waiter_id: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                  >
                    <option value="">Select Waiter</option>
                    {staff.filter(s => s.role === 'Waiter').map(waiter => (
                      <option key={waiter.id} value={waiter.id}>
                        {waiter.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Order Items */}
            <div className="mb-4">
              <h4 className="text-lg font-semibold mb-4 text-white">Items</h4>
              
              {orderItems.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-4xl mb-2">🍽️</div>
                  <p>No items added yet</p>
                  <p className="text-sm">Click on menu items to add them</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
                  {orderItems.map((item, index) => (
                    <div key={index} className="bg-gray-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-medium text-white">{item.menu_item_name}</div>
                        <button
                          onClick={() => handleRemoveItemFromOrder(item.menu_item_id)}
                          className="text-red-400 hover:text-red-300"
                        >
                          ✕
                        </button>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <button
                            onClick={() => handleUpdateItemQuantity(item.menu_item_id, item.quantity - 1)}
                            className="bg-gray-700 text-gray-300 w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-600"
                          >
                            −
                          </button>
                          <span className="font-medium text-lg text-white">{item.quantity}</span>
                          <button
                            onClick={() => handleUpdateItemQuantity(item.menu_item_id, item.quantity + 1)}
                            className="bg-gray-700 text-gray-300 w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-600"
                          >
                            +
                          </button>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-400">LKR {item.unit_price} each</div>
                          <div className="font-bold text-blue-400">LKR {item.total_price}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Order Summary Footer */}
            <div className="mt-6 pt-4 border-t border-gray-700">
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span className="text-gray-400">Subtotal:</span>
                  <span className="font-medium text-white">LKR {orderItems.reduce((sum, item) => sum + item.total_price, 0).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Tax ({hotelSettings.tax_rate || 0}%):</span>
                  <span className="font-medium text-white">LKR {(orderItems.reduce((sum, item) => sum + item.total_price, 0) * (hotelSettings.tax_rate || 0) / 100).toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Service Charge ({newOrder.service_charge_rate}%):</span>
                  <span className="font-medium text-white">LKR {(orderItems.reduce((sum, item) => sum + item.total_price, 0) * (newOrder.service_charge_rate / 100)).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-xl font-bold">
                  <span className="text-white">Total:</span>
                  <span className="text-blue-400">LKR {(orderItems.reduce((sum, item) => sum + item.total_price, 0) * (1 + (hotelSettings.tax_rate || 0) / 100 + newOrder.service_charge_rate / 100)).toFixed(2)}</span>
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-1">Service Charge Rate (%)</label>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    value={newOrder.service_charge_rate}
                    onChange={(e) => setNewOrder({...newOrder, service_charge_rate: parseFloat(e.target.value) || 0})}
                    className="flex-1 px-3 py-2 bg-gray-800 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                    min="0"
                    max="100"
                    step="0.5"
                    placeholder="10"
                  />
                  <button
                    onClick={() => setNewOrder({...newOrder, service_charge_rate: 0})}
                    className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors text-sm"
                    title="Remove service charge"
                  >
                    Remove
                  </button>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  Service charge: LKR {(orderItems.reduce((sum, item) => sum + item.total_price, 0) * (newOrder.service_charge_rate / 100)).toFixed(2)}
                </div>
              </div>
              
              <div className="mb-4">
                <label className="block text-sm text-gray-400 mb-1">Special Notes</label>
                <textarea
                  value={newOrder.notes}
                  onChange={(e) => setNewOrder({...newOrder, notes: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-white"
                  rows="3"
                  placeholder="Special instructions..."
                />
              </div>
              
              <button
                onClick={handleCreateOrder}
                disabled={orderItems.length === 0 || (newOrder.order_type === 'table' && !newOrder.table_id) || (newOrder.order_type === 'room_service' && !newOrder.room_number)}
                className="w-full bg-green-600 text-white py-4 rounded-lg font-semibold text-lg hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
              >
                {orderItems.length === 0 ? 'Add Items to Order' : 'Create Order'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Payment Modal */}
      {showPaymentModal && selectedOrderForPayment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">Process Payment</h3>
            
            {/* Order Details */}
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-2">Order Details</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Order Number:</span>
                  <span className="font-medium">{selectedOrderForPayment.order_number}</span>
                </div>
                <div className="flex justify-between">
                  <span>Customer:</span>
                  <span className="font-medium">{selectedOrderForPayment.customer_name}</span>
                </div>
                {selectedOrderForPayment.order_type === 'room_service' && (
                  <div className="flex justify-between">
                    <span>Room:</span>
                    <span className="font-medium">{selectedOrderForPayment.room_number}</span>
                  </div>
                )}
                {selectedOrderForPayment.order_type === 'table' && (
                  <div className="flex justify-between">
                    <span>Table:</span>
                    <span className="font-medium">{selectedOrderForPayment.table_number}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>LKR {selectedOrderForPayment.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Tax ({hotelSettings.tax_rate || 0}%):</span>
                  <span>LKR {selectedOrderForPayment.tax_amount.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Service Charge:</span>
                  <span>LKR {selectedOrderForPayment.service_charge.toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-lg border-t pt-2">
                  <span>Total:</span>
                  <span>LKR {selectedOrderForPayment.total_amount.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Room Service Special Options */}
            {selectedOrderForPayment.order_type === 'room_service' && (
              <div className="mb-4">
                <label className="flex items-center space-x-2 text-sm">
                  <input
                    type="checkbox"
                    checked={paymentData.add_to_room_bill}
                    onChange={(e) => setPaymentData({...paymentData, add_to_room_bill: e.target.checked})}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-gray-700">Add to Room Bill (will be charged at checkout)</span>
                </label>
              </div>
            )}

            {/* Payment Method Selection */}
            {(!paymentData.add_to_room_bill || selectedOrderForPayment.order_type !== 'room_service') && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Method</label>
                <select
                  value={paymentData.payment_method}
                  onChange={(e) => setPaymentData({...paymentData, payment_method: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                >
                  <option value="Cash">Cash</option>
                  <option value="Card">Card</option>
                  <option value="Bank Transfer">Bank Transfer</option>
                </select>
              </div>
            )}

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowPaymentModal(false);
                  setSelectedOrderForPayment(null);
                  setPaymentData({
                    payment_method: 'Cash',
                    add_to_room_bill: false
                  });
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleProcessPayment}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                {paymentData.add_to_room_bill && selectedOrderForPayment.order_type === 'room_service' 
                  ? 'Add to Room Bill' 
                  : 'Process Payment'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Temporary placeholder for Restaurant component
const RestaurantOld = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-2">Restaurant Management</h1>
        <p className="text-gray-300">Coming soon...</p>
      </div>
    </div>
  );
};

// Settings Component
const Settings = () => {
  // State for different sections
  const [users, setUsers] = useState([]);
  const [hotelSettings, setHotelSettings] = useState({});
  const [activityLogs, setActivityLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // UI state
  const [activeTab, setActiveTab] = useState('users'); // users, settings, email, channels, system, logs
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [showActivityLogs, setShowActivityLogs] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Email settings state
  const [emailSettings, setEmailSettings] = useState({
    provider: 'smtp',
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    sendgrid_api_key: '',
    aws_access_key: '',
    aws_secret_key: '',
    aws_region: 'us-east-1',
    from_email: '',
    from_name: '',
    is_configured: false
  });
  const [testingEmail, setTestingEmail] = useState(false);
  const [resetting, setResetting] = useState(false);
  
  // Booking channels state
  const [bookingChannels, setBookingChannels] = useState([]);
  const [showCreateChannelModal, setShowCreateChannelModal] = useState(false);
  const [newChannel, setNewChannel] = useState({
    channel_name: '',
    channel_type: 'OTA',
    commission_rate: 0,
    contact_email: '',
    contact_phone: ''
  });
  
  // Get current user context
  const { user } = useAuth();
  
  // Form states
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    full_name: '',
    role: 'Staff',
    email: ''
  });
  
  const [settingsForm, setSettingsForm] = useState({
    hotel_name: '',
    hotel_logo: '',
    hotel_contact: '',
    hotel_address: '',
    hotel_email: '',
    hotel_phone: '',
    currency: 'LKR',
    check_in_time: '14:00',
    check_out_time: '12:00',
    default_room_rate: 5000,
    tax_rate: 0
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        alert('Logo file size should be less than 5MB');
        return;
      }
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setSettingsForm({...settingsForm, hotel_logo: e.target.result});
      };
      reader.readAsDataURL(file);
    }
  };

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchUsers(),
        fetchSettings(),
        fetchEmailSettings(),
        fetchBookingChannels(),
        fetchActivityLogs()
      ]);
    } catch (error) {
      console.error('Error fetching settings data:', error);
    }
    setLoading(false);
  };

  const fetchBookingChannels = async () => {
    try {
      const response = await axios.get(`${API}/booking-channels`);
      setBookingChannels(response.data);
    } catch (error) {
      console.error('Error fetching booking channels:', error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setHotelSettings(response.data);
      setSettingsForm(response.data);
    } catch (error) {
      console.error('Error fetching settings:', error);
    }
  };

  const fetchEmailSettings = async () => {
    try {
      const response = await axios.get(`${API}/email-settings`);
      setEmailSettings(response.data);
    } catch (error) {
      console.error('Error fetching email settings:', error);
      // Create default settings if none exist
      setEmailSettings({
        provider: 'smtp',
        smtp_host: '',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        sendgrid_api_key: '',
        aws_access_key: '',
        aws_secret_key: '',
        aws_region: 'us-east-1',
        from_email: '',
        from_name: '',
        is_configured: false
      });
    }
  };

  const fetchActivityLogs = async (page = 1) => {
    try {
      const response = await axios.get(`${API}/activity-logs?page=${page}&limit=20`);
      setActivityLogs(response.data.logs);
      setCurrentPage(response.data.page);
      setTotalPages(response.data.total_pages);
    } catch (error) {
      console.error('Error fetching activity logs:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/users`, newUser);
      setNewUser({ username: '', password: '', full_name: '', role: 'Staff', email: '' });
      setShowCreateUserModal(false);
      fetchUsers();
      alert('User created successfully!');
    } catch (error) {
      alert('Error creating user: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteUser = async (userId) => {
    if (window.confirm('Are you sure you want to delete this user?')) {
      try {
        await axios.delete(`${API}/users/${userId}`);
        fetchUsers();
        alert('User deleted successfully!');
      } catch (error) {
        alert('Error deleting user: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const handleToggleUserStatus = async (userId) => {
    try {
      await axios.put(`${API}/users/${userId}/toggle-status`);
      fetchUsers();
    } catch (error) {
      alert('Error updating user status: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleUpdateSettings = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/settings`, settingsForm);
      setHotelSettings(settingsForm);
      alert('Settings updated successfully!');
    } catch (error) {
      alert('Error updating settings: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSaveEmailSettings = async () => {
    try {
      await axios.put(`${API}/email-settings`, emailSettings);
      await fetchEmailSettings(); // Refresh settings
      alert('Email settings updated successfully!');
    } catch (error) {
      alert('Error updating email settings: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleTestEmail = async () => {
    setTestingEmail(true);
    try {
      await axios.post(`${API}/email-settings/test`);
      alert('Test email sent successfully! Check your inbox.');
    } catch (error) {
      alert('Failed to send test email: ' + (error.response?.data?.detail || error.message));
    }
    setTestingEmail(false);
  };

  const handleCreateChannel = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/booking-channels`, newChannel);
      setShowCreateChannelModal(false);
      setNewChannel({
        channel_name: '',
        channel_type: 'OTA',
        commission_rate: 0,
        contact_email: '',
        contact_phone: ''
      });
      await fetchBookingChannels();
      alert('Booking channel created successfully!');
    } catch (error) {
      alert('Error creating booking channel: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleToggleChannelStatus = async (channelId) => {
    try {
      await axios.put(`${API}/booking-channels/${channelId}/toggle-status`);
      await fetchBookingChannels();
      alert('Channel status updated successfully!');
    } catch (error) {
      alert('Error updating channel status: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteChannel = async (channelId, channelName) => {
    if (window.confirm(`Are you sure you want to delete the "${channelName}" booking channel?`)) {
      try {
        await axios.delete(`${API}/booking-channels/${channelId}`);
        await fetchBookingChannels();
        alert('Booking channel deleted successfully!');
      } catch (error) {
        alert('Error deleting booking channel: ' + (error.response?.data?.detail || error.message));
      }
    }
  };

  const handleCompleteReset = async () => {
    // Multiple confirmation dialogs for safety
    const firstConfirm = window.confirm(
      '⚠️ DANGER: COMPLETE SYSTEM RESET\n\n' +
      'This will DELETE ALL DATA including:\n' +
      '• All rooms and bookings\n' +
      '• All guest records\n' +
      '• All financial data\n' +
      '• All users (except admin)\n' +
      '• All activity logs\n\n' +
      'Are you sure you want to continue?'
    );
    
    if (!firstConfirm) return;
    
    const secondConfirm = window.confirm(
      '🔥 FINAL WARNING: This action is IRREVERSIBLE!\n\n' +
      'All your hotel data will be permanently deleted.\n' +
      'Only hotel name and admin account will be preserved.\n\n' +
      'Type YES in the next dialog to confirm.'
    );
    
    if (!secondConfirm) return;
    
    const typeConfirm = window.prompt(
      'Please type "DELETE ALL DATA" to confirm complete reset:'
    );
    
    if (typeConfirm !== 'DELETE ALL DATA') {
      alert('Reset cancelled - confirmation text did not match.');
      return;
    }
    
    setResetting(true);
    try {
      const response = await axios.post(`${API}/admin/complete-reset`);
      
      // Check if setup is required
      if (response.data.requires_setup) {
        alert(
          '✅ COMPLETE RESET SUCCESSFUL!\n\n' +
          'All data has been cleared:\n' +
          `• Rooms cleared: ${response.data.reset_summary.rooms || 0}\n` +
          `• Bookings cleared: ${response.data.reset_summary.bookings || 0}\n` +
          `• Customers cleared: ${response.data.reset_summary.customers || 0}\n` +
          `• Expenses cleared: ${response.data.reset_summary.expenses || 0}\n` +
          `• Incomes cleared: ${response.data.reset_summary.incomes || 0}\n` +
          `• Users cleared: ${response.data.reset_summary.users_except_admin || 0}\n\n` +
          'Hotel settings and admin account preserved.\n' +
          'You will now be redirected to setup wizard to reconfigure hotel and set initial cash/bank balances.'
        );
        
        // Force logout and redirect to setup wizard
        localStorage.removeItem('token');
        window.location.reload();
      } else {
        alert(
          '✅ COMPLETE RESET SUCCESSFUL!\n\n' +
          'All data has been cleared:\n' +
          `• Rooms cleared: ${response.data.reset_summary.rooms || 0}\n` +
          `• Bookings cleared: ${response.data.reset_summary.bookings || 0}\n` +
          `• Customers cleared: ${response.data.reset_summary.customers || 0}\n` +
          `• Expenses cleared: ${response.data.reset_summary.expenses || 0}\n` +
          `• Users cleared: ${response.data.reset_summary.users_except_admin || 0}\n\n` +
          'Hotel name and admin account preserved.\n' +
          'Refreshing page...'
        );
        
        // Refresh the page to show clean state
        window.location.reload();
      }
      
    } catch (error) {
      alert('Reset failed: ' + (error.response?.data?.detail || error.message));
    }
    setResetting(false);
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-300 rounded mb-4"></div>
          <div className="h-64 bg-gray-300 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white">Settings</h1>
        <p className="text-gray-300">Manage users, configure hotel settings, and view activity logs</p>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('users')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'users'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            User Management
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'settings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Hotel Settings
          </button>
          <button
            onClick={() => setActiveTab('email')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'email'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Email Settings
          </button>
          <button
            onClick={() => setActiveTab('channels')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'channels'
                ? 'border-green-500 text-green-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📈 Booking Channels
          </button>
          {/* System Management Tab - Only visible to Admin */}
          {user?.role === 'Admin' && (
            <button
              onClick={() => setActiveTab('system')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'system'
                  ? 'border-red-500 text-red-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🔧 System Management
            </button>
          )}
          <button
            onClick={() => setActiveTab('logs')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'logs'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Activity Logs
          </button>
        </nav>
      </div>

      {/* User Management Tab */}
      {activeTab === 'users' && (
        <div className="space-y-6">
          <div className="bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">User Management</h2>
              <button
                onClick={() => setShowCreateUserModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                + Add New User
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="bg-gray-700">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Username</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Full Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-gray-800 divide-y divide-gray-600">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-white">{user.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{user.full_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user.role === 'Admin' 
                            ? 'bg-red-100 text-red-800' 
                            : user.role === 'Manager'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-green-100 text-green-800'
                        }`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-white">{user.email || 'N/A'}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          user.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                        <button
                          onClick={() => handleToggleUserStatus(user.id)}
                          className={`px-3 py-1 rounded ${
                            user.is_active 
                              ? 'bg-yellow-500 text-white hover:bg-yellow-600' 
                              : 'bg-green-500 text-white hover:bg-green-600'
                          } transition-colors`}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        {user.username !== 'admin' && (
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {users.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  No users found. Create your first user to get started.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Hotel Settings Tab */}
      {activeTab === 'settings' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Hotel Settings</h2>
            
            <form onSubmit={handleUpdateSettings} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Hotel Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Hotel Name
                  </label>
                  <input
                    type="text"
                    value={settingsForm.hotel_name}
                    onChange={(e) => setSettingsForm({...settingsForm, hotel_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-700 text-white"
                    placeholder="Enter hotel name"
                  />
                </div>

                {/* Hotel Logo */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Hotel Logo
                  </label>
                  <div className="space-y-2">
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleLogoUpload}
                      className="w-full px-3 py-2 border border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-gray-700 text-white file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                    />
                    {settingsForm.hotel_logo && (
                      <div className="flex items-center space-x-3 p-3 bg-gray-700 rounded-md">
                        <img
                          src={settingsForm.hotel_logo}
                          alt="Hotel Logo Preview"
                          className="w-16 h-16 object-contain bg-white rounded"
                        />
                        <div className="flex-1">
                          <p className="text-sm text-gray-300">Logo preview</p>
                          <button
                            type="button"
                            onClick={() => setSettingsForm({...settingsForm, hotel_logo: ''})}
                            className="text-red-400 hover:text-red-300 text-xs"
                          >
                            Remove logo
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Hotel Contact */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Contact Number
                  </label>
                  <input
                    type="text"
                    value={settingsForm.hotel_contact}
                    onChange={(e) => setSettingsForm({...settingsForm, hotel_contact: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter contact number"
                  />
                </div>

                {/* Hotel Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Hotel Email
                  </label>
                  <input
                    type="email"
                    value={settingsForm.hotel_email}
                    onChange={(e) => setSettingsForm({...settingsForm, hotel_email: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter hotel email"
                  />
                </div>

                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Currency
                  </label>
                  <select
                    value={settingsForm.currency}
                    onChange={(e) => setSettingsForm({...settingsForm, currency: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="LKR">Sri Lankan Rupee (LKR)</option>
                    <option value="USD">US Dollar (USD)</option>
                    <option value="EUR">Euro (EUR)</option>
                    <option value="GBP">British Pound (GBP)</option>
                  </select>
                </div>

                {/* Timezone */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Hotel Timezone
                  </label>
                  <select
                    value={settingsForm.timezone || 'UTC'}
                    onChange={(e) => setSettingsForm({...settingsForm, timezone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="Asia/Colombo">Asia/Colombo (Sri Lanka)</option>
                    <option value="Asia/Kolkata">Asia/Kolkata (India)</option>
                    <option value="Asia/Dubai">Asia/Dubai (UAE)</option>
                    <option value="Asia/Singapore">Asia/Singapore</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                    <option value="Europe/London">Europe/London (GMT)</option>
                    <option value="Europe/Paris">Europe/Paris (CET)</option>
                    <option value="Australia/Sydney">Australia/Sydney</option>
                    <option value="Asia/Tokyo">Asia/Tokyo (Japan)</option>
                    <option value="UTC">UTC</option>
                  </select>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    All timestamps in the application will use this timezone
                  </p>
                </div>

                {/* Check-in Time */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Check-in Time
                  </label>
                  <input
                    type="time"
                    value={settingsForm.check_in_time}
                    onChange={(e) => setSettingsForm({...settingsForm, check_in_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                {/* Check-out Time */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Check-out Time
                  </label>
                  <input
                    type="time"
                    value={settingsForm.check_out_time}
                    onChange={(e) => setSettingsForm({...settingsForm, check_out_time: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>

                {/* Default Room Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Default Room Rate ({settingsForm.currency})
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={settingsForm.default_room_rate}
                    onChange={(e) => setSettingsForm({...settingsForm, default_room_rate: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter default room rate"
                  />
                </div>

                {/* Tax Rate */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tax Rate (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={settingsForm.tax_rate}
                    onChange={(e) => setSettingsForm({...settingsForm, tax_rate: parseFloat(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                    placeholder="Enter tax rate percentage"
                  />
                </div>
              </div>

              {/* Hotel Address - Full Width */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Hotel Address
                </label>
                <textarea
                  value={settingsForm.hotel_address}
                  onChange={(e) => setSettingsForm({...settingsForm, hotel_address: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  rows="3"
                  placeholder="Enter hotel address"
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Update Settings
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Email Settings Tab */}
      {activeTab === 'email' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Email Configuration</h2>
              <div className="flex space-x-3">
                <button
                  onClick={handleTestEmail}
                  disabled={!emailSettings.is_configured || testingEmail}
                  className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {testingEmail ? 'Sending...' : 'Test Email'}
                </button>
                <button
                  onClick={handleSaveEmailSettings}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Save Settings
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Email Provider Selection */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Email Provider
                </label>
                <select
                  value={emailSettings.provider}
                  onChange={(e) => setEmailSettings({...emailSettings, provider: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="smtp">Custom SMTP</option>
                  <option value="sendgrid">SendGrid</option>
                  <option value="ses">AWS SES</option>
                  <option value="gmail">Gmail SMTP</option>
                </select>
              </div>

              {/* Common Fields */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  From Email
                </label>
                <input
                  type="email"
                  value={emailSettings.from_email}
                  onChange={(e) => setEmailSettings({...emailSettings, from_email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="noreply@yourhotel.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  From Name
                </label>
                <input
                  type="text"
                  value={emailSettings.from_name}
                  onChange={(e) => setEmailSettings({...emailSettings, from_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Your Hotel Name"
                />
              </div>

              {/* SMTP/Gmail Settings */}
              {(emailSettings.provider === 'smtp' || emailSettings.provider === 'gmail') && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      SMTP Host
                    </label>
                    <input
                      type="text"
                      value={emailSettings.smtp_host}
                      onChange={(e) => setEmailSettings({...emailSettings, smtp_host: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={emailSettings.provider === 'gmail' ? 'smtp.gmail.com' : 'mail.yourprovider.com'}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      SMTP Port
                    </label>
                    <input
                      type="number"
                      value={emailSettings.smtp_port}
                      onChange={(e) => setEmailSettings({...emailSettings, smtp_port: parseInt(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="587"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      SMTP Username
                    </label>
                    <input
                      type="text"
                      value={emailSettings.smtp_username}
                      onChange={(e) => setEmailSettings({...emailSettings, smtp_username: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="username@yourprovider.com"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      SMTP Password
                    </label>
                    <input
                      type="password"
                      value={emailSettings.smtp_password}
                      onChange={(e) => setEmailSettings({...emailSettings, smtp_password: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={emailSettings.smtp_password ? '••••••••' : 'Enter password'}
                    />
                  </div>
                </>
              )}

              {/* SendGrid Settings */}
              {emailSettings.provider === 'sendgrid' && (
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    SendGrid API Key
                  </label>
                  <input
                    type="password"
                    value={emailSettings.sendgrid_api_key}
                    onChange={(e) => setEmailSettings({...emailSettings, sendgrid_api_key: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    placeholder={emailSettings.sendgrid_api_key ? '••••••••' : 'SG.xxxxxxxxxxxxxxxx'}
                  />
                </div>
              )}

              {/* AWS SES Settings */}
              {emailSettings.provider === 'ses' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      AWS Access Key
                    </label>
                    <input
                      type="text"
                      value={emailSettings.aws_access_key}
                      onChange={(e) => setEmailSettings({...emailSettings, aws_access_key: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder="AKIAIOSFODNN7EXAMPLE"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      AWS Secret Key
                    </label>
                    <input
                      type="password"
                      value={emailSettings.aws_secret_key}
                      onChange={(e) => setEmailSettings({...emailSettings, aws_secret_key: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      placeholder={emailSettings.aws_secret_key ? '••••••••' : 'Enter secret key'}
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      AWS Region
                    </label>
                    <select
                      value={emailSettings.aws_region}
                      onChange={(e) => setEmailSettings({...emailSettings, aws_region: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    >
                      <option value="us-east-1">US East (Virginia)</option>
                      <option value="us-west-2">US West (Oregon)</option>
                      <option value="eu-west-1">EU (Ireland)</option>
                      <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
                    </select>
                  </div>
                </>
              )}
            </div>

            {/* Configuration Status */}
            <div className="mt-6 p-4 rounded-lg bg-gray-50 dark:bg-gray-700">
              <div className="flex items-center">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  emailSettings.is_configured 
                    ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100' 
                    : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100'
                }`}>
                  {emailSettings.is_configured ? '✓ Configured' : '⚠ Not Configured'}
                </span>
                <span className="ml-3 text-sm text-gray-600 dark:text-gray-300">
                  {emailSettings.is_configured 
                    ? 'Email service is ready to send notifications'
                    : 'Complete the configuration to enable email notifications'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Booking Channels Tab */}
      {activeTab === 'channels' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">📈 Booking Channels Management</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Manage all booking sources including OTAs, direct bookings, and corporate channels
                </p>
              </div>
              <button
                onClick={() => setShowCreateChannelModal(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
              >
                + Add Channel
              </button>
            </div>

            {/* Channels List */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-600">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Channel Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Commission Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                  {bookingChannels.map((channel) => (
                    <tr key={channel.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {channel.channel_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          channel.channel_type === 'Direct' 
                            ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                            : channel.channel_type === 'OTA'
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-100'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100'
                        }`}>
                          {channel.channel_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {channel.commission_rate}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        <div>
                          {channel.contact_email && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              📧 {channel.contact_email}
                            </div>
                          )}
                          {channel.contact_phone && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              📞 {channel.contact_phone}
                            </div>
                          )}
                          {!channel.contact_email && !channel.contact_phone && (
                            <span className="text-xs text-gray-400">No contact info</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          channel.is_active 
                            ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100'
                            : 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100'
                        }`}>
                          {channel.is_active ? '✅ Active' : '❌ Inactive'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button
                          onClick={() => handleToggleChannelStatus(channel.id)}
                          className={`px-3 py-1 rounded text-xs ${
                            channel.is_active
                              ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                              : 'bg-green-600 text-white hover:bg-green-700'
                          }`}
                        >
                          {channel.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        {channel.channel_name !== 'Direct' && (
                          <button
                            onClick={() => handleDeleteChannel(channel.id, channel.channel_name)}
                            className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {bookingChannels.length === 0 && (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  No booking channels found. Create your first channel to get started.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create Channel Modal */}
      {showCreateChannelModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Add New Booking Channel</h3>
            
            <form onSubmit={handleCreateChannel} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Channel Name *
                </label>
                <input
                  type="text"
                  value={newChannel.channel_name}
                  onChange={(e) => setNewChannel({...newChannel, channel_name: e.target.value})}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., Booking.com, Expedia"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Channel Type
                </label>
                <select
                  value={newChannel.channel_type}
                  onChange={(e) => setNewChannel({...newChannel, channel_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="OTA">OTA (Online Travel Agency)</option>
                  <option value="Direct">Direct</option>
                  <option value="Corporate">Corporate</option>
                  <option value="Walk-in">Walk-in</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Commission Rate (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={newChannel.commission_rate}
                  onChange={(e) => setNewChannel({...newChannel, commission_rate: parseFloat(e.target.value) || 0})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="e.g., 15.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Contact Email
                </label>
                <input
                  type="email"
                  value={newChannel.contact_email}
                  onChange={(e) => setNewChannel({...newChannel, contact_email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="contact@channel.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Contact Phone
                </label>
                <input
                  type="text"
                  value={newChannel.contact_phone}
                  onChange={(e) => setNewChannel({...newChannel, contact_phone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="+1-234-567-8900"
                />
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700"
                >
                  Create Channel
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateChannelModal(false)}
                  className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* System Management Tab - Admin Only */}
      {activeTab === 'system' && user?.role === 'Admin' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">🔧 System Management</h2>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Dangerous operations - Admin only
                </p>
              </div>
            </div>

            <div className="space-y-6">
              {/* Complete Database Reset Section */}
              <div className="border border-red-200 dark:border-red-800 rounded-lg p-6 bg-red-50 dark:bg-red-900/20">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-red-100 dark:bg-red-800 rounded-full flex items-center justify-center">
                      <span className="text-red-600 dark:text-red-400 text-lg">⚠️</span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-red-800 dark:text-red-200 mb-2">
                      Complete Database Reset
                    </h3>
                    <p className="text-sm text-red-700 dark:text-red-300 mb-4">
                      This will permanently delete ALL data from the system including rooms, bookings, 
                      guests, financial records, and all users except the admin account. 
                      Only hotel name and admin account will be preserved.
                    </p>
                    
                    <div className="bg-red-100 dark:bg-red-800/50 rounded-lg p-4 mb-4">
                      <h4 className="font-medium text-red-800 dark:text-red-200 mb-2">
                        ⚡ What will be deleted:
                      </h4>
                      <ul className="text-sm text-red-700 dark:text-red-300 space-y-1">
                        <li>• All rooms and room configurations</li>
                        <li>• All bookings and reservations</li>
                        <li>• All guest information and history</li>
                        <li>• All financial data (expenses, income, daily sales)</li>
                        <li>• All user accounts except admin</li>
                        <li>• All activity logs and system history</li>
                        <li>• All email configurations</li>
                      </ul>
                    </div>

                    <div className="bg-green-100 dark:bg-green-800/50 rounded-lg p-4 mb-4">
                      <h4 className="font-medium text-green-800 dark:text-green-200 mb-2">
                        ✅ What will be preserved:
                      </h4>
                      <ul className="text-sm text-green-700 dark:text-green-300 space-y-1">
                        <li>• Hotel name and basic settings</li>
                        <li>• Admin user account (you)</li>
                        <li>• System setup status</li>
                      </ul>
                    </div>
                    
                    <button
                      onClick={handleCompleteReset}
                      disabled={resetting}
                      className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                    >
                      {resetting ? (
                        <span className="flex items-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Resetting System...
                        </span>
                      ) : (
                        '🔥 COMPLETE RESET - DELETE ALL DATA'
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* System Information Section */}
              <div className="border border-blue-200 dark:border-blue-800 rounded-lg p-6 bg-blue-50 dark:bg-blue-900/20">
                <h3 className="text-lg font-medium text-blue-800 dark:text-blue-200 mb-4">
                  💡 System Information
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-blue-700 dark:text-blue-300">Current User:</span>
                    <span className="ml-2 text-blue-600 dark:text-blue-400">{user?.full_name} ({user?.username})</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-700 dark:text-blue-300">Role:</span>
                    <span className="ml-2 text-blue-600 dark:text-blue-400">{user?.role}</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-700 dark:text-blue-300">System Version:</span>
                    <span className="ml-2 text-blue-600 dark:text-blue-400">Hotel Management v2.0</span>
                  </div>
                  <div>
                    <span className="font-medium text-blue-700 dark:text-blue-300">Last Login:</span>
                    <span className="ml-2 text-blue-600 dark:text-blue-400">
                      {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Activity Logs Tab */}
      {activeTab === 'logs' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Activity Logs</h2>
              <button
                onClick={() => setShowActivityLogs(!showActivityLogs)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                {showActivityLogs ? 'Hide Logs' : 'Show Logs'}
              </button>
            </div>
            
            {showActivityLogs && (
              <div className="space-y-4">
                {activityLogs.length > 0 ? (
                  <>
                    <div className="space-y-3">
                      {activityLogs.map((log, index) => (
                        <div key={index} className="border dark:border-gray-600 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <span className={`px-2 py-1 text-xs rounded-full ${
                                  log.action.includes('created') || log.action.includes('added')
                                    ? 'bg-green-100 text-green-800'
                                    : log.action.includes('deleted') || log.action.includes('cancelled')
                                    ? 'bg-red-100 text-red-800'
                                    : log.action.includes('updated') || log.action.includes('checked')
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {log.action.replace('_', ' ').toUpperCase()}
                                </span>
                                <span className="text-sm font-medium text-gray-900 dark:text-white">
                                  {log.user_name}
                                </span>
                                <span className="text-sm text-gray-500 dark:text-gray-400">
                                  {new Date(log.timestamp).toLocaleString()}
                                </span>
                              </div>
                              <p className="text-sm text-gray-700 dark:text-gray-300">{log.description}</p>
                              {log.entity_type && (
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                  Entity: {log.entity_type}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Pagination */}
                    {totalPages > 1 && (
                      <div className="flex justify-center space-x-2 mt-6">
                        <button
                          onClick={() => fetchActivityLogs(currentPage - 1)}
                          disabled={currentPage <= 1}
                          className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                        >
                          Previous
                        </button>
                        
                        <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded">
                          Page {currentPage} of {totalPages}
                        </span>
                        
                        <button
                          onClick={() => fetchActivityLogs(currentPage + 1)}
                          disabled={currentPage >= totalPages}
                          className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No activity logs found.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Create New User</h3>
            
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Username *
                </label>
                <input
                  type="text"
                  value={newUser.username}
                  onChange={(e) => setNewUser({...newUser, username: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter username"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Password *
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter password"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Full Name *
                </label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter full name"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Role
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({...newUser, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="Staff">Staff</option>
                  <option value="Manager">Manager</option>
                  <option value="Admin">Admin</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="Enter email (optional)"
                />
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowCreateUserModal(false)}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Create User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

// Main App Component (Protected Content)
function AppContent() {
  const [hotelSettings, setHotelSettings] = useState({
    hotel_name: 'Hotel Management System',
    hotel_logo: '',
  });

  // Set dark mode on app load
  useEffect(() => {
    document.documentElement.classList.add('dark');
  }, []);

  // Fetch hotel settings for header
  useEffect(() => {
    fetchHotelSettings();
  }, []);

  const fetchHotelSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setHotelSettings({
        hotel_name: response.data.hotel_name || 'Hotel Management System',
        hotel_logo: response.data.hotel_logo || '',
      });
    } catch (error) {
      console.error('Error fetching hotel settings:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <BrowserRouter>
        {/* Header */}
        <header className="bg-gray-800 shadow-sm border-b border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 sm:space-x-3 min-w-0 flex-1">
                {hotelSettings.hotel_logo ? (
                  <img 
                    src={hotelSettings.hotel_logo} 
                    alt="Hotel Logo"
                    className="h-6 w-6 sm:h-8 sm:w-8 object-contain bg-white rounded flex-shrink-0"
                  />
                ) : (
                  <div className="text-lg sm:text-2xl flex-shrink-0">🏨</div>
                )}
                <h1 className="text-lg sm:text-2xl font-bold text-white truncate">{hotelSettings.hotel_name}</h1>
              </div>
              <div className="flex-shrink-0">
                <RealTimeClock />
              </div>
            </div>
          </div>
        </header>

        {/* Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className="bg-gray-900">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/restaurant" element={<Restaurant />} />
            <Route path="/rooms" element={<Rooms />} />
            <Route path="/guests" element={<Guests />} />
            <Route path="/bookings" element={<Bookings />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/commissions" element={<Commissions />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </BrowserRouter>
    </div>
  );
}

// Main App Component with Authentication
function App() {
  return (
    <FinancialProvider>
      <AuthProvider>
        <ProtectedRoute>
          <AppContent />
        </ProtectedRoute>
      </AuthProvider>
    </FinancialProvider>
  );
}

export default App;