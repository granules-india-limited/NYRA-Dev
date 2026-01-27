# Unlimited Credits Setup - Complete Guide

## Goal

Have unlimited credits in both dev and production, using your own LLM, with no Stripe billing.

## Solution

### Backend Configuration

Add to `backend/.env`:
```bash
ENV_MODE=local
DISABLE_BILLING=true
```

**IMPORTANT**: Restart the backend after adding `DISABLE_BILLING=true`!

### How It Works

1. **`DISABLE_BILLING=true`** bypasses ALL billing checks
2. Returns unlimited credits (999,999) for all users
3. Works in ANY environment (local, staging, production)
4. No Stripe integration needed
5. Uses your local LLM

### Frontend Changes Made

✅ **Pricing Modal**: Hidden when billing is disabled (no "billing features disabled" message)
✅ **Upgrade Button**: Hidden in credits display when billing is disabled
✅ **Promo Banner**: Hidden when billing is disabled
✅ **Sidebar Upgrade**: Hidden when billing is disabled

### Verification

After restarting backend:

1. **Check backend logs** for:
   ```
   DISABLE_BILLING: True (from env: true)
   ```

2. **Check account state** - should return:
   ```json
   {
     "credits": { "total": 999999, "can_run": true },
     "subscription": {
       "tier_key": "free",
       "tier_display_name": "Free (Billing Disabled)",
       "provider": "local"
     }
   }
   ```

3. **In browser**:
   - Should see **999,999 credits** (not 0)
   - **No upgrade buttons** visible
   - **No billing disabled message**
   - Can use your local LLM

### Key Points

- `DISABLE_BILLING=true` works independently of `ENV_MODE`
- You can disable billing in any environment
- When disabled, all users get unlimited credits automatically
- No database or Stripe checks are performed
- Your local LLM works without any billing restrictions

### Troubleshooting

If credits still show as 0:

1. **Restart backend** (required after changing `.env`)
2. **Check backend logs** for `DISABLE_BILLING: True`
3. **Clear browser cache** (Ctrl+Shift+R)
4. **Verify `.env` file**: Make sure `DISABLE_BILLING=true` is in `backend/.env`

### Summary

With `DISABLE_BILLING=true`:
- ✅ Unlimited credits (999,999)
- ✅ No Stripe required
- ✅ Use your own LLM
- ✅ Works in dev and prod
- ✅ No upgrade buttons
- ✅ No billing messages

Just restart the backend and you're done! 🎉

