# xcompose-stem

**Keyboard shortcuts for STEM symbols on Linux**

XCompose configuration providing hundreds of keyboard shortcuts for mathematical notation, Greek letters, arrows, and scientific typography.

**Platform:** Linux with X11 or Wayland + XCompose support
**Use case:** Technical writing in any application (browser, Discord, terminal, editors)
**Status:** Active development — mappings may change before v1.0
**License:** MIT

---

## Overview

This is a personal XCompose configuration, maintained for my own use and shared as a reference implementation. It provides systematic keyboard shortcuts for Unicode symbols commonly used in STEM fields, optimized for plain text workflows

---

## Features

- **Hundreds of validated sequences** - Zero internal conflicts, all symbols reachable
- **Dual access patterns** - ASCII shortcuts (`->` → →) + mnemonics (`h rarrow` → →)
- **Systematic prefixes** - `h`=math, `g`=Greek, `k`=keyboard, `p`=IPA, `b`=box-drawing
- **Complete symbol families** - All directional variants (arrows, inequalities, set relations)
- **Quality tooling** - Automated validation, design audits, multi-format documentation
- **Type-tagged sequences** - Every sequence classified as [VISUAL], [MNEM], or [ALT]
- **Frequency-optimized** - Common symbols get shorter sequences
- **LaTeX-inspired ergonomics** - `_` for subscripts (like LaTeX), `__` for macrons

---

## Symbol Coverage

| Category | Prefix | Examples |
|----------|--------|----------|
| Math/Logic/Sets | `h` | ∀ ∃ ∈ ∉ ⊂ ⊆ ∪ ∩ ∫ ∇ ∂ ∑ ∏ √ ∞ ∅ |
| Greek Letters | `g` | α β γ δ ε ζ η θ ι κ λ μ ν ξ π ρ σ φ χ ψ ω |
| Superscripts/Subscripts | `^` / `_` | ⁰¹²³ ᵃᵇᶜ ₀₁₂₃ ₐₑₕᵢ |
| Arrows | ASCII + `h` | → ← ↔ ⇒ ⇐ ⇔ ↑ ↓ ↕ ↗ ↘ ↖ ↙ ⟶ ⟹ |
| Typography | Visual | — – " " ' ' « » … • · |
| IPA Phonetics | `p` | ə ɛ ɪ ʃ θ ð ŋ ɹ ʒ |
| Box Drawing | `b` | ┌ ├ └ ┐ ┤ ┘ ─ │ ═ ║ |
| UI Symbols | `k` | ⌘ ⌥ ⇧ ⌃ ⏎ □ ☑ ○ ▲ |
| Currency | `c` | € £ ¥ ₹ ₽ ₿ |
| Chemistry | `h` + visual | ⚛ ⇌ ↽ ⇁ |
| Astronomy | `h` | ☉ ♁ ♂ ♀ ★ ☆ |
| Music | `u` | ♪ ♫ ♭ ♮ ♯ |
| Legal/Document | Visual | © ® ™ § ¶ † ‡ |

---

## Installation

### Requirements

- Linux distribution with XCompose support (most modern distros)
- X Window System or Wayland
- Compose key configured (see below)

### About the Compose Key

The **Compose key** is a special modifier key that lets you type sequences to create Unicode characters. You press and release the Compose key, then type a sequence of keys to produce a symbol.

**Default Compose key by distribution:**

| Distribution | Default Compose Key |
|--------------|---------------------|
| **Omarchy Linux** | Caps Lock |
| **Ubuntu (GNOME)** | None (must configure manually) |
| **Fedora (GNOME)** | None (must configure manually) |
| **KDE Neon / Kubuntu** | None (must configure manually) |
| **Pop!_OS** | None (must configure manually) |
| **Arch Linux** | None (must configure manually) |
| **Debian** | None (must configure manually) |

**Common choices when configuring:**
- Right Alt (most common)
- Menu key (Windows key between Right Alt and Right Ctrl)
- Caps Lock (Omarchy default, good choice if you rarely use caps)
- Right Ctrl

If your Compose key isn't configured, see [Configuring the Compose Key](#configuring-the-compose-key) below.

### Quick Install

```bash
# Clone the repository (note: using the home directory location)
git clone https://github.com/phil-bowens/xcompose-stem.git ~/.xcompose-stem
cd ~/.xcompose-stem

# Run installer (preserves existing ~/.XCompose sequences)
./install.sh
```

The installer adds an `include` directive to your `~/.XCompose`, preserving any existing configuration.

### Manual Installation

Clone like previous step. Add this line to your `~/.XCompose`:

```bash
include "$HOME/.xcompose-stem/XCompose"
```

If `~/.XCompose` doesn't exist, create it:

```bash
# Include system defaults
include "%L"

# Include xcompose-stem
include "$HOME/.xcompose-stem/XCompose"
```

### Activation

Restart your X session or reload XCompose:
- Omarchy: `omarchy-restart-xcompose`
- **GNOME/KDE:** Log out and log back in
- **i3/sway:** Restart compositor
- **Most systems:** `killall ibus-daemon; ibus-daemon -drx` or similar

### Omarchy Linux Integration

If you're using **Omarchy Linux**, the installer can optionally add a keybinding for quick access to the symbol reference:

**Keybinding:** `Super + Shift + U` → Opens symbol reference in webapp window

The installer will detect Omarchy and offer to add this keybinding automatically. You can also add it manually:

```bash
# Add to ~/.config/hypr/bindings.conf
bindd = SUPER SHIFT, U, Unicode Codepoints, exec, omarchy-launch-webapp "file://$HOME/.xcompose-stem/docs/xcompose_reference.html"
```

This gives you instant access to the full symbol reference while typing, optimized for tiling window manager workflows.

---

## Usage

After installation, type sequences using Compose key + pattern:

```
Compose + -> = →          # Rightward arrow
Compose + <= = ≤          # Less than or equal
Compose + g a = α         # Greek alpha
Compose + h impl = ⇒      # Implies (double arrow)
Compose + _1 = ₁          # Subscript 1
Compose + ^2 = ²          # Superscript 2
Compose + ... = …         # Ellipsis
Compose + --- = —         # Em dash
```

**Tip:** Common symbols have both visual and mnemonic access:
- `Compose + ->` and `Compose + h rarrow` both produce →
- `Compose + >=` and `Compose + h geq` both produce ≥

---

## Documentation

### 📖 Interactive Reference

**[Browse the documentation](https://phil-bowens.github.io/xcompose-stem/)** - Web interface with:
- Search by symbol, sequence, or description
- Category filtering
- Keyboard-first navigation (Tab, Enter, /)
- Clipboard copy on click

**Local:** Open `xcompose_reference.html` in your browser for offline access.

### Other Formats

- **Markdown table:** `xcompose_table.md` - Complete reference in table format
- **JSON export:** `xcompose_sequences.json` - For fuzzy finders and TUIs
- **Testing checklist:** `xcompose_checklist.md` - Manual verification guide

---

## Design Principles

### Cognitive Design

**5 prefix families** for easy memorization:
- `h` - Higher math (∀ ∃ ∫ ∇ → ⇒)
- `g` - Greek letters (α β γ δ)
- `k` - Keyboard/UI symbols (⌘ ⌥ □ ☑)
- `p` - Phonetic/IPA (ə ɛ ʃ θ)
- `b` - Box-drawing (┌ ├ ═)

**Self-documenting mnemonics:**
- `h leq` = "less than or equal" = ≤
- `h impl` = "implies" = ⇒
- `g a` = "Greek alpha" = α

**Dual access for speed + discoverability:**
- Learn via mnemonics (`h rarrow`)
- Speed up with ASCII shortcuts (`->`)

### Completeness

Symbol families include all variants:
- Arrows: → ← ↑ ↓ (basic) + ⇒ ⇐ ⇑ ⇓ (double)
- Inequalities: < > ≤ ≥ ≪ ≫ ≺ ≻
- Sets: ∈ ∉ ∋ ∌ ⊂ ⊃ ⊆ ⊇

If a symbol has directional or logical opposites, both are included.

---

## Quality Assurance

Three Python tools ensure correctness:

```bash
./tools/validate_xcompose.py XCompose       # Conflict detection & syntax validation
./tools/audit_xcompose_design.py XCompose   # Design quality analysis
./tools/generate_xcompose_docs.py XCompose --all  # Generate all documentation
```

See [tools/README.md](tools/README.md) for detailed usage.

---

## Platform Notes

### Tested On

- **Omarchy Linux** (Arch-based, custom desktop environment) - Primary development platform

### Should Work On

- Arch Linux, Ubuntu, Fedora, Debian, Pop!_OS
- GNOME, KDE, Xfce, i3, sway
- Any Linux distribution with standard XCompose support

### Wayland Support

Works via XWayland compatibility layer. Some compositors may have quirks.

### Alternatives for Other Platforms

**macOS:** Use Karabiner-Elements or system text replacements
**Windows:** Use AutoHotkey or WinCompose
**All platforms:** IDE snippets (VS Code, JetBrains), Espanso (cross-platform), Vim digraphs

---

## Configuring the Compose Key

If your Compose key isn't already configured, you'll need to set one up. Here's how for common desktop environments:

**Omarchy Linux:**
Already configured by default (Caps Lock). No setup needed.

**GNOME (Ubuntu, Fedora, Pop!_OS):**
```bash
# Right Alt (most common)
gsettings set org.gnome.desktop.input-sources xkb-options "['compose:ralt']"

# Or Caps Lock (recommended if you rarely use caps)
gsettings set org.gnome.desktop.input-sources xkb-options "['compose:caps']"

# Or Menu key
gsettings set org.gnome.desktop.input-sources xkb-options "['compose:menu']"
```

**KDE (Kubuntu, KDE Neon):**
System Settings → Input Devices → Keyboard → Advanced → Compose key position

**i3/sway:**
Add to your config file:
```bash
# Right Alt
exec_always setxkbmap -option compose:ralt

# Or Caps Lock
exec_always setxkbmap -option compose:caps
```

**Xfce (Xubuntu):**
Settings → Keyboard → Layout → Options → Compose key position

**Testing your Compose key:**
Try typing `Compose + -> ` (Compose, then minus, then greater-than). You should get: →

If it works, you're ready to use xcompose-stem!

---

## Contributing

Contributions are welcome. This is actively maintained for personal use, so changes should:
- Pass validation (`./tools/validate_xcompose.py`)
- Follow existing design patterns (see [CLAUDE.md](CLAUDE.md))
- Include documentation updates

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Uninstalling

**Automated:**
```bash
cd ~/.xcompose-stem
./uninstall.sh
```

**Manual:**
Edit `~/.XCompose` and remove the `include` line referencing xcompose-stem. Restart your X session.

---

## License

MIT License - See [LICENSE](LICENSE)

Free to use, modify, and redistribute.

---

## Acknowledgments

**Author:** Phil Bowens
**Built with:** Claude Code (Anthropic AI), Grok (xAI), ChatGPT (OpenAI)
**Inspired by:** LaTeX notation, Vim digraphs, standard XCompose conventions, Unicode standards

---

**Development:** See [CLAUDE.md](CLAUDE.md) for architecture and design decisions.
