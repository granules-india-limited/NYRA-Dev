# HTTPS Local Development Setup

This guide will help you set up HTTPS for local development using `www.nyra-team.com`.

## Prerequisites

- nginx installed and running
- mkcert downloaded to `/tmp/mkcert`
- SSL certificates generated in `/home/nyra/Documents/test/ssl/`

## Quick Setup

Run the automated setup script:

```bash
./setup-https.sh
```

This script will:
1. Install the mkcert CA (requires sudo password)
2. Install nginx configuration
3. Update `/etc/hosts`
4. Test and reload nginx

## Manual Setup

If you prefer to set up manually:

### 1. Install mkcert CA

```bash
sudo /tmp/mkcert -install
```

### 2. Install nginx configuration

```bash
sudo cp nginx-www.nyra-team.com.conf /etc/nginx/conf.d/www.nyra-team.com.conf
sudo nginx -t  # Test configuration
sudo systemctl reload nginx  # Or: sudo nginx -s reload
```

### 3. Update /etc/hosts

```bash
echo "127.0.0.1    www.nyra-team.com" | sudo tee -a /etc/hosts
```

### 4. Update Frontend Environment

Edit `apps/frontend/.env.local`:

```bash
NEXT_PUBLIC_URL=https://www.nyra-team.com
NEXT_PUBLIC_APP_URL=https://www.nyra-team.com
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/v1
NEXT_PUBLIC_ENV_MODE=LOCAL
NEXT_PUBLIC_SUPABASE_URL=<your-supabase-url>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-supabase-key>
```

### 5. Restart Frontend Dev Server

Stop your current frontend dev server and restart it:

```bash
cd apps/frontend
npm run dev
```

## Access Your App

Once everything is set up, access your app at:

**https://www.nyra-team.com**

The browser will trust the certificate because the mkcert CA is installed in your system trust store.

## Troubleshooting

### Certificate not trusted
- Make sure you ran `sudo /tmp/mkcert -install`
- Restart your browser after installing the CA

### nginx not starting
- Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Test configuration: `sudo nginx -t`
- Make sure certificates exist: `ls -la /home/nyra/Documents/test/ssl/`

### Connection refused
- Make sure your Next.js dev server is running on port 3000
- Check nginx is running: `sudo systemctl status nginx`

### Still seeing HTTP redirects
- Clear browser cache
- Make sure `.env.local` has `NEXT_PUBLIC_URL=https://www.nyra-team.com`
- Restart the frontend dev server

## Files Created

- `/home/nyra/Documents/test/ssl/www.nyra-team.com.pem` - SSL certificate
- `/home/nyra/Documents/test/ssl/www.nyra-team.com-key.pem` - SSL private key
- `/home/nyra/Documents/test/nginx-www.nyra-team.com.conf` - nginx configuration
- `/home/nyra/Documents/test/setup-https.sh` - Automated setup script

## Notes

- The nginx configuration proxies HTTPS (port 443) to your Next.js dev server (port 3000)
- HTTP (port 80) automatically redirects to HTTPS
- WebSocket support is included for Next.js HMR (Hot Module Replacement)
- The backend CORS is already configured to allow `https://www.nyra-team.com`

