"""
Unit tests for multiline parser.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.parser import MultilineParser


class TestMultilineParser:
  def testSimpleComplete(self):
    """Test parser with simple complete lines"""

    parser = MultilineParser()

    parser.processLine('x = 1')
    assert parser.isComplete()

  def testParenthesesTracking(self):
    """Test bracket tracking with parentheses"""

    parser = MultilineParser()

    parser.processLine('result = func(')
    assert not parser.isComplete()
    parser.processLine('  arg1,')
    assert not parser.isComplete()
    parser.processLine(')')
    assert parser.isComplete()

  def testSquareBrackets(self):
    """Test bracket tracking with square brackets"""

    parser = MultilineParser()

    parser.processLine('items = [')
    assert not parser.isComplete()
    parser.processLine('  1, 2, 3')
    assert not parser.isComplete()
    parser.processLine(']')
    assert parser.isComplete()

  def testCurlyBraces(self):
    """Test bracket tracking with curly braces"""

    parser = MultilineParser()

    parser.processLine('data = {')
    assert not parser.isComplete()
    parser.processLine('  "key": "value"')
    assert not parser.isComplete()
    parser.processLine('}')
    assert parser.isComplete()

  def testNestedBrackets(self):
    """Test nested bracket tracking"""

    parser = MultilineParser()

    parser.processLine('result = func([')
    assert not parser.isComplete()
    parser.processLine('  {"nested": True},')
    assert not parser.isComplete()
    parser.processLine('])')
    assert parser.isComplete()

  def testStringLiterals(self):
    """Test string literals don't interfere with bracket tracking"""

    parser = MultilineParser()

    parser.processLine('text = "this has (brackets) inside"')
    assert parser.isComplete()

  def testStringWithBrackets(self):
    """Test bracket inside string doesn't affect parsing"""

    parser = MultilineParser()

    parser.processLine('func("param with ()", ')
    assert not parser.isComplete()
    parser.processLine('     "another param")')
    assert parser.isComplete()

  def testTripleQuotes(self):
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

  def testEscapedQuotes(self):
    """Test escaped quotes in strings"""

    parser = MultilineParser()

    parser.processLine('text = "escaped \\" quote"')
    assert parser.isComplete()

  def testReset(self):
    """Test parser reset functionality"""

    parser = MultilineParser()

    parser.processLine('func(')
    assert not parser.isComplete()
    parser.reset()
    assert parser.isComplete()
    parser.processLine('x = 1')
    assert parser.isComplete()

  def testMismatchedBrackets(self):
    """Test handling of mismatched brackets"""

    parser = MultilineParser()

    parser.processLine('func(]')

    # Should still track as incomplete because opening bracket not properly closed
    assert not parser.isComplete()

  def testApostropheInComment(self):
    """Test that apostrophes in comments don't start string tracking"""

    parser = MultilineParser()

    parser.processLine("    await asyncio.sleep(0)  # Yield control but don't actually wait")
    assert parser.isComplete()
    assert not parser.inString

  def testQuotesInCommentsIgnored(self):
    """Test that both single and double quotes in comments are ignored"""

    parser = MultilineParser()

    parser.processLine('x = 1  # This comment has \'single\' and "double" quotes')
    assert parser.isComplete()
    assert not parser.inString
    parser.reset()
    parser.processLine("func()  # Comment with unmatched quote '")
    assert parser.isComplete()
    assert not parser.inString
