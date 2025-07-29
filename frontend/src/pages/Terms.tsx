import React from 'react';
import Footer from '../components/layout/Footer';

const Terms: React.FC = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 flex flex-col items-center justify-center">
    <div className="max-w-3xl w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
      <h1 className="text-4xl font-bold text-indigo-700 dark:text-indigo-400 mb-6 text-center">Terms of Service</h1>
      <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 text-center">
        By using HireWise, you agree to the following terms and conditions. Please read them carefully.
      </p>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">User Responsibilities</h2>
      <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
        <li>Use the platform responsibly and respectfully</li>
        <li>Do not share your account credentials with others</li>
        <li>All content you post must comply with our community guidelines</li>
        <li>Do not engage in fraudulent or illegal activities</li>
      </ul>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Platform Rights</h2>
      <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
        <li>We reserve the right to suspend or terminate accounts for violations</li>
        <li>We may update these terms at any time</li>
        <li>We are not liable for user-generated content</li>
      </ul>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Intellectual Property</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        All content and trademarks on HireWise are the property of their respective owners. You may not use, copy, or distribute content without permission.
      </p>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Contact & Updates</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        For questions or concerns, contact us at <a href="mailto:support@hirewise.com" className="text-indigo-600 hover:underline">support@hirewise.com</a>.
      </p>
      <div className="text-center text-xs text-gray-400 dark:text-gray-500 mt-8">
        These terms may be updated at any time. Continued use of HireWise constitutes acceptance of any changes.<br/>
        &copy; {new Date().getFullYear()} HireWise. All rights reserved.
      </div>
    </div>
    <div className="w-full mt-8">
      <Footer />
    </div>
  </div>
);

export default Terms;
