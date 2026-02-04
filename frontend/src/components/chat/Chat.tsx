/**
 * Chat Component - FIXED VERSION
 * 
 * Fixes:
 * 1. Fixed Spinner import
 * 2. Using correct API types
 * 3. Improved error handling
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { agentApi, AgentResponse } from '../../api/client';
import { Spinner, Alert, Button } from '../common';
import { MESSAGE_ROLE_CONFIG } from '../../constants/tickets';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    model?: string;
    context_used?: Array<{
      source: string;
      chunk: string;
      score: number;
    }>;
    timestamp?: string;
  } | null;
}

interface ChatProps {
  ticketId?: number;
  initialMessages?: Message[];
  onMessageSent?: (message: Message) => void;
  onEscalate?: (reason: string) => void;
}

export const Chat: React.FC<ChatProps> = ({
  ticketId,
  initialMessages = [],
  onMessageSent,
  onEscalate,
}) => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    setError(null);
    
    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      metadata: { timestamp: new Date().toISOString() },
    };
    setMessages((prev) => [...prev, userMessage]);
    onMessageSent?.(userMessage);
    setInput('');

    // Create placeholder for assistant response
    const assistantId = `assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      metadata: null,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    setIsLoading(true);

    try {
      let response: AgentResponse;
      
      if (ticketId) {
        response = await agentApi.respond(ticketId, { save_response: true });
      } else {
        response = await agentApi.ask({ question: content, max_context: 5 });
      }

      // Update assistant message with response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantId
            ? {
                ...msg,
                content: response.content,
                metadata: {
                  model: response.model,
                  context_used: response.context_used,
                  timestamp: new Date().toISOString(),
                },
              }
            : msg
        )
      );

      // Handle escalation
      if (response.needs_escalation && response.escalation_reason) {
        onEscalate?.(response.escalation_reason);
      }
    } catch (err) {
      setError('Failed to get response. Please try again.');
      // Remove placeholder message on error
      setMessages((prev) => prev.filter((msg) => msg.id !== assistantId));
    } finally {
      setIsLoading(false);
    }
  }, [isLoading, ticketId, onMessageSent, onEscalate]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Error */}
      {error && (
        <Alert type="error" message={error} onClose={() => setError(null)} className="m-4" />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            Start a conversation by typing a message below.
          </div>
        )}

        {messages.map((message) => {
          const config = MESSAGE_ROLE_CONFIG[message.role] || MESSAGE_ROLE_CONFIG.system;
          return (
            <div key={message.id} className={`max-w-3xl ${config.align}`}>
              <div className={`rounded-lg border p-4 ${config.bg}`}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-600">
                    {config.label}
                  </span>
                  {message.metadata?.timestamp && (
                    <span className="text-xs text-gray-400">
                      {new Date(message.metadata.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                
                {message.content ? (
                  <div className="text-sm text-gray-800 whitespace-pre-wrap">
                    {message.content}
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <Spinner size="sm" />
                    <span>Thinking...</span>
                  </div>
                )}

                {/* Context info */}
                {message.metadata?.context_used && message.metadata.context_used.length > 0 && (
                  <details className="mt-3 text-xs">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                      Context ({message.metadata.context_used.length} sources)
                    </summary>
                    <div className="mt-2 space-y-1">
                      {message.metadata.context_used.map((ctx, i) => (
                        <div key={i} className="flex justify-between text-gray-500">
                          <span>{ctx.source}</span>
                          <span>{(ctx.score * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </div>
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-white">
        <div className="flex gap-3">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            rows={2}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          />
          <Button type="submit" disabled={!input.trim() || isLoading} loading={isLoading}>
            Send
          </Button>
        </div>
      </form>
    </div>
  );
};

export default Chat;
