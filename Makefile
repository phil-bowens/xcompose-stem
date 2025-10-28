################################################################################
# Makefile for XCompose-STEM
# Part of XCompose-STEM - Easy Unicode Symbols on Linux for STEM Professionals
#
# Copyright (c) 2025 Phil Bowens
# Repository: https://github.com/phil-bowens/xcompose-stem
# License: MIT
################################################################################
#
# Common development tasks and CI targets.
#
# Quick start:
#   make help      - Show all available targets
#   make all       - Run validation, audit, and generate docs
#   make validate  - Check XCompose for errors (required before commit)
#   make docs      - Regenerate documentation
#
# Development workflow:
#   1. Edit XCompose
#   2. make validate (required)
#   3. make audit (recommended)
#   4. make docs
#   5. git commit XCompose docs/
#
################################################################################

.PHONY: help validate audit docs all clean test install uninstall check-defaults comparison-table

# Configuration
XCOMPOSE_FILE := XCompose
PYTHON := python3
VALIDATOR := tools/validate_xcompose.py
AUDITOR := tools/audit_xcompose_design.py
GENERATOR := tools/generate_xcompose_docs.py
CHECKER := tools/check_system_defaults.py
DOCS_DIR := docs

help:  ## Show this help message
	@echo "XCompose-STEM - Makefile targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Development workflow:"
	@echo "  1. Edit XCompose"
	@echo "  2. make validate (required)"
	@echo "  3. make audit (recommended)"
	@echo "  4. make docs"
	@echo "  5. git commit XCompose docs/"

validate:  ## Validate XCompose file for conflicts and errors
	@echo "==> Validating XCompose configuration..."
	@$(PYTHON) $(VALIDATOR) $(XCOMPOSE_FILE)

audit:  ## Run design quality audit
	@echo "==> Running design audit..."
	@$(PYTHON) $(AUDITOR) $(XCOMPOSE_FILE)

check-defaults:  ## Compare against system defaults (informational)
	@echo "==> Comparing against system defaults..."
	@$(PYTHON) $(CHECKER) $(XCOMPOSE_FILE)

comparison-table:  ## Generate comparison table (saves to docs/xcompose_comparison.md)
	@echo "==> Generating comparison table..."
	@$(PYTHON) $(CHECKER) $(XCOMPOSE_FILE) --table --output $(DOCS_DIR)/xcompose_comparison.md

docs:  ## Generate all documentation (HTML, JSON, Markdown, checklist)
	@echo "==> Generating documentation..."
	@$(PYTHON) $(GENERATOR) $(XCOMPOSE_FILE) --all

all: validate audit docs  ## Run validation, audit, and generate docs

test: validate  ## Run tests (for CI) - validate and audit
	@echo "==> Running design audit (warnings allowed)..."
	@$(PYTHON) $(AUDITOR) $(XCOMPOSE_FILE) || true

clean:  ## Remove generated documentation files
	@echo "==> Cleaning generated files..."
	@rm -f $(DOCS_DIR)/xcompose_reference.html
	@rm -f $(DOCS_DIR)/xcompose_table.md
	@rm -f $(DOCS_DIR)/xcompose_sequences.json
	@rm -f $(DOCS_DIR)/xcompose_checklist.md
	@echo "Cleaned $(DOCS_DIR)/"

install:  ## Run the installation script
	@./install.sh

uninstall:  ## Run the uninstallation script
	@./uninstall.sh

# Development helpers
.PHONY: check-docs
check-docs:  ## Check if documentation is up to date (for CI)
	@echo "==> Checking if documentation is current..."
	@$(PYTHON) $(GENERATOR) $(XCOMPOSE_FILE) --all
	@if git diff --quiet $(DOCS_DIR)/; then \
		echo "✓ Documentation is up to date"; \
	else \
		echo "✗ Documentation is out of date!"; \
		echo "  Run: make docs"; \
		echo "  Then commit the updated docs/"; \
		exit 1; \
	fi

.PHONY: stats
stats:  ## Show XCompose statistics
	@$(PYTHON) $(GENERATOR) $(XCOMPOSE_FILE) --stats

.PHONY: watch
watch:  ## Watch XCompose file and auto-regenerate docs (requires entr)
	@echo "Watching $(XCOMPOSE_FILE) for changes..."
	@echo "Press Ctrl+C to stop"
	@echo $(XCOMPOSE_FILE) | entr -c make docs

.PHONY: list-locales
list-locales:  ## List all available system Compose files
	@$(PYTHON) $(CHECKER) --list-locales
