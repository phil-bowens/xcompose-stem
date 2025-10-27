#!/usr/bin/env python3
"""
xcompose-stem: Documentation Generator

Parses XCompose files and generates various output formats:
- Interactive HTML reference (tiling WM optimized)
- Markdown table for quick reference
- JSON export for TUI/fuzzy finder
- Markdown checklist for manual verification

This script serves as the central documentation generator from the XCompose
configuration file, treating it as the single source of truth.

Part of xcompose-stem - Keyboard shortcuts for STEM symbols on Linux

Copyright (c) 2025 Phil Bowens
Repository: https://github.com/phil-bowens/xcompose-stem
License: MIT

Usage:
    ./generate_xcompose_docs.py XCompose --html
    ./generate_xcompose_docs.py XCompose --json
    ./generate_xcompose_docs.py XCompose --table
    ./generate_xcompose_docs.py XCompose --checklist
    ./generate_xcompose_docs.py XCompose --all
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import asdict

from xcompose_lib import XComposeSequence, XComposeParser as BaseParser


class XComposeParser:
    """Wrapper around shared XComposeParser for backward compatibility."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath)
        self._parser = BaseParser(str(filepath))
        self.sequences: List[XComposeSequence] = []
        self.categories: Dict[str, List[XComposeSequence]] = defaultdict(list)

    def parse(self) -> bool:
        """Parse the XCompose file and extract all sequences."""
        if not self._parser.parse():
            return False

        self.sequences = self._parser.get_sequences()
        self.categories = self._parser.get_categories()
        return True

    def get_statistics(self) -> Dict:
        """Get statistics about parsed sequences."""
        if not self.sequences:
            return {}

        # Count prefixes (first key after Multi_key)
        prefixes = defaultdict(int)
        for seq in self.sequences:
            if seq.keys:
                prefixes[seq.keys[0]] += 1

        # Sequence length distribution
        lengths = [len(seq.keys) for seq in self.sequences]

        return {
            'total_sequences': len(self.sequences),
            'total_categories': len(self.categories),
            'categories': list(self.categories.keys()),
            'unique_prefixes': len(prefixes),
            'top_prefixes': sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10],
            'sequence_length': {
                'min': min(lengths) if lengths else 0,
                'max': max(lengths) if lengths else 0,
                'avg': sum(lengths) / len(lengths) if lengths else 0
            }
        }


class MarkdownChecklistGenerator:
    """Generates a Markdown checklist for manual verification."""

    def __init__(self, parser: XComposeParser):
        self.parser = parser

    def generate(self, output_file: str):
        """Generate a Markdown checklist file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# XCompose Sequence Verification Checklist\n\n")
            f.write(f"Total sequences: {len(self.parser.sequences)}\n\n")
            f.write("Instructions: Test each sequence and check the box when verified.\n\n")
            f.write("---\n\n")

            for category, sequences in self.parser.categories.items():
                f.write(f"## {category}\n\n")

                # Group by subcategory
                by_subcat = defaultdict(list)
                for seq in sequences:
                    by_subcat[seq.subcategory].append(seq)

                for subcat, subseqs in by_subcat.items():
                    if subcat:
                        f.write(f"### {subcat}\n\n")

                    for seq in subseqs:
                        # Create checkbox item
                        checkbox = f"- [ ] `{seq.human_sequence}` → **{seq.symbol}**"
                        if seq.comment:
                            checkbox += f" — {seq.comment}"
                        checkbox += "\n"
                        f.write(checkbox)

                    f.write("\n")

        print(f"✓ Generated checklist: {output_file}")


class JSONGenerator:
    """Generates JSON export for TUI/fuzzy finder integration."""

    def __init__(self, parser: XComposeParser):
        self.parser = parser

    def generate(self, output_file: str):
        """Generate JSON export."""
        data = {
            'metadata': {
                'source_file': str(self.parser.filepath),
                'total_sequences': len(self.parser.sequences),
                'statistics': self.parser.get_statistics()
            },
            'sequences': [
                {
                    'keys': seq.keys,
                    'sequence': seq.human_sequence,
                    'symbol': seq.symbol,
                    'codepoint': seq.codepoint,
                    'comment': seq.comment,
                    'category': seq.category,
                    'subcategory': seq.subcategory,
                    'searchable': f"{seq.human_sequence} {seq.symbol} {seq.comment or ''} {seq.category}"
                }
                for seq in self.parser.sequences
            ],
            'categories': {
                cat: [
                    {
                        'keys': seq.keys,
                        'sequence': seq.human_sequence,
                        'symbol': seq.symbol,
                        'comment': seq.comment
                    }
                    for seq in seqs
                ]
                for cat, seqs in self.parser.categories.items()
            }
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Generated JSON export: {output_file}")


class MarkdownTableGenerator:
    """Generates a comprehensive Markdown table grouped by category/subcategory."""

    def __init__(self, parser: XComposeParser):
        self.parser = parser

    def classify_sequence(self, keys: List[str]) -> str:
        """Classify a sequence as 'ascii', 'mnemonic', or 'variant'."""
        if not keys:
            return 'variant'

        # Check if it's a mnemonic (starts with common prefixes)
        prefix_keys = {'h', 'g', 'k', 'b', 'p', 'u', 'i', 'c'}
        if keys[0] in prefix_keys:
            return 'mnemonic'

        # Check if it's an ASCII shortcut (2-4 chars, common punctuation)
        ascii_keys = {
            'minus', 'greater', 'less', 'equal', 'exclam', 'asciitilde',
            'asciicircum', 'bar', 'plus', 'asterisk', 'slash', 'colon',
            'period', 'v', 'question', 'quotedbl', 'apostrophe', 'comma',
            'ampersand', 'at', 'numbersign', 'dollar', 'percent',
            'parenleft', 'parenright', 'underscore', 'grave'
        }
        # Also include single letter/digit keys
        single_chars = set('0123456789')

        if len(keys) <= 5 and all(k in ascii_keys or k in single_chars for k in keys):
            return 'ascii'

        return 'variant'

    def format_keys_compact(self, keys: List[str]) -> str:
        """Format keys in a compact, readable way for table display."""
        # Map common X11 keysyms to readable symbols
        key_map = {
            'asciicircum': '^', 'asciitilde': '~', 'exclam': '!',
            'at': '@', 'numbersign': '#', 'dollar': '$', 'percent': '%',
            'ampersand': '&', 'asterisk': '*', 'parenleft': '(',
            'parenright': ')', 'minus': '-', 'underscore': '_',
            'plus': '+', 'equal': '=', 'bracketleft': '[',
            'bracketright': ']', 'braceleft': '{', 'braceright': '}',
            'backslash': '\\', 'bar': '|', 'semicolon': ';',
            'colon': ':', 'apostrophe': "'", 'quotedbl': '"',
            'comma': ',', 'period': '.', 'less': '<', 'greater': '>',
            'slash': '/', 'question': '?', 'grave': '`',
        }

        formatted = []
        for k in keys:
            if k in key_map:
                formatted.append(key_map[k])
            else:
                formatted.append(k)

        return ' '.join(formatted)

    def generate(self, output_file: str):
        """Generate comprehensive Markdown table."""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("# XCompose Sequence Reference\n\n")
            f.write("*A comprehensive reference showing all ways to type each symbol*\n\n")

            stats = self.parser.get_statistics()
            f.write(f"**Statistics**: {stats['total_sequences']} sequences | ")
            f.write(f"{stats['total_categories']} categories | ")
            f.write(f"{stats['unique_prefixes']} unique prefixes\n\n")

            f.write("---\n\n")

            # Table of contents
            f.write("## Table of Contents\n\n")
            for category in self.parser.categories.keys():
                anchor = category.lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
                f.write(f"- [{category}](#{anchor})\n")
            f.write("\n---\n\n")

            # Process each category
            for category, sequences in self.parser.categories.items():
                f.write(f"## {category}\n\n")

                # Group sequences by symbol (to collect all ways to type each symbol)
                symbol_map = defaultdict(lambda: {'ascii': [], 'mnemonic': [], 'variant': [],
                                                    'codepoint': None, 'comment': None})

                for seq in sequences:
                    # Use explicit tag if available, otherwise auto-classify
                    if seq.tag:
                        classification = seq.tag.lower()
                        # Map tags to our internal names
                        tag_map = {'visual': 'ascii', 'mnem': 'mnemonic', 'alt': 'variant'}
                        classification = tag_map.get(classification, classification)
                    else:
                        classification = self.classify_sequence(seq.keys)

                    formatted_seq = self.format_keys_compact(seq.keys)
                    symbol_map[seq.symbol][classification].append(formatted_seq)
                    if symbol_map[seq.symbol]['codepoint'] is None:
                        symbol_map[seq.symbol]['codepoint'] = seq.codepoint
                    if symbol_map[seq.symbol]['comment'] is None:
                        symbol_map[seq.symbol]['comment'] = seq.comment

                # Group by subcategory
                by_subcat = defaultdict(list)
                for seq in sequences:
                    # Add to subcategory only once per symbol
                    if seq.symbol not in [s.symbol for s in by_subcat[seq.subcategory]]:
                        by_subcat[seq.subcategory].append(seq)

                for subcat, subseqs in sorted(by_subcat.items(), key=lambda x: (x[0] is None, x[0])):
                    if subcat:
                        f.write(f"### {subcat}\n\n")

                    # Table header with style
                    f.write("| Symbol | Code | ASCII | Mnemonic | Variants | Description |\n")
                    f.write("|:------:|:----:|:------|:---------|:---------|:------------|\n")

                    # Get unique symbols in order of appearance
                    seen_symbols = set()
                    for seq in subseqs:
                        if seq.symbol in seen_symbols:
                            continue
                        seen_symbols.add(seq.symbol)

                        info = symbol_map[seq.symbol]

                        # Format columns
                        symbol_col = f"**{seq.symbol}**"
                        code_col = info['codepoint'] if info['codepoint'] else '-'
                        ascii_col = '<br>'.join(f"`{s}`" for s in info['ascii']) if info['ascii'] else '-'
                        mnemonic_col = '<br>'.join(f"`{s}`" for s in info['mnemonic']) if info['mnemonic'] else '-'
                        variant_col = '<br>'.join(f"`{s}`" for s in info['variant']) if info['variant'] else '-'
                        desc_col = info['comment'] if info['comment'] else ''

                        f.write(f"| {symbol_col} | {code_col} | {ascii_col} | {mnemonic_col} | {variant_col} | {desc_col} |\n")

                    f.write("\n")

                f.write("---\n\n")

            # Footer with legend
            f.write("## Legend\n\n")
            f.write("- **Symbol**: The Unicode character produced\n")
            f.write("- **Code**: Unicode codepoint in hexadecimal\n")
            f.write("- **ASCII**: Visual shortcuts using punctuation (e.g., `->`, `<=`, `!=`)\n")
            f.write("- **Mnemonic**: Letter-based sequences with prefixes:\n")
            f.write("  - `h` = Higher math/logic/sets/calculus\n")
            f.write("  - `g` = Greek letters\n")
            f.write("  - `k` = Keyboard/UI symbols\n")
            f.write("  - `b` = Box drawing\n")
            f.write("  - `p` = Phonetic (IPA)\n")
            f.write("  - `u` = Music notation\n")
            f.write("  - `c` = Currency\n")
            f.write("  - `i` = International diacritics\n")
            f.write("- **Variants**: Alternative sequences (less common patterns)\n")
            f.write("- **Description**: Explanation of symbol meaning/usage\n\n")

            f.write("---\n\n")
            f.write("*Generated from XCompose configuration*\n")
            f.write(f"*Total unique symbols: {len(set(seq.symbol for seq in self.parser.sequences))}*\n")

        print(f"✓ Generated Markdown table reference: {output_file}")


class HTMLGenerator:
    """Generates an HTML reference page."""

    # X11 keysym name to visual character mapping
    KEY_SYMBOL_MAP = {
        'asciicircum': '^',
        'asciitilde': '~',
        'exclam': '!',
        'at': '@',
        'numbersign': '#',
        'dollar': '$',
        'percent': '%',
        'ampersand': '&',
        'asterisk': '*',
        'parenleft': '(',
        'parenright': ')',
        'minus': '−',
        'underscore': '_',
        'plus': '+',
        'equal': '=',
        'bracketleft': '[',
        'bracketright': ']',
        'braceleft': '{',
        'braceright': '}',
        'backslash': '\\',
        'bar': '|',
        'semicolon': ';',
        'colon': ':',
        'apostrophe': "'",
        'quotedbl': '"',
        'comma': ',',
        'period': '.',
        'less': '<',
        'greater': '>',
        'slash': '/',
        'question': '?',
        'grave': '`',
        'space': '␣',
        'Tab': '⇥',
        'Return': '⏎',
        'Multi_key': '⎄',
        # Keep named keys as-is for clarity
    }

    def __init__(self, parser: XComposeParser):
        self.parser = parser

    def get_category_frequency_order(self) -> List[str]:
        """Define frequency-based ordering for HTML display.

        Categories ordered from most frequently used (daily) to least (specialized).
        This differs from the XCompose source file order, which uses logical
        hierarchical grouping for maintainability.

        Note: Names must match exact keys from parser (including prefix annotations).
        """
        return [
            # Most common (daily use)
            'MATH / LOGIC / SETS  (prefix: h)',
            'GREEK LETTERS  (prefix: g)',
            'SUPERSCRIPTS & SUBSCRIPTS (prefix: ^ _)',
            'TYPOGRAPHY & SPACING (prefix: visual)',
            'SMART QUOTES (prefix: visual)',
            # Common (weekly use)
            'UNITS & MEASUREMENTS (prefix: h, visual)',
            'INTERNATIONAL PUNCTUATION (prefix: visual)',
            'UI SYMBOLS & SHAPES (prefix: k)',
            'HIGHER LOGIC / CATEGORY THEORY / LONG ARROWS  (prefix: h)',
            # Occasional (monthly use)
            'CURRENCY (prefix: c)',
            'LEGAL / DOCUMENT SYMBOLS (prefix: visual)',
            # Specialized (field-dependent)
            'CHEMISTRY (prefix: h, visual)',
            'ASTRONOMY (prefix: h, visual)',
            'BOX-DRAWING (prefix: b)',
            'INTERNATIONAL DIACRITICS (prefix: i)',
            'IPA (prefix: p)',
            'CALLIGRAPHIC / FRAKTUR (prefix: k)',
            'MUSIC SYMBOLS (prefix: u)',
        ]

    def sort_categories_by_frequency(self, categories: Dict) -> List[tuple]:
        """Sort categories by frequency order, placing unlisted categories at end."""
        frequency_order = self.get_category_frequency_order()

        # Create dict mapping category name to its priority (lower = higher priority)
        priority_map = {cat: idx for idx, cat in enumerate(frequency_order)}

        # Sort categories: known ones by priority, unknown ones alphabetically at end
        def sort_key(item):
            category_name = item[0]
            if category_name in priority_map:
                return (0, priority_map[category_name])
            else:
                # Unknown categories go to end, sorted alphabetically
                return (1, category_name)

        return sorted(categories.items(), key=sort_key)

    def classify_sequence(self, keys: List[str]) -> str:
        """Classify a sequence as 'ascii', 'mnemonic', or 'variant'."""
        if not keys:
            return 'variant'

        # Check if it's a mnemonic (starts with common prefixes)
        prefix_keys = {'h', 'g', 'k', 'b', 'p', 'u', 'i', 'c'}
        if keys[0] in prefix_keys:
            return 'mnemonic'

        # Check if it's an ASCII shortcut (2-5 chars, common punctuation)
        ascii_keys = {
            'minus', 'greater', 'less', 'equal', 'exclam', 'asciitilde',
            'asciicircum', 'bar', 'plus', 'asterisk', 'slash', 'colon',
            'period', 'v', 'question', 'quotedbl', 'apostrophe', 'comma',
            'ampersand', 'at', 'numbersign', 'dollar', 'percent',
            'parenleft', 'parenright', 'underscore', 'grave', 'd'
        }
        # Also include single letter/digit keys
        single_chars = set('0123456789')

        if len(keys) <= 5 and all(k in ascii_keys or k in single_chars for k in keys):
            return 'ascii'

        return 'variant'

    def format_sequence_visual(self, keys: List[str]) -> str:
        """Convert key names to visual representation."""
        visual_keys = []
        for key in keys:
            # Map to symbol if available, otherwise use the key name
            visual_key = self.KEY_SYMBOL_MAP.get(key, key)
            visual_keys.append(visual_key)
        return ' '.join(visual_keys)

    def format_heading(self, text: str) -> str:
        """Convert heading text to title case for better readability."""
        if not text:
            return text
        # Convert to title case, preserving some acronyms
        words = text.split()
        formatted = []
        for word in words:
            # Keep common acronyms in uppercase
            if word in ['IPA', 'ASCII', 'UI', 'SUB', 'SUP']:
                formatted.append(word)
            # Keep words in parentheses as-is
            elif word.startswith('(') and word.endswith(')'):
                formatted.append(word)
            else:
                formatted.append(word.capitalize())
        return ' '.join(formatted)

    def generate(self, output_file: str):
        """Generate HTML reference."""
        stats = self.parser.get_statistics()
        unique_symbols = len(set(seq.symbol for seq in self.parser.sequences))

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>xcompose-stem Symbol Reference</title>
    <style>
        * {{ box-sizing: border-box; }}

        :root {{
            --primary: #667eea;
            --primary-dark: #5568d3;
            --secondary: #764ba2;
            --bg-main: linear-gradient(to bottom, #fafafa 0%, #f5f5f5 100%);
            --bg-card: white;
            --text-primary: #2c3e50;
            --text-secondary: #6c757d;
            --border: #dee2e6;
            --shadow: 0 2px 8px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.06);
            --shadow-hover: 0 4px 12px rgba(102, 126, 234, 0.15);
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 8px;
            background: var(--bg-main);
            line-height: 1.4;
            font-size: 14px;
            min-height: 100vh;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 16px;
            border-radius: 6px;
            margin-bottom: 12px;
            box-shadow: var(--shadow);
            border-bottom: 3px solid var(--primary);
        }}

        .header h1 {{
            margin: 0;
            font-size: 1.5em;
            font-weight: 600;
        }}

        .header-left {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .header-right {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
        }}

        h1 {{
            margin: 0;
            font-size: 1.5em;
            font-weight: 700;
        }}

        .project-name {{
            font-size: 0.9em;
            opacity: 0.95;
            font-weight: 500;
        }}

        .stats {{
            font-size: 0.7em;
            opacity: 0.9;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}

        .stat-item {{
            background: rgba(255,255,255,0.15);
            padding: 2px 8px;
            border-radius: 3px;
        }}

        .header-links {{
            font-size: 0.75em;
            opacity: 0.95;
            display: flex;
            gap: 4px;
            align-items: center;
        }}

        .header-links a {{
            color: white;
            text-decoration: none;
            transition: opacity 0.2s;
        }}

        .header-links a:hover {{
            opacity: 0.8;
            text-decoration: underline;
        }}

        .separator {{
            opacity: 0.6;
        }}

        .controls {{
            background: var(--bg-card);
            padding: 12px;
            margin-bottom: 12px;
            border-radius: 6px;
            box-shadow: var(--shadow);
        }}

        .search-box {{
            margin-bottom: 10px;
        }}

        .search-box input {{
            width: 100%;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.2s;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .category-selector {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .category-selector label {{
            font-size: 0.85em;
            font-weight: 600;
            color: var(--text-primary);
        }}

        .category-selector select {{
            width: 100%;
            padding: 8px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            background: white;
            cursor: pointer;
            transition: border-color 0.2s;
        }}

        .category-selector select:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .legend {{
            background: var(--bg-card);
            padding: 10px;
            margin-bottom: 12px;
            border-radius: 6px;
            box-shadow: var(--shadow);
        }}

        .legend h3 {{
            margin: 0 0 8px 0;
            font-size: 0.9em;
            color: var(--primary);
        }}

        .legend-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 0.75em;
        }}

        .legend-badge {{
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 600;
            white-space: nowrap;
        }}

        .badge-ascii {{ background: #e3f2fd; color: #1976d2; }}
        .badge-mnemonic {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-variant {{ background: #fff3e0; color: #f57c00; }}

        .category {{
            background: var(--bg-card);
            padding: 16px;
            margin-bottom: 12px;
            border-radius: 8px;
            box-shadow: var(--shadow);
            border-left: 3px solid var(--primary);
            display: none;
        }}

        .category.active {{
            display: block;
        }}

        .category h2 {{
            color: var(--primary);
            margin: 0 0 14px 0;
            padding-bottom: 0;
            font-size: 1.15em;
            font-weight: 600;
            border-bottom: none;
        }}

        .subcategory {{
            margin-top: 16px;
        }}

        .subcategory h3 {{
            color: var(--secondary);
            font-size: 0.95em;
            margin: 0 0 8px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            font-size: 0.85em;
            table-layout: fixed;
        }}

        th {{
            background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
            padding: 6px 4px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid var(--primary);
            font-size: 0.75em;
            letter-spacing: 0.3px;
            color: var(--text-secondary);
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th:first-child {{ text-align: center; width: 70px; }}
        th:nth-child(2) {{ width: 15%; }}
        th:nth-child(3) {{ width: 18%; }}
        th:nth-child(4) {{ width: 15%; }}
        th:last-child {{ width: auto; }}

        td {{
            padding: 6px 4px;
            border-bottom: 1px solid var(--border);
            vertical-align: top;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        td:first-child {{ text-align: center; }}

        td:last-child {{
            padding-right: 32px;
            position: relative;
        }}

        .symbol-row {{
            cursor: pointer;
            transition: all 0.15s ease;
        }}

        .symbol-row:hover {{
            background: #f8f8ff;
            border-left: 2px solid var(--primary);
        }}

        .symbol-row:hover td:last-child::after {{
            content: '🖱️';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9em;
            opacity: 0.6;
        }}

        .symbol-row:focus {{
            outline: none;
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%);
            box-shadow: inset 3px 0 0 var(--primary);
            position: relative;
        }}

        .symbol-row:focus:hover {{
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.12) 0%, rgba(118, 75, 162, 0.12) 100%);
        }}

        .symbol-row:focus td:last-child::after {{
            content: '↵';
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.9em;
            color: var(--primary);
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
            background: rgba(102, 126, 234, 0.1);
            border: 1px solid var(--primary);
            white-space: nowrap;
        }}

        .toast {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            font-weight: 600;
            font-size: 0.9em;
            z-index: 1000;
            display: none;
            animation: slideIn 0.3s ease;
        }}

        .toast.show {{
            display: block;
        }}

        @keyframes slideIn {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}

        .keyboard-hint {{
            font-size: 0.7em;
            color: var(--text-secondary);
            margin-top: 4px;
            font-style: italic;
        }}

        .kbd {{
            display: inline-block;
            padding: 2px 6px;
            background: #e9ecef;
            border: 1px solid #adb5bd;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            font-weight: 600;
            box-shadow: 0 2px 0 #adb5bd;
        }}

        .sequence {{
            font-family: 'Courier New', monospace;
            background: #e9ecef;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 0.9em;
            white-space: nowrap;
            display: inline-block;
            margin: 1px;
        }}

        .sequence-ascii {{
            background: #e3f2fd;
            color: #1565c0;
            border: 1px solid #bbdefb;
        }}

        .sequence-mnemonic {{
            background: #f3e5f5;
            color: #6a1b9a;
            border: 1px solid #e1bee7;
        }}

        .sequence-variant {{
            background: #fff3e0;
            color: #e65100;
            border: 1px solid #ffe0b2;
        }}

        .symbol {{
            font-size: 1.8em;
            font-weight: bold;
            color: var(--text-primary);
            line-height: 1;
        }}

        .codepoint {{
            font-family: 'Courier New', monospace;
            font-size: 0.7em;
            color: var(--text-secondary);
            display: block;
            margin-top: 2px;
        }}

        .comment {{
            color: var(--text-primary);
            font-size: 0.85em;
            line-height: 1.3;
        }}

        .sequences-cell {{
            display: flex;
            flex-wrap: wrap;
            gap: 2px;
            align-items: flex-start;
        }}

        /* Responsive breakpoints for tiling WMs */
        /* Half width (800-600px) - optimal */
        @media (max-width: 800px) {{
            body {{ padding: 6px; }}
            .header {{ padding: 12px; }}
            h1 {{ font-size: 1.3em; }}
            .stats {{ font-size: 0.7em; gap: 6px; }}
        }}

        /* Quarter width (600-400px) - compact */
        @media (max-width: 600px) {{
            body {{ padding: 4px; font-size: 13px; }}
            .header {{ padding: 10px; margin-bottom: 8px; }}
            h1 {{ font-size: 1.1em; }}
            .stats {{ font-size: 0.65em; gap: 4px; }}

            .controls {{ padding: 8px; margin-bottom: 8px; }}
            .search-box input {{ padding: 6px; font-size: 13px; }}
            .category-selector select {{ padding: 6px; font-size: 13px; }}

            .legend {{ padding: 8px; margin-bottom: 8px; }}
            .legend h3 {{ font-size: 0.85em; margin-bottom: 6px; }}
            .legend-item {{ font-size: 0.7em; }}

            .category {{ padding: 8px; margin-bottom: 8px; }}
            .category h2 {{ font-size: 1em; margin-bottom: 8px; padding-bottom: 6px; }}
            .subcategory h3 {{ font-size: 0.9em; margin-bottom: 6px; }}

            table {{ font-size: 0.75em; }}
            th {{ padding: 4px 2px; font-size: 0.7em; }}
            td {{ padding: 4px 2px; }}
            th:first-child {{ width: 50px; }}
            th:nth-child(2) {{ width: 20%; }}
            th:nth-child(3) {{ width: 22%; }}
            th:nth-child(4) {{ width: 18%; }}

            .symbol {{ font-size: 1.5em; }}
            .codepoint {{ font-size: 0.65em; }}
            .comment {{ font-size: 0.8em; }}
            .sequence {{ padding: 1px 3px; font-size: 0.85em; }}
        }}

        /* Very narrow (< 400px) - minimal */
        @media (max-width: 400px) {{
            body {{ font-size: 12px; }}
            h1 {{ font-size: 1em; }}
            .symbol {{ font-size: 1.3em; }}
            table {{ font-size: 0.7em; }}
            .sequence {{ font-size: 0.8em; }}

            /* Hide description column and enter hint on very narrow */
            td:last-child, th:last-child {{ display: none; }}
            .symbol-row:focus td:last-child::after {{ display: none; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Symbol Reference</h1>
    </div>

    <div class="toast" id="toast"></div>

    <div class="controls">
        <div class="search-box">
            <input type="text" id="search" placeholder="Search: symbols (→), sequences (g a), descriptions (arrow)..." autofocus>
            <div class="keyboard-hint">
                <span class="kbd">/</span> new search ·
                <span class="kbd">Tab</span> navigate ·
                <span class="kbd">↵</span> or <span class="kbd">Click</span> copy ·
                <span class="kbd">Esc</span> back
            </div>
        </div>
        <div class="category-selector">
            <label for="category-select">Category:</label>
            <select id="category-select">
                <option value="all">All Categories</option>"""

        # Add category options (sorted by frequency)
        sorted_categories = self.sort_categories_by_frequency(self.parser.categories)
        for category, _ in sorted_categories:
            # Format to title case and clean up
            formatted = self.format_heading(category)
            html += f'\n                <option value="{category}">{formatted}</option>'

        html += """
            </select>
        </div>
    </div>

    <div class="legend">
        <h3>Types</h3>
        <div class="legend-grid">
            <div class="legend-item">
                <span class="legend-badge badge-ascii">VIS</span>
                <span>Visual</span>
            </div>
            <div class="legend-item">
                <span class="legend-badge badge-mnemonic">MNE</span>
                <span>Mnemonic</span>
            </div>
            <div class="legend-item">
                <span class="legend-badge badge-variant">ALT</span>
                <span>Variant</span>
            </div>
        </div>
    </div>

    <div id="content">
"""

        # Add categories (sorted by frequency for better user experience)
        sorted_categories = self.sort_categories_by_frequency(self.parser.categories)
        for idx, (category, sequences) in enumerate(sorted_categories):
            # All categories visible initially when "All Categories" is selected
            active_class = ' active'
            html += f'        <div class="category{active_class}" data-category="{category}">\n'
            html += f'            <h2>{self.format_heading(category)}</h2>\n'

            # Group sequences by symbol (to collect all ways to type each symbol)
            symbol_map = defaultdict(lambda: {'ascii': [], 'mnemonic': [], 'variant': [],
                                               'codepoint': None, 'comment': None,
                                               'subcategory': None})

            for seq in sequences:
                # Use explicit tag if available, otherwise auto-classify
                if seq.tag:
                    classification = seq.tag.lower()
                    # Map tags to our internal names
                    tag_map = {'visual': 'ascii', 'mnem': 'mnemonic', 'alt': 'variant'}
                    classification = tag_map.get(classification, classification)
                else:
                    classification = self.classify_sequence(seq.keys)

                visual_seq = self.format_sequence_visual(seq.keys)
                symbol_map[seq.symbol][classification].append(visual_seq)
                if symbol_map[seq.symbol]['codepoint'] is None:
                    symbol_map[seq.symbol]['codepoint'] = seq.codepoint
                if symbol_map[seq.symbol]['comment'] is None:
                    symbol_map[seq.symbol]['comment'] = seq.comment
                symbol_map[seq.symbol]['subcategory'] = seq.subcategory

            # Group by subcategory
            by_subcat = defaultdict(list)
            seen_symbols = set()
            for seq in sequences:
                if seq.symbol not in seen_symbols:
                    by_subcat[seq.subcategory].append(seq.symbol)
                    seen_symbols.add(seq.symbol)

            for subcat, symbols in sorted(by_subcat.items(), key=lambda x: (x[0] is None, x[0])):
                if subcat:
                    html += f'            <div class="subcategory">\n'
                    html += f'                <h3>{self.format_heading(subcat)}</h3>\n'

                html += '                <table>\n'
                html += '                    <thead><tr>\n'
                html += '                        <th>Symbol</th>\n'
                html += '                        <th>ASCII</th>\n'
                html += '                        <th>Mnemonic</th>\n'
                html += '                        <th>Variants</th>\n'
                html += '                        <th>Description</th>\n'
                html += '                    </tr></thead>\n'
                html += '                    <tbody>\n'

                for symbol in symbols:
                    info = symbol_map[symbol]
                    comment = info['comment'] if info['comment'] else ""
                    codepoint_display = f"U+{info['codepoint']}" if info['codepoint'] else ""

                    # Collect all sequences for search
                    all_sequences = info['ascii'] + info['mnemonic'] + info['variant']
                    search_text = f"{symbol} {' '.join(all_sequences)} {comment}".lower()

                    html += f'                        <tr tabindex="0" class="symbol-row" data-symbol="{symbol}" data-search="{search_text}">\n'

                    # Symbol column
                    html += f'                            <td>\n'
                    html += f'                                <span class="symbol">{symbol}</span>\n'
                    if codepoint_display:
                        html += f'                                <span class="codepoint">{codepoint_display}</span>\n'
                    html += f'                            </td>\n'

                    # ASCII column
                    html += f'                            <td>\n'
                    if info['ascii']:
                        html += f'                                <div class="sequences-cell">\n'
                        for seq in info['ascii']:
                            html += f'                                    <span class="sequence sequence-ascii">{seq}</span>\n'
                        html += f'                                </div>\n'
                    else:
                        html += f'                                <span style="color: #adb5bd;">—</span>\n'
                    html += f'                            </td>\n'

                    # Mnemonic column
                    html += f'                            <td>\n'
                    if info['mnemonic']:
                        html += f'                                <div class="sequences-cell">\n'
                        for seq in info['mnemonic']:
                            html += f'                                    <span class="sequence sequence-mnemonic">{seq}</span>\n'
                        html += f'                                </div>\n'
                    else:
                        html += f'                                <span style="color: #adb5bd;">—</span>\n'
                    html += f'                            </td>\n'

                    # Variants column
                    html += f'                            <td>\n'
                    if info['variant']:
                        html += f'                                <div class="sequences-cell">\n'
                        for seq in info['variant']:
                            html += f'                                    <span class="sequence sequence-variant">{seq}</span>\n'
                        html += f'                                </div>\n'
                    else:
                        html += f'                                <span style="color: #adb5bd;">—</span>\n'
                    html += f'                            </td>\n'

                    # Description column
                    html += f'                            <td><span class="comment">{comment}</span></td>\n'
                    html += f'                        </tr>\n'

                html += '                    </tbody>\n'
                html += '                </table>\n'

                if subcat:
                    html += '            </div>\n'

            html += '        </div>\n'

        html += """    </div>

"""
        html += f"""    <footer style="background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%); color: white; text-align: center; padding: 1.5rem; margin-top: 2.5rem; box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05); border-radius: 6px;">
        <a href="index.html" style="color: #a8b8ff; text-decoration: none; transition: color 0.2s;" onmouseover="this.style.color='#c5d1ff'" onmouseout="this.style.color='#a8b8ff'">xcompose-stem</a> <span style="opacity: 0.7;">• {stats['total_sequences']} sequences • {unique_symbols} symbols • {stats['total_categories']} categories</span>
    </footer>

"""
        html += """    <script>
        const searchInput = document.getElementById('search');
        const categorySelect = document.getElementById('category-select');
        const categories = document.querySelectorAll('.category');
        const toast = document.getElementById('toast');

        // Toast notification
        function showToast(message) {
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2000);
        }

        // Clipboard copy
        async function copyToClipboard(text) {
            try {
                await navigator.clipboard.writeText(text);
                showToast(`Copied: ${text}`);
            } catch (err) {
                showToast('Copy failed');
            }
        }

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // "/" to focus search and select all (only when NOT in search field)
            if (e.key === '/' && !['INPUT', 'SELECT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }

            // Escape to return to search or clear it
            if (e.key === 'Escape') {
                if (document.activeElement === searchInput) {
                    searchInput.value = '';
                    searchInput.dispatchEvent(new Event('input'));
                } else if (document.activeElement.classList.contains('symbol-row')) {
                    searchInput.focus();
                }
            }

            // Enter to copy symbol from focused row
            if (e.key === 'Enter' && document.activeElement.classList.contains('symbol-row')) {
                e.preventDefault();
                const symbol = document.activeElement.dataset.symbol;
                if (symbol) {
                    copyToClipboard(symbol);
                }
            }
        });

        // Category filtering
        categorySelect.addEventListener('change', (e) => {
            const selectedCategory = e.target.value;

            categories.forEach(category => {
                const categoryName = category.dataset.category;

                if (selectedCategory === 'all') {
                    category.classList.add('active');
                } else if (categoryName === selectedCategory) {
                    category.classList.add('active');
                } else {
                    category.classList.remove('active');
                }
            });

            const query = searchInput.value.trim();
            if (query) {
                filterSearch(query);
            }
        });

        // Search filtering - now searches data-search attribute (includes sequences!)
        function filterSearch(query) {
            const queryLower = query.toLowerCase();
            const selectedCategory = categorySelect.value;

            categories.forEach(category => {
                const categoryName = category.dataset.category;

                if (selectedCategory !== 'all' && categoryName !== selectedCategory) {
                    return;
                }

                const rows = category.querySelectorAll('.symbol-row');
                const subcategories = category.querySelectorAll('.subcategory');
                let visibleCount = 0;

                const subcatVisibility = new Map();
                rows.forEach(row => {
                    // Search in data-search attribute (includes symbol + all sequences + description)
                    const searchText = row.dataset.search || '';
                    if (searchText.includes(queryLower)) {
                        row.style.display = '';
                        visibleCount++;
                        const subcatDiv = row.closest('.subcategory');
                        if (subcatDiv) {
                            subcatVisibility.set(subcatDiv, true);
                        }
                    } else {
                        row.style.display = 'none';
                    }
                });

                subcategories.forEach(subcat => {
                    if (subcatVisibility.get(subcat)) {
                        subcat.style.display = '';
                    } else {
                        subcat.style.display = 'none';
                    }
                });

                if (query && visibleCount > 0) {
                    category.classList.add('active');
                } else if (query && visibleCount === 0) {
                    category.classList.remove('active');
                }
            });
        }

        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();

            if (!query) {
                const selectedCategory = categorySelect.value;

                categories.forEach(category => {
                    const categoryName = category.dataset.category;
                    const rows = category.querySelectorAll('.symbol-row');
                    const subcategories = category.querySelectorAll('.subcategory');

                    rows.forEach(row => row.style.display = '');
                    subcategories.forEach(subcat => subcat.style.display = '');

                    if (selectedCategory === 'all') {
                        category.classList.add('active');
                    } else if (categoryName === selectedCategory) {
                        category.classList.add('active');
                    } else {
                        category.classList.remove('active');
                    }
                });
            } else {
                filterSearch(query);
            }
        });

        // Click to copy symbol
        document.addEventListener('click', (e) => {
            const row = e.target.closest('.symbol-row');
            if (row) {
                const symbol = row.dataset.symbol;
                if (symbol) {
                    copyToClipboard(symbol);
                    // Blur after a brief delay to show the copy happened, then restore hover
                    setTimeout(() => row.blur(), 500);
                }
            }
        });
    </script>
</body>
</html>
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✓ Generated HTML reference: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate documentation from XCompose files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s XCompose --checklist              # Generate verification checklist
  %(prog)s XCompose --json                   # Generate JSON for TUI
  %(prog)s XCompose --html                   # Generate HTML reference
  %(prog)s XCompose --all                    # Generate all formats
  %(prog)s XCompose --stats                  # Show statistics only
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        default='XCompose',
        help='Path to XCompose file (default: XCompose)'
    )

    parser.add_argument(
        '--checklist',
        action='store_true',
        help='Generate Markdown checklist'
    )


    parser.add_argument(
        '--json',
        action='store_true',
        help='Generate JSON export'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML reference'
    )

    parser.add_argument(
        '--table',
        action='store_true',
        help='Generate Markdown table reference'
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Generate all formats'
    )

    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics only'
    )

    parser.add_argument(
        '--output-dir',
        default='docs',
        help='Output directory for generated files (default: docs/)'
    )

    args = parser.parse_args()

    # If no format specified, show help
    if not (args.checklist or args.json or args.html or args.table or args.all or args.stats):
        parser.print_help()
        return 1

    # Parse XCompose file
    print(f"Parsing {args.file}...")
    xc_parser = XComposeParser(args.file)
    if not xc_parser.parse():
        return 1

    print(f"✓ Parsed {len(xc_parser.sequences)} sequences from {len(xc_parser.categories)} categories\n")

    # Show statistics
    if args.stats or args.all:
        stats = xc_parser.get_statistics()
        print("Statistics:")
        print(f"  Total sequences: {stats['total_sequences']}")
        print(f"  Total categories: {stats['total_categories']}")
        print(f"  Unique prefixes: {stats['unique_prefixes']}")
        print(f"  Sequence length: {stats['sequence_length']['min']}-{stats['sequence_length']['max']} (avg: {stats['sequence_length']['avg']:.1f})")
        print(f"\nTop prefixes:")
        for prefix, count in stats['top_prefixes'][:5]:
            print(f"    <{prefix}>: {count} sequences")
        print()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Generate outputs
    if args.checklist or args.all:
        generator = MarkdownChecklistGenerator(xc_parser)
        generator.generate(str(output_dir / 'xcompose_checklist.md'))

    if args.json or args.all:
        generator = JSONGenerator(xc_parser)
        generator.generate(str(output_dir / 'xcompose_sequences.json'))

    if args.html or args.all:
        generator = HTMLGenerator(xc_parser)
        generator.generate(str(output_dir / 'xcompose_reference.html'))

    if args.table or args.all:
        generator = MarkdownTableGenerator(xc_parser)
        generator.generate(str(output_dir / 'xcompose_table.md'))

    print("\n✓ Generation complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
