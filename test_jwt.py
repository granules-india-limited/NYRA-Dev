#!/usr/bin/env python3
"""
Test script to verify JWT secret and token decoding
"""
import os
import sys
import jwt
from pathlib import Path

def get_jwt_secret():
    """Get JWT secret from backend .env"""
    backend_env = Path("backend/.env")
    if not backend_env.exists():
        print("❌ backend/.env not found")
        return None
    
    with open(backend_env) as f:
        for line in f:
            if line.startswith("SUPABASE_JWT_SECRET="):
                secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                return secret
    
    print("❌ SUPABASE_JWT_SECRET not found in backend/.env")
    return None

def test_jwt_decoding():
    """Test JWT decoding with the secret"""
    jwt_secret = get_jwt_secret()
    if not jwt_secret:
        return
    
    print(f"✅ JWT Secret found: {jwt_secret[:50]}...")
    print(f"   Length: {len(jwt_secret)} characters")
    print()
    
    # Instructions for user
    print("To test JWT decoding:")
    print("1. Open browser console (F12)")
    print("2. Run: const supabase = (await import('/src/lib/supabase/client')).createClient(); const {data: {session}} = await supabase.auth.getSession(); console.log('Token:', session?.access_token);")
    print("3. Copy the token and run this script with it as an argument")
    print()
    
    if len(sys.argv) > 1:
        token = sys.argv[1]
        print(f"Testing token: {token[:50]}...")
        print()
        
        try:
            # Decode header first
            header = jwt.get_unverified_header(token)
            print(f"Token header: {header}")
            print(f"Algorithm: {header.get('alg', 'unknown')}")
            print()
            
            # Try to decode with verification
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=["HS256"],
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_aud": False,
                        "verify_iss": False,
                    }
                )
                print("✅ Token decoded successfully!")
                print(f"   User ID (sub): {payload.get('sub', 'N/A')}")
                print(f"   Role: {payload.get('role', 'N/A')}")
                print(f"   Expires: {payload.get('exp', 'N/A')}")
            except jwt.InvalidAlgorithmError as e:
                print(f"❌ Algorithm error: {e}")
                print(f"   Token uses: {header.get('alg')}")
                print(f"   Expected: HS256")
                print()
                print("   This means the token algorithm doesn't match.")
                print("   Solution: Sign out and sign in again to get a fresh token.")
            except jwt.InvalidSignatureError as e:
                print(f"❌ Signature verification failed: {e}")
                print()
                print("   This means the JWT secret doesn't match Supabase.")
                print("   Solution: Update SUPABASE_JWT_SECRET in backend/.env")
            except jwt.ExpiredSignatureError:
                print("❌ Token has expired")
                print("   Solution: Sign out and sign in again")
            except Exception as e:
                print(f"❌ Error: {e}")
                
        except Exception as e:
            print(f"❌ Failed to decode token: {e}")
    else:
        print("💡 Tip: Pass a JWT token as argument to test decoding")
        print("   Example: python3 test_jwt.py 'your-jwt-token-here'")

if __name__ == "__main__":
    test_jwt_decoding()

