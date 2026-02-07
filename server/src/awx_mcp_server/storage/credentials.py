"""Secure credential storage using OS keyring."""

import keyring
from typing import Optional
from uuid import UUID

from awx_mcp_server.domain import CredentialError, CredentialType


class CredentialStore:
    """Secure credential storage interface."""

    SERVICE_NAME = "awx-mcp-server"

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize credential store.
        
        Args:
            tenant_id: Tenant ID for multi-tenant isolation (optional)
        """
        self.tenant_id = tenant_id
        # Use tenant-specific service name for isolation
        if tenant_id:
            self.service_name = f"{self.SERVICE_NAME}:{tenant_id}"
        else:
            self.service_name = self.SERVICE_NAME

    def store_credential(
        self,
        env_id: UUID,
        credential_type: CredentialType,
        username: Optional[str],
        secret: str,
    ) -> None:
        """
        Store credential securely.

        Args:
            env_id: Environment UUID
            credential_type: Type of credential (password or token)
            username: Username (required for password auth)
            secret: Password or token value
        
        Raises:
            CredentialError: If storage fails
        """
        try:
            key = self._make_key(env_id, credential_type)
            
            if credential_type == CredentialType.PASSWORD:
                if not username:
                    raise CredentialError("Username required for password authentication")
                # Store username separately
                keyring.set_password(self.service_name, f"{key}:username", username)
                keyring.set_password(self.service_name, f"{key}:password", secret)
            else:
                # Token authentication
                keyring.set_password(self.service_name, f"{key}:token", secret)
        except Exception as e:
            raise CredentialError(f"Failed to store credential: {e}")

    def get_credential(
        self, env_id: UUID, credential_type: CredentialType
    ) -> tuple[Optional[str], str]:
        """
        Retrieve credential securely.

        Args:
            env_id: Environment UUID
            credential_type: Type of credential
        
        Returns:
            Tuple of (username, secret) - username is None for token auth
        
        Raises:
            CredentialError: If retrieval fails or credential not found
        """
        try:
            key = self._make_key(env_id, credential_type)
            
            if credential_type == CredentialType.PASSWORD:
                username = keyring.get_password(self.service_name, f"{key}:username")
                password = keyring.get_password(self.service_name, f"{key}:password")
                
                if not username or not password:
                    raise CredentialError(f"Credential not found for environment {env_id}")
                
                return username, password
            else:
                token = keyring.get_password(self.service_name, f"{key}:token")
                
                if not token:
                    raise CredentialError(f"Token not found for environment {env_id}")
                
                return None, token
        except Exception as e:
            if isinstance(e, CredentialError):
                raise
            raise CredentialError(f"Failed to retrieve credential: {e}")

    def delete_credential(self, env_id: UUID) -> None:
        """
        Delete all credentials for an environment.

        Args:
            env_id: Environment UUID
        """
        try:
            # Try both password and token
            for cred_type in [CredentialType.PASSWORD, CredentialType.TOKEN]:
                key = self._make_key(env_id, cred_type)
                try:
                    if cred_type == CredentialType.PASSWORD:
                        keyring.delete_password(self.service_name, f"{key}:username")
                        keyring.delete_password(self.service_name, f"{key}:password")
                    else:
                        keyring.delete_password(self.service_name, f"{key}:token")
                except keyring.errors.PasswordDeleteError:
                    # Credential doesn't exist, that's fine
                    pass
        except Exception as e:
            raise CredentialError(f"Failed to delete credential: {e}")

    def credential_exists(self, env_id: UUID) -> bool:
        """
        Check if credential exists for environment.

        Args:
            env_id: Environment UUID
        
        Returns:
            True if credential exists
        """
        try:
            # Check for password auth
            key = self._make_key(env_id, CredentialType.PASSWORD)
            password = keyring.get_password(self.service_name, f"{key}:password")
            if password:
                return True
            
            # Check for token auth
            key = self._make_key(env_id, CredentialType.TOKEN)
            token = keyring.get_password(self.service_name, f"{key}:token")
            return token is not None
        except Exception:
            return False

    def _make_key(self, env_id: UUID, credential_type: CredentialType) -> str:
        """Create storage key."""
        return f"{env_id}:{credential_type.value}"
