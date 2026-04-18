# Deployment Guide

This app is configured to deploy to **Fly.io** (and Render as an alternative).

## Prerequisites

Install `flyctl`:
```bash
# macOS
brew install flyctl

# Or via curl (all platforms)
curl -L https://fly.io/install.sh | sh
```

## Fly.io Deployment

1. **Authenticate:**
   ```bash
   fly auth signup  # Create new account, or
   fly auth login   # Sign into existing account
   ```

2. **Launch the app** (uses existing fly.toml):
   ```bash
   fly launch --no-deploy --copy-config --name mrel-peer-benchmark
   ```

3. **Deploy:**
   ```bash
   fly deploy
   ```

4. **Check deployment status:**
   ```bash
   fly logs       # Stream live logs
   fly apps open  # Open app in browser
   ```

5. **Scale down to avoid charges** (optional—free tier allows 3 shared-cpu-1x machines):
   ```bash
   fly scale count 0
   ```

## Alternative: Render.com

If you prefer Render:

1. Connect your GitHub repo at render.com
2. Set **Build Command:** `pip install -r requirements.txt`
3. Set **Start Command:** `gunicorn --bind 0.0.0.0:8080 --workers 2 app.app:server`
4. Deploy

## Notes

- The app runs on port **8080** internally
- Fly.io auto-scales from zero machines when idle (free tier)
- Health checks query `/` every 30s (Dash serves this by default)
- All deployment commands are run **by you** — the assistant does not execute them
