#!/bin/bash
# Install nginx configuration for www.nyra-team.com

set -e

CONFIG_FILE="/home/nyra/Documents/test/nginx-www.nyra-team.com.conf"
TARGET_DIR="/etc/nginx/conf.d"
TARGET_FILE="$TARGET_DIR/www.nyra-team.com.conf"

echo "🔧 Installing nginx configuration..."

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Config file not found: $CONFIG_FILE"
    exit 1
fi

# Copy config file
echo "📋 Copying config to $TARGET_FILE..."
sudo cp "$CONFIG_FILE" "$TARGET_FILE"

# Test nginx configuration
echo "🧪 Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
else
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Reload nginx
echo "🔄 Reloading nginx..."
if sudo systemctl reload nginx 2>/dev/null || sudo nginx -s reload 2>/dev/null; then
    echo "✅ Nginx reloaded successfully"
else
    echo "⚠️  Could not reload nginx automatically"
    echo "   Please run: sudo systemctl reload nginx"
fi

echo ""
echo "✅ Nginx configuration installed!"
echo ""
echo "The backend API is now accessible at:"
echo "  https://www.nyra-team.com/api/v1/*"
echo ""
echo "Test it:"
echo "  curl -k https://www.nyra-team.com/api/v1/health"

