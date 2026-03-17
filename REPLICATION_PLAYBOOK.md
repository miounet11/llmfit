# LLMFit Replication Playbook

This document explains the full process used to turn the original
`AlexsJones/llmfit` codebase into a complete, user-facing open-source product:
repo packaging, positioning, website creation, production deployment,
multilingual expansion, programmatic content generation, and automated daily
publishing.

It is written as a reusable blueprint so the same process can be repeated for
future projects with less trial and error.

## 1. Executive Summary

The project started from a solid technical engine, but not a complete product.
The work completed here converted it into four things at once:

1. A productized open-source repository with clear positioning and install flow.
2. A professional static website with docs, marketing pages, and bilingual UX.
3. A search-oriented content system that stays aligned with the product theme.
4. A production publishing pipeline that can update the site daily without
   breaking the repo or the existing server.

Final public result:

- Canonical site: `https://www.igeminicli.cn`
- Preferred host: `https://www.igeminicli.cn`
- Apex redirect: `https://igeminicli.cn` -> `https://www.igeminicli.cn`
- Content hubs:
  - `/insights/`
  - `/zh/insights/`
  - `/feed.xml`
  - `/zh/feed.xml`

## 2. What Was Built

### Product layer

- Repositioned the project as a hardware-aware local AI model selection tool.
- Defined a clearer target audience:
  - local AI builders
  - platform teams
  - consultants
  - homelab operators
- Rewrote the value proposition around fit, deployment realism, and operator
  usefulness.
- Improved open-source packaging:
  - clearer README
  - installation flow
  - deployment docs
  - site deployment helpers

### Website layer

- Built a static product site under `site/`.
- Expanded the site into a full docs and product property instead of a single
  landing page.
- Added pages for:
  - home
  - docs
  - use cases
  - API
  - self-host
  - compare
  - FAQ
  - insights/content hub
- Added multilingual support:
  - English under `/`
  - Simplified Chinese under `/zh/`

### Content layer

- Added a bilingual programmatic content engine.
- Generated pages around:
  - hardware fit
  - model family deployment
  - runtime planning
  - local AI deployment decisions
- Added internal linking improvements:
  - taxonomy/category pages
  - related article blocks
  - RSS discovery links
  - sitemap coverage

### Operations layer

- Added a build-and-publish pipeline that can generate content into a staging
  tree instead of mutating the tracked repo directly on the server.
- Added daily cron publishing.
- Kept publish state outside the repo to avoid dirty worktrees.
- Deployed safely onto an existing multi-site server without interrupting
  unrelated sites.

## 3. High-Level Transformation Path

The transformation followed this sequence:

1. Start from the original engine.
2. Rebrand and reposition it as a complete product.
3. Package the repository for public adoption.
4. Create a production-quality static website.
5. Deploy the website in a low-risk way.
6. Add multilingual support.
7. Add thematic content generation.
8. Add daily automated publishing.
9. Upgrade the content hub structure to improve crawlability and internal
   navigation.

This order matters. The site should not be scaled with automated content before
the product message, deployment shape, and editorial guardrails are stable.

## 4. Key Milestones in This Repo

Recent implementation milestones:

- `102b7ee` `Launch productized llmfit fork`
- `73fed18` `Add remote site deployment helper`
- `2382d16` `Polish marketing site metadata`
- `a218785` `Expand site into professional docs property`
- `abaa681` `Add bilingual site experience`
- `42a370c` `Add programmatic content engine`
- `dad0b96` `Upgrade insights hub structure`

These commits are the practical evolution path for this project. For future
projects, they can be treated as milestone categories even if the commit hashes
change.

## 5. Repository Areas That Matter

### Core product

- `llmfit-core/`: scoring, hardware detection, planning logic, embedded data
- `llmfit-tui/`: CLI, TUI, local API service
- `llmfit-desktop/`: desktop wrapper

### Website and docs

- `site/`: public static site
- `site/zh/`: Chinese mirror of the public site
- `site/insights/`: generated English content pages
- `site/zh/insights/`: generated Chinese content pages

### Deployment and operations

- `deploy/site.compose.yml`: isolated static-site container deployment
- `deploy/site.nginx.conf`: Nginx config for the isolated container
- `scripts/deploy-site.sh`: remote helper for containerized site rollout
- `scripts/publish_site_content.sh`: build + optional publish
- `scripts/refresh_and_publish_site.sh`: git refresh + publish
- `scripts/generate_site_content.py`: bilingual content generator
- `docs/DEPLOYMENT.md`: deployment guide
- `Makefile`: local operator shortcuts

## 6. Productization Workstream

The original reference project was technically useful, but not packaged like a
complete product. The productization work added:

- stronger message hierarchy
- clearer audience definition
- consistent branding
- install and deployment instructions
- site/demo assets
- safer deployment helpers
- better repo ergonomics

The important principle was this:

> The engine remained the foundation, but the repository was upgraded to behave
> like a product that a stranger could discover, understand, install, trust,
> and deploy.

For future replications, do not start with “how to make it prettier.” Start
with:

1. Who is the user?
2. What pain is being removed?
3. Why is this project better than guessing manually?
4. What must a new visitor understand within 10 seconds?

## 7. Website Build Strategy

The site was intentionally built as a static property instead of a dynamic app.

Reasons:

- low operational risk
- easy rollback
- easy rsync-based deployment
- cheap hosting
- no database requirement
- safer on an already crowded server
- fast SEO iteration

The design direction was not “generic SaaS landing page.” It was positioned as
a practical operator-facing product:

- strong typography
- warm editorial palette
- docs-ready structure
- simple deployment footprint
- product content plus education content in the same property

## 8. Multilingual Strategy

The multilingual approach is path-based:

- English root content at `/`
- Chinese content at `/zh/`

This approach was chosen because it is:

- easy to deploy statically
- easy to mirror
- easy to add hreflang tags to
- easy to manage in sitemap generation

What was added:

- mirrored navigation
- alternate language links
- bilingual SEO tags
- bilingual insights pages
- bilingual feeds

One bug found during the upgrade was that generated Chinese insight pages linked
home to `/zh` instead of `/zh/`. That was fixed in the generator so future
pages use the correct canonical Chinese home path.

## 9. Content System Strategy

The content system was not designed as a spam farm. It was designed as a
controlled editorial expansion layer around the core product.

### Allowed topic zones

- local AI model fit
- RAM and VRAM sizing
- runtime selection
- model family deployment planning
- realistic local inference decisions

### Explicitly avoided

- medical content
- legal content
- financial advice
- political topics
- adult content
- gambling
- deceptive pages
- fake benchmark claims
- copied documentation
- scraped article rewrites

### Why this matters

A content engine can create traffic, but if it drifts outside the product
boundary it damages both trust and maintainability. The content must strengthen
the product, not dilute it.

## 10. Content Engine Architecture

The main generator is `scripts/generate_site_content.py`.

It does the following:

1. Loads the embedded model catalog from `llmfit-core/data/hf_models.json`.
2. Builds a controlled topic pool.
3. Checks the manifest of already published articles.
4. Selects a small daily batch of unpublished topics.
5. Builds English and Chinese pages for each topic.
6. Updates feeds and sitemap.
7. Writes output into the target site tree.

### Topic classes currently supported

- `hardware`
- `family`
- `runtime`

### Output structure

- article pages under `/insights/<slug>/`
- Chinese mirrors under `/zh/insights/<slug>/`
- category pages:
  - `/insights/hardware/`
  - `/insights/families/`
  - `/insights/runtimes/`
  - `/zh/insights/hardware/`
  - `/zh/insights/families/`
  - `/zh/insights/runtimes/`
- RSS feeds:
  - `/feed.xml`
  - `/zh/feed.xml`
- sitemap:
  - `/sitemap.xml`

### Drafting modes

The generator supports two content modes:

1. Deterministic fallback copy.
2. Optional OpenAI-compatible LLM drafting.

The fallback mode is important. It means the system still publishes useful,
safe, on-theme pages even if the external LLM endpoint is slow, unavailable, or
returns invalid JSON.

## 11. Content Hub Upgrade

The first content version created individual pages and feeds. The next upgrade
made the property more professional and crawlable.

Added in the hub upgrade:

- category landing pages
- related article blocks
- feed discovery in generated pages
- stronger internal linking
- better crawl paths
- refreshed existing article pages to join the new structure

This was a meaningful jump in quality. It changed the content system from “a
set of generated pages” into “a structured content property.”

## 12. Publishing Pipeline

The publishing pipeline was designed so that daily generation would not pollute
the repo clone on the production server.

### Scripts

- `scripts/publish_site_content.sh`
- `scripts/refresh_and_publish_site.sh`
- `scripts/check_content_llm.py`

### Publishing model

1. Keep a clean repo clone on the server.
2. Keep state outside the repo.
3. Build generated output in a separate staging directory.
4. Rsync the finished result into the live static docroot.

### Why this design was chosen

- avoids dirty git worktrees
- makes `git pull --ff-only` safe
- isolates state from tracked files
- allows clean rollback using docroot backups
- reduces accidental breakage during cron runs
- makes it possible to keep JSON run reports for each publish cycle

## 13. Current Production Layout

The current production deployment uses an existing Nginx-based multi-site host.
Sensitive details such as credentials are intentionally not recorded here.

### Public routing

- Public domain: `www.igeminicli.cn`
- Apex redirect: `igeminicli.cn` -> `www.igeminicli.cn`

### Live static site location

- Static docroot: `/www/wwwroot/www.igeminicli.cn_static`

### Live Nginx vhost file

- `/www/server/panel/vhost/nginx/www.igeminicli.cn.conf`

The live vhost currently:

- redirects HTTP to HTTPS on the `www` host
- redirects apex traffic to `https://www.igeminicli.cn`
- serves the static site from `/www/wwwroot/www.igeminicli.cn_static`
- uses `try_files $uri $uri/ /index.html`
- applies long cache headers for assets

### Content publisher layout on server

- Publisher root: `/opt/llmfit-publisher`
- Repo clone: `/opt/llmfit-publisher/repo`
- Build directory: `/opt/llmfit-publisher/build`
- External manifest/state:
  `/opt/llmfit-publisher/state/content-manifest.json`
- Environment file: `/opt/llmfit-publisher/.content.env`
- Cron file: `/etc/cron.d/llmfit-content`
- Log file: `/var/log/llmfit-content.log`

### Current cron pattern

The active server cron runs daily at `03:17`:

```cron
17 3 * * * root cd /opt/llmfit-publisher/repo && /bin/bash -lc 'set -a; source /opt/llmfit-publisher/.content.env; set +a; /bin/bash scripts/refresh_and_publish_site.sh' >> /var/log/llmfit-content.log 2>&1
```

### Important security rule

Do not commit:

- API keys
- LLM endpoint secrets
- server credentials
- SSL private keys
- production-only env files

Keep them in server-side env files or your secret manager.

## 14. Recommended Environment Variables

Use an env file similar to this on the server:

```sh
export LLMFIT_CONTENT_BUILD_ROOT=/opt/your-project-publisher/build
export LLMFIT_CONTENT_STATE_FILE=/opt/your-project-publisher/state/content-manifest.json
export LLMFIT_CONTENT_DOCROOT=/www/wwwroot/your-domain_static
export LLMFIT_CONTENT_DAILY_COUNT=4
export LLMFIT_CONTENT_GIT_BRANCH=main
export LLMFIT_CONTENT_SITE_BASE_URL=https://www.your-domain.com
export LLMFIT_CONTENT_LLM_ENDPOINT=https://your-openai-compatible-endpoint/v1/chat/completions
export LLMFIT_CONTENT_LLM_API_KEY=replace-me
export LLMFIT_CONTENT_LLM_MODEL=auto
export LLMFIT_CONTENT_LLM_TIMEOUT=60
export LLMFIT_CONTENT_LLM_RETRIES=2
export LLMFIT_CONTENT_LLM_RETRY_DELAY_SECONDS=3
export LLMFIT_CONTENT_ALLOW_STALE_REPO=1
export LLMFIT_CONTENT_RUN_REPORT_FILE=/opt/your-project-publisher/build/last-run.json
```

Notes:

- `LLMFIT_CONTENT_DAILY_COUNT=4` is a good default inside the requested `3-5`
  page/day range.
- Keep the state file outside the repo.
- Keep the docroot separate from the repo clone.
- Allow either a base OpenAI-compatible endpoint such as `.../v1` or the full
  `.../chat/completions` path. Normalize it in code.
- Consider allowing stale-repo publishing when upstream git refresh fails
  temporarily, especially on unstable overseas links.

## 15. Deployment Modes

Two site deployment modes now exist in the repo.

### Mode A: isolated container deployment

Files:

- `deploy/site.compose.yml`
- `deploy/site.nginx.conf`
- `scripts/deploy-site.sh`

Use this when:

- you want a low-risk first rollout
- you want the site to listen on an unused port such as `18088`
- you plan to proxy from an existing edge later

### Mode B: direct static docroot deployment

Use this when:

- the server already has an Nginx vhost manager
- a static docroot already exists
- you want to update only one site without touching other services

This is the mode used by current production.

## 16. Safe Deployment Sequence Used Here

The actual deployment sequence was:

1. Build and verify site output locally.
2. Confirm the target server already had an Nginx stack.
3. Avoid changing unrelated sites or global Nginx behavior.
4. Create a dedicated static docroot for the new site.
5. Add a dedicated vhost for the domain.
6. Add apex-to-www redirect.
7. Sync site files into the docroot.
8. Verify public access over the domain.
9. Add automated publishing only after the manual deployment path was stable.

This order reduced risk because the manual deployment path was proven before the
cron publisher was introduced.

## 17. Verification Checklist

Every rollout should verify all of the following:

- home page returns `200`
- docs page returns `200`
- Chinese home page returns `200`
- insights index returns `200`
- Chinese insights index returns `200`
- feed returns `200`
- sitemap returns `200`
- apex domain redirects correctly
- alternate language links point to real pages
- RSS links exist on insights pages
- sitemap contains all major static and generated routes
- daily cron log shows successful generation
- the JSON run report reflects LLM success vs fallback counts

Examples used here:

- `https://www.igeminicli.cn/insights/`
- `https://www.igeminicli.cn/zh/insights/`
- `https://www.igeminicli.cn/feed.xml`
- `https://www.igeminicli.cn/insights/hardware/`
- `https://www.igeminicli.cn/zh/insights/hardware/`

## 18. Replication Procedure for the Next Project

This is the reusable SOP.

### Phase 1: source project selection

1. Start from a technically valuable open-source core.
2. Confirm the engine solves a real operator problem.
3. Confirm the repo license permits derivative packaging.

### Phase 2: product framing

1. Choose a sharper product name.
2. Define the target user.
3. Define the main pain point.
4. Rewrite the README around outcomes, not just features.
5. Create a clear install path.

### Phase 3: website creation

1. Build a static site directory inside the repo.
2. Add:
   - home
   - docs
   - use cases
   - API
   - FAQ
   - self-host/deployment page
3. Make the site independently deployable.

### Phase 4: production deployment

1. Choose isolated container deployment or direct static docroot deployment.
2. Do not modify unrelated services.
3. Set up a dedicated domain or subdomain.
4. Add HTTPS.
5. Verify public reachability before adding automation.

### Phase 5: multilingual expansion

1. Decide the language paths.
2. Mirror primary pages.
3. Add hreflang and language switchers.
4. Verify navigation symmetry.

### Phase 6: content engine

1. Define strict allowed topic zones.
2. Build deterministic fallback copy first.
3. Add optional external LLM drafting second.
4. Store publish state outside the repo.
5. Generate feeds and sitemap automatically.

### Phase 7: automated publishing

1. Keep a clean server clone.
2. Build in a staging directory.
3. Publish with rsync.
4. Add a manual healthcheck for the external LLM path.
5. Add cron only after manual runs succeed.
6. Log every run and persist a run report.

### Phase 8: content hub maturity

1. Add taxonomy pages.
2. Add related links.
3. Improve internal navigation.
4. Improve feed discovery.
5. Refresh older generated pages into the new structure.

## 19. What to Parameterize for Fast Reuse

To copy this system into another project quickly, treat these values as inputs:

- project name
- GitHub repo path
- tagline
- target audience
- value proposition
- brand assets
- domain
- site base URL
- deployment mode
- static docroot
- language set
- content topic pool
- daily publish count
- external LLM endpoint
- cron schedule

If these are defined early, the rest of the implementation becomes mostly a
repeatable packaging and operations exercise.

## 20. Non-Negotiable Guardrails

For future projects, keep these rules:

1. Never let the content engine drift outside the product theme.
2. Never depend on the external LLM as the only drafting path.
3. Never store production secrets in the repo.
4. Never run daily automation directly against tracked site files in the repo.
5. Never deploy onto a shared server by modifying global config blindly.
6. Always back up the live docroot before major syncs.
7. Always verify public URLs after deployment.

## 21. Suggested Next Improvements

If this system is expanded further, the next improvements should be:

- stronger retry/validation around external LLM JSON generation
- topic pool growth with tighter editorial templates
- search console integration and measurement loop
- automated stale-page refresh logic
- structured release notes for site/content milestones
- optional multi-domain or multi-project publisher template

## 22. Bottom Line

This project is no longer just a useful engine. It is now a repeatable product
pattern:

- technical core
- clear positioning
- deployable site
- multilingual presentation
- controlled content growth
- production automation

That pattern is the real asset to reuse.
