"""
Pytest configuration for E2E tests with Playwright.

These tests require a running frontend on localhost:3000.
They are skipped when the frontend is not available.
"""

import pytest
import socket
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


def is_frontend_available(host: str = "localhost", port: int = 3000) -> bool:
    """Check if frontend server is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


# Skip all e2e tests if frontend is not available
pytestmark = pytest.mark.skipif(
    not is_frontend_available(),
    reason="Frontend not available at localhost:3000. Start frontend to run E2E tests."
)


@pytest.fixture(scope="session")
def browser():
    """Launch browser for entire test session."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=["--disable-dev-shm-usage"],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """Create new browser context for each test."""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="en-US",
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """Create new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """
    Create authenticated page with demo user logged in.

    Uses the demo user account for testing.
    """
    base_url = "http://localhost:3000"

    # Navigate to login
    page.goto(f"{base_url}/login")

    # Fill login form
    page.fill('input[name="email"]', "user@demo.com")
    page.fill('input[name="password"]', "user123")

    # Submit form
    page.click('button[type="submit"]')

    # Wait for navigation to dashboard
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    yield page


@pytest.fixture(scope="function")
def admin_page(page: Page):
    """Create authenticated page with admin user."""
    base_url = "http://localhost:3000"

    page.goto(f"{base_url}/login")
    page.fill('input[name="email"]', "admin@demo.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard", timeout=5000)

    yield page


# Base URL constant
BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"
