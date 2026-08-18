## Goal

Establish a unified system security architecture and high-risk tool control model to consolidate fragmented security controls across Agent, MCP, RAG, Deployment domains into a centralized, verifiable, and consistent security posture.

## Scope

**In-Scope:**
- Develop a system-wide security architecture defining trust boundaries, protected assets, and a formal threat model.
- Define authentication and authorization requirements for all externally reachable APIs.
- Implement a standardized security policy for high-risk MCP tools (file-write, delete, shell, git, github, cicd, db) covering path/repository restrictions, command allowlists, argument validation, and approval workflows.
- Define and implement fail-safe behaviors (fail-closed in production, fail-open in local dev where appropriate).
- Establish clear protocols for secret management (provisioning, storage, rotation, revocation) and prohibit sensitive data in logs.
- Explicitly define responsibility boundaries for prompt-injection mitigation.
- Integrate audit logging requirements and ensure they capture necessary security events.

**Out-of-Scope:**
- Changes to existing MCP server implementations unless required by the unified policy.
- Changes to deployment infrastructure beyond what's needed for security enforcement.
- Changes to other systems' integration points (only internal security architecture).

## Assumptions

- The project already has some security controls (e.g., `SecurityProfile`, `security_lockdown_enabled`, allowlists in various MCP servers) but they're fragmented (verify current implementation against each claim).
- Fail-closed/fail-open behavior varies by context (e.g., CICD uses fail-closed for empty allowlists) (check current behavior in each MCP server).
- Secret management needs standardization (check how secrets are currently handled).
- Audit logging exists but may not capture all security events (review current audit log coverage).

## Design decisions

- Create a unified security module in `scripts/shared/security/` — provides a single source of truth for security policies.
- Use fail-closed as default — prevents unauthorized access in production environments.
- Separate secret management from security enforcement — keeps concerns isolated and allows independent evolution.
- Require explicit audit logging for all security events — ensures traceability and compliance.

## Alternatives considered

- Keep security controls distributed across MCP servers — rejected because it causes inconsistency and makes auditing difficult.
- Use fail-open as default — rejected because it would allow unauthorized access in production.
- Merge secret management into the security module — rejected because secret lifecycle is orthogonal to access control.
- Leave audit logging as-is — rejected because current coverage is incomplete.

## Implementation

### Procedure

#### Part A: Review current security controls

1. Search for all security profiles used today:
   ```bash
   rg -n "SecurityProfile\|security_lockdown\|allowlist\|denylist" scripts/
   ```
2. Determine current fail-closed/fail-open behavior in each MCP server.
3. Review current secret management mechanism.
4. Check current audit log coverage.

#### Part B: Create unified security module

1. Create `scripts/shared/security/__init__.py`:
   ```python
   """Unified security module for the agent system."""
   
   from .policy import SecurityPolicy, HighRiskToolPolicy
   from .auth import Authentication, Authorization
   from .secrets import SecretManager
   from .audit import AuditLogger
   
   __all__ = [
       "SecurityPolicy",
       "HighRiskToolPolicy",
       "Authentication",
       "Authorization",
       "SecretManager",
       "AuditLogger",
   ]
   ```

2. Create `scripts/shared/security/policy.py`:
   ```python
   """Security policy definitions."""
   
   from enum import Enum
   from typing import Optional
   
   class SecurityMode(Enum):
       FAIL_CLOSED = "fail_closed"
       FAIL_OPEN = "fail_open"
   
   class HighRiskToolPolicy:
       """Policy for high-risk MCP tools."""
       
       def __init__(
           self,
           allowed_paths: list[str] | None = None,
           allowed_commands: list[str] | None = None,
           mode: SecurityMode = SecurityMode.FAIL_CLOSED,
       ) -> None:
           self.allowed_paths = allowed_paths or []
           self.allowed_commands = allowed_commands or []
           self.mode = mode
       
       def validate_path(self, path: str) -> bool:
           """Validate a file path against the policy."""
           if not self.allowed_paths:
               return self.mode == SecurityMode.FAIL_OPEN
           return any(path.startswith(p) for p in self.allowed_paths)
       
       def validate_command(self, cmd: str) -> bool:
           """Validate a command against the policy."""
           if not self.allowed_commands:
               return self.mode == SecurityMode.FAIL_OPEN
           return cmd in self.allowed_commands
   ```

3. Create `scripts/shared/security/auth.py`:
   ```python
   """Authentication and authorization."""
   
   from abc import ABC, abstractmethod
   
   class Authentication(ABC):
       """Base class for authentication mechanisms."""
       
       @abstractmethod
       def authenticate(self, token: str) -> bool:
           """Authenticate a request token."""
           ...
   
   class Authorization(ABC):
       """Base class for authorization mechanisms."""
       
       @abstractmethod
       def authorize(self, user_id: str, resource: str, action: str) -> bool:
           """Authorize an action on a resource."""
           ...
   ```

4. Create `scripts/shared/security/secrets.py`:
   ```python
   """Secret management protocol."""
   
   from abc import ABC, abstractmethod
   
   class SecretManager(ABC):
       """Protocol for secret management."""
       
       @abstractmethod
       def provision(self, name: str, value: str) -> None:
           """Provision a new secret."""
           ...
       
       @abstractmethod
       def rotate(self, name: str) -> str:
           """Rotate a secret and return the new value."""
           ...
       
       @abstractmethod
       def revoke(self, name: str) -> None:
           """Revoke a secret."""
           ...
   ```

5. Create `scripts/shared/security/audit.py`:
   ```python
   """Audit logging integration."""
   
   import logging
   
   logger = logging.getLogger("security.audit")
   
   class AuditLogger:
       """Centralized audit logging for security events."""
       
       @staticmethod
       def log_security_event(event_type: str, details: dict) -> None:
           """Log a security event."""
           logger.warning(
               "SECURITY_EVENT type=%s details=%s",
               event_type,
               details,
           )
   ```

#### Part C: Update MCP servers to use unified security policies

1. For each high-risk MCP server (file-write, delete, shell, git, github, cicd, db):
   - Replace local allowlist/denylist logic with calls to `HighRiskToolPolicy`.
   - Add audit logging for all security events.
   - Ensure fail-closed behavior in production.

### Method

Part C — Example update for file-write MCP server:

```python
# BEFORE:
class FileWriteServer:
    def __init__(self):
        self.allowed_paths = [...]  # Local allowlist
    
    def execute_write(self, path: str, content: str) -> None:
        if path not in self.allowed_paths:
            raise PermissionError(f"Path {path} not allowed")
        # Write logic...

# AFTER:
from shared.security.policy import HighRiskToolPolicy, SecurityMode
from shared.security.audit import AuditLogger

class FileWriteServer:
    def __init__(self, policy: HighRiskToolPolicy | None = None):
        self.policy = policy or HighRiskToolPolicy(
            allowed_paths=[],  # Config-driven
            mode=SecurityMode.FAIL_CLOSED,
        )
    
    def execute_write(self, path: str, content: str) -> None:
        if not self.policy.validate_path(path):
            AuditLogger.log_security_event("WRITE_DENIED", {"path": path})
            raise PermissionError(f"Path {path} not allowed")
        # Write logic...
```

### Details

- Policy is injected via constructor — allows configuration per instance.
- Audit logging captures denied requests — enables incident response.
- Fail-closed behavior enforced by `HighRiskToolPolicy.validate_*()` methods.

---

#### Part D: Update documentation

1. Search for documents describing security controls:
   ```bash
   rg -n "security.*profile\|allowlist\|denylist\|security.*lockdown" docs/
   ```
2. Update references to use unified terminology.

### Method

Part D — Update documentation:

```markdown
<!-- BEFORE -->
The agent uses `SecurityProfile` for access control.

<!-- AFTER -->
The agent uses the unified security module (`scripts/shared/security/`) for access control. See [Security Architecture](./security_architecture.md) for details.
```

### Details

- Documentation update is optional — only modify docs that explicitly describe security controls.
- Follows project convention — concise, direct sentences.

## Compatibility considerations

- Adding unified security module does not break existing code — original security controls remain accessible.
- Fail-closed behavior may change existing security outcomes — verify before deploying to production.
- Secret management protocol is backward compatible — existing secret handling continues to work.
- Audit logging addition does not affect runtime behavior — purely observability.

## Security considerations

- This plan introduces security controls — must be reviewed by security team before deployment.
- Fail-closed behavior prevents unauthorized access in production.
- Secret management protocol prohibits sensitive data in logs — follows best practices.
- Audit logging captures all security events — enables incident response.

## Rollback considerations

- Revert unified security module: delete `scripts/shared/security/`.
- Revert MCP server updates: restore original allowlist/denylist logic.
- Revert documentation updates: restore original text.
- No schema changes — rollback is purely code-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/shared/security/*.py | Unit: verify security controls work correctly | `uv run pytest tests/mcp*/ -v` | All pass |
| scripts/shared/security/*.py | Static type check | `uv run pyright scripts/shared/security/*.py` | 0 errors |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |
| Generated inventory | Manual verification against active configuration | Visual inspection | Inventory matches config |
| CI pipeline | Stale output detection | Trigger CI build | Warning displayed for stale output |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260818_06_issue.md
- Source requirement: requires/20260818-171800_require.md
- Source plan: plans/20260818-184804_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-214148
- Related target files: docs/**/*.md, scripts/mcp_servers/*.py
