# Verify Billing is Disabled

## Current Configuration

Your backend `.env` has:
```bash
ENV_MODE=local
DISABLE_BILLING=true
```

## Steps to Verify

### 1. Check Backend Logs

After restarting the backend, you should see:
```
DISABLE_BILLING: True (from env: true)
```

### 2. Restart Backend

**IMPORTANT**: The backend must be restarted to pick up the `DISABLE_BILLING=true` setting!

```bash
# Stop your backend server (Ctrl+C)
# Then restart it
cd backend
# Your usual start command (e.g., python api.py or uv run api.py)
```

### 3. Check Account State Response

When you call `/api/v1/billing/account-state`, you should get:
```json
{
  "credits": {
    "total": 999999,
    "can_run": true
  },
  "subscription": {
    "tier_key": "free",
    "tier_display_name": "Free (Billing Disabled)"
  }
}
```

### 4. Check Backend Logs When Accessing Account State

You should see:
```
[ACCOUNT_STATE] Billing disabled - returning unlimited credits for <user_id>
```

## If It's Still Not Working

1. **Verify .env file location**: Make sure `DISABLE_BILLING=true` is in `backend/.env` (not `backend/.env.local` or elsewhere)

2. **Check backend is reading it**: Look for the log message `DISABLE_BILLING: True` when backend starts

3. **Clear browser cache**: The frontend might be caching the old account state

4. **Check frontend env**: Make sure `NEXT_PUBLIC_ENV_MODE=LOCAL` in `apps/frontend/.env.local`

## Why This Happens

When using a production domain (`nyra-team.com`), the app might try to use production Stripe keys. The `DISABLE_BILLING=true` flag bypasses ALL billing checks, regardless of domain or environment mode.

## Quick Test

After restarting backend, check the logs:
```bash
tail -f .logs/backend.log | grep -i "billing\|DISABLE_BILLING"
```

You should see the billing disabled messages when account state is requested.

