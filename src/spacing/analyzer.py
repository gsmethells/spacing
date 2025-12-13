"""
Pass 1: File structure analysis and statement parsing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import re
from .classifier import StatementClassifier
from .parser import MultilineParser
from .types import BLANK_LINE_INDENT, BlockType, Statement

# Regex pattern to detect spacing skip directive (case-insensitive)
SPACING_SKIP_PATTERN = re.compile(r'#\s*spacing:\s*skip\b', re.IGNORECASE)


class FileAnalyzer:
  """Pass 1: Parse file into logical statements"""

  def analyzeFile(self, lines: list[str]) -> list[Statement]:
    """Parse file into logical statements

    :param lines: List of file lines to analyze
    :type lines: list[str]
    :rtype: list[Statement]
    :return: List of Statement objects representing logical code blocks
    :raises TypeError: If lines contains non-string elements (via MultilineParser.processLine)
    """

    statements = []
    parser = MultilineParser()
    currentStatement = []
    statementStart = 0

    for i, line in enumerate(lines):
      # If we're in a multiline statement (like a docstring), just add the line
      # Skip stripping for performance since we don't use stripped in this branch
      if currentStatement and parser.inString:
        currentStatement.append(line)
        parser.processLine(line)

        # Check if statement is complete after this line
        if parser.isComplete():
          statements.append(self._createStatement(currentStatement, statementStart, i))

          currentStatement = []

          parser.reset()

        continue

      # Only strip when needed (not in a string)
      stripped = line.strip()

      # Handle blank lines (only when not in a string or brackets)
      if not stripped:
        # If we're inside brackets (list, tuple, dict, etc.), skip blank lines entirely
        if currentStatement and parser.bracketStack:
          # Don't include blank lines in multiline statements
          continue

        if currentStatement:
          # Don't finish current statement if we're expecting a definition (decorator case)
          if not parser.expectingDefinition:
            # Finish current statement
            statements.append(self._createStatement(currentStatement, statementStart, i - 1))

            currentStatement = []

            parser.reset()

        # Add blank line as separate statement (only if not expecting definition and not in brackets)
        if not parser.expectingDefinition:
          statements.append(
            Statement(
              lines=[line],
              startLineIndex=i,
              endLineIndex=i,
              blockType=BlockType.CALL,  # Dummy value
              indentLevel=BLANK_LINE_INDENT,
              isBlank=True,
            )
          )

        continue

      # Handle comments (only when not in a string or brackets)
      if stripped.startswith('#'):
        # If we're in the middle of a multiline statement (e.g., inside brackets), include the comment
        if currentStatement and parser.bracketStack:
          currentStatement.append(line)
          continue

        if currentStatement:
          # Finish current statement
          statements.append(self._createStatement(currentStatement, statementStart, i - 1))

          currentStatement = []

          parser.reset()

        # Add comment as separate statement (only when not inside brackets)
        statements.append(
          Statement(
            lines=[line],
            startLineIndex=i,
            endLineIndex=i,
            blockType=BlockType.COMMENT,
            indentLevel=self._getIndentLevel(line),
            isComment=True,
          )
        )
        continue

      # Process code line
      if not currentStatement:
        statementStart = i

      currentStatement.append(line)
      parser.processLine(line)

      # Check if statement is complete
      if parser.isComplete():
        statements.append(self._createStatement(currentStatement, statementStart, i))

        currentStatement = []

        parser.reset()

    # Handle any remaining statement
    if currentStatement:
      statements.append(self._createStatement(currentStatement, statementStart, len(lines) - 1))

    # Process spacing directives (e.g., # spacing: skip)
    statements = self._processDirectives(statements)

    return statements

  def _createStatement(self, lines: list[str], startIdx: int, endIdx: int) -> Statement:
    """Create Statement object from lines

    :param lines: Lines comprising the statement (must be non-empty)
    :type lines: list[str]
    :param startIdx: Starting line index
    :type startIdx: int
    :param endIdx: Ending line index
    :type endIdx: int
    :rtype: Statement
    :raises ValueError: If lines is empty
    """

    if not lines:
      raise ValueError('Cannot create statement from empty lines list')

    blockType = StatementClassifier.classifyStatement(lines)
    indentLevel = self._getIndentLevel(lines[0])
    isSecondary = StatementClassifier.isSecondaryClause(lines[0])

    return Statement(
      lines=lines,
      startLineIndex=startIdx,
      endLineIndex=endIdx,
      blockType=blockType,
      indentLevel=indentLevel,
      isSecondaryClause=isSecondary,
    )

  def _getIndentLevel(self, line: str) -> int:
    """Calculate indentation level

    :param line: Line to calculate indentation for
    :type line: str
    :rtype: int
    :return: Indentation level in spaces, or BLANK_LINE_INDENT for blank lines
    """

    if not line.strip():
      return BLANK_LINE_INDENT  # Blank lines have no meaningful indentation

    from .config import config

    indent = 0

    for char in line:
      if char == ' ':
        indent += 1
      elif char == '\t':
        indent += config.indentWidth
      else:
        break

    return indent

  def _processDirectives(self, statements: list[Statement]) -> list[Statement]:
    """Process spacing directives like # spacing: skip

    Scans for standalone # spacing: skip comments and marks all consecutive
    statements (no blank lines between them) with skipBlankLineRules flag.
    The directive statement itself is removed from the list.

    :param statements: List of statements to process
    :type statements: list[Statement]
    :rtype: list[Statement]
    :return: Modified list with directives processed and applied
    """

    result = []
    skipDirectiveActive = False

    for stmt in statements:
      # Check if this is a spacing skip directive
      if stmt.isComment and self._hasSpacingSkipDirective(stmt):
        # Activate skip mode for following consecutive statements
        skipDirectiveActive = True

        # Keep the directive comment in the output (for idempotency)
        result.append(stmt)
        continue

      # If skip is active and this is not a blank line, mark the statement
      if skipDirectiveActive and not stmt.isBlank:
        stmt.skipBlankLineRules = True

        result.append(stmt)

      # If we hit a blank line, deactivate skip mode
      elif stmt.isBlank:
        skipDirectiveActive = False

        result.append(stmt)
      # Normal statement
      else:
        result.append(stmt)

    return result

  def _hasSpacingSkipDirective(self, stmt: Statement) -> bool:
    """Check if statement contains spacing skip directive

    :param stmt: Statement to check
    :type stmt: Statement
    :rtype: bool
    :return: True if statement contains # spacing: skip directive
    """

    if not stmt.lines:
      return False

    # Check the first (and typically only) line of the comment
    return bool(SPACING_SKIP_PATTERN.search(stmt.lines[0]))
