"""
E2E tests for ticket management workflow.
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import BASE_URL, is_frontend_available

pytestmark = pytest.mark.skipif(
    not is_frontend_available(),
    reason="Frontend not available at localhost:3000"
)


class TestTicketCreation:
    """Test ticket creation and management."""

    def test_create_ticket_with_ai_response(self, authenticated_page: Page):
        """Test creating a ticket and receiving AI auto-response."""
        page = authenticated_page

        # Navigate to new ticket page
        page.goto(f"{BASE_URL}/tickets/new")

        # Fill ticket form
        page.fill('input[name="title"]', "How do I reset my password?")
        page.fill('textarea[name="description"]', "I forgot my password and need help.")

        # Select priority
        page.select_option('select[name="priority"]', "medium")

        # Submit form
        page.click('button[type="submit"]:has-text("Create")')

        # Wait for redirect to ticket detail
        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Verify ticket was created
        expect(page.locator("h1")).to_contain_text("How do I reset my password?")

        # Wait for AI response (max 10 seconds)
        ai_response = page.locator('[data-testid="ai-message"]').first
        expect(ai_response).to_be_visible(timeout=10000)

        # Verify AI response contains helpful content
        expect(ai_response).to_contain_text("password")

    def test_create_ticket_without_auto_response(self, authenticated_page: Page):
        """Test creating ticket with auto-response disabled."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets/new")

        page.fill('input[name="title"]', "Manual ticket without AI")
        page.fill('textarea[name="description"]', "This should not trigger AI.")

        # Uncheck auto-response checkbox
        page.uncheck('input[name="auto_respond"]')

        page.click('button[type="submit"]:has-text("Create")')

        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Should not have AI response
        ai_messages = page.locator('[data-testid="ai-message"]')
        expect(ai_messages).to_have_count(0)

    def test_list_tickets(self, authenticated_page: Page):
        """Test viewing list of tickets."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")

        # Should see tickets list
        expect(page.locator("h1")).to_contain_text("Tickets")

        # Should have at least one ticket (from previous tests or demo data)
        tickets = page.locator('[data-testid="ticket-item"]')
        expect(tickets.first).to_be_visible(timeout=5000)

    def test_filter_tickets_by_status(self, authenticated_page: Page):
        """Test filtering tickets by status."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")

        # Select open status
        page.select_option('select[name="status"]', "open")

        # Wait for filtered results
        page.wait_for_timeout(1000)

        # Verify URL includes filter
        assert "status=open" in page.url

    def test_search_tickets(self, authenticated_page: Page):
        """Test searching tickets."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")

        # Fill search box
        page.fill('input[name="search"]', "password")

        # Submit search
        page.press('input[name="search"]', "Enter")

        # Wait for results
        page.wait_for_timeout(1000)

        # Should show filtered results
        tickets = page.locator('[data-testid="ticket-item"]')
        expect(tickets.first).to_be_visible()


class TestTicketDetail:
    """Test ticket detail page and interactions."""

    def test_view_ticket_detail(self, authenticated_page: Page):
        """Test viewing a ticket's full details."""
        page = authenticated_page

        # Go to tickets list
        page.goto(f"{BASE_URL}/tickets")

        # Click first ticket
        page.locator('[data-testid="ticket-item"]').first.click()

        # Should navigate to detail page
        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Should see ticket title
        expect(page.locator("h1")).to_be_visible()

        # Should see messages section
        expect(page.locator('[data-testid="messages"]')).to_be_visible()

    def test_add_message_to_ticket(self, authenticated_page: Page):
        """Test adding a message to existing ticket."""
        page = authenticated_page

        # Navigate to any ticket
        page.goto(f"{BASE_URL}/tickets")
        page.locator('[data-testid="ticket-item"]').first.click()
        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Find message input
        message_input = page.locator('textarea[name="message"]')
        message_input.fill("This is a follow-up message")

        # Submit message
        page.click('button:has-text("Send")')

        # Wait for message to appear
        page.wait_for_timeout(1000)

        # Verify message was added
        messages = page.locator('[data-testid="message"]')
        expect(messages.last).to_contain_text("This is a follow-up message")

    def test_update_ticket_status(self, authenticated_page: Page):
        """Test changing ticket status."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")
        page.locator('[data-testid="ticket-item"]').first.click()
        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Change status to resolved
        page.select_option('select[name="status"]', "resolved")

        # Submit change
        page.click('button:has-text("Update")')

        # Wait for update
        page.wait_for_timeout(1000)

        # Verify status badge updated
        status_badge = page.locator('[data-testid="status-badge"]')
        expect(status_badge).to_contain_text("Resolved")


class TestTicketPermissions:
    """Test ticket access permissions."""

    def test_user_can_view_own_tickets(self, authenticated_page: Page):
        """Test that user can view their own tickets."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")

        # Should see their tickets
        tickets = page.locator('[data-testid="ticket-item"]')
        expect(tickets.first).to_be_visible()

    def test_user_cannot_delete_other_tickets(self, authenticated_page: Page):
        """Test that user cannot delete tickets they don't own."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/tickets")
        page.locator('[data-testid="ticket-item"]').first.click()
        page.wait_for_url(f"{BASE_URL}/tickets/*", timeout=5000)

        # Delete button should not be visible for other users' tickets
        # Or clicking it should show an error
        delete_button = page.locator('button:has-text("Delete")')

        if delete_button.is_visible():
            delete_button.click()

            # Should show error
            error = page.locator('[role="alert"]')
            expect(error).to_contain_text("Permission denied")
