# Nginx Config Issue Found! 🔧

## Problem

The `/api/v1` location block is **outside the server block** and has incorrect indentation. This causes nginx to not properly route requests.

## Current (Wrong) Structure:

```nginx
    # Video generate comment...
    }

# Backend API proxy - must come before default location  ← OUTSIDE server block!
   location /api/v1 {  ← Wrong indentation (3 spaces)
       ...
}

    # Default location - frontend app  ← INSIDE server block
    location / {
        ...
    }
}
```

## Correct Structure:

```nginx
    # Video generate comment...
    }

    # Backend API proxy - must come before default location  ← INSIDE server block
    location /api/v1 {  ← Correct indentation (4 spaces)
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

    # Default location - frontend app
    location / {
        ...
    }
}
```

## Quick Fix

### Option 1: Run the fix script
```bash
chmod +x fix-nginx-indentation.sh
./fix-nginx-indentation.sh
```

### Option 2: Manual fix

1. **Edit the file**:
   ```bash
   sudo nano /etc/nginx/sites-available/nyra-team.com
   ```

2. **Find this section** (around line 120-130):
   ```nginx
   # Backend API proxy - must come before default location
   location /api/v1 {
   ```

3. **Delete those lines** (the incorrectly placed block)

4. **Find this line** (around line 130):
   ```nginx
   # Default location - frontend app
   ```

5. **Add this block RIGHT BEFORE that line** (with proper 4-space indentation):
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

6. **Save and test**:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## Why This Matters

- Location blocks must be **inside** the server block
- Indentation must be consistent (4 spaces in your config)
- The `/api/v1` block must come **before** the `location /` block (more specific paths first)

After fixing this, both your frontend and backend API should work correctly!

