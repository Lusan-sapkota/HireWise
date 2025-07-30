import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { 
  Bot, 
  Heart, 
  MessageCircle, 
  Share2, 
  Briefcase, 
  MapPin, 
  DollarSign,
  TrendingUp,
  Clock,
  Star,
  Users,
  Eye,
  Zap,
  Target,
  Award,
  Plus,
  Send,
  Search,
  UserPlus,
  UserCheck,
  Building,
  Mail,
  Phone,
  Loader2,
  Filter,
  Globe,
  CheckCircle,
  Activity
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { user, userProfile, isAuthenticated } = useAuth();
  const [connections, setConnections] = useState([]);
  const [suggestedConnections, setSuggestedConnections] = useState([]);
  const [networkActivity, setNetworkActivity] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'feed' | 'network' | 'discover'>('feed');

  // Load network data
  useEffect(() => {
    if (isAuthenticated && user) {
      loadNetworkData();
      
      // Set up periodic refresh
      const networkInterval = setInterval(() => {
        loadNetworkData();
      }, 120000); // Refresh every 2 minutes

      return () => {
        clearInterval(networkInterval);
      };
    }
  }, [isAuthenticated, user]);

  const loadNetworkData = async () => {
    setIsLoading(true);
    try {
      // Load connections with fallback
      try {
        const connectionsResponse = await apiService.getConnections();
        setConnections(connectionsResponse.data.results || []);
      } catch (error: any) {
        if (error.response?.status === 404) {
          console.log('Connections API not available, using mock data');
          setConnections(mockConnections);
        } else {
          throw error;
        }
      }

      // Load suggested connections with fallback
      try {
        const suggestionsResponse = await apiService.getSuggestedConnections();
        setSuggestedConnections(suggestionsResponse.data.results || []);
      } catch (error: any) {
        if (error.response?.status === 404) {
          console.log('Suggestions API not available, using mock data');
          setSuggestedConnections(mockSuggestedConnections);
        } else {
          throw error;
        }
      }

      // Load network activity with fallback
      try {
        const activityResponse = await apiService.getNetworkActivity();
        setNetworkActivity(activityResponse.data.results || []);
      } catch (error: any) {
        if (error.response?.status === 404) {
          console.log('Network activity API not available, using mock data');
          setNetworkActivity(mockNetworkActivity);
        } else {
          throw error;
        }
      }
    } catch (error) {
      console.error('Failed to load network data:', error);
      // Use mock data as complete fallback
      setConnections(mockConnections);
      setSuggestedConnections(mockSuggestedConnections);
      setNetworkActivity(mockNetworkActivity);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConnect = async (userId: string) => {
    try {
      await apiService.sendConnectionRequest(userId);
      // Update UI optimistically
      setSuggestedConnections(prev => 
        prev.map(conn => 
          conn.id === userId 
            ? { ...conn, connection_status: 'pending' }
            : conn
        )
      );
    } catch (error) {
      console.error('Failed to send connection request:', error);
    }
  };

  const handleAcceptConnection = async (requestId: string) => {
    try {
      await apiService.acceptConnectionRequest(requestId);
      loadNetworkData(); // Refresh data
    } catch (error) {
      console.error('Failed to accept connection:', error);
    }
  };

  // Mock data for fallback
  const mockConnections = [
    {
      id: '1',
      name: 'Sarah Chen',
      title: 'Senior Product Manager at Microsoft',
      avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150',
      mutual_connections: 12,
      is_online: true,
      last_activity: '2 hours ago'
    },
    {
      id: '2', 
      name: 'Mike Rodriguez',
      title: 'Full Stack Developer at Google',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150',
      mutual_connections: 8,
      is_online: false,
      last_activity: '1 day ago'
    }
  ];

  const mockSuggestedConnections = [
    {
      id: '3',
      name: 'Emily Johnson',
      title: 'UX Designer at Adobe',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150',
      mutual_connections: 5,
      connection_reason: 'Works in Design',
      connection_status: 'none'
    },
    {
      id: '4',
      name: 'David Kim',
      title: 'Software Engineer at Netflix',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
      mutual_connections: 3,
      connection_reason: 'Similar background',
      connection_status: 'none'
    }
  ];

  const mockNetworkActivity = [
    {
      id: '1',
      type: 'promotion',
      user: { name: 'Sarah Chen', avatar: 'https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150' },
      content: 'got promoted to Senior Product Manager',
      timestamp: '2 hours ago'
    },
    {
      id: '2',
      type: 'job_change',
      user: { name: 'Mike Rodriguez', avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150' },
      content: 'started a new position at Google',
      timestamp: '1 day ago'
    }
  ];

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Please Sign In
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Sign in to access your professional network and dashboard.
          </p>
          <Link to="/signin">
            <Button>Sign In</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Professional Network
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Connect, discover, and grow your professional network
              </p>
            </div>
            
            {/* Search */}
            <div className="flex items-center space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search professionals..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Button variant="outline" size="sm">
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-8 border-b border-gray-200 dark:border-gray-700">
            {[
              { id: 'feed', label: 'Feed', icon: Globe },
              { id: 'network', label: 'My Network', icon: Users },
              { id: 'discover', label: 'Discover', icon: Search }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 xl:px-8 py-4 sm:py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
          
          {/* Left Sidebar */}
          <div className="lg:col-span-3 space-y-4 sm:space-y-6">
            {/* Profile Summary Card */}
            <Card>
              <div className="relative">
                <div className="h-20 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-t-lg"></div>
                <div className="px-4 sm:px-6 pb-4 sm:pb-6">
                  <div className="relative -mt-10 mb-4">
                    <img
                      src={user?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent((user?.first_name || '') + ' ' + (user?.last_name || ''))}&background=6366f1&color=fff`}
                      alt={`${user?.first_name} ${user?.last_name}`}
                      className="w-20 h-20 rounded-full border-4 border-white dark:border-gray-800 shadow-lg"
                    />
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">
                    {user?.first_name} {user?.last_name}
                  </h3>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {userProfile?.bio || `${user?.user_type === 'job_seeker' ? 'Job Seeker' : 'Recruiter'}`}
                  </p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Connections</span>
                      <span className="text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400">
                        {connections.length}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Network</span>
                      <span className="text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400">
                        {suggestedConnections.length} suggestions
                      </span>
                    </div>
                  </div>
                  <Link to="/profile">
                    <Button variant="outline" size="sm" className="w-full mt-4">
                      View Profile
                    </Button>
                  </Link>
                </div>
              </div>
            </Card>

            {/* AI Insights Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Zap className="w-4 h-4 text-white" />
                  </div>
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">AI Insights</h3>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="p-2 sm:p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-800">
                    <div className="flex items-center space-x-2 mb-2">
                      <Target className="w-4 h-4 text-emerald-600" />
                      <span className="text-xs sm:text-sm font-medium text-emerald-800 dark:text-emerald-200">Profile Optimization</span>
                    </div>
                    <p className="text-xs sm:text-sm text-emerald-700 dark:text-emerald-300">
                      Add 2 more skills to increase your profile strength to 95%
                    </p>
                  </div>
                  
                  <div className="p-2 sm:p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-200 dark:border-indigo-800">
                    <div className="flex items-center space-x-2 mb-2">
                      <Award className="w-4 h-4 text-indigo-600" />
                      <span className="text-xs sm:text-sm font-medium text-indigo-800 dark:text-indigo-200">Interview Ready</span>
                    </div>
                    <p className="text-xs sm:text-sm text-indigo-700 dark:text-indigo-300">
                      Your last AI interview score: 85%. Practice more to reach 90%+
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
              <CardHeader>
                <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">Quick Actions</h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 sm:space-y-3">
                  <Link to="/ai-interview">
                    <Button variant="secondary" size="sm" className="w-full justify-start">
                      <Bot className="w-4 h-4 mr-2" />
                      Start AI Interview
                    </Button>
                  </Link>
                  <Link to="/jobs">
                    <Button variant="outline" size="sm" className="w-full justify-start">
                      <Briefcase className="w-4 h-4 mr-2" />
                      Browse Jobs
                    </Button>
                  </Link>
                  <Button variant="ghost" size="sm" className="w-full justify-start">
                    <Users className="w-4 h-4 mr-2" />
                    Find Connections
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Main Feed */}
          <div className="lg:col-span-6 space-y-4 sm:space-y-6">
            {/* Create Post */}
            <Card>
              <CardContent className="p-4 sm:p-6">
                <div className="flex space-x-4">
                  <img
                    src={user?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent((user?.first_name || '') + ' ' + (user?.last_name || ''))}&background=6366f1&color=fff`}
                    alt="Your avatar"
                    className="w-12 h-12 rounded-full"
                  />
                  <div className="flex-1">
                    <button className="w-full text-left p-4 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400 hover:border-indigo-400 dark:hover:border-indigo-500 hover:bg-indigo-50 dark:hover:bg-indigo-900/10 transition-all">
                      <span className="text-sm sm:text-base">Share your professional update, achievement, or insight...</span>
                    </button>
                    <div className="flex items-center justify-between mt-4">
                      <div className="flex space-x-2 sm:space-x-4">
                        <button className="flex items-center space-x-2 text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400">
                          <Plus className="w-4 h-4" />
                          <span className="text-xs sm:text-sm">Photo</span>
                        </button>
                        <button className="flex items-center space-x-2 text-gray-500 hover:text-indigo-600 dark:hover:text-indigo-400">
                          <Briefcase className="w-4 h-4" />
                          <span className="text-xs sm:text-sm hidden sm:inline">Job Update</span>
                          <span className="text-xs sm:text-sm sm:hidden">Job</span>
                        </button>
                      </div>
                      <Button size="sm" disabled>
                        <Send className="w-4 h-4 mr-2" />
                        Post
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Recommendations Banner */}
            <Card className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white">
              <CardContent className="p-4 sm:p-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between space-y-3 sm:space-y-0">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold mb-1 sm:mb-2">🎯 AI Found Perfect Matches!</h3>
                    <p className="text-sm sm:text-base text-indigo-100">3 new job opportunities with 90%+ compatibility</p>
                  </div>
                  <Link to="/jobs">
                    <Button className="bg-white text-indigo-600 hover:bg-gray-100 w-full sm:w-auto">
                      View Jobs
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Tab Content */}
            {activeTab === 'feed' && (
              <div className="space-y-6">
                {/* Sample Feed Content */}
                <Card>
                  <CardContent className="p-6 text-center">
                    <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Your Professional Feed
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Stay updated with your network's professional activities and industry insights.
                    </p>
                    <Button>
                      <Plus className="w-4 h-4 mr-2" />
                      Create Your First Post
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'network' && (
              <div className="space-y-6">
                {/* My Connections */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      My Connections ({connections.length})
                    </h3>
                  </CardHeader>
                  <CardContent>
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                      </div>
                    ) : connections.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {connections.map((connection: any) => (
                          <div key={connection.id} className="flex items-center space-x-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                            <div className="relative">
                              <img
                                src={connection.avatar || `https://ui-avatars.io/api/?name=${encodeURIComponent(connection.name)}&background=6366f1&color=fff`}
                                alt={connection.name}
                                className="w-12 h-12 rounded-full"
                              />
                              {connection.is_online && (
                                <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-white dark:border-gray-700 rounded-full"></div>
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-gray-900 dark:text-white truncate">
                                {connection.name}
                              </h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                                {connection.title}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-500">
                                {connection.mutual_connections} mutual connections
                              </p>
                            </div>
                            <Button variant="outline" size="sm">
                              <Mail className="w-4 h-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                          No connections yet
                        </h4>
                        <p className="text-gray-600 dark:text-gray-400 mb-4">
                          Start building your professional network by connecting with colleagues and industry professionals.
                        </p>
                        <Button onClick={() => setActiveTab('discover')}>
                          <Search className="w-4 h-4 mr-2" />
                          Discover People
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === 'discover' && (
              <div className="space-y-6">
                {/* Suggested Connections */}
                <Card>
                  <CardHeader>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      People You May Know
                    </h3>
                  </CardHeader>
                  <CardContent>
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                      </div>
                    ) : suggestedConnections.length > 0 ? (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        {suggestedConnections.map((suggestion: any) => (
                          <div key={suggestion.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                            <div className="text-center">
                              <img
                                src={suggestion.avatar || `https://ui-avatars.io/api/?name=${encodeURIComponent(suggestion.name)}&background=6366f1&color=fff`}
                                alt={suggestion.name}
                                className="w-16 h-16 rounded-full mx-auto mb-3"
                              />
                              <h4 className="font-medium text-gray-900 dark:text-white mb-1">
                                {suggestion.name}
                              </h4>
                              <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                                {suggestion.title}
                              </p>
                              <p className="text-xs text-gray-500 dark:text-gray-500 mb-3">
                                {suggestion.mutual_connections} mutual connections • {suggestion.connection_reason}
                              </p>
                              <div className="flex space-x-2">
                                {suggestion.connection_status === 'pending' ? (
                                  <Button variant="outline" size="sm" disabled className="flex-1">
                                    <Clock className="w-4 h-4 mr-2" />
                                    Pending
                                  </Button>
                                ) : (
                                  <Button 
                                    onClick={() => handleConnect(suggestion.id)}
                                    size="sm" 
                                    className="flex-1"
                                  >
                                    <UserPlus className="w-4 h-4 mr-2" />
                                    Connect
                                  </Button>
                                )}
                                <Button variant="outline" size="sm">
                                  <Mail className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h4 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                          No suggestions available
                        </h4>
                        <p className="text-gray-600 dark:text-gray-400">
                          Complete your profile to get better connection suggestions.
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </div>

          {/* Right Panel */}
          <div className="lg:col-span-3 space-y-4 sm:space-y-6">
            {/* AI Assistant */}
            <Card className="border-2 border-violet-200 dark:border-violet-800">
              <CardHeader>
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-r from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">AI Career Coach</h3>
                    <p className="text-xs text-violet-600 dark:text-violet-400">Online & Ready</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="p-2 sm:p-3 bg-violet-50 dark:bg-violet-900/20 rounded-lg">
                    <p className="text-xs sm:text-sm text-violet-800 dark:text-violet-200 mb-2">
                      💡 <strong>Today's Tip:</strong>
                    </p>
                    <p className="text-xs sm:text-sm text-violet-700 dark:text-violet-300">
                      Your profile views increased 23% this week! Consider posting more about your React expertise.
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">Interview Readiness</span>
                      <span className="text-xs sm:text-sm font-medium text-emerald-600">85%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full w-4/5"></div>
                    </div>
                  </div>

                  <Link to="/ai-interview">
                    <Button variant="secondary" size="sm" className="w-full">
                      <Bot className="w-4 h-4 mr-2" />
                      Start AI Session
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Trending Jobs */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">Trending for You</h3>
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 sm:space-y-4">
                  <div className="group cursor-pointer">
                    <div className="flex items-start space-x-3 p-2 sm:p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                      <div className="w-8 sm:w-10 h-8 sm:h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                        <Building className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 dark:text-white text-xs sm:text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                          Senior React Developer
                        </h4>
                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">TechCorp Inc.</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Star className="w-3 h-3 text-emerald-500" />
                          <span className="text-xs text-emerald-600 font-medium">
                            92% match
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="group cursor-pointer">
                    <div className="flex items-start space-x-3 p-2 sm:p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                      <div className="w-8 sm:w-10 h-8 sm:h-10 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center">
                        <Building className="w-4 h-4 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 dark:text-white text-xs sm:text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                          Full Stack Engineer
                        </h4>
                        <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">StartupXYZ</p>
                        <div className="flex items-center space-x-2 mt-1">
                          <Star className="w-3 h-3 text-emerald-500" />
                          <span className="text-xs text-emerald-600 font-medium">
                            88% match
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <Link to="/jobs">
                  <Button variant="ghost" size="sm" className="w-full mt-4">
                    View All Jobs
                  </Button>
                </Link>
              </CardContent>
            </Card>

            {/* Network Activity */}
            <Card>
              <CardHeader>
                <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">Network Activity</h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 sm:space-y-3">
                  {networkActivity.length > 0 ? (
                    networkActivity.map((activity: any) => (
                      <div key={activity.id} className="flex items-center space-x-3">
                        <div className={`w-2 h-2 rounded-full ${
                          activity.type === 'promotion' ? 'bg-emerald-500' :
                          activity.type === 'job_change' ? 'bg-indigo-500' :
                          'bg-violet-500'
                        }`}></div>
                        <div className="flex-1">
                          <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                            <span className="font-medium">{activity.user.name}</span> {activity.content}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{activity.timestamp}</p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-center py-4">
                      <Activity className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        No recent network activity
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};