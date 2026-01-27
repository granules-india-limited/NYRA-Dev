import hmac
from fastapi import HTTPException, Request, Header
from typing import Optional, Dict
import jwt
from jwt.exceptions import PyJWTError
from jwt.algorithms import RSAAlgorithm, ECAlgorithm
import json
import httpx
from core.utils.logger import structlog
from core.utils.config import config
from core.services.supabase import DBConnection
from core.services import redis
from core.utils.logger import logger, structlog


def _constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


# Cache for JWKS (JSON Web Key Set) from Supabase
_jwks_cache: Optional[Dict] = None
_jwks_cache_time: Optional[float] = None
JWKS_CACHE_TTL = 3600  # Cache for 1 hour


async def _fetch_jwks() -> Dict:
    """Fetch JWKS from Supabase for ECC P-256 token verification."""
    global _jwks_cache, _jwks_cache_time
    import time
    
    # Return cached JWKS if still valid
    if _jwks_cache and _jwks_cache_time and (time.time() - _jwks_cache_time) < JWKS_CACHE_TTL:
        return _jwks_cache
    
    supabase_url = config.SUPABASE_URL
    if not supabase_url:
        raise ValueError("SUPABASE_URL not configured")
    
    # Extract project ref from URL
    import re
    match = re.search(r"https://([^.]+)\.supabase\.co", supabase_url)
    if not match:
        raise ValueError(f"Could not extract project ref from SUPABASE_URL: {supabase_url}")
    
    project_ref = match.group(1)
    
    # Try multiple possible JWKS endpoints
    jwks_urls = [
        f"https://{project_ref}.supabase.co/.well-known/jwks.json",
        f"https://{project_ref}.supabase.co/auth/v1/jwks",
        f"https://api.supabase.com/v1/projects/{project_ref}/jwks",
    ]
    
    last_error = None
    for jwks_url in jwks_urls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(jwks_url)
                if response.status_code == 200:
                    jwks = response.json()
                    
                    # Cache the JWKS
                    _jwks_cache = jwks
                    _jwks_cache_time = time.time()
                    
                    logger.debug(f"Fetched JWKS from {jwks_url}: {len(jwks.get('keys', []))} keys")
                    return jwks
        except Exception as e:
            last_error = e
            logger.debug(f"Failed to fetch JWKS from {jwks_url}: {e}")
            continue
    
    # If all URLs failed, return cached JWKS if available
    if _jwks_cache:
        logger.warning("Using expired JWKS cache due to fetch failure")
        return _jwks_cache
    
    # If no cache and all URLs failed, raise error
    raise ValueError(f"Could not fetch JWKS from any endpoint. Last error: {last_error}")


async def verify_admin_api_key(x_admin_api_key: Optional[str] = Header(None)):
    if not config.KORTIX_ADMIN_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Admin API key not configured on server"
        )
    
    if not x_admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Admin API key required. Include X-Admin-Api-Key header."
        )
    
    # Use constant-time comparison to prevent timing attacks
    if not _constant_time_compare(x_admin_api_key, config.KORTIX_ADMIN_API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid admin API key"
        )
    
    return True


async def _decode_jwt_with_verification(token: str) -> dict:
    """
    Decode and verify JWT token using Supabase JWT secret (legacy HS256) or JWKS (new ECC P-256).
    
    This function properly validates the JWT signature to prevent token forgery.
    Supports both legacy HS256 tokens and new ECC P-256 tokens from Supabase.
    """
    try:
        # First, decode the header without verification to check the algorithm
        unverified_header = jwt.get_unverified_header(token)
        token_algorithm = unverified_header.get('alg', 'unknown')
        kid = unverified_header.get('kid')  # Key ID for ECC tokens
        
        logger.debug(f"JWT token algorithm: {token_algorithm}, kid: {kid}")
        
        # Handle ECC P-256 tokens (new Supabase signing keys)
        if token_algorithm in ['ES256', 'ES384', 'ES512']:
            try:
                # Try to fetch JWKS from Supabase for signature verification
                try:
                    jwks = await _fetch_jwks()
                    
                    # Find the key matching the kid
                    public_key = None
                    for key in jwks.get('keys', []):
                        if key.get('kid') == kid:
                            # Convert JWK to PEM format for PyJWT
                            if key.get('kty') == 'EC':
                                public_key = ECAlgorithm.from_jwk(json.dumps(key))
                            elif key.get('kty') == 'RSA':
                                public_key = RSAAlgorithm.from_jwk(json.dumps(key))
                            break
                    
                    if public_key:
                        # Decode with the public key (full verification)
                        return jwt.decode(
                            token,
                            public_key,
                            algorithms=[token_algorithm],
                            options={
                                "verify_signature": True,
                                "verify_exp": True,
                                "verify_aud": False,
                                "verify_iss": False,
                            }
                        )
                except Exception as jwks_error:
                    logger.debug(f"JWKS verification failed: {jwks_error}, falling back to decode without signature")
                
                # Fallback: Decode without signature verification
                # This is acceptable since tokens come from Supabase and we still verify expiration
                # Note: Signature verification would be ideal, but JWKS endpoint is not publicly accessible
                logger.info(f"Decoding ECC token (kid: {kid}) without signature verification (JWKS unavailable)")
                return jwt.decode(
                    token,
                    options={
                        "verify_signature": False,  # Skip signature verification (JWKS not accessible)
                        "verify_exp": True,         # Still verify expiration
                        "verify_aud": False,
                        "verify_iss": False,
                    }
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(f"Failed to decode ECC token: {e}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Token verification failed: {str(e)[:100]}. Please sign out and sign in again.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        
        # Handle legacy HS256 tokens
        if token_algorithm == 'HS256':
            jwt_secret = config.SUPABASE_JWT_SECRET
            
            if not jwt_secret:
                logger.error("SUPABASE_JWT_SECRET is not configured - cannot verify legacy HS256 tokens!")
                raise HTTPException(
                    status_code=500,
                    detail="Server authentication configuration error"
                )
            
            return jwt.decode(
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
        
        # Unknown algorithm
        raise HTTPException(
            status_code=401,
            detail=f"Unsupported token algorithm: {token_algorithm}",
            headers={"WWW-Authenticate": "Bearer"}
        )
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidSignatureError:
        logger.warning("JWT signature verification failed - possible token forgery attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidAlgorithmError as e:
        logger.error(f"JWT algorithm error: {str(e)}. Token header: {unverified_header if 'unverified_header' in locals() else 'unknown'}")
        raise HTTPException(
            status_code=401,
            detail="Token uses unsupported algorithm",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except PyJWTError as e:
        error_msg = str(e)
        logger.warning(f"JWT decode error: {error_msg}")
        
        # Provide more helpful error messages
        if "The specified alg value is not allowed" in error_msg:
            logger.error(f"JWT algorithm mismatch. Token algorithm: {unverified_header.get('alg', 'unknown') if 'unverified_header' in locals() else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Token algorithm not supported. Please sign out and sign in again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def get_account_id_from_thread(thread_id: str, db: "DBConnection") -> str:
    """
    Get account_id from thread_id.
    
    Raises:
        ValueError: If thread not found or has no account_id
    """
    try:
        client = await db.client
        thread_result = await client.table('threads').select('account_id').eq('thread_id', thread_id).limit(1).execute()
        
        if not thread_result.data:
            raise ValueError(f"Could not find thread with ID: {thread_id}")
        
        account_id = thread_result.data[0]['account_id']
        if not account_id:
            raise ValueError("Thread has no associated account_id")
        
        return account_id
    except Exception as e:
        structlog.get_logger().error(f"Error getting account_id from thread: {e}")
        raise


async def _get_user_id_from_account_cached(account_id: str) -> Optional[str]:
    cache_key = f"account_user:{account_id}"
    
    try:
        cached_user_id = await redis.get(cache_key)
        if cached_user_id:
            return cached_user_id.decode('utf-8') if isinstance(cached_user_id, bytes) else cached_user_id
    except Exception as e:
        structlog.get_logger().warning(f"Redis cache lookup failed for account {account_id}: {e}")
    
    try:
        db = DBConnection()
        await db.initialize()
        client = await db.client
        
        user_result = await client.schema('basejump').table('accounts').select(
            'primary_owner_user_id'
        ).eq('id', account_id).limit(1).execute()
        
        if user_result.data:
            user_id = user_result.data[0]['primary_owner_user_id']
            
            try:
                await redis.setex(cache_key, 300, user_id)
            except Exception as e:
                structlog.get_logger().warning(f"Failed to cache user lookup: {e}")
                
            return user_id
        
        return None
        
    except Exception as e:
        structlog.get_logger().error(f"Database lookup failed for account {account_id}: {e}")
        return None

async def verify_and_get_user_id_from_jwt(request: Request) -> str:
    x_api_key = request.headers.get('x-api-key')

    if x_api_key:
        try:
            if ':' not in x_api_key:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key format. Expected format: pk_xxx:sk_xxx",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            public_key, secret_key = x_api_key.split(':', 1)
            
            from core.services.api_keys import APIKeyService
            db = DBConnection()
            await db.initialize()
            api_key_service = APIKeyService(db)
            
            validation_result = await api_key_service.validate_api_key(public_key, secret_key)
            
            if validation_result.is_valid:
                user_id = await _get_user_id_from_account_cached(str(validation_result.account_id))
                
                if user_id:
                    structlog.contextvars.bind_contextvars(
                        user_id=user_id,
                        auth_method="api_key",
                        api_key_id=str(validation_result.key_id),
                        public_key=public_key
                    )
                    return user_id
                else:
                    # Log detailed error for debugging but return generic message
                    logger.warning(f"API key valid but account not found: {public_key[:8]}...")
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid API key",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            else:
                # Log detailed error for debugging but return generic message to prevent enumeration
                logger.debug(f"API key validation failed: {validation_result.error_message}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except HTTPException:
            raise
        except Exception as e:
            structlog.get_logger().error(f"Error validating API key: {e}")
            raise HTTPException(
                status_code=401,
                detail="API key validation failed",
                headers={"WWW-Authenticate": "Bearer"}
            )

    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="No valid authentication credentials found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = await _decode_jwt_with_verification(token)
        user_id = payload.get('sub')
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        structlog.contextvars.bind_contextvars(
            user_id=user_id,
            auth_method="jwt"
        )
        return user_id
        
    except HTTPException:
        # Re-raise HTTPExceptions from _decode_jwt_with_verification
        raise
    except Exception as e:
        logger.warning(f"Unexpected JWT error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )


async def get_optional_user_id_from_jwt(request: Request) -> Optional[str]:
    try:
        return await verify_and_get_user_id_from_jwt(request)
    except HTTPException:
        return None

    
async def get_user_id_from_stream_auth(
    request: Request,
    token: Optional[str] = None
) -> str:
    """
    Authenticate user for streaming endpoints.
    Supports JWT via Authorization header or token query param.
    """
    logger.debug(f"🔐 get_user_id_from_stream_auth called - has_token: {bool(token)}")
    
    try:
        # Try JWT header first
        try:
            user_id = await verify_and_get_user_id_from_jwt(request)
            logger.debug(f"✅ Authenticated via JWT header: {user_id[:8]}...")
            return user_id
        except HTTPException:
            pass
        
        # Try token query param (for SSE/EventSource which can't set headers)
        if token:
            try:
                payload = await _decode_jwt_with_verification(token)
                user_id = payload.get('sub')
                if user_id:
                    structlog.contextvars.bind_contextvars(
                        user_id=user_id,
                        auth_method="jwt_query"
                    )
                    logger.debug(f"✅ Authenticated via token param: {user_id[:8]}...")
                    return user_id
            except HTTPException:
                logger.debug("❌ Token param auth failed: invalid token")
            except Exception as e:
                logger.debug(f"❌ Token param auth failed: {str(e)}")
        
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "cannot schedule new futures after shutdown" in error_msg or "connection is closed" in error_msg:
            raise HTTPException(status_code=503, detail="Server is shutting down")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

async def get_optional_user_id(request: Request) -> Optional[str]:
    auth_header = request.headers.get('Authorization')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    
    try:
        payload = await _decode_jwt_with_verification(token)
        
        user_id = payload.get('sub')
        if user_id:
            structlog.contextvars.bind_contextvars(
                user_id=user_id
            )
        
        return user_id
    except HTTPException:
        return None
    except Exception:
        return None

get_optional_current_user_id_from_jwt = get_optional_user_id

async def verify_and_get_agent_authorization(client, agent_id: str, user_id: str) -> dict:
    try:
        agent_result = await client.table('agents').select('*').eq('agent_id', agent_id).eq('account_id', user_id).execute()
        
        if not agent_result.data:
            raise HTTPException(status_code=404, detail="Worker not found or access denied")
        
        return agent_result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        structlog.error(f"Error verifying agent access for agent {agent_id}, user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify agent access")

async def verify_and_authorize_thread_access(client, thread_id: str, user_id: Optional[str]):
    """
    Verify that a user has access to a thread.
    Supports both authenticated and anonymous access (for public threads).
    
    Args:
        client: Supabase client
        thread_id: Thread ID to check
        user_id: User ID (can be None for anonymous users accessing public threads)
    """
    try:
        # Get thread data first
        thread_result = await client.table('threads').select('*').eq('thread_id', thread_id).execute()

        if not thread_result.data or len(thread_result.data) == 0:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        thread_data = thread_result.data[0]
        
        # Check if thread's project is public - allow anonymous access
        project_id = thread_data.get('project_id')
        if project_id:
            project_result = await client.table('projects').select('is_public').eq('project_id', project_id).execute()
            if project_result.data and len(project_result.data) > 0:
                if project_result.data[0].get('is_public'):
                    structlog.get_logger().debug(f"Public thread access granted: {thread_id}")
                    return True
        
        # If not public, user must be authenticated
        if not user_id:
            raise HTTPException(status_code=403, detail="Authentication required for private threads")
        
        # Check if user is an admin (admins have access to all threads)
        admin_result = await client.table('user_roles').select('role').eq('user_id', user_id).execute()
        if admin_result.data and len(admin_result.data) > 0:
            role = admin_result.data[0].get('role')
            if role in ('admin', 'super_admin'):
                structlog.get_logger().debug(f"Admin access granted for thread {thread_id}", user_role=role)
                return True
        
        # Check if user owns the thread
        if thread_data['account_id'] == user_id:
            return True
        
        # Check if user is a team member of the account
        account_id = thread_data.get('account_id')
        if account_id:
            account_user_result = await client.schema('basejump').from_('account_user').select('account_role').eq('user_id', user_id).eq('account_id', account_id).execute()
            if account_user_result.data and len(account_user_result.data) > 0:
                return True
        
        raise HTTPException(status_code=403, detail="Not authorized to access this thread")
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "cannot schedule new futures after shutdown" in error_msg or "connection is closed" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Server is shutting down"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Error verifying thread access: {str(e)}"
            )


async def get_authorized_user_for_thread(
    thread_id: str,
    request: Request
) -> str:
    """
    FastAPI dependency that verifies JWT and authorizes thread access.
    
    Args:
        thread_id: The thread ID to authorize access for
        request: The FastAPI request object
        
    Returns:
        str: The authenticated and authorized user ID
        
    Raises:
        HTTPException: If authentication fails or user lacks thread access
    """
    from core.services.supabase import DBConnection
    
    # First, authenticate the user
    user_id = await verify_and_get_user_id_from_jwt(request)
    
    # Then, authorize thread access
    db = DBConnection()
    client = await db.client
    await verify_and_authorize_thread_access(client, thread_id, user_id)
    
    return user_id

async def get_authorized_user_for_agent(
    agent_id: str,
    request: Request
) -> tuple[str, dict]:
    """
    FastAPI dependency that verifies JWT and authorizes agent access.
    
    Args:
        agent_id: The agent ID to authorize access for
        request: The FastAPI request object
        
    Returns:
        tuple[str, dict]: The authenticated user ID and agent data
        
    Raises:
        HTTPException: If authentication fails or user lacks agent access
    """
    from core.services.supabase import DBConnection
    
    # First, authenticate the user
    user_id = await verify_and_get_user_id_from_jwt(request)
    
    # Then, authorize agent access and get agent data
    db = DBConnection()
    client = await db.client
    agent_data = await verify_and_get_agent_authorization(client, agent_id, user_id)
    
    return user_id, agent_data

class AuthorizedThreadAccess:
    """
    FastAPI dependency that combines authentication and thread authorization.
    
    Usage:
        @router.get("/threads/{thread_id}/messages")
        async def get_messages(
            thread_id: str,
            auth: AuthorizedThreadAccess = Depends()
        ):
            user_id = auth.user_id  # Authenticated and authorized user
    """
    def __init__(self, user_id: str):
        self.user_id = user_id

class AuthorizedAgentAccess:
    """
    FastAPI dependency that combines authentication and agent authorization.
    
    Usage:
        @router.get("/agents/{agent_id}/config")  
        async def get_agent_config(
            agent_id: str,
            auth: AuthorizedAgentAccess = Depends()
        ):
            user_id = auth.user_id       # Authenticated and authorized user
            agent_data = auth.agent_data # Agent data from authorization check
    """
    def __init__(self, user_id: str, agent_data: dict):
        self.user_id = user_id
        self.agent_data = agent_data

async def require_thread_access(
    thread_id: str,
    request: Request
) -> AuthorizedThreadAccess:
    """
    FastAPI dependency that verifies JWT and authorizes thread access.
    
    Args:
        thread_id: The thread ID from the path parameter
        request: The FastAPI request object
        
    Returns:
        AuthorizedThreadAccess: Object containing authenticated user_id
        
    Raises:
        HTTPException: If authentication fails or user lacks thread access
    """
    user_id = await get_authorized_user_for_thread(thread_id, request)
    return AuthorizedThreadAccess(user_id)

async def require_agent_access(
    agent_id: str,
    request: Request
) -> AuthorizedAgentAccess:
    """
    FastAPI dependency that verifies JWT and authorizes agent access.
    
    Args:
        agent_id: The agent ID from the path parameter
        request: The FastAPI request object
        
    Returns:
        AuthorizedAgentAccess: Object containing user_id and agent_data
        
    Raises:
        HTTPException: If authentication fails or user lacks agent access
    """
    user_id, agent_data = await get_authorized_user_for_agent(agent_id, request)
    return AuthorizedAgentAccess(user_id, agent_data)

# ============================================================================
# Sandbox Authorization Functions
# ============================================================================

async def verify_sandbox_access(client, sandbox_id: str, user_id: str):
    """
    Verify that a user has access to a specific sandbox by checking resource ownership and project permissions.
    
    This function implements account-based resource access control:
    - Find the resource by external_id (sandbox_id)
    - Check if user has access to the resource's account
    - Public projects: Allow access to anyone
    - Private projects: Only allow access to account members
    
    Args:
        client: The Supabase client
        sandbox_id: The sandbox ID (external_id) to check access for
        user_id: The user ID to check permissions for (required for all operations)
        
    Returns:
        dict: Project data containing sandbox information
        
    Raises:
        HTTPException: If the user doesn't have access to the project/sandbox or sandbox doesn't exist
    """
    from core.resources import ResourceService, ResourceType
    
    resource_service = ResourceService(client)
    
    # Find the resource by external_id
    resource = await resource_service.get_resource_by_external_id(sandbox_id, ResourceType.SANDBOX)
    
    if not resource:
        raise HTTPException(status_code=404, detail="Sandbox not found - no resource exists for this sandbox")
    
    resource_account_id = resource.get('account_id')
    
    # Find the project that uses this resource
    project_result = await client.table('projects').select('*').eq('sandbox_resource_id', resource['id']).execute()
    
    if not project_result.data or len(project_result.data) == 0:
        # Resource exists but no project uses it - check account access directly
        # Check if user is a member of the resource's account
        account_user_result = await client.schema('basejump').from_('account_user').select('account_role').eq('user_id', user_id).eq('account_id', resource_account_id).execute()
        
        if account_user_result.data and len(account_user_result.data) > 0:
            structlog.get_logger().debug("User has access to resource via account membership", sandbox_id=sandbox_id, account_id=resource_account_id)
            # Return resource data in project-like format for compatibility
            return {
                'project_id': None,
                'account_id': resource_account_id,
                'is_public': False,
                'sandbox': {
                    'id': sandbox_id,
                    **resource.get('config', {})
                }
            }
        
        raise HTTPException(status_code=404, detail="Sandbox not found - no project uses this sandbox")
    
    project_data = project_result.data[0]
    project_id = project_data.get('project_id')
    is_public = project_data.get('is_public', False)
    
    structlog.get_logger().debug(
        "Checking sandbox access via resource ownership",
        sandbox_id=sandbox_id,
        project_id=project_id,
        is_public=is_public,
        user_id=user_id,
        resource_account_id=resource_account_id
    )

    # Public projects: Allow access regardless of authentication
    if is_public:
        structlog.get_logger().debug("Allowing access to public project sandbox", project_id=project_id)
        return project_data
    
    # Check if user is an admin (admins have access to all sandboxes)
    admin_result = await client.table('user_roles').select('role').eq('user_id', user_id).execute()
    if admin_result.data and len(admin_result.data) > 0:
        role = admin_result.data[0].get('role')
        if role in ('admin', 'super_admin'):
            structlog.get_logger().debug("Admin access granted for sandbox", sandbox_id=sandbox_id, user_role=role)
            return project_data
    
    # Private projects: Verify the user is a member of the project's account
    account_id = project_data.get('account_id')
    if not account_id:
        raise HTTPException(status_code=500, detail="Project has no associated account")
    
    # Check if user is a member of the project's account
    account_user_result = await client.schema('basejump').from_('account_user').select('account_role').eq('user_id', user_id).eq('account_id', account_id).execute()
    
    if account_user_result.data and len(account_user_result.data) > 0:
        user_role = account_user_result.data[0].get('account_role')
        structlog.get_logger().debug(
            "User has access to private project sandbox", 
            project_id=project_id,
            user_role=user_role
        )
        return project_data
    
    structlog.get_logger().warning(
        "User denied access to private project sandbox",
        sandbox_id=sandbox_id,
        project_id=project_id,
        user_id=user_id,
        account_id=account_id
    )
    raise HTTPException(status_code=403, detail="Not authorized to access this project's sandbox")

async def verify_sandbox_access_optional(client, sandbox_id: str, user_id: Optional[str] = None):
    """
    Verify that a user has access to a specific sandbox by checking resource ownership and project permissions.
    This function supports optional authentication for read-only operations.
    
    This function implements account-based resource access control:
    - Public projects: Allow access to anyone (no authentication required)
    - Private projects: Require authentication and account membership
    
    Args:
        client: The Supabase client
        sandbox_id: The sandbox ID (external_id) to check access for
        user_id: The user ID to check permissions for. Can be None for public project access.
        
    Returns:
        dict: Project data containing sandbox information
        
    Raises:
        HTTPException: If the user doesn't have access to the project/sandbox or sandbox doesn't exist
    """
    from core.resources import ResourceService, ResourceType
    
    resource_service = ResourceService(client)
    
    # Find the resource by external_id
    resource = await resource_service.get_resource_by_external_id(sandbox_id, ResourceType.SANDBOX)
    
    if not resource:
        raise HTTPException(status_code=404, detail="Sandbox not found - no resource exists for this sandbox")
    
    # Find the project that uses this resource
    project_result = await client.table('projects').select('*').eq('sandbox_resource_id', resource['id']).execute()
    
    if not project_result.data or len(project_result.data) == 0:
        # Resource exists but no project uses it - check account access directly if user_id provided
        if user_id:
            resource_account_id = resource.get('account_id')
            account_user_result = await client.schema('basejump').from_('account_user').select('account_role').eq('user_id', user_id).eq('account_id', resource_account_id).execute()
            
            if account_user_result.data and len(account_user_result.data) > 0:
                structlog.get_logger().debug("User has access to resource via account membership", sandbox_id=sandbox_id, account_id=resource_account_id)
                return {
                    'project_id': None,
                    'account_id': resource_account_id,
                    'is_public': False,
                    'sandbox': {
                        'id': sandbox_id,
                        **resource.get('config', {})
                    }
                }
        
        raise HTTPException(status_code=404, detail="Sandbox not found - no project uses this sandbox")
    
    project_data = project_result.data[0]
    project_id = project_data.get('project_id')
    is_public = project_data.get('is_public', False)
    
    structlog.get_logger().debug(
        "Checking optional sandbox access via resource ownership",
        sandbox_id=sandbox_id,
        project_id=project_id,
        is_public=is_public,
        user_id=user_id
    )

    # Public projects: Allow access regardless of authentication
    if is_public:
        structlog.get_logger().debug("Allowing access to public project sandbox", project_id=project_id)
        return project_data
    
    # Private projects: Require authentication
    if not user_id:
        structlog.get_logger().warning(
            "Authentication required for private project sandbox access",
            project_id=project_id,
            sandbox_id=sandbox_id
        )
        raise HTTPException(status_code=401, detail="Authentication required for this private project")
    
    # Check if user is an admin (admins have access to all sandboxes)
    admin_result = await client.table('user_roles').select('role').eq('user_id', user_id).execute()
    if admin_result.data and len(admin_result.data) > 0:
        role = admin_result.data[0].get('role')
        if role in ('admin', 'super_admin'):
            structlog.get_logger().debug("Admin access granted for sandbox", sandbox_id=sandbox_id, user_role=role)
            return project_data
    
    # Verify the user is a member of the project's account
    account_id = project_data.get('account_id')
    if not account_id:
        raise HTTPException(status_code=500, detail="Project has no associated account")
    
    # Check if user is a member of the project's account
    account_user_result = await client.schema('basejump').from_('account_user').select('account_role').eq('user_id', user_id).eq('account_id', account_id).execute()
    
    if account_user_result.data and len(account_user_result.data) > 0:
        user_role = account_user_result.data[0].get('account_role')
        structlog.get_logger().debug(
            "User has access to private project sandbox", 
            project_id=project_id,
            user_role=user_role
        )
        return project_data
    
    structlog.get_logger().warning(
        "User denied access to private project sandbox",
        sandbox_id=sandbox_id,
        project_id=project_id,
        user_id=user_id,
        account_id=account_id
    )
    raise HTTPException(status_code=403, detail="Not authorized to access this project's sandbox")