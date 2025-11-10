"""
Multiline statement parser with bracket tracking.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""


class MultilineParser:
  """Handles multiline statement parsing with bracket tracking"""

  def __init__(self):
    self.reset()

  def reset(self):
    self.bracketStack = []
    self.inString = False
    self.stringDelimiter = None
    self.expectingDefinition = False

  def processLine(self, line: str):
    """Process line and update bracket state"""

    import re

    if re.match(r'^\s*@\w+', line.strip()):
      # Check for decorator
      self.expectingDefinition = True
    elif re.match(r'^\s*(async\s+)?(def|class)\s+', line.strip()):
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
            expected = {'(': ')', '[': ']', '{': '}'}

            if expected.get(self.bracketStack[-1]) == char:
              self.bracketStack.pop()

      i += 1

  def isComplete(self) -> bool:
    """Returns True if all brackets are closed and not in string"""

    return len(self.bracketStack) == 0 and not self.inString and not self.expectingDefinition
