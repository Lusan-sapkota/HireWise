import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { apiService, Notification } from '../services/api';
import { 
  Bell, 
  BellOff, 
  Check, 
  CheckCheck, 
  Trash2, 
  Filter, 
  Search,
  Briefcase,
  User,
  Bot,
  Calendar,
  FileText,
  Award,
  MessageCircle,
  Settings
} from 'lucide-react';

export const Notifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filteredNotifications, setFilteredNotifications] = useState<Notification[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Mock data - replace with actual API calls
  const mockNotifications: Notification[] = [
    {
      id: '1',
      user: 'current-user',
      title: 'New Job Match Found!',
      message: 'We found 3 new job opportunities that match your profile with 90%+ compatibility.',
      notification_type: 'job_match',
      is_read: false,
      created_at: '2024-01-15T10:30:00Z',
      data: { job_count: 3, match_score: 92 }
    },
    {
      id: '2',
      user: 'current-user',
      title: 'Interview Scheduled',
      message: 'Sarah Chen from TechCorp has scheduled an interview for tomorrow at 2:00 PM.',
      notification_type: 'interview',
      is_read: false,
      created_at: '2024-01-15T09:15:00Z',
      data: { interviewer: 'Sarah Chen', company: 'TechCorp', time: '2024-01-16T14:00:00Z' }
    },
    {
      id: '3',
      user: 'current-user',
      title: 'AI Interview Analysis Complete',
      message: 'Your AI interview analysis is ready. You scored 85% with personalized feedback.',
      notification_type: 'ai_analysis',
      is_read: true,
      created_at: '2024-01-15T08:45:00Z',
      data: { score: 85, session_id: 'ai-123' }
    },
    {
      id: '4',
      user: 'current-user',
      title: 'Application Status Update',
      message: 'Your application for Senior Frontend Developer at StartupXYZ has been reviewed.',
      notification_type: 'application_update',
      is_read: true,
      created_at: '2024-01-14T16:20:00Z',
      data: { status: 'reviewed', job_title: 'Senior Frontend Developer', company: 'StartupXYZ' }
    },
    {
      id: '5',
      user: 'current-user',
      title: 'Profile View Alert',
      message: '5 recruiters viewed your profile this week. Your visibility is increasing!',
      notification_type: 'profile_activity',
      is_read: false,
      created_at: '2024-01-14T12:00:00Z',
      data: { view_count: 5, period: 'week' }
    },
    {
      id: '6',
      user: 'current-user',
      title: 'New Message',
      message: 'You have a new message from Mike Rodriguez regarding your application.',
      notification_type: 'message',
      is_read: true,
      created_at: '2024-01-14T10:30:00Z',
      data: { sender: 'Mike Rodriguez', message_id: 'msg-456' }
    },
  ];

  useEffect(() => {
    loadNotifications();
  }, []);

  useEffect(() => {
    filterNotifications();
  }, [notifications, filter, typeFilter, searchQuery]);

  const loadNotifications = async () => {
    setIsLoading(true);
    try {
      // TODO: Replace with actual API call
      // const response = await apiService.getNotifications();
      // setNotifications(response.data.results);
      
      // Using mock data for now
      setNotifications(mockNotifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filterNotifications = () => {
    let filtered = notifications;

    // Filter by read status
    if (filter === 'unread') {
      filtered = filtered.filter(n => !n.is_read);
    } else if (filter === 'read') {
      filtered = filtered.filter(n => n.is_read);
    }

    // Filter by type
    if (typeFilter !== 'all') {
      filtered = filtered.filter(n => n.notification_type === typeFilter);
    }

    // Filter by search query
    if (searchQuery) {
      filtered = filtered.filter(n => 
        n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.message.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    setFilteredNotifications(filtered);
  };

  const markAsRead = async (id: string) => {
    try {
      // TODO: Replace with actual API call
      // await apiService.markNotificationAsRead(id);
      
      setNotifications(prev => 
        prev.map(n => n.id === id ? { ...n, is_read: true } : n)
      );
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      // TODO: Replace with actual API call
      // await apiService.markAllNotificationsAsRead();
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      );
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const deleteNotification = async (id: string) => {
    try {
      // TODO: Replace with actual API call
      // await apiService.deleteNotification(id);
      
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'job_match':
        return <Briefcase className="w-5 h-5 text-indigo-600" />;
      case 'interview':
        return <Calendar className="w-5 h-5 text-green-600" />;
      case 'ai_analysis':
        return <Bot className="w-5 h-5 text-violet-600" />;
      case 'application_update':
        return <FileText className="w-5 h-5 text-blue-600" />;
      case 'profile_activity':
        return <User className="w-5 h-5 text-emerald-600" />;
      case 'message':
        return <MessageCircle className="w-5 h-5 text-orange-600" />;
      case 'achievement':
        return <Award className="w-5 h-5 text-yellow-600" />;
      default:
        return <Bell className="w-5 h-5 text-gray-600" />;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const diffInMinutes = Math.floor(diffInHours * 60);
      return `${diffInMinutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)}h ago`;
    } else if (diffInHours < 168) { // 7 days
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;
  const notificationTypes = [
    { value: 'all', label: 'All Types' },
    { value: 'job_match', label: 'Job Matches' },
    { value: 'interview', label: 'Interviews' },
    { value: 'ai_analysis', label: 'AI Analysis' },
    { value: 'application_update', label: 'Applications' },
    { value: 'profile_activity', label: 'Profile Activity' },
    { value: 'message', label: 'Messages' },
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading notifications...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
              <Bell className="w-7 h-7 mr-3 text-indigo-600" />
              Notifications
              {unreadCount > 0 && (
                <span className="ml-3 px-2 py-1 bg-red-500 text-white text-sm rounded-full">
                  {unreadCount}
                </span>
              )}
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Stay updated with your job search activities
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            {unreadCount > 0 && (
              <Button onClick={markAllAsRead} variant="outline" size="sm">
                <CheckCheck className="w-4 h-4 mr-2" />
                Mark All Read
              </Button>
            )}
            <Button variant="ghost" size="sm">
              <Settings className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search notifications..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              
              {/* Read Status Filter */}
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as 'all' | 'unread' | 'read')}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="all">All Notifications</option>
                <option value="unread">Unread ({unreadCount})</option>
                <option value="read">Read</option>
              </select>
              
              {/* Type Filter */}
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                {notificationTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Notifications List */}
        <div className="space-y-3">
          {filteredNotifications.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <BellOff className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No notifications found
                </h3>
                <p className="text-gray-600 dark:text-gray-400">
                  {searchQuery || filter !== 'all' || typeFilter !== 'all'
                    ? 'Try adjusting your filters to see more notifications.'
                    : 'You\'re all caught up! New notifications will appear here.'}
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredNotifications.map((notification) => (
              <Card
                key={notification.id}
                className={`transition-all hover:shadow-md ${
                  !notification.is_read
                    ? 'border-l-4 border-l-indigo-500 bg-indigo-50/50 dark:bg-indigo-900/10'
                    : ''
                }`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 mt-1">
                      {getNotificationIcon(notification.notification_type)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className={`text-sm font-medium ${
                            !notification.is_read
                              ? 'text-gray-900 dark:text-white'
                              : 'text-gray-700 dark:text-gray-300'
                          }`}>
                            {notification.title}
                          </h3>
                          <p className={`text-sm mt-1 ${
                            !notification.is_read
                              ? 'text-gray-700 dark:text-gray-300'
                              : 'text-gray-600 dark:text-gray-400'
                          }`}>
                            {notification.message}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                            {formatTime(notification.created_at)}
                          </p>
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-4">
                          {!notification.is_read && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => markAsRead(notification.id)}
                              className="text-indigo-600 hover:text-indigo-700"
                            >
                              <Check className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => deleteNotification(notification.id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Load More Button */}
        {filteredNotifications.length > 0 && (
          <div className="text-center mt-8">
            <Button variant="outline">
              Load More Notifications
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};