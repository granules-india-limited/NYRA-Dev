#!/bin/bash
# Add backend API proxy to existing nginx config

NGINX_CONFIG="/etc/nginx/sites-available/nyra-team.com"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Adding backend API proxy to nginx config..."

# Backup existing config
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ Backed up config to $BACKUP_FILE"

# Check if proxy already exists
if sudo grep -q "location /api/v1" "$NGINX_CONFIG"; then
    echo "⚠️  Backend proxy already exists in config"
    exit 0
fi

# Find the line with "location / {" in the HTTPS server block for www.nyra-team.com
# and add the backend proxy BEFORE it
sudo sed -i '/server_name www.nyra-team.com nyra-team.com;/,/location \/ {/ {
    /location \/ {/i\
    # Backend API proxy - must come before default location\
    location /api/v1 {\
        proxy_pass http://127.0.0.1:8000/v1;\
        proxy_redirect off;\
        proxy_http_version 1.1;\
        proxy_set_header Upgrade $http_upgrade;\
        proxy_set_header Connection '\''upgrade'\'';\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        proxy_set_header Authorization $http_authorization;\
        proxy_cache_bypass $http_upgrade;\
        proxy_connect_timeout 600s;\
        proxy_send_timeout 600s;\
        proxy_read_timeout 600s;\
    }
}' "$NGINX_CONFIG"

echo "✅ Added backend API proxy to nginx config"

# Test configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null
    echo "✅ Done!"
else
    echo "❌ Nginx configuration test failed"
    echo "   Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

