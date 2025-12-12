"""
Pass 2: Blank line rule engine.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .types import BlockType, Statement


class BlankLineRuleEngine:
  """Pass 2: Apply blank line rules"""

  def applyRules(self, statements):
    """Return list indicating how many blank lines should exist before each statement"""

    if not statements:
      return []

    shouldHaveBlankLine = [False] * len(statements)
    doNotAlterExistingNumberOfBlankLines = [False] * len(statements)  # Track blank lines after comments to not alter

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
          # Use helper to determine if this blank should not be altered
          if self._shouldNotAlterBlankLinesAfterComment(statements, i, nextNonBlankIdx):
            doNotAlterExistingNumberOfBlankLines[nextNonBlankIdx] = True

    # Apply rules at each indentation level independently
    shouldHaveBlankLine = self._applyRulesAtLevel(
      statements, shouldHaveBlankLine, doNotAlterExistingNumberOfBlankLines, startsNewScope, 0
    )

    # Convert boolean list to actual blank line counts
    return self._convertToBlankLineCounts(
      statements, shouldHaveBlankLine, doNotAlterExistingNumberOfBlankLines, startsNewScope
    )

  def _shouldNotAlterBlankLinesAfterComment(self, statements, beforeIdx, afterIdx):
    """Determine if blank lines between statements should not be altered

    Philosophy: Trust user's intent with blank lines adjacent to comments.
    Don't alter blank lines when directly before or after a comment.
    EXCEPTION: Do alter if PEP 8 requires 2 blank lines (module-level definitions).

    :param statements: List of statements
    :param beforeIdx: Index of statement before blank line
    :param afterIdx: Index of statement after blank line
    :return: True if blank lines should not be altered
    """

    beforeStmt = statements[beforeIdx]
    afterStmt = statements[afterIdx]

    # Only avoid altering blank lines adjacent to comments
    if not (beforeStmt.isComment or afterStmt.isComment):
      return False

    shouldNotAlterExisting = True

    # Case 1: comment after module-level definition - do alter (let PEP 8 apply)
    if afterStmt.isComment and afterStmt.indentLevel == 0:
      # Check if there's a module-level definition immediately before
      prevStmt, prevIdx = self._findPreviousNonBlankAtLevel(statements, beforeIdx + 1, 0)

      if prevStmt and prevStmt.blockType == BlockType.DEFINITION:
        shouldNotAlterExisting = False

    # Case 2: module-level definition after comment
    # XXX: Do alter existing blank lines after comment before module-level definition
    # Always apply PEP 8 rule: 2 blank lines between top-level definitions (even with comments)
    if (
      beforeStmt.isComment
      and beforeStmt.indentLevel == 0
      and afterStmt.blockType == BlockType.DEFINITION
      and afterStmt.indentLevel == 0
    ):
      shouldNotAlterExisting = False

    return shouldNotAlterExisting

  def _findPreviousNonBlankAtLevel(self, statements, fromIdx, targetIndent):
    """Find previous non-blank statement at target indentation level

    :param statements: List of statements
    :param fromIdx: Index to start searching backwards from
    :param targetIndent: Indentation level to match
    :return: Tuple of (statement, index) or (None, None) if not found
    """

    for j in range(fromIdx - 1, -1, -1):
      stmt = statements[j]

      if stmt.isBlank or stmt.indentLevel > targetIndent:
        continue

      if stmt.indentLevel == targetIndent:
        return (stmt, j)

      break

    return (None, None)

  def _hasBodyBetween(self, statements, defIdx, endIdx, targetIndent):
    """Check if definition has indented body between two indices

    :param statements: List of statements
    :param defIdx: Index of definition statement
    :param endIdx: Index to search up to
    :param targetIndent: Base indentation level
    :return: True if body exists
    """

    for k in range(defIdx + 1, endIdx):
      if statements[k].indentLevel > targetIndent:
        return True

    return False

  def _hasCompletedDefinitionBlock(self, statements, beforeIdx, targetIndent):
    """Check if there's a completed definition block before given index

    :param statements: List of statements
    :param beforeIdx: Index to check before
    :param targetIndent: Indentation level to check at
    :return: True if completed definition block exists
    """

    prevStmt, prevIdx = self._findPreviousNonBlankAtLevel(statements, beforeIdx, targetIndent)

    if prevStmt is None:
      return False

    if prevStmt.blockType != BlockType.DEFINITION:
      return False

    return self._hasBodyBetween(statements, prevIdx, beforeIdx, targetIndent)

  def _hasCompletedDefinitionBeforeComment(self, statements, currentIdx):
    """Check if there's a completed definition before the most recent module-level comment

    :param statements: List of statements
    :param currentIdx: Current statement index
    :return: True if completed definition exists before most recent comment
    """

    # Find the most recent module-level comment
    commentIdx = None

    for k in range(currentIdx - 1, -1, -1):
      if statements[k].isComment and statements[k].indentLevel == 0:
        commentIdx = k

        break

    if commentIdx is None:
      return False

    # Use existing helper to check for completed definition before comment
    return self._hasCompletedDefinitionBlock(statements, commentIdx, 0)

  def _applyCommentRules(
    self,
    completedDefinitionBlock,
    prevBlockType,
    stmt,
    startsNewScope,
  ):
    """Apply blank line rules for comment statements

    :param completedDefinitionBlock: Whether a completed def block precedes
    :param prevBlockType: Block type of previous statement
    :param stmt: Current comment statement
    :param startsNewScope: Whether this starts a new scope
    :return: True if blank line needed before comment, False otherwise
    """

    # Comment break rule: blank line before comment (unless following comment)
    # BUT: no blank line at start of new scope has highest precedence
    # ALSO: if after a completed definition at module level, apply PEP 8 rule
    # ALSO: if after a docstring, preserve the PEP 257 blank line rule
    # AT ALL LEVELS: blank line before comment when transitioning from non-comment block
    if completedDefinitionBlock:
      return self._needsBlankLineBetween(BlockType.DEFINITION, stmt.blockType, stmt.indentLevel) > 0
    elif prevBlockType == BlockType.DOCSTRING:
      # PEP 257: blank line after docstring (configurable via afterDocstring)
      return self._needsBlankLineBetween(BlockType.DOCSTRING, stmt.blockType, stmt.indentLevel) > 0
    elif prevBlockType is not None and prevBlockType != BlockType.COMMENT and not startsNewScope:
      # Universal rule: transitioning to a comment from any non-comment block requires blank line
      return True

    return False

  def _isReturningFromNestedLevel(self, statements, currentIdx, targetIndent):
    """Check if current statement is returning from deeper indentation

    :param statements: List of statements
    :param currentIdx: Current statement index
    :param targetIndent: Target indentation level
    :return: True if returning from nested level
    """

    for j in range(currentIdx - 1, -1, -1):
      stmt = statements[j]

      if stmt.isBlank:
        continue

      # If we find a statement at a deeper level, we're returning from nested
      if stmt.indentLevel > targetIndent:
        return True

      # If we find a statement at our level, stop looking
      if stmt.indentLevel <= targetIndent:
        break

    return False

  def _hasCompletedControlBlock(self, statements, beforeIdx, targetIndent):
    """Check if there's a completed control block before given index

    :param statements: List of statements
    :param beforeIdx: Index to check before
    :param targetIndent: Indentation level
    :return: True if completed control block exists
    """

    prevStmt, prevIdx = self._findPreviousNonBlankAtLevel(statements, beforeIdx, targetIndent)

    if prevStmt is None or prevStmt.blockType != BlockType.CONTROL:
      return False

    return self._hasBodyBetween(statements, prevIdx, beforeIdx, targetIndent)

  def _isClassDocstring(self, statements, docstringIdx, prevBlockType):
    """Check if statement at index is a class docstring

    :param statements: List of statements
    :param docstringIdx: Index of potential docstring
    :param prevBlockType: Block type of the statement
    :return: True if this is a class docstring
    """

    if prevBlockType != BlockType.DOCSTRING or docstringIdx is None:
      return False

    # Look back from the docstring to see if it follows a class definition
    for j in range(docstringIdx - 1, -1, -1):
      if not statements[j].isBlank:
        return self._isClassDefinition(statements[j])

    return False

  def _isModuleLevelDocstring(self, statements, docstringIdx, prevBlockType):
    """Check if statement at index is a module-level docstring

    :param statements: List of statements
    :param docstringIdx: Index of potential docstring
    :param prevBlockType: Block type of the statement
    :return: True if this is a module-level docstring
    """

    if prevBlockType != BlockType.DOCSTRING or docstringIdx is None:
      return False

    # Must be at indent level 0
    if statements[docstringIdx].indentLevel != 0:
      return False

    # Look back to see if there's anything before this docstring besides comments/blanks
    for j in range(docstringIdx - 1, -1, -1):
      if statements[j].isBlank or statements[j].isComment:
        continue

      # Found a non-comment, non-blank statement before the docstring
      return False

    # No non-comment statement found before docstring - it's module-level
    return True

  def _determineBlankLineForStatement(
    self,
    statements,
    currentIdx,
    stmt,
    startsNewScope,
    completedDefinitionBlock,
    completedControlBlock,
    returningFromNestedLevel,
    prevBlockType,
    prevStmtIdx,
    targetIndent,
  ):
    """Determine if current statement needs a blank line before it

    :param statements: List of statements
    :param currentIdx: Current statement index
    :param stmt: Current statement
    :param startsNewScope: Whether this starts a new scope
    :param completedDefinitionBlock: Whether a completed definition block precedes
    :param completedControlBlock: Whether a completed control block precedes
    :param returningFromNestedLevel: Whether returning from nested indentation
    :param prevBlockType: Previous block type
    :param prevStmtIdx: Previous statement index
    :param targetIndent: Target indentation level
    :return: True if blank line needed, False otherwise
    """

    # Rule 1: No blank line at start of new scope (highest priority)
    if startsNewScope:
      return False

    # Rule 2: After completed definition block
    if completedDefinitionBlock:
      return self._needsBlankLineBetween(BlockType.DEFINITION, stmt.blockType, stmt.indentLevel) > 0

    # Rule 3: After previous block type
    if prevBlockType is not None:
      # Special case: after comments, don't apply normal block transition rules
      if prevBlockType != BlockType.COMMENT:
        # Check if previous statement is a class or module-level docstring
        isClassDocstring = self._isClassDocstring(statements, prevStmtIdx, prevBlockType)
        isModuleLevelDocstring = self._isModuleLevelDocstring(statements, prevStmtIdx, prevBlockType)

        return (
          self._needsBlankLineBetween(
            prevBlockType, stmt.blockType, stmt.indentLevel, isClassDocstring, isModuleLevelDocstring
          )
          > 0
        )
      else:
        # After comment blocks, leave-as-is (no blank line added here)
        # EXCEPT: at module level, if next statement is a definition
        if stmt.indentLevel == 0 and stmt.blockType == BlockType.DEFINITION:
          # XXX: Check if there's a blank line between the comment and this definition
          # If there IS a blank line, always apply PEP 8 (2 blanks total)
          # If there's NO blank line, only add if no completed def before comment
          hasBlankAfterComment = False

          for j in range(currentIdx - 1, -1, -1):
            if statements[j].isBlank:
              hasBlankAfterComment = True

              break
            elif statements[j].isComment:
              break

          if hasBlankAfterComment:
            # There's already a blank after the comment - ensure we have 2 total
            return self._needsBlankLineBetween(BlockType.COMMENT, stmt.blockType, stmt.indentLevel) > 0
          else:
            # No blank after comment - only add if no completed def before comment
            hasCompletedDefBeforeComment = self._hasCompletedDefinitionBeforeComment(statements, currentIdx)

            if not hasCompletedDefBeforeComment:
              return self._needsBlankLineBetween(BlockType.COMMENT, stmt.blockType, stmt.indentLevel) > 0
            else:
              return False
        else:
          return False

    # Rule 4: After completed control block
    if completedControlBlock:
      return self._needsBlankLineBetween(BlockType.CONTROL, stmt.blockType, stmt.indentLevel) > 0

    # Rule 5: Returning from nested level
    if returningFromNestedLevel:
      return True

    # Default: no blank line
    return False

  def _applyRulesAtLevel(
    self,
    statements: list[Statement],
    shouldHaveBlankLine: list[bool],
    doNotAlterExistingNumberOfBlankLines: list[bool],
    startsNewScope: list[bool],
    targetIndent: int,
  ):
    """Apply rules at specific indentation level"""

    prevBlockType = None  # Includes skip-marked statements (for PEP 8 when skip at start)
    prevNonSkipBlockType = None  # Excludes skip-marked statements (for normal rule application)
    prevStmtIdx = None  # Track index of previous statement for class docstring detection

    for i, stmt in enumerate(statements):
      # Skip statements at different indentation levels
      if stmt.indentLevel != targetIndent and not stmt.isBlank:
        continue

      # Skip blank lines for rule processing (they will be reconstructed)
      if stmt.isBlank:
        continue

      # Handle spacing skip directive - preserve existing blank lines
      if stmt.skipBlankLineRules:
        # Count blank lines before this statement in original
        blankCount = 0

        for j in range(i - 1, -1, -1):
          if statements[j].isBlank:
            blankCount += 1
          else:
            break

        shouldHaveBlankLine[i] = blankCount > 0

        # Update prevBlockType so statements after the skip block can be properly compared
        # This is important when skip blocks are at the start of the file
        prevBlockType = stmt.blockType
        prevStmtIdx = i

        # Check if the NEXT non-blank statement should preserve its leading blank line
        # (to preserve blank lines after skip blocks)
        for j in range(i + 1, len(statements)):
          if not statements[j].isBlank:
            if not statements[j].skipBlankLineRules:  # Only if next is not also skip-marked
              # Check if there's a blank line before it
              if j > i + 1:  # There's at least one blank between them
                doNotAlterExistingNumberOfBlankLines[j] = True

            break

        continue

      # For comments, we need to check completedDefinitionBlock BEFORE the early exit
      # Check for completed definition blocks (needed for comments too)
      completedDefinitionBlock = self._hasCompletedDefinitionBlock(statements, i, targetIndent)

      if stmt.isComment:
        # Use prevNonSkipBlockType if available, else prevBlockType
        effectivePrevBlockType = prevNonSkipBlockType if prevNonSkipBlockType is not None else prevBlockType
        shouldHaveBlankLine[i] = self._applyCommentRules(
          completedDefinitionBlock,
          effectivePrevBlockType,
          stmt,
          startsNewScope[i],
        )

        # Comments cause a break - set both prev types to COMMENT
        prevBlockType = BlockType.COMMENT
        prevNonSkipBlockType = BlockType.COMMENT
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

      # Recompute completedDefinitionBlock for non-comments (already done for comments)
      if not stmt.isComment:
        completedDefinitionBlock = self._hasCompletedDefinitionBlock(statements, i, targetIndent)

      completedControlBlock = self._hasCompletedControlBlock(statements, i, targetIndent)
      returningFromNestedLevel = self._isReturningFromNestedLevel(statements, i, targetIndent)

      # Main blank line rules - use prevNonSkipBlockType if available, else prevBlockType
      effectivePrevBlockType = prevNonSkipBlockType if prevNonSkipBlockType is not None else prevBlockType
      shouldHaveBlankLine[i] = self._determineBlankLineForStatement(
        statements,
        i,
        stmt,
        startsNewScope[i],
        completedDefinitionBlock,
        completedControlBlock,
        returningFromNestedLevel,
        effectivePrevBlockType,
        prevStmtIdx,
        targetIndent,
      )
      prevBlockType = stmt.blockType
      prevNonSkipBlockType = stmt.blockType  # Normal statements update both
      prevStmtIdx = i

    # Recursively process nested indentation levels
    processedIndents = set()

    for stmt in statements:
      if stmt.indentLevel > targetIndent and stmt.indentLevel not in processedIndents:
        processedIndents.add(stmt.indentLevel)
        self._applyRulesAtLevel(
          statements, shouldHaveBlankLine, doNotAlterExistingNumberOfBlankLines, startsNewScope, stmt.indentLevel
        )

    return shouldHaveBlankLine

  def _convertToBlankLineCounts(
    self,
    statements: list[Statement],
    shouldHaveBlankLine: list[bool],
    doNotAlterExistingNumberOfBlankLines: list[bool],
    startsNewScope: list[bool],
  ) -> list[int]:
    """Convert boolean blank line indicators to actual counts
    :param statements: List of statements
    :type statements: list[Statement]
    :param shouldHaveBlankLine: Boolean indicators of where blank lines should exist
    :type shouldHaveBlankLine: list[bool]
    :param doNotAlterExistingNumberOfBlankLines: Boolean indicators of existing blank lines to not alter
    :type doNotAlterExistingNumberOfBlankLines: list[bool]
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

      # Don't alter existing blank lines after comments (leave-as-is rule)
      # BUT: if rules require MORE blank lines (e.g., PEP 8's 2 blanks), use those instead
      if doNotAlterExistingNumberOfBlankLines[i]:
        if shouldHaveBlankLine[i]:
          # Calculate what blank lines would normally be required
          # (continue with normal processing to get the count, then take max)
          # Fall through to normal processing
          pass
        else:
          # No blank line required by rules, keep the single blank
          blankLineCounts[i] = 1

          continue

      if not shouldHaveBlankLine[i]:
        continue

      # Find appropriate previous statement for blank line count calculation
      prevNonBlankIdx = -1
      immediatelyPrevIdx = -1

      # First, find the immediately preceding non-blank statement
      # For shouldHaveBlankLine determination, we skip over skip-marked statements
      # But for blank line COUNT determination (when shouldHaveBlankLine[i] is True),
      # we need to look at the immediate previous (even if skip-marked) to get the type
      skipPrevIdx = -1  # Previous statement skipping over skip-marked ones
      immediatePrevIdx = -1  # Immediate previous (including skip-marked)

      for j in range(i - 1, -1, -1):
        if not statements[j].isBlank:
          if immediatePrevIdx == -1:
            immediatePrevIdx = j

          if not statements[j].skipBlankLineRules and skipPrevIdx == -1:
            skipPrevIdx = j

          if immediatePrevIdx != -1 and skipPrevIdx != -1:
            break

      # Use skipPrevIdx for finding the "real" previous, fall back to immediatePrevIdx if no non-skip found
      immediatelyPrevIdx = skipPrevIdx if skipPrevIdx != -1 else immediatePrevIdx

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
        isModuleLevelDocstring = False

        if prevStmt.blockType == BlockType.DOCSTRING:
          # Check if it's a class or module-level docstring
          isClassDocstring = self._isClassDocstring(statements, prevNonBlankIdx, prevStmt.blockType)
          isModuleLevelDocstring = self._isModuleLevelDocstring(statements, prevNonBlankIdx, prevStmt.blockType)

        # Determine the effective block types
        # For comments, use BlockType.COMMENT regardless of what blockType field says
        prevBlockType = BlockType.COMMENT if prevStmt.isComment else prevStmt.blockType
        currentBlockType = BlockType.COMMENT if stmt.isComment else stmt.blockType

        # Use block-to-block configuration for blank line count
        blankLineCount = self._needsBlankLineBetween(
          prevBlockType, currentBlockType, stmt.indentLevel, isClassDocstring, isModuleLevelDocstring
        )

        # If doNotAlterExistingNumberOfBlankLines is set and we fell through, use max(1, calculated)
        if doNotAlterExistingNumberOfBlankLines[i]:
          blankLineCounts[i] = max(1, blankLineCount)
        else:
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

  def _needsBlankLineBetween(
    self, prevType, currentType, indentLevel=None, isClassDocstring=False, isModuleLevelDocstring=False
  ):
    """Determine number of blank lines needed between block types
    :param prevType: Previous block type
    :type prevType: BlockType
    :param currentType: Current block type
    :type currentType: BlockType
    :param indentLevel: Indentation level of current statement (for scope-aware rules)
    :type indentLevel: int
    :param isClassDocstring: True if prevType is a class docstring
    :type isClassDocstring: bool
    :param isModuleLevelDocstring: True if prevType is a module-level docstring
    :type isModuleLevelDocstring: bool
    :rtype: int
    """

    from .config import config

    return config.getBlankLines(prevType, currentType, indentLevel, isClassDocstring, isModuleLevelDocstring)
