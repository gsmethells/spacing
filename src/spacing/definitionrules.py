"""
Definition-specific blank line rules (PEP 8 and PEP 257).
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .helpers import isClassDefinition
from .types import BlockType


class DefinitionRuleHandler:
  """Handle blank line rules for definitions

  Implements PEP 8 rules for blank lines between module-level definitions
  and PEP 257 rules for blank lines after docstrings.
  All methods use guard clauses to maintain max 3-level nesting.
  """

  def needsBlankAfterDefinition(self, prevStmt, currentStmt, statements, prevStmtIdx):
    """Determine blank lines needed after a completed definition block

    Implements PEP 8: 2 blank lines between module-level definitions

    :type prevStmt: Statement
    :param prevStmt: Previous non-blank statement
    :type currentStmt: Statement
    :param currentStmt: Current statement
    :type statements: list[Statement]
    :param statements: Full list of statements
    :type prevStmtIdx: int
    :param prevStmtIdx: Index of previous statement
    :rtype: int
    :return: Number of blank lines needed
    """

    from .config import config

    isClassDocstring = self._isClassDocstring(statements, prevStmtIdx, prevStmt.blockType)
    isModuleLevelDocstring = self._isModuleLevelDocstring(statements, prevStmtIdx, prevStmt.blockType)

    return config.getBlankLines(
      BlockType.DEFINITION, currentStmt.blockType, currentStmt.indentLevel, isClassDocstring, isModuleLevelDocstring
    )

  def needsBlankAfterControl(self, currentStmt):
    """Determine blank lines needed after a completed control block

    :type currentStmt: Statement
    :param currentStmt: Current statement
    :rtype: int
    :return: Number of blank lines needed
    """

    from .config import config

    return config.getBlankLines(BlockType.CONTROL, currentStmt.blockType, currentStmt.indentLevel)

  def needsBlankAfterBlockType(self, prevBlockType, currentStmt, statements, prevStmtIdx):
    """Determine blank lines needed after a specific block type

    :type prevBlockType: BlockType
    :param prevBlockType: Previous block type
    :type currentStmt: Statement
    :param currentStmt: Current statement
    :type statements: list[Statement]
    :param statements: Full list of statements
    :type prevStmtIdx: int
    :param prevStmtIdx: Index of previous statement
    :rtype: int
    :return: Number of blank lines needed
    """

    from .config import config

    isClassDocstring = self._isClassDocstring(statements, prevStmtIdx, prevBlockType)
    isModuleLevelDocstring = self._isModuleLevelDocstring(statements, prevStmtIdx, prevBlockType)

    return config.getBlankLines(
      prevBlockType, currentStmt.blockType, currentStmt.indentLevel, isClassDocstring, isModuleLevelDocstring
    )

  def _isClassDocstring(self, statements, docstringIdx, prevBlockType):
    """Check if statement at index is a class docstring

    :type statements: list[Statement]
    :param statements: List of statements
    :type docstringIdx: int
    :param docstringIdx: Index of potential docstring
    :type prevBlockType: BlockType
    :param prevBlockType: Block type of the statement
    :rtype: bool
    :return: True if this is a class docstring
    """

    if prevBlockType != BlockType.DOCSTRING or docstringIdx is None:
      return False

    # Look back from the docstring to see if it follows a class definition
    for j in range(docstringIdx - 1, -1, -1):
      stmt = statements[j]

      if stmt.isBlank:
        continue

      # Found non-blank statement - check if it's a class definition
      return isClassDefinition(stmt)

    return False

  def _isModuleLevelDocstring(self, statements, docstringIdx, prevBlockType):
    """Check if statement at index is a module-level docstring

    :type statements: list[Statement]
    :param statements: List of statements
    :type docstringIdx: int
    :param docstringIdx: Index of potential docstring
    :type prevBlockType: BlockType
    :param prevBlockType: Block type of the statement
    :rtype: bool
    :return: True if this is a module-level docstring
    """

    if prevBlockType != BlockType.DOCSTRING or docstringIdx is None:
      return False

    # Module-level docstring is the first non-blank, non-comment statement
    for j in range(docstringIdx):
      stmt = statements[j]

      # Skip blank lines and comments
      if stmt.isBlank or stmt.isComment:
        continue

      # If we find a non-blank/non-comment before the docstring, it's not module-level
      return False

    # No non-blank/non-comment statements before this docstring
    return True
