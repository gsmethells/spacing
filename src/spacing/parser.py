"""
Multiline statement parser with bracket tracking.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import re


class MultilineParser:
  """Handles multiline statement parsing with bracket tracking"""

  # Pre-compiled regex patterns for performance
  DECORATOR_PATTERN = re.compile(r'^\s*@\w+')
  DEFINITION_PATTERN = re.compile(r'^\s*(async\s+)?(def|class)\s+')

  # Bracket matching pairs
  BRACKET_PAIRS = {'(': ')', '[': ']', '{': '}'}

  def __init__(self):
    self.reset()

  def reset(self):
    self.bracketStack = []
    self.inString = False
    self.stringDelimiter = None
    self.expectingDefinition = False

  def processLine(self, line: str):
    """Process line and update bracket state

    :param line: Line to process
    :type line: str
    :raises TypeError: If line is not a string
    """

    # Input validation
    if not isinstance(line, str):
      raise TypeError(f'Expected str, got {type(line).__name__}')

    # Only check for decorators/definitions when NOT inside a string
    # Otherwise we'll incorrectly match patterns inside multiline strings
    if not self.inString:
      if self.DECORATOR_PATTERN.match(line.strip()):
        # Check for decorator
        self.expectingDefinition = True
      elif self.DEFINITION_PATTERN.match(line.strip()):
        # Check for function/class definition (including async def)
        self.expectingDefinition = False
      else:
        # Regular line - no action needed for expectingDefinition
        pass

    i = 0

    while i < len(line):
      char = line[i]

      # Handle comments: stop processing when we hit # (unless we're in a string)
      if char == '#' and not self.inString:
        break

      # Handle escape sequences
      if char == '\\' and i + 1 < len(line):
        i += 2

        continue

      # Handle string literals
      if char in ['"', "'"]:
        if not self.inString:
          # Check for triple quotes
          if i + 2 < len(line) and line[i : i + 3] == char * 3:
            self.inString = True
            self.stringDelimiter = char * 3
            i += 3

            continue
          else:
            self.inString = True
            self.stringDelimiter = char
        elif self.stringDelimiter == char or (
          len(self.stringDelimiter) == 3 and i + 3 <= len(line) and line[i : i + 3] == self.stringDelimiter
        ):
          # Check if we need to skip 3 characters BEFORE clearing stringDelimiter
          skipThree = len(self.stringDelimiter) == 3
          self.inString = False
          self.stringDelimiter = None

          if skipThree:
            i += 3

            continue

      if not self.inString:
        if char in '([{':
          self.bracketStack.append(char)
        elif char in ')]}':
          if self.bracketStack:
            if self.BRACKET_PAIRS.get(self.bracketStack[-1]) == char:
              self.bracketStack.pop()

      i += 1

  def isComplete(self) -> bool:
    """Check if current statement is complete

    A statement is considered complete when all of these conditions are met:
    - All opening brackets ( [ { have matching closing brackets ) ] }
    - Not currently inside a string literal (single/double/triple quoted)
    - Not expecting a definition after a decorator (@decorator)

    :rtype: bool
    :return: True if statement is complete, False if more lines needed
    """

    return len(self.bracketStack) == 0 and not self.inString and not self.expectingDefinition
