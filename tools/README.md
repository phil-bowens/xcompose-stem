# XCompose Quality Assurance Tools

This directory contains tools for validating, auditing, and documenting XCompose configurations.

## Tools Overview

| Tool | Purpose | Usage |
|------|---------|-------|
| `validate_xcompose.py` | Syntax & conflict validation | Required before every commit |
| `audit_xcompose_design.py` | Design quality analysis | Recommended for major changes |
| `generate_xcompose_docs.py` | Documentation generation | Run after XCompose changes |
| `check_system_defaults.py` | Compare against system defaults | Recommended before release |
| `auto_tag_xcompose.py` | Bulk comment tagging | One-time or migration tool |

---

## validate_xcompose.py

**Purpose**: Validates XCompose file for syntax errors, conflicts, and format compliance.

**Usage**:
```bash
./tools/validate_xcompose.py XCompose
./tools/validate_xcompose.py XCompose --verbose
./tools/validate_xcompose.py XCompose --json
```

**Checks**:
- ✅ Syntax errors (malformed sequences)
- ✅ Prefix shadowing (unreachable sequences)
- ✅ Duplicate definitions
- ✅ Comment format compliance
- ✅ Unicode codepoint validation

**Exit codes**:
- `0` - All validations passed
- `1` - Prefix shadowing detected
- `2` - Duplicate sequences
- `3` - Syntax errors
- `4` - Multiple failures
- `5` - File not found

**Options**:
- `-v, --verbose` - Show detailed information
- `-q, --quiet` - Only show pass/fail
- `--json` - Output as JSON
- `--no-warnings` - Hide warnings
- `--no-stats` - Hide statistics

---

## audit_xcompose_design.py

**Purpose**: Analyzes design quality and suggests improvements.

**Usage**:
```bash
./tools/audit_xcompose.py XCompose
./tools/audit_xcompose.py XCompose --verbose
```

**Analyzes**:
- Sequence length distribution
- Symbol family completeness
- Dual-access coverage
- Ergonomic issues
- Confusing namespaces
- Typo-prone patterns

**Output**: Generates analysis report with recommendations for improvement.

**Use cases**:
- Before adding a new category
- When reviewing design decisions
- To identify optimization opportunities
- For quality metrics tracking

---

## generate_xcompose_docs.py

**Purpose**: Generates documentation in multiple formats from XCompose file.

**Usage**:
```bash
# Generate all formats
./tools/generate_xcompose_docs.py XCompose --all

# Generate specific formats
./tools/generate_xcompose_docs.py XCompose --html
./tools/generate_xcompose_docs.py XCompose --json
./tools/generate_xcompose_docs.py XCompose --table
./tools/generate_xcompose_docs.py XCompose --checklist

# Show statistics only
./tools/generate_xcompose_docs.py XCompose --stats
```

**Generates**:
- `docs/xcompose_reference.html` - Interactive HTML reference (tiling WM optimized)
- `docs/xcompose_table.md` - Comprehensive Markdown table
- `docs/xcompose_sequences.json` - JSON export for TUIs/fuzzy finders
- `docs/xcompose_checklist.md` - Manual testing checklist

**Options**:
- `--all` - Generate all formats
- `--html` - HTML reference only
- `--json` - JSON export only
- `--table` - Markdown table only
- `--checklist` - Testing checklist only
- `--stats` - Show statistics
- `--output-dir DIR` - Specify output directory

---

## check_system_defaults.py

**Purpose**: Compares custom XCompose sequences against system defaults to identify overlaps, conflicts, and unique additions.

**Usage**:
```bash
# Basic comparison report
./tools/check_system_defaults.py XCompose

# Verbose output with all sequences
./tools/check_system_defaults.py XCompose --verbose

# Generate documentation notes for README
./tools/check_system_defaults.py XCompose --notes

# Generate comparison table (markdown, csv, or tsv)
./tools/check_system_defaults.py XCompose --table
./tools/check_system_defaults.py XCompose --table --format csv
./tools/check_system_defaults.py XCompose --table --format tsv

# Save table to file
./tools/check_system_defaults.py XCompose --table --output docs/xcompose_comparison.md
./tools/check_system_defaults.py XCompose --table --format csv --output comparison.csv

# List all available system Compose files
./tools/check_system_defaults.py --list-locales

# Compare against specific locale
./tools/check_system_defaults.py XCompose --system-file /usr/share/X11/locale/el_GR.UTF-8/Compose
```

**Identifies**:
- **Overlaps**: Sequences producing same output as system (redundant but harmless)
- **Conflicts**: Sequences overriding system defaults (intentional customization)
- **Unique additions**: Sequences not in system defaults

**Multi-Platform Features**:
- Auto-detects user's current locale
- Falls back to common locales (en_US.UTF-8, C)
- Lists all available system Compose files
- Supports comparing against any locale

**Output Formats**:
- **Report** (default): Analysis with statistics, value assessment, and recommendations
- **Table** (--table): Detailed comparison table with columns:
  - Character
  - Codepoint
  - Custom Sequence(s)
  - System Sequence(s)
  - Status (Unique, Overlap, Override, Available in System)
- **Formats**: Markdown (default), CSV, or TSV

**Use cases**:
- Before public release (verify uniqueness)
- Multi-platform testing (check against different locales)
- Documentation generation (explain overrides)
- Quality assessment (measure value-add)
- Side-by-side comparison of custom vs system sequences

---

## auto_tag_xcompose.py

**Purpose**: Automatically tags XCompose comments with type classification.

**Usage**:
```bash
# Dry run (preview changes)
./tools/auto_tag_xcompose.py XCompose --dry-run

# Apply tags
./tools/auto_tag_xcompose.py XCompose
```

**Tags**:
- `[ICONIC]` - Sequences that visually resemble their output
- `[MNEMONIC]` - Sequences based on linguistic/semantic associations

**Use cases**:
- Initial setup of type tagging system
- Migrating from untagged to tagged format
- Bulk reclassification after design changes

**Options**:
- `--dry-run` - Preview changes without modifying file

---

## Integration with CI/CD

These tools are integrated into the GitHub Actions workflow (`.github/workflows/validate.yml`):

1. **On every push/PR**: Validation runs automatically
2. **Documentation check**: Ensures docs are up to date
3. **Design audit**: Reports quality metrics

---

## Requirements

- Python 3.6+
- No external dependencies (pure Python stdlib)

---

## Exit Codes

All tools follow standard exit code conventions:
- `0` - Success
- `non-zero` - Failure (see tool-specific codes above)

This allows integration with CI/CD pipelines and build systems.
