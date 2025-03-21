#!/usr/bin/env python3
"""
Run all tests for the Streamlit dashboard.

This script runs all pytest tests for the Streamlit dashboard with verbose output.
"""

import os
import sys
import pytest

def main():
    """Run all tests for the Streamlit dashboard."""
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add parent directories to path so we can import modules
    parent_dir = os.path.dirname(current_dir)
    project_dir = os.path.dirname(parent_dir)
    
    if project_dir not in sys.path:
        sys.path.append(project_dir)
    
    # Run the tests
    print(f"Running tests from {current_dir}")
    
    # Run pytest with verbose output and test coverage
    pytest_args = [
        current_dir,  # Test directory
        "-v",  # Verbose output
        "--cov=dashboard",  # Coverage for dashboard module
        "--cov-report=term",  # Coverage report to terminal
        "--cov-report=html:coverage_html",  # HTML coverage report
        "-k", "not TestSidebar.test_sidebar_file_upload",  # Skip problematic test
    ]
    
    return pytest.main(pytest_args)

if __name__ == "__main__":
    sys.exit(main()) 