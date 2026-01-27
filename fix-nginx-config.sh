#!/bin/bash
# Fix the /api/v1 location block placement and indentation

NGINX_CONFIG="/etc/nginx/sites-available/nyra-team.com"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Fixing nginx config..."

# Backup
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ Backed up to $BACKUP_FILE"

# Remove the incorrectly placed /api/v1 block (lines 113-128)
sudo sed -i '/^# Backend API proxy - must come before default location$/,/^}$/d' "$NGINX_CONFIG"

# Add it in the correct place (before "Default location - frontend app") with proper indentation
sudo sed -i '/^    # Default location - frontend app$/i\
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
    }\
' "$NGINX_CONFIG"

echo "✅ Fixed /api/v1 block placement and indentation"

# Test configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null
    echo ""
    echo "✅ Done! Your app should now work correctly."
    echo ""
    echo "Test it:"
    echo "  - Frontend: https://nyra-team.com"
    echo "  - Backend API: curl -k https://nyra-team.com/api/v1/health"
else
    echo "❌ Nginx configuration test failed"
    echo "   Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

