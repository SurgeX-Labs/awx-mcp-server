"""Authentication and authorization for MCP server."""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel


class APIKey(BaseModel):
    """API key model."""
    key_id: str
    key_hash: str
    name: str
    tenant_id: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    permissions: list[str] = ["read", "write", "execute"]


class APIKeyManager:
    """Manage API keys for authentication."""

    def __init__(self):
        """Initialize API key manager."""
        self.keys: dict[str, APIKey] = {}
    
    def generate_key(
        self,
        name: str,
        tenant_id: str,
        expires_days: Optional[int] = 90,
        permissions: Optional[list[str]] = None,
    ) -> tuple[str, APIKey]:
        """
        Generate a new API key.
        
        Returns:
            Tuple of (plaintext_key, api_key_object)
        """
        # Generate secure random key
        plaintext_key = f"awx_mcp_{secrets.token_urlsafe(32)}"
        key_hash = self._hash_key(plaintext_key)
        key_id = secrets.token_hex(8)
        
        created_at = datetime.utcnow()
        expires_at = (
            created_at + timedelta(days=expires_days)
            if expires_days
            else None
        )
        
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            tenant_id=tenant_id,
            created_at=created_at,
            expires_at=expires_at,
            permissions=permissions or ["read", "write", "execute"],
        )
        
        self.keys[key_hash] = api_key
        return plaintext_key, api_key
    
    def verify_key(self, plaintext_key: str) -> Optional[APIKey]:
        """
        Verify an API key and return key info.
        
        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self._hash_key(plaintext_key)
        api_key = self.keys.get(key_hash)
        
        if not api_key:
            return None
        
        # Check if active
        if not api_key.is_active:
            return None
        
        # Check expiration
        if api_key.expires_at and datetime.utcnow() > api_key.expires_at:
            return None
        
        # Update last used
        api_key.last_used = datetime.utcnow()
        
        return api_key
    
    def revoke_key(self, key_hash: str) -> bool:
        """Revoke an API key."""
        if key_hash in self.keys:
            self.keys[key_hash].is_active = False
            return True
        return False
    
    def list_keys(self, tenant_id: Optional[str] = None) -> list[APIKey]:
        """List all API keys, optionally filtered by tenant."""
        keys = list(self.keys.values())
        if tenant_id:
            keys = [k for k in keys if k.tenant_id == tenant_id]
        return keys
    
    @staticmethod
    def _hash_key(plaintext_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(plaintext_key.encode()).hexdigest()


class TenantContext:
    """Thread-local tenant context for multi-tenancy."""
    
    _current_tenant: Optional[str] = None
    
    @classmethod
    def set_tenant(cls, tenant_id: str):
        """Set current tenant ID."""
        cls._current_tenant = tenant_id
    
    @classmethod
    def get_tenant(cls) -> Optional[str]:
        """Get current tenant ID."""
        return cls._current_tenant
    
    @classmethod
    def clear(cls):
        """Clear tenant context."""
        cls._current_tenant = None
