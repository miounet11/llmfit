# Makefile for llmfit
# Convenience commands for building, testing, previewing the site, and running the local stack.

.PHONY: help build release clean run test update-models update-docker-models update-catalogs check fmt clippy install site-preview generate-content publish-content check-content-llm publish-content-now refresh-publish-content stack-up stack-down

# Default target
help:
	@echo "llmfit - hardware-aware model selection for local AI"
	@echo ""
	@echo "Available targets:"
	@echo "  make build          - Build debug binary"
	@echo "  make release        - Build release binary"
	@echo "  make run            - Run in TUI mode (debug)"
	@echo "  make test           - Run all unit tests"
	@echo "  make site-preview   - Preview the static marketing/docs site at http://127.0.0.1:4173"
	@echo "  make generate-content - Publish 4 new programmatic SEO pages into site/"
	@echo "  make publish-content  - Build generated pages into a staging dir and optionally rsync to \$LLMFIT_CONTENT_DOCROOT"
	@echo "  make check-content-llm - Smoke-test the OpenAI-compatible drafting endpoint"
	@echo "  make publish-content-now - Run one publish cycle for DATE=\$(date +%F) without git refresh"
	@echo "  make refresh-publish-content - Pull latest main, then run one publish cycle for DATE=\$(date +%F)"
	@echo "  make stack-up       - Run the local API + web site stack with Docker Compose"
	@echo "  make stack-down     - Stop the local API + web site stack"
	@echo "  make update-models  - Fetch latest model data from HuggingFace"
	@echo "  make update-docker-models - Refresh Docker Model Runner catalog"
	@echo "  make update-catalogs - Refresh all catalogs (HF models + Docker) and rebuild"
	@echo "  make check          - Run cargo check"
	@echo "  make fmt            - Format code with rustfmt"
	@echo "  make clippy         - Run clippy linter"
	@echo "  make clean          - Remove build artifacts"
	@echo "  make install        - Install release binary to ~/.cargo/bin"
	@echo ""

# Build debug version
build:
	cargo build

# Build release version
release:
	cargo build --release

# Clean build artifacts
clean:
	cargo clean

# Run in TUI mode
run:
	cargo run

# Run tests
test:
	cargo test

# Update model database from HuggingFace
update-models:
	@./scripts/update_models.sh

# Refresh Docker Model Runner catalog from Docker Hub
update-docker-models:
	python3 scripts/scrape_docker_models.py

# Refresh all catalogs (HF models + Docker) and rebuild
# Runs HF scraper first (via update_models.sh which also rebuilds),
# then Docker scraper (which depends on hf_models.json), then rebuilds again
# to embed the updated Docker catalog.
update-catalogs:
	@./scripts/update_models.sh
	python3 scripts/scrape_docker_models.py
	cargo build --release

# Check compilation without building
check:
	cargo check

# Format code
fmt:
	cargo fmt

# Run clippy
clippy:
	cargo clippy -- -D warnings

# Install to ~/.cargo/bin
install:
	cargo install --path .

# Preview the static site locally
site-preview:
	python3 -m http.server 4173 --directory site

# Generate 4 new content pages inside site/
generate-content:
	python3 scripts/generate_site_content.py --count $${COUNT:-4}

# Build generated pages in a staging dir and optionally publish them
publish-content:
	bash scripts/publish_site_content.sh

# Smoke-test the OpenAI-compatible content endpoint
check-content-llm:
	python3 scripts/check_content_llm.py

# Force a same-day publish run without refreshing git
publish-content-now:
	bash scripts/publish_site_content.sh $${DATE:-$$(date +%F)}

# Pull latest code, then force a same-day publish run
refresh-publish-content:
	bash scripts/refresh_and_publish_site.sh $${DATE:-$$(date +%F)}

# Run the local stack
stack-up:
	docker compose up --build

# Stop the local stack
stack-down:
	docker compose down
