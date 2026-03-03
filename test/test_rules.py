"""
Unit tests for blank line rule engine.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

from spacing.config import BlankLineConfig, setConfig
from spacing.processor import FileProcessor
from spacing.rules import BlankLineRuleEngine
from spacing.types import BlockType, Statement


class TestBlankLineRuleEngine:
  def createStatement(self, blockType, indentLevel=0, isComment=False, isBlank=False, isSecondaryClause=False):
    """Helper to create test statements"""

    return Statement(
      lines=['dummy'],
      startLineIndex=0,
      endLineIndex=0,
      blockType=blockType,
      indentLevel=indentLevel,
      isComment=isComment,
      isBlank=isBlank,
      isSecondaryClause=isSecondaryClause,
    )

  def test_sameBlockType(self):
    """Test no blank line between same block types (except Control/Definition)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0]

  def test_differentBlockTypes(self):
    """Test blank line between different block types"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.IMPORT),
      self.createStatement(BlockType.ASSIGNMENT),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before second statement

  def test_consecutiveControlBlocks(self):
    """Test consecutive Control blocks need separation"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.CONTROL),
      self.createStatement(BlockType.CONTROL),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before second control block

  def test_consecutiveDefinitionBlocks(self):
    """Test consecutive Definition blocks at module level (PEP 8: 2 blank lines)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=0),
      self.createStatement(BlockType.DEFINITION, indentLevel=0),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 2]  # PEP 8: 2 blank lines at module level

  def test_consecutiveDefinitionBlocksNested(self):
    """Test consecutive Definition blocks inside class (PEP 8: 1 blank line)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=2),
      self.createStatement(BlockType.DEFINITION, indentLevel=2),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # PEP 8: 1 blank line inside class

  def test_secondaryClauseRule(self):
    """Test no blank line before secondary clauses"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.CONTROL),  # if
      self.createStatement(BlockType.CONTROL, isSecondaryClause=True),  # else
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0]  # No blank line before else

  def test_commentBreakRule(self):
    """Test blank line before comments (comment break rule)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 1]  # Blank line before comment

  def test_blankLinesIgnored(self):
    """Test blank lines are ignored in rule processing"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isBlank=True),
      self.createStatement(BlockType.CALL),
    ]
    result = engine.applyRules(statements)

    assert result == [0, 0, 1]  # Blank line before CALL (different from ASSIGNMENT)

  def test_indentationLevelProcessing(self):
    """Test rules applied independently at each indentation level"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=0),
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # Nested
      self.createStatement(BlockType.CALL, indentLevel=2),  # Nested different type
      self.createStatement(BlockType.CALL, indentLevel=0),  # Back to level 0
    ]
    result = engine.applyRules(statements)

    # Level 0: ASSIGNMENT -> CALL (different types, need blank line)
    # Level 2: ASSIGNMENT -> CALL (different types, need blank line)
    assert result == [0, 0, 1, 1]

  def test_emptyStatements(self):
    """Test handling of empty statement list"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    result = engine.applyRules([])

    assert result == []

  def test_complexScenario(self):
    """Test complex scenario with multiple rules"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.IMPORT),  # 0: import
      self.createStatement(BlockType.IMPORT),  # 1: import (same type)
      self.createStatement(BlockType.ASSIGNMENT),  # 2: assignment (different type)
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),  # 3: comment (comment break)
      self.createStatement(BlockType.CALL),  # 4: call (after comment)
      self.createStatement(BlockType.CONTROL),  # 5: if (different type)
      self.createStatement(BlockType.CONTROL, isSecondaryClause=True),  # 6: else (secondary clause)
      self.createStatement(BlockType.CONTROL),  # 7: another if (consecutive control)
    ]
    result = engine.applyRules(statements)
    expected = [
      0,  # 0: first statement
      0,  # 1: same type as previous (import)
      1,  # 2: different type (assignment after import)
      1,  # 3: comment break rule
      0,  # 4: after comment reset
      1,  # 5: different type (control after call)
      0,  # 6: secondary clause rule (no blank before else)
      1,  # 7: consecutive control blocks rule
    ]

    assert result == expected

  def test_commentBreakRuleRegression(self):
    """Regression test for comment break rule bug (original issue)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT),
      self.createStatement(BlockType.ASSIGNMENT, isComment=True),
    ]
    result = engine.applyRules(statements)

    # Comment should get blank line despite same block type
    assert result == [0, 1]

  def test_indentationProcessingRegression(self):
    """Regression test for indentation level processing bug (original issue)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=0),
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # Nested
      self.createStatement(BlockType.CALL, indentLevel=2),  # Nested different type
      self.createStatement(BlockType.CALL, indentLevel=0),  # Back to level 0
    ]
    result = engine.applyRules(statements)

    # Should get blank lines: none, none, different types at level 2, returning from nested
    assert result == [0, 0, 1, 1]

  def test_commentBlankLinePreservation(self):
    """Test that existing blank lines after comments are preserved (leave-as-is rule)"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      # Copyright header scenario
      self.createStatement(BlockType.COMMENT, isComment=True),  # 0: # Copyright line 1
      self.createStatement(BlockType.COMMENT, isComment=True),  # 1: # Copyright line 2
      self.createStatement(BlockType.COMMENT, isComment=True),  # 2: # Copyright line 3
      self.createStatement(BlockType.CALL, isBlank=True),  # 3: blank line after comment
      self.createStatement(BlockType.IMPORT),  # 4: import statement
      self.createStatement(BlockType.ASSIGNMENT),  # 5: assignment statement
    ]
    result = engine.applyRules(statements)

    # Expected: no blank before comments, preserve existing blank after comment block
    # 0: first comment (no blank line)
    # 1: second comment (no blank line - same type)
    # 2: third comment (no blank line - same type)
    # 3: blank line (skipped in processing)
    # 4: import after comment block (should preserve existing blank line)
    # 5: assignment after import (different type)
    assert result == [0, 0, 0, 0, 1, 1]

  def test_commentWithoutBlankLineFollowing(self):
    """Test that no blank line is added after comment when none exists"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.COMMENT, isComment=True),  # 0: comment
      self.createStatement(BlockType.IMPORT),  # 1: import (no blank between)
      self.createStatement(BlockType.ASSIGNMENT),  # 2: assignment
    ]
    result = engine.applyRules(statements)

    # Expected: no blank after comment when none exists originally
    # 0: first comment (no blank line)
    # 1: import after comment (no blank preserved since none existed)
    # 2: assignment after import (different type gets blank line)
    assert result == [0, 0, 1]

  def test_blankLineAfterTryExceptInFunctionBody(self):
    """Regression test: blank line should be added after try/except completes in function body"""

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      self.createStatement(BlockType.DEFINITION, indentLevel=0),  # 0: def foo():
      self.createStatement(BlockType.CONTROL, indentLevel=2),  # 1: try:
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=4),  # 2: x = 1
      self.createStatement(BlockType.CALL, indentLevel=2, isSecondaryClause=True),  # 3: except:
      self.createStatement(BlockType.CALL, indentLevel=4),  # 4: print(...)
      self.createStatement(BlockType.ASSIGNMENT, indentLevel=2),  # 5: y = 2
    ]
    result = engine.applyRules(statements)

    # Expected: blank line before statement after try/except completes
    # Statement 5 (y = 2) comes after the try/except CONTROL block completes
    # Since we're in a function body, CONTROL -> ASSIGNMENT should get a blank line
    assert result == [0, 0, 0, 0, 0, 1]

  def test_commentParagraphSeparationPreserved(self):
    """Regression: Blank lines between comment blocks (comment paragraphs) should be preserved"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    # Input with blank lines separating comment paragraphs
    inputCode = """def setup():
  from catapult.lang.console import promptForAnswer, promptYesOrNo

  # Define the base environment variables

  # Stage
  if JOINTS_STAGE not in environ or environ[JOINTS_STAGE] not in STAGES:
    environ[JOINTS_STAGE] = promptForAnswer('What stage is this system currently in', STAGES, PRODUCTION)

  # Architecture check
  isProduction = environ[JOINTS_STAGE] == PRODUCTION
  cpuCount = getCPUCount()

  # XXX: Important implementation note goes here
  #
  # This comment block has multiple lines
  # but it's a single paragraph
  #

  # Define the default environment variable values
  # Any environment variable with a defined value will not be prompted for later
  defaults = {}
"""

    # Expected: preserve blank lines directly adjacent to comments only
    expectedCode = """def setup():
  from catapult.lang.console import promptForAnswer, promptYesOrNo

  # Define the base environment variables

  # Stage
  if JOINTS_STAGE not in environ or environ[JOINTS_STAGE] not in STAGES:
    environ[JOINTS_STAGE] = promptForAnswer('What stage is this system currently in', STAGES, PRODUCTION)

  # Architecture check
  isProduction = environ[JOINTS_STAGE] == PRODUCTION
  cpuCount = getCPUCount()

  # XXX: Important implementation note goes here
  #
  # This comment block has multiple lines
  # but it's a single paragraph
  #

  # Define the default environment variable values
  # Any environment variable with a defined value will not be prompted for later
  defaults = {}
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Comment paragraph separation should be preserved\nGot:\n{result}'
      assert not changed, 'Input already correctly formatted - no changes needed'

  def test_decoratedClassDocstringAlwaysGetsBlankLine(self):
    """Regression: Decorated class docstrings should always have 1 blank line after them"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    # Set after_docstring = 0 to verify class docstrings are NOT affected
    config = BlankLineConfig.fromDefaults()
    config.afterDocstring = 0

    setConfig(config)

    inputCode = '''@dataclass
class DICOMPushRequest:
  """Event payload representing a request to push a study"""

  source: 'PushSource'
  destination: 'AEConfiguration'
'''

    # Expected: Class docstrings ALWAYS get 1 blank line (PEP 257), regardless of after_docstring config
    expectedCode = '''@dataclass
class DICOMPushRequest:
  """Event payload representing a request to push a study"""

  source: 'PushSource'
  destination: 'AEConfiguration'
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Decorated class docstrings must have 1 blank line\nGot:\n{result}'
      assert not changed, 'Input already has correct formatting'

    # Reset config to defaults to avoid test pollution
    defaultConfig = BlankLineConfig.fromDefaults()

    setConfig(defaultConfig)

  def test_consecutiveControlBlocksGetBlankLine(self):
    """Regression: Consecutive if statements (control blocks) should have blank line between them"""

    import tempfile
    from pathlib import Path
    from spacing.processor import FileProcessor

    inputCode = '''def makeDir(path):
  """Docstring"""
  if (not wasDir or forceGroup) and isDir:
    chgrp(path, groupname)

  if (not wasDir or forceMode) and isDir:
    chmod(path, mode)
'''

    # Expected: blank line after docstring added, blank line between consecutive control blocks preserved
    expectedCode = '''def makeDir(path):
  """Docstring"""

  if (not wasDir or forceGroup) and isDir:
    chgrp(path, groupname)

  if (not wasDir or forceMode) and isDir:
    chmod(path, mode)
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Consecutive if statements should keep blank line\nGot:\n{result}'

  def test_pep8TwoBlankLinesBeforeCommentAtModuleLevel(self):
    """Regression: 2 blank lines before comment after module-level class definition"""

    import tempfile
    from pathlib import Path

    inputLines = [
      'class Foo:\n',
      '  pass\n',
      '\n',
      '# Comment before module-level variable\n',
      'x = 1\n',
    ]
    expectedLines = [
      'class Foo:\n',
      '  pass\n',
      '\n',
      '\n',
      '# Comment before module-level variable\n',
      'x = 1\n',
    ]
    inputCode = ''.join(inputLines)
    expectedCode = ''.join(expectedLines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Expected 2 blank lines before comment after class definition\nGot:\n{result}'

  def test_pep8TwoBlankLinesBetweenDefinitionsWithComment(self):
    """Regression: 2 blank lines between top-level definitions even with comment in between"""

    import tempfile
    from pathlib import Path

    inputLines = [
      'def foo():\n',
      '  pass\n',
      '\n',
      '# Comment\n',
      'def bar():\n',
      '  pass\n',
    ]
    expectedLines = [
      'def foo():\n',
      '  pass\n',
      '\n',
      '\n',
      '# Comment\n',
      'def bar():\n',
      '  pass\n',
    ]
    inputCode = ''.join(inputLines)
    expectedCode = ''.join(expectedLines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Expected 2 blank lines before comment between definitions\nGot:\n{result}'

  def test_pep8TwoBlankLinesAfterCommentBeforeDefinition(self):
    """Regression: 2 blank lines after comment when followed by module-level definition

    This tests the case where a comment appears BETWEEN two top-level definitions.
    PEP 8 requires 2 blank lines between top-level definitions, even with a comment.
    """

    import tempfile
    from pathlib import Path

    inputLines = [
      'class TestReconciler(unittest.TestCase):\n',
      '  pass\n',
      '\n',
      '# Hash tests moved to test_algorithms.py\n',
      '\n',  # Only 1 blank line initially
      'class TestDuplicateRuleValidation(TestReconciler):\n',
      '  pass\n',
    ]
    expectedLines = [
      'class TestReconciler(unittest.TestCase):\n',
      '  pass\n',
      '\n',
      '\n',
      '# Hash tests moved to test_algorithms.py\n',
      '\n',
      '\n',  # Should add another blank line here (2 total after comment)
      'class TestDuplicateRuleValidation(TestReconciler):\n',
      '  pass\n',
    ]
    inputCode = ''.join(inputLines)
    expectedCode = ''.join(expectedLines)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(inputCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as resultFile:
        result = resultFile.read()

      assert result == expectedCode, f'Expected 2 blank lines after comment before definition\nGot:\n{result}'

  def test_determineBlankLineWithoutPreserveHasCompletedDefBefore(self):
    """_determineBlankLineWithoutPreserve hits hasCompletedDefBefore when preserveBlankLines is set by a skip block

    When a skip block (def + body) is followed by a blank then a module-level definition,
    the second definition has preserveBlankLines=True (from the skip block).
    It also has hasCompletedDefBefore=True (the first def has a body).
    The result is max(1 existing blank, 2 required by PEP 8) = 2.
    This covers line 172 of rules.py.
    """

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      Statement(
        lines=['def foo():\n'],
        startLineIndex=0,
        endLineIndex=0,
        blockType=BlockType.DEFINITION,
        indentLevel=0,
        skipBlankLineRules=True,
      ),
      Statement(
        lines=['  pass\n'],
        startLineIndex=1,
        endLineIndex=1,
        blockType=BlockType.CALL,
        indentLevel=2,
        skipBlankLineRules=True,
      ),
      Statement(
        lines=['\n'], startLineIndex=2, endLineIndex=2, blockType=BlockType.ASSIGNMENT, indentLevel=-1, isBlank=True
      ),
      Statement(
        lines=['def bar():\n'], startLineIndex=3, endLineIndex=3, blockType=BlockType.DEFINITION, indentLevel=0
      ),
    ]
    result = engine.applyRules(statements)

    # def bar: max(1 existing blank, 2 required by PEP 8 for module-level def) = 2
    assert result[3] == 2

  def test_determineBlankLineWithoutPreserveReturningFromNestedLevel(self):
    """_determineBlankLineWithoutPreserve hits returningFromNestedLevel when preserveBlankLines is set by a skip block

    A skip block with mixed indent levels (x at 0, y at 2) is followed by a blank
    then z at level 0. z has preserveBlankLines=True and returningFromNestedLevel=True,
    with no prevAtSameLevel (prevNonBlank y is at a different indent level).
    Result is max(1 existing blank, 1 required by returningFromNestedLevel) = 1.
    This covers lines 203-207 of rules.py and the branch where prevAtSameLevel is None.
    """

    setConfig(BlankLineConfig.fromDefaults())

    engine = BlankLineRuleEngine()
    statements = [
      Statement(
        lines=['x = 1\n'],
        startLineIndex=0,
        endLineIndex=0,
        blockType=BlockType.ASSIGNMENT,
        indentLevel=0,
        skipBlankLineRules=True,
      ),
      Statement(
        lines=['  y = 2\n'],
        startLineIndex=1,
        endLineIndex=1,
        blockType=BlockType.ASSIGNMENT,
        indentLevel=2,
        skipBlankLineRules=True,
      ),
      Statement(
        lines=['\n'], startLineIndex=2, endLineIndex=2, blockType=BlockType.ASSIGNMENT, indentLevel=-1, isBlank=True
      ),
      Statement(lines=['z = 3\n'], startLineIndex=3, endLineIndex=3, blockType=BlockType.ASSIGNMENT, indentLevel=0),
    ]
    result = engine.applyRules(statements)

    # z=3: max(1 existing blank, 1 required by returningFromNestedLevel) = 1
    assert result[3] == 1
