# Vault Integration - Future Enhancement

This document describes the planned integration with enterprise secret management systems.

> **Status:** 🚧 Placeholder - Not Yet Implemented  
> **Target Version:** 2.0.0  
> **Priority:** Medium

---

## 🎯 Overview

Enable AWX MCP Server to retrieve AWX credentials from enterprise secret management systems instead of requiring clients to provide them.

### Benefits

- ✅ Centralized credential management
- ✅ Automatic credential rotation
- ✅ Audit trail for credential access
- ✅ Compliance with security policies
- ✅ No credentials in client configuration
- ✅ Role-based access control

---

## 🔐 Supported Secret Managers (Planned)

### 1. HashiCorp Vault
- **Use Case:** Self-hosted, enterprise-grade
- **Auth Methods:** Token, Kubernetes, AppRole, LDAP
- **Features:** Dynamic secrets, encryption, audit logs

### 2. AWS Secrets Manager
- **Use Case:** AWS-native deployments
- **Auth Methods:** IAM roles, access keys
- **Features:** Automatic rotation, KMS encryption

### 3. Azure Key Vault
- **Use Case:** Azure-native deployments
- **Auth Methods:** Managed identity, service principal
- **Features:** HSM-backed, RBAC

### 4. Google Secret Manager
- **Use Case:** GCP-native deployments
- **Auth Methods:** Service accounts, workload identity
- **Features:** Versioning, IAM integration

### 5. Kubernetes Secrets
- **Use Case:** K8s-native deployments
- **Auth Methods:** Service account
- **Features:** Native integration, RBAC

### 6. GitHub Secrets
- **Use Case:** GitHub-hosted workflows
- **Auth Methods:** GitHub App, PAT
- **Features:** Environment secrets

### 7. CyberArk
- **Use Case:** Enterprise PAM
- **Auth Methods:** API key, certificate
- **Features:** Advanced PAM, compliance

### 8. 1Password Secrets Automation
- **Use Case:** Developer-friendly
- **Auth Methods:** Service account
- **Features:** Shared vaults, CLI

---

## 📋 Configuration

### Server Configuration

**config/vault-config.yaml** (template):

```yaml
# Vault provider selection
provider: "hashicorp_vault"  # or aws, azure, gcp, k8s, github, cyberark, onepassword

# HashiCorp Vault Configuration
hashicorp_vault:
  address: "https://vault.company.com:8200"
  namespace: "awx"  # Optional
  
  # Authentication method
  auth_method: "kubernetes"  # or token, approle, ldap, aws, azure, gcp
  
  # Kubernetes auth
  kubernetes:
    role: "awx-mcp-server"
    service_account_token_path: "/var/run/secrets/kubernetes.io/serviceaccount/token"
  
  # Token auth (not recommended for production)
  token:
    token_path: "/vault/secrets/token"
  
  # AppRole auth
  approle:
    role_id_path: "/vault/secrets/role-id"
    secret_id_path: "/vault/secrets/secret-id"
  
  # Secret paths
  secret_engine: "kv-v2"
  secret_path_template: "secret/awx/{environment}/{user_id}"
  
  # Caching
  cache_ttl: 300  # seconds
  
  # TLS
  tls_verify: true
  ca_cert_path: "/etc/ssl/certs/vault-ca.pem"

# AWS Secrets Manager Configuration
aws_secrets_manager:
  region: "us-east-1"
  secret_name_template: "awx/{environment}/{user_id}"
  
  # Authentication (auto-detected from IAM role)
  # Or specify credentials
  access_key_id: ""  # From environment or IAM role
  secret_access_key: ""  # From environment or IAM role

# Azure Key Vault Configuration
azure_key_vault:
  vault_url: "https://company.vault.azure.net"
  secret_name_template: "awx-{environment}-{user-id}"
  
  # Authentication (auto-detected from managed identity)
  # Or specify credentials
  client_id: ""
  client_secret: ""
  tenant_id: ""

# Google Secret Manager Configuration
google_secret_manager:
  project_id: "my-project"
  secret_name_template: "awx-{environment}-{user_id}"
  
  # Authentication (auto-detected from workload identity)
  # Or specify service account
  service_account_path: "/secrets/gcp-sa.json"

# Kubernetes Secrets Configuration
kubernetes_secrets:
  namespace: "awx-mcp"
  secret_name_template: "awx-creds-{user-id}"
  key: "awx-token"

# GitHub Secrets Configuration
github_secrets:
  repository: "company/awx-mcp-config"
  environment: "production"  # Optional
  
  # Authentication
  app_id: ""
  private_key_path: "/secrets/github-app.pem"
  # Or use PAT
  personal_access_token: ""

# CyberArk Configuration
cyberark:
  base_url: "https://cyberark.company.com"
  app_id: "awx-mcp-server"
  safe: "AWX_Credentials"
  object_name_template: "{environment}_{user_id}"
  
  # Authentication
  api_key_path: "/secrets/cyberark-api.key"
  certificate_path: "/secrets/cyberark-cert.pem"

# 1Password Configuration
onepassword:
  service_account_token_path: "/secrets/1password-sa-token"
  vault: "AWX Credentials"
  item_name_template: "{environment}-{user_id}"

# User mapping
user_mapping:
  # How to identify users from MCP requests
  user_id_source: "header"  # header, jwt, certificate, static
  user_id_header: "X-User-ID"
  
  # JWT validation
  jwt:
    issuer: "https://auth.company.com"
    audience: "awx-mcp-server"
    public_key_path: "/secrets/jwt-public.pem"
  
  # Static mapping (for testing)
  static_user: "default"

# Environment mapping
environment_mapping:
  default: "production"
  allowed_environments:
    - development
    - staging
    - production
```

---

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure (v1.6.0)
- [ ] Abstract credential provider interface
- [ ] Implement provider registry
- [ ] Add configuration loader
- [ ] Create unit tests

### Phase 2: HashiCorp Vault (v1.7.0)
- [ ] Implement Vault client
- [ ] Support Kubernetes auth
- [ ] Support AppRole auth
- [ ] Support Token auth
- [ ] Add integration tests

### Phase 3: Cloud Providers (v1.8.0)
- [ ] AWS Secrets Manager
- [ ] Azure Key Vault
- [ ] Google Secret Manager
- [ ] Kubernetes Secrets

### Phase 4: Enterprise PAM (v1.9.0)
- [ ] CyberArk integration
- [ ] 1Password Secrets Automation
- [ ] GitHub Secrets

### Phase 5: Advanced Features (v2.0.0)
- [ ] Automatic credential rotation
- [ ] Credential caching with TTL
- [ ] Multi-provider fallback
- [ ] Audit logging
- [ ] Metrics and monitoring

---

## 💻 Code Structure

### Placeholder Files Created

```
server/src/awx_mcp_server/storage/
├── __init__.py
├── credentials.py                 # Current keyring implementation
├── vault_integration.py           # 🚧 Placeholder
└── providers/                     # 🚧 New directory
    ├── __init__.py
    ├── base.py                    # Abstract base class
    ├── hashicorp_vault.py         # HashiCorp Vault provider
    ├── aws_secrets.py             # AWS Secrets Manager
    ├── azure_keyvault.py          # Azure Key Vault
    ├── gcp_secrets.py             # Google Secret Manager
    ├── kubernetes_secrets.py      # K8s Secrets
    ├── github_secrets.py          # GitHub Secrets
    ├── cyberark.py                # CyberArk
    └── onepassword.py             # 1Password
```

---

## 📝 Usage Example (Future)

Once implemented, server will retrieve credentials from vault:

```python
# Server code (future)
from awx_mcp_server.storage.vault_integration import VaultCredentialProvider

# Initialize vault provider
vault_provider = VaultCredentialProvider(config_path="config/vault-config.yaml")

# Get credentials for user from vault
credentials = await vault_provider.get_credentials(
    user_id="john.doe@company.com",
    environment="production"
)

# Use credentials to connect to AWX
awx_client = CompositeAWXClient(
    base_url=credentials.awx_url,
    token=credentials.awx_token
)
```

### Client Configuration (Future)

When vault is enabled, clients don't need to provide AWX credentials:

```json
{
  "github.copilot.chat.mcpServers": {
    "awx-remote": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-sse", "https://awx-mcp.company.com"],
      "env": {
        "USER_ID": "john.doe@company.com",
        "AWX_ENVIRONMENT": "production"
      }
    }
  }
}
```

Server retrieves credentials from vault based on user identity and environment.

---

## 🔒 Security Considerations

### Credential Access Audit

All credential retrievals should be logged:

```python
# Future implementation
logger.audit(
    event="credential_access",
    user_id="john.doe@company.com",
    environment="production",
    vault_provider="hashicorp_vault",
    vault_path="secret/awx/production/john.doe",
    awx_url="https://awx-prod.example.com",
    timestamp=datetime.utcnow()
)
```

### Least Privilege

Server should only have access to credentials for authorized users:

```hcl
# HashiCorp Vault policy example
path "secret/data/awx/production/*" {
  capabilities = ["read"]
}

path "secret/data/awx/development/*" {
  capabilities = ["read"]
}
```

### Credential Rotation

Automatic rotation support:

```python
# Future implementation
@schedule.every(24).hours
async def rotate_credentials():
    """Rotate AWX tokens in vault."""
    for environment in ["production", "staging", "development"]:
        new_token = await awx_admin.create_token(
            user="automation",
            scope="write",
            expires_in_days=30
        )
        
        await vault.update_secret(
            path=f"secret/awx/{environment}/automation",
            data={"token": new_token}
        )
        
        logger.info(f"Rotated token for {environment}")
```

---

## 🧪 Testing Plan

### Unit Tests

```python
# tests/test_vault_integration.py (future)

import pytest
from awx_mcp_server.storage.vault_integration import VaultCredentialProvider

@pytest.mark.asyncio
async def test_hashicorp_vault_provider():
    """Test HashiCorp Vault integration."""
    provider = VaultCredentialProvider(provider="hashicorp_vault")
    credentials = await provider.get_credentials(
        user_id="test.user",
        environment="development"
    )
    assert credentials.awx_url == "https://awx-dev.example.com"
    assert credentials.awx_token.startswith("awx_")

@pytest.mark.asyncio
async def test_aws_secrets_manager():
    """Test AWS Secrets Manager integration."""
    provider = VaultCredentialProvider(provider="aws_secrets_manager")
    credentials = await provider.get_credentials(
        user_id="test.user",
        environment="production"
    )
    assert credentials is not None
```

---

## 📚 References

- [HashiCorp Vault Documentation](https://www.vaultproject.io/docs)
- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [Azure Key Vault](https://docs.microsoft.com/en-us/azure/key-vault/)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [CyberArk REST API](https://docs.cyberark.com/Product-Doc/OnlineHelp/PAS/Latest/en/Content/WebServices/Implementing%20Privileged%20Account%20Security%20Web%20Services%20.htm)
- [1Password Secrets Automation](https://developer.1password.com/docs/connect/)

---

## 🤝 Contributing

To contribute to vault integration:

1. Review this design document
2. Implement a provider in `server/src/awx_mcp_server/storage/providers/`
3. Follow the base provider interface
4. Add tests in `tests/test_vault_integration.py`
5. Update this documentation
6. Submit PR

---

## 📧 Support

For questions about vault integration:

- Open an issue: https://github.com/SurgeX-Labs/awx-mcp-server/issues
- Label: `enhancement`, `vault-integration`
- Email: support@surgexlabs.com
