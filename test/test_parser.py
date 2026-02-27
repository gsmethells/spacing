"""
Unit tests for multiline parser.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import pytest
from spacing.parser import MultilineParser


class TestMultilineParser:
  def test_simpleComplete(self):
    """Test parser with simple complete lines"""

    parser = MultilineParser()

    parser.processLine('x = 1')
    assert parser.isComplete()

  def test_parenthesesTracking(self):
    """Test bracket tracking with parentheses"""

    parser = MultilineParser()

    parser.processLine('result = func(')
    assert not parser.isComplete()
    parser.processLine('  arg1,')
    assert not parser.isComplete()
    parser.processLine(')')
    assert parser.isComplete()

  def test_squareBrackets(self):
    """Test bracket tracking with square brackets"""

    parser = MultilineParser()

    parser.processLine('items = [')
    assert not parser.isComplete()
    parser.processLine('  1, 2, 3')
    assert not parser.isComplete()
    parser.processLine(']')
    assert parser.isComplete()

  def test_curlyBraces(self):
    """Test bracket tracking with curly braces"""

    parser = MultilineParser()

    parser.processLine('data = {')
    assert not parser.isComplete()
    parser.processLine('  "key": "value"')
    assert not parser.isComplete()
    parser.processLine('}')
    assert parser.isComplete()

  def test_nestedBrackets(self):
    """Test nested bracket tracking"""

    parser = MultilineParser()

    parser.processLine('result = func([')
    assert not parser.isComplete()
    parser.processLine('  {"nested": True},')
    assert not parser.isComplete()
    parser.processLine('])')
    assert parser.isComplete()

  def test_stringLiterals(self):
    """Test string literals don't interfere with bracket tracking"""

    parser = MultilineParser()

    parser.processLine('text = "this has (brackets) inside"')
    assert parser.isComplete()

  def test_stringWithBrackets(self):
    """Test bracket inside string doesn't affect parsing"""

    parser = MultilineParser()

    parser.processLine('func("param with ()", ')
    assert not parser.isComplete()
    parser.processLine('     "another param")')
    assert parser.isComplete()

  def test_tripleQuotes(self):
    """Test triple quoted strings"""

    parser = MultilineParser()

    parser.processLine('text = """')
    assert not parser.isComplete()
    parser.processLine('multiline string')
    assert not parser.isComplete()
    parser.processLine('with (brackets)')
    assert not parser.isComplete()
    parser.processLine('"""')
    assert parser.isComplete()

  def test_escapedQuotes(self):
    """Test escaped quotes in strings"""

    parser = MultilineParser()

    parser.processLine('text = "escaped \\" quote"')
    assert parser.isComplete()

  def test_reset(self):
    """Test parser reset functionality"""

    parser = MultilineParser()

    parser.processLine('func(')
    assert not parser.isComplete()
    parser.reset()
    assert parser.isComplete()
    parser.processLine('x = 1')
    assert parser.isComplete()

  def test_mismatchedBrackets(self):
    """Test handling of mismatched brackets"""

    parser = MultilineParser()

    parser.processLine('func(]')

    # Should still track as incomplete because opening bracket not properly closed
    assert not parser.isComplete()

  def test_apostropheInComment(self):
    """Test that apostrophes in comments don't start string tracking"""

    parser = MultilineParser()

    parser.processLine("    await asyncio.sleep(0)  # Yield control but don't actually wait")
    assert parser.isComplete()
    assert not parser.inString

  def test_quotesInCommentsIgnored(self):
    """Test that both single and double quotes in comments are ignored"""

    parser = MultilineParser()

    parser.processLine('x = 1  # This comment has \'single\' and "double" quotes')
    assert parser.isComplete()
    assert not parser.inString
    parser.reset()
    parser.processLine("func()  # Comment with unmatched quote '")
    assert parser.isComplete()
    assert not parser.inString

  def test_decoratorPatternInMultilineString(self):
    """
    Test that decorator patterns inside multiline strings don't set expectingDefinition.

    Regression test for MAJOR-1 bug: Parser was checking for decorators (@foo)
    even when inside a multiline string, causing it to wait for a def/class statement
    that would never come, making the parser think the statement was incomplete.
    """

    parser = MultilineParser()

    # Start multiline string with decorator-like pattern inside
    parser.processLine("x = '''@decorator")
    assert parser.inString
    assert not parser.isComplete()  # String not closed yet
    assert not parser.expectingDefinition  # Should NOT be set when inside string

    # Continue string with more lines
    parser.processLine('@another_decorator')
    assert parser.inString
    assert not parser.expectingDefinition

    # Close the string
    parser.processLine("'''")
    assert not parser.inString
    assert parser.isComplete()  # Should be complete now
    assert not parser.expectingDefinition

  def test_processLineTypeError(self):
    """Test that processLine raises TypeError for non-string input"""

    parser = MultilineParser()

    with pytest.raises(TypeError, match='Expected str, got int'):
      parser.processLine(123)

    with pytest.raises(TypeError, match='Expected str, got list'):
      parser.processLine(['not', 'a', 'string'])
