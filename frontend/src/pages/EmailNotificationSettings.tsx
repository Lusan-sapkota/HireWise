import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Mail, 
  Bell, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  Bot,
  Briefcase,
  Users,
  TrendingUp,
  Calendar,
  Settings,
  Send,
  Eye
} from 'lucide-react';

interface NotificationSettings {
  interview_reminders: boolean;
  application_updates: boolean;
  job_matches: boolean;
  network_updates: boolean;
  ai_insights: boolean;
  weekly_digest: boolean;
  message_notifications: boolean;
  profile_views: boolean;
  connection_requests: boolean;
}

export const EmailNotificationSettings: React.FC = () => {
  const { user } = useAuth();
  const [settings, setSettings] = useState<NotificationSettings>({
    interview_reminders: true,
    application_updates: true,
    job_matches: true,
    network_updates: true,
    ai_insights: true,
    weekly_digest: true,
    message_notifications: true,
    profile_views: false,
    connection_requests: true,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [testEmailSending, setTestEmailSending] = useState<string | null>(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getEmailNotificationSettings();
      setSettings(response.data);
    } catch (error: any) {
      console.error('Failed to load notification settings:', error);
      // Use default settings if API fails
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = (key: keyof NotificationSettings) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      await apiService.updateEmailNotificationSettings(settings);
      setSuccess('Notification settings updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error: any) {
      setError(error.response?.data?.message || 'Failed to update settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSendTestEmail = async (emailType: string) => {
    setTestEmailSending(emailType);
    setError('');
    setSuccess('');

    try {
      await apiService.sendTestEmail(emailType);
      setSuccess(`Test ${emailType.replace('_', ' ')} email sent successfully!`);
      setTimeout(() => setSuccess(''), 3000);
    } catch (error: any) {
      setError(error.response?.data?.message || 'Failed to send test email.');
    } finally {
      setTestEmailSending(null);
    }
  };

  const notificationCategories = [
    {
      title: 'Interview & Applications',
      icon: Bot,
      color: 'text-violet-600',
      bgColor: 'bg-violet-100 dark:bg-violet-900/20',
      settings: [
        {
          key: 'interview_reminders' as keyof NotificationSettings,
          title: 'Interview Reminders',
          description: 'Get notified about upcoming AI interviews and scheduled calls',
          testType: 'interview_reminder'
        },
        {
          key: 'application_updates' as keyof NotificationSettings,
          title: 'Application Updates',
          description: 'Receive updates when recruiters view or respond to your applications',
          testType: 'application_update'
        }
      ]
    },
    {
      title: 'Job Opportunities',
      icon: Briefcase,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100 dark:bg-blue-900/20',
      settings: [
        {
          key: 'job_matches' as keyof NotificationSettings,
          title: 'Job Matches',
          description: 'Get notified when AI finds jobs that match your profile and preferences',
          testType: 'job_match'
        },
        {
          key: 'ai_insights' as keyof NotificationSettings,
          title: 'AI Career Insights',
          description: 'Receive personalized career advice and market insights from our AI',
          testType: 'ai_insight'
        }
      ]
    },
    {
      title: 'Network & Social',
      icon: Users,
      color: 'text-green-600',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      settings: [
        {
          key: 'network_updates' as keyof NotificationSettings,
          title: 'Network Updates',
          description: 'Stay updated with your professional network\'s activities and achievements',
          testType: 'network_update'
        },
        {
          key: 'connection_requests' as keyof NotificationSettings,
          title: 'Connection Requests',
          description: 'Get notified when someone wants to connect with you',
          testType: 'connection_request'
        },
        {
          key: 'message_notifications' as keyof NotificationSettings,
          title: 'New Messages',
          description: 'Receive notifications for new messages from recruiters and connections',
          testType: 'message_notification'
        }
      ]
    },
    {
      title: 'Profile & Analytics',
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100 dark:bg-orange-900/20',
      settings: [
        {
          key: 'profile_views' as keyof NotificationSettings,
          title: 'Profile Views',
          description: 'Get notified when someone views your profile',
          testType: 'profile_view'
        },
        {
          key: 'weekly_digest' as keyof NotificationSettings,
          title: 'Weekly Digest',
          description: 'Receive a weekly summary of your activity, opportunities, and insights',
          testType: 'weekly_digest'
        }
      ]
    }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading notification settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900 rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Email Notifications
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage your email notification preferences
              </p>
            </div>
          </div>

          {/* User Email */}
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-3">
              <Mail className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Notifications will be sent to:
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {user?.email}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-6 flex items-center space-x-2 text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-6 flex items-center space-x-2 text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Notification Categories */}
        <div className="space-y-8">
          {notificationCategories.map((category) => (
            <Card key={category.title}>
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 ${category.bgColor} rounded-lg flex items-center justify-center`}>
                    <category.icon className={`w-4 h-4 ${category.color}`} />
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {category.title}
                  </h2>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {category.settings.map((setting) => (
                    <div key={setting.key} className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <label className="flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={settings[setting.key]}
                              onChange={() => handleToggle(setting.key)}
                              className="sr-only"
                            />
                            <div className={`relative w-6 h-6 rounded border-2 transition-colors ${
                              settings[setting.key]
                                ? 'bg-indigo-600 border-indigo-600'
                                : 'border-gray-300 dark:border-gray-600'
                            }`}>
                              {settings[setting.key] && (
                                <CheckCircle className="w-4 h-4 text-white absolute top-0.5 left-0.5" />
                              )}
                            </div>
                          </label>
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">
                              {setting.title}
                            </h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                              {setting.description}
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      {/* Test Email Button */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleSendTestEmail(setting.testType)}
                        disabled={testEmailSending === setting.testType || !settings[setting.key]}
                        className="ml-4"
                      >
                        {testEmailSending === setting.testType ? (
                          <>
                            <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                            Sending...
                          </>
                        ) : (
                          <>
                            <Send className="w-3 h-3 mr-1" />
                            Test
                          </>
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <Card className="mt-8">
          <CardHeader>
            <div className="flex items-center space-x-3">
              <Settings className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Quick Actions
              </h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                variant="outline"
                onClick={() => {
                  const allEnabled = Object.values(settings).every(Boolean);
                  const newSettings = Object.keys(settings).reduce((acc, key) => ({
                    ...acc,
                    [key]: !allEnabled
                  }), {} as NotificationSettings);
                  setSettings(newSettings);
                }}
                className="flex-1"
              >
                <Bell className="w-4 h-4 mr-2" />
                {Object.values(settings).every(Boolean) ? 'Disable All' : 'Enable All'}
              </Button>
              
              <Button
                variant="outline"
                onClick={() => setSettings({
                  interview_reminders: true,
                  application_updates: true,
                  job_matches: true,
                  network_updates: false,
                  ai_insights: true,
                  weekly_digest: true,
                  message_notifications: true,
                  profile_views: false,
                  connection_requests: true,
                })}
                className="flex-1"
              >
                <Settings className="w-4 h-4 mr-2" />
                Reset to Recommended
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="px-8"
          >
            {isSaving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Save Settings
              </>
            )}
          </Button>
        </div>

        {/* Help Text */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            You can change these settings at any time. Critical notifications like security alerts will always be sent.
          </p>
        </div>
      </div>
    </div>
  );
};