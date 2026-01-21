"""
Pure helper functions for blank line rules.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from .types import BlockType, Statement


def findPreviousNonBlankAtLevel(statements, fromIdx, targetIndent):
  """Find previous non-blank statement at target indentation level

  :param statements: List of statements
  :type statements: list[Statement]
  :param fromIdx: Index to start searching backwards from
  :type fromIdx: int
  :param targetIndent: Indentation level to match
  :type targetIndent: int
  :rtype: tuple
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


def hasBodyBetween(statements, defIdx, endIdx, targetIndent):
  """Check if definition has indented body between two indices

  :param statements: List of statements
  :type statements: list[Statement]
  :param defIdx: Index of definition statement
  :type defIdx: int
  :param endIdx: Index to search up to
  :type endIdx: int
  :param targetIndent: Base indentation level
  :type targetIndent: int
  :rtype: bool
  :return: True if body exists
  """

  for k in range(defIdx + 1, endIdx):
    if statements[k].indentLevel > targetIndent:
      return True

  return False


def isClassDefinition(statement):
  """Check if a statement is a class definition

  :param statement: Statement to check
  :type statement: Statement
  :rtype: bool
  :return: True if statement is a class definition
  """

  if statement.blockType != BlockType.DEFINITION:
    return False

  # Check if any line starts with 'class ' (handles decorators)
  if statement.lines:
    for line in statement.lines:
      if line.strip().startswith('class '):
        return True

  return False
