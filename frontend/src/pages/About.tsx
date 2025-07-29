
import React from 'react';
import Footer from '../components/layout/Footer';

const About: React.FC = () => (
  <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4 flex flex-col items-center justify-center">
    <div className="max-w-3xl w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
      <h1 className="text-4xl font-bold text-indigo-700 dark:text-indigo-400 mb-6 text-center">About HireWise</h1>
      <p className="text-lg text-gray-700 dark:text-gray-300 mb-6 text-center">
        HireWise is your AI-powered career companion, designed to help you land your dream job and grow your professional network. Our platform combines advanced AI interview practice, smart job matching, and a vibrant professional community to accelerate your career journey.
      </p>

      <div className="mb-10">
        <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Our Story</h2>
        <p className="text-gray-700 dark:text-gray-300 mb-4">
          Founded in 2025, HireWise was born out of a desire to bridge the gap between talent and opportunity. Our founders, a group of engineers and career coaches, saw the need for a smarter, more supportive job search experience. Today, HireWise serves thousands of users worldwide, helping them navigate the ever-changing job market with confidence.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
        <div>
          <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Our Mission</h2>
          <p className="text-gray-700 dark:text-gray-300 mb-4">
            We believe everyone deserves the opportunity to succeed. Our mission is to empower job seekers and recruiters with cutting-edge AI tools, actionable insights, and a supportive community.
          </p>
          <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
            <li>AI-driven interview practice with real-time feedback</li>
            <li>Personalized job recommendations</li>
            <li>Professional networking and messaging</li>
            <li>Career growth analytics and insights</li>
            <li>Resume and portfolio builder</li>
            <li>Mock interviews with instant scoring</li>
          </ul>
        </div>
        <div>
          <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Why Choose HireWise?</h2>
          <ul className="list-disc pl-6 text-gray-700 dark:text-gray-300 mb-4">
            <li>Trusted by thousands of professionals worldwide</li>
            <li>Cutting-edge AI technology for interview prep</li>
            <li>Secure and privacy-focused platform</li>
            <li>Continuous updates and new features</li>
            <li>Dedicated support team</li>
            <li>Community-driven events and webinars</li>
          </ul>
        </div>
      </div>

      <div className="mb-10">
        <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">How HireWise Works</h2>
        <ol className="list-decimal pl-6 text-gray-700 dark:text-gray-300 mb-4">
          <li>Sign up and create your professional profile</li>
          <li>Access AI-powered interview practice tailored to your field</li>
          <li>Receive personalized job recommendations</li>
          <li>Connect with recruiters and other professionals</li>
          <li>Track your progress and get actionable feedback</li>
        </ol>
      </div>

      <div className="mb-10">
        <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Success Stories</h2>
        <div className="bg-indigo-50 dark:bg-indigo-900 rounded-lg p-4 mb-4">
          <p className="italic text-gray-800 dark:text-gray-200">“HireWise helped me ace my interviews and land my dream job at a top tech company. The AI feedback was spot on!”</p>
          <div className="text-right text-sm text-indigo-700 dark:text-indigo-300">— Priya S., Software Engineer</div>
        </div>
        <div className="bg-indigo-50 dark:bg-indigo-900 rounded-lg p-4">
          <p className="italic text-gray-800 dark:text-gray-200">“The job matching and networking features made my job search so much easier. Highly recommend!”</p>
          <div className="text-right text-sm text-indigo-700 dark:text-indigo-300">— Alex M., Marketing Specialist</div>
        </div>
      </div>

      <div className="mb-10">
        <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Meet the Team</h2>
        <p className="text-gray-700 dark:text-gray-300 mb-4">
          Our diverse team of engineers, designers, and career experts is passionate about helping you succeed. We are committed to building a platform that is inclusive, innovative, and user-focused.
        </p>
      </div>

      <div className="mb-10">
        <h2 className="text-2xl font-semibold text-indigo-600 dark:text-indigo-300 mb-2">Contact Us</h2>
        <p className="text-gray-700 dark:text-gray-300 mb-2">
          Have questions, feedback, or partnership ideas? We'd love to hear from you!
        </p>
        <a href="mailto:support@hirewise.com" className="text-indigo-600 hover:underline">support@hirewise.com</a>
      </div>

      <div className="text-center text-xs text-gray-400 dark:text-gray-500 mt-8">
        &copy; {new Date().getFullYear()} HireWise. All rights reserved.
      </div>
    </div>
    <div className="w-full mt-8">
      <Footer />
    </div>
  </div>
);

export default About;
