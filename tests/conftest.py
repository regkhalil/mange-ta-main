"""
Pytest configuration and shared fixtures for the test suite.
"""

import os
import sys
from pathlib import Path


def pytest_configure(config):
    """Configure pytest before running tests."""
    # Add root directory to Python path
    root_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(root_dir))

    # Disable Streamlit cache for tests
    os.environ["STREAMLIT_SERVER_ENABLE_STATIC_SERVING"] = "false"

    # Register custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
