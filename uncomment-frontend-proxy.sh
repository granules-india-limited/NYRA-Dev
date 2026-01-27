#!/bin/bash
# Uncomment the frontend proxy location block

NGINX_CONFIG="/etc/nginx/sites-available/nyra-team.com"
BACKUP_FILE="${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

echo "🔧 Uncommenting frontend proxy in nginx config..."

# Backup
sudo cp "$NGINX_CONFIG" "$BACKUP_FILE"
echo "✅ Backed up to $BACKUP_FILE"

# Uncomment lines from "# Default location" to the closing "#}"
# This removes # from lines that start with # followed by whitespace and a directive
sudo sed -i '/# Default location - frontend app/,/#}/ {
    s/^#\([[:space:]]*location \/ {\)/\1/
    s/^#\([[:space:]]*proxy_pass\)/\1/
    s/^#\([[:space:]]*proxy_http_version\)/\1/
    s/^#\([[:space:]]*proxy_set_header\)/\1/
    s/^#\([[:space:]]*proxy_cache_bypass\)/\1/
    s/^#\([[:space:]]*proxy_connect_timeout\)/\1/
    s/^#\([[:space:]]*proxy_send_timeout\)/\1/
    s/^#\([[:space:]]*proxy_read_timeout\)/\1/
    s/^#\([[:space:]]*proxy_buffering\)/\1/
    s/^#\([[:space:]]*client_max_body_size\)/\1/
    s/^#\(}\)/\1/
}' "$NGINX_CONFIG"

echo "✅ Uncommented frontend proxy block"

# Test configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    echo "🔄 Reloading nginx..."
    sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null
    echo ""
    echo "✅ Done! Your app should now be accessible at https://nyra-team.com"
else
    echo "❌ Nginx configuration test failed"
    echo "   Restoring backup..."
    sudo cp "$BACKUP_FILE" "$NGINX_CONFIG"
    exit 1
fi

