"""
Unit and integration tests for spacing directives.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.analyzer import FileAnalyzer
from spacing.processor import FileProcessor
from spacing.types import BlockType


class TestDirectiveDetection:
  """Unit tests for directive detection in FileAnalyzer"""

  def test_basicSkipDirective(self):
    """Test basic # spacing: skip directive is detected and statement is marked"""

    analyzer = FileAnalyzer()
    lines = [
      '# spacing: skip',
      'x = 1',
      'y = 2',
    ]
    statements = analyzer.analyzeFile(lines)

    # Should have 3 statements (directive kept, both assignments marked)
    assert len(statements) == 3
    assert statements[0].isComment  # The directive comment
    assert statements[1].blockType == BlockType.ASSIGNMENT
    assert statements[1].skipBlankLineRules
    assert statements[2].blockType == BlockType.ASSIGNMENT
    assert statements[2].skipBlankLineRules

  def test_skipDirectiveCaseInsensitive(self):
    """Test directive works with various case combinations"""

    analyzer = FileAnalyzer()

    # Test uppercase
    lines = ['# SPACING: SKIP', 'x = 1']
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 2  # directive + marked statement
    assert statements[0].isComment
    assert statements[1].skipBlankLineRules

    # Test mixed case
    lines = ['# Spacing: Skip', 'x = 1']
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 2
    assert statements[0].isComment
    assert statements[1].skipBlankLineRules

    # Test lowercase no spaces
    lines = ['#spacing:skip', 'x = 1']
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 2
    assert statements[0].isComment
    assert statements[1].skipBlankLineRules

  def test_skipDirectiveWhitespaceVariations(self):
    """Test directive tolerates extra whitespace"""

    analyzer = FileAnalyzer()
    lines = [
      '#  spacing:  skip',
      'x = 1',
    ]
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 2  # directive + marked statement
    assert statements[0].isComment
    assert statements[1].skipBlankLineRules

  def test_skipDirectiveEndsAtBlankLine(self):
    """Test skip directive block ends at first blank line"""

    analyzer = FileAnalyzer()
    lines = [
      '# spacing: skip',
      'x = 1',
      'y = 2',
      '',
      'z = 3',
    ]
    statements = analyzer.analyzeFile(lines)

    # Directive, two marked assignments, blank line, then unmarked assignment
    assert len(statements) == 5
    assert statements[0].isComment  # directive

    assert statements[1].skipBlankLineRules  # x = 1
    assert statements[2].skipBlankLineRules  # y = 2

    assert statements[3].isBlank

    assert not statements[4].skipBlankLineRules  # z = 3

  def test_multipleSkipDirectives(self):
    """Test multiple skip directives in same file work independently"""

    analyzer = FileAnalyzer()
    lines = [
      '# spacing: skip',
      'a = 1',
      'b = 2',
      '',
      'c = 3',
      '',
      '# spacing: skip',
      'd = 4',
      'e = 5',
    ]
    statements = analyzer.analyzeFile(lines)

    # directive1, a, b marked; blank; c unmarked; blank; directive2, d, e marked
    assert len(statements) == 9
    assert statements[0].isComment  # directive 1

    assert statements[1].skipBlankLineRules  # a = 1
    assert statements[2].skipBlankLineRules  # b = 2

    assert statements[3].isBlank

    assert not statements[4].skipBlankLineRules  # c = 3

    assert statements[5].isBlank
    assert statements[6].isComment  # directive 2

    assert statements[7].skipBlankLineRules  # d = 4
    assert statements[8].skipBlankLineRules  # e = 5

  def test_skipDirectiveWithNoFollowingStatements(self):
    """Test skip directive at end of file with no following statements"""

    analyzer = FileAnalyzer()
    lines = [
      'x = 1',
      '# spacing: skip',
    ]
    statements = analyzer.analyzeFile(lines)

    # Should have the assignment and the directive (nothing to mark)
    assert len(statements) == 2

    assert not statements[0].skipBlankLineRules  # x = 1

    assert statements[1].isComment  # directive


class TestDirectiveIntegration:
  """Integration tests for directive behavior with full processing pipeline"""

  def test_basicSkipTwoStatements(self):
    """Test skip directive preserves spacing for two consecutive statements"""

    inputCode = """import sys
# spacing: skip
x = 1
y = 2

z = 3
"""

    # Directive is kept in output, x and y keep no blank lines between them
    expectedOutput = """import sys

# spacing: skip
x = 1
y = 2

z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipLongerBlock(self):
    """Test skip directive for block with 3+ statements"""

    inputCode = """import sys
# spacing: skip
x = 1
y = 2
z = 3

a = 4
"""
    expectedOutput = """import sys

# spacing: skip
x = 1
y = 2
z = 3

a = 4
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipEndsAtBlankLine(self):
    """Test skip directive block ends at first blank line (block = consecutive non-blank statements)"""

    inputCode = """import sys
# spacing: skip
x = 1

y = 2
z = 3
"""

    # Only x = 1 is in the skip block (ends at blank line)
    # y and z follow normal rules (no blank between assignments)
    expectedOutput = """import sys

# spacing: skip
x = 1

y = 2
z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipInNestedScope(self):
    """Test skip directive inside function/class"""

    inputCode = """def foo():
  import sys
  # spacing: skip
  x = 1
  y = 2

  z = 3
"""
    expectedOutput = """def foo():
  import sys

  # spacing: skip
  x = 1
  y = 2

  z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipMultipleBlocks(self):
    """Test multiple skip directives in same file"""

    inputCode = """import sys
# spacing: skip
a = 1
b = 2

import os
# spacing: skip
c = 3
d = 4
"""
    expectedOutput = """import sys

# spacing: skip
a = 1
b = 2

import os

# spacing: skip
c = 3
d = 4
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_directiveInDocstring(self):
    """Test directive inside docstring is ignored"""

    inputCode = '''def foo():
  """
  This is a docstring.
  # spacing: skip
  This should not activate the directive.
  """
  x = 1

  y = 2
'''

    # Directive in docstring is ignored - normal formatting rules apply
    # Blank line after docstring added, blank between assignments removed
    expectedOutput = '''def foo():
  """
  This is a docstring.
  # spacing: skip
  This should not activate the directive.
  """

  x = 1
  y = 2
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      # Changes should be made (directive in docstring is ignored)
      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_directiveInString(self):
    """Test directive inside regular string is ignored"""

    inputCode = """x = '# spacing: skip'
y = 1

z = 2
"""

    # Blank line between y and z should be removed normally
    expectedOutput = """x = '# spacing: skip'
y = 1
z = 2
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipWithDifferentBlockTypes(self):
    """Test skip directive works across different block types"""

    inputCode = """import os
# spacing: skip
import sys
x = 1
print(x)

y = 2
"""

    # import, assignment, call should have no blanks between them
    expectedOutput = """import os

# spacing: skip
import sys
x = 1
print(x)

y = 2
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_skipAtModuleLevel(self):
    """Test skip directive at module level"""

    inputCode = """# spacing: skip
import sys
import os

def foo():
  pass
"""

    # Imports should have no blank between them
    # But function should have proper spacing (2 blank lines)
    expectedOutput = """# spacing: skip
import sys
import os


def foo():
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedOutput

  def test_idempotency(self):
    """Test that processing a file with skip directive is idempotent"""

    inputCode = """import sys
# spacing: skip
x = 1
y = 2

z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      # First pass - should add blank line before directive
      changed1 = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed1

      # Second pass should not change anything
      changed2 = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert not changed2
