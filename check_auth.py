#!/usr/bin/env python3
"""
Diagnostic script to check authentication configuration
"""
import os
import sys
from pathlib import Path

def check_env_file(filepath, required_vars):
    """Check if environment file exists and has required variables."""
    if not Path(filepath).exists():
        print(f"❌ {filepath} NOT FOUND")
        return False
    
    print(f"✅ {filepath} exists")
    
    with open(filepath) as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content or f"{var}=" not in content:
            missing.append(var)
        else:
            # Extract value
            for line in content.split('\n'):
                if line.startswith(var + '=') and not line.strip().startswith('#'):
                    value = line.split('=', 1)[1].strip().strip('"').strip("'")
                    if value:
                        print(f"  ✅ {var}: {value[:50]}...")
                    else:
                        print(f"  ⚠️  {var}: EMPTY")
                    break
    
    if missing:
        print(f"  ❌ Missing: {', '.join(missing)}")
        return False
    
    return True

def main():
    print("=" * 70)
    print("Authentication Configuration Check")
    print("=" * 70)
    print()
    
    # Check backend
    print("Backend Configuration:")
    backend_ok = check_env_file(
        "backend/.env",
        ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET"]
    )
    print()
    
    # Check frontend
    print("Frontend Configuration:")
    frontend_ok = check_env_file(
        "apps/frontend/.env.local",
        ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]
    )
    print()
    
    # Verify URLs match
    print("URL Verification:")
    try:
        with open("backend/.env") as f:
            backend_content = f.read()
        with open("apps/frontend/.env.local") as f:
            frontend_content = f.read()
        
        backend_url = None
        frontend_url = None
        
        for line in backend_content.split('\n'):
            if line.startswith("SUPABASE_URL=") and not line.strip().startswith('#'):
                backend_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                break
        
        for line in frontend_content.split('\n'):
            if line.startswith("NEXT_PUBLIC_SUPABASE_URL=") and not line.strip().startswith('#'):
                frontend_url = line.split('=', 1)[1].strip().strip('"').strip("'")
                break
        
        if backend_url and frontend_url:
            if backend_url == frontend_url:
                print(f"  ✅ URLs match: {backend_url}")
            else:
                print(f"  ❌ URLs DON'T MATCH!")
                print(f"     Backend:  {backend_url}")
                print(f"     Frontend: {frontend_url}")
        else:
            print("  ⚠️  Could not extract URLs for comparison")
    except Exception as e:
        print(f"  ⚠️  Error checking URLs: {e}")
    
    print()
    print("=" * 70)
    
    if backend_ok and frontend_ok:
        print("✅ Configuration files look good!")
        print()
        print("Next steps:")
        print("  1. Make sure you're signed in to the frontend")
        print("  2. Go to http://localhost:3000/auth and sign in")
        print("  3. Check browser console for authentication errors")
        print("  4. Verify JWT secret in Supabase Dashboard matches backend/.env")
    else:
        print("❌ Configuration issues found!")
        print()
        print("Fix:")
        print("  1. Run: python3 setup.py")
        print("  2. Or manually check the missing environment variables")
    
    print()

if __name__ == "__main__":
    main()

