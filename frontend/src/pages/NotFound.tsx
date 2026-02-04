/**
 * NotFound Page - FIXED VERSION
 * 
 * Fixes:
 * 1. Using relative imports
 * 2. Improved design
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/common';

const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center px-4">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="text-2xl font-bold text-gray-900 mt-4">Page Not Found</h2>
        <p className="text-gray-500 mt-2 max-w-md mx-auto">
          Sorry, we couldn't find the page you're looking for.
          Perhaps you've mistyped the URL or the page has been moved.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/dashboard">
            <Button>Go to Dashboard</Button>
          </Link>
          <Link to="/tickets">
            <Button variant="secondary">View Tickets</Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
