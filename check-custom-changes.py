#!/usr/bin/env python3
"""
Conflict Detection Script for NYRA-Dev Upstream Sync

This script helps identify potential conflicts before syncing with upstream.
It scans for files with NYRA customizations and compares them with upstream.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Set

# Files that should always preserve NYRA customizations
CRITICAL_FILES = {
    "backend/core/prompts/core_prompt.py",
    "backend/core/config/suna_config.py",
    "backend/core/services/transcription.py",
    "backend/core/billing/endpoints/account_state.py",
    "backend/core/billing/credits/integration.py",
    "backend/core/billing/subscriptions/handlers/tier.py",
    "backend/core/sandbox/tool_base.py",
    "backend/core/tools/web_search_tool.py",
    "backend/core/tools/image_search_tool.py",
    "backend/core/jit/mcp_tool_wrapper.py",
    "backend/core/tools/utils/mcp_tool_executor.py",
    "apps/frontend/src/components/home/dashboard-promo-banner.tsx",
}

# Keywords that indicate NYRA customizations
NYRA_KEYWORDS = [
    "NYRA",
    "nyra-team.com",
    "DISABLE_BILLING",
    "tier_25_200",
    "nyra-logomark-white.gif",
    "api.nyra-team.com",
]

# Keywords that indicate upstream (Kortix) content
UPSTREAM_KEYWORDS = [
    "Kortix",
    "kortix.com",
    "kortix-ai",
    "nyra-logomark-white.svg",
    "api.openai.com/v1/audio/transcriptions",
]


def run_command(cmd: List[str]) -> str:
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return ""


def check_git_repo() -> bool:
    """Check if we're in a git repository."""
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_upstream_remote() -> bool:
    """Check if upstream remote exists."""
    remotes = run_command(["git", "remote"])
    return "upstream" in remotes.split("\n")


def get_modified_files() -> Set[str]:
    """Get list of files that differ from upstream."""
    if not check_upstream_remote():
        print("⚠️  Upstream remote not found. Run: git remote add upstream https://github.com/kortix-ai/suna.git")
        return set()
    
    # Fetch upstream first
    print("📥 Fetching upstream...")
    run_command(["git", "fetch", "upstream"])
    
    # Get files that differ
    diff_output = run_command([
        "git", "diff", "--name-only", "upstream/main"
    ])
    
    if not diff_output:
        return set()
    
    return set(diff_output.split("\n"))


def check_file_for_keywords(filepath: str) -> Dict[str, List[str]]:
    """Check a file for NYRA and upstream keywords."""
    if not os.path.exists(filepath):
        return {"nyra": [], "upstream": []}
    
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  Could not read {filepath}: {e}")
        return {"nyra": [], "upstream": []}
    
    nyra_matches = []
    upstream_matches = []
    
    for keyword in NYRA_KEYWORDS:
        if keyword in content:
            nyra_matches.append(keyword)
    
    for keyword in UPSTREAM_KEYWORDS:
        if keyword in content:
            upstream_matches.append(keyword)
    
    return {"nyra": nyra_matches, "upstream": upstream_matches}


def analyze_conflicts():
    """Main analysis function."""
    print("🔍 NYRA-Dev Conflict Detection\n")
    print("=" * 60)
    
    # Check prerequisites
    if not check_git_repo():
        print("❌ Error: Not in a git repository")
        sys.exit(1)
    
    if not check_upstream_remote():
        print("⚠️  Upstream remote not found.")
        print("   Run: git remote add upstream https://github.com/kortix-ai/suna.git")
        sys.exit(1)
    
    # Get modified files
    print("\n📋 Analyzing files with NYRA customizations...\n")
    modified_files = get_modified_files()
    
    if not modified_files:
        print("✅ No differences found with upstream (or upstream not fetched)")
        return
    
    print(f"Found {len(modified_files)} file(s) that differ from upstream\n")
    
    # Analyze critical files
    critical_conflicts = []
    potential_conflicts = []
    safe_files = []
    
    for filepath in modified_files:
        if not filepath.strip():
            continue
        
        is_critical = filepath in CRITICAL_FILES
        keywords = check_file_for_keywords(filepath)
        
        has_nyra = len(keywords["nyra"]) > 0
        has_upstream = len(keywords["upstream"]) > 0
        
        file_info = {
            "path": filepath,
            "is_critical": is_critical,
            "nyra_keywords": keywords["nyra"],
            "upstream_keywords": keywords["upstream"],
        }
        
        if is_critical:
            critical_conflicts.append(file_info)
        elif has_nyra or has_upstream:
            potential_conflicts.append(file_info)
        else:
            safe_files.append(file_info)
    
    # Print results
    print("=" * 60)
    print("🚨 CRITICAL FILES (Always preserve NYRA customizations)")
    print("=" * 60)
    
    if critical_conflicts:
        for info in critical_conflicts:
            print(f"\n📄 {info['path']}")
            if info["nyra_keywords"]:
                print(f"   NYRA keywords: {', '.join(info['nyra_keywords'])}")
            if info["upstream_keywords"]:
                print(f"   ⚠️  Upstream keywords found: {', '.join(info['upstream_keywords'])}")
                print(f"   ⚠️  CONFLICT LIKELY - Manual resolution required")
    else:
        print("   None found")
    
    print("\n" + "=" * 60)
    print("⚠️  POTENTIAL CONFLICTS (Review carefully)")
    print("=" * 60)
    
    if potential_conflicts:
        for info in potential_conflicts[:20]:  # Limit output
            print(f"\n📄 {info['path']}")
            if info["nyra_keywords"]:
                print(f"   NYRA keywords: {', '.join(info['nyra_keywords'])}")
            if info["upstream_keywords"]:
                print(f"   Upstream keywords: {', '.join(info['upstream_keywords'])}")
    else:
        print("   None found")
    
    if len(potential_conflicts) > 20:
        print(f"\n   ... and {len(potential_conflicts) - 20} more files")
    
    print("\n" + "=" * 60)
    print("✅ SAFE FILES (Can likely accept upstream changes)")
    print("=" * 60)
    print(f"   {len(safe_files)} file(s) - Review during merge")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"Total files analyzed: {len(modified_files)}")
    print(f"Critical files: {len(critical_conflicts)}")
    print(f"Potential conflicts: {len(potential_conflicts)}")
    print(f"Safe files: {len(safe_files)}")
    
    if critical_conflicts:
        print("\n⚠️  WARNING: Critical files with potential conflicts detected!")
        print("   Review these files carefully during merge.")
        print("   Always preserve NYRA customizations in critical files.")
    
    print("\n💡 Next steps:")
    print("   1. Review critical files before syncing")
    print("   2. Use sync-upstream.sh for guided merge")
    print("   3. Refer to UPSTREAM_SYNC_PLAN.md for conflict resolution")


if __name__ == "__main__":
    try:
        analyze_conflicts()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
