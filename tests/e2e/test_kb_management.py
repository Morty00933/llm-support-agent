"""
E2E tests for Knowledge Base management.
"""

import pytest
from playwright.sync_api import Page, expect
from .conftest import BASE_URL, is_frontend_available

pytestmark = pytest.mark.skipif(
    not is_frontend_available(),
    reason="Frontend not available at localhost:3000"
)


class TestKnowledgeBase:
    """Test Knowledge Base functionality."""

    def test_view_kb_chunks(self, authenticated_page: Page):
        """Test viewing KB chunks list."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/kb")

        # Should see KB page
        expect(page.locator("h1")).to_contain_text("Knowledge Base")

        # Should see chunks list
        chunks = page.locator('[data-testid="kb-chunk"]')
        expect(chunks.first).to_be_visible()

    def test_add_kb_chunk_manually(self, authenticated_page: Page):
        """Test adding KB chunk through UI."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/kb")

        # Click add button
        page.click('button:has-text("Add Content")')

        # Fill form
        page.fill('textarea[name="content"]', "This is test KB content about refund policy.")
        page.fill('input[name="source"]', "test-manual")

        # Submit
        page.click('button[type="submit"]:has-text("Save")')

        # Wait for success message
        success = page.locator('[role="status"]')
        expect(success).to_be_visible()
        expect(success).to_contain_text("added successfully")

    def test_upload_document_to_kb(self, authenticated_page: Page):
        """Test uploading a document to KB."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/kb/upload")

        # Select file to upload
        page.set_input_files('input[type="file"]', "tests/fixtures/sample.txt")

        # Fill source
        page.fill('input[name="source"]', "uploaded-doc")

        # Submit upload
        page.click('button[type="submit"]:has-text("Upload")')

        # Wait for processing
        page.wait_for_timeout(2000)

        # Should show success
        success = page.locator('[role="status"]')
        expect(success).to_contain_text("uploaded successfully")

    def test_search_kb(self, authenticated_page: Page):
        """Test semantic search in KB."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/kb")

        # Fill search box
        page.fill('input[name="search"]', "how to reset password")

        # Submit search
        page.press('input[name="search"]', "Enter")

        # Wait for results
        page.wait_for_timeout(1000)

        # Should show relevant results
        results = page.locator('[data-testid="search-result"]')
        expect(results.first).to_be_visible()

        # Results should contain relevant content
        expect(results.first).to_contain_text("password")

    def test_delete_kb_source(self, admin_page: Page):
        """Test deleting all chunks from a source (admin only)."""
        page = admin_page

        page.goto(f"{BASE_URL}/kb")

        # Find source to delete
        source_item = page.locator('[data-testid="kb-source"]').first

        # Click delete button
        source_item.locator('button:has-text("Delete")').click()

        # Confirm deletion
        page.click('button:has-text("Confirm")')

        # Wait for deletion
        page.wait_for_timeout(1000)

        # Should show success message
        expect(page.locator('[role="status"]')).to_contain_text("deleted")


class TestAIPlayground:
    """Test AI Playground functionality."""

    def test_ask_ai_question(self, authenticated_page: Page):
        """Test asking question in AI playground."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/playground")

        # Fill question
        page.fill('textarea[name="question"]', "How do I reset my password?")

        # Submit
        page.click('button:has-text("Ask AI")')

        # Wait for response (max 10 seconds)
        response = page.locator('[data-testid="ai-response"]')
        expect(response).to_be_visible(timeout=10000)

        # Should contain helpful response
        expect(response).not_to_be_empty()

    def test_playground_history(self, authenticated_page: Page):
        """Test that playground shows conversation history."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/playground")

        # Ask first question
        page.fill('textarea[name="question"]', "What are your support hours?")
        page.click('button:has-text("Ask AI")')
        page.wait_for_timeout(3000)

        # Ask second question
        page.fill('textarea[name="question"]', "Do you offer 24/7 support?")
        page.click('button:has-text("Ask AI")')
        page.wait_for_timeout(3000)

        # Should show both questions and responses
        messages = page.locator('[data-testid="chat-message"]')
        expect(messages).to_have_count(4)  # 2 questions + 2 responses

    def test_clear_playground_history(self, authenticated_page: Page):
        """Test clearing playground conversation."""
        page = authenticated_page

        page.goto(f"{BASE_URL}/playground")

        # Ask a question
        page.fill('textarea[name="question"]', "Test question")
        page.click('button:has-text("Ask AI")')
        page.wait_for_timeout(2000)

        # Clear history
        page.click('button:has-text("Clear")')

        # Verify history is empty
        messages = page.locator('[data-testid="chat-message"]')
        expect(messages).to_have_count(0)
