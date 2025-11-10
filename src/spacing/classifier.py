"""
Statement classification into block types.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import re
from .types import BlockType


class StatementClassifier:
  """Classifies statements into block types"""

  # Classification patterns in precedence order
  # Note: More specific patterns (keywords) should come before general patterns (assignments)
  PATTERNS = {
    BlockType.COMMENT: [
      r'^\s*#',  # Comment line
    ],
    BlockType.IMPORT: [
      r'^\s*(import|from)\s+',
    ],
    BlockType.DEFINITION: [
      r'^\s*@\w+',  # Decorator
      r'^\s*(async\s+)?(def|class)\s+',  # Function/class definition (including async def)
    ],
    BlockType.CONTROL: [
      r'^\s*(async\s+)?(if|elif|else|for|while|try|except|finally|with)(\s|:)',
    ],
    BlockType.FLOW_CONTROL: [
      r'^\s*(return|yield)(\s|$)',  # return, yield, yield from
    ],
    BlockType.ASSIGNMENT: [
      r'^\s*[\w\s\[\]\'.{}():+&?;@#%*|/",-]+\s*=(?!=)',  # Variable/tuple assignment (includes f-strings, method calls, and common string characters, but not ==)
      r'^\s*[\w.\[\]]+\s*[+\-*/%@&|^]=',  # Augmented assignment (+=, -=, *=, etc.)
      r'^\s*[\[\{].*=',  # Comprehension assignment
    ],
    BlockType.DECLARATION: [
      r'^\s*(global|nonlocal)\s+',
    ],
    BlockType.CALL: [
      r'^\s*(del|assert|pass|raise)(\s|$)',
      r'^\s*\w+\s*\(',  # Function call
    ],
  }
  SECONDARY_CLAUSES = r'^\s*(elif|else|except|finally)(\s|:)'

  # Pre-compiled regex patterns for performance
  COMPILED_PATTERNS = {
    blockType: [re.compile(pattern) for pattern in patterns] for blockType, patterns in PATTERNS.items()
  }
  COMPILED_SECONDARY_CLAUSES = re.compile(SECONDARY_CLAUSES)

  @classmethod
  def classifyStatement(cls, lines: list[str]) -> BlockType:
    """Classify multi-line statement by combining all lines"""

    if not lines:
      return BlockType.CALL

    # Combine all lines for classification
    combined = ' '.join(line.strip() for line in lines)
    firstLine = lines[0].strip()

    # Check for docstrings (triple-quoted strings)
    if firstLine.startswith('"""') or firstLine.startswith("'''"):
      return BlockType.DOCSTRING

    # Special check for method calls (e.g., obj.method(), obj[key].method()) before assignment check
    # This prevents misclassification of calls with keyword arguments
    # But exclude control keywords (if, for, while, etc.) and flow control (return, yield)
    # Also exclude if there's a closing bracket/paren followed by = (that's an assignment like dict[key()] = val)
    controlKeywords = r'^\s*(if|elif|else|for|while|try|except|finally|with|async|def|class|return|yield)\s'

    if (
      re.match(r'^[\w\.\[\]]+\s*\(', firstLine)
      and not re.search(r'[\]\)]\s*=', firstLine)  # Not assignment to dict/subscript
      and not re.match(controlKeywords, firstLine)
    ):
      return BlockType.CALL

    # Check patterns in precedence order using compiled patterns
    for blockType, compiledPatterns in cls.COMPILED_PATTERNS.items():
      for compiledPattern in compiledPatterns:
        if compiledPattern.search(combined) or compiledPattern.search(firstLine):
          return blockType

    return BlockType.CALL  # Default

  @classmethod
  def isSecondaryClause(cls, line: str) -> bool:
    """Check if line starts a secondary clause"""

    return bool(cls.COMPILED_SECONDARY_CLAUSES.match(line))
