"""
Pytest configuration for spacing tests.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import pytest


@pytest.fixture(autouse=True)
def resetConfig():
  """Reset global config singleton before each test to ensure test isolation"""

  from spacing.config import BlankLineConfig, setConfig

  # Reset to default values before each test
  setConfig(BlankLineConfig.fromDefaults())

  yield

  # Reset again after test completes
  setConfig(BlankLineConfig.fromDefaults())
