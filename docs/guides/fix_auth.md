# Fix Authentication Issues

## Problem
You're signed in but getting 401 errors because your session token is invalid or expired.

## Solution 1: Sign Out and Sign Back In

1. **Open Browser Console** (F12)
2. **Run this command** to sign out:
   ```javascript
   // In browser console
   const supabase = window.supabase || (await import('/src/lib/supabase/client')).createClient();
   await supabase.auth.signOut();
   localStorage.clear();
   sessionStorage.clear();
   window.location.href = '/auth';
   ```

3. **Or manually:**
   - Go to Settings → Log out
   - Clear browser cache and localStorage
   - Sign in again at http://localhost:3000/auth

## Solution 2: Force Sign Out via URL

Add this to your auth page URL to force sign out:
```
http://localhost:3000/auth?mode=signin&expired=true
```

## Solution 3: Verify JWT Secret Matches

The backend needs the correct JWT secret to verify tokens:

1. Go to: https://supabase.com/dashboard/project/fbpipahzwmkjfaolvlgz/settings/api
2. Scroll to "JWT Settings" 
3. Copy the JWT Secret
4. Update `backend/.env`:
   ```
   SUPABASE_JWT_SECRET=your_jwt_secret_here
   ```
5. Restart the backend

## Solution 4: Check Backend Logs

Check if backend is rejecting tokens:
```bash
tail -f .logs/backend.log | grep -i "jwt\|auth\|401"
```

## Quick Fix Script

Run this in browser console to completely reset auth:
```javascript
// Complete auth reset
localStorage.clear();
sessionStorage.clear();
document.cookie.split(";").forEach(c => {
  document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
});
window.location.href = '/auth';
```

