# HTTPS Setup - Quick Start Guide

## ✅ What's Already Done

1. ✅ SSL certificates generated (`/home/nyra/Documents/test/ssl/`)
2. ✅ nginx configuration created (`nginx-www.nyra-team.com.conf`)
3. ✅ Frontend `.env.local` updated to use `https://www.nyra-team.com`
4. ✅ Backend CORS already configured for `https://www.nyra-team.com`
5. ✅ Setup scripts created

## 🚀 Next Steps (Run These Commands)

### 1. Run the HTTPS Setup Script

This will install the CA, configure nginx, and update `/etc/hosts`:

```bash
cd /home/nyra/Documents/test
./setup-https.sh
```

**Note:** This requires your sudo password to:
- Install the mkcert CA certificate
- Copy nginx configuration
- Update `/etc/hosts`

### 2. Verify Frontend Environment

Make sure your `apps/frontend/.env.local` has all required variables:

```bash
cat apps/frontend/.env.local
```

You should see:
- `NEXT_PUBLIC_URL=https://www.nyra-team.com` ✅
- `NEXT_PUBLIC_APP_URL=https://www.nyra-team.com` ✅
- `NEXT_PUBLIC_SUPABASE_URL=...` (must be set)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY=...` (must be set)
- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/v1`
- `NEXT_PUBLIC_ENV_MODE=LOCAL`

### 3. Restart Your Services

**Frontend:**
```bash
cd apps/frontend
# Stop current dev server (Ctrl+C), then:
npm run dev
```

**Backend:**
```bash
# Restart if needed to pick up any changes
```

### 4. Access Your App

Open your browser and go to:

**https://www.nyra-team.com**

The browser will trust the certificate automatically because the mkcert CA is installed.

## 🔍 Troubleshooting

### "Certificate not trusted" error
- Make sure you ran `./setup-https.sh` (installs the CA)
- Restart your browser after installing the CA

### "Connection refused" or "This site can't be reached"
- Check nginx is running: `sudo systemctl status nginx`
- Check Next.js dev server is running on port 3000
- Verify `/etc/hosts` has: `127.0.0.1    www.nyra-team.com`

### Still seeing HTTP instead of HTTPS
- Clear browser cache
- Make sure `.env.local` has `NEXT_PUBLIC_URL=https://www.nyra-team.com`
- Restart frontend dev server

### nginx errors
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Test config: `sudo nginx -t`
- Verify certificates exist: `ls -la ssl/`

## 📝 Manual Setup (If Script Fails)

If the automated script doesn't work, see `HTTPS-SETUP.md` for manual steps.

## 🎯 What This Setup Does

- **nginx** listens on port 443 (HTTPS) and proxies to Next.js on port 3000
- **HTTP** (port 80) automatically redirects to HTTPS
- **WebSocket** support included for Next.js HMR
- **SSL certificates** are trusted by your browser (via mkcert CA)

