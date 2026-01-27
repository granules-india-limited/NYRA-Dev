#!/bin/bash
# Update frontend .env.local to use proxied backend URL when on HTTPS

ENV_FILE="apps/frontend/.env.local"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found"
    exit 1
fi

# Backup
cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"

# Update NEXT_PUBLIC_BACKEND_URL to use proxied path
# When frontend is on HTTPS, it will use /api/v1 which nginx proxies to backend
sed -i 's|NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=/api/v1|' "$ENV_FILE"

echo "✅ Updated NEXT_PUBLIC_BACKEND_URL to use nginx proxy"
echo ""
echo "Current value:"
grep "NEXT_PUBLIC_BACKEND_URL" "$ENV_FILE"
