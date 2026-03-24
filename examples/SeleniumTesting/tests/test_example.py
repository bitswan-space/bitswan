"""Example Selenium test — replace TARGET_URL with your deployment's public URL.

Get the URL with:
    bitswan-agent deployments list

The URL column shows the public URL for each deployment.
"""

import os
import pytest
from selenium.webdriver.common.by import By


# Set this to the public URL of the deployment you want to test.
# The coding agent should read this from `bitswan-agent deployments list`.
TARGET_URL = os.environ.get("TARGET_URL", "")


@pytest.mark.skipif(not TARGET_URL, reason="TARGET_URL not set")
def test_page_loads(browser):
    """Verify the deployment's public URL is reachable and returns a page."""
    browser.get(TARGET_URL)
    assert browser.title, f"Page at {TARGET_URL} has no title"


@pytest.mark.skipif(not TARGET_URL, reason="TARGET_URL not set")
def test_page_has_content(browser):
    """Verify the page has visible body content."""
    browser.get(TARGET_URL)
    body = browser.find_element(By.TAG_NAME, "body")
    assert body.text.strip(), f"Page at {TARGET_URL} has an empty body"
