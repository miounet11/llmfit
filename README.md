# LLMFit

<p align="center">
  <img src="assets/icon.svg" alt="LLMFit icon" width="128" height="128">
</p>

<p align="center">
  <a href="https://github.com/miounet11/llmfit/actions/workflows/ci.yml"><img src="https://github.com/miounet11/llmfit/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/miounet11/llmfit/releases"><img src="https://img.shields.io/github/v/release/miounet11/llmfit" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

**Choose the right open model for your hardware before you waste time downloading the wrong one.**

LLMFit is a hardware-aware model selection tool for local AI builders, platform
teams, consultants, and homelab operators. It inspects CPU, RAM, GPU, VRAM, and
local runtimes, then recommends the best-fitting models, quantizations, and run
paths for your machine.

This repository packages the original `AlexsJones/llmfit` engine as a more
complete open-source product: sharper messaging, cleaner install flow, deployable
site assets, local stack orchestration, and repo hygiene that makes the project
easier to adopt and operate.

![demo](demo.gif)

## Who this is for

- Builders shipping local AI apps on laptops, workstations, and edge servers
- Platform and MLOps teams standardizing which models can run on which nodes
- Consultants who need fast answers on "what model fits this box?"
- Power users running Ollama, llama.cpp, MLX, or Docker Model Runner locally

## Why users pick LLMFit

- **Hardware-aware recommendations**: stop guessing whether a 7B, 14B, 32B, or MoE model will actually fit.
- **TUI, CLI, and API**: use the tool interactively or script it into schedulers, agents, and setup flows.
- **Provider-aware results**: compare model options across Ollama, GGUF, MLX, and Docker runtimes.
- **Planning mode**: invert the workflow and ask what hardware is needed for a model and latency target.
- **Low-friction deployment**: run the binary locally, ship the API in a container, and deploy the product site independently.

## Product direction

The packaging of this fork takes cues from high-adoption open-source products:

- the install simplicity and distribution mindset of [Ollama](https://github.com/ollama/ollama)
- the release quality and tool-first polish seen in [uv](https://github.com/astral-sh/uv)
- the self-hosted product presentation popularized by [Open WebUI](https://github.com/open-webui/open-webui)

## Install

### Quick install

```sh
curl -fsSL https://raw.githubusercontent.com/miounet11/llmfit/main/install.sh | sh
```

Install to `~/.local/bin` without sudo:

```sh
curl -fsSL https://raw.githubusercontent.com/miounet11/llmfit/main/install.sh | sh -s -- --local
```

### From source

```sh
git clone https://github.com/miounet11/llmfit.git
cd llmfit
cargo build --release
./target/release/llmfit
```

### Docker

```sh
docker run --rm ghcr.io/miounet11/llmfit recommend --json --limit 5
```

### Full local stack

```sh
docker compose up --build
```

- API: `http://127.0.0.1:8787`
- Site: `http://127.0.0.1:8080`

## Fast start

```sh
# launch the TUI
llmfit

# top recommendations for coding
llmfit recommend --json --use-case coding --limit 3

# inspect detected hardware
llmfit system

# plan required hardware for a specific model
llmfit plan "Qwen/Qwen3-4B-MLX-4bit" --context 8192 --target-tps 25

# run the node-local REST API
llmfit serve --host 0.0.0.0 --port 8787
```

## What ships in this repo

- `llmfit-core/`: scoring, hardware detection, model catalogs, plan estimation
- `llmfit-tui/`: terminal UI, classic CLI, and REST API
- `llmfit-desktop/`: desktop wrapper for macOS users
- `site/`: static marketing and docs site ready for independent deployment
- `deploy/`: isolated Nginx and Compose assets for low-risk site rollout

## Typical workflows

### 1. Pick the best model for a laptop or workstation

Open the TUI, filter by use case, compare candidates, and download a runnable
model from the runtime that already exists on the machine.

### 2. Standardize a team baseline

Run `llmfit recommend --json` or `llmfit serve` across nodes and feed the output
into a scheduler, inventory system, or setup script.

### 3. Plan an upgrade before buying hardware

Use `llmfit plan` or TUI Plan mode to estimate the RAM, VRAM, and CPU needed to
hit a target model and latency range.

## Site and deployment

The repository includes a dedicated static product site under `site/` and a safe
deployment recipe that keeps the site isolated from existing services by default.

- Local preview: `make site-preview`
- Generate 4 new safe programmatic-content pages: `make generate-content`
- Build/publish generated content with an external manifest/docroot: `make publish-content`
- Smoke-test the drafting endpoint: `make check-content-llm`
- Force one publish cycle now: `make publish-content-now DATE=2026-03-17`
- Pull latest code, then publish now: `make refresh-publish-content DATE=2026-03-17`
- Local stack: `make stack-up`
- Remote deployment helper: `scripts/deploy-site.sh user@host /opt/llmfit`
- Production deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Programmatic content engine

The site now supports a bilingual content engine for search-oriented pages that
stay inside the product theme:

- Topic pool: local AI model fit, hardware sizing, runtime choice, and deployment planning
- Output: English + Simplified Chinese pages under `/insights/` and `/zh/insights/`
- Guardrails: no scraping, no copied docs, no medical/legal/financial content, no fake benchmark claims
- Source data: the bundled Hugging Face model catalog already embedded in this repo
- Drafting mode: deterministic by default, with optional OpenAI-compatible LLM drafting through environment variables

Useful env vars:

```sh
export LLMFIT_CONTENT_LLM_ENDPOINT="https://example.com/v1"
export LLMFIT_CONTENT_LLM_API_KEY="..."
export LLMFIT_CONTENT_LLM_MODEL="auto"
export LLMFIT_CONTENT_LLM_TIMEOUT="60"
export LLMFIT_CONTENT_LLM_RETRIES="2"
export LLMFIT_CONTENT_LLM_RETRY_DELAY_SECONDS="3"
export LLMFIT_CONTENT_ALLOW_STALE_REPO="1"
export LLMFIT_CONTENT_DOCROOT="/www/wwwroot/www.igeminicli.cn_static"
export LLMFIT_CONTENT_STATE_FILE="/opt/llmfit-publisher/state/content-manifest.json"
export LLMFIT_CONTENT_RUN_REPORT_FILE="/opt/llmfit-publisher/build/last-run.json"
```

`LLMFIT_CONTENT_LLM_ENDPOINT` accepts either a base OpenAI-compatible API URL
such as `https://example.com/v1` or the full chat completions path. The
publisher normalizes it automatically.

## API and data references

- REST API details: [API.md](API.md)
- Model catalog notes: [MODELS.md](MODELS.md)

## Attribution

This project is based on the original MIT-licensed work by Alex Jones. See
[NOTICE](NOTICE) for the packaging and attribution note for this fork.

## License

MIT. See [LICENSE](LICENSE).
