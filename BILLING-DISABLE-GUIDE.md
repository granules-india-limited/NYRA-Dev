# Disable Billing Mode - Quick Guide

## Overview

This guide explains how to easily disable billing checks in development and production environments.

## Backend Configuration

Add this to your `backend/.env` file:

```bash
DISABLE_BILLING=true
```

When `DISABLE_BILLING=true`:
- All users get unlimited credits (999,999)
- All users get free tier access with unlimited limits
- All billing checks are bypassed
- Subscription checks return "Free (Billing Disabled)" tier

## Frontend Configuration

The frontend automatically respects the backend's billing disabled state. No frontend configuration needed.

## How It Works

1. **Backend**: When `DISABLE_BILLING=true`, the `/account-state` endpoint returns:
   - Unlimited credits (999,999)
   - Free tier with unlimited limits
   - All models available

2. **Frontend**: The frontend automatically uses this data and:
   - Shows unlimited credits
   - Skips subscription checks
   - Allows all features

## Toggle Billing On/Off

### Disable Billing
```bash
# In backend/.env
DISABLE_BILLING=true
```

### Enable Billing
```bash
# In backend/.env
DISABLE_BILLING=false
# Or remove the line entirely (defaults to false)
```

**Important**: Restart the backend server after changing this setting.

## Environment-Specific Usage

### Local Development
```bash
# backend/.env
ENV_MODE=local
DISABLE_BILLING=true  # Optional - local mode already has mock data
```

### Production (Testing)
```bash
# backend/.env
ENV_MODE=production
DISABLE_BILLING=true  # Disables billing even in production
```

## Notes

- The `DISABLE_BILLING` flag works independently of `ENV_MODE`
- You can disable billing in any environment (local, staging, production)
- When disabled, all users effectively have unlimited access
- This is useful for:
  - Development and testing
  - Demos and presentations
  - Internal testing environments

## Verification

After setting `DISABLE_BILLING=true` and restarting the backend:

1. Check backend logs - you should see billing checks being skipped
2. Check frontend - account state should show:
   - Tier: "Free (Billing Disabled)"
   - Credits: 999,999
   - All limits: Unlimited

