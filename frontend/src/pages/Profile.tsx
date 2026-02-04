/**
 * Profile Page - FIXED VERSION
 * 
 * Fixes:
 * 1. Replaced placeholder code with actual API calls
 * 2. Replaced confirm() with ConfirmModal
 * 3. Added proper form validation
 * 4. Using common components
 */
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../api/client';
import { Card, Button, Input, Alert, ConfirmModal } from '../components/common';

const Profile: React.FC = () => {
  const { user, logout, refreshUser } = useAuth();
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [showLogoutModal, setShowLogoutModal] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSavingProfile(true);
      setError(null);
      setSuccessMessage(null);
      
      await api.patch('/v1/auth/me', {
        full_name: fullName.trim() || null,
      });
      
      await refreshUser();
      
      setSuccessMessage('Profile updated successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError('Failed to update profile. Please try again.');
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Validation
    if (!currentPassword) {
      setError('Current password is required');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }
    
    try {
      setSavingPassword(true);
      setSuccessMessage(null);
      
      await api.post('/v1/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      });
      
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setSuccessMessage('Password changed successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: unknown) {
      const errorResponse = err as { response?: { data?: { detail?: string } } };
      setError(errorResponse.response?.data?.detail || 'Failed to change password');
    } finally {
      setSavingPassword(false);
    }
  };

  const handleLogout = () => {
    logout();
    setShowLogoutModal(false);
  };

  if (!user) {
    return (
      <div className="p-6">
        <Alert type="warning" message="Please log in to view your profile." />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile</h1>

      {/* Alerts */}
      {error && (
        <Alert type="error" message={error} onClose={() => setError(null)} className="mb-6" />
      )}
      
      {successMessage && (
        <Alert type="success" message={successMessage} onClose={() => setSuccessMessage(null)} className="mb-6" />
      )}

      {/* Profile Information */}
      <Card className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h2>
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <Input
            label="Email"
            type="email"
            value={user.email}
            disabled
            hint="Email cannot be changed"
          />
          
          <Input
            label="Full Name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Enter your full name"
          />
          
          <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
            <div>
              <span className="font-medium">Role:</span> {user.role}
            </div>
            <div>
              <span className="font-medium">Status:</span>{' '}
              <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>
                {user.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="font-medium">Tenant ID:</span> {user.tenant_id}
            </div>
            <div>
              <span className="font-medium">Member since:</span>{' '}
              {new Date(user.created_at).toLocaleDateString()}
            </div>
          </div>
          
          <div className="pt-4">
            <Button type="submit" loading={savingProfile}>
              Save Changes
            </Button>
          </div>
        </form>
      </Card>

      {/* Change Password */}
      <Card className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Change Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="Enter current password"
          />
          
          <Input
            label="New Password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="Enter new password"
            hint="Minimum 8 characters"
          />
          
          <Input
            label="Confirm New Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm new password"
          />
          
          <div className="pt-4">
            <Button
              type="submit"
              loading={savingPassword}
              disabled={!currentPassword || !newPassword || !confirmPassword}
            >
              Change Password
            </Button>
          </div>
        </form>
      </Card>

      {/* Danger Zone */}
      <Card>
        <h2 className="text-lg font-semibold text-red-600 mb-4">Danger Zone</h2>
        <p className="text-sm text-gray-600 mb-4">
          Log out from your account. You will need to log in again to access the system.
        </p>
        <Button variant="danger" onClick={() => setShowLogoutModal(true)}>
          Logout
        </Button>
      </Card>

      {/* Logout Confirmation */}
      <ConfirmModal
        isOpen={showLogoutModal}
        onClose={() => setShowLogoutModal(false)}
        onConfirm={handleLogout}
        title="Logout"
        message="Are you sure you want to log out?"
        confirmText="Logout"
      />
    </div>
  );
};

export default Profile;
