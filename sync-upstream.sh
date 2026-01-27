#!/bin/bash

# Upstream Sync Script for NYRA-Dev
# This script helps sync with kortix-ai/suna upstream repository

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
UPSTREAM_REPO="https://github.com/kortix-ai/suna.git"
UPSTREAM_BRANCH="main"
LOCAL_BRANCH="main"
SYNC_DATE=$(date +%Y%m%d)
SYNC_BRANCH="sync-upstream-$SYNC_DATE"

echo -e "${BLUE}=== NYRA-Dev Upstream Sync Script ===${NC}\n"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    exit 1
fi

# Check if upstream remote exists
if ! git remote | grep -q "^upstream$"; then
    echo -e "${YELLOW}Upstream remote not found. Adding it...${NC}"
    git remote add upstream "$UPSTREAM_REPO"
    echo -e "${GREEN}✓ Upstream remote added${NC}\n"
fi

# Ensure we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "$LOCAL_BRANCH" ]; then
    echo -e "${YELLOW}Switching to $LOCAL_BRANCH branch...${NC}"
    git checkout "$LOCAL_BRANCH"
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: You have uncommitted changes. Please commit or stash them first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Working directory is clean${NC}\n"

# Fetch upstream
echo -e "${BLUE}Fetching latest changes from upstream...${NC}"
git fetch upstream

# Check what's new
UPSTREAM_COMMITS=$(git log $LOCAL_BRANCH..upstream/$UPSTREAM_BRANCH --oneline | wc -l)

if [ "$UPSTREAM_COMMITS" -eq 0 ]; then
    echo -e "${GREEN}✓ Already up to date with upstream${NC}"
    exit 0
fi

echo -e "${YELLOW}Found $UPSTREAM_COMMITS new commit(s) from upstream${NC}"
echo -e "${BLUE}Recent upstream commits:${NC}"
git log $LOCAL_BRANCH..upstream/$UPSTREAM_BRANCH --oneline | head -10
echo ""

# Ask for confirmation
read -p "Do you want to proceed with sync? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Sync cancelled${NC}"
    exit 0
fi

# Create sync branch
echo -e "${BLUE}Creating sync branch: $SYNC_BRANCH${NC}"
git checkout -b "$SYNC_BRANCH"
echo -e "${GREEN}✓ Sync branch created${NC}\n"

# Attempt merge
echo -e "${BLUE}Merging upstream/$UPSTREAM_BRANCH into $SYNC_BRANCH...${NC}"
if git merge upstream/$UPSTREAM_BRANCH --no-edit; then
    echo -e "${GREEN}✓ Merge completed successfully (no conflicts)${NC}\n"
    CONFLICTS=0
else
    echo -e "${YELLOW}⚠ Merge conflicts detected${NC}\n"
    CONFLICTS=1
    
    # Show conflicted files
    CONFLICTED_FILES=$(git diff --name-only --diff-filter=U)
    echo -e "${YELLOW}Conflicted files:${NC}"
    echo "$CONFLICTED_FILES"
    echo ""
    
    echo -e "${YELLOW}Please resolve conflicts manually.${NC}"
    echo -e "${BLUE}After resolving:${NC}"
    echo "  1. Review each conflicted file"
    echo "  2. Preserve NYRA customizations (see UPSTREAM_SYNC_PLAN.md)"
    echo "  3. Run: git add <resolved-files>"
    echo "  4. Run: git commit -m 'Resolve conflicts: preserve NYRA customizations'"
    echo "  5. Then run this script again or continue manually"
    echo ""
    echo -e "${BLUE}Current branch: $SYNC_BRANCH${NC}"
    exit 1
fi

# If no conflicts, ask about testing
if [ "$CONFLICTS" -eq 0 ]; then
    echo -e "${GREEN}=== Merge Successful ===${NC}\n"
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Test the application thoroughly"
    echo "  2. Verify all NYRA customizations still work"
    echo "  3. If everything is good, merge to main:"
    echo "     git checkout main"
    echo "     git merge $SYNC_BRANCH --no-ff"
    echo "     git push origin main"
    echo ""
    echo -e "${BLUE}Or run: ./sync-upstream.sh --complete${NC}"
fi
