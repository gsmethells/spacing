"""
Test docstring preservation.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.config import BlankLineConfig, setConfig
from spacing.processor import FileProcessor


class TestDocstringPreservation:
  def test_multilineDocstringWithBlankLines(self):
    """Test that multiline docstrings with blank lines are preserved"""

    inputCode = '''class AIService:
  """
  **DESIGN REFERENCE: Layer 0: Foundational Services - LLM Service**

  Encapsulates all interactions with the AI model (Gemini).
  This service provides AI-powered functionality for User Need determination, functional statement generation,
  and Design Input matching used by the Builder Service and other specialized services.

  Architecture: Layer 0 - Foundational Services
  """

  def __init__(self):
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change - docstring should be preserved as-is
      assert not changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == inputCode

  def test_multilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and between block types"""

    inputCode = '''def suggestUserNeedId(featureFile):
    """
    Suggests the most appropriate User Need ID.

    Returns:
      tuple[str|None, float]: A tuple containing the suggested User Need ID
      (or None) and the confidence score (0.0 to 1.0).
    """
    from fcheck.parser.featureextractor import extractCompleteFeatureData
    result_un_id = None
    return result_un_id, 0.0
'''
    expectedCode = '''def suggestUserNeedId(featureFile):
    """
    Suggests the most appropriate User Need ID.

    Returns:
      tuple[str|None, float]: A tuple containing the suggested User Need ID
      (or None) and the confidence score (0.0 to 1.0).
    """

    from fcheck.parser.featureextractor import extractCompleteFeatureData

    result_un_id = None

    return result_un_id, 0.0
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      # Should add blank lines: after docstring, between import/assignment/return
      assert changed
      assert result == expectedCode

  def test_singleQuoteDocstring(self):
    """Test that single-quoted docstrings are preserved"""

    # Set afterDocstring = 0 for this test (compact docstring formatting)
    from spacing.config import BlankLineConfig, setConfig

    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    inputCode = """def my_function():
  '''
  This is a docstring with single quotes.

  It has blank lines inside.
  '''
  return 42
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == inputCode

  def test_docstringWithHashSymbol(self):
    """Test that # symbols inside docstrings are not treated as comments"""

    # Set afterDocstring = 0 for this test (compact docstring formatting)
    from spacing.config import BlankLineConfig, setConfig

    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    inputCode = '''def parse_markdown():
  """
  Parse markdown with headers.

  # This is not a comment, it's part of the docstring
  ## This is also part of the docstring

  Returns parsed content.
  """
  pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == inputCode

  def test_nestedQuotesInDocstring(self):
    """Test docstrings containing nested quotes"""

    # Set afterDocstring = 0 for this test (compact docstring formatting)
    from spacing.config import BlankLineConfig, setConfig

    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    inputCode = '''def example():
  """
  This docstring contains "quotes" and 'apostrophes'.

  It also has a code example:
      print("Hello, world!")

  And it's preserved correctly.
  """
  pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == inputCode

  def test_docstringFollowedByCodeInFunctionBody(self):
    """Test that blank line is added between docstring and code per PEP 257"""

    # Ensure we're using default config (in case previous tests modified global config)
    from spacing.config import BlankLineConfig, setConfig

    setConfig(BlankLineConfig.fromDefaults())

    inputCode = '''def __init__(self):
  """Initialize the AI service."""
  try:
    self.client = None
  except Exception:
    pass
'''
    expectedCode = '''def __init__(self):
  """Initialize the AI service."""

  try:
    self.client = None
  except Exception:
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank line after docstring per PEP 257
      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode

  def test_regularStatementsInFunctionBody(self):
    """Test that blank lines are added between different block types in function body"""

    inputCode = """def func():
  x = "not a docstring"
  y = 42
  return x + str(y)
"""
    expectedCode = """def func():
  x = "not a docstring"
  y = 42

  return x + str(y)
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank line between ASSIGNMENT (y = 42) and CALL (return)
      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode

  def test_multilineDocstringFollowedByImportCompactDocstring(self):
    """Test blank lines after docstring and between different block types with afterDocstring=0"""

    # Set afterDocstring = 0 for this test (compact docstring formatting)
    from spacing.config import BlankLineConfig, setConfig

    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    inputCode = '''def suggestUserNeedId(featureFile):
    """
    Suggests the most appropriate User Need ID.

    Returns:
      tuple[str|None, float]: A tuple containing the suggested User Need ID
      (or None) and the confidence score (0.0 to 1.0).
    """
    from fcheck.parser.featureextractor import extractCompleteFeatureData
    result_un_id = None
    return result_un_id, 0.0
'''
    expectedCode = '''def suggestUserNeedId(featureFile):
    """
    Suggests the most appropriate User Need ID.

    Returns:
      tuple[str|None, float]: A tuple containing the suggested User Need ID
      (or None) and the confidence score (0.0 to 1.0).
    """
    from fcheck.parser.featureextractor import extractCompleteFeatureData

    result_un_id = None

    return result_un_id, 0.0
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      # Should add blank lines: IMPORT->ASSIGNMENT and ASSIGNMENT->CALL
      # Should NOT add blank line after docstring
      assert result == expectedCode
      assert changed

  def test_noBlankLineAfterAsyncDefBeforeDocstring(self):
    """Test that no blank line is added between async def and its docstring"""

    inputCode = '''class Foo:
  async def method(self):
    """Docstring"""
    pass
'''

    # Should not add blank line between async def and docstring
    expected = '''class Foo:
  async def method(self):
    """Docstring"""

    pass
'''
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expected, f'Expected no blank before docstring\nGot:\n{result}'

  def test_moduleLevelDocstringAlwaysHasBlankLineAfter(self):
    """Test that module-level docstrings ALWAYS have blank line after them (PEP 257)"""

    inputCode = '''"""
This is a module-level docstring.
"""
import sys

x = 1
'''
    expected = '''"""
This is a module-level docstring.
"""

import sys

x = 1
'''

    # Use default config (after_docstring = 1)
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expected, f'Expected blank line after module docstring\nGot:\n{result}'

  def test_moduleLevelDocstringWithAfterDocstringZero(self):
    """Test that module-level docstrings ALWAYS have blank line even with after_docstring=0"""

    inputCode = '''"""
This is a module-level docstring.
It should have a blank line after it regardless of after_docstring config.
"""
import sys

def foo():
  """Function docstring should NOT have blank line with after_docstring=0"""
  return 42
'''
    expected = '''"""
This is a module-level docstring.
It should have a blank line after it regardless of after_docstring config.
"""

import sys


def foo():
  """Function docstring should NOT have blank line with after_docstring=0"""
  return 42
'''

    # Configure after_docstring = 0
    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expected, f'Module docstring should have blank line even with after_docstring=0\nGot:\n{result}'

    # Reset to defaults
    setConfig(BlankLineConfig.fromDefaults())

  def test_moduleLevelDocstringFollowedByDefinition(self):
    """Test module-level docstring followed by top-level definition"""

    inputCode = '''"""Module docstring."""
def foo():
  pass
'''
    expected = '''"""Module docstring."""


def foo():
  pass
'''
    config = BlankLineConfig.fromDefaults()

    setConfig(config)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expected, (
        f'Module docstring should have blank line, then PEP 8 spacing before def\nGot:\n{result}'
      )
