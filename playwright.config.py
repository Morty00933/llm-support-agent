"""
Playwright configuration for E2E tests.
"""

import os

# Base URL for tests
BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:3000")
API_URL = os.getenv("E2E_API_URL", "http://localhost:8000")

# Browser settings
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SLOW_MO = int(os.getenv("SLOW_MO", "0"))  # Slow down operations by N ms

# Timeouts
DEFAULT_TIMEOUT = 30000  # 30 seconds
NAVIGATION_TIMEOUT = 30000

# Screenshots and videos
SCREENSHOT_ON_FAILURE = True
VIDEO_ON_FAILURE = True

# Browsers to test
BROWSERS = ["chromium"]  # Can add "firefox", "webkit"

# Viewport
VIEWPORT = {"width": 1280, "height": 720"}

# Locale
LOCALE = "en-US"
TIMEZONE = "America/New_York"
