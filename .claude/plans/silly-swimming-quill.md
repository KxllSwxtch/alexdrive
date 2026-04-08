# Commit & Deploy to Production

## Context
All code changes from the carmanager migration + detail page fixes (images, translations, year, blur) are ready. Need to commit everything, push, and redeploy on the production server.

## Step 1: Commit all changes

Stage all modified/deleted/new files (excluding sensitive files):
- **DO NOT commit**: `alexdrive-key.pem`, `ssh.txt`, `auth.txt` (credentials)
- **Stage**: all `alexdriveapp/` changes, all `alexdrivebackend/` changes, `docker-compose.yml`, `prompts.md`
- Commit message: summarize the carmanager migration + detail page fixes

## Step 2: Push to origin/main

```bash
git push origin main
```

## Step 3: SSH into production & redeploy

Server: `ssh root@175.45.194.210` (password in ssh.txt)

```bash
cd /path/to/project   # find the project directory first
git pull origin main
docker compose down
docker compose up -d --build
```

## Verification
- Check `docker compose ps` shows both services running
- Check `docker compose logs --tail=20 backend` for healthy startup
- Check `docker compose logs --tail=20 frontend` for successful build
