/**
 * Dashboard Page - REFACTORED with error handler utility
 *
 * Improvements:
 * 1. Using constants from constants/tickets.ts
 * 2. Using types from api/client.ts
 * 3. Centralized error handling with errorHandler utility
 */
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { tenantsApi, ticketsApi, TenantStats, Ticket } from '../api/client';
import { STATUS_COLORS, PRIORITY_COLORS } from '../constants/tickets';
import { Spinner, Alert, Card } from '../components/common';
import { formatErrorForUser } from '../utils/errorHandler';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<TenantStats | null>(null);
  const [recentTickets, setRecentTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [statsData, ticketsData] = await Promise.all([
          tenantsApi.getStats(),
          ticketsApi.list({ limit: 5 }),
        ]);

        setStats(statsData);
        setRecentTickets(ticketsData);
      } catch (err) {
        // Use formatErrorForUser for consistent, user-friendly error messages
        const errorMessage = formatErrorForUser(err, 'loading dashboard data');
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Alert type="error" message={error} onClose={() => setError(null)} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Link
          to="/tickets/new"
          className="bg-blue-600 text-white rounded-lg p-4 hover:bg-blue-700 transition-colors text-center"
        >
          <span className="text-2xl">🎫</span>
          <p className="mt-2 font-medium">New Ticket</p>
        </Link>
        <Link
          to="/playground"
          className="bg-green-600 text-white rounded-lg p-4 hover:bg-green-700 transition-colors text-center"
        >
          <span className="text-2xl">🤖</span>
          <p className="mt-2 font-medium">AI Playground</p>
        </Link>
        <Link
          to="/kb"
          className="bg-purple-600 text-white rounded-lg p-4 hover:bg-purple-700 transition-colors text-center"
        >
          <span className="text-2xl">📚</span>
          <p className="mt-2 font-medium">Knowledge Base</p>
        </Link>
        <Link
          to="/tickets"
          className="bg-gray-600 text-white rounded-lg p-4 hover:bg-gray-700 transition-colors text-center"
        >
          <span className="text-2xl">📋</span>
          <p className="mt-2 font-medium">All Tickets</p>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase">Total Tickets</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {stats?.tickets_by_status ? Object.values(stats.tickets_by_status).reduce((a, b) => a + b, 0) : 0}
          </p>
        </Card>

        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase">Active Users</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {stats?.total_users ?? 0}
          </p>
        </Card>

        <Card>
          <h3 className="text-sm font-medium text-gray-500 uppercase">KB Chunks</h3>
          <p className="mt-2 text-3xl font-bold text-gray-900">
            {stats?.total_kb_chunks ?? 0}
          </p>
        </Card>
      </div>

      {/* Tickets by Status */}
      {stats?.tickets_by_status && Object.keys(stats.tickets_by_status).length > 0 && (
        <Card className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Tickets by Status</h3>
          <div className="flex flex-wrap gap-3">
            {Object.entries(stats.tickets_by_status).map(([status, count]) => (
              <Link
                key={status}
                to={`/tickets?status=${status}`}
                className={`px-4 py-2 rounded-full text-sm font-medium ${STATUS_COLORS[status] || 'bg-gray-100 text-gray-800'}`}
              >
                {status.replace('_', ' ')}: {count}
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Tickets */}
      <Card padding="none">
        <div className="px-6 py-4 border-b">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Recent Tickets</h3>
            <Link to="/tickets" className="text-blue-600 hover:text-blue-800 text-sm">
              View all →
            </Link>
          </div>
        </div>
        
        {recentTickets.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No tickets yet.{' '}
            <Link to="/tickets/new" className="text-blue-600 hover:underline">
              Create one!
            </Link>
          </div>
        ) : (
          <div className="divide-y">
            {recentTickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/tickets/${ticket.id}`}
                className="block px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {ticket.title}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      #{ticket.id} • {new Date(ticket.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-2 ml-4">
                    <span className={`text-xs font-medium ${PRIORITY_COLORS[ticket.priority] || ''}`}>
                      {ticket.priority}
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs ${STATUS_COLORS[ticket.status] || 'bg-gray-100 text-gray-800'}`}>
                      {ticket.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

export default Dashboard;
