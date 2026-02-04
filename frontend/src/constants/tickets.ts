/**
 * Ticket Constants - Single Source of Truth
 * 
 * Eliminates duplication across Tickets.tsx, TicketDetail.tsx, Dashboard.tsx
 */

// ===== Status Options =====

export const STATUS_OPTIONS = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'pending_customer', label: 'Pending Customer' },
  { value: 'pending_agent', label: 'Pending Agent' },
  { value: 'escalated', label: 'Escalated' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
] as const;

export const STATUS_OPTIONS_WITH_ALL = [
  { value: '', label: 'All Statuses' },
  ...STATUS_OPTIONS,
] as const;

// ===== Priority Options =====

export const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
] as const;

// ===== Status Colors =====

export const STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  pending_customer: 'bg-orange-100 text-orange-800',
  pending_agent: 'bg-purple-100 text-purple-800',
  escalated: 'bg-red-100 text-red-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
  reopened: 'bg-indigo-100 text-indigo-800',
};

// ===== Priority Colors =====

export const PRIORITY_COLORS: Record<string, string> = {
  low: 'text-gray-600',
  medium: 'text-blue-600',
  high: 'text-orange-600',
  urgent: 'text-red-600',
};

// ===== Priority Badge Colors =====

export const PRIORITY_BADGE_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

// ===== Message Role Config =====

export const MESSAGE_ROLE_CONFIG: Record<string, { label: string; bg: string; align: string }> = {
  user: {
    label: '👤 User',
    bg: 'bg-blue-50 border-blue-200',
    align: 'ml-auto',
  },
  assistant: {
    label: '🤖 AI Assistant',
    bg: 'bg-green-50 border-green-200',
    align: 'mr-auto',
  },
  system: {
    label: '⚙️ System',
    bg: 'bg-gray-50 border-gray-200',
    align: 'mx-auto',
  },
};

// ===== Type exports =====

export type TicketStatus = typeof STATUS_OPTIONS[number]['value'];
export type TicketPriority = typeof PRIORITY_OPTIONS[number]['value'];
export type MessageRole = 'user' | 'assistant' | 'system';
