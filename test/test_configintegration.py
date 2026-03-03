"""
Integration tests for configuration system with file processing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.config import BlankLineConfig, setConfig
from spacing.processor import FileProcessor
from spacing.types import BlockType


class TestConfigurationIntegration:
  def test_defaultConfigurationBehavior(self):
    """Test that default configuration produces PEP 8 compliant behavior"""

    inputCode = """import sys
x = 1
def func():
  pass
if True:
  pass
"""

    # PEP 8: 2 blank lines around module-level definitions
    expectedOutput = """import sys

x = 1


def func():
  pass


if True:
  pass
"""
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_zeroBlankLinesConfiguration(self):
    """Test custom configuration with 0 blank lines between different types (PEP 8 rules still apply)"""

    inputCode = """import sys

x = 1

def func():
  pass

if True:
  pass

"""

    # With 0 blank lines, removes blank lines between non-definition types
    # BUT PEP 8 rule for module-level definitions still applies (2 blank lines)
    expectedOutput = """import sys
x = 1


def func():
  pass


if True:
  pass
"""
    config = BlankLineConfig(defaultBetweenDifferent=0)

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_twoBlankLinesConfiguration(self):
    """Test custom configuration with 2 blank lines between different types"""

    inputCode = """import sys
x = 1
def func():
  pass
"""

    # With 2 blank lines config, adds 2 blank lines between different types
    # Module-level definitions also get 2 blank lines (PEP 8)
    expectedOutput = """import sys


x = 1


def func():
  pass
"""
    config = BlankLineConfig(defaultBetweenDifferent=2)

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_specificTransitionOverrides(self):
    """Test specific transition overrides work correctly"""

    inputCode = """import sys
x = 1
print(x)
def func():
  pass
"""

    # Transition overrides: assignment->call = 0, import->assignment = 2
    # PEP 8 still applies: module-level definition gets 2 blank lines
    expectedOutput = """import sys


x = 1
print(x)


def func():
  pass
"""
    config = BlankLineConfig(
      defaultBetweenDifferent=1,
      transitions={
        (BlockType.ASSIGNMENT, BlockType.CALL): 0,  # x=1 -> print(x): no blank line
        (BlockType.IMPORT, BlockType.ASSIGNMENT): 2,  # import -> x=1: 2 blank lines
      },
    )

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_consecutiveControlConfiguration(self):
    """Test consecutive control configuration works"""

    inputCode = """if condition1:
  pass
if condition2:
  pass
"""

    # Change to 2 blank lines between consecutive control blocks
    expectedOutput = """if condition1:
  pass


if condition2:
  pass
"""
    config = BlankLineConfig(consecutiveControl=2)

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_consecutiveDefinitionConfiguration(self):
    """Test consecutive definition configuration works at nested level"""

    # Use nested definitions to avoid PEP 8 module-level 2-blank-line rule
    inputCode = """class Foo:
  def func1(self):
    pass

  def func2(self):
    pass
"""

    # Change to 0 blank lines between consecutive nested definitions
    expectedOutput = """class Foo:
  def func1(self):
    pass
  def func2(self):
    pass
"""
    config = BlankLineConfig(consecutiveDefinition=0)

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_compactStyleConfiguration(self):
    """Test compact style with minimal blanks between block types"""

    inputCode = """import sys
from os import path

x = 1
y = 2

print(x)
print(y)

def func():
  pass
"""

    # Compact style: no blanks between different block types (except PEP 8 rules)
    # Statements of same type still group together automatically
    config = BlankLineConfig(
      defaultBetweenDifferent=0,  # No blanks between different block types
    )

    # Expected: all blocks tight together, except module-level def gets PEP 8's 2 blanks
    expectedOutput = """import sys
from os import path
x = 1
y = 2
print(x)
print(y)


def func():
  pass
"""

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_configurationDoesNotChangeAlreadyCorrectFile(self):
    """Test that correctly formatted files are not changed"""

    # This input is already correctly formatted with default config (PEP 8)
    inputCode = """import sys

x = 1

print(x)


def func():
  pass
"""
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      # Should return False (no changes needed)
      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      # Content should be unchanged
      assert result == inputCode

  def test_afterDocstringConfiguration(self):
    """Test afterDocstring configuration controls blank lines after docstrings"""

    inputCode = '''def func():
  """This is a docstring"""
  pass
'''

    # Test with default (1 blank line after docstring)
    expectedWithBlank = '''def func():
  """This is a docstring"""

  pass
'''
    configDefault = BlankLineConfig.fromDefaults()

    setConfig(configDefault)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedWithBlank

    # Test with afterDocstring=0 (no blank line after docstring)
    expectedNoBlank = '''def func():
  """This is a docstring"""
  pass
'''
    configCompact = BlankLineConfig(afterDocstring=0)

    setConfig(configCompact)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not changed  # No changes needed since input already matches config

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedNoBlank

  def test_classDocstringAlwaysHasBlankLine(self):
    """Regression test: Class docstrings must always have 1 blank line before first method, regardless of afterDocstring config"""

    # Test with afterDocstring=0 (compact mode for function docstrings)
    configCompact = BlankLineConfig(afterDocstring=0)

    setConfig(configCompact)

    inputCode = '''class MessageServer:
  """Message server."""
  def __init__(self):
    pass
'''
    expectedOutput = '''class MessageServer:
  """Message server."""

  def __init__(self):
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed  # Should add blank line after class docstring

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

    # Verify function docstrings still respect afterDocstring=0
    functionInput = '''def foo():
  """Foo function."""

  return 42
'''
    functionExpected = '''def foo():
  """Foo function."""
  return 42
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(functionInput)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed  # Should remove blank line after function docstring

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == functionExpected
