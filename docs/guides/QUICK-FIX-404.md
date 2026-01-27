# Quick Fix for 404 Errors

## Problem
Frontend is getting 404 errors when calling `/api/v1/*` endpoints because nginx isn't proxying them to the backend.

## Solution

You need to add a backend API proxy location block to your existing nginx config.

### Option 1: Manual Edit (Recommended)

1. **Edit the nginx config**:
   ```bash
   sudo nano /etc/nginx/sites-available/nyra-team.com
   ```

2. **Find the HTTPS server block** for `www.nyra-team.com` (around line 20-30)

3. **Find the line** that says:
   ```nginx
   # Default location - frontend app
   location / {
       proxy_pass http://127.0.0.1:3000;
   ```

4. **Add this block BEFORE the `location / {` block**:
   ```nginx
   # Backend API proxy - must come before default location
   location /api/v1 {
       proxy_pass http://127.0.0.1:8000/v1;
       proxy_redirect off;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection 'upgrade';
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
       proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       proxy_set_header X-Forwarded-Proto $scheme;
       proxy_set_header Authorization $http_authorization;
       proxy_cache_bypass $http_upgrade;
       proxy_connect_timeout 600s;
       proxy_send_timeout 600s;
       proxy_read_timeout 600s;
   }
   ```

5. **Test and reload**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Option 2: Use the Patch File

The exact block to add is in `nginx-backend-proxy-patch.txt`. Copy it into your nginx config before the `location / {` block.

## Verification

After adding the proxy, test it:

```bash
curl -k https://www.nyra-team.com/api/v1/health
```

Should return JSON from the backend, not a 404.

## Important

- The `/api/v1` location **must come before** the `location /` block
- nginx matches locations in order, so more specific paths must come first
- After editing, always test with `sudo nginx -t` before reloading

