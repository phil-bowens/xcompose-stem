# Contributing to XCompose-STEM

Thank you for your interest in contributing! This guide will help you add new sequences or improve existing ones.

## Quick Start

1. **Fork the repository**
2. **Clone your fork**
3. **Make changes** to `XCompose`
4. **Validate** your changes
5. **Submit a pull request**

## Adding New Sequences

### 1. Edit the XCompose File

Add your sequence to the appropriate category in `XCompose`:

```
<Multi_key> <h> <example> : "★" U2605  # [MNEMONIC] Black star
```

**Format requirements:**
- Use `<Multi_key>` prefix
- Include Unicode codepoint (U+XXXX format)
- Add type tag: `[ICONIC]` or `[MNEMONIC]`
- Write clear description

### 2. Choose the Right Type Tag

**`[ICONIC]`** - Sequences that visually resemble their output:
```
<Multi_key> <minus> <greater> : "→" U2192  # [ICONIC] Rightwards arrow
<Multi_key> <less> <equal> : "≤" U2264     # [ICONIC] Less than or equal
```

**Characteristics:** Self-documenting, language-independent, typically 2-3 keys

**`[MNEMONIC]`** - Sequences based on linguistic/semantic associations:
```
<Multi_key> <h> <impl> : "⇒" U21D2        # [MNEMONIC] Implies
<Multi_key> <g> <a> : "α" U03B1            # [MNEMONIC] Greek small letter alpha
```

**Characteristics:** Abbreviations or names, systematic prefixes, discoverable patterns

### 3. Follow Prefix Conventions

| Prefix | Category | Example |
|--------|----------|---------|
| `h` | Higher math/logic/sets | `<h> <impl>` → ⇒ |
| `g` | Greek letters | `<g> <a>` → α |
| `k` | Keyboard/UI glyphs | `<k> <cmd>` → ⌘ |
| `b` | Box drawing | `<b> <ul>` → ┌ |
| `p` | Phonetic (IPA) | `<p> <schwa>` → ə |
| `u` | Music notation | `<u> <note>` → ♪ |
| `c` | Currency | `<c> <euro>` → € |

### 4. Validate Your Changes

**Required before submitting PR:**

```bash
# Check for conflicts and syntax errors
./tools/validate_xcompose.py XCompose

# Check design quality
./tools/audit_xcompose_design.py XCompose

# Regenerate documentation
./tools/generate_xcompose_docs.py XCompose --all
```

All validation must pass with zero errors.

## Design Principles

### Completeness
If you add a symbol with variants, add **all of them**:
- Arrows: Add both directions (←, →, ↑, ↓)
- Inequalities: Add inverse (<, >, ≤, ≥)
- Sets: Add complement (⊂, ⊃, ⊆, ⊇)

### Dual Access (Optional)
Common symbols should ideally have both:
- **Visual shortcut**: Fast, intuitive (`->` → →)
- **Mnemonic**: Discoverable (`h rarrow` → →)

### Avoid Conflicts
- Run validator before submitting
- Don't create sequences that shadow longer sequences
- Check for duplicate definitions

## Pull Request Process

1. **Create a branch** for your changes
   ```bash
   git checkout -b add-symbol-name
   ```

2. **Make your changes** to `XCompose`

3. **Run validation** (all must pass)
   ```bash
   ./tools/validate_xcompose.py XCompose
   ./tools/audit_xcompose_design.py XCompose
   ```

4. **Regenerate docs**
   ```bash
   ./tools/generate_xcompose_docs.py XCompose --all
   ```

5. **Commit your changes**
   ```bash
   git add XCompose docs/
   git commit -m "Add: [symbol] for [use case]"
   ```

6. **Push and create PR**
   ```bash
   git push origin add-symbol-name
   ```

### PR Requirements

Your PR must include:
- [ ] Changes to `XCompose`
- [ ] Updated generated docs (in `docs/`)
- [ ] Zero validation errors
- [ ] Clear commit message explaining the change
- [ ] Why the symbol is useful (in PR description)

## Reporting Issues

### Found a Bug?
- Check if sequence produces wrong output
- Run validator to confirm
- Open issue with: symbol, sequence, expected vs actual

### Requesting a Symbol?
- Check if it already exists (search `docs/xcompose_reference.html`)
- Open issue with: symbol, Unicode codepoint, use case
- Bonus: Suggest a sequence that fits the conventions

## Code of Conduct

- Be respectful and constructive
- Focus on technical merit
- Help maintain quality standards
- Welcome newcomers

## Questions?

- **Installation help**: See [README.md](README.md)
- **Technical questions**: Open a GitHub issue
- **General discussion**: Start a GitHub Discussion

## Testing

Before submitting, test your sequences:

1. **Install locally for testing**
   ```bash
   # Option 1: Use the installer (creates include directive)
   ./install.sh

   # Option 2: Temporarily add include to your ~/.XCompose
   echo 'include "/path/to/your/clone/XCompose"' >> ~/.XCompose
   ```

2. **Reload XCompose** (method varies by DE)

3. **Test your sequences** manually

4. **Verify no conflicts** with existing shortcuts

5. **When done testing, restore your original setup**
   ```bash
   ./uninstall.sh  # If you used the installer
   ```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make XCompose-STEM better!**
