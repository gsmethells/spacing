"""
Configuration management for spacing blank line rules.
Copyright (c) 2025-2026 Greg Smethells. All rights reserved.
See the accompanying AUTHORS file for a complete list of authors.
This file is subject to the terms and conditions defined in LICENSE.
"""

import tomllib
from .types import BlockType
from dataclasses import dataclass, field


@dataclass
class BlankLineConfig:
  """Configuration for blank line rules between block types"""

  defaultBetweenDifferent: int = 1
  transitions: dict = field(default_factory=dict)
  consecutiveControl: int = 1
  consecutiveDefinition: int = 1
  afterDocstring: int = 1
  indentWidth: int = 2
  excludeNames: list = field(default_factory=list)
  excludePatterns: list = field(default_factory=list)
  includeHidden: bool = False

  @classmethod
  def fromToml(cls, configPath):
    """Load configuration from TOML file
    :param configPath: Path to spacing.toml file
    :type configPath: Path
    :rtype: BlankLineConfig
    :raises: ValueError for invalid configuration values
    :raises: FileNotFoundError if config file doesn't exist
    """

    if not configPath.exists():
      raise FileNotFoundError(f'Configuration file not found: {configPath}')

    try:
      with open(configPath, 'rb') as f:
        data = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
      raise ValueError(f'Failed to parse TOML file {configPath}: {e}')
    except OSError as e:
      raise ValueError(f'Failed to read TOML file {configPath}: {e}')

    blankLinesConfig = data.get('blank_lines', {})
    pathsConfig = data.get('paths', {})

    # Parse default value
    defaultBetweenDifferent = blankLinesConfig.get('default_between_different', 1)

    cls._validateBlankLineCount(defaultBetweenDifferent, 'default_between_different')

    # Parse special rules
    consecutiveControl = blankLinesConfig.get('consecutive_control', 1)
    consecutiveDefinition = blankLinesConfig.get('consecutive_definition', 1)
    afterDocstring = blankLinesConfig.get('after_docstring', 1)

    cls._validateBlankLineCount(consecutiveControl, 'consecutive_control')
    cls._validateBlankLineCount(consecutiveDefinition, 'consecutive_definition')
    cls._validateBlankLineCount(afterDocstring, 'after_docstring')

    # Parse indent width
    indentWidth = blankLinesConfig.get('indent_width', 2)

    cls._validateBlankLineCount(indentWidth, 'indent_width')

    # Parse transition overrides
    transitions = {}

    for key, value in blankLinesConfig.items():
      if key in [
        'default_between_different',
        'consecutive_control',
        'consecutive_definition',
        'after_docstring',
        'indent_width',
      ]:
        continue

      # Parse transition key (e.g., "assignment_to_call")
      parts = key.split('_to_')

      if len(parts) != 2:
        raise ValueError(f'Invalid transition key format: {key}. Expected format: blocktype_to_blocktype')

      fromBlockName, toBlockName = parts

      try:
        fromBlock = cls._parseBlockType(fromBlockName)
        toBlock = cls._parseBlockType(toBlockName)
      except ValueError as e:
        raise ValueError(f'Invalid transition key {key}: {e}')

      cls._validateBlankLineCount(value, key)

      transitions[(fromBlock, toBlock)] = value

    # Parse path exclusions
    excludeNames = pathsConfig.get('exclude_names', [])
    excludePatterns = pathsConfig.get('exclude_patterns', [])
    includeHidden = pathsConfig.get('include_hidden', False)

    if not isinstance(excludeNames, list):
      raise ValueError('paths.exclude_names must be a list')

    if not isinstance(excludePatterns, list):
      raise ValueError('paths.exclude_patterns must be a list')

    if not isinstance(includeHidden, bool):
      raise ValueError('paths.include_hidden must be a boolean')

    return cls(
      defaultBetweenDifferent=defaultBetweenDifferent,
      transitions=transitions,
      consecutiveControl=consecutiveControl,
      consecutiveDefinition=consecutiveDefinition,
      afterDocstring=afterDocstring,
      indentWidth=indentWidth,
      excludeNames=excludeNames,
      excludePatterns=excludePatterns,
      includeHidden=includeHidden,
    )

  @classmethod
  def fromDefaults(cls) -> 'BlankLineConfig':
    """Create configuration with default values (current behavior)
    :rtype: BlankLineConfig
    """

    return cls()

  def getBlankLines(self, fromBlock, toBlock, indentLevel=None, isClassDocstring=False):
    """Get number of blank lines for transition between block types
    :param fromBlock: Source block type
    :type fromBlock: BlockType
    :param toBlock: Target block type
    :type toBlock: BlockType
    :param indentLevel: Indentation level for scope-aware rules (None = unknown)
    :type indentLevel: int
    :param isClassDocstring: True if fromBlock is a class docstring (not configurable)
    :type isClassDocstring: bool
    :rtype: int
    """

    # Check for specific transition override first
    key = (fromBlock, toBlock)

    if key in self.transitions:
      blankLines = self.transitions[key]
    elif fromBlock == toBlock:
      # Handle same-type special rules
      if fromBlock == BlockType.CONTROL:
        blankLines = self.consecutiveControl
      elif fromBlock == BlockType.DEFINITION:
        # PEP 8: 2 blank lines at module level (indent 0), 1 blank line nested
        if indentLevel == 0:
          blankLines = 2
        else:
          blankLines = self.consecutiveDefinition
      else:
        # Same type blocks (except Control/Definition) have no blank lines
        blankLines = 0
    else:
      # PEP 8: Surround top-level function and class definitions with 2 blank lines
      # This applies when:
      # 1. Transitioning TO a definition at module level
      # 2. Transitioning FROM a definition at module level
      if indentLevel == 0 and (toBlock == BlockType.DEFINITION or fromBlock == BlockType.DEFINITION):
        blankLines = 2

      # PEP 257: blank line after docstrings
      # Class docstrings ALWAYS get 1 blank line (non-configurable)
      # Method/function docstrings use afterDocstring config (default 1)
      elif fromBlock == BlockType.DOCSTRING and toBlock != BlockType.DOCSTRING:
        if isClassDocstring:
          blankLines = 1  # Always 1 for class docstrings
        else:
          blankLines = self.afterDocstring  # Configurable for method/function docstrings
      else:
        # Use default for different block types
        blankLines = self.defaultBetweenDifferent

    return blankLines

  @staticmethod
  def _parseBlockType(blockTypeName: str) -> BlockType:
    """Parse block type name from string
    :param blockTypeName: Name of block type (e.g., 'assignment', 'call')
    :type blockTypeName: str
    :rtype: BlockType
    :raises: ValueError if block type name is invalid
    """

    blockTypeMap = {
      'assignment': BlockType.ASSIGNMENT,
      'call': BlockType.CALL,
      'import': BlockType.IMPORT,
      'control': BlockType.CONTROL,
      'definition': BlockType.DEFINITION,
      'declaration': BlockType.DECLARATION,
      'docstring': BlockType.DOCSTRING,
      'comment': BlockType.COMMENT,
    }

    if blockTypeName not in blockTypeMap:
      validNames = ', '.join(blockTypeMap.keys())

      raise ValueError(f'Unknown block type: {blockTypeName}. Valid types: {validNames}')

    return blockTypeMap[blockTypeName]

  @staticmethod
  def _validateBlankLineCount(value: int, key: str):
    """Validate blank line count is in valid range (0-3)
    :param value: Blank line count to validate
    :type value: int
    :param key: Configuration key name for error messages
    :type key: str
    :raises: ValueError if value is invalid
    """

    if not isinstance(value, int):
      raise ValueError(f'{key} must be an integer, got {type(value).__name__}: {value}')

    if value < 0 or value > 3:
      raise ValueError(f'{key} must be between 0 and 3, got: {value}')


# Global configuration instance available for import
config = BlankLineConfig.fromDefaults()


def setConfig(newConfig):
  """Update the global configuration instance
  :param newConfig: Configuration to set as global
  :type newConfig: BlankLineConfig
  """

  global config

  config = newConfig
