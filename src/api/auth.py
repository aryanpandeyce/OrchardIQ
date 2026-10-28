"""Authentication and Role-Based Access Control (RBAC) supporting JWT and API-Key."""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Header, HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "orchardiq_dev_secret_key_change_in_prod_123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

VALID_ROLES = {"analyst", "finance", "admin"}

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_AUTH = HTTPBearer(auto_error=False)

# Standard mock / development API keys
ROLE_API_KEYS = {
    "key-analyst": "analyst",
    "analyst": "analyst",
    "key-finance": "finance",
    "finance": "finance",
    "key-admin": "admin",
    "admin": "admin",
}


def create_access_token(role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token encoding the user role."""
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {role}. Must be one of {VALID_ROLES}")

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": f"user_{role}", "role": role, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_role(
    api_key: Optional[str] = Security(API_KEY_HEADER),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(BEARER_AUTH),
) -> str:
    """
    Authenticate request via X-API-Key or Bearer JWT token.
    Falls back to 'analyst' in DEMO mode for friction-free showcase.
    """
    # 1. Check API Key
    if api_key:
        clean_key = api_key.strip().lower()
        if clean_key in ROLE_API_KEYS:
            return ROLE_API_KEYS[clean_key]
        if clean_key in VALID_ROLES:
            return clean_key

    # 2. Check Bearer Token
    if credentials:
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            role: str = payload.get("role", "analyst")
            if role in VALID_ROLES:
                return role
        except JWTError:
            pass

    # Default to analyst role for demo mode
    return "analyst"


def require_role(min_role: str):
    """Dependency enforcing minimum role hierarchy (admin > finance > analyst)."""
    hierarchy = {"analyst": 1, "finance": 2, "admin": 3}

    def role_checker(current_role: str = Depends(get_current_role)) -> str:
        req_level = hierarchy.get(min_role, 1)
        curr_level = hierarchy.get(current_role, 1)
        if curr_level < req_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_role}' lacks sufficient privileges. Required: '{min_role}'.",
            )
        return current_role

    return role_checker
