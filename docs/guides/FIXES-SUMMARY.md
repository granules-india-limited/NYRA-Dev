# Fixes Summary - Setup Issue & Billing Disable

## Issues Fixed

### 1. "Failed to fetch" Setup Error ✅

**Problem**: Frontend on HTTPS (`https://www.nyra-team.com`) couldn't call backend on HTTP (`http://localhost:8000`) due to mixed content blocking.

**Solution**:
- Added nginx proxy for backend API at `/api/v1/` → `http://127.0.0.1:8000/v1/`
- Updated frontend API client to automatically use proxied path when on HTTPS
- Updated frontend `.env.local` to use `/api/v1` (relative path)

**Files Changed**:
- `nginx-www.nyra-team.com.conf` - Added backend API proxy
- `apps/frontend/src/lib/api-client.ts` - Auto-detect HTTPS and use proxy
- `apps/frontend/.env.local` - Updated `NEXT_PUBLIC_BACKEND_URL=/api/v1`

### 2. Billing/Subscription Issue ✅

**Problem**: App showing 0 credits and asking for subscription even in local dev mode when using DNS.

**Solution**:
- Added `DISABLE_BILLING` environment variable for easy toggle
- Backend returns unlimited credits and free tier when `DISABLE_BILLING=true`
- Works in any environment (local, staging, production)

**Files Changed**:
- `backend/core/utils/config.py` - Added `DISABLE_BILLING` config
- `backend/core/billing/endpoints/account_state.py` - Check `DISABLE_BILLING` and return mock data
- Frontend automatically respects backend's billing disabled state

## How to Use

### Fix Setup Error

1. **Restart nginx** (if you haven't already):
   ```bash
   sudo systemctl reload nginx
   ```

2. **Restart frontend dev server**:
   ```bash
   cd apps/frontend
   npm run dev
   ```

3. **Access app**: `https://www.nyra-team.com`

The frontend will now automatically use the proxied backend API.

### Disable Billing

1. **Add to `backend/.env`**:
   ```bash
   DISABLE_BILLING=true
   ```

2. **Restart backend**:
   ```bash
   # Stop and restart your backend server
   ```

3. **Verify**: 
   - Account state should show 999,999 credits
   - Tier should show "Free (Billing Disabled)"
   - All limits should be unlimited

### Enable Billing

1. **Update `backend/.env`**:
   ```bash
   DISABLE_BILLING=false
   # Or remove the line (defaults to false)
   ```

2. **Restart backend**

## Testing

### Test Setup Endpoint

1. Go to `https://www.nyra-team.com/setting-up`
2. Should successfully initialize account (no "Failed to fetch" error)
3. Should redirect to dashboard

### Test Billing Disabled

1. Set `DISABLE_BILLING=true` in `backend/.env`
2. Restart backend
3. Check account state:
   - Credits: 999,999
   - Tier: "Free (Billing Disabled)"
   - Can run agents: Yes

## Files Modified

### Backend
- `backend/core/utils/config.py` - Added `DISABLE_BILLING` config
- `backend/core/billing/endpoints/account_state.py` - Billing disabled check

### Frontend
- `apps/frontend/src/lib/api-client.ts` - Auto-proxy backend URL on HTTPS
- `apps/frontend/.env.local` - Updated backend URL to `/api/v1`

### Infrastructure
- `nginx-www.nyra-team.com.conf` - Added backend API proxy

## Documentation

- `BILLING-DISABLE-GUIDE.md` - Detailed guide for disabling billing
- `HTTPS-SETUP.md` - HTTPS setup instructions
- `HTTPS-QUICK-START.md` - Quick reference for HTTPS

## Next Steps

1. ✅ Run `./setup-https.sh` to complete HTTPS setup (if not done)
2. ✅ Restart nginx: `sudo systemctl reload nginx`
3. ✅ Restart frontend: `cd apps/frontend && npm run dev`
4. ✅ Add `DISABLE_BILLING=true` to `backend/.env` (if you want billing disabled)
5. ✅ Restart backend
6. ✅ Test at `https://www.nyra-team.com`

