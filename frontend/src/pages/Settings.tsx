import React, { useEffect, useState } from 'react';
import { api } from '../api/client';

interface IntegrationStatus {
  system: string;
  enabled: boolean;
  configured: boolean;
  last_sync: string | null;
}

interface TenantInfo {
  id: number;
  name: string;
  slug: string | null;
  is_active: boolean;
}

const Settings: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);
  const [tenant, setTenant] = useState<TenantInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        
        const [integrationsRes, tenantRes] = await Promise.all([
          api.get<IntegrationStatus[]>('/v1/integrations/status'),
          api.get<TenantInfo>('/v1/tenants/current'),
        ]);
        
        setIntegrations(integrationsRes.data);
        setTenant(tenantRes.data);
      } catch (err) {
        setError('Failed to load settings');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);
      
      // Placeholder for save logic
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      setSuccessMessage('Settings saved successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
          {successMessage}
        </div>
      )}

      {/* Tenant Information */}
      <section className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Organization</h2>
        </div>
        <div className="p-6">
          {tenant && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Organization Name
                </label>
                <input
                  type="text"
                  value={tenant.name}
                  disabled
                  className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slug
                </label>
                <input
                  type="text"
                  value={tenant.slug || ''}
                  disabled
                  className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-500"
                />
              </div>
            </div>
          )}
        </div>
      </section>

      {/* AI Agent Settings */}
      <section className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">🤖 AI Agent</h2>
        </div>
        <div className="p-6 space-y-4">
          <label className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-gray-700">Enable AI Auto-Response</span>
              <p className="text-xs text-gray-500">AI will automatically respond to new tickets</p>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 text-blue-600 rounded border-gray-300"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-gray-700">Use Knowledge Base Context</span>
              <p className="text-xs text-gray-500">AI will search KB for relevant information</p>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 text-blue-600 rounded border-gray-300"
            />
          </label>
          
          <label className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-gray-700">Auto-Escalate Complex Issues</span>
              <p className="text-xs text-gray-500">AI will flag tickets it cannot handle</p>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 text-blue-600 rounded border-gray-300"
            />
          </label>
          
          <div className="pt-4 border-t">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              AI Model
            </label>
            <select className="w-full border border-gray-300 rounded-md px-3 py-2">
              <option value="qwen2.5:3b">qwen2.5:3b (Default, 3B params)</option>
              <option value="qwen2.5:7b">qwen2.5:7b (Better quality, 7B params)</option>
              <option value="llama3.2:3b">llama3.2:3b (Alternative)</option>
              <option value="phi3:mini">phi3:mini (Lightweight)</option>
            </select>
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Integrations</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {integrations.map((integration) => (
            <div key={integration.system} className="p-6 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium text-gray-900 capitalize">
                  {integration.system}
                </h3>
                <p className="text-sm text-gray-500">
                  {integration.configured
                    ? 'Configured and ready to use'
                    : 'Not configured - add credentials in environment'}
                </p>
                {integration.last_sync && (
                  <p className="text-xs text-gray-400 mt-1">
                    Last sync: {new Date(integration.last_sync).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    integration.enabled
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {integration.enabled ? 'Enabled' : 'Disabled'}
                </span>
                <button
                  className="text-blue-600 hover:text-blue-800 text-sm"
                  onClick={() => alert(`Configure ${integration.system} in .env file`)}
                >
                  Configure
                </button>
              </div>
            </div>
          ))}
          
          {integrations.length === 0 && (
            <div className="p-6 text-center text-gray-500">
              No integrations available
            </div>
          )}
        </div>
      </section>

      {/* Notification Settings */}
      <section className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Notifications</h2>
        </div>
        <div className="p-6 space-y-4">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Email notifications for new tickets</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              defaultChecked
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Email notifications for ticket updates</span>
          </label>
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              className="h-4 w-4 text-blue-600 rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">Daily digest email</span>
          </label>
        </div>
      </section>

      {/* API Settings */}
      <section className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">API</h2>
        </div>
        <div className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              API Endpoint
            </label>
            <input
              type="text"
              value={window.location.origin + '/v1'}
              disabled
              className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50 text-gray-500 font-mono text-sm"
            />
          </div>
          <p className="text-sm text-gray-500">
            Use this endpoint to integrate with external applications.
            See the <a href="/docs" className="text-blue-600 hover:underline">API documentation</a> for more details.
          </p>
        </div>
      </section>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>
    </div>
  );
};

export default Settings;
