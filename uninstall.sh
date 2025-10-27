#!/bin/bash
set -e

################################################################################
# xcompose-stem uninstaller
# Part of xcompose-stem - Keyboard shortcuts for STEM symbols on Linux
#
# Copyright (c) 2025 Phil Bowens
# Repository: https://github.com/phil-bowens/xcompose-stem
# License: MIT
################################################################################
#
# This script removes xcompose-stem from your ~/.XCompose, restoring your
# original configuration.

XCOMPOSE_FILE="$HOME/.XCompose"
BACKUP_FILE="$HOME/.XCompose.backup.$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== xcompose-stem uninstaller ===${NC}\n"

# Check if XCompose file exists
if [ ! -f "$XCOMPOSE_FILE" ]; then
    echo -e "${YELLOW}No ~/.XCompose file found.${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

# Check if xcompose-stem is installed (look for the actual include line)
if ! grep -q "include.*xcompose-stem.*XCompose" "$XCOMPOSE_FILE" 2>/dev/null; then
    echo -e "${YELLOW}xcompose-stem is not installed in ~/.XCompose${NC}"
    echo "Nothing to uninstall."
    exit 0
fi

# Backup existing file
echo -e "Creating backup: ${BACKUP_FILE}"
cp "$XCOMPOSE_FILE" "$BACKUP_FILE"

# Remove xcompose-stem lines (only the include and related comments)
echo "Removing xcompose-stem from ~/.XCompose..."
# Remove the comment line above the include
sed -i '/^# xcompose-stem - STEM symbols for technical writing$/d' "$XCOMPOSE_FILE"
# Remove the GitHub URL comment
sed -i '\|^# https://github.com/phil-bowens/xcompose-stem$|d' "$XCOMPOSE_FILE"
# Remove the actual include line
sed -i '\|^include.*xcompose-stem.*XCompose"$|d' "$XCOMPOSE_FILE"

# Remove excess empty lines that might have been left behind
sed -i '/^$/N;/^\n$/D' "$XCOMPOSE_FILE"

echo -e "${GREEN}✓ Uninstallation complete!${NC}"
echo ""
echo "xcompose-stem has been removed from ~/.XCompose"
echo -e "Backup saved: ${BACKUP_FILE}"
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
echo -e "${YELLOW}Note:${NC} You can restore your previous config with:"
echo "  cp $BACKUP_FILE ~/.XCompose"
echo ""
