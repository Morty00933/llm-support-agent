"""
E2E tests for authentication flow.
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import BASE_URL, is_frontend_available

pytestmark = pytest.mark.skipif(
    not is_frontend_available(),
    reason="Frontend not available at localhost:3000"
)


class TestAuthenticationFlow:
    """Test user authentication flows."""

    def test_login_success(self, page: Page):
        """Test successful login with valid credentials."""
        # Navigate to login page
        page.goto(f"{BASE_URL}/login")

        # Check page loaded
        expect(page).to_have_title("LLM Support Agent")

        # Fill login form
        page.fill('input[name="email"]', "user@demo.com")
        page.fill('input[name="password"]', "user123")

        # Submit form
        page.click('button[type="submit"]')

        # Should redirect to dashboard
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)

        # Verify we're on dashboard
        expect(page.locator("h1")).to_contain_text("Dashboard")

    def test_login_invalid_credentials(self, page: Page):
        """Test login with invalid credentials shows error."""
        page.goto(f"{BASE_URL}/login")

        page.fill('input[name="email"]', "invalid@example.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        # Should show error message
        error = page.locator('[role="alert"]')
        expect(error).to_be_visible()
        expect(error).to_contain_text("Invalid credentials")

    def test_logout(self, authenticated_page: Page):
        """Test logout functionality."""
        page = authenticated_page

        # Find and click logout button/link
        page.click('button:has-text("Logout")')

        # Should redirect to login
        page.wait_for_url(f"{BASE_URL}/login", timeout=5000)

    def test_protected_route_redirect(self, page: Page):
        """Test that protected routes redirect to login."""
        # Try to access dashboard without login
        page.goto(f"{BASE_URL}/dashboard")

        # Should redirect to login
        page.wait_for_url(f"{BASE_URL}/login", timeout=5000)

    def test_register_new_user(self, page: Page):
        """Test user registration flow."""
        page.goto(f"{BASE_URL}/register")

        # Fill registration form
        page.fill('input[name="email"]', f"test{page.url}@example.com")
        page.fill('input[name="password"]', "testpassword123")
        page.fill('input[name="full_name"]', "Test User")

        page.click('button[type="submit"]')

        # Should redirect to dashboard or login
        page.wait_for_url([f"{BASE_URL}/dashboard", f"{BASE_URL}/login"], timeout=5000)


class TestRoleBasedAccess:
    """Test role-based access control."""

    def test_admin_can_access_admin_panel(self, admin_page: Page):
        """Test that admin user can access admin features."""
        page = admin_page

        # Navigate to users management (admin only)
        page.goto(f"{BASE_URL}/admin/users")

        # Should not see 403 error
        expect(page.locator("h1")).not_to_contain_text("Forbidden")

    def test_user_cannot_access_admin_panel(self, authenticated_page: Page):
        """Test that regular user cannot access admin features."""
        page = authenticated_page

        # Try to navigate to admin panel
        page.goto(f"{BASE_URL}/admin/users")

        # Should show forbidden or redirect
        page.wait_for_timeout(1000)
        # Check for either 403 page or redirect
        assert page.url == f"{BASE_URL}/dashboard" or "403" in page.content()
