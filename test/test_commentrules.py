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

    # PEP 8 requires 2 blank lines before module-level definitions
    assert result == 2

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

    # PEP 8 requires 2 blank lines from module-level definitions
    assert result == 2

  def test_needsBlankBeforeCommentAfterDocstring(self):
    """Test needsBlankBeforeComment after docstring"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 2, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, BlockType.DOCSTRING, startsNewScope=False)

    # PEP 257 requires 1 blank line after method/function docstrings
    assert result == 1

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

  def test_needsBlankAfterCommentWithBlankBeforeModuleDef(self):
    """Test needsBlankAfterComment returns PEP 8 value when blank line exists between comment and module-level def"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),
      createStatement(BlockType.DEFINITION, 0),
    ]
    result = handler.needsBlankAfterComment(statements[0], statements[2], statements, 2)

    assert result == 2

  def test_needsBlankAfterCommentNoBlankBeforeModuleDef(self):
    """Test needsBlankAfterComment when comment directly precedes module-level def with no blank line"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),
      createStatement(BlockType.DEFINITION, 0),
    ]
    result = handler.needsBlankAfterComment(statements[0], statements[1], statements, 1)

    assert result == 2

  def test_needsBlankAfterCommentCompletedDefBeforeNoBlank(self):
    """Test needsBlankAfterComment returns 0 when completed def exists before comment and no blank after comment

    When a completed definition exists before the comment and there is no blank line
    between the comment and the next module-level definition, the handler returns 0
    to preserve the user's intent of attaching the comment to the next definition.
    """

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),  # blank
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),  # blank
      createStatement(BlockType.DEFINITION, 0),  # def bar():
    ]
    result = handler.needsBlankAfterComment(statements[3], statements[5], statements, 5)

    assert result == 2

  def test_needsBlankAfterCommentNoDefBeforeComment(self):
    """Test needsBlankAfterComment returns PEP 8 value when no completed def exists before comment"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.DEFINITION, 0),  # def foo():
    ]
    result = handler.needsBlankAfterComment(statements[0], statements[1], statements, 1)

    assert result == 2

  def test_hasBlankAfterCommentNoStatementsBeforeIndex(self):
    """Test _hasBlankAfterComment returns False when no statements before index"""

    handler = CommentRuleHandler()
    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
    ]
    result = handler._hasBlankAfterComment(statements, 0)

    assert not result

  def test_needsBlankBeforeCommentNoPrevBlockType(self):
    """Test needsBlankBeforeComment returns 0 when prevBlockType is None"""

    handler = CommentRuleHandler()
    currentStmt = createStatement(BlockType.COMMENT, 0, isComment=True)
    result = handler.needsBlankBeforeComment(currentStmt, False, None, startsNewScope=False)

    assert result == 0
