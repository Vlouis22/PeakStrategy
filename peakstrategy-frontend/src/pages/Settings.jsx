import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const Settings = () => {
  const { currentUser, getProfile, updateBackendProfile } = useAuth();
  const [profile, setProfile] = useState({
    display_name: '',
    email: '',
    created_at: null
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (!currentUser) {
      setLoading(false); // user is not logged in
      return;
    }
    fetchProfile();
  }, [currentUser]);

  const fetchProfile = async () => {
    try {
      const data = await getProfile();
      console.log("Fetched profile data:", data);
      setProfile({
        display_name: data.display_name || currentUser?.displayName || '',
        email: data.email || currentUser?.email || '',
        created_at: data.created_at
      });
    } catch (error) {
      console.error("Failed to fetch profile:", error);
      setError('Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSaving(true);

    try {
      await updateBackendProfile({
        displayName: profile.display_name.trim()
      });
      setSuccess('Profile updated successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (error) {
      setError(error.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Show loading
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  // Show message if user is not logged in
  if (!currentUser) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">No profile found</h1>
          <p className="text-gray-600">Please sign in to access your Settings.</p>
        </div>
      </div>
    );
  }

  // Main settings form
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          Manage your account settings and profile.
        </p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          {success}
        </div>
      )}
      
      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Profile Information</h2>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-2">
              Display Name
            </label>
            <input
              type="text"
              id="display_name"
              name="display_name"
              value={profile.display_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your name"
              required
              minLength="2"
              maxLength="50"
            />
            <p className="mt-1 text-sm text-gray-500">
              This is how your name will appear across PeakStrategy.
            </p>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={profile.email}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm bg-gray-50 text-gray-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Your email address cannot be changed.
            </p>
          </div>

          {profile.created_at && (
            <div className="pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                Account created on{' '}
                <span className="font-medium">
                  {new Date(profile.created_at.toDate()).toLocaleDateString()}
                </span>
              </p>
            </div>
          )}

          <div className="pt-4 border-t border-gray-200">
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>

      {/* Security Section (Optional) */}
      <div className="mt-8 bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">Security</h2>
        </div>
        <div className="p-6">
          <button
            className="px-4 py-2 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
            onClick={() => {
              alert('Password reset functionality coming soon!');
            }}
          >
            Change Password
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
