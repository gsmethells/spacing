"""
Pass 2: Blank line rule engine.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .types import BlockType, Statement


class BlankLineRuleEngine:
  """Pass 2: Apply blank line rules"""

  def __init__(self):
    """Initialize rule engine with global configuration"""

    pass

  def applyRules(self, statements):
    """Return list indicating how many blank lines should exist before each statement"""

    if not statements:
      return []

    shouldHaveBlankLine = [False] * len(statements)
    preserveExistingBlank = [False] * len(statements)  # Track blank lines after comments to preserve

    # Track which indices start new scopes (first statement after control/def block)
    startsNewScope = [False] * len(statements)

    for i in range(1, len(statements)):
      # Skip blank lines
      if statements[i].isBlank:
        continue

      # Look backwards to find the most recent non-blank statement
      prev_non_blank_idx = -1

      for j in range(i - 1, -1, -1):
        if not statements[j].isBlank:
          prev_non_blank_idx = j

          break

      if prev_non_blank_idx >= 0:
        prev_stmt = statements[prev_non_blank_idx]

        # If this statement is indented more than the previous one
        if statements[i].indentLevel > prev_stmt.indentLevel:
          # And the previous one was a control/definition statement or secondary clause
          if prev_stmt.blockType in [BlockType.CONTROL, BlockType.DEFINITION] or prev_stmt.isSecondaryClause:
            startsNewScope[i] = True

    # Detect blank lines that should be preserved (comment-related blank lines)
    # Philosophy: Trust the user's intent with blank lines directly adjacent to comments
    # Preserve blank lines when:
    # 1. Immediately before a comment (code -> blank -> comment)
    # 2. Immediately after a comment (comment -> blank -> anything)
    # 3. Between comments (comment -> blank -> comment)
    # EXCEPTION: Don't preserve if PEP 8 requires 2 blank lines (module-level definitions)
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
          # Preserve blank line if:
          # - Previous statement (i) is a comment, OR
          # - Next non-blank statement is a comment
          if statements[i].isComment or statements[nextNonBlankIdx].isComment:
            # Check if this is a case where PEP 8 requires 2 blank lines
            # (comment after module-level definition)
            shouldPreserve = True

            if statements[nextNonBlankIdx].isComment and statements[nextNonBlankIdx].indentLevel == 0:
              # Look back past blanks to find if there's a completed definition block
              for k in range(i, -1, -1):
                if statements[k].isBlank:
                  continue

                # Found a non-blank statement at module level
                if statements[k].indentLevel == 0:
                  # If it's a DEFINITION, don't preserve - let PEP 8 apply
                  if statements[k].blockType == BlockType.DEFINITION:
                    shouldPreserve = False

                  break

                # If we found a statement at deeper level, keep looking back
                # (we might be after a definition block body)
                if statements[k].indentLevel > 0:
                  continue

            if shouldPreserve:
              preserveExistingBlank[nextNonBlankIdx] = True

    # Apply rules at each indentation level independently
    shouldHaveBlankLine = self._applyRulesAtLevel(statements, shouldHaveBlankLine, startsNewScope, 0)

    # Convert boolean list to actual blank line counts
    return self._convertToBlankLineCounts(statements, shouldHaveBlankLine, preserveExistingBlank, startsNewScope)

  def _applyRulesAtLevel(
    self,
    statements: list[Statement],
    shouldHaveBlankLine: list[bool],
    startsNewScope: list[bool],
    targetIndent: int,
  ):
    """Apply rules at specific indentation level"""

    prevBlockType = None
    prevStmtIdx = None  # Track index of previous statement for class docstring detection

    for i, stmt in enumerate(statements):
      # Skip statements at different indentation levels
      if stmt.indentLevel != targetIndent and not stmt.isBlank:
        continue

      # Skip blank lines for rule processing (they will be reconstructed)
      if stmt.isBlank:
        continue

      # For comments, we need to check completedDefinitionBlock BEFORE the early exit
      # Check for completed definition blocks (needed for comments too)
      completedDefinitionBlock = False

      if i > 0:
        for j in range(i - 1, -1, -1):
          prevStmt = statements[j]

          if prevStmt.isBlank or prevStmt.indentLevel > targetIndent:
            continue

          if prevStmt.indentLevel == targetIndent:
            if prevStmt.blockType == BlockType.DEFINITION:
              hasBody = False

              for k in range(j + 1, i):
                if statements[k].indentLevel > targetIndent:
                  hasBody = True

                  break

              if hasBody:
                completedDefinitionBlock = True

            break

      if stmt.isComment:
        # Comment break rule: blank line before comment (unless following comment)
        # BUT: no blank line at start of new scope has highest precedence
        # ALSO: if after a completed definition at module level, apply PEP 8 rule
        # ALSO: if after a docstring, preserve the PEP 257 blank line rule
        # AT ALL LEVELS: blank line before comment when transitioning from non-comment block
        if completedDefinitionBlock:
          shouldHaveBlankLine[i] = (
            self._needsBlankLineBetween(BlockType.DEFINITION, stmt.blockType, stmt.indentLevel) > 0
          )
        elif prevBlockType == BlockType.DOCSTRING:
          # PEP 257: blank line after docstring (configurable via afterDocstring)
          shouldHaveBlankLine[i] = (
            self._needsBlankLineBetween(BlockType.DOCSTRING, stmt.blockType, stmt.indentLevel) > 0
          )
        elif prevBlockType is not None and prevBlockType != BlockType.COMMENT and not startsNewScope[i]:
          # Universal rule: transitioning to a comment from any non-comment block requires blank line
          shouldHaveBlankLine[i] = True

        # Comments cause a break - set prevBlockType to COMMENT so next statement
        # can decide whether it needs a blank line after the comment
        prevBlockType = BlockType.COMMENT
        prevStmtIdx = i

        continue

      # Secondary clause rule: NO blank line before secondary clauses
      if stmt.isSecondaryClause:
        shouldHaveBlankLine[i] = False

        # Secondary clauses are part of control structures, so prevBlockType should be CONTROL
        # This ensures the next statement after the control structure completes gets proper spacing
        prevBlockType = BlockType.CONTROL
        prevStmtIdx = i

        continue

      # Check if there was a completed control block before this statement
      # (completedDefinitionBlock was already checked for comments above)
      # OR if we're returning from a deeper indentation level
      completedControlBlock = False
      returningFromNestedLevel = False

      # Recompute completedDefinitionBlock for non-comments (already done for comments)
      if not stmt.isComment:
        completedDefinitionBlock = False

        if i > 0:
          for j in range(i - 1, -1, -1):
            prevStmt = statements[j]

            if prevStmt.isBlank or prevStmt.indentLevel > targetIndent:
              continue

            if prevStmt.indentLevel == targetIndent:
              if prevStmt.blockType == BlockType.DEFINITION:
                hasBody = False

                for k in range(j + 1, i):
                  if statements[k].indentLevel > targetIndent:
                    hasBody = True

                    break

                if hasBody:
                  completedDefinitionBlock = True

              break

      if i > 0:
        # Check if we're returning from a deeper indentation level
        for j in range(i - 1, -1, -1):
          prevStmt = statements[j]

          if prevStmt.isBlank:
            continue

          # If we find a statement at a deeper level, we're returning from nested
          if prevStmt.indentLevel > targetIndent:
            returningFromNestedLevel = True

            break

          # If we find a statement at our level, stop looking
          if prevStmt.indentLevel <= targetIndent:
            break

        # Also check for completed control blocks (not definitions, already handled)
        for j in range(i - 1, -1, -1):
          prevStmt = statements[j]

          # Skip blanks and deeper indents
          if prevStmt.isBlank or prevStmt.indentLevel > targetIndent:
            continue

          # If we find a statement at our level
          if prevStmt.indentLevel == targetIndent:
            # Check if it's a control block that had a body after it
            if prevStmt.blockType == BlockType.CONTROL:
              # Check if there was a deeper indented block after it (its body)
              hasBody = False

              for k in range(j + 1, i):
                if statements[k].indentLevel > targetIndent:
                  hasBody = True

                  break

              if hasBody:
                completedControlBlock = True

            break

      # Main blank line rules
      # Don't add blank line if this is the first statement in a new scope
      if startsNewScope[i]:
        # Never add blank line at start of new scope, regardless of completed control blocks
        shouldHaveBlankLine[i] = False
      elif completedDefinitionBlock:
        # After a completed definition block, apply normal rules with DEFINITION as prev type
        # This handles PEP 8's "surround top-level definitions with 2 blank lines"
        shouldHaveBlankLine[i] = self._needsBlankLineBetween(BlockType.DEFINITION, stmt.blockType, stmt.indentLevel) > 0
      elif prevBlockType is not None:
        # Special case: after comments, don't apply normal block transition rules
        # Comments follow "leave-as-is" behavior - only existing blanks are preserved
        if prevBlockType != BlockType.COMMENT:
          # Check if previous statement is a class docstring
          isClassDocstring = False

          if prevBlockType == BlockType.DOCSTRING and prevStmtIdx is not None:
            # Look back from the docstring to see if it follows a class definition
            for j in range(prevStmtIdx - 1, -1, -1):
              if not statements[j].isBlank:
                isClassDocstring = self._isClassDefinition(statements[j])

                break

          shouldHaveBlankLine[i] = (
            self._needsBlankLineBetween(prevBlockType, stmt.blockType, stmt.indentLevel, isClassDocstring) > 0
          )
        else:
          # After comment blocks, leave-as-is (no blank line added here)
          shouldHaveBlankLine[i] = False
      elif completedControlBlock:
        # After a completed control block, apply normal rules with CONTROL as prev type
        shouldHaveBlankLine[i] = self._needsBlankLineBetween(BlockType.CONTROL, stmt.blockType, stmt.indentLevel) > 0
      elif returningFromNestedLevel:
        # When returning from nested level, add blank line
        shouldHaveBlankLine[i] = True
      else:
        # No previous block, no completed control, not returning from nested - no blank line
        shouldHaveBlankLine[i] = False

      prevBlockType = stmt.blockType
      prevStmtIdx = i

    # Recursively process nested indentation levels
    processedIndents = set()

    for stmt in statements:
      if stmt.indentLevel > targetIndent and stmt.indentLevel not in processedIndents:
        processedIndents.add(stmt.indentLevel)
        self._applyRulesAtLevel(statements, shouldHaveBlankLine, startsNewScope, stmt.indentLevel)

    return shouldHaveBlankLine

  def _convertToBlankLineCounts(
    self,
    statements: list[Statement],
    shouldHaveBlankLine: list[bool],
    preserveExistingBlank: list[bool],
    startsNewScope: list[bool],
  ) -> list[int]:
    """Convert boolean blank line indicators to actual counts
    :param statements: List of statements
    :type statements: list[Statement]
    :param shouldHaveBlankLine: Boolean indicators of where blank lines should exist
    :type shouldHaveBlankLine: list[bool]
    :param preserveExistingBlank: Boolean indicators of existing blank lines to preserve
    :type preserveExistingBlank: list[bool]
    :param startsNewScope: Boolean indicators of statements that start a new scope
    :type startsNewScope: list[bool]
    :rtype: list[int]
    """

    blankLineCounts = [0] * len(statements)

    for i, stmt in enumerate(statements):
      if stmt.isBlank:
        continue

      # NEVER add blank line at start of scope (highest precedence rule)
      if startsNewScope[i]:
        blankLineCounts[i] = 0

        continue

      # Preserve existing blank lines after comments (leave-as-is rule)
      if preserveExistingBlank[i]:
        blankLineCounts[i] = 1

        continue

      if not shouldHaveBlankLine[i]:
        continue

      # Find appropriate previous statement for blank line count calculation
      prevNonBlankIdx = -1
      immediatelyPrevIdx = -1

      # First, find the immediately preceding non-blank statement
      for j in range(i - 1, -1, -1):
        if not statements[j].isBlank:
          immediatelyPrevIdx = j

          break

      # For determining blank line count, we need to find the right "previous" statement
      # If we're returning from a nested level, use the last statement at the same level
      if immediatelyPrevIdx >= 0 and statements[immediatelyPrevIdx].indentLevel > stmt.indentLevel:
        # We're returning from nested level - find previous statement at same level
        for j in range(immediatelyPrevIdx - 1, -1, -1):
          if not statements[j].isBlank and statements[j].indentLevel <= stmt.indentLevel:
            prevNonBlankIdx = j

            break
      else:
        # Normal case - use immediately preceding statement
        prevNonBlankIdx = immediatelyPrevIdx

      if prevNonBlankIdx >= 0:
        prevStmt = statements[prevNonBlankIdx]

        # Check if prevStmt is a class docstring (docstring immediately after class definition)
        isClassDocstring = False

        if prevStmt.blockType == BlockType.DOCSTRING:
          # Look back to find what came before the docstring
          for j in range(prevNonBlankIdx - 1, -1, -1):
            if not statements[j].isBlank:
              isClassDocstring = self._isClassDefinition(statements[j])

              break

        # Determine the effective block types
        # For comments, use BlockType.COMMENT regardless of what blockType field says
        prevBlockType = BlockType.COMMENT if prevStmt.isComment else prevStmt.blockType
        currentBlockType = BlockType.COMMENT if stmt.isComment else stmt.blockType

        # Use block-to-block configuration for blank line count
        blankLineCount = self._needsBlankLineBetween(
          prevBlockType, currentBlockType, stmt.indentLevel, isClassDocstring
        )
        blankLineCounts[i] = blankLineCount

    return blankLineCounts

  def _isClassDefinition(self, statement):
    """Check if a statement is a class definition
    :param statement: Statement to check
    :type statement: Statement
    :rtype: bool
    """

    if statement.blockType != BlockType.DEFINITION:
      return False

    # Check if any line starts with 'class ' (handles decorators)
    if statement.lines:
      for line in statement.lines:
        if line.strip().startswith('class '):
          return True

    return False

  def _needsBlankLineBetween(self, prevType, currentType, indentLevel=None, isClassDocstring=False):
    """Determine number of blank lines needed between block types
    :param prevType: Previous block type
    :type prevType: BlockType
    :param currentType: Current block type
    :type currentType: BlockType
    :param indentLevel: Indentation level of current statement (for scope-aware rules)
    :type indentLevel: int
    :param isClassDocstring: True if prevType is a class docstring
    :type isClassDocstring: bool
    :rtype: int
    """

    from .config import config

    return config.getBlankLines(prevType, currentType, indentLevel, isClassDocstring)
