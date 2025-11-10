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
  def testMultilineDocstringWithBlankLines(self):
    """Test that multiline docstrings with blank lines are preserved"""

    input_code = '''class AIService:
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change - docstring should be preserved as-is
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testMultilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and import"""

    input_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank line after docstring per PEP 257
      assert result == input_code
      assert not changed

  def testSingleQuoteDocstring(self):
    """Test that single-quoted docstrings are preserved"""

    input_code = """def my_function():
  '''
  This is a docstring with single quotes.
  
  It has blank lines inside.
  '''
  return 42
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testMultilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and import"""

    input_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank line after docstring per PEP 257
      assert result == input_code
      assert not changed

  def testDocstringWithHashSymbol(self):
    """Test that # symbols inside docstrings are not treated as comments"""

    input_code = '''def parse_markdown():
  """
  Parse markdown with headers.
  
  # This is not a comment, it's part of the docstring
  ## This is also part of the docstring
  
  Returns parsed content.
  """
  pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testMultilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and import"""

    input_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank line after docstring per PEP 257
      assert result == input_code
      assert not changed

  def testNestedQuotesInDocstring(self):
    """Test docstrings containing nested quotes"""

    input_code = '''def example():
  """
  This docstring contains "quotes" and 'apostrophes'.
  
  It also has a code example:
      print("Hello, world!")
  
  And it's preserved correctly.
  """
  pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should not change
      assert not changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == input_code

  def testMultilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and import"""

    input_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank line after docstring per PEP 257
      assert result == input_code
      assert not changed

  def testDocstringFollowedByCodeInFunctionBody(self):
    """Test that blank line is added between docstring and code per PEP 257"""

    # Ensure we're using default config (in case previous tests modified global config)
    from spacing.config import BlankLineConfig, setConfig

    setConfig(BlankLineConfig.fromDefaults())

    input_code = '''def __init__(self):
  """Initialize the AI service."""
  try:
    self.client = None
  except Exception:
    pass
'''
    expected_code = '''def __init__(self):
  """Initialize the AI service."""

  try:
    self.client = None
  except Exception:
    pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank line after docstring per PEP 257
      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code

  def testMultilineDocstringFollowedByImport(self):
    """Test that blank line is added after docstring per PEP 257 and import"""

    input_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank line after docstring per PEP 257
      assert result == input_code
      assert not changed

  def testRegularStatementsInFunctionBody(self):
    """Test that blank lines are added between different block types in function body"""

    input_code = """def func():
  x = "not a docstring"
  y = 42
  return x + str(y)
"""
    expected_code = """def func():
  x = "not a docstring"
  y = 42

  return x + str(y)
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Should add blank line between ASSIGNMENT (y = 42) and CALL (return)
      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code

  def testMultilineDocstringFollowedByImport(self):
    """Test blank lines after docstring and between different block types"""

    input_code = '''def suggestUserNeedId(featureFile):
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
    expected_code = '''def suggestUserNeedId(featureFile):
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # Should add blank lines: IMPORT->ASSIGNMENT and ASSIGNMENT->CALL
      # Should NOT add blank line after docstring
      assert result == expected_code
      assert changed

  def testNoBlankLineAfterAsyncDefBeforeDocstring(self):
    """Test that no blank line is added between async def and its docstring"""

    input_code = '''class Foo:
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
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected, f'Expected no blank before docstring\nGot:\n{result}'
