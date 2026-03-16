# Makefile for llmfit
# Convenience commands for building, testing, previewing the site, and running the local stack.

.PHONY: help build release clean run test update-models update-docker-models update-catalogs check fmt clippy install site-preview stack-up stack-down

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

# Run the local stack
stack-up:
	docker compose up --build

# Stop the local stack
stack-down:
	docker compose down
