import React, { useState, useEffect } from 'react';
import { api } from '../api/client';

interface AgentResponse {
  content: string;
  needs_escalation: boolean;
  escalation_reason: string | null;
  context_used: { id: number; source: string; score: number }[];
  model: string;
}

interface HealthStatus {
  ollama_available: boolean;
  chat_model: string;
  embed_model: string;
  models_loaded: string[];
}

const Playground: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AgentResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(false);
  
  // ADDED: Timer for showing elapsed time during long requests
  const [elapsedTime, setElapsedTime] = useState(0);

  // ADDED: Timer effect for showing progress
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      setElapsedTime(0);
      interval = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    try {
      setLoading(true);
      setError(null);
      setResponse(null);

      // FIXED: Extended timeout for LLM requests (3 minutes)
      const result = await api.post<AgentResponse>('/v1/agent/ask', {
        question: question.trim(),
        max_context: 5,
      }, {
        timeout: 180000, // 3 minutes
      });

      setResponse(result.data);
    } catch (err: any) {
      // IMPROVED: Better error messages
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('Request timed out. The AI is taking longer than expected. Please try again.');
      } else if (err.response?.status === 503) {
        setError('AI service is temporarily unavailable. Please check if Ollama is running.');
      } else {
        setError(err.response?.data?.detail || err.message || 'Failed to get response');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      setCheckingHealth(true);
      const result = await api.get<HealthStatus>('/v1/agent/health');
      setHealth(result.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to check health');
    } finally {
      setCheckingHealth(false);
    }
  };

  // Auto-check health on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const exampleQuestions = [
    "Как восстановить пароль?",
    "What are your business hours?",
    "How do I request a refund?",
    "Как связаться с поддержкой?",
  ];

  // Format elapsed time
  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Agent Playground</h1>
        <p className="text-sm text-gray-500 mt-1">
          Test the AI agent with any question. Uses knowledge base for context.
        </p>
      </div>

      {/* Health Check */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="font-medium">Agent Status:</span>
            {health ? (
              <span className={`px-2 py-1 rounded-full text-xs ${
                health.ollama_available 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-red-100 text-red-700'
              }`}>
                {health.ollama_available ? '● Online' : '○ Offline'}
              </span>
            ) : (
              <span className="text-gray-400 text-sm">Unknown</span>
            )}
          </div>
          <button
            onClick={checkHealth}
            disabled={checkingHealth}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {checkingHealth ? 'Checking...' : 'Check Status'}
          </button>
        </div>
        
        {health && health.ollama_available && (
          <div className="mt-3 text-sm text-gray-600 grid grid-cols-2 gap-2">
            <div>Chat Model: <code className="bg-gray-100 px-1 rounded">{health.chat_model}</code></div>
            <div>Embed Model: <code className="bg-gray-100 px-1 rounded">{health.embed_model}</code></div>
            {health.models_loaded.length > 0 && (
              <div className="col-span-2">
                Loaded Models: {health.models_loaded.join(', ')}
              </div>
            )}
          </div>
        )}
        
        {/* ADDED: Warning about slow responses */}
        {health && health.ollama_available && (
          <div className="mt-3 text-xs text-amber-600 bg-amber-50 px-3 py-2 rounded">
            ⚠️ AI responses may take 15-60 seconds on CPU. Please be patient.
          </div>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* Question Form */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Ask a Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your question here..."
              rows={4}
              className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          {/* Example Questions */}
          <div className="mb-4">
            <p className="text-xs text-gray-500 mb-2">Try an example:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQuestions.map((q, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setQuestion(q)}
                  className="text-xs bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded-full text-gray-700"
                  disabled={loading}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                Thinking... ({formatTime(elapsedTime)})
              </span>
            ) : (
              '🤖 Ask AI Agent'
            )}
          </button>
          
          {/* ADDED: Progress indicator for long requests */}
          {loading && (
            <div className="mt-3">
              <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-blue-500 transition-all duration-1000 ease-linear"
                  style={{ 
                    width: `${Math.min((elapsedTime / 60) * 100, 100)}%`,
                  }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1 text-center">
                {elapsedTime < 10 
                  ? 'Searching knowledge base...'
                  : elapsedTime < 30
                    ? 'Generating AI response...'
                    : 'Still working, please wait...'}
              </p>
            </div>
          )}
        </form>
      </div>

      {/* Response */}
      {response && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b bg-green-50">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-green-800">AI Response</h2>
              <div className="flex items-center gap-2">
                {response.needs_escalation && (
                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                    ⚠️ Escalation Needed
                  </span>
                )}
                <span className="text-xs text-gray-500">
                  Model: {response.model}
                </span>
              </div>
            </div>
          </div>

          <div className="p-6">
            <div className="prose max-w-none">
              <div className="text-gray-800 whitespace-pre-wrap">
                {response.content}
              </div>
            </div>
          </div>

          {/* Context Info */}
          {response.context_used.length > 0 && (
            <div className="px-6 py-4 border-t bg-gray-50">
              <details>
                <summary className="cursor-pointer text-sm font-medium text-gray-600">
                  Knowledge Base Context ({response.context_used.length} sources)
                </summary>
                <div className="mt-3 space-y-2">
                  {response.context_used.map((ctx, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between text-sm bg-white p-2 rounded border"
                    >
                      <span className="text-blue-600">{ctx.source}</span>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        ctx.score >= 0.7
                          ? 'bg-green-100 text-green-700'
                          : ctx.score >= 0.4
                            ? 'bg-yellow-100 text-yellow-700'
                            : 'bg-gray-100 text-gray-600'
                      }`}>
                        {(ctx.score * 100).toFixed(0)}% relevance
                      </span>
                    </div>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Escalation Info */}
          {response.needs_escalation && response.escalation_reason && (
            <div className="px-6 py-4 border-t bg-red-50">
              <p className="text-sm text-red-700">
                <strong>Escalation Reason:</strong> {response.escalation_reason}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Playground;
