"""
Pass 2: Blank line rule engine.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .commentrules import CommentRuleHandler
from .context import ContextBuilder
from .definitionrules import DefinitionRuleHandler


class BlankLineRuleEngine:
  """Pass 2: Apply blank line rules

  Uses context-based approach for O(n) complexity:
  1. Build StatementContext objects in one pass (ContextBuilder)
  2. Apply rules using pre-computed context (no backward scanning)
  3. Return blank line counts directly
  """

  def __init__(self):
    """Initialize rule engine with specialized handlers"""

    self.contextBuilder = ContextBuilder()
    self.commentHandler = CommentRuleHandler()
    self.definitionHandler = DefinitionRuleHandler()

  def applyRules(self, statements):
    """Return list indicating how many blank lines should exist before each statement

    O(n) complexity with no recursion or backward scanning.

    :type statements: list[Statement]
    :param statements: List of statements to apply rules to
    :rtype: list[int]
    :return: Blank line count for each statement
    """

    if not statements:
      return []

    # Build contexts in one O(n) pass
    contexts = self.contextBuilder.buildContexts(statements)

    # Apply rules in single forward pass
    blankLineCounts = [0] * len(statements)

    for ctx in contexts:
      if ctx.statement.isBlank:
        continue

      # Handle skip directive - preserve existing blank lines
      if ctx.statement.skipBlankLineRules:
        blankLineCounts[ctx.index] = self._countExistingBlanks(statements, ctx.index)

        # Check if next non-blank statement should preserve its blank lines
        # (to preserve blank lines after skip blocks)
        for j in range(ctx.index + 1, len(statements)):
          if not statements[j].isBlank:
            if not statements[j].skipBlankLineRules:
              # If there's a blank line between skip block and next statement
              if j > ctx.index + 1:
                # Mark next statement to preserve its blank lines
                contexts[j].preserveBlankLines = True

            break

        continue

      # Secondary clauses (else, elif, except, finally) - no blank before
      if ctx.statement.isSecondaryClause:
        blankLineCounts[ctx.index] = 0

        continue

      # Determine blank lines using context
      blankLineCounts[ctx.index] = self._determineBlankLine(ctx, statements)

    return blankLineCounts

  def _determineBlankLine(self, ctx, statements, skipPreserve=False):
    """Determine blank lines needed before a statement using context

    Replaces old _determineBlankLineForStatement (91 lines, 10 params, 6-level nesting)
    with context-based approach (simple dispatching, 3-level max nesting).

    :type ctx: StatementContext
    :param ctx: Pre-computed context for the statement
    :type statements: list[Statement]
    :param statements: Full list of statements
    :type skipPreserve: bool
    :param skipPreserve: If True, skip preserve-blank-lines logic (used for calculating rule-based count)
    :rtype: int
    :return: Number of blank lines needed
    """

    stmt = ctx.statement

    # Rule 1: No blank line at start of new scope (highest priority)
    if ctx.startsNewScope:
      return 0

    # Rule 2: Preserve blank lines (comment-adjacent or after skip block)
    # Use max of existing and calculated to ensure PEP 8 compliance
    if not skipPreserve and ctx.preserveBlankLines:
      existingBlanks = self._countExistingBlanks(statements, ctx.index)

      # Calculate what the rule would normally require
      calculatedBlanks = self._determineBlankLine(ctx, statements, skipPreserve=True)

      return max(existingBlanks, calculatedBlanks)

    # Rule 3: After completed definition block
    if ctx.hasCompletedDefBefore:
      return self.definitionHandler.needsBlankAfterDefinition(ctx.prevNonBlank, stmt, statements, ctx.prevNonBlankIdx)

    # Rule 4: After completed control block
    if ctx.hasCompletedControlBefore:
      return self.definitionHandler.needsBlankAfterControl(stmt)

    # Find previous statement at SAME indent level (for transition rules)
    prevAtSameLevel = None
    prevAtSameLevelIdx = None

    if ctx.prevNonBlank and ctx.prevNonBlank.indentLevel == stmt.indentLevel:
      prevAtSameLevel = ctx.prevNonBlank
      prevAtSameLevelIdx = ctx.prevNonBlankIdx

    # Rule 5: Handle comments specially
    if stmt.isComment:
      prevBlockType = prevAtSameLevel.blockType if prevAtSameLevel else None

      return self.commentHandler.needsBlankBeforeComment(stmt, False, prevBlockType, ctx.startsNewScope)

    # Rule 6: After comment (at same level)
    if prevAtSameLevel and prevAtSameLevel.isComment:
      return self.commentHandler.needsBlankAfterComment(prevAtSameLevel, stmt, statements, ctx.index)

    # Rule 7: After other block types (at same level)
    if prevAtSameLevel:
      prevBlockType = prevAtSameLevel.blockType

      return self.definitionHandler.needsBlankAfterBlockType(prevBlockType, stmt, statements, prevAtSameLevelIdx)

    # Rule 8: Returning from nested level
    if ctx.returningFromNestedLevel:
      return 1

    # Default: no blank line
    return 0

  def _countExistingBlanks(self, statements, index):
    """Count existing blank lines before a statement

    :type statements: list[Statement]
    :param statements: List of statements
    :type index: int
    :param index: Index of statement
    :rtype: int
    :return: Number of blank lines before statement
    """

    count = 0

    for j in range(index - 1, -1, -1):
      if statements[j].isBlank:
        count += 1
      else:
        break

    return count
