"""
Comment-specific blank line rules.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .types import BlockType


class CommentRuleHandler:
  """Handle blank line rules for comments

  Implements PEP 8 and PEP 257 rules for blank lines around comments.
  All methods use guard clauses to maintain max 3-level nesting.

  Philosophy: Trust user's intent with blank lines adjacent to comments,
  except when PEP 8 requires specific formatting (module-level definitions).
  """

  def needsBlankAfterComment(self, prevStmt, currentStmt, statements, currentIdx):
    """Determine blank lines needed when previous statement is a comment

    :type prevStmt: Statement
    :param prevStmt: Previous non-blank statement (must be a comment)
    :type currentStmt: Statement
    :param currentStmt: Current statement
    :type statements: list[Statement]
    :param statements: Full list of statements
    :type currentIdx: int
    :param currentIdx: Index of current statement
    :rtype: int
    :return: Number of blank lines needed
    """

    # Guard: Only applies when previous is a comment
    if not prevStmt.isComment:
      return 0

    # Module-level definition after comment: Apply PEP 8
    if self._isModuleLevelDefinitionAfterComment(currentStmt):
      return self._handleCommentBeforeModuleLevelDef(statements, currentIdx)

    # Default: no blank line after comment (trust user's formatting)
    return 0

  def needsBlankBeforeComment(self, currentStmt, completedDefinitionBlock, prevBlockType, startsNewScope):
    """Determine blank lines needed before a comment statement

    :type currentStmt: Statement
    :param currentStmt: Current comment statement
    :type completedDefinitionBlock: bool
    :param completedDefinitionBlock: Whether completed definition precedes
    :type prevBlockType: BlockType
    :param prevBlockType: Block type of previous statement
    :type startsNewScope: bool
    :param startsNewScope: Whether this starts a new scope
    :rtype: int
    :return: Number of blank lines needed
    """

    from .config import config

    # Guard: No blank line at start of new scope (highest priority)
    if startsNewScope:
      return 0

    # After completed definition block: apply definition rules
    if completedDefinitionBlock:
      return config.getBlankLines(BlockType.DEFINITION, BlockType.COMMENT, currentStmt.indentLevel)

    # After docstring: apply docstring rules
    if prevBlockType == BlockType.DOCSTRING:
      return config.getBlankLines(BlockType.DOCSTRING, BlockType.COMMENT, currentStmt.indentLevel)

    # Transitioning to comment from non-comment block: add blank line
    if prevBlockType is not None and prevBlockType != BlockType.COMMENT:
      return 1

    # Default: no blank line
    return 0

  def _isModuleLevelDefinitionAfterComment(self, stmt):
    """Check if statement is a module-level definition

    :type stmt: Statement
    :param stmt: Statement to check
    :rtype: bool
    :return: True if module-level definition
    """

    return stmt.indentLevel == 0 and stmt.blockType == BlockType.DEFINITION

  def _handleCommentBeforeModuleLevelDef(self, statements, currentIdx):
    """Handle blank lines for module-level definition after comment

    Logic:
    - If there IS a blank after the comment: ensure 2 total (PEP 8)
    - If there's NO blank after comment: only add if no completed def before comment

    :type statements: list[Statement]
    :param statements: List of statements
    :type currentIdx: int
    :param currentIdx: Index of current statement
    :rtype: int
    :return: Number of blank lines needed
    """

    from .config import config

    hasBlankAfterComment = self._hasBlankAfterComment(statements, currentIdx)

    if hasBlankAfterComment:
      # Already has blank after comment - ensure we have 2 total (PEP 8)
      return config.getBlankLines(BlockType.COMMENT, BlockType.DEFINITION, 0)

    # No blank after comment - only add if no completed def before comment
    hasCompletedDefBeforeComment = self._hasCompletedDefinitionBeforeComment(statements, currentIdx)

    if not hasCompletedDefBeforeComment:
      return config.getBlankLines(BlockType.COMMENT, BlockType.DEFINITION, 0)

    return 0

  def _hasBlankAfterComment(self, statements, currentIdx):
    """Check if there's a blank line between comment and current statement

    :type statements: list[Statement]
    :param statements: List of statements
    :type currentIdx: int
    :param currentIdx: Index of current statement
    :rtype: bool
    :return: True if blank exists after comment
    """

    for j in range(currentIdx - 1, -1, -1):
      if statements[j].isBlank:
        return True

      if statements[j].isComment:
        return False

    return False

  def _hasCompletedDefinitionBeforeComment(self, statements, currentIdx):
    """Check if there's a completed definition before the most recent module-level comment

    :type statements: list[Statement]
    :param statements: List of statements
    :type currentIdx: int
    :param currentIdx: Index of current statement
    :rtype: bool
    :return: True if completed definition exists before comment
    """

    from .helpers import findPreviousNonBlankAtLevel, hasBodyBetween

    # Find the most recent module-level comment
    commentIdx = None

    for k in range(currentIdx - 1, -1, -1):
      if statements[k].isComment and statements[k].indentLevel == 0:
        commentIdx = k

        break

    if commentIdx is None:
      return False

    # Check for completed definition before comment
    prevStmt, prevIdx = findPreviousNonBlankAtLevel(statements, commentIdx, 0)

    if prevStmt is None or prevStmt.blockType != BlockType.DEFINITION:
      return False

    return hasBodyBetween(statements, prevIdx, commentIdx, 0)
