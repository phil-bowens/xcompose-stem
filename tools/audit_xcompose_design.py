#!/usr/bin/env python3
"""
XCompose-STEM: Design Audit Tool

Analyzes XCompose file for:
1. ASCII shortcut + mnemonic coverage (dual access principle)
2. Symmetry (left/right, up/down, variants)
3. Family completeness (if A exists, should B exist?)
4. Design consistency

Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals

Copyright (c) 2025 Phil Bowens
Repository: https://github.com/phil-bowens/xcompose-stem
License: MIT

Usage: ./audit_xcompose_design.py XCompose [--verbose] [--json]
"""

import sys
import json
from collections import defaultdict
from typing import List, Set, Dict, Optional, Tuple

from xcompose_lib import XComposeSequence, parse_xcompose


class DesignAuditor:
    """Audit XCompose design for coverage, symmetry, and completeness"""

    def __init__(self, sequences: List[XComposeSequence]):
        self.sequences = sequences
        self.symbol_to_seqs: Dict[str, List[XComposeSequence]] = defaultdict(list)

        # Build symbol mapping
        for seq in sequences:
            self.symbol_to_seqs[seq.symbol].append(seq)

    def audit_dual_access(self) -> Dict[str, List[XComposeSequence]]:
        """Check ASCII + mnemonic coverage"""
        has_both = []
        ascii_only = []
        mnemonic_only = []
        neither = []

        for symbol, seqs in self.symbol_to_seqs.items():
            has_ascii = any(s.is_ascii_shortcut for s in seqs)
            has_mnemonic = any(s.is_mnemonic for s in seqs)

            if has_ascii and has_mnemonic:
                has_both.append((symbol, seqs))
            elif has_ascii:
                ascii_only.append((symbol, seqs))
            elif has_mnemonic:
                mnemonic_only.append((symbol, seqs))
            else:
                neither.append((symbol, seqs))

        return {
            'both': has_both,
            'ascii_only': ascii_only,
            'mnemonic_only': mnemonic_only,
            'neither': neither
        }

    def audit_symmetry(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Check for symmetry patterns (left/right, up/down, etc.)"""
        issues = []

        # Define symmetry pairs to check
        symmetry_pairs = [
            ('left', 'right'),
            ('up', 'down'),
            ('less', 'greater'),
            ('open', 'close'),
            ('start', 'end'),
            ('top', 'bottom'),
            ('upper', 'lower'),
            ('black', 'white'),
            ('forward', 'backward'),
            ('clockwise', 'counterclockwise'),
        ]

        for word1, word2 in symmetry_pairs:
            # Find sequences containing word1
            seqs_with_word1 = [
                s for s in self.sequences
                if any(word1 in k.lower() for k in s.keys) or
                   (s.comment and word1 in s.comment.lower())
            ]

            for seq1 in seqs_with_word1:
                # Try to construct symmetric key sequence
                symmetric_keys = []
                for key in seq1.keys:
                    if word1 in key.lower():
                        symmetric_keys.append(key.replace(word1, word2))
                    else:
                        symmetric_keys.append(key)

                # Check if symmetric sequence exists
                symmetric_exists = any(
                    s.keys == symmetric_keys for s in self.sequences
                )

                if not symmetric_exists:
                    issues.append((
                        seq1.symbol,
                        seq1.key_string,
                        ' '.join(symmetric_keys),
                        f"Has {word1}, missing {word2}?"
                    ))

        # Also check for symbol patterns in comments
        comment_pairs = [
            ('left', 'right'),
            ('up', 'down'),
            ('forward', 'backward'),
        ]

        for word1, word2 in comment_pairs:
            symbols_with_word1 = {}
            for seq in self.sequences:
                if seq.comment and word1 in seq.comment.lower():
                    symbols_with_word1[seq.symbol] = seq

            for symbol, seq in symbols_with_word1.items():
                # Look for symmetric comment
                symmetric_comment_exists = any(
                    s.comment and word2 in s.comment.lower() and
                    s.category == seq.category
                    for s in self.sequences
                )

                if not symmetric_comment_exists:
                    # Check if it's intentional (some symbols don't have pairs)
                    pass  # Don't report everything, too noisy

        return {'symmetry_issues': issues}

    def audit_family_completeness(self) -> Dict[str, List[Dict]]:
        """Check for completeness within symbol families"""
        issues = []

        # Define families to check
        families = {
            'arrows': {
                'symbols': ['→', '←', '↑', '↓', '↔', '↕'],
                'names': ['right', 'left', 'up', 'down', 'left-right', 'up-down']
            },
            'double_arrows': {
                'symbols': ['⇒', '⇐', '⇑', '⇓', '⇔'],
                'names': ['implies', 'implied', 'up double', 'down double', 'iff']
            },
            'long_arrows': {
                'symbols': ['⟶', '⟵', '⟷'],
                'names': ['long right', 'long left', 'long left-right']
            },
            'inequalities': {
                'symbols': ['<', '>', '≤', '≥', '≪', '≫', '≠'],
                'names': ['less', 'greater', 'leq', 'geq', 'much less', 'much greater', 'not equal']
            },
            'set_relations': {
                'symbols': ['∈', '∉', '∋', '∌', '⊂', '⊃', '⊆', '⊇'],
                'names': ['in', 'not in', 'contains', 'not contains',
                          'subset', 'superset', 'subset-eq', 'superset-eq']
            },
            'logical': {
                'symbols': ['∧', '∨', '¬', '∀', '∃'],
                'names': ['and', 'or', 'not', 'forall', 'exists']
            },
            'turnstiles': {
                'symbols': ['⊢', '⊣', '⊨', '⊭'],
                'names': ['proves', 'reverse proves', 'models', 'not models']
            },
        }

        existing_symbols = {seq.symbol for seq in self.sequences}

        for family_name, family_data in families.items():
            expected = set(family_data['symbols'])
            actual = expected & existing_symbols
            missing = expected - actual

            if missing:
                issues.append({
                    'family': family_name,
                    'expected': list(expected),
                    'actual': list(actual),
                    'missing': list(missing),
                    'coverage': f"{len(actual)}/{len(expected)}"
                })

        return {'family_issues': issues}

    def audit_prefix_consistency(self) -> Dict[str, any]:
        """Check that prefixes are used consistently"""
        prefix_usage = defaultdict(set)

        for seq in self.sequences:
            if seq.keys and seq.is_mnemonic:
                prefix = seq.keys[0]
                prefix_usage[prefix].add(seq.category)

        return {'prefix_categories': {k: list(v) for k, v in prefix_usage.items()}}


def audit_usage_patterns(sequences: List[XComposeSequence]) -> Dict[str, any]:
    """Analyze real-world usage patterns and potential issues"""

    # Ergonomics: sequence length distribution
    length_dist = {}
    for length in range(2, 11):
        seqs = [s for s in sequences if len(s.keys) == length]
        length_dist[length] = len(seqs)

    # Very long sequences (>=6 keys)
    long_sequences = sorted([s for s in sequences if len(s.keys) >= 6],
                           key=lambda x: len(x.keys), reverse=True)

    # Confusability: prefix clustering
    prefix_clusters = {}
    for seq in sequences:
        if len(seq.keys) >= 2:
            prefix = tuple(seq.keys[:2])
            if prefix not in prefix_clusters:
                prefix_clusters[prefix] = []
            prefix_clusters[prefix].append(seq)

    # High confusability prefixes (>5 sequences)
    confusing_prefixes = [(p, len(seqs)) for p, seqs in prefix_clusters.items()
                          if len(seqs) > 5]
    confusing_prefixes.sort(key=lambda x: x[1], reverse=True)

    # Repeated key patterns (typo-prone)
    repeated_key_seqs = []
    for seq in sequences:
        if len(seq.keys) >= 3:
            for i in range(len(seq.keys) - 1):
                if seq.keys[i] == seq.keys[i+1]:
                    repeated_key_seqs.append(seq)
                    break

    # Shift key burden
    shift_keys = {'asciicircum', 'quotedbl', 'exclam', 'asterisk', 'parenleft',
                  'parenright', 'plus', 'colon', 'less', 'greater', 'underscore'}

    heavy_shift = []
    for seq in sequences:
        shift_count = sum(1 for k in seq.keys
                         if k in shift_keys or (len(k) == 1 and k.isupper()))
        if shift_count >= 3 and len(seq.keys) <= 4:
            heavy_shift.append((seq, shift_count))
    heavy_shift.sort(key=lambda x: x[1], reverse=True)

    # Common math symbols accessibility
    common_math = ['±', '×', '÷', '∞', '∂', '∇', '∫', '∑', '∏', '√', '∛']
    math_access = {}
    for symbol in common_math:
        matches = [s for s in sequences if s.symbol == symbol]
        if matches:
            shortest = min(matches, key=lambda x: len(x.keys))
            math_access[symbol] = {
                'shortest_length': len(shortest.keys),
                'shortest_keys': shortest.key_string,
                'alternatives': len(matches)
            }

    return {
        'length_dist': length_dist,
        'long_sequences': long_sequences[:10],
        'confusing_prefixes': confusing_prefixes[:10],
        'repeated_key_seqs': repeated_key_seqs,
        'heavy_shift': heavy_shift[:10],
        'math_access': math_access
    }


def generate_report(sequences: List[XComposeSequence], verbose: bool = False):
    """Generate human-readable audit report"""
    auditor = DesignAuditor(sequences)

    print("=" * 70)
    print("XCompose Design & Usage Quality Report")
    print("=" * 70)
    print(f"\nTotal sequences: {len(sequences)}")
    print(f"Unique symbols: {len(auditor.symbol_to_seqs)}")

    # Dual Access Audit
    print("\n" + "=" * 70)
    print("1. DUAL ACCESS COVERAGE (ASCII + Mnemonic)")
    print("=" * 70)

    dual = auditor.audit_dual_access()

    print(f"\n✅ Symbols with BOTH ASCII + mnemonic: {len(dual['both'])}")
    if verbose and dual['both']:
        for symbol, seqs in dual['both'][:10]:
            ascii_seq = next(s for s in seqs if s.is_ascii_shortcut)
            mnem_seq = next(s for s in seqs if s.is_mnemonic)
            print(f"  {symbol:3} : {ascii_seq.key_string:15} + {mnem_seq.key_string}")
        if len(dual['both']) > 10:
            print(f"  ... and {len(dual['both']) - 10} more")

    print(f"\n⚠️  Symbols with ASCII ONLY: {len(dual['ascii_only'])}")
    if dual['ascii_only']:
        for symbol, seqs in dual['ascii_only'][:15]:
            seq = seqs[0]
            print(f"  {symbol:3} : {seq.key_string:20} — {seq.comment or 'no comment'}")

    print(f"\n⚠️  Symbols with MNEMONIC ONLY: {len(dual['mnemonic_only'])}")
    if verbose and dual['mnemonic_only']:
        for symbol, seqs in dual['mnemonic_only'][:15]:
            seq = seqs[0]
            print(f"  {symbol:3} : {seq.key_string:20} — {seq.comment or 'no comment'}")
        if len(dual['mnemonic_only']) > 15:
            print(f"  ... and {len(dual['mnemonic_only']) - 15} more")

    # Symmetry Audit
    print("\n" + "=" * 70)
    print("2. SYMMETRY CHECK")
    print("=" * 70)

    symmetry = auditor.audit_symmetry()
    if symmetry['symmetry_issues']:
        print(f"\n⚠️  Potential symmetry gaps: {len(symmetry['symmetry_issues'])}")
        for symbol, keys, symmetric_keys, reason in symmetry['symmetry_issues'][:20]:
            print(f"  {symbol:3} {keys:25} → missing {symmetric_keys:25} ({reason})")
        if len(symmetry['symmetry_issues']) > 20:
            print(f"  ... and {len(symmetry['symmetry_issues']) - 20} more")
    else:
        print("\n✅ No obvious symmetry gaps detected")

    # Family Completeness
    print("\n" + "=" * 70)
    print("3. FAMILY COMPLETENESS")
    print("=" * 70)

    families = auditor.audit_family_completeness()
    if families['family_issues']:
        for issue in families['family_issues']:
            print(f"\n{issue['family'].upper()}: {issue['coverage']} coverage")
            print(f"  Present: {', '.join(issue['actual'])}")
            if issue['missing']:
                print(f"  ⚠️  Missing: {', '.join(issue['missing'])}")
    else:
        print("\n✅ All symbol families complete")

    # Prefix Consistency
    print("\n" + "=" * 70)
    print("4. PREFIX USAGE")
    print("=" * 70)

    prefix_info = auditor.audit_prefix_consistency()
    for prefix, categories in sorted(prefix_info['prefix_categories'].items()):
        print(f"\n<{prefix}> prefix used in:")
        for cat in sorted(categories):
            count = len([s for s in sequences if s.keys and s.keys[0] == prefix and s.category == cat])
            print(f"  - {cat:40} ({count} sequences)")

    # Usage Patterns Audit
    print("\n" + "=" * 70)
    print("5. USAGE PATTERNS & ERGONOMICS")
    print("=" * 70)

    usage = audit_usage_patterns(sequences)

    print("\nSequence Length Distribution:")
    for length in sorted(usage['length_dist'].keys()):
        count = usage['length_dist'][length]
        bar = '█' * (count // 10) if count >= 10 else '▌' if count > 0 else ''
        warning = ""
        if length >= 7:
            warning = " ⚠️  (very long)"
        elif length >= 5:
            warning = " ⚠️  (long)"
        print(f"  {length:2} keys: {count:3} sequences {bar}{warning}")

    if verbose and usage['long_sequences']:
        print(f"\nLongest sequences (top 10):")
        for seq in usage['long_sequences']:
            print(f"  {len(seq.keys)} keys: {seq.key_string[:40]:40} → {seq.symbol}")

    print(f"\nPrefix Confusability (>5 variants per prefix):")
    for prefix, count in usage['confusing_prefixes'][:5]:
        prefix_str = ' '.join(prefix)
        print(f"  {prefix_str:20} → {count} different sequences")

    if usage['repeated_key_seqs']:
        print(f"\nTypo-prone patterns (repeated keys): {len(usage['repeated_key_seqs'])} sequences")
        if verbose:
            for seq in usage['repeated_key_seqs'][:10]:
                print(f"  {seq.key_string[:40]:40} → {seq.symbol}")

    if usage['heavy_shift']:
        print(f"\nHeavy shift burden (≥3 shifts in ≤4 keys):")
        for seq, shift_count in usage['heavy_shift'][:5]:
            print(f"  {shift_count} shifts: {seq.key_string[:30]:30} → {seq.symbol}")

    print(f"\nCommon Math Symbols Accessibility:")
    for symbol, info in usage['math_access'].items():
        length = info['shortest_length']
        keys = info['shortest_keys']
        warning = ""
        if length >= 6:
            warning = " ⚠️  very long"
        elif length >= 4:
            warning = " ⚠️  long"
        print(f"  {symbol} : {keys[:30]:30} ({length} keys){warning}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    dual_coverage = len(dual['both']) / len(auditor.symbol_to_seqs) * 100 if auditor.symbol_to_seqs else 0
    print(f"\nDual access coverage: {dual_coverage:.1f}% of symbols")
    print(f"ASCII-only symbols: {len(dual['ascii_only'])}")
    print(f"Mnemonic-only symbols: {len(dual['mnemonic_only'])}")
    print(f"Potential symmetry gaps: {len(symmetry['symmetry_issues'])}")
    print(f"Incomplete families: {len(families['family_issues'])}")

    # Usage quality metrics
    very_long = len([s for s in sequences if len(s.keys) >= 6])
    print(f"\nUsage Quality:")
    print(f"  Very long sequences (≥6 keys): {very_long}")
    print(f"  Typo-prone patterns: {len(usage['repeated_key_seqs'])}")
    print(f"  High shift burden: {len(usage['heavy_shift'])}")
    print(f"  Confusing prefixes (>5 variants): {len(usage['confusing_prefixes'])}")


def generate_json_report(sequences: List[XComposeSequence]) -> str:
    """Generate machine-readable JSON report"""
    auditor = DesignAuditor(sequences)

    dual = auditor.audit_dual_access()
    symmetry = auditor.audit_symmetry()
    families = auditor.audit_family_completeness()
    prefixes = auditor.audit_prefix_consistency()
    usage = audit_usage_patterns(sequences)

    report = {
        'metadata': {
            'total_sequences': len(sequences),
            'unique_symbols': len(auditor.symbol_to_seqs),
        },
        'dual_access': {
            'both_count': len(dual['both']),
            'ascii_only_count': len(dual['ascii_only']),
            'mnemonic_only_count': len(dual['mnemonic_only']),
            'coverage_percent': len(dual['both']) / len(auditor.symbol_to_seqs) * 100 if auditor.symbol_to_seqs else 0,
            'ascii_only': [
                {
                    'symbol': symbol,
                    'keys': seqs[0].key_string,
                    'comment': seqs[0].comment
                }
                for symbol, seqs in dual['ascii_only']
            ],
        },
        'symmetry': {
            'issues_count': len(symmetry['symmetry_issues']),
            'issues': [
                {
                    'symbol': symbol,
                    'existing_keys': keys,
                    'missing_keys': sym_keys,
                    'reason': reason
                }
                for symbol, keys, sym_keys, reason in symmetry['symmetry_issues']
            ]
        },
        'families': families,
        'prefixes': prefixes,
        'usage_patterns': {
            'length_distribution': usage['length_dist'],
            'very_long_count': len([s for s in sequences if len(s.keys) >= 6]),
            'longest_sequences': [
                {
                    'keys': s.key_string,
                    'length': len(s.keys),
                    'symbol': s.symbol,
                    'comment': s.comment
                }
                for s in usage['long_sequences']
            ],
            'confusing_prefixes_count': len(usage['confusing_prefixes']),
            'typo_prone_count': len(usage['repeated_key_seqs']),
            'heavy_shift_count': len(usage['heavy_shift']),
            'math_symbols_access': usage['math_access']
        }
    }

    return json.dumps(report, indent=2, ensure_ascii=False)


def main():
    if len(sys.argv) < 2:
        print("Usage: audit_xcompose_design.py <XCompose_file> [--verbose] [--json]")
        sys.exit(1)

    filepath = sys.argv[1]
    verbose = '--verbose' in sys.argv
    json_output = '--json' in sys.argv

    sequences = parse_xcompose(filepath)
    if sequences is None:
        sys.exit(1)

    if json_output:
        print(generate_json_report(sequences))
    else:
        generate_report(sequences, verbose)


if __name__ == '__main__':
    main()
