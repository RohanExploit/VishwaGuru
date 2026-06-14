/**
 * 💾 Supabase Client Configuration
 * 
 * This file initializes and exports the Supabase client for use throughout the application.
 * Environment variables are loaded via Vite's import.meta.env
 * 
 * Security Notes:
 * - VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are safe to expose in the frontend
 * - The anon key is designed for client-side use and is protected by Row Level Security (RLS)
 * - Never expose service_role keys or database passwords in the frontend
 * 
 * @see https://supabase.com/docs/reference/javascript/initializing
 */

import { createClient } from '@supabase/supabase-js';

// Validate environment variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase environment variables!');
  console.error('Please ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set in your .env file');
  throw new Error('Missing Supabase configuration');
}

// Create and export Supabase client
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});

/**
 * Helper function to check if Supabase is properly configured
 * @returns {boolean} True if Supabase is configured
 */
export const isSupabaseConfigured = () => {
  return !!(supabaseUrl && supabaseAnonKey);
};

/**
 * Helper to get the current authenticated user
 * @returns {Promise<{data: {user: object|null}, error: Error|null}>}
 */
export const getCurrentUser = async () => {
  try {
    const { data, error } = await supabase.auth.getUser();
    return { data, error };
  } catch (error) {
    console.error('Error fetching current user:', error);
    return { data: null, error };
  }
};

/**
 * Helper to sign up a new user
 * @param {string} email 
 * @param {string} password 
 * @param {object} metadata - Optional user metadata
 * @returns {Promise<{data: object, error: Error|null}>}
 */
export const signUp = async (email, password, metadata = {}) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata
    }
  });
  return { data, error };
};

/**
 * Helper to sign in an existing user
 * @param {string} email 
 * @param {string} password 
 * @returns {Promise<{data: object, error: Error|null}>}
 */
export const signIn = async (email, password) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  });
  return { data, error };
};

/**
 * Helper to sign out the current user
 * @returns {Promise<{error: Error|null}>}
 */
export const signOut = async () => {
  const { error } = await supabase.auth.signOut();
  return { error };
};

/**
 * Helper to listen to auth state changes
 * @param {function} callback - Function to call when auth state changes
 * @returns {function} Unsubscribe function
 */
export const onAuthStateChange = (callback) => {
  const { data: { subscription } } = supabase.auth.onAuthStateChange(callback);
  return () => subscription.unsubscribe();
};

export default supabase;
