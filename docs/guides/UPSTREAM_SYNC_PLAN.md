# Upstream/Downstream Sync Plan

## Overview

This document outlines the strategy for keeping the **NYRA-Dev** repository synchronized with the upstream **kortix-ai/suna** repository while preserving all NYRA customizations.

## Repository Structure

- **Upstream**: `https://github.com/kortix-ai/suna` (original repository)
- **Downstream**: `https://github.com/nyra-team/NYRA-Dev` (your fork with customizations)
- **Sync Frequency**: Monthly or as needed when upstream releases important updates

## Customizations to Preserve

### 1. Branding Changes
- **Files**: Multiple frontend components, config files
- **Changes**: "NYRA" instead of "Kortix", custom logos
- **Key Files**:
  - `backend/core/prompts/core_prompt.py` - System prompt mentions "NYRA"
  - `backend/core/config/suna_config.py` - Agent name "NYRA"
  - `apps/frontend/src/components/**` - UI components with NYRA branding
  - Logo files: `nyra-logomark-white.gif` instead of SVG

### 2. API Endpoints
- **File**: `backend/core/services/transcription.py`
- **Change**: Custom transcription endpoint `api.nyra-team.com/v1/transcription`
- **Action**: Always preserve this custom endpoint

### 3. Billing Logic
- **Files**: Multiple frontend and backend files
- **Change**: `DISABLE_BILLING=true` logic throughout the codebase
- **Key Files**:
  - `backend/core/billing/endpoints/account_state.py`
  - `backend/core/billing/credits/integration.py`
  - `backend/core/billing/subscriptions/handlers/tier.py`
  - `apps/frontend/src/components/billing/**`
  - `apps/frontend/src/components/dashboard/dashboard-content.tsx`
  - `apps/frontend/src/components/sidebar/nav-user-with-teams.tsx`

### 4. Agent Configuration
- **Files**: Agent config screens and dialogs
- **Change**: Removed restrictions on editing default "NYRA" agent
- **Key Files**:
  - `apps/frontend/src/app/(dashboard)/agents/config/[agentId]/screens/instructions-screen.tsx`
  - `apps/frontend/src/app/(dashboard)/agents/config/[agentId]/screens/tools-screen.tsx`
  - `apps/frontend/src/components/agents/agent-configuration-dialog.tsx`

### 5. Environment Variables
- **File**: `backend/.env`
- **Change**: Custom API keys (Composio, Tavily, etc.)
- **Action**: Never commit `.env` file, but document required variables

### 6. Workspace Path Detection
- **File**: `backend/core/sandbox/tool_base.py`
- **Change**: Dynamic workspace path detection for Daytona
- **Action**: Preserve custom detection logic

### 7. Search Result Limits
- **Files**: 
  - `backend/core/tools/web_search_tool.py` - Default 3 results
  - `backend/core/tools/image_search_tool.py` - Default 8 results
- **Action**: Preserve custom limits

### 8. System Prompts
- **File**: `backend/core/prompts/core_prompt.py`
- **Change**: Extensive customizations including anti-hallucination rules
- **Action**: Always preserve custom prompt logic

## Sync Workflow

### Initial Setup (One-Time)

```bash
# Add upstream remote
git remote add upstream https://github.com/kortix-ai/suna.git

# Verify remotes
git remote -v
```

### Regular Sync Process

#### Step 1: Prepare for Sync

```bash
# Ensure you're on main branch and it's clean
git checkout main
git status  # Should be clean

# Fetch latest from upstream
git fetch upstream

# Check what's new
git log main..upstream/main --oneline
```

#### Step 2: Create Sync Branch

```bash
# Create a new branch for this sync
SYNC_DATE=$(date +%Y%m%d)
git checkout -b sync-upstream-$SYNC_DATE
```

#### Step 3: Merge Upstream Changes

```bash
# Merge upstream/main into your sync branch
git merge upstream/main --no-edit

# If conflicts occur, resolve them (see Conflict Resolution below)
```

#### Step 4: Test Thoroughly

```bash
# Test the application
# - Start backend
# - Start frontend
# - Verify all customizations still work
# - Test critical features
```

#### Step 5: Commit and Merge

```bash
# If you made conflict resolutions, commit them
git add .
git commit -m "Resolve merge conflicts with upstream while preserving NYRA customizations"

# Switch back to main
git checkout main

# Merge the sync branch
git merge sync-upstream-$SYNC_DATE --no-ff

# Push to GitHub
git push origin main

# Optionally delete the sync branch
git branch -d sync-upstream-$SYNC_DATE
```

## Conflict Resolution Strategy

### Priority Rules

1. **Always Preserve** (NYRA customizations):
   - Branding (NYRA vs Kortix)
   - Custom API endpoints
   - Billing disable logic
   - Custom system prompts
   - Custom logo files
   - Agent configuration edits

2. **Accept Upstream** (unless they conflict):
   - Bug fixes
   - Security patches
   - New features (if they don't break customizations)
   - Performance improvements
   - Dependency updates

3. **Merge Carefully**:
   - UI changes (may affect branding)
   - Configuration files
   - Database migrations
   - API changes

### Conflict Resolution Process

When conflicts occur:

1. **Identify the conflict type**:
   ```bash
   git status  # Shows conflicted files
   ```

2. **For each conflicted file**:
   - Open the file
   - Look for conflict markers: `<<<<<<<`, `=======`, `>>>>>>>`
   - Decide: preserve NYRA changes or accept upstream
   - Edit to resolve

3. **Common conflict patterns**:

   **Pattern 1: Branding conflicts**
   ```
   <<<<<<< HEAD (NYRA)
   "NYRA"
   =======
   "Kortix"
   >>>>>>> upstream/main
   ```
   **Resolution**: Keep "NYRA"

   **Pattern 2: API endpoint conflicts**
   ```
   <<<<<<< HEAD (NYRA)
   transcription_url = "https://api.nyra-team.com/v1/transcription"
   =======
   transcription_url = "https://api.openai.com/v1/audio/transcriptions"
   >>>>>>> upstream/main
   ```
   **Resolution**: Keep NYRA endpoint

   **Pattern 3: Billing logic conflicts**
   ```
   <<<<<<< HEAD (NYRA)
   if config.DISABLE_BILLING:
       return all_features_unlocked
   =======
   if user.tier == "free":
       return limited_features
   >>>>>>> upstream/main
   ```
   **Resolution**: Keep NYRA billing disable logic

4. **After resolving all conflicts**:
   ```bash
   git add <resolved-files>
   git commit -m "Resolve conflicts: preserve NYRA customizations"
   ```

## Automated Sync Script

Use the provided `sync-upstream.sh` script for automated syncing:

```bash
./sync-upstream.sh
```

This script:
- Fetches upstream changes
- Creates a sync branch
- Attempts automatic merge
- Reports conflicts for manual resolution
- Guides you through the process

## Conflict Detection

Use the provided `check-custom-changes.py` script to detect potential conflicts:

```bash
python check-custom-changes.py
```

This script:
- Scans for files with NYRA customizations
- Compares with upstream
- Reports potential conflict areas
- Helps plan merge strategy

## Best Practices

1. **Sync Regularly**: Don't let too many changes accumulate
2. **Test Before Merging**: Always test after resolving conflicts
3. **Document Changes**: Update `CUSTOM_CHANGES.md` when adding new customizations
4. **Use Branches**: Never sync directly on main
5. **Review Changes**: Always review upstream changes before merging
6. **Backup First**: Consider creating a backup branch before syncing

## Emergency Rollback

If a sync breaks something:

```bash
# Find the commit before the merge
git log --oneline

# Reset to that commit
git reset --hard <commit-hash>

# Force push (use with caution!)
git push origin main --force
```

## Tracking Custom Changes

Maintain `CUSTOM_CHANGES.md` with:
- List of all custom files
- Description of changes
- Reason for customization
- Last sync date
- Notes about conflicts

## Sync Checklist

Before syncing:
- [ ] Backup current state
- [ ] Review upstream changelog/releases
- [ ] Check for breaking changes
- [ ] Ensure local main is clean

During sync:
- [ ] Create sync branch
- [ ] Merge upstream
- [ ] Resolve conflicts
- [ ] Test thoroughly
- [ ] Update documentation

After sync:
- [ ] Merge to main
- [ ] Push to GitHub
- [ ] Update CUSTOM_CHANGES.md
- [ ] Document any issues
- [ ] Notify team if needed

## Support

For questions or issues with syncing:
1. Check this document
2. Review `CUSTOM_CHANGES.md`
3. Use conflict detection scripts
4. Consult Git documentation
