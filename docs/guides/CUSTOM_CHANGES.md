# NYRA Customizations Tracker

This document tracks all customizations made to the NYRA-Dev fork that differ from the upstream `kortix-ai/suna` repository.

**Last Sync Date**: Not yet synced  
**Last Updated**: 2026-01-27

## Customization Categories

### 1. Branding & Identity

#### System Prompts
- **File**: `backend/core/prompts/core_prompt.py`
- **Change**: Changed "Kortix" to "NYRA" throughout system prompts
- **Lines**: Multiple (entire file customized)
- **Reason**: Brand identity
- **Preserve**: Always

#### Agent Configuration
- **File**: `backend/core/config/suna_config.py`
- **Change**: Agent name set to "NYRA"
- **Reason**: Brand identity
- **Preserve**: Always

#### Logo Files
- **Files**: Multiple logo files in `apps/frontend/public/`
- **Change**: Using `nyra-logomark-white.gif` instead of SVG versions
- **Files Changed**:
  - `apps/frontend/src/components/thread/chat-input/unified-config-menu.tsx`
  - `apps/frontend/src/components/home/example-showcase.tsx`
  - `apps/frontend/src/components/thread/ThreadContent.tsx`
- **Reason**: Brand identity
- **Preserve**: Always

### 2. API Endpoints

#### Transcription Service
- **File**: `backend/core/services/transcription.py`
- **Change**: Switched from OpenAI Whisper to custom endpoint `https://api.nyra-team.com/v1/transcription`
- **Implementation**: Uses `httpx` for HTTP requests instead of OpenAI SDK
- **Reason**: Custom transcription service
- **Preserve**: Always

### 3. Billing & Feature Access

#### Billing Disable Logic
- **Files**: Multiple backend and frontend files
- **Change**: Added `DISABLE_BILLING` checks throughout codebase to unlock all features when billing is disabled
- **Key Files**:
  - `backend/core/billing/endpoints/account_state.py` - Unlimited limits when billing disabled
  - `backend/core/billing/credits/integration.py` - Bypass credit checks
  - `backend/core/billing/subscriptions/handlers/tier.py` - All models available
  - `apps/frontend/src/components/billing/**` - UI components
  - `apps/frontend/src/components/dashboard/dashboard-content.tsx` - Dashboard access
  - `apps/frontend/src/components/sidebar/nav-user-with-teams.tsx` - Plan display
  - `apps/frontend/src/components/agents/composio/composio-connections-section.tsx` - App connections
  - `apps/frontend/src/components/thread/chat-input/unified-config-menu.tsx` - Model access
  - `apps/frontend/src/components/agents/config/model-selector.tsx` - Model selector
- **Reason**: Development/testing without billing restrictions
- **Preserve**: Always

#### Plan Display
- **File**: `apps/frontend/src/components/billing/plan-utils.ts`
- **Change**: Returns "Ultra" plan when billing is disabled
- **Reason**: Consistent UI experience
- **Preserve**: Always

### 4. Agent Configuration

#### Default Agent Editing
- **Files**: 
  - `apps/frontend/src/app/(dashboard)/agents/config/[agentId]/screens/instructions-screen.tsx`
  - `apps/frontend/src/app/(dashboard)/agents/config/[agentId]/screens/tools-screen.tsx`
  - `apps/frontend/src/components/agents/agent-configuration-dialog.tsx`
- **Change**: Removed `!isSunaAgent` restrictions, allowing editing of default "NYRA" agent
- **Reason**: Need to customize default agent behavior
- **Preserve**: Always

### 5. Environment Configuration

#### API Keys
- **File**: `backend/.env` (not committed, but documented)
- **Custom Keys**:
  - `COMPOSIO_API_KEY` - Custom Composio integration
  - `COMPOSIO_WEBHOOK_SECRET` - Composio webhook
  - `TAVILY_API_KEY` - Custom Tavily API key
  - `TRANSCRIPTION_API_URL` - Custom transcription endpoint
- **Reason**: Custom service integrations
- **Preserve**: Always (via .env, not in code)

### 6. Workspace Path Detection

#### Sandbox Workspace
- **File**: `backend/core/sandbox/tool_base.py`
- **Change**: Added dynamic workspace path detection for Daytona sandbox
- **Implementation**: Detects workspace from common locations (`/workspace`, `/home/user/project`, etc.)
- **Reason**: Compatibility with Daytona sandbox environment
- **Preserve**: Always

### 7. Search Result Limits

#### Web Search
- **File**: `backend/core/tools/web_search_tool.py`
- **Change**: Default `num_results` changed from 5 to 3
- **Reason**: Cost optimization
- **Preserve**: Always

#### Image Search
- **File**: `backend/core/tools/image_search_tool.py`
- **Change**: Default `num_results` changed from 12 to 8
- **Reason**: Cost optimization
- **Preserve**: Always

### 8. System Prompt Enhancements

#### Anti-Hallucination Rules
- **File**: `backend/core/prompts/core_prompt.py`
- **Change**: Extensive additions for preventing email tool hallucination
- **Sections Added**:
  - Critical tool result usage rules
  - Email/Gmail tool anti-hallucination rules
  - Detailed examples of correct/forbidden behavior
- **Reason**: Improve tool usage accuracy
- **Preserve**: Always

#### MCP Tool Result Extraction
- **Files**:
  - `backend/core/jit/mcp_tool_wrapper.py`
  - `backend/core/tools/utils/mcp_tool_executor.py`
- **Change**: Enhanced result extraction to properly parse Composio JSON responses and extract `data` field
- **Reason**: Fix MCP tool result display issues
- **Preserve**: Always

### 9. Promo Banner Removal

#### Dashboard Promo
- **File**: `apps/frontend/src/components/home/dashboard-promo-banner.tsx`
- **Change**: Component simplified to return `null`, removing all promo banners
- **Reason**: Clean UI without billing promotions
- **Preserve**: Always

## Files to Always Preserve During Sync

When merging upstream changes, always preserve these files' NYRA customizations:

1. `backend/core/prompts/core_prompt.py` - System prompts
2. `backend/core/config/suna_config.py` - Agent config
3. `backend/core/services/transcription.py` - Transcription endpoint
4. `backend/core/billing/**` - Billing disable logic
5. `backend/core/sandbox/tool_base.py` - Workspace detection
6. `backend/core/tools/web_search_tool.py` - Search limits
7. `backend/core/tools/image_search_tool.py` - Image search limits
8. `backend/core/jit/mcp_tool_wrapper.py` - MCP result extraction
9. `backend/core/tools/utils/mcp_tool_executor.py` - MCP execution
10. `apps/frontend/src/components/**` - All frontend components with NYRA branding
11. `apps/frontend/src/app/**` - All frontend pages with NYRA branding
12. Logo files in `apps/frontend/public/`

## Files That Can Accept Upstream Changes

These files can generally accept upstream changes unless they conflict with NYRA customizations:

1. Dependencies (`package.json`, `pyproject.toml`) - Review for conflicts
2. Build configurations - Review for conflicts
3. Documentation (unless it mentions branding)
4. Test files
5. Utility scripts (unless they reference branding)

## Conflict Resolution Notes

### Common Conflict Patterns

1. **Branding Conflicts**: Always choose "NYRA" over "Kortix"
2. **API Endpoint Conflicts**: Always keep `api.nyra-team.com` endpoints
3. **Billing Logic Conflicts**: Always preserve `DISABLE_BILLING` checks
4. **Logo References**: Always use GIF version over SVG

### Merge Strategy

- **Theirs (Upstream)**: Bug fixes, security patches, new features (if compatible)
- **Ours (NYRA)**: Branding, API endpoints, billing logic, custom prompts

## Testing Checklist After Sync

After each sync, verify:

- [ ] Application starts without errors
- [ ] NYRA branding appears correctly
- [ ] Transcription service works (custom endpoint)
- [ ] Billing disable logic works (all features unlocked)
- [ ] Default agent can be edited
- [ ] MCP tools return correct results
- [ ] Search tools use correct result limits
- [ ] Workspace path detection works
- [ ] No promo banners appear
- [ ] All custom API keys work

## Notes

- This document should be updated after each sync
- Add new customizations as they are made
- Document any conflicts encountered during sync
- Note any upstream changes that were particularly difficult to merge
