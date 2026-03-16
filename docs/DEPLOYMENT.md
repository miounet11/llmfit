# Deployment

This repository ships two deployment targets:

1. The `llmfit` binary and API service.
2. A separate static product site in [`site/`](../site/).

## Local stack

Run both the API and the site locally:

```sh
docker compose up --build
```

- API: `http://127.0.0.1:8787`
- Site: `http://127.0.0.1:8080`

## Production site deployment

The safest production path is to deploy the static site as its own container on
an unused port and keep any existing reverse proxy unchanged until the new site
is verified.

### Example

```sh
git clone https://github.com/miounet11/llmfit.git /opt/llmfit
cd /opt/llmfit
docker compose -f deploy/site.compose.yml up -d
```

The site listens on port `18088` by default. Reverse proxy traffic to that port
from your existing Nginx, Caddy, or load balancer once DNS is ready.

### Remote helper script

You can also drive the same rollout from your local machine:

```sh
scripts/deploy-site.sh root@your-server /opt/llmfit
```

## Daily content publishing

The repository now includes a safe programmatic-content pipeline:

- `scripts/generate_site_content.py`: selects unpublished topics and renders bilingual pages
- `scripts/publish_site_content.sh`: builds a staging site tree and optionally rsyncs it to a live docroot
- `scripts/refresh_and_publish_site.sh`: updates the repo clone, then runs the publish step

Recommended production pattern:

1. Keep a clean repo clone on the server, for example `/opt/llmfit-publisher/repo`.
2. Store the publish manifest outside the repo, for example `/opt/llmfit-publisher/state/content-manifest.json`.
3. Build generated output into a separate staging directory.
4. Rsync the staging site into the live static docroot only after generation succeeds.

Example environment:

```sh
export LLMFIT_CONTENT_BUILD_ROOT=/opt/llmfit-publisher/build
export LLMFIT_CONTENT_STATE_FILE=/opt/llmfit-publisher/state/content-manifest.json
export LLMFIT_CONTENT_DOCROOT=/www/wwwroot/www.igeminicli.cn_static
export LLMFIT_CONTENT_DAILY_COUNT=4
export LLMFIT_CONTENT_LLM_ENDPOINT=https://example.com/v1/chat/completions
export LLMFIT_CONTENT_LLM_API_KEY=replace-me
export LLMFIT_CONTENT_LLM_MODEL=auto
```

Example cron entry:

```cron
17 3 * * * cd /opt/llmfit-publisher/repo && /bin/bash scripts/refresh_and_publish_site.sh >> /var/log/llmfit-content.log 2>&1
```

This keeps the git worktree clean because generation happens in an external build
directory, not inside tracked site files.

## Reverse proxy example

```nginx
server {
    listen 80;
    server_name igeminicli.cn www.igeminicli.cn;

    location / {
        proxy_pass http://127.0.0.1:18088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Notes

- The deployment assets are isolated on purpose to avoid colliding with any
  existing service on ports `80` or `443`.
- If you already run a reverse proxy, only add a new vhost after confirming the
  container is healthy on `127.0.0.1:18088`.
