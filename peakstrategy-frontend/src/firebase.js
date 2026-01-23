import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Load from environment variables
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

// Validate environment variables
if (!firebaseConfig.apiKey || firebaseConfig.apiKey === 'your_api_key_here') {
  console.error('Firebase API key is missing or incorrect!');
  console.error('Please set VITE_FIREBASE_API_KEY in your .env file');
  throw new Error('Firebase configuration is missing');
}

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth };