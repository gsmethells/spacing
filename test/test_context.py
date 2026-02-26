"""
Unit tests for context builder.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.context import ContextBuilder
from spacing.types import BlockType, Statement


def createStatement(blockType, indentLevel, isComment=False, isBlank=False, isSecondaryClause=False):
  """Helper to create test statements

  :type blockType: BlockType
  :param blockType: Type of the statement
  :type indentLevel: int
  :param indentLevel: Indentation level
  :type isComment: bool
  :param isComment: Whether this is a comment
  :type isBlank: bool
  :param isBlank: Whether this is a blank line
  :type isSecondaryClause: bool
  :param isSecondaryClause: Whether this is a secondary clause
  :rtype: Statement
  :return: Statement object for testing
  """

  return Statement(
    lines=['test'],
    startLineIndex=0,
    endLineIndex=0,
    blockType=blockType,
    indentLevel=indentLevel,
    isComment=isComment,
    isBlank=isBlank,
    isSecondaryClause=isSecondaryClause,
  )


class TestContextBuilder:
  """Test suite for ContextBuilder class"""

  def test_initializeContexts(self):
    """Test _initializeContexts creates correct number of contexts"""

    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.ASSIGNMENT, 0),
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)

    assert len(contexts) == 3
    assert contexts[0].index == 0
    assert contexts[0].statement == statements[0]
    assert contexts[1].index == 1
    assert contexts[1].statement == statements[1]
    assert contexts[2].index == 2
    assert contexts[2].statement == statements[2]

  def test_computePrevNextBasic(self):
    """Test _computePrevNext links statements correctly"""

    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.ASSIGNMENT, 0),
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)

    # First statement has no previous
    assert contexts[0].prevNonBlank is None
    assert contexts[0].prevNonBlankIdx == -1
    assert contexts[0].nextNonBlank == statements[1]
    assert contexts[0].nextNonBlankIdx == 1

    # Middle statement links both ways
    assert contexts[1].prevNonBlank == statements[0]
    assert contexts[1].prevNonBlankIdx == 0
    assert contexts[1].nextNonBlank == statements[2]
    assert contexts[1].nextNonBlankIdx == 2

    # Last statement has no next
    assert contexts[2].prevNonBlank == statements[1]
    assert contexts[2].prevNonBlankIdx == 1
    assert contexts[2].nextNonBlank is None
    assert contexts[2].nextNonBlankIdx == -1

  def test_computePrevNextWithBlanks(self):
    """Test _computePrevNext skips blank lines"""

    statements = [
      createStatement(BlockType.ASSIGNMENT, 0),
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),
      createStatement(BlockType.ASSIGNMENT, 0),
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)

    # First non-blank links to last non-blank (skipping blanks)
    assert contexts[0].nextNonBlank == statements[3]
    assert contexts[0].nextNonBlankIdx == 3

    # Last non-blank links to first non-blank (skipping blanks)
    assert contexts[3].prevNonBlank == statements[0]
    assert contexts[3].prevNonBlankIdx == 0

    # Blank lines have no prev/next
    assert contexts[1].prevNonBlank is None
    assert contexts[1].nextNonBlank is None
    assert contexts[2].prevNonBlank is None
    assert contexts[2].nextNonBlank is None

  def test_computeScopeInfoNewScope(self):
    """Test _computeScopeInfo detects new scopes"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1  <- starts new scope
      createStatement(BlockType.ASSIGNMENT, 2),  #   y = 2
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeScopeInfo(statements, contexts)

    assert not contexts[0].startsNewScope
    assert contexts[1].startsNewScope  # First statement after definition
    assert not contexts[2].startsNewScope

  def test_computeScopeInfoControlBlock(self):
    """Test _computeScopeInfo detects new scopes after control blocks"""

    statements = [
      createStatement(BlockType.CONTROL, 0),  # if x:
      createStatement(BlockType.ASSIGNMENT, 2),  #   y = 1  <- starts new scope
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeScopeInfo(statements, contexts)

    assert contexts[1].startsNewScope

  def test_computeScopeInfoSecondaryClause(self):
    """Test _computeScopeInfo detects new scopes after secondary clauses"""

    statements = [
      createStatement(BlockType.CONTROL, 0),  # if x:
      createStatement(BlockType.ASSIGNMENT, 2),  #   y = 1
      createStatement(BlockType.CONTROL, 0, isSecondaryClause=True),  # else:
      createStatement(BlockType.ASSIGNMENT, 2),  #   z = 2  <- starts new scope
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeScopeInfo(statements, contexts)

    assert contexts[1].startsNewScope  # After if
    assert contexts[3].startsNewScope  # After else

  def test_computeScopeInfoReturningFromNested(self):
    """Test _computeScopeInfo detects returning from nested levels"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.CONTROL, 2),  #   if y:
      createStatement(BlockType.ASSIGNMENT, 4),  #     z = 2
      createStatement(BlockType.ASSIGNMENT, 2),  #   w = 3  <- returning from nested
      createStatement(BlockType.ASSIGNMENT, 0),  # a = 4  <- returning from nested
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeScopeInfo(statements, contexts)

    assert not contexts[0].returningFromNestedLevel
    assert not contexts[1].returningFromNestedLevel
    assert not contexts[2].returningFromNestedLevel
    assert not contexts[3].returningFromNestedLevel
    assert contexts[4].returningFromNestedLevel  # Back to indent 2 from 4
    assert contexts[5].returningFromNestedLevel  # Back to indent 0 from 2

  def test_computeCompletedBlocksDefinition(self):
    """Test _computeCompletedBlocks identifies completed definition blocks"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.DEFINITION, 0),  # def bar():  <- after completed def
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCompletedBlocks(statements, contexts)

    assert not contexts[0].hasCompletedDefBefore
    assert not contexts[1].hasCompletedDefBefore
    assert contexts[2].hasCompletedDefBefore  # foo() is complete

  def test_computeCompletedBlocksControl(self):
    """Test _computeCompletedBlocks identifies completed control blocks"""

    statements = [
      createStatement(BlockType.CONTROL, 0),  # if x:
      createStatement(BlockType.ASSIGNMENT, 2),  #   y = 1
      createStatement(BlockType.ASSIGNMENT, 0),  # z = 2  <- after completed control
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCompletedBlocks(statements, contexts)

    assert not contexts[0].hasCompletedControlBefore
    assert not contexts[1].hasCompletedControlBefore
    assert contexts[2].hasCompletedControlBefore  # if block is complete

  def test_computeCompletedBlocksNoBodyNoCompletion(self):
    """Test _computeCompletedBlocks requires body to mark as completed"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.DEFINITION, 0),  # def bar():  <- no body between
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCompletedBlocks(statements, contexts)

    assert not contexts[0].hasCompletedDefBefore
    assert not contexts[1].hasCompletedDefBefore  # No body, so not completed

  def test_computeCommentPreservationBasic(self):
    """Test _computeCommentPreservation marks blank lines adjacent to comments"""

    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),  # (blank)
      createStatement(BlockType.ASSIGNMENT, 0),  # x = 1  <- preserve blank before
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCommentPreservation(statements, contexts)

    assert contexts[2].preserveBlankLines  # Blank after comment

  def test_computeCommentPreservationModuleLevelDefException(self):
    """Test _computeCommentPreservation does not preserve for module-level definitions after comments"""

    statements = [
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),  # (blank)
      createStatement(BlockType.DEFINITION, 0),  # def foo():  <- don't preserve (PEP 8)
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCommentPreservation(statements, contexts)

    assert not contexts[2].preserveBlankLines  # PEP 8 overrides preservation

  def test_computeCommentPreservationCommentAfterDef(self):
    """Test _computeCommentPreservation does not preserve for comment after module-level definition"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.ASSIGNMENT, 0, isBlank=True),  # (blank)
      createStatement(BlockType.COMMENT, 0, isComment=True),  # # comment  <- don't preserve (PEP 8)
    ]

    builder = ContextBuilder()
    contexts = builder._initializeContexts(statements)
    builder._computePrevNext(statements, contexts)
    builder._computeCommentPreservation(statements, contexts)

    assert not contexts[3].preserveBlankLines  # PEP 8 overrides preservation

  def test_buildContextsIntegration(self):
    """Test buildContexts integration with all methods"""

    statements = [
      createStatement(BlockType.DEFINITION, 0),  # def foo():
      createStatement(BlockType.ASSIGNMENT, 2),  #   x = 1
      createStatement(BlockType.DEFINITION, 0),  # def bar():
      createStatement(BlockType.ASSIGNMENT, 2),  #   y = 2
    ]

    builder = ContextBuilder()
    contexts = builder.buildContexts(statements)

    # Check all contexts created
    assert len(contexts) == 4

    # Check prev/next links
    assert contexts[0].nextNonBlank == statements[1]
    assert contexts[1].prevNonBlank == statements[0]
    assert contexts[1].nextNonBlank == statements[2]
    assert contexts[2].prevNonBlank == statements[1]

    # Check scope detection
    assert contexts[1].startsNewScope  # After def foo()
    assert contexts[3].startsNewScope  # After def bar()

    # Check completed blocks
    assert contexts[2].hasCompletedDefBefore  # foo() is complete

  def test_buildContextsEmptyList(self):
    """Test buildContexts handles empty statement list"""

    builder = ContextBuilder()
    contexts = builder.buildContexts([])

    assert contexts == []

  def test_buildContextsSingleStatement(self):
    """Test buildContexts handles single statement"""

    statements = [createStatement(BlockType.ASSIGNMENT, 0)]

    builder = ContextBuilder()
    contexts = builder.buildContexts(statements)

    assert len(contexts) == 1
    assert contexts[0].prevNonBlank is None
    assert contexts[0].nextNonBlank is None
    assert not contexts[0].startsNewScope
    assert not contexts[0].returningFromNestedLevel
