import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { formatErrorForUser } from '../utils/errorHandler';

interface Ticket {
  id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  source: string;
  created_at: string;
  updated_at: string;
}

interface Message {
  id: number;
  ticket_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  created_at: string;
}

interface AgentResponse {
  content: string;
  needs_escalation: boolean;
  escalation_reason: string | null;
  context_used: { id: number; source: string; score: number }[];
  model: string;
}

const STATUS_OPTIONS = [
  { value: 'open', label: 'Open' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'pending_customer', label: 'Pending Customer' },
  { value: 'pending_agent', label: 'Pending Agent' },
  { value: 'escalated', label: 'Escalated' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' },
];

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

const TicketDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [newMessage, setNewMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [lastAgentInfo, setLastAgentInfo] = useState<AgentResponse | null>(null);
  
  // ADDED: Timer for showing elapsed time
  const [elapsedTime, setElapsedTime] = useState(0);

  // ADDED: Timer effect for showing progress
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (generating) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [generating]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchTicket = useCallback(async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const [ticketRes, messagesRes] = await Promise.all([
        api.get<Ticket>(`/v1/tickets/${id}`),
        api.get<Message[]>(`/v1/tickets/${id}/messages`),
      ]);
      
      setTicket(ticketRes.data);
      setMessages(messagesRes.data);
    } catch (err: any) {
      setError(formatErrorForUser(err, 'loading ticket'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || sending || !id) return;
    
    try {
      setSending(true);
      setError(null);
      
      // Send user message (auto_respond=false to manually control AI)
      await api.post(`/v1/tickets/${id}/messages`, {
        content: newMessage.trim(),
        role: 'user',
        auto_respond: false, // Changed to false for better control
      });
      
      setNewMessage('');
      
      // Refresh messages
      const messagesRes = await api.get<Message[]>(`/v1/tickets/${id}/messages`);
      setMessages(messagesRes.data);


    } catch (err: any) {
      setError(formatErrorForUser(err, 'sending message'));
    } finally {
      setSending(false);
    }
  };

  const handleGenerateResponse = async () => {
    if (!id || generating) return;
    
    try {
      setGenerating(true);
      setError(null);
      
      // FIXED: Extended timeout for LLM requests (3 minutes)
      const response = await api.post<AgentResponse>(`/v1/agent/respond/${id}`, {
        save_response: true,
        max_context: 5,
      }, {
        timeout: 180000, // 3 minutes
      });
      
      setLastAgentInfo(response.data);
      
      // Refresh messages
      const messagesRes = await api.get<Message[]>(`/v1/tickets/${id}/messages`);
      setMessages(messagesRes.data);


    } catch (err: any) {
      setError(formatErrorForUser(err, 'generating AI response'));
    } finally {
      setGenerating(false);
    }
  };

  const handleStatusChange = async (newStatus: string) => {
    if (!id || !ticket) return;
    
    try {
      await api.patch(`/v1/tickets/${id}`, { status: newStatus });
      setTicket({ ...ticket, status: newStatus });
    } catch (err: any) {
      setError(formatErrorForUser(err, 'updating ticket status'));
    }
  };

  // Format elapsed time
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const roleConfig: Record<string, { bg: string; align: string; label: string }> = {
    user: { bg: 'bg-blue-50 border-blue-200', align: 'ml-auto', label: 'Customer' },
    assistant: { bg: 'bg-green-50 border-green-200', align: 'mr-auto', label: 'AI Agent' },
    system: { bg: 'bg-gray-50 border-gray-200', align: 'mx-auto', label: 'System' },
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Ticket not found</p>
        <button
          onClick={() => navigate('/tickets')}
          className="mt-4 text-blue-600 hover:underline"
        >
          ← Back to Tickets
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/tickets')}
              className="text-gray-500 hover:text-gray-700"
            >
              ←
            </button>
            <div>
              <h1 className="text-lg font-semibold text-gray-900">
                #{ticket.id}: {ticket.title}
              </h1>
              <div className="flex items-center gap-2 mt-1">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${PRIORITY_COLORS[ticket.priority] || 'bg-gray-100'}`}>
                  {ticket.priority}
                </span>
                <span className="text-xs text-gray-500">
                  Created: {new Date(ticket.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <select
              value={ticket.status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {ticket.description && (
          <p className="mt-3 text-sm text-gray-600 bg-gray-50 p-3 rounded">
            {ticket.description}
          </p>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 py-8">
            No messages yet. Start the conversation!
          </div>
        )}
        
        {messages.map((message) => {
          const config = roleConfig[message.role] || roleConfig.system;
          return (
            <div
              key={message.id}
              className={`max-w-2xl ${config.align}`}
            >
              <div className={`rounded-lg border p-4 ${config.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-600">
                    {config.label}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(message.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="text-sm text-gray-800 whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            </div>
          );
        })}
        
        {/* IMPROVED: Better loading indicator with timer */}
        {generating && (
          <div className="max-w-2xl mr-auto">
            <div className="rounded-lg border p-4 bg-green-50 border-green-200">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600"></div>
                AI is generating response... ({formatTime(elapsedTime)})
              </div>
              {/* Progress indicator */}
              <div className="mt-2 h-1 bg-green-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all duration-1000 ease-linear"
                  style={{ width: `${Math.min((elapsedTime / 60) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {elapsedTime < 10 
                  ? 'Searching knowledge base...'
                  : elapsedTime < 30
                    ? 'Generating AI response...'
                    : 'Still working, please wait...'}
              </p>
            </div>
          </div>
        )}
        
        {sending && (
          <div className="max-w-2xl ml-auto">
            <div className="rounded-lg border p-4 bg-blue-50 border-blue-200">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                Sending message...
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Agent Info Panel (collapsed by default) */}
      {lastAgentInfo && (
        <div className="bg-blue-50 border-t border-blue-200 px-6 py-3">
          <details className="text-sm">
            <summary className="cursor-pointer text-blue-700 font-medium">
              AI Response Info
              {lastAgentInfo.needs_escalation && (
                <span className="ml-2 px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs">
                  Escalation needed
                </span>
              )}
            </summary>
            <div className="mt-2 text-gray-600 space-y-1">
              <p>Model: {lastAgentInfo.model}</p>
              {lastAgentInfo.escalation_reason && (
                <p>Escalation reason: {lastAgentInfo.escalation_reason}</p>
              )}
              {lastAgentInfo.context_used.length > 0 && (
                <p>
                  Context from KB: {lastAgentInfo.context_used.map(c => 
                    `${c.source} (${(c.score * 100).toFixed(0)}%)`
                  ).join(', ')}
                </p>
              )}
            </div>
          </details>
        </div>
      )}

      {/* Input Area */}
      <div className="bg-white border-t px-6 py-4">
        {/* ADDED: Warning about slow AI responses */}
        <div className="mb-3 text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded">
          ⚠️ AI responses may take 15-60 seconds. Please be patient after clicking "AI Respond".
        </div>
        
        <form onSubmit={handleSendMessage} className="flex items-end gap-3">
          <div className="flex-1">
            <textarea
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage(e);
                }
              }}
              placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
              rows={2}
              className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              disabled={sending || generating}
            />
          </div>
          
          <div className="flex flex-col gap-2">
            <button
              type="submit"
              disabled={!newMessage.trim() || sending || generating}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {sending ? 'Sending...' : 'Send'}
            </button>
            
            <button
              type="button"
              onClick={handleGenerateResponse}
              disabled={generating || sending}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {generating ? `AI... ${formatTime(elapsedTime)}` : '🤖 AI Respond'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TicketDetail;
