import React, { useState } from 'react';
import ChangePassword from '../components/settings/ChangePassword';
import { useTheme } from '../contexts/useTheme';
import { useAuth } from '../contexts/AuthContext';

const SettingsPage: React.FC = () => {
  // In-app settings state
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const [emailNotifications, setEmailNotifications] = useState(true);

  return (
    <div className="max-w-2xl mx-auto py-10 px-4">
      <h1 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Settings</h1>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 space-y-6 border border-gray-200 dark:border-gray-700">
        <section>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Account</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-700 dark:text-gray-300">Email</span>
              <div className="flex flex-col items-end">
                <span className="font-medium text-gray-900 dark:text-white">{user?.email || '...'}</span>
                <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">You cannot change this for 3 months after account creation.</span>
              </div>
            </div>
            <div className="mt-4">
              <ChangePassword />
            </div>
          </div>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Preferences</h2>
          <div className="flex items-center justify-between">
            <span className="text-gray-700 dark:text-gray-300">Dark Mode</span>
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={theme === 'dark'}
              onChange={toggleTheme}
            />
          </div>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-200 mb-2">Notifications</h2>
          <div className="flex items-center justify-between">
            <span className="text-gray-700 dark:text-gray-300">Email Notifications</span>
            <input
              type="checkbox"
              className="toggle toggle-primary"
              checked={emailNotifications}
              onChange={() => setEmailNotifications((v) => !v)}
            />
          </div>
        </section>
        <section>
          <h2 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-2">Danger Zone</h2>
          <button className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg">Delete Account</button>
        </section>
      </div>
    </div>
  );
};

export default SettingsPage;
