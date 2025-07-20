import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Card } from '../ui/Card';
import { mockUser } from '../../data/mockData';
import { User, Users, Briefcase, Bookmark, Settings } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const location = useLocation();

  const sidebarItems = [
    { name: 'My Profile', href: '/profile', icon: User },
    { name: 'My Network', href: '/network', icon: Users },
    { name: 'Saved Jobs', href: '/saved-jobs', icon: Bookmark },
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="w-64 space-y-6">
      {/* Profile Card */}
      <Card>
        <div className="p-6 text-center">
          <img
            src={mockUser.avatar}
            alt={mockUser.name}
            className="w-16 h-16 rounded-full mx-auto mb-4"
          />
          <h3 className="font-semibold text-gray-900 dark:text-white">{mockUser.name}</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{mockUser.title}</p>
          <div className="text-sm text-gray-500 dark:text-gray-400">
            <p>{mockUser.connections} connections</p>
          </div>
        </div>
      </Card>

      {/* Navigation */}
      <Card>
        <div className="p-4">
          <nav className="space-y-2">
            {sidebarItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20'
                      : 'text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </Card>

      {/* Quick Stats */}
      <Card>
        <div className="p-4">
          <h4 className="font-medium text-gray-900 dark:text-white mb-3">Quick Stats</h4>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Profile Views</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">142</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">Job Applications</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">8</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">AI Interviews</span>
              <span className="text-sm font-medium text-gray-900 dark:text-white">3</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};