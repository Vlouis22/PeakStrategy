import { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../firebase.js';
import { signInWithCustomToken, signOut, onAuthStateChanged } from 'firebase/auth';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Your Flask backend URL - uses Vite proxy when empty
  const BACKEND_URL = import.meta.env.VITE_REACT_APP_BACKEND_URL || '';

  const signup = async (email, password, displayName = '') => {
    try {
        const response = await fetch(`${BACKEND_URL}/api/v1/auth/signup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          // No credentials: 'include' unless you need cookies
          body: JSON.stringify({ email, password, display_name: displayName}),
        });
      const data = await response.json();

      if (!response.ok) {
        // Handle backend validation errors
        const errorMessage = data.error || data.message || 'Failed to create account';
        throw new Error(errorMessage);
      }

      // The backend should return a custom token
      const customToken = data.token || data.data?.token;
      
      if (!customToken) {
        throw new Error('No authentication token received from server');
      }

      // Sign in with the custom token from Flask backend
      const userCredential = await signInWithCustomToken(auth, customToken);
      return userCredential;
    } catch (error) {
      console.error('Signup error:', error);
      throw error;
    }
  };

  // ✅ NEW: Login via Flask backend
  const login = async (email, password) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.error || data.message || 'Failed to sign in';
        throw new Error(errorMessage);
      }

      // Get custom token from backend response
      const customToken = data.token || data.data?.token;
      
      if (!customToken) {
        throw new Error('No authentication token received from server');
      }

      // Sign in with the custom token
      const userCredential = await signInWithCustomToken(auth, customToken);
      return userCredential;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  // Logout remains the same
  const logout = () => {
    return signOut(auth);
  };

  // Get current user profile from backend
  const getProfile = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/users/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${await auth.currentUser.getIdToken()}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Get profile error:', error);
      throw error;
    }
  };

  // Update user profile
  const updateProfile = async (profileData) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/users/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await auth.currentUser.getIdToken()}`,
        },
        credentials: 'include',
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to update profile');
      }

      return await response.json();
    } catch (error) {
      console.error('Update profile error:', error);
      throw error;
    }
  };

  // Listen for auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setCurrentUser(user);
      setLoading(false);
      
      // Optional: Update user's last login timestamp
      if (user) {
        // You can call a backend endpoint to update last login
        // fetch(`${BACKEND_URL}/api/v1/users/${user.uid}/last-login`, { method: 'POST' });
      }
    });

    return unsubscribe;
  }, []);

  const value = {
    currentUser,
    signup,
    login,
    logout,
    getProfile,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
}