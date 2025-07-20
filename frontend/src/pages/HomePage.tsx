import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { Bot, Users, Briefcase, TrendingUp, Star, CheckCircle } from 'lucide-react';

export const HomePage: React.FC = () => {
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
    <div className="min-h-screen">
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
              <Link to="/dashboard">
                <Button size="lg" className="bg-white text-indigo-600 hover:bg-gray-100 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg w-full sm:w-auto">
                  Get Started Free
                </Button>
              </Link>
              <Link to="/ai-interview">
                <Button variant="outline" size="lg" className="border-white text-white hover:bg-white hover:text-indigo-600 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg w-full sm:w-auto">
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
          <Link to="/dashboard">
            <Button size="lg" className="bg-white text-indigo-600 hover:bg-gray-100 px-6 sm:px-8 py-3 sm:py-4 text-base sm:text-lg">
              Start Your Journey Today
            </Button>
          </Link>
        </div>
      </section>
    </div>
  );
};