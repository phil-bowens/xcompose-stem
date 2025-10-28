#!/usr/bin/env python3
################################################################################
# check_system_defaults.py
# Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals
#
# Copyright (c) 2025 Phil Bowens
# Repository: https://github.com/phil-bowens/xcompose-stem
# License: MIT
################################################################################
#
# Compares custom XCompose sequences against system defaults to identify:
# - Overlaps (same sequence producing same symbol)
# - Conflicts (same sequence producing different symbol)
# - Unique additions (sequences not in system defaults)
#

import sys
import re
import os
from pathlib import Path
from collections import defaultdict

class ComposeComparator:
    def __init__(self, custom_file, system_file=None):
        self.custom_file = custom_file
        self.system_file = system_file or self._find_system_compose()

        self.custom_sequences = {}
        self.system_sequences = {}

        self.overlaps = []
        self.conflicts = []
        self.unique = []

    def _find_system_compose(self):
        """Find the system's default Compose file intelligently."""
        import locale
        import glob

        # Try to detect current locale
        current_locale = None
        try:
            current_locale = locale.getlocale()[0]
            if current_locale:
                # Convert locale name to X11 format (e.g., en_US.UTF-8)
                if '.' not in current_locale:
                    current_locale = f"{current_locale}.UTF-8"
        except:
            pass

        # Build search order based on detected locale
        candidates = []

        # 1. User's current locale (if detected)
        if current_locale:
            candidates.append(f'/usr/share/X11/locale/{current_locale}/Compose')

        # 2. Common English locales
        candidates.extend([
            '/usr/share/X11/locale/en_US.UTF-8/Compose',
            '/usr/share/X11/locale/en_GB.UTF-8/Compose',
        ])

        # 3. Generic C locale (fallback)
        candidates.append('/usr/share/X11/locale/C/Compose')

        # 4. Try to find ANY Compose file as last resort
        if not any(os.path.exists(c) for c in candidates):
            compose_files = glob.glob('/usr/share/X11/locale/*/Compose')
            if compose_files:
                candidates.append(compose_files[0])

        # Return first existing candidate
        for path in candidates:
            if os.path.exists(path):
                return path

        return None

    def list_available_compose_files(self):
        """List all available system Compose files."""
        import glob

        compose_files = glob.glob('/usr/share/X11/locale/*/Compose')

        if not compose_files:
            return []

        # Parse each file to get sequence count
        results = []
        for filepath in sorted(compose_files):
            locale_name = filepath.split('/locale/')[1].split('/')[0]
            try:
                sequences = self.parse_file(filepath)
                results.append({
                    'locale': locale_name,
                    'path': filepath,
                    'sequences': len(sequences)
                })
            except:
                results.append({
                    'locale': locale_name,
                    'path': filepath,
                    'sequences': '?'
                })

        return results

    def _parse_sequence(self, line):
        """Parse a compose sequence line."""
        # Match: <Multi_key> <key1> <key2> : "output" UXXXX
        pattern = r'^(<Multi_key>(?:\s+<[^>]+>)+)\s*:\s*"([^"]+)"(?:\s+U([0-9A-Fa-f]{4,6}))?'
        match = re.match(pattern, line.strip())

        if match:
            sequence = match.group(1)
            output = match.group(2)
            codepoint = match.group(3)

            # Normalize sequence (remove extra whitespace)
            sequence = ' '.join(sequence.split())

            return sequence, output, codepoint

        return None, None, None

    def parse_file(self, filepath):
        """Parse a Compose file and return sequences dict."""
        sequences = {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue

                    sequence, output, codepoint = self._parse_sequence(line)

                    if sequence and output:
                        sequences[sequence] = {
                            'output': output,
                            'codepoint': codepoint,
                            'line': line_num
                        }

        except Exception as e:
            print(f"Error parsing {filepath}: {e}", file=sys.stderr)
            return {}

        return sequences

    def compare(self):
        """Compare custom sequences against system defaults."""
        print("Parsing files...")
        print(f"  Custom: {self.custom_file}")
        print(f"  System: {self.system_file}")
        print()

        self.custom_sequences = self.parse_file(self.custom_file)
        self.system_sequences = self.parse_file(self.system_file)

        print(f"Custom sequences: {len(self.custom_sequences)}")
        print(f"System sequences: {len(self.system_sequences)}")
        print()

        # Compare
        for seq, custom_data in self.custom_sequences.items():
            if seq in self.system_sequences:
                system_data = self.system_sequences[seq]

                if custom_data['output'] == system_data['output']:
                    # Exact overlap - redundant definition
                    self.overlaps.append({
                        'sequence': seq,
                        'output': custom_data['output'],
                        'custom_line': custom_data['line']
                    })
                else:
                    # Conflict - overriding system default
                    self.conflicts.append({
                        'sequence': seq,
                        'custom_output': custom_data['output'],
                        'system_output': system_data['output'],
                        'custom_line': custom_data['line']
                    })
            else:
                # Unique addition
                self.unique.append({
                    'sequence': seq,
                    'output': custom_data['output'],
                    'codepoint': custom_data['codepoint'],
                    'custom_line': custom_data['line']
                })

    def print_report(self, verbose=False, show_notes=False):
        """Print comparison report."""
        print("=" * 70)
        print("XCompose System Defaults Comparison")
        print("=" * 70)
        print()
        print(f"System file: {self.system_file}")
        print()

        # Summary
        total = len(self.custom_sequences)
        overlap_pct = (len(self.overlaps) / total * 100) if total > 0 else 0
        conflict_pct = (len(self.conflicts) / total * 100) if total > 0 else 0
        unique_pct = (len(self.unique) / total * 100) if total > 0 else 0

        print("📊 SUMMARY")
        print("-" * 70)
        print(f"Total custom sequences:     {total}")
        print(f"Overlaps (redundant):       {len(self.overlaps):4d} ({overlap_pct:5.1f}%)")
        print(f"Conflicts (overrides):      {len(self.conflicts):4d} ({conflict_pct:5.1f}%)")
        print(f"Unique additions:           {len(self.unique):4d} ({unique_pct:5.1f}%)")
        print()

        # Value assessment
        print("🎯 VALUE ASSESSMENT")
        print("-" * 70)

        if unique_pct > 80:
            print("✅ EXCELLENT: Configuration is highly unique!")
            print("   Most sequences are not available in system defaults.")
        elif unique_pct > 60:
            print("✅ GOOD: Configuration adds significant value.")
            print("   Majority of sequences are unique additions.")
        elif unique_pct > 40:
            print("⚠️  MODERATE: About half the sequences are already available.")
            print("   Consider reviewing overlaps for cleanup.")
        else:
            print("⚠️  LOW: Many sequences overlap with system defaults.")
            print("   You may be colliding with common sequences.")

        print()

        # Overlaps
        if self.overlaps:
            print("🔄 OVERLAPS (Redundant - Already in System)")
            print("-" * 70)
            print(f"These {len(self.overlaps)} sequences produce the same output as system defaults.")
            print("They're redundant but harmless (just duplicate definitions).")
            print()

            if verbose:
                for item in self.overlaps[:20]:
                    seq = item['sequence'].replace('<Multi_key> ', '')
                    print(f"  {seq:40s} → {item['output']:5s} (line {item['custom_line']})")

                if len(self.overlaps) > 20:
                    print(f"  ... and {len(self.overlaps) - 20} more")
            else:
                # Show a few examples
                for item in self.overlaps[:5]:
                    seq = item['sequence'].replace('<Multi_key> ', '')
                    print(f"  {seq:40s} → {item['output']}")

                if len(self.overlaps) > 5:
                    print(f"  ... and {len(self.overlaps) - 5} more (use --verbose to see all)")

            print()

        # Conflicts
        if self.conflicts:
            print("⚠️  CONFLICTS (Overriding System Defaults)")
            print("-" * 70)
            print(f"These {len(self.conflicts)} sequences override system defaults.")
            print("This is intentional customization (not necessarily bad).")
            print()

            if verbose or len(self.conflicts) <= 10:
                for item in self.conflicts:
                    seq = item['sequence'].replace('<Multi_key> ', '')
                    print(f"  {seq:40s}")
                    print(f"    System: {item['system_output']:5s}  →  Custom: {item['custom_output']:5s} (line {item['custom_line']})")
                    print()
            else:
                for item in self.conflicts[:5]:
                    seq = item['sequence'].replace('<Multi_key> ', '')
                    print(f"  {seq:40s}")
                    print(f"    System: {item['system_output']:5s}  →  Custom: {item['custom_output']:5s}")

                if len(self.conflicts) > 5:
                    print(f"  ... and {len(self.conflicts) - 5} more (use --verbose to see all)")

            print()

        # Unique additions
        print("✨ UNIQUE ADDITIONS")
        print("-" * 70)
        print(f"These {len(self.unique)} sequences are NOT in system defaults.")
        print()

        if verbose:
            # Group by prefix for better readability
            by_prefix = defaultdict(list)
            for item in self.unique:
                seq_parts = item['sequence'].split()
                if len(seq_parts) >= 2:
                    prefix = seq_parts[1].strip('<>')
                else:
                    prefix = "other"
                by_prefix[prefix].append(item)

            for prefix in sorted(by_prefix.keys()):
                items = by_prefix[prefix]
                print(f"  Prefix '{prefix}': {len(items)} sequences")
                for item in items[:10]:
                    seq = item['sequence'].replace('<Multi_key> ', '')
                    cp = f"U{item['codepoint']}" if item['codepoint'] else ""
                    print(f"    {seq:40s} → {item['output']:5s} {cp}")
                if len(items) > 10:
                    print(f"    ... and {len(items) - 10} more")
                print()
        else:
            # Just show counts by prefix
            by_prefix = defaultdict(int)
            for item in self.unique:
                seq_parts = item['sequence'].split()
                if len(seq_parts) >= 2:
                    prefix = seq_parts[1].strip('<>')
                else:
                    prefix = "other"
                by_prefix[prefix] += 1

            print("  By prefix:")
            for prefix in sorted(by_prefix.keys(), key=lambda x: by_prefix[x], reverse=True):
                print(f"    {prefix:15s}: {by_prefix[prefix]:3d} sequences")

            print()
            print("  Use --verbose to see all unique sequences")
            print()

        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 70)

        if len(self.overlaps) > 50:
            print("• Consider removing overlapping sequences to reduce file size")

        if len(self.conflicts) > 0:
            print("• Review conflicts - ensure overrides are intentional")

        if unique_pct > 70:
            print("• Excellent work! Your configuration is highly unique")
            print("• Consider documenting what makes it special in README")

        if unique_pct < 50:
            print("• Consider focusing on unique STEM symbols")
            print("• Let system defaults handle common symbols")

        print()
        print("=" * 70)

        # Documentation notes (if requested)
        if show_notes:
            self.print_documentation_notes()

    def generate_comparison_table(self, output_format='markdown'):
        """Generate a comparison table of all characters.

        Args:
            output_format: 'markdown', 'csv', or 'tsv'

        Returns a table with columns:
        - Unicode Character
        - Codepoint
        - Custom Sequence(s)
        - System Sequence(s)
        - Status
        """
        # Reorganize data by output character (not by sequence)
        # Multiple sequences can map to same character
        chars_data = {}

        # Process custom sequences
        for seq, data in self.custom_sequences.items():
            output_char = data['output']
            codepoint = data['codepoint'] or ''

            if output_char not in chars_data:
                chars_data[output_char] = {
                    'codepoint': codepoint,
                    'custom_sequences': [],
                    'system_sequences': [],
                    'status': 'Unique'
                }

            # Clean up sequence for display
            clean_seq = seq.replace('<Multi_key> ', '').replace('<', '').replace('>', ' ')
            chars_data[output_char]['custom_sequences'].append(clean_seq)

        # Check system sequences for same output characters
        for seq, sys_data in self.system_sequences.items():
            output_char = sys_data['output']

            if output_char in chars_data:
                clean_seq = seq.replace('<Multi_key> ', '').replace('<', '').replace('>', ' ')
                chars_data[output_char]['system_sequences'].append(clean_seq)

                # Update status - this character is available in system
                if chars_data[output_char]['status'] == 'Unique':
                    chars_data[output_char]['status'] = 'Available in System'

        # Re-check status based on our comparison results
        for conflict in self.conflicts:
            output = conflict['custom_output']
            if output in chars_data:
                chars_data[output]['status'] = 'Override'

        for overlap in self.overlaps:
            output = overlap['output']
            if output in chars_data:
                chars_data[output]['status'] = 'Overlap'

        # Sort by codepoint for consistent ordering
        sorted_chars = sorted(chars_data.items(),
                            key=lambda x: x[1]['codepoint'] if x[1]['codepoint'] else 'ZZZZ')

        # Generate output based on format
        if output_format == 'markdown':
            return self._format_table_markdown(sorted_chars)
        elif output_format == 'csv':
            return self._format_table_csv(sorted_chars)
        elif output_format == 'tsv':
            return self._format_table_tsv(sorted_chars)
        else:
            return self._format_table_markdown(sorted_chars)

    def _format_table_markdown(self, sorted_chars):
        """Format comparison table as Markdown."""
        lines = []
        lines.append("# XCompose Character Comparison Table")
        lines.append("")
        lines.append("Comparison of custom XCompose sequences vs system defaults.")
        lines.append("")
        lines.append(f"- **Total characters:** {len(sorted_chars)}")
        lines.append(f"- **Custom file:** `{self.custom_file}`")
        lines.append(f"- **System file:** `{self.system_file}`")
        lines.append("")
        lines.append("| Character | Codepoint | Custom Sequence(s) | System Sequence(s) | Status |")
        lines.append("|-----------|-----------|-------------------|-------------------|--------|")

        for char, data in sorted_chars:
            # Escape special characters for Markdown
            char_display = char if char not in ['|', '\\'] else f'`{char}`'
            codepoint = f"U+{data['codepoint']}" if data['codepoint'] else "—"

            # Join multiple sequences with <br> for readability
            custom_seqs = '<br>'.join(f"`{s.strip()}`" for s in data['custom_sequences'][:5])
            if len(data['custom_sequences']) > 5:
                custom_seqs += f"<br>*+{len(data['custom_sequences'])-5} more*"

            system_seqs = "—"
            if data['system_sequences']:
                system_seqs = '<br>'.join(f"`{s.strip()}`" for s in data['system_sequences'][:3])
                if len(data['system_sequences']) > 3:
                    system_seqs += f"<br>*+{len(data['system_sequences'])-3} more*"

            status = data['status']

            lines.append(f"| {char_display} | {codepoint} | {custom_seqs} | {system_seqs} | {status} |")

        lines.append("")
        lines.append("## Status Legend")
        lines.append("")
        lines.append("- **Unique**: Character sequence not available in system defaults")
        lines.append("- **Overlap**: Same sequence produces same character in both")
        lines.append("- **Override**: Custom sequence overrides system default for this character")
        lines.append("- **Available in System**: Character can be produced via system defaults (different sequence)")

        return '\n'.join(lines)

    def _format_table_csv(self, sorted_chars):
        """Format comparison table as CSV."""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        writer.writerow(['Character', 'Codepoint', 'Custom Sequences', 'System Sequences', 'Status'])

        for char, data in sorted_chars:
            codepoint = f"U+{data['codepoint']}" if data['codepoint'] else ""
            custom_seqs = '; '.join(s.strip() for s in data['custom_sequences'])
            system_seqs = '; '.join(s.strip() for s in data['system_sequences']) if data['system_sequences'] else ""
            status = data['status']

            writer.writerow([char, codepoint, custom_seqs, system_seqs, status])

        return output.getvalue()

    def _format_table_tsv(self, sorted_chars):
        """Format comparison table as TSV."""
        lines = []
        lines.append("Character\tCodepoint\tCustom Sequences\tSystem Sequences\tStatus")

        for char, data in sorted_chars:
            codepoint = f"U+{data['codepoint']}" if data['codepoint'] else ""
            custom_seqs = '; '.join(s.strip() for s in data['custom_sequences'])
            system_seqs = '; '.join(s.strip() for s in data['system_sequences']) if data['system_sequences'] else ""
            status = data['status']

            lines.append(f"{char}\t{codepoint}\t{custom_seqs}\t{system_seqs}\t{status}")

        return '\n'.join(lines)

    def print_documentation_notes(self):
        """Print suggested documentation for README."""
        print()
        print("=" * 70)
        print("📝 SUGGESTED DOCUMENTATION")
        print("=" * 70)
        print()
        print("Add this section to README.md:")
        print()
        print("```markdown")
        print("## Known System Overrides")
        print()
        print("This configuration intentionally overrides some system default")
        print("Compose sequences to better support STEM workflows:")
        print()

        if self.conflicts:
            # Group conflicts by type
            superscripts = [c for c in self.conflicts if '<asciicircum>' in c['sequence']]
            subscripts = [c for c in self.conflicts if '<underscore>' in c['sequence']]
            currency = [c for c in self.conflicts if c['sequence'].startswith('<Multi_key> <c>')]
            other = [c for c in self.conflicts if c not in superscripts + subscripts + currency]

            if superscripts:
                print(f"### Superscripts ({len(superscripts)} sequences)")
                print("- **Pattern:** `^letter` (e.g., `^a`, `^2`, `^n`)")
                print("- **System default:** Produces circumflex accents (â, ĉ, ê)")
                print("- **Our override:** Produces superscripts (ᵃ, ², ⁿ)")
                print("- **Rationale:** Superscripts are essential for STEM notation (exponents,")
                print("  footnotes, mathematical symbols). Circumflex accents are rarely needed")
                print("  in English/STEM contexts.")
                print()

            if subscripts:
                print(f"### Subscripts ({len(subscripts)} sequences)")
                print("- **Pattern:** `_letter` (e.g., `_a`, `_1`, `_n`)")
                print("- **System default:** Produces macrons (ā, ē, ō)")
                print("- **Our override:** Produces subscripts (ₐ, ₁, ₙ)")
                print("- **Rationale:** Matches LaTeX convention (`x_a` for subscripts). Essential")
                print("  for chemical formulas, mathematical indices, and scientific notation.")
                print("  Macrons are rarely used in English.")
                print()

            if currency:
                print(f"### Currency Shortcuts ({len(currency)} sequences)")
                print("- **Pattern:** `ce`, `cr`, `cR`, etc.")
                print("- **System default:** Various (some Czech characters)")
                print("- **Our override:** Common currencies (€, ₹, ₽)")
                print("- **Rationale:** Quick access to frequently-used currency symbols.")
                print("- **Note:** May conflict with Czech language typing.")
                print()

            if other:
                print(f"### Other Overrides ({len(other)} sequences)")
                for conflict in other[:5]:
                    seq = conflict['sequence'].replace('<Multi_key> ', '')
                    print(f"- `{seq}`: {conflict['system_output']} → {conflict['custom_output']}")
                if len(other) > 5:
                    print(f"- ... and {len(other) - 5} more")
                print()

        print("### Compatibility Notes")
        print()
        print("- **Most users:** These overrides improve usability for STEM work")
        print("- **European language users:** May need to reorder include directives")
        print("  in `~/.XCompose` to prioritize system defaults for accented characters")
        print("- **Alternative:** Use longer mnemonic sequences (e.g., `h sup a` instead")
        print("  of `^a`) which don't conflict with system defaults")
        print()
        print(f"**Statistics:** {len(self.unique)} unique sequences ({len(self.unique)/len(self.custom_sequences)*100:.1f}%) | ")
        print(f"{len(self.conflicts)} intentional overrides ({len(self.conflicts)/len(self.custom_sequences)*100:.1f}%)")
        print("```")
        print()
        print("=" * 70)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Compare custom XCompose against system defaults'
    )
    parser.add_argument(
        'custom_file',
        nargs='?',
        default='XCompose',
        help='Path to custom XCompose file (default: XCompose)'
    )
    parser.add_argument(
        '--system-file',
        help='Path to system Compose file (auto-detected if not specified)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed output with all sequences'
    )
    parser.add_argument(
        '--list-locales',
        action='store_true',
        help='List all available system Compose files and exit'
    )
    parser.add_argument(
        '--notes',
        action='store_true',
        help='Generate documentation notes for README'
    )
    parser.add_argument(
        '--table',
        action='store_true',
        help='Generate comparison table (default: markdown)'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'csv', 'tsv'],
        default='markdown',
        help='Output format for table (default: markdown)'
    )
    parser.add_argument(
        '--output',
        help='Output file for table (default: stdout)'
    )

    args = parser.parse_args()

    # Handle --list-locales
    if args.list_locales:
        comparator = ComposeComparator(args.custom_file if args.custom_file else 'XCompose')
        print("Available system Compose files:")
        print("=" * 70)

        locales = comparator.list_available_compose_files()
        if not locales:
            print("No Compose files found in /usr/share/X11/locale/")
            return 1

        print(f"{'Locale':<30} {'Sequences':<12} Path")
        print("-" * 70)
        for item in locales:
            seq_count = str(item['sequences']).rjust(8)
            print(f"{item['locale']:<30} {seq_count:<12} {item['path']}")

        print()
        print(f"Total locales: {len(locales)}")
        print()
        print("Use --system-file <path> to compare against a specific locale")
        return 0

    if not os.path.exists(args.custom_file):
        print(f"Error: Custom file not found: {args.custom_file}", file=sys.stderr)
        return 1

    comparator = ComposeComparator(args.custom_file, args.system_file)

    if not comparator.system_file:
        print("Error: Could not find system Compose file", file=sys.stderr)
        print("Try specifying it with --system-file", file=sys.stderr)
        return 1

    comparator.compare()

    # Handle --table flag
    if args.table:
        table_output = comparator.generate_comparison_table(output_format=args.format)

        if args.output:
            # Write to file
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(table_output)
            print(f"Table written to: {args.output}")
        else:
            # Print to stdout
            print(table_output)
    else:
        # Default report output
        comparator.print_report(verbose=args.verbose, show_notes=args.notes)

    return 0

if __name__ == '__main__':
    sys.exit(main())
