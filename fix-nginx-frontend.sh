#!/bin/bash
# Uncomment the frontend proxy location block in nginx config

NGINX_CONFIG="/etc/nginx/sites-available/nyra-team.com"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Fixing nginx frontend proxy..."

# Backup
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ Backed up to $BACKUP_FILE"

# Uncomment the frontend location block
sudo sed -i '/# Default location - frontend app/,/#}/ {
    s/^#\([[:space:]]*location \/ {\)/\1/
    s/^#\([[:space:]]*proxy_pass http:\/\/127\.0\.0\.1:3000;\)/\1/
    s/^#\([[:space:]]*proxy_http_version 1\.1;\)/\1/
    s/^#\([[:space:]]*proxy_set_header Upgrade \$http_upgrade;\)/\1/
    s/^#\([[:space:]]*proxy_set_header Connection '\''upgrade'\'';\)/\1/
    s/^#\([[:space:]]*proxy_set_header Host \$host;\)/\1/
    s/^#\([[:space:]]*proxy_set_header X-Real-IP \$remote_addr;\)/\1/
    s/^#\([[:space:]]*proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\)/\1/
    s/^#\([[:space:]]*proxy_set_header X-Forwarded-Proto \$scheme;\)/\1/
    s/^#\([[:space:]]*proxy_cache_bypass \$http_upgrade;\)/\1/
    s/^#\([[:space:]]*proxy_connect_timeout 600s;\)/\1/
    s/^#\([[:space:]]*proxy_send_timeout 600s;\)/\1/
    s/^#\([[:space:]]*proxy_read_timeout 600s;\)/\1/
    s/^#\(}\)/\1/
}' "$NGINX_CONFIG"

echo "✅ Uncommented frontend proxy location block"

# Test configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null
    echo "✅ Done! Your app should be accessible now."
else
    echo "❌ Nginx configuration test failed"
    echo "   Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

