# Fix: App Not Displaying - Frontend Location Block Commented Out

## Problem
The frontend proxy location block in nginx is commented out, so nginx shows the default page instead of your app.

## Quick Fix (2 minutes)

### Step 1: Edit nginx config
```bash
sudo nano /etc/nginx/sites-available/nyra-team.com
```

### Step 2: Find and uncomment the block
Press `Ctrl+W` to search, type: `Default location - frontend app`

You should see around **line 130-149**:
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
        # Increase buffer sizes to handle large Supabase auth headers
        # Supabase sets many cookies during OAuth, requiring much larger buffers
        proxy_buffer_size 64k;
        proxy_buffers 32 64k;
        proxy_busy_buffers_size 128k;
        # Note: large_client_header_buffers must be in http block, not here
    #}
```

### Step 3: Remove the `#` from these specific lines:
- `#location / {` → `location / {`
- `#proxy_pass http://127.0.0.1:3000;` → `proxy_pass http://127.0.0.1:3000;`
- `#proxy_http_version 1.1;` → `proxy_http_version 1.1;`
- All `#proxy_set_header` lines → remove the `#`
- `#proxy_cache_bypass` → remove the `#`
- `#proxy_connect_timeout` → remove the `#`
- `#proxy_send_timeout` → remove the `#`
- `#proxy_read_timeout` → remove the `#`
- `#}` → `}`

**Keep the comment lines** (lines starting with `# Cookie`, `# Timeouts`, `# Increase`, `# Supabase`, `# Note:`) as comments.

### Step 4: Save and exit
- Press `Ctrl+O` to save
- Press `Enter` to confirm
- Press `Ctrl+X` to exit

### Step 5: Test and reload
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Test your app
Open `https://nyra-team.com` in your browser - you should see your app!

## What it should look like after uncommenting:

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
        # Increase buffer sizes to handle large Supabase auth headers
        # Supabase sets many cookies during OAuth, requiring much larger buffers
        proxy_buffer_size 64k;
        proxy_buffers 32 64k;
        proxy_busy_buffers_size 128k;
        # Note: large_client_header_buffers must be in http block, not here
    }
```

## Troubleshooting

If you get an error after uncommenting:
1. Check the syntax: `sudo nginx -t`
2. Make sure you didn't accidentally remove a closing `}`
3. Make sure the `location /api/v1` block comes BEFORE the `location /` block

