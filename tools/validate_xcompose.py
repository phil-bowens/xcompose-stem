#!/usr/bin/env python3
"""
XCompose-STEM: XCompose Validator

Validation tool for XCompose files that checks for:
- Prefix shadowing (complete sequences that shadow longer ones)
- Duplicate sequences (same sequence mapping to different symbols)
- Syntax errors (malformed sequence definitions)
- Statistics and coverage analysis

Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals

Copyright (c) 2025 Phil Bowens
Repository: https://github.com/phil-bowens/xcompose-stem
License: MIT

Exit codes:
    0: All validations passed
    1: Prefix shadowing detected
    2: Duplicate sequences detected
    3: Syntax errors detected
    4: Multiple validation failures
    5: File not found or read error

Author: Phil Bowens (https://github.com/phil-bowens)
License: MIT
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class ValidationError:
    """Represents a validation error with context."""

    def __init__(self, error_type: str, message: str, line_num: int = 0,
                 severity: str = "error", details: Optional[Dict] = None):
        self.error_type = error_type
        self.message = message
        self.line_num = line_num
        self.severity = severity
        self.details = details or {}

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON output."""
        return {
            'type': self.error_type,
            'message': self.message,
            'line': self.line_num,
            'severity': self.severity,
            'details': self.details
        }


class XComposeValidator:
    """Validates XCompose configuration files."""

    def __init__(self, filepath: str, verbose: bool = False):
        self.filepath = Path(filepath)
        self.verbose = verbose
        self.sequences: Dict[str, Tuple[str, int, str]] = {}  # seq -> (symbol, line_num, full_line)
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate_all(self) -> bool:
        """Run all validations. Returns True if all pass."""
        if not self._load_file():
            return False

        self._validate_syntax()
        self._validate_duplicates()
        self._validate_shadowing()
        self._validate_comment_format()

        return len(self.errors) == 0

    def _load_file(self) -> bool:
        """Load and parse the XCompose file."""
        if not self.filepath.exists():
            self.errors.append(ValidationError(
                'file_error',
                f'File not found: {self.filepath}',
                severity='critical'
            ))
            return False

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except UnicodeDecodeError as e:
            self.errors.append(ValidationError(
                'encoding_error',
                f'Invalid UTF-8 encoding: {e}',
                severity='critical'
            ))
            return False
        except Exception as e:
            self.errors.append(ValidationError(
                'read_error',
                f'Failed to read file: {e}',
                severity='critical'
            ))
            return False

        return True

    def _validate_syntax(self):
        """Validate XCompose syntax and extract sequences."""
        # Pattern with explicit Unicode codepoint
        sequence_with_codepoint = re.compile(
            r'^(<Multi_key>(?:\s+<[^>]+>)+)\s*:\s*"([^"]+)"\s+U([0-9A-Fa-f]{4,6})'
        )
        # Pattern without explicit codepoint (multi-char strings or composed sequences)
        sequence_without_codepoint = re.compile(
            r'^(<Multi_key>(?:\s+<[^>]+>)+)\s*:\s*"([^"]+)"\s*(?:#.*)?$'
        )

        for line_num, line in enumerate(self.lines, 1):
            line_stripped = line.strip()

            # Skip comments and empty lines
            if not line_stripped or line_stripped.startswith('#'):
                continue

            # Check for sequence definitions
            if '<Multi_key>' in line_stripped:
                # Try pattern with codepoint first
                match = sequence_with_codepoint.match(line_stripped)
                has_codepoint = True

                if not match:
                    # Try pattern without explicit codepoint
                    match = sequence_without_codepoint.match(line_stripped)
                    has_codepoint = False

                if not match:
                    # Give helpful error messages
                    if '<Multi_key>' in line_stripped and ':' not in line_stripped:
                        self.errors.append(ValidationError(
                            'syntax_error',
                            'Missing colon separator',
                            line_num,
                            details={'line': line_stripped[:60]}
                        ))
                    elif '<Multi_key>' in line_stripped and '"' not in line_stripped:
                        self.errors.append(ValidationError(
                            'syntax_error',
                            'Missing output string in quotes',
                            line_num,
                            details={'line': line_stripped[:60]}
                        ))
                    else:
                        self.errors.append(ValidationError(
                            'syntax_error',
                            'Malformed sequence definition',
                            line_num,
                            details={'line': line_stripped[:60]}
                        ))
                    continue

                sequence = match.group(1).strip()
                symbol = match.group(2)

                # If codepoint is provided, validate it
                if has_codepoint:
                    codepoint = match.group(3)

                    # Only validate single-character outputs
                    if len(symbol) == 1:
                        expected_codepoint = f"{ord(symbol):04X}"
                        if codepoint.upper() != expected_codepoint:
                            self.warnings.append(ValidationError(
                                'codepoint_mismatch',
                                f'Symbol "{symbol}" (U+{expected_codepoint}) does not match declared codepoint U+{codepoint}',
                                line_num,
                                severity='warning',
                                details={'sequence': sequence}
                            ))
                    elif len(symbol) > 1:
                        self.warnings.append(ValidationError(
                            'multi_char_with_codepoint',
                            f'Multi-character output "{symbol}" has codepoint U+{codepoint} (unusual)',
                            line_num,
                            severity='warning',
                            details={'sequence': sequence}
                        ))

                # Store sequence (don't add error for duplicates here - caught in duplicate check)
                if sequence not in self.sequences:
                    self.sequences[sequence] = (symbol, line_num, line_stripped)

                # Validate sequence keys
                self._validate_sequence_keys(sequence, line_num)

    def _validate_sequence_keys(self, sequence: str, line_num: int):
        """Validate individual keys in a sequence."""
        keys = re.findall(r'<([^>]+)>', sequence)

        for key in keys:
            if key == 'Multi_key':
                continue

            # Check for common mistakes
            if ' ' in key:
                self.warnings.append(ValidationError(
                    'suspicious_key',
                    f'Key contains space: "<{key}>"',
                    line_num,
                    severity='warning',
                    details={'sequence': sequence}
                ))

            # Check for very long key names (likely error)
            if len(key) > 20:
                self.warnings.append(ValidationError(
                    'suspicious_key',
                    f'Unusually long key name: "<{key}>"',
                    line_num,
                    severity='warning',
                    details={'sequence': sequence}
                ))

    def _validate_duplicates(self):
        """Check for duplicate sequence definitions."""
        sequence_occurrences = defaultdict(list)

        for line_num, line in enumerate(self.lines, 1):
            line_stripped = line.strip()
            if '<Multi_key>' in line_stripped:
                match = re.match(r'^(<Multi_key>(?:\s+<[^>]+>)+)\s*:', line_stripped)
                if match:
                    sequence = match.group(1).strip()
                    symbol_match = re.search(r':\s*"([^"]+)"', line_stripped)
                    symbol = symbol_match.group(1) if symbol_match else '?'
                    sequence_occurrences[sequence].append((symbol, line_num, line_stripped))

        for sequence, occurrences in sequence_occurrences.items():
            if len(occurrences) > 1:
                # Check if they map to the same symbol (harmless duplicate)
                symbols = {occ[0] for occ in occurrences}
                if len(symbols) == 1:
                    self.warnings.append(ValidationError(
                        'duplicate_harmless',
                        f'Duplicate sequence (same symbol): {sequence} → {symbols.pop()}',
                        occurrences[0][1],
                        severity='warning',
                        details={
                            'sequence': sequence,
                            'occurrences': [{'line': occ[1], 'symbol': occ[0]} for occ in occurrences]
                        }
                    ))
                else:
                    # Different symbols - critical error
                    self.errors.append(ValidationError(
                        'duplicate_conflict',
                        f'Duplicate sequence with different symbols: {sequence}',
                        occurrences[0][1],
                        severity='error',
                        details={
                            'sequence': sequence,
                            'conflicts': [{'line': occ[1], 'symbol': occ[0]} for occ in occurrences]
                        }
                    ))

    def _validate_shadowing(self):
        """Check for prefix shadowing issues."""
        seq_list = sorted(self.sequences.keys())

        for short in seq_list:
            for long in seq_list:
                if short != long and long.startswith(short + ' '):
                    short_sym, short_line, _ = self.sequences[short]
                    long_sym, long_line, _ = self.sequences[long]

                    self.errors.append(ValidationError(
                        'prefix_shadowing',
                        f'{short} → {short_sym} shadows {long} → {long_sym}',
                        short_line,
                        severity='error',
                        details={
                            'shadowing_sequence': short,
                            'shadowing_symbol': short_sym,
                            'shadowing_line': short_line,
                            'shadowed_sequence': long,
                            'shadowed_symbol': long_sym,
                            'shadowed_line': long_line
                        }
                    ))

    def _validate_comment_format(self):
        """Check for standardized comment format with type tags."""
        valid_tags = {'ICONIC', 'MNEMONIC'}
        tag_pattern = re.compile(r'#\s*\[(' + '|'.join(valid_tags) + r')\]\s+(.+)')

        tagged_count = 0
        untagged_count = 0

        for line_num, line in enumerate(self.lines, 1):
            line_stripped = line.strip()

            # Only check sequence lines
            if not line_stripped or not line_stripped.startswith('<Multi_key>'):
                continue

            # Extract comment if present
            if '#' not in line_stripped:
                self.warnings.append(ValidationError(
                    'missing_comment',
                    'Sequence has no comment',
                    line_num,
                    severity='warning',
                    details={'line': line_stripped[:60]}
                ))
                continue

            comment_part = line_stripped.split('#', 1)[1]

            # Check if comment has type tag
            match = tag_pattern.match('#' + comment_part)

            if match:
                tagged_count += 1
                tag_type = match.group(1)
                description = match.group(2).strip()

                # Validate description is not empty
                if not description:
                    self.warnings.append(ValidationError(
                        'empty_description',
                        f'Comment has tag [{tag_type}] but no description',
                        line_num,
                        severity='warning',
                        details={'tag': tag_type}
                    ))

                # Optional: Check for proper description format
                # Could add more checks here (capitalization, punctuation, etc.)
            else:
                untagged_count += 1
                # Only warn if comment doesn't match expected format at all
                if self.verbose:
                    self.warnings.append(ValidationError(
                        'untagged_comment',
                        f'Comment not tagged with [ICONIC] or [MNEMONIC]',
                        line_num,
                        severity='info',
                        details={'comment': comment_part.strip()[:40]}
                    ))

        # Add summary info
        if self.verbose and (tagged_count > 0 or untagged_count > 0):
            total = tagged_count + untagged_count
            pct = (tagged_count / total * 100) if total > 0 else 0
            self.warnings.append(ValidationError(
                'tagging_progress',
                f'Comment tagging: {tagged_count}/{total} ({pct:.1f}%) tagged',
                0,
                severity='info',
                details={'tagged': tagged_count, 'untagged': untagged_count}
            ))

    def get_statistics(self) -> Dict:
        """Get statistics about the XCompose file."""
        if not self.sequences:
            return {}

        # Analyze sequence lengths
        lengths = [len(re.findall(r'<[^>]+>', seq)) - 1 for seq in self.sequences.keys()]  # -1 for Multi_key

        # Analyze prefixes
        prefixes = defaultdict(int)
        for seq in self.sequences.keys():
            keys = re.findall(r'<([^>]+)>', seq)
            if len(keys) >= 2:  # Multi_key + first key
                prefixes[keys[1]] += 1

        # Most common prefixes
        top_prefixes = sorted(prefixes.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            'total_sequences': len(self.sequences),
            'total_lines': len(self.lines),
            'sequence_length': {
                'min': min(lengths) if lengths else 0,
                'max': max(lengths) if lengths else 0,
                'avg': sum(lengths) / len(lengths) if lengths else 0
            },
            'unique_prefixes': len(prefixes),
            'top_prefixes': [{'prefix': k, 'count': v} for k, v in top_prefixes],
            'errors': len(self.errors),
            'warnings': len(self.warnings)
        }

    def print_results(self, show_warnings: bool = True, show_stats: bool = True):
        """Print validation results in human-readable format."""
        stats = self.get_statistics()

        # Print header
        print("=" * 70)
        print(f"XCompose Validation Report")
        print(f"File: {self.filepath.name}")
        print("=" * 70)

        # Print statistics
        if show_stats and stats:
            print(f"\n📊 Statistics:")
            print(f"   Total sequences: {stats['total_sequences']}")
            print(f"   File lines: {stats['total_lines']}")
            print(f"   Sequence length: {stats['sequence_length']['min']}-{stats['sequence_length']['max']} keys (avg: {stats['sequence_length']['avg']:.1f})")
            print(f"   Unique prefixes: {stats['unique_prefixes']}")

            if self.verbose and stats['top_prefixes']:
                print(f"\n   Top prefixes:")
                for prefix_info in stats['top_prefixes'][:5]:
                    print(f"     <{prefix_info['prefix']}>: {prefix_info['count']} sequences")

        # Print errors
        if self.errors:
            print(f"\n❌ Errors Found: {len(self.errors)}")
            print("-" * 70)

            # Group by type
            errors_by_type = defaultdict(list)
            for error in self.errors:
                errors_by_type[error.error_type].append(error)

            for error_type, errors in errors_by_type.items():
                print(f"\n{error_type.replace('_', ' ').title()} ({len(errors)}):")
                for error in errors[:20]:  # Limit output
                    if error.line_num:
                        print(f"  Line {error.line_num}: {error.message}")
                    else:
                        print(f"  {error.message}")

                    if self.verbose and error.details:
                        for key, value in error.details.items():
                            if key == 'conflicts':
                                print(f"    Conflicts:")
                                for conflict in value:
                                    print(f"      Line {conflict['line']}: → {conflict['symbol']}")
                            elif key not in ['line', 'sequence']:
                                print(f"    {key}: {value}")

                if len(errors) > 20:
                    print(f"  ... and {len(errors) - 20} more")
        else:
            print("\n✅ No Errors Found")

        # Print warnings
        if show_warnings and self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            print("-" * 70)

            for warning in self.warnings[:10]:  # Limit output
                if warning.line_num:
                    print(f"  Line {warning.line_num}: {warning.message}")
                else:
                    print(f"  {warning.message}")

            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        # Final verdict
        print("\n" + "=" * 70)
        if not self.errors:
            print("✅ VALIDATION PASSED")
            if stats:
                print(f"   All {stats['total_sequences']} sequences are valid and reachable!")
        else:
            print("❌ VALIDATION FAILED")
            print(f"   {len(self.errors)} error(s) must be fixed")
        print("=" * 70)

    def get_exit_code(self) -> int:
        """Get appropriate exit code based on validation results."""
        if not self.errors:
            return 0

        error_types = {error.error_type for error in self.errors}

        # Critical errors
        if 'file_error' in error_types or 'read_error' in error_types or 'encoding_error' in error_types:
            return 5

        # Check for specific error types
        has_shadowing = 'prefix_shadowing' in error_types
        has_duplicates = 'duplicate_conflict' in error_types
        has_syntax = 'syntax_error' in error_types

        if has_shadowing and has_duplicates:
            return 4
        elif has_shadowing:
            return 1
        elif has_duplicates:
            return 2
        elif has_syntax:
            return 3
        else:
            return 4

    def to_json(self) -> str:
        """Export results as JSON."""
        return json.dumps({
            'file': str(self.filepath),
            'statistics': self.get_statistics(),
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings],
            'passed': len(self.errors) == 0
        }, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description='Validate XCompose configuration files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0: All validations passed
  1: Prefix shadowing detected
  2: Duplicate sequences detected
  3: Syntax errors detected
  4: Multiple validation failures
  5: File not found or read error

Examples:
  %(prog)s XCompose                    # Validate XCompose file
  %(prog)s XCompose -v                 # Verbose output
  %(prog)s XCompose --json             # JSON output for CI/CD
  %(prog)s XCompose --no-warnings      # Hide warnings
  %(prog)s XCompose --quiet            # Only show pass/fail
        """
    )

    parser.add_argument(
        'file',
        nargs='?',
        default='./XCompose',
        help='Path to XCompose file (default: ./XCompose)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed information'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Only show pass/fail result'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )

    parser.add_argument(
        '--no-warnings',
        action='store_true',
        help='Do not show warnings'
    )

    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Do not show statistics'
    )

    args = parser.parse_args()

    # Create validator
    validator = XComposeValidator(args.file, verbose=args.verbose)

    # Run validation
    validator.validate_all()

    # Output results
    if args.json:
        print(validator.to_json())
    elif args.quiet:
        if validator.errors:
            print(f"FAILED: {len(validator.errors)} error(s)")
        else:
            print("PASSED")
    else:
        validator.print_results(
            show_warnings=not args.no_warnings,
            show_stats=not args.no_stats
        )

    return validator.get_exit_code()


if __name__ == '__main__':
    sys.exit(main())
