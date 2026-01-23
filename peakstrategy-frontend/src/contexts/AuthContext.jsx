import { createContext, useContext, useState, useEffect } from 'react';
import { auth } from '../firebase.js';
import { signInWithEmailAndPassword, createUserWithEmailAndPassword, updateProfile, signOut, onAuthStateChanged } from 'firebase/auth';

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
      // Create user directly with Firebase
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      
      // Update the user's display name if provided
      if (displayName && userCredential.user) {
        await updateProfile(userCredential.user, { displayName });
      }
      
      return userCredential;
    } catch (error) {
      console.error('Signup error:', error);
      // Provide user-friendly error messages
      if (error.code === 'auth/email-already-in-use') {
        throw new Error('This email is already registered');
      } else if (error.code === 'auth/weak-password') {
        throw new Error('Password should be at least 6 characters');
      } else if (error.code === 'auth/invalid-email') {
        throw new Error('Invalid email address');
      }
      throw error;
    }
  };

  // Login via Firebase directly
  const login = async (email, password) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential;
    } catch (error) {
      console.error('Login error:', error);
      // Provide user-friendly error messages
      if (error.code === 'auth/user-not-found') {
        throw new Error('No account found with this email');
      } else if (error.code === 'auth/wrong-password' || error.code === 'auth/invalid-credential') {
        throw new Error('Invalid email or password');
      } else if (error.code === 'auth/too-many-requests') {
        throw new Error('Too many failed attempts. Please try again later.');
      }
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