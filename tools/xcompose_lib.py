#!/usr/bin/env python3
"""
XCompose-STEM: Shared Library

Common data structures and parser logic shared across XCompose-STEM tools.

Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals

Copyright (c) 2025 Phil Bowens
Repository: https://github.com/phil-bowens/xcompose-stem
License: MIT
"""

import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class XComposeSequence:
    """Represents a single XCompose sequence.

    This unified model is used by all XCompose-STEM tools.
    """
    keys: List[str]  # List of key names (excluding Multi_key)
    symbol: str  # Output character(s)
    codepoint: Optional[str]  # Unicode codepoint if specified
    comment: Optional[str]  # Inline comment (without tag)
    tag: Optional[str]  # Type tag: ICONIC or MNEMONIC
    category: str  # Section header (e.g., "GREEK LETTERS")
    subcategory: Optional[str]  # Subsection if applicable
    line_num: int  # Line number in source file

    @property
    def sequence_string(self) -> str:
        """Human-readable sequence like '<g> <a>'"""
        return ' '.join(f'<{k}>' for k in self.keys)

    @property
    def human_sequence(self) -> str:
        """Simplified sequence for display like 'g a'"""
        return ' '.join(self.keys)

    @property
    def key_string(self) -> str:
        """Space-separated key string"""
        return ' '.join(self.keys)

    @property
    def is_ascii_shortcut(self) -> bool:
        """Heuristic: ASCII shortcut if uses mainly ASCII symbols, no prefix"""
        if not self.keys:
            return False
        # ASCII shortcuts typically use: arrows (<>), operators (+-=), quotes, etc.
        ascii_keys = {'less', 'greater', 'minus', 'plus', 'equal', 'bar', 'slash',
                      'asterisk', 'apostrophe', 'quotedbl', 'grave', 'asciicircum',
                      'underscore', 'period', 'colon', 'exclam', 'parenleft', 'parenright',
                      'bracketleft', 'bracketright', 'at', 'numbersign', 'ampersand'}
        # Not ASCII if starts with h/g/k/b/p/u/c/i (prefix categories)
        if self.keys[0] in ['h', 'g', 'k', 'b', 'p', 'u', 'c', 'i']:
            return False
        # ASCII if mostly uses ASCII symbol keys
        return any(k in ascii_keys for k in self.keys)

    @property
    def is_mnemonic(self) -> bool:
        """Heuristic: mnemonic if uses h/g/k/b/p/u/c/i prefix"""
        if not self.keys:
            return False
        # Mnemonics start with category prefixes
        return self.keys[0] in ['h', 'g', 'k', 'b', 'p', 'u', 'c', 'i']


class XComposeParser:
    """Unified parser for XCompose configuration files.

    Extracts sequences, categories, subcategories, and metadata from XCompose files.
    Used by all XCompose-STEM tools for consistent parsing.
    """

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self.sequences: List[XComposeSequence] = []
        self.categories: Dict[str, List[XComposeSequence]] = defaultdict(list)
        self.current_category = "Uncategorized"
        self.current_subcategory = None

    def parse(self) -> bool:
        """Parse the XCompose file and extract all sequences.

        Returns:
            True if parsing succeeded, False otherwise
        """
        if not self.filepath.exists():
            print(f"Error: File not found: {self.filepath}", file=sys.stderr)
            return False

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            return False

        # Regex patterns
        category_pattern = re.compile(r'^#{5,}\s*$')  # Line of #####
        section_header = re.compile(r'^#\s+([A-Z][A-Z\s/&\-]+(?:\([^)]+\))?)\s*(?:—|–|-)\s*(.*)$')
        subsection_header = re.compile(r'^##\s+([A-Z][A-Z\s/&\-]+)$')
        sequence_pattern = re.compile(
            r'^<Multi_key>(\s+<[^>]+>)+\s*:\s*"([^"]+)"(?:\s+U([0-9A-Fa-f]{4,6}))?(?:\s*#\s*(.*))?$'
        )

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Skip empty lines and includes
            if not line_stripped or line_stripped.startswith('include'):
                continue

            # Check for category headers (lines of ####)
            if category_pattern.match(line_stripped):
                continue

            # Check for section headers
            section_match = section_header.match(line_stripped)
            if section_match:
                self.current_category = section_match.group(1).strip()
                self.current_subcategory = None
                continue

            # Check for subsection headers
            subsection_match = subsection_header.match(line_stripped)
            if subsection_match:
                self.current_subcategory = subsection_match.group(1).strip()
                continue

            # Check for sequence definitions
            seq_match = sequence_pattern.match(line_stripped)
            if seq_match:
                # Extract keys (everything between < >)
                keys_raw = seq_match.group(0)
                keys = re.findall(r'<([^>]+)>', keys_raw)
                # Remove Multi_key from the list
                keys = [k for k in keys if k != 'Multi_key']

                symbol = seq_match.group(2)
                codepoint = seq_match.group(3) if seq_match.group(3) else None
                comment_raw = seq_match.group(4).strip() if seq_match.group(4) else None

                # Extract tag and clean comment
                tag = None
                comment = comment_raw
                if comment_raw:
                    tag_match = re.match(r'\[(ICONIC|MNEMONIC)\]\s*(.*)', comment_raw)
                    if tag_match:
                        tag = tag_match.group(1)
                        comment = tag_match.group(2).strip()

                # Create sequence object
                seq = XComposeSequence(
                    keys=keys,
                    symbol=symbol,
                    codepoint=codepoint,
                    comment=comment,
                    tag=tag,
                    category=self.current_category,
                    subcategory=self.current_subcategory,
                    line_num=line_num
                )

                self.sequences.append(seq)
                self.categories[self.current_category].append(seq)

        return True

    def get_sequences(self) -> List[XComposeSequence]:
        """Get all parsed sequences."""
        return self.sequences

    def get_categories(self) -> Dict[str, List[XComposeSequence]]:
        """Get sequences grouped by category."""
        return self.categories


def parse_xcompose(filepath: str) -> Optional[List[XComposeSequence]]:
    """Convenience function to parse an XCompose file.

    Args:
        filepath: Path to XCompose file

    Returns:
        List of XComposeSequence objects, or None if parsing failed
    """
    parser = XComposeParser(filepath)
    if parser.parse():
        return parser.get_sequences()
    return None


__all__ = ['XComposeSequence', 'XComposeParser', 'parse_xcompose']
__version__ = '1.0.0'
