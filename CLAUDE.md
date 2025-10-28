# XCompose-STEM - Developer Documentation

**Architecture, design decisions, and development guide for maintainers**

For user-facing docs, see [README.md](README.md) | For contributing, see [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Project Scope

This is a personal XCompose configuration, maintained for my own use and shared as a reference implementation.

**Maintenance:** Active for personal use; contributions are welcome but not actively solicited. Changes are driven by real-world needs rather than feature requests.

**For forkers:** This is designed to be forkable. The tooling, documentation, and systematic design make it straightforward to customize for different symbol sets or workflows.

This document describes the architecture and development practices for maintainers and contributors.

---

## 🏗️ Architecture & Design

### Repository Structure

```
xcompose-stem/
├── README.md                         # User-facing documentation
├── CONTRIBUTING.md                   # Contributor guidelines
├── CLAUDE.md                         # This file - architecture & development docs
├── LICENSE                           # MIT License
├── XCompose                          # Main configuration file (SINGLE SOURCE OF TRUTH)
├── install.sh                        # Installation script
├── uninstall.sh                      # Uninstallation script
│
├── .github/workflows/                # CI/CD Pipelines
│   ├── validate.yml                  # Validation on push/PR
│   └── deploy-pages.yml              # GitHub Pages deployment
│
├── tools/                            # Quality Assurance Tools
│   ├── README.md                     # Tool usage documentation
│   ├── validate_xcompose.py          # Conflict detection & format validation
│   ├── audit_xcompose_design.py      # Design quality analysis
│   ├── generate_xcompose_docs.py     # Documentation generator
│   └── auto_tag_xcompose.py          # Auto-tagging utility
│
└── docs/                             # Generated Documentation
    ├── index.html                    # GitHub Pages landing page
    ├── xcompose_reference.html       # Interactive web reference (tiling WM optimized)
    ├── xcompose_table.md             # Comprehensive Markdown table
    ├── xcompose_sequences.json       # TUI/fuzzy finder data
    └── xcompose_checklist.md         # Manual testing checklist
```

### Design Principles

#### 1. Single Source of Truth
The `XCompose` file is the **only** authoritative source. All documentation is generated from it.

Comment format includes type tags:
```
<Multi_key> <minus> <greater> : "→" U2192  # [ICONIC] Rightwards arrow
<Multi_key> <h> <rarrow> : "→" U2192       # [MNEMONIC] Rightwards arrow
<Multi_key> <g> <a> : "α" U03B1            # [MNEMONIC] Greek small letter alpha
```

Type tags (based on Peircean semiotics):
- `[ICONIC]` - Sequences that visually resemble their output (self-documenting, language-independent)
- `[MNEMONIC]` - Sequences based on linguistic/semantic associations (abbreviations, systematic prefixes)

See `docs/taxonomy-refinement-proposal.md` for the theoretical foundation and rationale.

#### 2. Dual Access Pattern
Frequently-used symbols should have **both**:
- **ASCII shortcut** (fast, visual): `->`, `>=`, `**`
- **Mnemonic** (discoverable): `hrarrow`, `hgeq`, `htimes`

This balances speed (for experts) with discoverability (for learners).

#### 3. Systematic Prefixes
- `<h>` = Higher math, logic, sets, arrows, calculus
- `<g>` = Greek letters
- `<k>` = Keyboard symbols, navigation
- `<b>` = Box drawing
- `<p>` = Phonetic (IPA)
- `<u>` = Music notation
- `<c>` = Currency

#### 4. Symmetry & Completeness
If a symbol has directional/polar variants, include all:
- left ↔ right
- up ↔ down
- subset ↔ superset
- clockwise ↔ counterclockwise

Example: If we have → (right arrow), we must also have ← ↑ ↓

#### 5. Ergonomic Design
- Most sequences are 2-3 keys
- Common symbols prioritized for short sequences
- Avoid excessive shift key burden
- Minimize typo-prone patterns (when possible)

#### 6. Validation-Driven Development
**Every** edit must pass validation before proceeding:
```bash
./tools/validate_xcompose.py XCompose  # MUST return 0 errors
```

This prevents accumulating technical debt and ensures all sequences are reachable.

#### 7. Quality-Aware Development
Regular design audits ensure:
- No missing symmetries
- Families remain complete
- Ergonomics don't degrade
- Common symbols stay accessible

---

## 🔄 Development Workflow

### Standard Edit Cycle

**Using Makefile** (recommended):
```bash
# 1. Edit XCompose file
vim XCompose

# 2. Validate immediately (REQUIRED)
make validate
# If errors: fix them, return to step 1

# 3. Check design quality
make audit
# Review: length, symmetry, families, confusability

# 4. Regenerate documentation
make docs

# 5. (Optional) Check against system defaults
make check-defaults
# Review: uniqueness %, overlaps, conflicts

# 6. Commit atomically
git add XCompose docs/*
git commit -m "Add X, fix Y, update docs"
```

**Using tools directly**:
```bash
# 1. Edit XCompose file
vim XCompose

# 2. Validate immediately (REQUIRED)
./tools/validate_xcompose.py XCompose
# If errors: fix them, return to step 1

# 3. Check design quality
./tools/audit_xcompose_design.py XCompose
# Review: length, symmetry, families, confusability

# 4. Regenerate documentation
./tools/generate_xcompose_docs.py XCompose --all

# 5. Commit atomically
git add XCompose docs/*
git commit -m "Add X, fix Y, update docs"
```

**Quick all-in-one**:
```bash
make all  # Runs validate + audit + docs
```

### Key Principles

**✅ DO:**
- Validate after EVERY edit
- Run audit before adding new categories
- Regenerate docs when making user-visible changes
- Keep commits atomic (XCompose + generated docs together)
- Test sequences manually using the checklist

**❌ DON'T:**
- Skip validation ("I'll fix it later")
- Accumulate multiple unvalidated edits
- Commit XCompose without regenerating docs
- Add sequences without checking for conflicts
- Break established patterns without documenting why

### Quality Gates

**Before committing:**
- [ ] `validate_xcompose.py` returns 0 errors
- [ ] `audit_xcompose_design.py` shows no new critical issues
- [ ] Generated docs are updated
- [ ] Manual spot-check of new sequences

**Before releasing:**
- [ ] All validation passes
- [ ] Documentation is comprehensive and up-to-date
- [ ] CI pipeline passes
- [ ] `check_system_defaults.py` shows high uniqueness (>70%)
- [ ] Version tagged in git

---

## 🎓 Design Decisions & Rationale

### Why `_a` for subscript instead of `__a`?

**Decision**: Swapped subscript and macron bindings.
- `_a` → ₐ (subscript a)
- `__a` → ā (a with macron)

**Rationale**:
- Subscripts are far more common in scientific writing
- Matches LaTeX convention (`x_a` for subscripts)
- Single underscore more ergonomic
- Macrons still accessible (just one extra key)

### Why `hjoin` AND `><` for bowtie?

**Decision**: Provide both mnemonic and visual shortcut.

**Rationale**:
- `hjoin` is discoverable (you can guess "join operator")
- `><` is fast and visually matches the symbol shape
- Dual access exemplified: learn via mnemonic, speed up via visual
- No conflicts with existing sequences

### Why `h'`, `h2'`, `h3'`, `h4'` instead of `h'`, `h''`, `h'''`, `h''''`?

**Decision**: Number-based pattern for primes.

**Rationale**:
- **Shadowing prevention**: `h'` would shadow `h''` (unreachable)
- **Clarity**: `h2'` is unambiguous (2 = double prime)
- **Scalability**: Works for quadruple prime without confusion
- **Consistency**: Base case + numbered extensions

### Why "h-prefix overload" is acceptable?

**Observation**: `<h>` prefix has many sequences across multiple categories.

**Rationale**:
- `h` = "higher math" is broad by design
- Math/logic/sets are conceptually related
- Alternative (splitting into multiple prefixes) breaks muscle memory
- Solved via **documentation**, not reorganization
- Subcategories in comments provide discoverability

---

## 📊 Known Issues & Future Work

### High Priority

1. **Remove redundant long sequences**
   - Some mnemonics are excessively long when ASCII shortcuts exist
   - Review sequences >6 keys for removal candidates

2. **Add ASCII shortcuts for common math**
   - `∂` (partial derivative) - currently only mnemonic
   - `√` (square root) - currently only mnemonic
   - Potential: `d/` or `d6` for ∂, `/v` for √

3. **Improve dual access coverage**
   - Add mnemonics for existing ASCII-only shortcuts
   - Target: common symbols should have both access methods

### Medium Priority

4. **Document confusing namespaces**
   - Some prefixes have many variants (e.g., `<h><t>` has turnstile, times, therefore...)
   - Create cheat sheet grouping all variations

### Low Priority

5. **Consider frequency-based optimization**
   - Track actual usage patterns
   - Optimize most-used sequences first
   - Data-driven design decisions

6. **Keyboard layout analysis**
   - Currently optimized for QWERTY
   - Consider Dvorak/Colemak compatibility

7. **Visual TUI for discovery**
   - Interactive browser for sequences
   - Fuzzy search integration
   - Real-time preview

---

## 🧪 Testing & Validation

### Automated Tests (Always Run)

```bash
# Correctness (MUST PASS)
./tools/validate_xcompose.py XCompose

# Quality (SHOULD REVIEW)
./tools/audit_xcompose_design.py XCompose --verbose
```

### CI Pipeline

**Validation Workflow** (`.github/workflows/validate.yml`):
- Runs on every push/PR
- Validates XCompose syntax
- Runs design audit
- Checks documentation is up to date

**GitHub Pages Deployment** (`.github/workflows/deploy-pages.yml`):
- Runs on push to main/master
- Generates fresh documentation
- Deploys to GitHub Pages
- Live docs: `https://phil-bowens.github.io/xcompose-stem/`

GitHub Pages is configured to deploy automatically on every push to master. The workflow builds the docs and publishes them to the `gh-pages` branch.

### Manual Testing

Use generated checklist:
```bash
make docs  # Generates all docs including checklist
# Open docs/xcompose_checklist.md
# Test each sequence manually, check off boxes
```

### Integration Testing

1. **Load XCompose**:
   ```bash
   # Use the install script (adds via include directive)
   ./install.sh

   # Or manually add include to ~/.XCompose
   echo 'include "/path/to/repo/XCompose"' >> ~/.XCompose

   # Restart X session or reload XCompose
   ```

2. **Spot test common symbols**:
   - Type `->` → should get →
   - Type `<=` → should get ≤
   - Type `ga` → should get α
   - Type `h'` → should get ′

3. **Check for conflicts**:
   - Try typing normal text
   - Ensure no accidental triggers
   - Verify sequences complete properly

---

## 📚 Documentation Map

**For Users:**
- `README.md` - Installation, quick start, feature overview
- `docs/xcompose_reference.html` - Interactive symbol browser ⭐ **START HERE**
- `docs/xcompose_checklist.md` - Manual testing checklist
- `docs/xcompose_sequences.json` - For TUI/fuzzy finder integration
- Live docs: `https://phil-bowens.github.io/xcompose-stem/`

**For Contributors:**
- `CONTRIBUTING.md` - How to contribute ⭐ **START HERE**
- `CLAUDE.md` - This file - architecture & design rationale
- `tools/README.md` - Quality assurance tool documentation

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

### Quick Start

1. **Check if symbol already exists**:
   ```bash
   grep "U2190" XCompose  # Search by codepoint
   grep "→" XCompose      # Search by symbol
   ```

2. **Design the sequence**:
   - Follow prefix conventions (`h`, `g`, `k`, etc.)
   - Keep it short (2-4 keys ideal)
   - Make it memorable
   - Check for symmetry (need variants?)

3. **Add to XCompose** with proper comment format:
   ```
   <Multi_key> <sequence> : "symbol" UXXXX  # [TYPE] Description
   ```

4. **Validate immediately**:
   ```bash
   make validate
   ```

5. **Regenerate docs**:
   ```bash
   make docs
   ```

6. **Commit atomically**:
   ```bash
   git add XCompose docs/*
   git commit -m "Add symbol X with sequence Y"
   ```

---

## 📖 Learning Resources

**XCompose Format:**
- [Official Compose File Spec](https://www.x.org/releases/current/doc/libX11/i18n/compose/compose-chart.html)
- [ArchWiki: XCompose](https://wiki.archlinux.org/title/Xorg/Keyboard_configuration#Configuring_compose_key)

**Unicode References:**
- [Unicode Character Search](https://unicode-table.com/)
- [Mathematical Operators](https://en.wikipedia.org/wiki/Mathematical_operators_and_symbols_in_Unicode)
- [List of Unicode Characters](https://en.wikipedia.org/wiki/List_of_Unicode_characters)

**Quality Assurance:**
- Run `./tools/audit_xcompose_design.py --help` for tool usage
- See `tools/README.md` for workflow details

---

## 🙏 Acknowledgments

**Developed with:**
- Claude Code (Anthropic) - AI pair programming assistant
- Grok (xAI) - Design feedback and analysis
- ChatGPT (OpenAI) - Additional development support
- XCompose (X.Org) - Compose key mechanism
- Python 3 - Quality assurance tools

**Inspiration:**
- LaTeX math notation
- Vim mnemonic patterns
- Standard XCompose conventions
- Mathematical typography traditions

---

**Last Updated**: 2025-10-26
**Status**: Stable, actively maintained

---

*This project represents a thoughtful, systematic approach to XCompose configuration design. Every sequence is intentional. Every decision is documented. Every change is validated. The result: a reliable, usable, high-quality tool for technical writing.*
