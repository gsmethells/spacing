"""
Core types and data structures for spacing.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from dataclasses import dataclass
from enum import Enum


class BlockType(Enum):
  """Block types for statement classification

  Enum values represent different Python statement categories used
  for determining blank line placement between code blocks.

  - ASSIGNMENT: Variable assignments, comprehensions, lambdas
  - CALL: Function calls, del, assert, pass, raise statements
  - IMPORT: Import and from-import statements
  - CONTROL: Control flow structures (if, for, while, try, with)
  - DEFINITION: Function and class definitions (including decorators)
  - DECLARATION: Variable scope declarations (global, nonlocal)
  - DOCSTRING: Triple-quoted documentation strings
  - COMMENT: Single-line comments starting with #
  - FLOW_CONTROL: Return and yield statements
  - TYPE_ANNOTATION: Type annotations (PEP 526) with or without default values
  """

  ASSIGNMENT = 1
  CALL = 2
  IMPORT = 3
  CONTROL = 4
  DEFINITION = 5
  DECLARATION = 6
  DOCSTRING = 7
  COMMENT = 8
  FLOW_CONTROL = 9  # return, yield, yield from
  TYPE_ANNOTATION = 10  # Type annotations (name: Type or name: Type = value)


# Sentinel value for indentation level of blank lines
BLANK_LINE_INDENT = -1


@dataclass
class Statement:
  """Represents a logical statement that may span multiple lines"""

  lines: list[str]
  startLineIndex: int
  endLineIndex: int
  blockType: BlockType
  indentLevel: int
  isComment: bool = False
  isBlank: bool = False
  isSecondaryClause: bool = False
  skipBlankLineRules: bool = False
