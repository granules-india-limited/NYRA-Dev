import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  // Only create client in browser environment
  if (typeof window === 'undefined') {
    // Return a mock client for SSR - this should never actually be used
    // but prevents errors during server-side rendering
    return null as any
  }

  // createBrowserClient uses localStorage by default for PKCE
  // We need to provide cookie handlers so PKCE code verifier is stored in cookies
  // This allows the server-side callback route to read it
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          // Parse cookies from document.cookie
          const cookies: { name: string; value: string }[] = []
          if (typeof document !== 'undefined' && document.cookie) {
            document.cookie.split('; ').forEach(cookie => {
              const [name, ...rest] = cookie.split('=')
              if (name) {
                cookies.push({ 
                  name: name.trim(), 
                  value: decodeURIComponent(rest.join('=')) 
                })
              }
            })
          }
          return cookies
        },
        setAll(cookiesToSet) {
          // Set cookies via document.cookie
          if (typeof document === 'undefined') return
          
          cookiesToSet.forEach(({ name, value, options }) => {
            let cookieString = `${name}=${encodeURIComponent(value)}`
            
            // Set path (default to root)
            cookieString += `; path=${options?.path || '/'}`
            
            // Set max-age if provided
            if (options?.maxAge) {
              cookieString += `; max-age=${options.maxAge}`
            }
            
            // Set SameSite (default to lax for OAuth to work)
            const sameSite = options?.sameSite || 'lax'
            cookieString += `; samesite=${sameSite}`
            
            // Only set secure flag if we're on HTTPS
            // Setting secure on HTTP cookies prevents them from being set
            if (options?.secure && window.location.protocol === 'https:') {
              cookieString += '; secure'
            }
            
            // Set max-age if not already set (default 1 hour for PKCE)
            if (!options?.maxAge) {
              cookieString += `; max-age=3600`
            }
            
            // Note: httpOnly cannot be set via document.cookie (server-only)
            // Note: Don't set domain - let browser use current domain automatically
            
            document.cookie = cookieString
            // Debug: Log PKCE-related cookies
            if (name.includes('code-verifier') || name.includes('pkce') || name.includes('auth')) {
              console.log('🍪 Set auth cookie:', name.substring(0, 20) + '...', 'path:', options?.path || '/', 'sameSite:', sameSite)
            }
          })
        },
      },
    }
  )
}
