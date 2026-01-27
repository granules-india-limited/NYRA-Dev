#!/bin/bash
# Setup script for HTTPS local development with nginx

set -e

echo "🔒 Setting up HTTPS for local development..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Install mkcert CA (requires sudo)
echo -e "${YELLOW}Step 1: Installing mkcert CA...${NC}"
if [ -f "/tmp/mkcert" ]; then
    sudo /tmp/mkcert -install
    echo -e "${GREEN}✓ CA installed${NC}"
else
    echo -e "${RED}✗ mkcert not found in /tmp. Please download it first.${NC}"
    exit 1
fi

# 2. Copy nginx config
echo -e "${YELLOW}Step 2: Installing nginx configuration...${NC}"
if [ -f "/home/nyra/Documents/test/nginx-www.nyra-team.com.conf" ]; then
    sudo cp /home/nyra/Documents/test/nginx-www.nyra-team.com.conf /etc/nginx/conf.d/www.nyra-team.com.conf
    echo -e "${GREEN}✓ Nginx config installed${NC}"
else
    echo -e "${RED}✗ Nginx config not found${NC}"
    exit 1
fi

# 3. Update /etc/hosts
echo -e "${YELLOW}Step 3: Updating /etc/hosts...${NC}"
if ! grep -q "www.nyra-team.com" /etc/hosts; then
    echo "127.0.0.1    www.nyra-team.com" | sudo tee -a /etc/hosts
    echo -e "${GREEN}✓ /etc/hosts updated${NC}"
else
    echo -e "${YELLOW}⚠ www.nyra-team.com already in /etc/hosts${NC}"
fi

# 4. Test nginx configuration
echo -e "${YELLOW}Step 4: Testing nginx configuration...${NC}"
if sudo nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration test failed${NC}"
    exit 1
fi

# 5. Reload nginx
echo -e "${YELLOW}Step 5: Reloading nginx...${NC}"
if sudo systemctl reload nginx || sudo nginx -s reload; then
    echo -e "${GREEN}✓ Nginx reloaded${NC}"
else
    echo -e "${YELLOW}⚠ Could not reload nginx automatically. Please run: sudo systemctl reload nginx${NC}"
fi

echo ""
echo -e "${GREEN}✅ HTTPS setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update apps/frontend/.env.local:"
echo "   NEXT_PUBLIC_URL=https://www.nyra-team.com"
echo "   NEXT_PUBLIC_APP_URL=https://www.nyra-team.com"
echo ""
echo "2. Restart your frontend dev server"
echo ""
echo "3. Access your app at: https://www.nyra-team.com"
echo "   (The browser will trust the certificate because mkcert CA is installed)"

