"""
Unit tests for core types and data structures.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.types import BlockType, Statement


class TestBlockType:
  def testBlockTypeEnumValues(self):
    """Test BlockType enum has correct values and precedence order"""

    assert BlockType.ASSIGNMENT.value == 1
    assert BlockType.CALL.value == 2
    assert BlockType.IMPORT.value == 3
    assert BlockType.CONTROL.value == 4
    assert BlockType.DEFINITION.value == 5
    assert BlockType.DECLARATION.value == 6

  def testBlockTypePrecedence(self):
    """Test BlockType precedence ordering"""

    # Assignment has highest precedence (lowest number)
    assert BlockType.ASSIGNMENT.value < BlockType.CALL.value
    assert BlockType.CALL.value < BlockType.IMPORT.value
    assert BlockType.IMPORT.value < BlockType.CONTROL.value
    assert BlockType.CONTROL.value < BlockType.DEFINITION.value
    assert BlockType.DEFINITION.value < BlockType.DECLARATION.value

  def testBlockTypeNames(self):
    """Test BlockType enum names"""

    assert BlockType.ASSIGNMENT.name == 'ASSIGNMENT'
    assert BlockType.CALL.name == 'CALL'
    assert BlockType.IMPORT.name == 'IMPORT'
    assert BlockType.CONTROL.name == 'CONTROL'
    assert BlockType.DEFINITION.name == 'DEFINITION'
    assert BlockType.DECLARATION.name == 'DECLARATION'


class TestStatement:
  def testStatementCreation(self):
    """Test Statement dataclass creation"""

    lines = ['x = 1']
    stmt = Statement(lines=lines, startLineIndex=0, endLineIndex=0, blockType=BlockType.ASSIGNMENT, indentLevel=0)

    assert stmt.lines == lines
    assert stmt.startLineIndex == 0
    assert stmt.endLineIndex == 0
    assert stmt.blockType == BlockType.ASSIGNMENT
    assert stmt.indentLevel == 0
    assert not stmt.isComment  # Default
    assert not stmt.isBlank  # Default
    assert not stmt.isSecondaryClause  # Default

  def testStatementWithAllFields(self):
    """Test Statement with all fields specified"""

    lines = ['# Comment']
    stmt = Statement(
      lines=lines,
      startLineIndex=5,
      endLineIndex=5,
      blockType=BlockType.CALL,
      indentLevel=2,
      isComment=True,
      isBlank=False,
      isSecondaryClause=False,
    )

    assert stmt.lines == lines
    assert stmt.startLineIndex == 5
    assert stmt.endLineIndex == 5
    assert stmt.blockType == BlockType.CALL
    assert stmt.indentLevel == 2
    assert stmt.isComment
    assert not stmt.isBlank
    assert not stmt.isSecondaryClause

  def testStatementMultiline(self):
    """Test Statement for multiline statement"""

    lines = ['result = func(', '  arg1,', '  arg2', ')']
    stmt = Statement(lines=lines, startLineIndex=10, endLineIndex=13, blockType=BlockType.ASSIGNMENT, indentLevel=0)

    assert len(stmt.lines) == 4
    assert stmt.startLineIndex == 10
    assert stmt.endLineIndex == 13
    assert stmt.blockType == BlockType.ASSIGNMENT

  def testStatementBlankLine(self):
    """Test Statement for blank line"""

    stmt = Statement(
      lines=[''],
      startLineIndex=2,
      endLineIndex=2,
      blockType=BlockType.CALL,  # Dummy value for blank lines
      indentLevel=-1,
      isBlank=True,
    )

    assert stmt.lines == ['']
    assert stmt.isBlank
    assert stmt.indentLevel == -1

  def testStatementSecondaryClause(self):
    """Test Statement for secondary clause"""

    stmt = Statement(
      lines=['else:'],
      startLineIndex=8,
      endLineIndex=8,
      blockType=BlockType.CONTROL,
      indentLevel=0,
      isSecondaryClause=True,
    )

    assert stmt.isSecondaryClause
    assert stmt.blockType == BlockType.CONTROL

  def testStatementEquality(self):
    """Test Statement equality comparison"""

    stmt1 = Statement(lines=['x = 1'], startLineIndex=0, endLineIndex=0, blockType=BlockType.ASSIGNMENT, indentLevel=0)
    stmt2 = Statement(lines=['x = 1'], startLineIndex=0, endLineIndex=0, blockType=BlockType.ASSIGNMENT, indentLevel=0)

    assert stmt1 == stmt2

  def testStatementInequality(self):
    """Test Statement inequality comparison"""

    stmt1 = Statement(lines=['x = 1'], startLineIndex=0, endLineIndex=0, blockType=BlockType.ASSIGNMENT, indentLevel=0)
    stmt2 = Statement(lines=['y = 2'], startLineIndex=0, endLineIndex=0, blockType=BlockType.ASSIGNMENT, indentLevel=0)

    assert stmt1 != stmt2
