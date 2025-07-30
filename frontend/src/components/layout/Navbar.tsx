import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '../../contexts/useTheme';
import { useAuth } from '../../contexts/AuthContext';
import { apiService } from '../../services/api';
import { 
  Home, 
  Users, 
  Briefcase, 
  User, 
  Bot, 
  Moon, 
  Sun, 
  Bell,
  Search,
  Menu,
  X,
  ChevronDown,
  Settings,
  LogOut,
  MessageSquare,
  LogIn,
  UserPlus,
  Check,
  Trash2,
  MoreHorizontal,
} from 'lucide-react';

const logo = '/logo.png';

interface NavbarProps {
  isLoggedIn?: boolean;
}

interface Notification {
  id: string;
  message: string;
  created_at: string;
  unread: boolean;
  type?: 'info' | 'success' | 'warning' | 'error';
}

export const Navbar: React.FC<NavbarProps> = ({ isLoggedIn: propIsLoggedIn }) => {
  const { theme, toggleTheme } = useTheme();
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isNotificationModalOpen, setIsNotificationModalOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  // Use auth context state or prop fallback
  const isLoggedIn = propIsLoggedIn !== undefined ? propIsLoggedIn : isAuthenticated;

  // Load real-time notifications
  useEffect(() => {
    if (isLoggedIn) {
      loadNotifications();
      
      // Set up periodic refresh for notifications (fallback for WebSocket)
      const notificationInterval = setInterval(() => {
        loadNotifications();
      }, 30000); // Refresh every 30 seconds

      return () => {
        clearInterval(notificationInterval);
      };
    }
  }, [isLoggedIn]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      if (!target.closest('.notification-dropdown') && !target.closest('.notification-button')) {
        setIsNotificationOpen(false);
      }
      if (!target.closest('.profile-dropdown') && !target.closest('.profile-button')) {
        setIsProfileDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadNotifications = async () => {
    try {
      const response = await apiService.getNotifications();
      setNotifications(response.data.results || []);
      setUnreadCount(response.data.results?.filter(n => n.unread).length || 0);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const markAsRead = async (notificationId: string) => {
    try {
      await apiService.markNotificationAsRead(notificationId);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, unread: false } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await apiService.markAllNotificationsAsRead();
      setNotifications(notifications.map(n => ({ ...n, unread: false })));
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      await apiService.deleteNotification(notificationId);
      const deletedNotification = notifications.find(n => n.id === notificationId);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      if (deletedNotification?.unread) {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  // Navigation items for logged-in users
  const loggedInNavigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Network', href: '/dashboard', icon: Users },
    { name: 'Jobs', href: '/jobs', icon: Briefcase },
    { name: 'AI Interview', href: '/ai-interview', icon: Bot },
    { name: 'Messages', href: '/messages', icon: MessageSquare },
  ];

  // Navigation items for logged-out users
  const loggedOutNavigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Jobs', href: '/jobs', icon: Briefcase },
    { name: 'AI Interview', href: '/ai-interview', icon: Bot },
  ];

  const navigation = isLoggedIn ? loggedInNavigation : loggedOutNavigation;

  const handleLogout = async () => {
    try {
      await logout();
      setIsProfileDropdownOpen(false);
      setIsMobileMenuOpen(false);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path: string) => location.pathname === path;

  const openNotificationModal = () => {
    setIsNotificationModalOpen(true);
    setIsNotificationOpen(false);
  };

  // Notifications Modal Component
  const NotificationsModal = () => {
    if (!isNotificationModalOpen) return null;

    return (
      <div className="fixed inset-0 z-[60] overflow-hidden">
        {/* Backdrop */}
        <div 
          className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity"
          onClick={() => setIsNotificationModalOpen(false)}
        />
        
        {/* Modal */}
        <div className="fixed inset-x-0 top-0 bottom-0 sm:inset-4 sm:top-8 sm:bottom-8 flex items-center justify-center p-4 sm:p-0">
          <div className="bg-white dark:bg-gray-800 rounded-none sm:rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 w-full h-full sm:w-full sm:max-w-2xl sm:h-auto sm:max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
              <div className="flex items-center space-x-3">
                <Bell className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  All Notifications
                </h2>
                {unreadCount > 0 && (
                  <span className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 text-xs font-medium px-2.5 py-0.5 rounded-full">
                    {unreadCount} new
                  </span>
                )}
              </div>
              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <button
                    onClick={markAllAsRead}
                    className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium"
                  >
                    Mark all read
                  </button>
                )}
                <button
                  onClick={() => setIsNotificationModalOpen(false)}
                  className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {notifications.length > 0 ? (
                <div className="divide-y divide-gray-100 dark:divide-gray-700">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 sm:p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group ${
                        notification.unread ? 'bg-indigo-50/50 dark:bg-indigo-900/10' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            {notification.unread && (
                              <div className="w-2 h-2 bg-indigo-600 rounded-full flex-shrink-0" />
                            )}
                            <p className={`text-sm sm:text-base ${
                              notification.unread 
                                ? 'font-medium text-gray-900 dark:text-white' 
                                : 'text-gray-700 dark:text-gray-300'
                            }`}>
                              {notification.message}
                            </p>
                          </div>
                          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity">
                          {notification.unread && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="p-1.5 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                              title="Mark as read"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => deleteNotification(notification.id)}
                            className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                            title="Delete notification"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12 sm:py-16 px-4">
                  <Bell className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    No notifications
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 text-center">
                    When you get notifications, they'll show up here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <nav className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2 sm:space-x-3 flex-shrink-0">
              <div className="flex bg-gradient-to-t from-indigo-500 to-violet-500 items-center justify-center shadow-lg rounded-lg">
                <img src={logo} alt="HireWise Logo" className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12" />
              </div>
              <div className="flex flex-col">
                <span className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">HireWise</span>
                <span className="text-xs text-violet-600 dark:text-violet-400 font-medium hidden sm:block">AI Powered</span>
              </div>
            </Link>

            {/* Search Bar - Desktop (only for logged-in users) */}
            {isLoggedIn && (
              <div className="hidden lg:flex flex-1 max-w-lg mx-6 xl:mx-8">
                <div className="relative w-full">
                  <Search className="absolute left-3 lg:left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 lg:w-5 lg:h-5" />
                  <input
                    type="text"
                    placeholder="Search jobs, people, companies..."
                    className="w-full pl-10 lg:pl-12 pr-4 py-2.5 lg:py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-sm lg:text-base"
                  />
                </div>
              </div>
            )}

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center space-x-1 xl:space-x-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex flex-col items-center px-2 xl:px-3 py-2 rounded-lg text-xs font-medium transition-all hover:bg-gray-100 dark:hover:bg-gray-800 ${
                      isActive(item.href)
                        ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    <Icon className="w-5 h-5 mb-1" />
                    <span className="whitespace-nowrap">{item.name}</span>
                  </Link>
                );
              })}
            </div>

            {/* Right side actions */}
            <div className="flex items-center space-x-1 sm:space-x-2">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Toggle theme"
              >
                {theme === 'light' ? <Moon className="w-5 h-5 sm:w-6 sm:h-6" /> : <Sun className="w-5 h-5 sm:w-6 sm:h-6" />}
              </button>

              {isLoggedIn ? (
                <>
                  {/* Notifications (only for logged-in users) */}
                  <div className="relative">
                    <button
                      onClick={() => setIsNotificationOpen(!isNotificationOpen)}
                      className="notification-button p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors relative"
                      aria-label="Notifications"
                    >
                      <Bell className="w-5 h-5 sm:w-6 sm:h-6" />
                      {unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                          {unreadCount > 99 ? '99+' : unreadCount}
                        </span>
                      )}
                    </button>
                  </div>
                  {/* Enhanced Notifications Dropdown - Mobile Responsive Fix */}
                  {isNotificationOpen && (
                    <div className="notification-dropdown fixed inset-x-0 top-16 sm:absolute sm:right-0 sm:top-auto sm:inset-x-auto sm:mt-2 sm:w-96 bg-white dark:bg-gray-800 shadow-xl border-t sm:border border-gray-200 dark:border-gray-700 z-50 sm:rounded-xl max-h-[calc(100vh-4rem)] sm:max-h-96">
                      {/* Header */}
                      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 sticky top-0">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold text-gray-900 dark:text-white text-base">
                            Notifications
                          </h3>
                          {unreadCount > 0 && (
                            <span className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 text-xs font-medium px-2 py-0.5 rounded-full">
                              {unreadCount}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          {unreadCount > 0 && (
                            <button
                              onClick={markAllAsRead}
                              className="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium"
                            >
                              Mark all read
                            </button>
                          )}
                          {/* Close button for mobile */}
                          <button
                            onClick={() => setIsNotificationOpen(false)}
                            className="sm:hidden p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            <X className="w-5 h-5" />
                          </button>
                        </div>
                      </div>

                      {/* Content - Scrollable */}
                      <div className="overflow-y-auto flex-1" style={{ maxHeight: 'calc(100vh - 12rem)' }}>
                        {notifications.length > 0 ? (
                          <>
                            {notifications.slice(0, 8).map((notification) => (
                              <div
                                key={notification.id}
                                className={`p-4 border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group ${
                                  notification.unread ? 'bg-indigo-50 dark:bg-indigo-900/10' : ''
                                }`}
                              >
                                <div className="flex items-start space-x-3">
                                  {notification.unread && (
                                    <div className="w-2 h-2 bg-indigo-600 rounded-full flex-shrink-0 mt-2" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm text-gray-900 dark:text-white leading-relaxed">
                                      {notification.message}
                                    </p>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                                      {new Date(notification.created_at).toLocaleString()}
                                    </p>
                                  </div>
                                  <div className="flex flex-col space-y-1 opacity-0 group-hover:opacity-100 sm:opacity-100 transition-opacity">
                                    {notification.unread && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          markAsRead(notification.id);
                                        }}
                                        className="p-1.5 text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                                        title="Mark as read"
                                      >
                                        <Check className="w-4 h-4" />
                                      </button>
                                    )}
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        deleteNotification(notification.id);
                                      }}
                                      className="p-1.5 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
                                      title="Delete"
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </button>
                                  </div>
                                </div>
                              </div>
                            ))}
                            {notifications.length > 8 && (
                              <div className="p-3 bg-gray-50 dark:bg-gray-700/50 text-center text-sm text-gray-600 dark:text-gray-400 border-b border-gray-100 dark:border-gray-700">
                                And {notifications.length - 8} more notifications...
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                            <Bell className="w-16 h-16 mx-auto mb-4 opacity-50" />
                            <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                              No notifications yet
                            </h4>
                            <p className="text-sm">
                              We'll notify you when something arrives!
                            </p>
                          </div>
                        )}
                      </div>

                      {/* Footer - Sticky */}
                      <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 sticky bottom-0">
                        <button
                          onClick={openNotificationModal}
                          className="w-full text-center text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 font-medium py-3 px-4 rounded-lg hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors border border-indigo-200 dark:border-indigo-800"
                        >
                          View all notifications
                        </button>
                      </div>
                    </div>
                  )}


                  {/* Profile Dropdown - Rest of the existing profile dropdown code remains the same */}
                  <div className="relative">
                    <button
                      onClick={() => setIsProfileDropdownOpen(!isProfileDropdownOpen)}
                      className="profile-button flex items-center space-x-2 sm:space-x-3 p-1.5 sm:p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                      aria-label="Profile menu"
                    >
                      <img
                        src={user?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent(user?.first_name + ' ' + user?.last_name)}&background=6366f1&color=fff`}
                        alt={user?.first_name + ' ' + user?.last_name}
                        className="w-7 h-7 sm:w-8 sm:h-8 rounded-full ring-2 ring-indigo-500 object-cover"
                      />
                      <div className="hidden md:block text-left">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-24 lg:max-w-32">
                          {user?.first_name} {user?.last_name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">View profile</p>
                      </div>
                      <ChevronDown className="w-3 h-3 sm:w-4 sm:h-4 text-gray-500 dark:text-gray-400" />
                    </button>

                    {/* Profile Dropdown Menu */}
                    {isProfileDropdownOpen && (
                      <div className="profile-dropdown absolute right-0 mt-2 w-56 sm:w-64 bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 z-50">
                        <div className="p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700">
                          <div className="flex items-center space-x-3">
                            <img
                              src={user?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent(user?.first_name + ' ' + user?.last_name)}&background=6366f1&color=fff`}
                              alt={user?.first_name + ' ' + user?.last_name}
                              className="w-10 h-10 sm:w-12 sm:h-12 rounded-full object-cover"
                            />
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-gray-900 dark:text-white text-sm sm:text-base truncate">
                                {user?.first_name} {user?.last_name}
                              </p>
                              <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                                {user?.user_type === 'job_seeker' ? 'Job Seeker' : 'Recruiter'}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="py-1 sm:py-2">
                          <Link
                            to="/profile"
                            className="flex items-center space-x-3 px-3 sm:px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            onClick={() => setIsProfileDropdownOpen(false)}
                          >
                            <User className="w-4 h-4" />
                            <span>View Profile</span>
                          </Link>
                          <Link
                            to="/settings"
                            className="flex items-center space-x-3 px-3 sm:px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                            onClick={() => setIsProfileDropdownOpen(false)}
                          >
                            <Settings className="w-4 h-4" />
                            <span>Settings</span>
                          </Link>
                          <button 
                            onClick={handleLogout}
                            className="flex items-center space-x-3 px-3 sm:px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 w-full text-left transition-colors"
                          >
                            <LogOut className="w-4 h-4" />
                            <span>Sign Out</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <>
                  {/* Login/Signup buttons for logged-out users */}
                  <div className="hidden sm:flex items-center space-x-2 lg:space-x-3">
                    <Link
                      to="/signin"
                      className="flex items-center space-x-1 lg:space-x-2 px-3 lg:px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                    >
                      <LogIn className="w-4 h-4" />
                      <span className="hidden lg:inline">Log In</span>
                    </Link>
                    <Link
                      to="/signup"
                      className="flex items-center space-x-1 lg:space-x-2 px-3 lg:px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
                    >
                      <UserPlus className="w-4 h-4" />
                      <span>Sign Up</span>
                    </Link>
                  </div>
                </>
              )}

              {/* Mobile menu button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                aria-label="Toggle mobile menu"
              >
                {isMobileMenuOpen ? <X className="w-5 h-5 sm:w-6 sm:h-6" /> : <Menu className="w-5 h-5 sm:w-6 sm:h-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Navigation - Rest of the existing mobile navigation code remains the same */}
          {isMobileMenuOpen && (
            <div className="lg:hidden border-t border-gray-200 dark:border-gray-700 py-3 bg-white dark:bg-gray-900">
              {/* Mobile Search (only for logged-in users) */}
              {isLoggedIn && (
                <div className="px-2 sm:px-3 mb-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4 sm:w-5 sm:h-5" />
                    <input
                      type="text"
                      placeholder="Search..."
                      className="w-full pl-9 sm:pl-10 pr-4 py-2.5 sm:py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}

              {/* Mobile Navigation Items */}
              <div className="space-y-1 px-2 sm:px-3">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium transition-colors ${
                        isActive(item.href)
                          ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                          : 'text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                      }`}
                    >
                      <Icon className="w-5 h-5 flex-shrink-0" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}

                {/* Mobile Login/Signup for logged-out users */}
                {!isLoggedIn && (
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3 space-y-1">
                    <Link
                      to="/signin"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <LogIn className="w-5 h-5 flex-shrink-0" />
                      <span>Log In</span>
                    </Link>
                    <Link
                      to="/signup"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
                    >
                      <UserPlus className="w-5 h-5 flex-shrink-0" />
                      <span>Sign Up</span>
                    </Link>
                  </div>
                )}

                {/* Mobile Profile Actions (for logged-in users) */}
                {isLoggedIn && (
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3 space-y-1">
                    <Link
                      to="/profile"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <User className="w-5 h-5 flex-shrink-0" />
                      <span>View Profile</span>
                    </Link>
                    <Link
                      to="/settings"
                      onClick={() => setIsMobileMenuOpen(false)}
                      className="flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <Settings className="w-5 h-5 flex-shrink-0" />
                      <span>Settings</span>
                    </Link>
                    <button 
                      onClick={handleLogout}
                      className="flex items-center space-x-3 px-3 sm:px-4 py-3 rounded-lg text-base font-medium text-gray-700 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-800 w-full text-left transition-colors"
                    >
                      <LogOut className="w-5 h-5 flex-shrink-0" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Notifications Modal */}
      <NotificationsModal />
    </>
  );
};
