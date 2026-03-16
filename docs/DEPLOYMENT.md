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
