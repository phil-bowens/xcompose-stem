#!/bin/bash
set -e

################################################################################
# XCompose-STEM uninstaller
# Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals
#
# Copyright (c) 2025 Phil Bowens
# Repository: https://github.com/phil-bowens/xcompose-stem
# License: MIT
################################################################################
#
# This script removes XCompose-STEM from your ~/.XCompose, restoring your
# original configuration.

XCOMPOSE_FILE="$HOME/.XCompose"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== XCompose-STEM uninstaller ===${NC}\n"

# Check if XCompose file exists
if [ ! -f "$XCOMPOSE_FILE" ]; then
    echo -e "${YELLOW}No ~/.XCompose file found.${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

# Check if XCompose-STEM is installed (look for the actual include line)
if ! grep -q "include.*xcompose-stem.*XCompose" "$XCOMPOSE_FILE" 2>/dev/null; then
    echo -e "${YELLOW}XCompose-STEM is not installed in ~/.XCompose${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

# Find the most recent pre-installation backup
INSTALL_BACKUP=$(ls -t "$HOME"/.XCompose.backup.* 2>/dev/null | head -1)

if [ -n "$INSTALL_BACKUP" ]; then
    echo -e "${YELLOW}Found backup from installation:${NC} $(basename "$INSTALL_BACKUP")"
    echo ""
    read -p "Restore from this backup? (Y/n): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # Restore from backup
        cp "$INSTALL_BACKUP" "$XCOMPOSE_FILE"
        echo -e "${GREEN}✓ Restored from backup!${NC}"
        echo "Your original ~/.XCompose has been restored."
    else
        # Manual removal
        UNINSTALL_BACKUP="$HOME/.XCompose.backup.uninstall.$(date +%Y%m%d_%H%M%S)"
        echo -e "Creating backup: ${UNINSTALL_BACKUP}"
        cp "$XCOMPOSE_FILE" "$UNINSTALL_BACKUP"

        # Remove XCompose-STEM lines
        echo "Removing XCompose-STEM from ~/.XCompose..."
        sed -i '/^# XCompose-STEM - STEM symbols for technical writing$/d' "$XCOMPOSE_FILE"
        sed -i '\|^# https://github.com/phil-bowens/xcompose-stem$|d' "$XCOMPOSE_FILE"
        sed -i '\|^include.*xcompose-stem.*XCompose"$|d' "$XCOMPOSE_FILE"
        sed -i '/^$/N;/^\n$/D' "$XCOMPOSE_FILE"

        echo -e "${GREEN}✓ Removed XCompose-STEM lines${NC}"
        echo -e "Backup saved: ${UNINSTALL_BACKUP}"
    fi
else
    # No backup found - do manual removal
    echo -e "${YELLOW}No installation backup found.${NC}"
    UNINSTALL_BACKUP="$HOME/.XCompose.backup.uninstall.$(date +%Y%m%d_%H%M%S)"
    echo -e "Creating backup: ${UNINSTALL_BACKUP}"
    cp "$XCOMPOSE_FILE" "$UNINSTALL_BACKUP"

    # Remove XCompose-STEM lines
    echo "Removing XCompose-STEM from ~/.XCompose..."
    sed -i '/^# XCompose-STEM - STEM symbols for technical writing$/d' "$XCOMPOSE_FILE"
    sed -i '\|^# https://github.com/phil-bowens/xcompose-stem$|d' "$XCOMPOSE_FILE"
    sed -i '\|^include.*xcompose-stem.*XCompose"$|d' "$XCOMPOSE_FILE"
    sed -i '/^$/N;/^\n$/D' "$XCOMPOSE_FILE"

    echo -e "${GREEN}✓ Removed XCompose-STEM lines${NC}"
    echo -e "Backup saved: ${UNINSTALL_BACKUP}"
fi

echo ""
echo -e "${GREEN}✓ Uninstallation complete!${NC}"
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
echo "Your previous Compose sequences should still work."
echo ""
if [ -n "$INSTALL_BACKUP" ]; then
    echo -e "${YELLOW}Note:${NC} If needed, you can find backups in your home directory:"
    echo "  ls -lt ~/.XCompose.backup.*"
fi
echo ""
