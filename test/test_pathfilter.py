"""
Tests for path discovery and filtering.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tempfile
from pathlib import Path
from spacing.config import BlankLineConfig
from spacing.pathfilter import discoverPythonFiles, shouldExcludePath


def test_shouldExcludeHiddenDirs():
  """Test that hidden directories are excluded by default"""

  config = BlankLineConfig.fromDefaults()

  assert shouldExcludePath(Path('.git/hooks/pre-commit'), config) is True
  assert shouldExcludePath(Path('.vscode/settings.json'), config) is True
  assert shouldExcludePath(Path('src/.hidden/file.py'), config) is True


def test_shouldNotExcludeRegularDirs():
  """Test that regular directories are not excluded"""

  config = BlankLineConfig.fromDefaults()

  assert shouldExcludePath(Path('src/main.py'), config) is False
  assert shouldExcludePath(Path('tests/test_main.py'), config) is False


def test_shouldExcludeVenv():
  """Test that venv directories are excluded by default"""

  config = BlankLineConfig.fromDefaults()

  assert shouldExcludePath(Path('venv/lib/python3.11/site-packages/foo.py'), config) is True
  assert shouldExcludePath(Path('env/bin/activate'), config) is True
  assert shouldExcludePath(Path('virtualenv/lib/foo.py'), config) is True


def test_shouldExcludeBuildArtifacts():
  """Test that build artifacts are excluded by default"""

  config = BlankLineConfig.fromDefaults()

  assert shouldExcludePath(Path('build/lib/foo.py'), config) is True
  assert shouldExcludePath(Path('dist/package-1.0.tar.gz'), config) is True
  assert shouldExcludePath(Path('__pycache__/foo.pyc'), config) is True
  assert shouldExcludePath(Path('foo.egg-info/PKG-INFO'), config) is True


def test_includeHiddenOverride():
  """Test that includeHidden config allows hidden directories"""

  config = BlankLineConfig.fromDefaults()
  config.includeHidden = True

  assert shouldExcludePath(Path('.git/hooks/pre-commit'), config) is False
  assert shouldExcludePath(Path('src/.hidden/file.py'), config) is False


def test_customExcludeNames():
  """Test that custom exclude names work"""

  config = BlankLineConfig.fromDefaults()
  config.excludeNames = ['my_generated_code']

  assert shouldExcludePath(Path('my_generated_code/foo.py'), config) is True
  assert shouldExcludePath(Path('src/my_generated_code/bar.py'), config) is True


def test_customExcludePatterns():
  """Test that custom exclude patterns work"""

  config = BlankLineConfig.fromDefaults()
  config.excludePatterns = ['**/old_*.py']

  assert shouldExcludePath(Path('src/old_main.py'), config) is True
  assert shouldExcludePath(Path('tests/old_test.py'), config) is True
  assert shouldExcludePath(Path('src/new_main.py'), config) is False


def test_discoverPythonFilesWithExclusions():
  """Test that discoverPythonFiles applies exclusions correctly"""

  with tempfile.TemporaryDirectory() as tmpdir:
    tmpPath = Path(tmpdir)

    # Create test structure
    (tmpPath / 'main.py').touch()
    (tmpPath / 'src').mkdir()
    (tmpPath / 'src' / 'foo.py').touch()
    (tmpPath / 'venv').mkdir()
    (tmpPath / 'venv' / 'bar.py').touch()
    (tmpPath / '.git').mkdir()
    (tmpPath / '.git' / 'hooks.py').touch()

    config = BlankLineConfig.fromDefaults()
    files = discoverPythonFiles(tmpPath, config)

    # Should only find main.py and src/foo.py (not venv or .git)
    assert len(files) == 2
    assert (tmpPath / 'main.py') in files
    assert (tmpPath / 'src' / 'foo.py') in files
    assert (tmpPath / 'venv' / 'bar.py') not in files
    assert (tmpPath / '.git' / 'hooks.py') not in files


def test_discoverPythonFilesWithIncludeHidden():
  """Test that discoverPythonFiles respects includeHidden config"""

  with tempfile.TemporaryDirectory() as tmpdir:
    tmpPath = Path(tmpdir)

    # Create test structure
    (tmpPath / 'main.py').touch()
    (tmpPath / '.hidden').mkdir()
    (tmpPath / '.hidden' / 'secret.py').touch()

    config = BlankLineConfig.fromDefaults()
    config.includeHidden = True
    files = discoverPythonFiles(tmpPath, config)

    # Should find both files when includeHidden is True
    assert len(files) == 2
    assert (tmpPath / 'main.py') in files
    assert (tmpPath / '.hidden' / 'secret.py') in files


def test_discoverPythonFilesEmpty():
  """Test that discoverPythonFiles returns empty list for non-directory"""

  config = BlankLineConfig.fromDefaults()
  files = discoverPythonFiles(Path('/nonexistent'), config)

  assert files == []
