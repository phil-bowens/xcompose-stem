#!/usr/bin/env python3
"""
xcompose-stem: Auto-Tagger

Automatically adds type tags ([VISUAL], [MNEM], [ALT]) to comments in the
XCompose file based on sequence patterns. Manual review recommended after running.

Part of xcompose-stem - Keyboard shortcuts for STEM symbols on Linux

Copyright (c) 2025 Phil Bowens
Repository: https://github.com/phil-bowens/xcompose-stem
License: MIT
"""

import re
import sys
from pathlib import Path


def classify_sequence(keys):
    """Classify a sequence as VISUAL, MNEM, or ALT."""
    if not keys:
        return 'ALT'

    # Check if it's a mnemonic (starts with common prefixes)
    prefix_keys = {'h', 'g', 'k', 'b', 'p', 'u', 'i', 'c'}
    if keys[0] in prefix_keys:
        return 'MNEM'

    # Check if it's a visual shortcut (2-5 chars, common punctuation)
    ascii_keys = {
        'minus', 'greater', 'less', 'equal', 'exclam', 'asciitilde',
        'asciicircum', 'bar', 'plus', 'asterisk', 'slash', 'colon',
        'period', 'v', 'question', 'quotedbl', 'apostrophe', 'comma',
        'ampersand', 'at', 'numbersign', 'dollar', 'percent',
        'parenleft', 'parenright', 'underscore', 'grave', 'd'
    }
    single_chars = set('0123456789')

    if len(keys) <= 5 and all(k in ascii_keys or k in single_chars for k in keys):
        return 'VISUAL'

    return 'ALT'


def auto_tag_file(filepath, dry_run=False):
    """Auto-tag the XCompose file."""
    path = Path(filepath)

    if not path.exists():
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        return False

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified_lines = []
    changes = {'VISUAL': 0, 'MNEM': 0, 'ALT': 0, 'already_tagged': 0}

    sequence_pattern = re.compile(r'^(<Multi_key>(?:\s+<[^>]+>)+)\s*:\s*"([^"]+)"')
    tag_pattern = re.compile(r'#\s*\[(VISUAL|MNEM|ALT)\]')

    for line in lines:
        stripped = line.strip()

        # Only process sequence lines with comments
        if stripped.startswith('<Multi_key>') and '#' in stripped:
            # Check if already tagged
            if tag_pattern.search(stripped):
                changes['already_tagged'] += 1
                modified_lines.append(line)
                continue

            # Extract keys
            match = sequence_pattern.match(stripped)
            if match:
                sequence = match.group(1).strip()
                keys = re.findall(r'<([^>]+)>', sequence)
                # Remove Multi_key
                keys = [k for k in keys if k != 'Multi_key']

                # Classify
                tag = classify_sequence(keys)
                changes[tag] += 1

                # Add tag to comment
                parts = stripped.split('#', 1)
                if len(parts) == 2:
                    before_comment = parts[0]
                    comment = parts[1].strip()
                    new_line = f"{before_comment}  # [{tag}] {comment}\n"
                    modified_lines.append(new_line)
                else:
                    # No comment found, shouldn't happen but handle it
                    modified_lines.append(line)
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    # Print summary
    print(f"\n{'=' * 70}")
    print("Auto-Tagging Summary")
    print(f"{'=' * 70}")
    print(f"  [VISUAL] tags added: {changes['VISUAL']}")
    print(f"  [MNEM] tags added:   {changes['MNEM']}")
    print(f"  [ALT] tags added:    {changes['ALT']}")
    print(f"  Already tagged:      {changes['already_tagged']}")
    print(f"  Total processed:     {sum(changes.values())}")
    print(f"{'=' * 70}")

    if dry_run:
        print("\nDRY RUN - No changes written to file")
        print("\nSample changes (first 10):")
        count = 0
        for original, modified in zip(lines, modified_lines):
            if original != modified:
                print(f"\nBEFORE: {original.rstrip()}")
                print(f"AFTER:  {modified.rstrip()}")
                count += 1
                if count >= 10:
                    break
        return True

    # Write changes
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(modified_lines)

    print(f"\n✓ File updated: {filepath}")
    print("\n⚠️  IMPORTANT: Please review changes and run validation!")
    print("    ./validate_xcompose.py XCompose")

    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Auto-tag XCompose file with sequence type tags'
    )
    parser.add_argument(
        'file',
        nargs='?',
        default='XCompose',
        help='Path to XCompose file (default: XCompose)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be changed without modifying the file'
    )

    args = parser.parse_args()

    success = auto_tag_file(args.file, dry_run=args.dry_run)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
