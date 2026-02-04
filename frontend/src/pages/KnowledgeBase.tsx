import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api/client';

interface KBChunk {
  id: number;
  source: string;
  chunk: string;
  version: number;
  is_current: boolean;
}

interface SearchResult {
  id: number;
  source: string;
  chunk: string;
  score: number;
}

const KnowledgeBase: React.FC = () => {
  // List state
  const [chunks, setChunks] = useState<KBChunk[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Add form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSource, setNewSource] = useState('');
  const [newContent, setNewContent] = useState('');
  const [adding, setAdding] = useState(false);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [searching, setSearching] = useState(false);
  
  // Reindex state
  const [reindexing, setReindexing] = useState(false);
  const [reindexResult, setReindexResult] = useState<string | null>(null);

  const fetchChunks = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.get<KBChunk[]>('/v1/kb/chunks?limit=100');
      setChunks(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load knowledge base');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChunks();
  }, [fetchChunks]);

  const handleAddChunk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSource.trim() || !newContent.trim() || adding) return;
    
    try {
      setAdding(true);
      setError(null);
      
      await api.post('/v1/kb/chunks', {
        source: newSource.trim(),
        chunks: [{ content: newContent.trim() }],
      });
      
      setNewSource('');
      setNewContent('');
      setShowAddForm(false);
      await fetchChunks();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add chunk');
    } finally {
      setAdding(false);
    }
  };

  const handleDeleteSource = async (source: string) => {
    if (!confirm(`Delete all chunks from "${source}"?`)) return;
    
    try {
      setError(null);
      await api.delete(`/v1/kb/sources/${encodeURIComponent(source)}`);
      await fetchChunks();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete source');
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || searching) return;
    
    try {
      setSearching(true);
      setError(null);
      
      const response = await api.post<SearchResult[]>('/v1/kb/search', {
        query: searchQuery.trim(),
        limit: 10,
      });
      
      setSearchResults(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleReindex = async () => {
    if (reindexing) return;
    
    try {
      setReindexing(true);
      setError(null);
      setReindexResult(null);
      
      const response = await api.post<{ processed: number; success: number; failed: number }>(
        '/v1/kb/reindex'
      );
      
      setReindexResult(
        `Reindexed: ${response.data.success}/${response.data.processed} successful` +
        (response.data.failed > 0 ? `, ${response.data.failed} failed` : '')
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Reindex failed');
    } finally {
      setReindexing(false);
    }
  };

  const clearSearch = () => {
    setSearchResults(null);
    setSearchQuery('');
  };

  // Group chunks by source
  const chunksBySource = chunks.reduce((acc, chunk) => {
    if (!acc[chunk.source]) {
      acc[chunk.source] = [];
    }
    acc[chunk.source].push(chunk);
    return acc;
  }, {} as Record<string, KBChunk[]>);

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-sm text-gray-500 mt-1">
            {chunks.length} chunks from {Object.keys(chunksBySource).length} sources
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleReindex}
            disabled={reindexing}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {reindexing ? 'Reindexing...' : '🔄 Reindex All'}
          </button>
          
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            + Add Content
          </button>
        </div>
      </div>

      {/* Reindex Result */}
      {reindexResult && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
          {reindexResult}
          <button
            onClick={() => setReindexResult(null)}
            className="ml-4 text-green-500 hover:text-green-700"
          >
            ✕
          </button>
        </div>
      )}

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

      {/* Add Form */}
      {showAddForm && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Add New Content</h2>
          <form onSubmit={handleAddChunk}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source (category name)
              </label>
              <input
                type="text"
                value={newSource}
                onChange={(e) => setNewSource(e.target.value)}
                placeholder="e.g., FAQ, Product Docs, Troubleshooting"
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Content
              </label>
              <textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="Enter knowledge base content..."
                rows={5}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={adding || !newSource.trim() || !newContent.trim()}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {adding ? 'Adding...' : 'Add Chunk'}
              </button>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <form onSubmit={handleSearch} className="flex items-center gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search knowledge base (semantic search)..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {searching ? 'Searching...' : '🔍 Search'}
          </button>
          {searchResults && (
            <button
              type="button"
              onClick={clearSearch}
              className="text-gray-500 hover:text-gray-700"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Search Results */}
      {searchResults && (
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">
              Search Results ({searchResults.length})
            </h2>
          </div>
          
          {searchResults.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              No results found for "{searchQuery}"
            </div>
          )}
          
          <div className="divide-y">
            {searchResults.map((result) => (
              <div key={result.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-600">
                    {result.source}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    result.score >= 0.7 
                      ? 'bg-green-100 text-green-700' 
                      : result.score >= 0.4 
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-600'
                  }`}>
                    {(result.score * 100).toFixed(0)}% match
                  </span>
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                  {result.chunk}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}

      {/* Chunks by Source */}
      {!loading && !searchResults && (
        <div className="space-y-6">
          {Object.keys(chunksBySource).length === 0 && (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <p className="text-gray-500 mb-4">Knowledge base is empty</p>
              <button
                onClick={() => setShowAddForm(true)}
                className="text-blue-600 hover:text-blue-800"
              >
                Add your first content
              </button>
            </div>
          )}
          
          {Object.entries(chunksBySource).map(([source, sourceChunks]) => (
            <div key={source} className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">{source}</h2>
                  <p className="text-sm text-gray-500">{sourceChunks.length} chunks</p>
                </div>
                <button
                  onClick={() => handleDeleteSource(source)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Delete All
                </button>
              </div>
              
              <div className="divide-y max-h-96 overflow-y-auto">
                {sourceChunks.map((chunk) => (
                  <div key={chunk.id} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-400">ID: {chunk.id}</span>
                      <span className="text-xs text-gray-400">v{chunk.version}</span>
                    </div>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap line-clamp-4">
                      {chunk.chunk}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;
