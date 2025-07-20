import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { mockPosts, mockJobs, mockUser } from '../data/mockData';
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
  Send
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
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
                      src={mockUser.avatar}
                      alt={mockUser.name}
                      className="w-20 h-20 rounded-full border-4 border-white dark:border-gray-800 shadow-lg"
                    />
                  </div>
                  <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white">{mockUser.name}</h3>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-3">{mockUser.title}</p>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Profile views</span>
                      <span className="text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400">142</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">Connections</span>
                      <span className="text-xs sm:text-sm font-medium text-indigo-600 dark:text-indigo-400">{mockUser.connections}</span>
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
                    src={mockUser.avatar}
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

            {/* Posts Feed */}
            {mockPosts.map((post) => (
              <Card key={post.id} hover>
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <img
                      src={post.avatar}
                      alt={post.author}
                      className="w-10 sm:w-12 h-10 sm:h-12 rounded-full"
                    />
                    <div className="flex-1">
                      <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-white">{post.author}</h3>
                      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{post.title}</p>
                      <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-500">{post.timeAgo}</p>
                    </div>
                    <button className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                      </svg>
                    </button>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm sm:text-base text-gray-800 dark:text-gray-200 mb-4 leading-relaxed">{post.content}</p>
                  <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center space-x-4 sm:space-x-6">
                      <button className="flex items-center space-x-2 text-gray-500 hover:text-red-500 transition-colors">
                        <Heart className="w-5 h-5" />
                        <span className="text-xs sm:text-sm font-medium">{post.likes}</span>
                      </button>
                      <button className="flex items-center space-x-2 text-gray-500 hover:text-blue-500 transition-colors">
                        <MessageCircle className="w-5 h-5" />
                        <span className="text-xs sm:text-sm font-medium">{post.comments}</span>
                      </button>
                      <button className="flex items-center space-x-2 text-gray-500 hover:text-green-500 transition-colors">
                        <Share2 className="w-5 h-5" />
                        <span className="text-xs sm:text-sm font-medium hidden sm:inline">Share</span>
                      </button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
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
                  {mockJobs.slice(0, 3).map((job) => (
                    <div key={job.id} className="group cursor-pointer">
                      <div className="flex items-start space-x-3 p-2 sm:p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        <img
                          src={job.logo}
                          alt={job.company}
                          className="w-8 sm:w-10 h-8 sm:h-10 rounded-lg"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-gray-900 dark:text-white text-xs sm:text-sm group-hover:text-indigo-600 dark:group-hover:text-indigo-400">
                            {job.title}
                          </h4>
                          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">{job.company}</p>
                          <div className="flex items-center space-x-2 mt-1">
                            <Star className="w-3 h-3 text-emerald-500" />
                            <span className="text-xs text-emerald-600 font-medium">
                              {job.aiMatch}% match
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
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
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        <span className="font-medium">Sarah Chen</span> got promoted to Senior PM
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">2 hours ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-indigo-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        <span className="font-medium">Mike Rodriguez</span> started at Google
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">1 day ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-violet-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300">
                        <span className="font-medium">3 connections</span> viewed your profile
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">2 days ago</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};