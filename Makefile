# Root Makefile for the research-kit Claude Code plugin.
#
# The plugin ships from plugin/; the repo root is its marketplace.

PLUGIN := plugin

.PHONY: all help deps lint format test network validate manifest check clean

all: help

help:
	@echo "========================================================="
	@echo " research-kit - Root Makefile"
	@echo "========================================================="
	@echo "Available commands:"
	@echo "  make deps      - check dependencies; pip-install ruff and pymupdf if missing"
	@echo "  make lint      - ruff check + ruff format --check, version check"
	@echo "  make format    - ruff format, then re-sync pdf_tools.py into the skills"
	@echo "  make test      - offline checks (tests/test_plugin.py)"
	@echo "  make network   - offline checks plus live Crossref checks"
	@echo "  make validate  - claude plugin validate on the plugin and the marketplace"
	@echo "  make manifest  - fail if plugin.json and marketplace.json versions differ"
	@echo "  make check     - lint, test and validate"
	@echo "  make clean     - remove __pycache__ and .ruff_cache"
	@echo "========================================================="

deps:
	@command -v ruff >/dev/null || python3 -m pip install ruff
	@python3 -c 'import pymupdf' 2>/dev/null || python3 -m pip install pymupdf
	@command -v claude >/dev/null || echo "claude not found (needed for make validate)"
	@echo "deps OK: $$(ruff --version), pymupdf $$(python3 -c 'import pymupdf; print(pymupdf.VersionBind)')"

lint: manifest
	@command -v ruff >/dev/null || { echo "ruff not found; install with: pip install ruff"; exit 1; }
	ruff check .
	ruff format --check .
	@echo "lint OK"

# The sync hook fires only on Write/Edit, so a Bash-run format leaves the
# skills' copies of pdf_tools.py stale; copy the master over them.
format:
	ruff format .
	@for d in $(PLUGIN)/skills/*/scripts; do \
		[ -f $$d/pdf_tools.py ] && cp scripts/pdf_tools.py $$d/pdf_tools.py; \
	done; true
	@echo "pdf_tools.py re-synced into the skills"

test:
	python3 tests/test_plugin.py

network:
	RESEARCH_KIT_NETWORK=1 python3 tests/test_plugin.py

validate:
	claude plugin validate ./$(PLUGIN)
	claude plugin validate .

manifest:
	@python3 -c 'import json, sys; \
		p = json.load(open("$(PLUGIN)/.claude-plugin/plugin.json"))["version"]; \
		m = json.load(open(".claude-plugin/marketplace.json"))["metadata"]["version"]; \
		sys.exit(0) if p == m else sys.exit(f"version mismatch: plugin.json {p}, marketplace.json {m}")'

check: lint test validate

clean:
	rm -rf .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
