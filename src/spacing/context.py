"""
Context builder for pre-computing statement relationships.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .types import BlockType, Statement, StatementContext
from .helpers import findPreviousNonBlankAtLevel, hasBodyBetween


class ContextBuilder:
  """Build StatementContext objects in one O(n) forward pass

  This class pre-computes all relational information needed for blank line
  rule application, eliminating the need for O(n²) backward scanning during
  rule evaluation.

  The buildContexts method performs a single forward pass to populate:
  - prevNonBlank/nextNonBlank references
  - startsNewScope flags (statements starting new indentation scope)
  - returningFromNestedLevel flags (statements returning from deeper indent)
  - hasCompletedDefBefore flags (completed definition block before statement)
  - hasCompletedControlBefore flags (completed control block before statement)
  - preserveBlankLines flags (blank lines that should not be altered)

  This pre-computation enables O(1) lookups during rule application.
  """

  def buildContexts(self, statements):
    """Build context in one O(n) forward pass

    :type statements: list[Statement]
    :param statements: List of statements to build context for
    :rtype: list[StatementContext]
    :return: List of StatementContext objects, one per statement
    """

    contexts = self._initializeContexts(statements)

    self._computePrevNext(statements, contexts)
    self._computeScopeInfo(statements, contexts)
    self._computeCompletedBlocks(statements, contexts)
    self._computeCommentPreservation(statements, contexts)

    return contexts

  def _initializeContexts(self, statements):
    """Create initial context objects for each statement

    :type statements: list[Statement]
    :param statements: List of statements
    :rtype: list[StatementContext]
    :return: List of initialized StatementContext objects
    """

    return [StatementContext(index=i, statement=stmt) for i, stmt in enumerate(statements)]

  def _computePrevNext(self, statements, contexts):
    """Populate prevNonBlank and nextNonBlank references

    Single forward pass to link prev/next non-blank statements.

    :type statements: list[Statement]
    :param statements: List of statements
    :type contexts: list[StatementContext]
    :param contexts: List of contexts to populate
    """

    lastNonBlankIdx = -1

    for i, stmt in enumerate(statements):
      if not stmt.isBlank:
        # Link to previous non-blank
        if lastNonBlankIdx >= 0:
          contexts[i].prevNonBlank = statements[lastNonBlankIdx]
          contexts[i].prevNonBlankIdx = lastNonBlankIdx

          # Back-link: set next for previous
          contexts[lastNonBlankIdx].nextNonBlank = stmt
          contexts[lastNonBlankIdx].nextNonBlankIdx = i

        lastNonBlankIdx = i

  def _computeScopeInfo(self, statements, contexts):
    """Detect scope boundaries (startsNewScope, returningFromNestedLevel)

    Track indent levels to detect scope changes.

    :type statements: list[Statement]
    :param statements: List of statements
    :type contexts: list[StatementContext]
    :param contexts: List of contexts to populate
    """

    for i in range(1, len(statements)):
      if statements[i].isBlank:
        continue

      # Find previous non-blank statement
      prevNonBlankIdx = contexts[i].prevNonBlankIdx

      if prevNonBlankIdx >= 0:
        prevStmt = statements[prevNonBlankIdx]

        # Detect new scope: indented more after control/definition/secondary clause
        if statements[i].indentLevel > prevStmt.indentLevel:
          if prevStmt.blockType in [BlockType.CONTROL, BlockType.DEFINITION] or prevStmt.isSecondaryClause:
            contexts[i].startsNewScope = True

    # Detect returning from nested level
    for i in range(len(statements)):
      if statements[i].isBlank:
        continue

      targetIndent = statements[i].indentLevel

      # Look backward for deeper indentation
      for j in range(i - 1, -1, -1):
        if statements[j].isBlank:
          continue

        # Found deeper indent - we're returning from nested
        if statements[j].indentLevel > targetIndent:
          contexts[i].returningFromNestedLevel = True

          break

        # Found same or shallower - stop looking
        if statements[j].indentLevel <= targetIndent:
          break

  def _computeCompletedBlocks(self, statements, contexts):
    """Identify completed definition/control blocks

    Mark statements that follow completed blocks.

    :type statements: list[Statement]
    :param statements: List of statements
    :type contexts: list[StatementContext]
    :param contexts: List of contexts to populate
    """

    for i in range(len(statements)):
      if statements[i].isBlank:
        continue

      targetIndent = statements[i].indentLevel

      # Check for completed definition block at this indent level
      prevStmt, prevIdx = findPreviousNonBlankAtLevel(statements, i, targetIndent)

      if prevStmt and prevStmt.blockType == BlockType.DEFINITION:
        if hasBodyBetween(statements, prevIdx, i, targetIndent):
          contexts[i].hasCompletedDefBefore = True

      # Check for completed control block at this indent level
      if prevStmt and prevStmt.blockType == BlockType.CONTROL:
        if hasBodyBetween(statements, prevIdx, i, targetIndent):
          contexts[i].hasCompletedControlBefore = True

  def _computeCommentPreservation(self, statements, contexts):
    """Mark comments that need blank line preservation

    Detect blank lines adjacent to comments that should not be altered.
    Philosophy: Trust user's intent with blank lines directly adjacent to comments.
    Exception: Do alter if PEP 8 requires 2 blank lines (module-level definitions).

    :type statements: list[Statement]
    :param statements: List of statements
    :type contexts: list[StatementContext]
    :param contexts: List of contexts to populate
    """

    for i in range(len(statements) - 1):
      # If there's a blank line, check what comes immediately before and after
      if statements[i + 1].isBlank:
        # Look ahead to find the next non-blank statement
        nextNonBlankIdx = None

        for j in range(i + 2, len(statements)):
          if not statements[j].isBlank:
            nextNonBlankIdx = j

            break

        if nextNonBlankIdx is not None:
          beforeStmt = statements[i]
          afterStmt = statements[nextNonBlankIdx]

          # Only consider blank lines adjacent to comments
          if beforeStmt.isComment or afterStmt.isComment:
            shouldPreserve = True

            # Case 1: comment after module-level definition - do alter (let PEP 8 apply)
            if afterStmt.isComment and afterStmt.indentLevel == 0:
              # Check if there's a module-level definition immediately before
              prevStmt, prevIdx = findPreviousNonBlankAtLevel(statements, i + 1, 0)

              if prevStmt and prevStmt.blockType == BlockType.DEFINITION:
                shouldPreserve = False

            # Case 2: module-level definition after comment - do alter (let PEP 8 apply)
            if (
              beforeStmt.isComment
              and beforeStmt.indentLevel == 0
              and afterStmt.blockType == BlockType.DEFINITION
              and afterStmt.indentLevel == 0
            ):
              shouldPreserve = False

            if shouldPreserve:
              contexts[nextNonBlankIdx].preserveBlankLines = True
