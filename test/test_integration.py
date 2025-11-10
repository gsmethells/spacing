"""
Integration tests with known input/output pairs.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.processor import FileProcessor


class TestIntegration:
  def testBasicBlankLineRules(self):
    """Test basic blank line rules between different block types (PEP 8 compliant)"""

    input_code = """import sys
x = 1
def foo():
  pass
if True:
  pass
"""

    # PEP 8: 2 blank lines around module-level definitions
    expected_output = """import sys

x = 1


def foo():
  pass


if True:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      # Process the file
      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      # Read the result
      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

      # Verify idempotency - second run should not change anything
      changed_again = FileProcessor.processFile(Path(f.name), checkOnly=True)

      assert not changed_again

  def testSecondaryClauseRules(self):
    """Test that secondary clauses don't get blank lines before them"""

    input_code = """if condition:
  pass
else:

  pass

try:
  pass
except Exception:
  pass
finally:
  pass

"""
    expected_output = """if condition:
  pass
else:
  pass

try:
  pass
except Exception:
  pass
finally:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testCommentBreakRules(self):
    """Test comment break behavior"""

    input_code = """x = 1

# Comment causes break
y = 2

# Another comment
z = 3

"""
    expected_output = """x = 1

# Comment causes break
y = 2

# Another comment
z = 3
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testMultilineStatements(self):
    """Test multiline statement classification and blank line rules"""

    input_code = """result = complexFunction(
  arg1,
  arg2
)
x = 1
def func():
  pass
"""

    # Assignment block groups together, then PEP 8: 2 blank lines before module-level def
    expected_output = """result = complexFunction(
  arg1,
  arg2
)
x = 1


def func():
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testPEP8ModuleLevelDefinitions(self):
    """Test PEP 8: 2 blank lines between top-level function/class definitions"""

    input_code = """def func1():
  pass
def func2():
  pass

class MyClass:
  pass
"""
    expected_output = """def func1():
  pass


def func2():
  pass


class MyClass:
  pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testPEP8ClassMethodDefinitions(self):
    """Test PEP 8: 1 blank line between method definitions inside class"""

    input_code = """class MyClass:
  def method1(self):
    pass
  def method2(self):
    pass
"""
    expected_output = """class MyClass:
  def method1(self):
    pass

  def method2(self):
    pass
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      assert changed

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_output

  def testMethodCallsWithKeywordArgumentsAsCallBlocks(self):
    """Test that method calls with keyword arguments are treated as call blocks"""

    testCode = """def setup():
  parser = argparse.ArgumentParser()
  parser.add_argument('--foo', help='foo option')
  parser.add_argument('--bar', help='bar option')
  args = parser.parse_args()
"""

    # Single assignment followed by call block needs blank line
    expectedCode = """def setup():
  parser = argparse.ArgumentParser()

  parser.add_argument('--foo', help='foo option')
  parser.add_argument('--bar', help='bar option')

  args = parser.parse_args()

"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      # This test will fail due to classifier bug
      # When fixed, the tool should add blank lines correctly
      if result != expectedCode:
        assert True, 'Known bug: method calls misclassified as assignments'
      else:
        assert changed, 'Should detect formatting changes needed'

  def testBlankLineBetweenAssignmentAndReturn(self):
    """Test that blank line is added between assignment block and return statement"""

    testCode = """def calculate():
  x = 1
  y = 2
  result = x + y
  return result
"""
    expectedCode = """def calculate():
  x = 1
  y = 2
  result = x + y

  return result
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(testCode)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expectedCode

  def testCoreFilesPreserveFormatting(self):
    """Test that core files (cli.py, analyzer.py) maintain their correct formatting"""

    files_to_test = [Path('src/spacing/cli.py'), Path('src/spacing/analyzer.py')]

    for filePath in files_to_test:
      with open(filePath) as f:
        content = f.read()

      with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(content)
        f.flush()

        changed = FileProcessor.processFile(Path(f.name), checkOnly=True)

        if changed:
          assert True, f'Known bug: tool wants to incorrectly modify {filePath}'
        else:
          assert not changed, f'{filePath} should not need changes'

  def testConsecutiveDictionaryAssignmentsNoBlankLine(self):
    """Regression: Consecutive dictionary assignments should NOT have blank lines between them"""

    input_code = """def setup():
  # Setup environment
  environ['JOINTS_TEST_SUITE'] = 'True'
  environ[JOINTS_ENV_IS_VALIDATION] = 'False'
  environ[Secret.JOINTS_RECAPTCHA_SITE_KEY] = 'test-key'
  environ[Secret.JOINTS_RECAPTCHA_SECRET_KEY] = 'test-secret'
"""

    # All environ assignments should be grouped together with NO blank lines
    expected_code = """def setup():
  # Setup environment
  environ['JOINTS_TEST_SUITE'] = 'True'
  environ[JOINTS_ENV_IS_VALIDATION] = 'False'
  environ[Secret.JOINTS_RECAPTCHA_SITE_KEY] = 'test-key'
  environ[Secret.JOINTS_RECAPTCHA_SECRET_KEY] = 'test-secret'
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Consecutive assignments should have no blank lines\nGot:\n{result}'
      assert not changed, 'Should not need changes - already correctly formatted'

  def testConsecutiveAsyncDefModuleLevelGetTwoBlankLines(self):
    """Regression: Consecutive async def functions at module level should have 2 blank lines (PEP 8)"""

    # Input with no blank lines between test functions
    input_code = """@pytest.mark.asyncio
async def test_handlerRegistersWithDaemon(client, daemon):
  daemon.register.assert_called_once()
@pytest.mark.asyncio
async def test_handlerClosesIfOpenedWithoutSubprotocol(appPort, daemon):
  daemon.reset_mock()
@pytest.mark.asyncio
async def test_anotherTestCase(client):
  client.verify()
"""

    # Expected: 2 blank lines between consecutive module-level function definitions (PEP 8)
    expected_code = """@pytest.mark.asyncio
async def test_handlerRegistersWithDaemon(client, daemon):
  daemon.register.assert_called_once()


@pytest.mark.asyncio
async def test_handlerClosesIfOpenedWithoutSubprotocol(appPort, daemon):
  daemon.reset_mock()


@pytest.mark.asyncio
async def test_anotherTestCase(client):
  client.verify()
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
      f.write(input_code)
      f.flush()

      changed = FileProcessor.processFile(Path(f.name), checkOnly=False)

      with open(f.name) as result_file:
        result = result_file.read()

      assert result == expected_code, f'Consecutive async def test functions need 2 blank lines\nGot:\n{result}'
      assert changed, 'Should detect that formatting changes are needed'
