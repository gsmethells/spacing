"""
Behavioral regression tests verifying formatter output is byte-for-byte correct.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.config import BlankLineConfig, setConfig
from spacing.processor import FileProcessor


def formatContent(content):
  """Write content to a temp file, run formatter in-place, and return the result.

  :type content: str
  :param content: Python source code to format
  :rtype: str
  :return: Formatted Python source code
  """

  with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(content)

    tmpPath = Path(f.name)

  FileProcessor.processFile(tmpPath, checkOnly=False)

  with open(tmpPath, encoding='utf-8') as f:
    result = f.read()

  tmpPath.unlink()

  return result


class TestRegressionFormatting:
  def setup_method(self):
    """Reset to default config before each test."""

    setConfig(BlankLineConfig.fromDefaults())

  def test_formatSimpleFile(self):
    """Verify blank lines between import/assignment/call transitions"""

    # Same block types get no blank; different types get 1 blank
    inputCode = 'import os\nimport sys\nx = 1\ny = 2\nprint(x)\nprint(y)\n'
    expected = 'import os\nimport sys\n\nx = 1\ny = 2\n\nprint(x)\nprint(y)\n'

    assert formatContent(inputCode) == expected

  def test_formatClassWithMethods(self):
    """Verify 1 blank line between nested method definitions (PEP 8)"""

    # No blanks between methods in input; formatter should add exactly 1
    inputCode = (
      'class MyClass:\n'
      '  def methodA(self):\n'
      '    return 1\n'
      '  def methodB(self):\n'
      '    return 2\n'
      '  def methodC(self):\n'
      '    return 3\n'
    )
    expected = (
      'class MyClass:\n'
      '  def methodA(self):\n'
      '    return 1\n'
      '\n'
      '  def methodB(self):\n'
      '    return 2\n'
      '\n'
      '  def methodC(self):\n'
      '    return 3\n'
    )

    assert formatContent(inputCode) == expected

  def test_formatNestedScopes(self):
    """Verify extra blank lines at scope starts are removed"""

    # Extra blank lines after def/for headers should be removed;
    # blank before return is kept (returning from nested level)
    inputCode = 'def outer():\n\n  x = 1\n\n  for i in range(10):\n\n    y = i * 2\n\n  return x\n'
    expected = 'def outer():\n  x = 1\n\n  for i in range(10):\n    y = i * 2\n\n  return x\n'

    assert formatContent(inputCode) == expected

  def test_formatModuleLevelDefinitions(self):
    """Verify PEP 8: 2 blank lines between module-level function and class definitions"""

    inputCode = 'def foo():\n  pass\n\ndef bar():\n  pass\n\nclass Baz:\n  pass\n'
    expected = 'def foo():\n  pass\n\n\ndef bar():\n  pass\n\n\nclass Baz:\n  pass\n'

    assert formatContent(inputCode) == expected

  def test_formatDocstrings(self):
    """Verify PEP 257: 1 blank line after class and method docstrings"""

    # No blank after docstrings in input; formatter should add them
    inputCode = (
      'class Foo:\n'
      '  """Class docstring."""\n'
      '  x = 1\n'
      '\n'
      '  def method(self):\n'
      '    """Method docstring."""\n'
      '    return self.x\n'
    )
    expected = (
      'class Foo:\n'
      '  """Class docstring."""\n'
      '\n'
      '  x = 1\n'
      '\n'
      '  def method(self):\n'
      '    """Method docstring."""\n'
      '\n'
      '    return self.x\n'
    )

    assert formatContent(inputCode) == expected

  def test_formatCommentsPreservation(self):
    """Verify 1 blank line is added before a comment that follows a non-comment"""

    # No blank before comment in input; formatter should add one
    inputCode = 'x = 1\n# section title\ny = 2\n'
    expected = 'x = 1\n\n# section title\ny = 2\n'

    assert formatContent(inputCode) == expected

  def test_formatSkipDirective(self):
    """Verify # spacing: skip prevents blank line insertion between consecutive statements"""

    # Without the skip directive, ASSIGNMENT→IMPORT would normally get 1 blank
    inputCode = '# spacing: skip\nx = 1\nimport os\ny = 2\n'
    expected = '# spacing: skip\nx = 1\nimport os\ny = 2\n'

    assert formatContent(inputCode) == expected

  def test_formatDecoratedDefinitions(self):
    """Verify decorators are grouped with their definition (2 blanks between module-level)"""

    inputCode = '@decorator\ndef foo():\n  pass\n@other_decorator\ndef bar():\n  pass\n'
    expected = '@decorator\ndef foo():\n  pass\n\n\n@other_decorator\ndef bar():\n  pass\n'

    assert formatContent(inputCode) == expected

  def test_formatSecondaryClause(self):
    """Verify no blank line is inserted before else/elif/except (secondary clauses)"""

    # Extra blank before else in input; formatter should remove it
    inputCode = 'if x > 0:\n  pass\n\nelse:\n  pass\n'
    expected = 'if x > 0:\n  pass\nelse:\n  pass\n'

    assert formatContent(inputCode) == expected

  def test_formatConsecutiveControl(self):
    """Verify 1 blank line between consecutive completed control blocks"""

    # No blank between if blocks in input; formatter should add 1
    inputCode = 'if x > 0:\n  a = 1\nif y > 0:\n  b = 2\n'
    expected = 'if x > 0:\n  a = 1\n\nif y > 0:\n  b = 2\n'

    assert formatContent(inputCode) == expected

  def test_importGroupSeparatorPreserved(self):
    """Verify blank line separating stdlib from third-party imports is preserved

    Regression test for issue #1: spacing was removing the import group separator,
    conflicting with ruff's I001 rule (isort / PEP 8 convention).
    """

    # Blank line between stdlib and third-party groups must not be removed
    inputCode = 'import os\nimport sys\n\nimport pytest\n'

    assert formatContent(inputCode) == inputCode

  def test_noBlankLineAddedBetweenSameGroupImports(self):
    """Verify spacing does not insert blank lines between imports that have none

    Complements test_importGroupSeparatorPreserved: the preserve logic must not
    create blank lines where none existed.
    """

    # No blank between imports → spacing must leave them as-is
    inputCode = 'import os\nimport sys\nimport pytest\n'

    assert formatContent(inputCode) == inputCode
