import React from 'react';
import Footer from '../components/layout/Footer';

const Privacy: React.FC = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 flex flex-col items-center justify-center">
    <div className="max-w-3xl w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
      <h1 className="text-4xl font-bold text-indigo-700 dark:text-indigo-400 mb-6 text-center">Privacy Policy</h1>
      <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 text-center">
        Your privacy is important to us. This Privacy Policy explains how HireWise collects, uses, and protects your personal information.
      </p>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Information We Collect</h2>
      <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
        <li>Account information (name, email, etc.)</li>
        <li>Profile details and job preferences</li>
        <li>Usage data and analytics</li>
        <li>Communications and support requests</li>
      </ul>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">How We Use Your Information</h2>
      <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
        <li>To provide and improve our services</li>
        <li>To personalize your experience</li>
        <li>To communicate important updates</li>
        <li>To ensure security and prevent fraud</li>
      </ul>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Your Rights & Choices</h2>
      <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
        <li>Access, update, or delete your data at any time</li>
        <li>Opt out of marketing communications</li>
        <li>Request data export or account deletion</li>
      </ul>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Data Security</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        We use industry-standard security measures to protect your data. Your information is encrypted and stored securely. We never sell your data to third parties.
      </p>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Cookies & Analytics</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        We use cookies and analytics tools to enhance your experience and improve our services. You can manage your cookie preferences in your browser settings.
      </p>
      <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Contact Us</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-4">
        For questions or concerns about your privacy, contact us at <a href="mailto:support@hirewise.com" className="text-indigo-600 hover:underline">support@hirewise.com</a>.
      </p>
      <div className="text-center text-xs text-gray-400 dark:text-gray-500 mt-8">
        This policy may be updated from time to time. Please review it regularly for changes.<br/>
        &copy; {new Date().getFullYear()} HireWise. All rights reserved.
      </div>
    </div>
    <div className="w-full mt-8">
      <Footer />
    </div>
  </div>
);

export default Privacy;
