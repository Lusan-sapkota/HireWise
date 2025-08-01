import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import Footer from '../components/layout/Footer';
import {
  Bot,
  Users,
  Briefcase,
  TrendingUp,
  Star,
  CheckCircle,
  Plus,
  MessageSquare,
  Share2,
  BookmarkPlus,
  Clock,
  ThumbsUp,
  Calendar,
  Target,
  Loader2
} from 'lucide-react';

interface HomePageProps {
  isLoggedIn?: boolean;
}

export const HomePage: React.FC<HomePageProps> = ({ isLoggedIn: propIsLoggedIn }) => {
  const { user, isAuthenticated, userProfile } = useAuth();
  const [recentPosts, setRecentPosts] = useState([]);
  const [todayStats, setTodayStats] = useState({
    profileViews: 0,
    newConnections: 0,
    jobMatches: 0,
    interviewScore: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [jobRecommendations, setJobRecommendations] = useState([]);

  // Use auth context state or prop fallback
  const isLoggedIn = propIsLoggedIn !== undefined ? propIsLoggedIn : isAuthenticated;

  const quickActions = [
    { icon: Bot, label: 'Practice Interview', href: '/ai-interview', color: 'bg-violet-500' },
    { icon: Briefcase, label: 'Browse Jobs', href: '/jobs', color: 'bg-blue-500' },
    { icon: Users, label: 'Network', href: '/dashboard', color: 'bg-green-500' },
    { icon: MessageSquare, label: 'Messages', href: '/messages', color: 'bg-orange-500' }
  ];

  // Load real-time data for logged-in users
  useEffect(() => {
    if (isLoggedIn && user) {
      loadDashboardData();

      // Set up periodic refresh for dashboard data (fallback for WebSocket)
      const dashboardInterval = setInterval(() => {
        loadDashboardData();
      }, 60000); // Refresh every minute

      return () => {
        clearInterval(dashboardInterval);
      };
    }
  }, [isLoggedIn, user]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Load dashboard stats
      const statsResponse = await apiService.getDashboardStats();
      setTodayStats(statsResponse.data);

      // Load recent posts/activity feed
      const postsResponse = await apiService.getActivityFeed();
      setRecentPosts(postsResponse.data.results || []);

      // Load job recommendations for job seekers
      if (user?.user_type === 'job_seeker') {
        const jobsResponse = await apiService.getJobRecommendations();
        setJobRecommendations(jobsResponse.data.results || []);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    return `${Math.floor(diffInSeconds / 86400)}d ago`;
  };

  if (isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Welcome Header */}
        <section className="bg-gradient-to-r from-indigo-600 to-violet-600 text-white py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
              <div>
                <h1 className="text-2xl md:text-3xl font-bold mb-2">
                  Welcome back, {user?.first_name}! 👋
                </h1>
                <p className="text-indigo-100 text-lg">
                  {user?.user_type === 'job_seeker'
                    ? 'Ready to find your next opportunity?'
                    : 'Ready to find great talent today?'
                  }
                </p>
              </div>
              <div className="mt-4 md:mt-0 flex space-x-3">
                <Link to="/ai-interview">
                  <Button variant='secondary' size='lg'>
                    <Bot className="w-4 h-4 mr-2" />
                    Practice Interview
                  </Button>
                </Link>
                <Button variant="outline" className="border-white text-white hover:bg-white hover:text-indigo-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Post
                </Button>
              </div>
            </div>
          </div>
        </section>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Left Sidebar - Quick Actions & Stats */}
            <div className="lg:col-span-1 space-y-6">
              {/* Today's Stats */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <Calendar className="w-5 h-5 mr-2 text-indigo-600" />
                    Today's Activity
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Profile Views</span>
                      <span className="font-semibold text-gray-900 dark:text-white">{todayStats.profileViews}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">New Connections</span>
                      <span className="font-semibold text-gray-900 dark:text-white">{todayStats.newConnections}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Job Matches</span>
                      <span className="font-semibold text-gray-900 dark:text-white">{todayStats.jobMatches}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Interview Score</span>
                      <span className="font-semibold text-emerald-600">{todayStats.interviewScore}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardContent className="p-6">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                    <Target className="w-5 h-5 mr-2 text-indigo-600" />
                    Quick Actions
                  </h3>
                  <div className="space-y-3">
                    {quickActions.map((action, index) => (
                      <Link
                        key={index}
                        to={action.href}
                        className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      >
                        <div className={`w-8 h-8 ${action.color} rounded-lg flex items-center justify-center`}>
                          <action.icon className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {action.label}
                        </span>
                      </Link>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Main Content - Posts Feed */}
            <div className="lg:col-span-3">
              <div className="space-y-6">
                {/* Create Post Card */}
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center space-x-4">
                      <img
                        src={user?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent(user?.first_name + ' ' + user?.last_name)}&background=6366f1&color=fff`}
                        alt="Your avatar"
                        className="w-12 h-12 rounded-full"
                      />
                      <button className="flex-1 text-left px-4 py-3 bg-gray-50 dark:bg-gray-700 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                        Share your professional insights, {user?.first_name}...
                      </button>
                      <Button>
                        <Plus className="w-4 h-4 mr-2" />
                        Post
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Loading State */}
                {isLoading && (
                  <Card>
                    <CardContent className="p-6 text-center">
                      <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-indigo-600" />
                      <p className="text-gray-600 dark:text-gray-400">Loading your feed...</p>
                    </CardContent>
                  </Card>
                )}

                {/* Recent Posts */}
                {!isLoading && recentPosts.length > 0 && recentPosts.map((post) => (
                  <Card key={post.id}>
                    <CardContent className="p-6">
                      {/* Post Header */}
                      <div className="flex items-start space-x-3 mb-4">
                        <img
                          src={post.author?.profile_picture || `https://ui-avatars.io/api/?name=${encodeURIComponent(post.author?.name || 'User')}&background=6366f1&color=fff`}
                          alt={post.author?.name || 'User'}
                          className="w-12 h-12 rounded-full"
                        />
                        <div className="flex-1">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-semibold text-gray-900 dark:text-white">
                              {post.author?.name || 'Anonymous User'}
                            </h4>
                            {post.author?.is_verified && (
                              <CheckCircle className="w-4 h-4 text-blue-500" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {post.author?.title || 'Professional'}
                          </p>
                          <div className="flex items-center space-x-1 mt-1">
                            <Clock className="w-3 h-3 text-gray-400" />
                            <span className="text-xs text-gray-400">{formatTimeAgo(post.created_at)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Post Content */}
                      <p className="text-gray-900 dark:text-white mb-4 leading-relaxed">
                        {post.content}
                      </p>

                      {/* Post Image */}
                      {post.image && (
                        <img
                          src={post.image}
                          alt="Post content"
                          className="w-full h-64 object-cover rounded-lg mb-4"
                        />
                      )}

                      {/* Post Actions */}
                      <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                        <div className="flex items-center space-x-6">
                          <button className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                            <ThumbsUp className="w-4 h-4" />
                            <span className="text-sm">{post.likes_count || 0}</span>
                          </button>
                          <button className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-green-600 dark:hover:text-green-400 transition-colors">
                            <MessageSquare className="w-4 h-4" />
                            <span className="text-sm">{post.comments_count || 0}</span>
                          </button>
                          <button className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors">
                            <Share2 className="w-4 h-4" />
                            <span className="text-sm">{post.shares_count || 0}</span>
                          </button>
                        </div>
                        <button className="text-gray-600 dark:text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400 transition-colors">
                          <BookmarkPlus className="w-4 h-4" />
                        </button>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {/* Empty State */}
                {!isLoading && recentPosts.length === 0 && (
                  <Card>
                    <CardContent className="p-8 text-center">
                      <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        No posts yet
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400 mb-4">
                        Start following professionals or create your first post to see content here.
                      </p>
                      <Button>
                        <Plus className="w-4 h-4 mr-2" />
                        Create Your First Post
                      </Button>
                    </CardContent>
                  </Card>
                )}

                {/* Load More */}
                <div className="text-center">
                  <Button variant="outline" className="px-8">
                    Load More Posts
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Original marketing page for logged-out users
  const features = [
    {
      icon: Bot,
      title: 'AI Interview Assistant',
      description: 'Practice with our advanced AI that provides real-time feedback and confidence scoring.'
    },
    {
      icon: Users,
      title: 'Professional Network',
      description: 'Connect with industry professionals and expand your career opportunities.'
    },
    {
      icon: Briefcase,
      title: 'Smart Job Matching',
      description: 'Get AI-powered job recommendations based on your skills and preferences.'
    },
    {
      icon: TrendingUp,
      title: 'Career Growth',
      description: 'Track your progress and receive personalized career development insights.'
    }
  ];

  const testimonials = [
    {
      name: 'Sarah Johnson',
      role: 'Software Engineer',
      avatar: 'https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
      content: 'HireWise helped me land my dream job! The AI interview practice was incredibly realistic.'
    },
    {
      name: 'Michael Chen',
      role: 'Product Manager',
      avatar: 'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=100&h=100&fit=crop',
      content: 'The networking features and job matching are outstanding. Highly recommend!'
    }
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-indigo-600 via-violet-600 to-indigo-800 text-white py-12 sm:py-16 lg:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold mb-4 sm:mb-6">
              Your AI-Powered
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-400 mt-2">
                Career Companion
              </span>
            </h1>
            <p className="text-lg sm:text-xl md:text-2xl mb-6 sm:mb-8 text-indigo-100 max-w-3xl mx-auto px-4">
              HireWise combines professional networking with advanced AI interview preparation
              to accelerate your career growth and land your dream job.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4">
              <Link to="/signup">
                <Button variant="secondary" size="lg">
                  Get Started Free
                </Button>
              </Link>
              <Link to="/ai-interview">
                <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-indigo-600 px-6 sm:px-8 py-2 sm:py-3 text-base sm:text-lg w-full sm:w-auto">
                  Try AI Interview
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 sm:py-16 lg:py-20 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Powerful Features for Your Success
            </h2>
            <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto px-4">
              Everything you need to advance your career, powered by cutting-edge AI technology
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            {features.map((feature, index) => (
              <Card key={index} hover className="text-center">
                <CardContent className="p-4 sm:p-6">
                  <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-violet-600 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* AI Assistant Showcase */}
      <section className="py-12 sm:py-16 lg:py-20 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
            <div>
              <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4 sm:mb-6">
                Meet Your AI Interview Coach
              </h2>
              <p className="text-base sm:text-lg text-gray-600 dark:text-gray-300 mb-6 sm:mb-8">
                Our advanced AI assistant provides personalized interview practice with real-time
                feedback, confidence scoring, and detailed performance analytics.
              </p>
              <div className="space-y-3 sm:space-y-4 mb-6 sm:mb-8">
                {[
                  'Real-time confidence tracking',
                  'Personalized question generation',
                  'Detailed performance analytics',
                  'Industry-specific scenarios'
                ].map((benefit, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                    <span className="text-sm sm:text-base text-gray-700 dark:text-gray-300">{benefit}</span>
                  </div>
                ))}
              </div>
              <Link to="/ai-interview">
                <Button variant="secondary" size="lg">
                  Start AI Interview
                </Button>
              </Link>
            </div>
            <div className="bg-white dark:bg-gray-800 p-6 sm:p-8 rounded-2xl shadow-xl mt-8 lg:mt-0">
              <div className="flex items-center space-x-3 mb-6">
                <Bot className="w-8 h-8 text-violet-600" />
                <span className="font-semibold text-gray-900 dark:text-white">AI Assistant</span>
              </div>
              <div className="space-y-4">
                <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg">
                  <p className="text-sm sm:text-base text-indigo-800 dark:text-indigo-200">
                    "Tell me about a challenging project you worked on recently."
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-emerald-500 h-2 rounded-full w-4/5"></div>
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-emerald-600">85% Confidence</span>
                </div>
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                  Great structure! Try to include more specific metrics in your example.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-12 sm:py-16 lg:py-20 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 sm:mb-16">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Success Stories
            </h2>
            <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300 px-4">
              See how HireWise helped professionals achieve their career goals
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="p-6 sm:p-8">
                <div className="flex items-center space-x-4 mb-6">
                  <img
                    src={testimonial.avatar}
                    alt={testimonial.name}
                    className="w-12 h-12 rounded-full"
                  />
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">
                      {testimonial.name}
                    </h4>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                      {testimonial.role}
                    </p>
                  </div>
                  <div className="ml-auto flex space-x-1">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                </div>
                <p className="text-sm sm:text-base text-gray-700 dark:text-gray-300 italic">
                  "{testimonial.content}"
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-12 sm:py-16 lg:py-20 bg-gradient-to-r from-indigo-600 to-violet-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-4 sm:mb-6">
            Ready to Transform Your Career?
          </h2>
          <p className="text-lg sm:text-xl mb-6 sm:mb-8 text-indigo-100 max-w-2xl mx-auto px-4">
            Join thousands of professionals who are advancing their careers with HireWise
          </p>
          <Link to="/signup">
            <Button variant="secondary" size="lg">
              Start Your Journey Today
            </Button>
          </Link>
        </div>
      </section>
      <Footer />
    </div>
  );
};
