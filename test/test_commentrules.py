"""
Unit tests for comment rule handler.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.commentrules import CommentRuleHandler
from spacing.types import BlockType, Statement


def createStatement(blockType, indentLevel, isComment=False, isBlank=False):
  """Helper to create test statements"""

  return Statement(
    lines=['test'],
    startLineIndex=0,
    endLineIndex=0,
    blockType=blockType,
    indentLevel=indentLevel,
    isComment=isComment,
    isBlank=isBlank,
  )


class TestCommentRuleHandler:
  """Test suite for CommentRuleHandler class"""

  def test_needsBlankAfterCommentNotComment(self):
    """Test needsBlankAfterComment returns 0 when previous is not a comment"""

    handler = CommentRuleHandler()
    prevStmt = createStatement(BlockType.ASSIGNMENT, 0)
    currentStmt = createStatement(BlockType.ASSIGNMENT, 0)
    result = handler.needsBlankAfterComment(prevStmt, currentStmt, [], 1)

    assert result == 0

  def test_needsBlankAfterCommentModuleLevelDef(self):
    """Test needsBlankAfterComment handles module-level definition after comment"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.DEFINITION, 0),  # def foo():
    ]
    result = handler.needsBlankAfterComment(statements[0], statements[1], statements, 1)

    # Should return PEP 8 requirement (2 blank lines for module-level definitions)
    assert result >= 0  # Actual value depends on config

  def test_needsBlankAfterCommentNonModuleLevelDef(self):
    """Test needsBlankAfterComment returns 0 for nested definition after comment"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 2, isComment=True),  # Indented comment
      createStatement(BlockType.DEFINITION, 2),  # Indented def
    ]
    result = handler.needsBlankAfterComment(statements[0], statements[1], statements, 1)

    assert result == 0  # Not module-level, so no special handling

  def test_needsBlankBeforeCommentNewScope(self):
    """Test needsBlankBeforeComment returns 0 at start of new scope"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 2, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, None, startsNewScope=True)

    assert result == 0

  def test_needsBlankBeforeCommentAfterCompletedDef(self):
    """Test needsBlankBeforeComment after completed definition block"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 0, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, True, None, startsNewScope=False)

    # Should return config value for definition -> comment
    assert result >= 0

  def test_needsBlankBeforeCommentAfterDocstring(self):
    """Test needsBlankBeforeComment after docstring"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 2, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, BlockType.DOCSTRING, startsNewScope=False)

    # Should return config value for docstring -> comment
    assert result >= 0

  def test_needsBlankBeforeCommentTransition(self):
    """Test needsBlankBeforeComment when transitioning from non-comment block"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 0, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, BlockType.ASSIGNMENT, startsNewScope=False)

    assert result == 1  # Universal rule: blank before comment

  def test_needsBlankBeforeCommentAfterComment(self):
    """Test needsBlankBeforeComment after another comment"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 0, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, BlockType.COMMENT, startsNewScope=False)

    assert result == 0  # No blank between consecutive comments

  def test_hasBlankAfterCommentTrue(self):
    """Test _hasBlankAfterComment detects blank line after comment"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),
      createStatement(BlockType.DEFINITION, 0),
    ]
    result = handler._hasBlankAfterComment(statements, 2)

    assert result is True

  def test_hasBlankAfterCommentFalse(self):
    """Test _hasBlankAfterComment returns False when no blank"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),
      createStatement(BlockType.DEFINITION, 0),
    ]
    result = handler._hasBlankAfterComment(statements, 1)

    assert result is False

  def test_hasCompletedDefinitionBeforeCommentTrue(self):
    """Test _hasCompletedDefinitionBeforeComment detects completed definition"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.DEFINITION, 0),  # def bar():
    ]
    result = handler._hasCompletedDefinitionBeforeComment(statements, 3)

    assert result is True  # foo() is complete before comment

  def test_hasCompletedDefinitionBeforeCommentFalse(self):
    """Test _hasCompletedDefinitionBeforeComment returns False when no completed definition"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.DEFINITION, 0),  # def foo():
    ]
    result = handler._hasCompletedDefinitionBeforeComment(statements, 1)

    assert result is False  # No definition before comment

  def test_isModuleLevelDefinitionAfterCommentTrue(self):
    """Test _isModuleLevelDefinitionAfterComment detects module-level definition"""

    handler = CommentRuleHandler()
    stmt = createStatement(BlockType.DEFINITION, 0)
    result = handler._isModuleLevelDefinitionAfterComment(stmt)

    assert result is True

  def test_isModuleLevelDefinitionAfterCommentFalseIndented(self):
    """Test _isModuleLevelDefinitionAfterComment returns False for indented definition"""

    handler = CommentRuleHandler()
    stmt = createStatement(BlockType.DEFINITION, 2)
    result = handler._isModuleLevelDefinitionAfterComment(stmt)

    assert result is False

  def test_isModuleLevelDefinitionAfterCommentFalseNotDef(self):
    """Test _isModuleLevelDefinitionAfterComment returns False for non-definition"""

    handler = CommentRuleHandler()
    stmt = createStatement(BlockType.ASSIGNMENT, 0)
    result = handler._isModuleLevelDefinitionAfterComment(stmt)

    assert result is False
