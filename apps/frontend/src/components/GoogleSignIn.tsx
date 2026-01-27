'use client';

import { useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import { toast } from '@/lib/toast';
import { Icons } from './home/icons';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslations } from 'next-intl';

interface GoogleSignInProps {
  returnUrl?: string;
}

export default function GoogleSignIn({ returnUrl }: GoogleSignInProps) {
  const [isLoading, setIsLoading] = useState(false);
  const supabase = createClient();
  const t = useTranslations('auth');

  const handleGoogleSignIn = async () => {
    try {
      setIsLoading(true);
      
      // Always use production domain for OAuth redirects
      const origin = process.env.NEXT_PUBLIC_URL || 'https://www.nyra-team.com'
      
      // Debug: Log before OAuth initiation
      console.log('🔐 Initiating Google OAuth with redirectTo:', `${origin}/auth/callback${returnUrl ? `?returnUrl=${encodeURIComponent(returnUrl)}` : ''}`)
      console.log('🍪 Current cookies before OAuth:', document.cookie)
      
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${origin}/auth/callback${returnUrl ? `?returnUrl=${encodeURIComponent(returnUrl)}` : ''
            }`,
        },
      });
      
      // Debug: Log after OAuth initiation (cookies should be set now)
      setTimeout(() => {
        console.log('🍪 Cookies after OAuth initiation:', document.cookie)
      }, 100)

      if (error) {
        throw error;
      }
    } catch (error: any) {
      console.error('Google sign-in error:', error);
      toast.error(error.message || 'Failed to sign in with Google');
      setIsLoading(false);
    }
  };

  return (
    <Button
      onClick={handleGoogleSignIn}
      disabled={isLoading}
      variant="outline"
      size="lg"
      className="w-full h-12"
      type="button"
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Icons.google className="w-4 h-4" />
      )}
      <span>
        {isLoading ? t('signingIn') : t('continueWithGoogle')}
      </span>
    </Button>
  );
}