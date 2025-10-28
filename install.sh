#!/bin/bash
set -e

################################################################################
# XCompose-STEM installer
# Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals
#
# Copyright (c) 2025 Phil Bowens
# Repository: https://github.com/phil-bowens/xcompose-stem
# License: MIT
################################################################################
#
# This script adds xcompose-stem to your ~/.XCompose using an include
# directive, preserving any existing configuration.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
XCOMPOSE_FILE="$HOME/.XCompose"
BACKUP_FILE="$HOME/.XCompose.backup.$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== XCompose-STEM installer ===${NC}\n"

# Check if XCompose file exists
if [ -f "$XCOMPOSE_FILE" ]; then
    echo -e "${YELLOW}Found existing ~/.XCompose${NC}"

    # Check if already installed (look for the actual include line)
    if grep -q "include.*xcompose-stem.*XCompose" "$XCOMPOSE_FILE" 2>/dev/null; then
        echo -e "${GREEN}✓ XCompose-STEM is already installed!${NC}"
        echo ""
        echo "Your ~/.XCompose already includes XCompose-STEM."
        echo "No changes needed."
        exit 0
    fi

    # Backup existing file
    echo -e "Creating backup: ${BACKUP_FILE}"
    cp "$XCOMPOSE_FILE" "$BACKUP_FILE"

    # Append include directive
    echo ""
    echo "Adding xcompose-stem include directive..."
    echo "" >> "$XCOMPOSE_FILE"
    echo "# XCompose-STEM - STEM symbols for technical writing" >> "$XCOMPOSE_FILE"
    echo "# https://github.com/phil-bowens/xcompose-stem" >> "$XCOMPOSE_FILE"
    echo "include \"$SCRIPT_DIR/XCompose\"" >> "$XCOMPOSE_FILE"

    echo -e "${GREEN}✓ Installation complete!${NC}"
    echo ""
    echo "XCompose-STEM has been added to your existing ~/.XCompose"
    echo -e "Backup saved: ${BACKUP_FILE}"
else
    # Create new .XCompose file
    echo "No ~/.XCompose found. Creating new file..."

    cat > "$XCOMPOSE_FILE" << EOF
# XCompose configuration
# This file defines custom Compose key sequences

# Include system defaults first
include "%L"

# xcompose-stem - STEM symbols for technical writing
# https://github.com/phil-bowens/xcompose-stem
include "$SCRIPT_DIR/XCompose"
EOF

    echo -e "${GREEN}✓ Installation complete!${NC}"
    echo ""
    echo "Created new ~/.XCompose with XCompose-STEM included"
fi

# Omarchy Linux integration
HYPR_BINDINGS="$HOME/.config/hypr/bindings.conf"
if [ -f "$HYPR_BINDINGS" ]; then
    echo ""
    echo -e "${BLUE}Omarchy Linux detected!${NC}"

    # Check if keybinding already exists
    if grep -q "xcompose-stem/docs/xcompose_reference.html" "$HYPR_BINDINGS" 2>/dev/null || \
       grep -q "xcompose_reference.html.*Unicode" "$HYPR_BINDINGS" 2>/dev/null; then
        echo -e "${GREEN}✓ Symbol reference keybinding already configured${NC}"
    else
        echo ""
        echo "Would you like to add a keybinding for quick access to the symbol reference?"
        echo -e "${YELLOW}Keybinding: Super + Shift + U${NC} → Opens symbol reference in webapp"
        echo ""
        read -p "Add keybinding? (y/N): " -n 1 -r
        echo ""

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Backup bindings.conf
            BINDINGS_BACKUP="$HOME/.config/hypr/bindings.conf.backup.$(date +%Y%m%d_%H%M%S)"
            cp "$HYPR_BINDINGS" "$BINDINGS_BACKUP"

            # Add keybinding
            echo "" >> "$HYPR_BINDINGS"
            echo "# XCompose-STEM - Quick access to symbol reference" >> "$HYPR_BINDINGS"
            echo "bindd = SUPER SHIFT, U, Unicode Codepoints, exec, omarchy-launch-webapp \"file://$SCRIPT_DIR/docs/xcompose_reference.html\"" >> "$HYPR_BINDINGS"

            echo -e "${GREEN}✓ Keybinding added to $HYPR_BINDINGS${NC}"
            echo -e "Backup saved: ${BINDINGS_BACKUP}"
            echo ""
            echo -e "${YELLOW}Note:${NC} Reload Hyprland config with Super + Shift + C (or restart Hyprland)"
        else
            echo "Skipped. You can add it manually later (see README.md)"
        fi
    fi
fi

echo ""
echo -e "${BLUE}Reloading XCompose...${NC}"

# Auto-restart on Omarchy if available
if command -v omarchy-restart-xcompose &> /dev/null; then
    echo "Omarchy detected, restarting XCompose..."
    omarchy-restart-xcompose
    echo -e "${GREEN}✓ XCompose reloaded!${NC}"
else
    echo -e "${YELLOW}Manual reload required:${NC}"
    echo "   - GNOME/KDE: Log out and back in"
    echo "   - Or: killall ibus-daemon && ibus-daemon -drx"
fi

echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test it: Compose + -> should produce →"
echo "2. Browse all sequences: open docs/xcompose_reference.html"
echo ""
echo -e "${YELLOW}Note:${NC} Make sure your Compose key is configured"
echo "Run: gsettings set org.gnome.desktop.input-sources xkb-options \"['compose:ralt']\""
echo ""
