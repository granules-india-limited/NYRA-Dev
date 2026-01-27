'use client';

import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from 'react';
import { createClient } from '@/lib/supabase/client';
import { User, Session } from '@supabase/supabase-js';
import { SupabaseClient } from '@supabase/supabase-js';
import { clearUserLocalStorage } from '@/lib/utils/clear-local-storage';
// Auth tracking moved to AuthEventTracker component (handles OAuth redirects)

type AuthContextType = {
  supabase: SupabaseClient;
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [supabase, setSupabase] = useState<SupabaseClient | null>(null);

  useEffect(() => {
    // Only initialize Supabase client in browser environment
    if (typeof window === 'undefined') {
      setIsLoading(false);
      return;
    }

    const client = createClient();
    if (!client) {
      setIsLoading(false);
      return;
    }

    setSupabase(client);

    const getInitialSession = async () => {
      try {
        const {
          data: { session: currentSession },
        } = await client.auth.getSession();
        setSession(currentSession);
        setUser(currentSession?.user ?? null);
      } catch (error) {
      } finally {
        setIsLoading(false);
      }
    };

    getInitialSession();

    const { data: authListener } = client.auth.onAuthStateChange(
      async (event, newSession) => {
        setSession(newSession);
        setUser(newSession?.user ?? null);
        setIsLoading(false);
        
        switch (event) {
          case 'SIGNED_IN':
            // Auth tracking handled by AuthEventTracker component via URL params
            break;
          case 'SIGNED_OUT':
            clearUserLocalStorage();
            break;
          case 'TOKEN_REFRESHED':
            break;
          case 'MFA_CHALLENGE_VERIFIED':
            break;
          default:
        }
      },
    );

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, []); // Empty deps - only run once on mount

  const signOut = async () => {
    if (!supabase) return;
    try {
      await supabase.auth.signOut();
      // Clear local storage after successful sign out
      clearUserLocalStorage();
    } catch (error) {
      console.error('❌ Error signing out:', error);
    }
  };

  // Create a mock client for SSR or when client isn't ready
  const client = supabase || (null as any);

  const value = {
    supabase: client,
    session,
    user,
    isLoading,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
