"""Tests for role-based access control (RBAC) system."""
from unittest.mock import MagicMock

from src.core.permissions import (
    Permission,
    ROLE_PERMISSIONS,
    has_permission,
    has_any_permission,
    has_all_permissions,
    can_access_ticket,
    can_update_ticket,
    can_delete_ticket,
)


class TestRolePermissionsMapping:
    """Tests for ROLE_PERMISSIONS constant."""

    def test_user_role_permissions(self):
        """Test user role has correct permissions."""
        user_perms = ROLE_PERMISSIONS["user"]

        # User should have these
        assert Permission.TICKET_READ_OWN in user_perms
        assert Permission.TICKET_CREATE in user_perms
        assert Permission.TICKET_UPDATE_OWN in user_perms
        assert Permission.TICKET_DELETE_OWN in user_perms
        assert Permission.KB_READ in user_perms

        # User should NOT have these
        assert Permission.TICKET_READ_ALL not in user_perms
        assert Permission.TICKET_UPDATE_ALL not in user_perms
        assert Permission.TICKET_DELETE_ALL not in user_perms
        assert Permission.KB_CREATE not in user_perms
        assert Permission.KB_DELETE not in user_perms
        assert Permission.USER_READ not in user_perms
        assert Permission.TENANT_READ not in user_perms

    def test_agent_role_permissions(self):
        """Test agent role has correct permissions."""
        agent_perms = ROLE_PERMISSIONS["agent"]

        # Agent should have all user permissions
        for perm in ROLE_PERMISSIONS["user"]:
            assert perm in agent_perms

        # Agent should have additional permissions
        assert Permission.TICKET_READ_ALL in agent_perms
        assert Permission.TICKET_UPDATE_ALL in agent_perms
        assert Permission.TICKET_ASSIGN in agent_perms
        assert Permission.KB_CREATE in agent_perms
        assert Permission.KB_UPDATE in agent_perms
        assert Permission.ANALYTICS_VIEW in agent_perms

        # Agent should NOT have these
        assert Permission.TICKET_DELETE_ALL not in agent_perms
        assert Permission.KB_DELETE not in agent_perms
        assert Permission.USER_READ not in agent_perms
        assert Permission.TENANT_READ not in agent_perms

    def test_admin_role_permissions(self):
        """Test admin role has correct permissions."""
        admin_perms = ROLE_PERMISSIONS["admin"]

        # Admin should have most permissions
        assert Permission.USER_READ in admin_perms
        assert Permission.USER_CREATE in admin_perms
        assert Permission.USER_UPDATE in admin_perms
        assert Permission.USER_DELETE in admin_perms
        assert Permission.TICKET_READ_ALL in admin_perms
        assert Permission.TICKET_DELETE_ALL in admin_perms
        assert Permission.KB_DELETE in admin_perms
        assert Permission.KB_UPLOAD in admin_perms
        assert Permission.TENANT_READ in admin_perms
        assert Permission.TENANT_UPDATE in admin_perms
        assert Permission.TENANT_MANAGE_USERS in admin_perms
        assert Permission.ANALYTICS_EXPORT in admin_perms
        assert Permission.INTEGRATION_MANAGE in admin_perms

        # Admin should NOT have these
        assert Permission.TENANT_CREATE not in admin_perms
        assert Permission.TENANT_DELETE not in admin_perms
        assert Permission.SYSTEM_ADMIN not in admin_perms

    def test_superadmin_role_permissions(self):
        """Test superadmin role has all permissions."""
        superadmin_perms = ROLE_PERMISSIONS["superadmin"]

        # Superadmin should have all admin permissions
        for perm in ROLE_PERMISSIONS["admin"]:
            assert perm in superadmin_perms

        # Superadmin should have additional permissions
        assert Permission.TENANT_CREATE in superadmin_perms
        assert Permission.TENANT_DELETE in superadmin_perms
        assert Permission.SYSTEM_ADMIN in superadmin_perms

    def test_all_roles_defined(self):
        """Test all expected roles are defined."""
        expected_roles = ["user", "agent", "admin", "superadmin"]
        for role in expected_roles:
            assert role in ROLE_PERMISSIONS


class TestHasPermission:
    """Tests for has_permission function."""

    def _create_mock_user(self, role: str, is_active: bool = True):
        """Helper to create mock user."""
        user = MagicMock()
        user.role = role
        user.is_active = is_active
        user.id = 1
        return user

    def test_user_has_own_permission(self):
        """Test user has their role permissions."""
        user = self._create_mock_user("user")
        assert has_permission(user, Permission.TICKET_CREATE) is True
        assert has_permission(user, Permission.TICKET_READ_OWN) is True

    def test_user_lacks_higher_permission(self):
        """Test user lacks permissions from higher roles."""
        user = self._create_mock_user("user")
        assert has_permission(user, Permission.TICKET_READ_ALL) is False
        assert has_permission(user, Permission.USER_READ) is False

    def test_agent_has_user_permissions(self):
        """Test agent inherits user permissions."""
        agent = self._create_mock_user("agent")
        assert has_permission(agent, Permission.TICKET_CREATE) is True
        assert has_permission(agent, Permission.TICKET_READ_ALL) is True

    def test_admin_has_all_expected_permissions(self):
        """Test admin has expected permissions."""
        admin = self._create_mock_user("admin")
        assert has_permission(admin, Permission.USER_CREATE) is True
        assert has_permission(admin, Permission.KB_DELETE) is True
        assert has_permission(admin, Permission.TENANT_UPDATE) is True

    def test_superadmin_has_all_permissions(self):
        """Test superadmin has all permissions."""
        superadmin = self._create_mock_user("superadmin")
        assert has_permission(superadmin, Permission.SYSTEM_ADMIN) is True
        assert has_permission(superadmin, Permission.TENANT_CREATE) is True
        assert has_permission(superadmin, Permission.TENANT_DELETE) is True

    def test_inactive_user_has_no_permissions(self):
        """Test inactive user has no permissions."""
        user = self._create_mock_user("admin", is_active=False)
        assert has_permission(user, Permission.TICKET_CREATE) is False
        assert has_permission(user, Permission.USER_READ) is False

    def test_none_user_has_no_permissions(self):
        """Test None user has no permissions."""
        assert has_permission(None, Permission.TICKET_CREATE) is False

    def test_unknown_role_has_no_permissions(self):
        """Test unknown role has no permissions."""
        user = self._create_mock_user("unknown_role")
        assert has_permission(user, Permission.TICKET_CREATE) is False


class TestHasAnyPermission:
    """Tests for has_any_permission function."""

    def _create_mock_user(self, role: str):
        user = MagicMock()
        user.role = role
        user.is_active = True
        return user

    def test_user_has_any_of_multiple(self):
        """Test user has at least one of multiple permissions."""
        user = self._create_mock_user("user")
        permissions = [Permission.TICKET_CREATE, Permission.USER_READ]
        assert has_any_permission(user, permissions) is True

    def test_user_has_none_of_multiple(self):
        """Test user has none of the permissions."""
        user = self._create_mock_user("user")
        permissions = [Permission.USER_READ, Permission.TENANT_READ]
        assert has_any_permission(user, permissions) is False

    def test_admin_has_all_checked_permissions(self):
        """Test admin has all checked permissions."""
        admin = self._create_mock_user("admin")
        permissions = [Permission.USER_READ, Permission.KB_DELETE]
        assert has_any_permission(admin, permissions) is True


class TestHasAllPermissions:
    """Tests for has_all_permissions function."""

    def _create_mock_user(self, role: str):
        user = MagicMock()
        user.role = role
        user.is_active = True
        return user

    def test_user_has_all_own_permissions(self):
        """Test user has all their permissions."""
        user = self._create_mock_user("user")
        permissions = [Permission.TICKET_CREATE, Permission.KB_READ]
        assert has_all_permissions(user, permissions) is True

    def test_user_lacks_some_permissions(self):
        """Test user lacks some permissions."""
        user = self._create_mock_user("user")
        permissions = [Permission.TICKET_CREATE, Permission.USER_READ]
        assert has_all_permissions(user, permissions) is False

    def test_admin_has_all_admin_permissions(self):
        """Test admin has all admin permissions."""
        admin = self._create_mock_user("admin")
        permissions = [Permission.USER_READ, Permission.KB_DELETE, Permission.TENANT_UPDATE]
        assert has_all_permissions(admin, permissions) is True


class TestCanAccessTicket:
    """Tests for can_access_ticket function."""

    def _create_mock_user(self, role: str, user_id: int = 1):
        user = MagicMock()
        user.role = role
        user.is_active = True
        user.id = user_id
        return user

    def test_user_can_access_own_ticket(self):
        """Test user can access their own ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_access_ticket(user, ticket_user_id=1) is True

    def test_user_cannot_access_other_ticket(self):
        """Test user cannot access other's ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_access_ticket(user, ticket_user_id=2) is False

    def test_agent_can_access_any_ticket(self):
        """Test agent can access any ticket."""
        agent = self._create_mock_user("agent", user_id=1)
        assert can_access_ticket(agent, ticket_user_id=1) is True
        assert can_access_ticket(agent, ticket_user_id=999) is True

    def test_admin_can_access_any_ticket(self):
        """Test admin can access any ticket."""
        admin = self._create_mock_user("admin", user_id=1)
        assert can_access_ticket(admin, ticket_user_id=1) is True
        assert can_access_ticket(admin, ticket_user_id=999) is True


class TestCanUpdateTicket:
    """Tests for can_update_ticket function."""

    def _create_mock_user(self, role: str, user_id: int = 1):
        user = MagicMock()
        user.role = role
        user.is_active = True
        user.id = user_id
        return user

    def test_user_can_update_own_ticket(self):
        """Test user can update their own ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_update_ticket(user, ticket_user_id=1) is True

    def test_user_cannot_update_other_ticket(self):
        """Test user cannot update other's ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_update_ticket(user, ticket_user_id=2) is False

    def test_agent_can_update_any_ticket(self):
        """Test agent can update any ticket."""
        agent = self._create_mock_user("agent", user_id=1)
        assert can_update_ticket(agent, ticket_user_id=1) is True
        assert can_update_ticket(agent, ticket_user_id=999) is True


class TestCanDeleteTicket:
    """Tests for can_delete_ticket function."""

    def _create_mock_user(self, role: str, user_id: int = 1):
        user = MagicMock()
        user.role = role
        user.is_active = True
        user.id = user_id
        return user

    def test_user_can_delete_own_ticket(self):
        """Test user can delete their own ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_delete_ticket(user, ticket_user_id=1) is True

    def test_user_cannot_delete_other_ticket(self):
        """Test user cannot delete other's ticket."""
        user = self._create_mock_user("user", user_id=1)
        assert can_delete_ticket(user, ticket_user_id=2) is False

    def test_agent_cannot_delete_any_ticket(self):
        """Test agent cannot delete tickets (only update)."""
        agent = self._create_mock_user("agent", user_id=1)
        # Agent can delete own ticket (inherits from user)
        assert can_delete_ticket(agent, ticket_user_id=1) is True
        # But cannot delete other's tickets
        assert can_delete_ticket(agent, ticket_user_id=2) is False

    def test_admin_can_delete_any_ticket(self):
        """Test admin can delete any ticket."""
        admin = self._create_mock_user("admin", user_id=1)
        assert can_delete_ticket(admin, ticket_user_id=1) is True
        assert can_delete_ticket(admin, ticket_user_id=999) is True
