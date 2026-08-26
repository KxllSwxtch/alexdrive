#!/usr/bin/env bash
# Deploy AlexDrive to the production VPS.
#
#   ./deploy.sh              # pull + rebuild + restart, then verify health
#   ./deploy.sh backend      # only the backend service
#   ./deploy.sh --no-build   # restart without rebuilding images
#
# Requires SSH access to the production host as root.
set -euo pipefail

HOST="${ALEXDRIVE_HOST:-175.45.194.210}"
USER="${ALEXDRIVE_USER:-root}"
APP_DIR="${ALEXDRIVE_APP_DIR:-/opt/alexdrive}"
BRANCH="${ALEXDRIVE_BRANCH:-main}"
SITE="${ALEXDRIVE_SITE:-https://alexdrive.kr}"

# The production host has no Host block in ~/.ssh/config, so ssh falls back to
# `IdentitiesOnly no` plus its seven default identity paths. Every existing key
# (~/.ssh/id_rsa, ~/.ssh/id_ed25519) is offered BEFORE the password and each one
# burns a server-side auth attempt. This host runs a hardened MaxAuthTries, so those
# stray keys exhaust it and ssh dies with "Too many authentication failures" -- which
# looks like a bad password but is not. Offer exactly one credential and nothing else.
SSH_KEY="${ALEXDRIVE_SSH_KEY:-}"
SSH_OPTS=(-o ConnectTimeout=20 -o IdentitiesOnly=yes -o IdentityAgent=none)
if [ -n "$SSH_KEY" ]; then
  [ -f "$SSH_KEY" ] || { echo "ssh key not found: $SSH_KEY" >&2; exit 2; }
  SSH_OPTS+=(-i "$SSH_KEY" -o PreferredAuthentications=publickey)
  echo "==> auth: key $SSH_KEY"
else
  # Password only -- do not offer any key, so all attempts go to the password.
  SSH_OPTS+=(-o PubkeyAuthentication=no -o PreferredAuthentications=password)
  echo "==> auth: password (no keys offered)"
fi

SERVICE=""
BUILD=1
for arg in "$@"; do
  case "$arg" in
    --no-build) BUILD=0 ;;
    backend|frontend) SERVICE="$arg" ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

echo "==> Deploying ${BRANCH} to ${USER}@${HOST}:${APP_DIR}"

ssh "${SSH_OPTS[@]}" "${USER}@${HOST}" APP_DIR="$APP_DIR" BRANCH="$BRANCH" SERVICE="$SERVICE" BUILD="$BUILD" 'bash -euo pipefail -s' <<'REMOTE'
cd "$APP_DIR"

echo "--> git pull"
git fetch --all --prune
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
echo "--> now at: $(git log --oneline -1)"

COMPOSE="docker compose"
$COMPOSE version >/dev/null 2>&1 || COMPOSE="docker-compose"

if [ "$BUILD" = "1" ]; then
  echo "--> building images"
  $COMPOSE build $SERVICE
fi

echo "--> restarting"
$COMPOSE up -d $SERVICE

echo "--> container status"
$COMPOSE ps
REMOTE

echo "==> Waiting for backend health to come up..."
for i in $(seq 1 30); do
  sleep 5
  BODY="$(curl -fsS --max-time 15 "${SITE}/api/health" 2>/dev/null || true)"
  [ -n "$BODY" ] || { echo "  [$i/30] no response yet"; continue; }
  echo "  [$i/30] $BODY"
  case "$BODY" in
    *'"status":"ok"'*) echo "==> Backend healthy."; exit 0 ;;
  esac
done

echo "==> WARNING: backend did not report status=ok within ~2.5 minutes." >&2
echo "    A 'degraded' status means the scraper still cannot reach the source." >&2
echo "    Check:  ssh ${SSH_OPTS[*]} ${USER}@${HOST} 'cd ${APP_DIR} && docker compose logs --tail 100 backend'" >&2
exit 1
