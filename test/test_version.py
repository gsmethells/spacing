"""
Test version functionality.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import subprocess
import sys
from spacing.cli import getVersion


class TestVersion:
  def testGetVersion(self):
    """Test that getVersion returns a version string"""

    ver = getVersion()

    # Should return something that looks like a version
    assert ver is not None
    assert isinstance(ver, str)
    assert len(ver) > 0

    # In development or installed, should not be 'unknown'
    assert 'unknown' not in ver or 'development' in ver

  def testVersionFlag(self):
    """Test that --version flag works from command line"""

    # Run spacing --version as a subprocess
    result = subprocess.run(
      [sys.executable, '-m', 'spacing.cli', '--version'],
      capture_output=True,
      text=True,
      cwd='src',  # Run from src directory
    )

    # Should exit successfully
    assert result.returncode == 0

    # Should output version string
    assert 'spacing' in result.stdout.lower()

    # Should have some version-like string
    output = result.stdout.strip()

    assert len(output) > 5  # At least "spacing X"

  def testVersionInHelp(self):
    """Test that --version is listed in help"""

    result = subprocess.run([sys.executable, '-m', 'spacing.cli', '--help'], capture_output=True, text=True, cwd='src')

    # Should exit successfully
    assert result.returncode == 0

    # Should mention --version in help
    assert '--version' in result.stdout
