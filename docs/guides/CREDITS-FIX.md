# Fix: Credits Issue When Using Production Domain

## Problem

When using the production domain (`nyra-team.com`), the app shows 0 credits and tries to use Stripe, even though you're in local dev mode.

## Root Cause

The backend needs to be **restarted** to pick up the `DISABLE_BILLING=true` setting from `.env`.

## Solution

### Step 1: Verify Backend Configuration

Check `backend/.env` has:
```bash
ENV_MODE=local
DISABLE_BILLING=true
```

### Step 2: Restart Backend Server

**This is critical!** The backend only reads `.env` on startup.

```bash
# Stop your current backend (Ctrl+C in the terminal where it's running)
# Then restart it with your usual command
cd backend
# Example: python api.py or uv run api.py or whatever you use
```

### Step 3: Verify It's Working

After restarting, check the backend logs. You should see:
```
DISABLE_BILLING: True (from env: true)
```

When you access the account state endpoint, you should see:
```
[ACCOUNT_STATE] Billing disabled - returning unlimited credits for <user_id>
```

### Step 4: Test in Browser

1. Clear browser cache (or use incognito)
2. Go to `https://nyra-team.com/dashboard`
3. You should see:
   - **999,999 credits** (not 0)
   - **Tier: "Free (Billing Disabled)"**
   - **Can use local LLM** without Stripe

## How It Works

The `DISABLE_BILLING=true` flag:
- ✅ Bypasses ALL Stripe checks
- ✅ Returns unlimited credits (999,999)
- ✅ Works regardless of domain (localhost or production domain)
- ✅ Works regardless of ENV_MODE (local, staging, or production)

## Important Notes

1. **Backend must be restarted** after changing `DISABLE_BILLING` in `.env`
2. The flag works independently of `ENV_MODE` - you can disable billing in any environment
3. When `DISABLE_BILLING=true`, the `/account-state` endpoint returns unlimited credits immediately, without checking the database

## Troubleshooting

If credits still show as 0 after restarting:

1. **Check backend logs** for the `DISABLE_BILLING: True` message on startup
2. **Check backend logs** for `[ACCOUNT_STATE] Billing disabled` when accessing account state
3. **Verify .env file**: Make sure `DISABLE_BILLING=true` is in `backend/.env` (not commented out)
4. **Clear frontend cache**: Hard refresh browser (Ctrl+Shift+R)
5. **Check frontend env**: `NEXT_PUBLIC_ENV_MODE=LOCAL` in `apps/frontend/.env.local`

## Quick Verification Command

After restarting backend, check logs:
```bash
tail -f .logs/backend.log | grep -i "billing\|DISABLE_BILLING"
```

You should see billing disabled messages when the app requests account state.

