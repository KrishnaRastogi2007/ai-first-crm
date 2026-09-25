from enum import Enum, unique
from types import MappingProxyType


@unique
class Permission(str, Enum):
    """System permissions enforced across API endpoints."""

    USERS_READ = "users:read"

    HCP_READ = "hcps:read"
    HCP_CREATE = "hcps:create"
    HCP_UPDATE = "hcps:update"
    HCP_DELETE = "hcps:delete"

    INTERACTION_READ = "interactions:read"
    INTERACTION_CREATE = "interactions:create"
    INTERACTION_UPDATE = "interactions:update"
    INTERACTION_DELETE = "interactions:delete"

    FOLLOWUP_READ = "followups:read"
    FOLLOWUP_CREATE = "followups:create"
    FOLLOWUP_UPDATE = "followups:update"
    FOLLOWUP_DELETE = "followups:delete"

    AUDIT_READ = "audit:read"


ROLE_PERMISSIONS = MappingProxyType(
    {
        "admin": frozenset(
            {
                Permission.USERS_READ,

                Permission.HCP_READ,
                Permission.HCP_CREATE,
                Permission.HCP_UPDATE,
                Permission.HCP_DELETE,

                Permission.INTERACTION_READ,
                Permission.INTERACTION_CREATE,
                Permission.INTERACTION_UPDATE,
                Permission.INTERACTION_DELETE,

                Permission.FOLLOWUP_READ,
                Permission.FOLLOWUP_CREATE,
                Permission.FOLLOWUP_UPDATE,
                Permission.FOLLOWUP_DELETE,

                Permission.AUDIT_READ,
            }
        ),

        "sales_manager": frozenset(
            {
                Permission.USERS_READ,

                Permission.HCP_READ,
                Permission.HCP_CREATE,
                Permission.HCP_UPDATE,
                Permission.HCP_DELETE,

                Permission.INTERACTION_READ,
                Permission.INTERACTION_CREATE,
                Permission.INTERACTION_UPDATE,
                Permission.INTERACTION_DELETE,

                Permission.FOLLOWUP_READ,
                Permission.FOLLOWUP_CREATE,
                Permission.FOLLOWUP_UPDATE,
                Permission.FOLLOWUP_DELETE,
            }
        ),

        "field_representative": frozenset(
            {
                Permission.HCP_READ,
                Permission.HCP_CREATE,
                Permission.HCP_UPDATE,
                Permission.HCP_DELETE,

                Permission.INTERACTION_READ,
                Permission.INTERACTION_CREATE,
                Permission.INTERACTION_UPDATE,

                Permission.FOLLOWUP_READ,
                Permission.FOLLOWUP_CREATE,
                Permission.FOLLOWUP_UPDATE,
            }
        ),

        "compliance_officer": frozenset(
            {
                Permission.AUDIT_READ,
            }
        ),
    }
)


def has_permission(role: str,permission: Permission) -> bool:
    """Helper utility to check if a given role possesses a specific permission."""

    return (role in ROLE_PERMISSIONS and  permission in ROLE_PERMISSIONS[role])