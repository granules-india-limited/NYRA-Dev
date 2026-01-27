# Quick Fix: Frontend Not Showing

## Problem
You're seeing the default nginx welcome page instead of your app.

## Cause
The frontend proxy location block is commented out in the nginx config.

## Solution

Edit the nginx config and uncomment the frontend location block:

```bash
sudo nano /etc/nginx/sites-available/nyra-team.com
```

Find the section around **line 130** that says:
```nginx
    # Default location - frontend app
    #location / {
        #proxy_pass http://127.0.0.1:3000;
        #proxy_http_version 1.1;
        #proxy_set_header Upgrade $http_upgrade;
        #proxy_set_header Connection 'upgrade';
        #proxy_set_header Host $host;
        #proxy_set_header X-Real-IP $remote_addr;
        #proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        #proxy_set_header X-Forwarded-Proto $scheme;
        #proxy_cache_bypass $http_upgrade;
        #proxy_set_header X-Forwarded-Host $host;
        # Cookie forwarding for OAuth (CRITICAL for PKCE)
        #proxy_set_header Cookie $http_cookie;
        # Timeouts for OAuth callbacks
        #proxy_connect_timeout 600s;
        #proxy_send_timeout 600s;
        #proxy_read_timeout 600s;
    #}
```

**Remove all the `#` characters** from these lines (uncomment them), so it becomes:
```nginx
    # Default location - frontend app
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Forwarded-Host $host;
        # Cookie forwarding for OAuth (CRITICAL for PKCE)
        proxy_set_header Cookie $http_cookie;
        # Timeouts for OAuth callbacks
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
```

Then test and reload:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

Your app should now be accessible at `https://nyra-team.com` or `https://www.nyra-team.com`!

