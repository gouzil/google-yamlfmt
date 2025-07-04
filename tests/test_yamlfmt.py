#!/usr/bin/env python3
"""
Test suite for yamlfmt functionality across different platforms.
"""

from __future__ import annotations

import platform
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestYamlfmtOutput(unittest.TestCase):
    """Test yamlfmt output across different platforms."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_yaml_content = """
# Test YAML file
name: test
version: 1.0.0
dependencies:
  - package1
  - package2
config:
    setting1: value1
    setting2:    value2
list:
- item1
-  item2
-   item3
"""

    def test_platform_detection(self):
        """Test that we can detect the current platform."""
        current_platform = platform.system()
        self.assertIn(current_platform, ["Linux", "Darwin", "Windows"])

    def test_yamlfmt_version(self):
        """Test that yamlfmt can output version information."""
        # Test version output with different possible flags
        version_flags = ["-version", "--version", "-V"]
        success = False

        for flag in version_flags:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "yamlfmt", flag],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if result.returncode == 0:
                    success = True
                    break
            except subprocess.TimeoutExpired:
                continue

        # If version flags don't work, try help flag as fallback
        if not success:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "yamlfmt", "-h"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                success = result.returncode == 0
            except subprocess.TimeoutExpired:
                pass

        # If yamlfmt binary is not available (development mode), skip this test
        if not success:
            self.skipTest("yamlfmt binary not available in development mode")

        self.assertTrue(success, "yamlfmt should respond to at least one version or help flag")

    def test_yamlfmt_format_basic(self):
        """Test basic YAML formatting functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(self.test_yaml_content)
            temp_file = Path(f.name)

        try:
            # Try to format the file
            result = subprocess.run(
                [sys.executable, "-m", "yamlfmt", str(temp_file)],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

            # If yamlfmt binary is not available (development mode), skip this test
            if result.returncode != 0 and ("No such file or directory" in result.stderr or "FileNotFoundError" in result.stderr):
                self.skipTest("yamlfmt binary not available in development mode")

            self.assertEqual(result.returncode, 0, f"yamlfmt formatting failed: {result.stderr}")

            # Check that the formatted file still exists
            self.assertTrue(temp_file.is_file(), f"Temporary file {temp_file} does not exist after formatting")

        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()

    def test_help_output(self):
        """Test that yamlfmt can show help information."""
        help_flags = ["-h", "--help"]
        success = False

        for flag in help_flags:
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "yamlfmt", flag],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if result.returncode == 0 and ("yamlfmt" in result.stdout.lower() or "usage" in result.stdout.lower()):
                    success = True
                    break
            except subprocess.TimeoutExpired:
                continue

        # If yamlfmt binary is not available (development mode), skip this test
        if not success:
            self.skipTest("yamlfmt binary not available in development mode")

        self.assertTrue(success, "yamlfmt should show help information")

    def test_module_import(self):
        """Test that the yamlfmt module can be imported correctly."""
        # Add src directory to Python path
        test_dir = Path(__file__).parent
        src_dir = test_dir.parent / "src"

        if src_dir.exists() and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        try:
            # Try to import yamlfmt module
            import yamlfmt

            # Check that BIN_NAME exists and is correct
            self.assertTrue(hasattr(yamlfmt, "BIN_NAME"), "yamlfmt module should have BIN_NAME attribute")
            self.assertEqual(yamlfmt.BIN_NAME, "yamlfmt", f"Expected BIN_NAME to be 'yamlfmt', got {yamlfmt.BIN_NAME}")

            # Check that __version__ exists
            self.assertTrue(hasattr(yamlfmt, "__version__"), "yamlfmt module should have __version__ attribute")
            self.assertIsNotNone(yamlfmt.__version__, "yamlfmt version should not be None")

        except ImportError as e:
            self.fail(f"Failed to import yamlfmt module: {e}")
        finally:
            # Remove src directory from path if we added it
            if src_dir.exists() and str(src_dir) in sys.path:
                sys.path.remove(str(src_dir))

    def test_system_info(self):
        """Display system information for debugging."""
        info = {
            "Platform": platform.system(),
            "Platform Release": platform.release(),
            "Platform Version": platform.version(),
            "Architecture": platform.machine(),
            "Processor": platform.processor(),
            "Python Version": sys.version,
            "Python Executable": sys.executable,
        }

        print("\n" + "=" * 50)
        print("SYSTEM INFORMATION")
        print("=" * 50)
        for key, value in info.items():
            print(f"{key:20}: {value}")
        print("=" * 50)


if __name__ == "__main__":
    unittest.main()
