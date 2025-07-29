import React from 'react';
import { NavLink } from 'react-router-dom';
import logo from '/logo.png'; 

const year = new Date().getFullYear();

export const Footer: React.FC = () => (
  <footer className="w-full bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col items-center gap-4 md:flex-row md:items-center md:justify-between">
      <div className="flex flex-col items-center md:flex-row md:items-center md:space-x-2">
        <div className="flex bg-gradient-to-t from-indigo-500 to-violet-500 items-center justify-center shadow-lg rounded-lg mb-2 md:mb-0">
          <img src={logo} alt="HireWise Logo" className="w-12 h-12" />
        </div>
        <span className="font-bold text-gray-900 dark:text-white text-lg">HireWise</span>
      </div>
      <nav className="flex flex-wrap justify-center gap-4 text-sm text-gray-600 dark:text-gray-400 w-full md:w-auto">
        <NavLink to="/about" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>About</NavLink>
        <NavLink to="/jobs" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>Jobs</NavLink>
        <NavLink to="/ai-interview" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>AI Interview</NavLink>
        <NavLink to="/privacy" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>Privacy</NavLink>
        <NavLink to="/terms" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>Terms</NavLink>
        <NavLink to="/contact" className={({ isActive }) => isActive ? "text-indigo-600 font-semibold underline" : "hover:text-indigo-600"}>Contact</NavLink>
      </nav>
      <div className="text-xs text-gray-400 text-center w-full md:w-auto">&copy; {year} HireWise. All rights reserved.</div>
    </div>
  </footer>
);

export default Footer;
