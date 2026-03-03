"""
Unit tests for pure helper functions.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.helpers import findPreviousNonBlankAtLevel, hasBodyBetween, isClassDefinition
from spacing.types import BlockType, Statement


def makeStatement(blockType, indentLevel, lines=None, isBlank=False):
  """
  Helper to build a Statement for tests.

  :type blockType: BlockType
  :type indentLevel: int
  :type lines: list[str] | None
  :type isBlank: bool
  :rtype: Statement
  """

  return Statement(
    lines=lines or [],
    startLineIndex=0,
    endLineIndex=0,
    blockType=blockType,
    indentLevel=indentLevel,
    isBlank=isBlank,
  )


class TestFindPreviousNonBlankAtLevel:
  def test_findPreviousNonBlankAtLevelBasic(self):
    """Find previous statement at same indentation level"""

    stmts = [
      makeStatement(BlockType.ASSIGNMENT, 0),
      makeStatement(BlockType.CALL, 0),
    ]
    result = findPreviousNonBlankAtLevel(stmts, 1, 0)

    assert result == (stmts[0], 0)

  def test_findPreviousNonBlankAtLevelSkipsBlanks(self):
    """Skips blank lines between statements at the same level"""

    blank = makeStatement(BlockType.ASSIGNMENT, -1, isBlank=True)
    stmts = [
      makeStatement(BlockType.ASSIGNMENT, 0),
      blank,
      makeStatement(BlockType.CALL, 0),
    ]
    result = findPreviousNonBlankAtLevel(stmts, 2, 0)

    assert result == (stmts[0], 0)

  def test_findPreviousNonBlankAtLevelNotFound(self):
    """Returns (None, None) when no matching statement exists"""

    stmts = [makeStatement(BlockType.CALL, 0)]
    result = findPreviousNonBlankAtLevel(stmts, 0, 0)

    assert result == (None, None)

  def test_findPreviousNonBlankAtLevelDifferentIndent(self):
    """Stops and returns (None, None) when a statement at a lower indent is encountered"""

    stmts = [
      makeStatement(BlockType.DEFINITION, 0),
      makeStatement(BlockType.ASSIGNMENT, 2),
      makeStatement(BlockType.CALL, 2),
    ]

    # Searching from idx 2 for indent 2; idx 1 is at indent 2 — should return it
    result = findPreviousNonBlankAtLevel(stmts, 2, 2)

    assert result == (stmts[1], 1)

  def test_findPreviousNonBlankAtLevelStopsAtLowerIndent(self):
    """Returns (None, None) when a lower-indent statement is encountered before a match"""

    stmts = [
      makeStatement(BlockType.DEFINITION, 0),
      makeStatement(BlockType.ASSIGNMENT, 4),
    ]

    # Searching for indent 4 from idx 1, but idx 0 has indent 0 — should stop and return (None, None)
    result = findPreviousNonBlankAtLevel(stmts, 1, 4)

    assert result == (None, None)

  def test_findPreviousNonBlankAtLevelSkipsDeeper(self):
    """Skips over statements at a deeper indent level"""

    stmts = [
      makeStatement(BlockType.ASSIGNMENT, 0),
      makeStatement(BlockType.ASSIGNMENT, 4),
      makeStatement(BlockType.CALL, 0),
    ]
    result = findPreviousNonBlankAtLevel(stmts, 2, 0)

    assert result == (stmts[0], 0)


class TestHasBodyBetween:
  def test_hasBodyBetweenTrue(self):
    """Returns True when an indented body exists between the definition and end index"""

    stmts = [
      makeStatement(BlockType.DEFINITION, 0),
      makeStatement(BlockType.ASSIGNMENT, 2),
      makeStatement(BlockType.DEFINITION, 0),
    ]

    assert hasBodyBetween(stmts, 0, 2, 0) is True

  def test_hasBodyBetweenFalse(self):
    """Returns False when no indented body exists between the indices"""

    stmts = [
      makeStatement(BlockType.DEFINITION, 0),
      makeStatement(BlockType.DEFINITION, 0),
    ]

    assert hasBodyBetween(stmts, 0, 1, 0) is False

  def test_hasBodyBetweenEmptyRange(self):
    """Returns False when defIdx and endIdx are adjacent (no statements between)"""

    stmts = [
      makeStatement(BlockType.DEFINITION, 0),
      makeStatement(BlockType.DEFINITION, 0),
    ]

    assert hasBodyBetween(stmts, 0, 1, 0) is False


class TestIsClassDefinition:
  def test_isClassDefinitionTrue(self):
    """Returns True for a class definition"""

    stmt = makeStatement(BlockType.DEFINITION, 0, lines=['class Foo:'])

    assert isClassDefinition(stmt) is True

  def test_isClassDefinitionFalseFunction(self):
    """Returns False for a function definition"""

    stmt = makeStatement(BlockType.DEFINITION, 0, lines=['def foo():'])

    assert isClassDefinition(stmt) is False

  def test_isClassDefinitionFalseNotDefinition(self):
    """Returns False for a non-definition block type"""

    stmt = makeStatement(BlockType.CALL, 0, lines=['class_name = Foo()'])

    assert isClassDefinition(stmt) is False

  def test_isClassDefinitionEmptyLines(self):
    """Returns False when the statement has no lines"""

    stmt = makeStatement(BlockType.DEFINITION, 0, lines=[])

    assert isClassDefinition(stmt) is False

  def test_isClassDefinitionWithDecorator(self):
    """Returns True for a class definition that has a decorator line before it"""

    stmt = makeStatement(BlockType.DEFINITION, 0, lines=['@some_decorator', 'class Foo:'])

    assert isClassDefinition(stmt) is True
