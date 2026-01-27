#!/bin/bash
# Update frontend .env.local to use HTTPS

ENV_FILE="apps/frontend/.env.local"
ENV_DIR="apps/frontend"

# Ensure directory exists
mkdir -p "$ENV_DIR"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE..."
    touch "$ENV_FILE"
fi

# Backup existing file
if [ -s "$ENV_FILE" ]; then
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "Backed up existing .env.local"
fi

# Update or add NEXT_PUBLIC_URL
if grep -q "NEXT_PUBLIC_URL=" "$ENV_FILE"; then
    sed -i 's|NEXT_PUBLIC_URL=.*|NEXT_PUBLIC_URL=https://www.nyra-team.com|' "$ENV_FILE"
    echo "Updated NEXT_PUBLIC_URL"
else
    echo "NEXT_PUBLIC_URL=https://www.nyra-team.com" >> "$ENV_FILE"
    echo "Added NEXT_PUBLIC_URL"
fi

# Update or add NEXT_PUBLIC_APP_URL
if grep -q "NEXT_PUBLIC_APP_URL=" "$ENV_FILE"; then
    sed -i 's|NEXT_PUBLIC_APP_URL=.*|NEXT_PUBLIC_APP_URL=https://www.nyra-team.com|' "$ENV_FILE"
    echo "Updated NEXT_PUBLIC_APP_URL"
else
    echo "NEXT_PUBLIC_APP_URL=https://www.nyra-team.com" >> "$ENV_FILE"
    echo "Added NEXT_PUBLIC_APP_URL"
fi

echo ""
echo "✅ Frontend environment updated!"
echo ""
echo "Current configuration:"
grep -E "NEXT_PUBLIC_URL|NEXT_PUBLIC_APP_URL" "$ENV_FILE" || echo "No matching variables found"
echo ""
echo "⚠️  Make sure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY are set!"
echo "⚠️  Restart your frontend dev server after this change!"

