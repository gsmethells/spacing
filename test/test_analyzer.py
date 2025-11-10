"""
Unit tests for file analyzer.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.analyzer import FileAnalyzer
from spacing.types import BlockType


class TestFileAnalyzer:
  def testAnalyzeSimpleStatements(self):
    """Test analysis of simple single-line statements"""

    analyzer = FileAnalyzer()
    lines = [
      'import sys',
      'x = 1',
      'print(x)',
    ]
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 3
    assert statements[0].blockType == BlockType.IMPORT
    assert statements[1].blockType == BlockType.ASSIGNMENT
    assert statements[2].blockType == BlockType.CALL

  def testAnalyzeBlankLines(self):
    """Test handling of blank lines"""

    analyzer = FileAnalyzer()
    lines = [
      'x = 1',
      '',
      'y = 2',
    ]
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 3
    assert statements[0].blockType == BlockType.ASSIGNMENT
    assert statements[1].isBlank
    assert statements[2].blockType == BlockType.ASSIGNMENT

  def testAnalyzeComments(self):
    """Test handling of comment lines"""

    analyzer = FileAnalyzer()
    lines = [
      'x = 1',
      '# This is a comment',
      'y = 2',
    ]
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 3
    assert statements[0].blockType == BlockType.ASSIGNMENT
    assert statements[1].isComment
    assert statements[2].blockType == BlockType.ASSIGNMENT

  def testAnalyzeMultilineStatement(self):
    """Test analysis of multiline statements"""

    analyzer = FileAnalyzer()
    lines = [
      'result = func(',
      '  arg1,',
      '  arg2',
      ')',
      'x = 1',
    ]
    statements = analyzer.analyzeFile(lines)

    assert len(statements) == 2

    # First statement should be the complete multiline assignment
    assert statements[0].blockType == BlockType.ASSIGNMENT
    assert statements[0].startLineIndex == 0
    assert statements[0].endLineIndex == 3
    assert len(statements[0].lines) == 4

    # Second statement is single line
    assert statements[1].blockType == BlockType.ASSIGNMENT
    assert statements[1].startLineIndex == 4
    assert statements[1].endLineIndex == 4

  def testIndentationLevel(self):
    """Test indentation level calculation"""

    analyzer = FileAnalyzer()
    lines = [
      'def func():',
      '  x = 1',
      '    y = 2',
    ]
    statements = analyzer.analyzeFile(lines)

    assert statements[0].indentLevel == 0
    assert statements[1].indentLevel == 2
    assert statements[2].indentLevel == 4

  def testSecondaryClauseDetection(self):
    """Test detection of secondary clauses"""

    analyzer = FileAnalyzer()
    lines = [
      'if True:',
      '  pass',
      'else:',
      '  pass',
    ]
    statements = analyzer.analyzeFile(lines)

    assert not statements[0].isSecondaryClause  # if
    assert not statements[1].isSecondaryClause  # pass
    assert statements[2].isSecondaryClause  # else
    assert not statements[3].isSecondaryClause  # pass

  def testMixedContent(self):
    """Test file with mixed content types"""

    analyzer = FileAnalyzer()
    lines = [
      '# Header comment',
      '',
      'import sys',
      'from os import path',
      '',
      'def func():',
      '  """Docstring"""',
      '  result = complex(',
      '    arg1,',
      '  )',
      '  return result',
    ]
    statements = analyzer.analyzeFile(lines)

    # Should have: comment, blank, import, import, blank, def, docstring, multiline assignment, return
    assert len(statements) == 9
    assert statements[0].isComment
    assert statements[1].isBlank
    assert statements[2].blockType == BlockType.IMPORT
    assert statements[3].blockType == BlockType.IMPORT
    assert statements[4].isBlank
    assert statements[5].blockType == BlockType.DEFINITION
    assert statements[6].blockType == BlockType.DOCSTRING  # Docstring properly classified
    assert statements[7].blockType == BlockType.ASSIGNMENT  # Multiline assignment
    assert statements[8].blockType == BlockType.FLOW_CONTROL  # return statement

  def testGetIndentLevel(self):
    """Test private _getIndentLevel method"""

    analyzer = FileAnalyzer()

    assert analyzer._getIndentLevel('no indent') == 0
    assert analyzer._getIndentLevel('  two spaces') == 2
    assert analyzer._getIndentLevel('    four spaces') == 4
    assert analyzer._getIndentLevel('\ttab') == 2  # Tab uses config.indentWidth (default 2)
    assert analyzer._getIndentLevel('') == -1  # blank line

  def testDecoratorsGroupedWithDefinition(self):
    """Test that decorators are properly grouped with their function/class definition"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    testCode = """class TestClass:
  @staticmethod
  def staticMethod():
    return 42

  @classmethod
  @property
  def classProperty(cls):
    return True

  def normalMethod(self):
    return None"""

    # No blank lines should be added between decorators and their function definitions
    expectedCode = testCode

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expectedCode, 'Should not add blank lines between decorators and definitions'
      assert not changed, 'Properly formatted decorators should not trigger changes'
