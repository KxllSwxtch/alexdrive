#!/usr/bin/env bash
# AlexDrive health watchdog. Runs from cron every 5 minutes.
#
# Detects a degraded scraper and, when it stays degraded, restarts the backend.
# The 2026-08 outage was a leaked httpx connection pool: a restart clears it
# instantly, but nothing ever restarted, so the site served 6-day-old data while
# this script's predecessor logged 1844 alerts to syslog that nobody read.
#
# Deliberate guards:
#   * a restart needs DEGRADED_STREAK consecutive failures, never a single blip
#   * never restart while rate_limited -- that is the SOURCE throttling us, so a
#     restart cannot help and repeatedly reconnecting risks an IP ban
#   * at most one restart per RESTART_MIN_INTERVAL and RESTART_MAX_PER_DAY per day;
#     past that it logs and stops, because a restart loop against a genuinely
#     dead upstream is worse than staying down
#
# Env overrides exist so the test suite can run this against stubs.
set -uo pipefail

HEALTH_URL="${ALEXDRIVE_HEALTH_URL:-http://localhost:3001/api/health}"
STATE_DIR="${ALEXDRIVE_STATE_DIR:-/var/lib/alexdrive}"
APP_DIR="${ALEXDRIVE_APP_DIR:-/opt/alexdrive}"
LOG_FILE="${ALEXDRIVE_LOG:-/var/log/alexdrive-health.log}"
SERVICE="${ALEXDRIVE_SERVICE:-backend}"

DEGRADED_STREAK="${ALEXDRIVE_DEGRADED_STREAK:-3}"        # x5min cron = 15 minutes
RESTART_MIN_INTERVAL="${ALEXDRIVE_RESTART_MIN_INTERVAL:-3600}"
RESTART_MAX_PER_DAY="${ALEXDRIVE_RESTART_MAX_PER_DAY:-4}"
VERIFY_WAIT="${ALEXDRIVE_VERIFY_WAIT:-25}"

STATE_FILE="$STATE_DIR/health-state"
mkdir -p "$STATE_DIR" 2>/dev/null
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null

now=$(date +%s)
today=$(date +%Y-%m-%d)

log() {
  printf '%s %s\n' "$(date -Is)" "$*" >> "$LOG_FILE" 2>/dev/null
  command -v logger >/dev/null 2>&1 && logger -t alexdrive "$*"
}

# --- state: streak | last_restart_epoch | restart_day | restarts_today ---------
streak=0; last_restart=0; restart_day=""; restarts_today=0
if [ -f "$STATE_FILE" ]; then
  # shellcheck disable=SC2162
  IFS='|' read streak last_restart restart_day restarts_today < "$STATE_FILE" 2>/dev/null
fi
streak="${streak:-0}"; last_restart="${last_restart:-0}"
restart_day="${restart_day:-}"; restarts_today="${restarts_today:-0}"
[ "$restart_day" = "$today" ] || restarts_today=0   # new day resets the daily cap

save_state() {
  printf '%s|%s|%s|%s\n' "$1" "$2" "$3" "$4" > "$STATE_FILE" 2>/dev/null
}

# --- probe ---------------------------------------------------------------------
HEALTH=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null)

if [ -z "$HEALTH" ]; then
  status="unreachable"; rate_limited="false"
else
  status=$(printf '%s' "$HEALTH" | jq -r '.status // "unparseable"' 2>/dev/null || echo "unparseable")
  rate_limited=$(printf '%s' "$HEALTH" | jq -r '.rate_limited // false' 2>/dev/null || echo "false")
fi

# --- healthy: reset and report recovery ----------------------------------------
if [ "$status" = "ok" ]; then
  if [ "$streak" -gt 0 ]; then
    log "RECOVERED: healthy again after $streak degraded check(s): $HEALTH"
  fi
  save_state 0 "$last_restart" "$today" "$restarts_today"
  exit 0
fi

# --- degraded ------------------------------------------------------------------
streak=$((streak + 1))
log "ALERT: degraded (streak=$streak/$DEGRADED_STREAK) status=$status: ${HEALTH:-<no response>}"

if [ "$rate_limited" = "true" ]; then
  log "SKIP restart: rate_limited by the source -- a restart cannot help and risks a ban"
  save_state "$streak" "$last_restart" "$today" "$restarts_today"
  exit 1
fi

if [ "$streak" -lt "$DEGRADED_STREAK" ]; then
  save_state "$streak" "$last_restart" "$today" "$restarts_today"
  exit 1
fi

since_restart=$((now - last_restart))
if [ "$last_restart" -gt 0 ] && [ "$since_restart" -lt "$RESTART_MIN_INTERVAL" ]; then
  log "SKIP restart: last restart was ${since_restart}s ago (< ${RESTART_MIN_INTERVAL}s cooldown)"
  save_state "$streak" "$last_restart" "$today" "$restarts_today"
  exit 1
fi

if [ "$restarts_today" -ge "$RESTART_MAX_PER_DAY" ]; then
  log "SKIP restart: already restarted $restarts_today time(s) today (cap $RESTART_MAX_PER_DAY). Needs a human."
  save_state "$streak" "$last_restart" "$today" "$restarts_today"
  exit 1
fi

# --- restart -------------------------------------------------------------------
log "RESTARTING $SERVICE after $streak consecutive degraded checks"
if (cd "$APP_DIR" && docker compose restart "$SERVICE" >/dev/null 2>&1); then
  restarts_today=$((restarts_today + 1))
  save_state 0 "$now" "$today" "$restarts_today"
  sleep "$VERIFY_WAIT"
  AFTER=$(curl -s --max-time 10 "$HEALTH_URL" 2>/dev/null)
  after_status=$(printf '%s' "$AFTER" | jq -r '.status // "unparseable"' 2>/dev/null || echo "unparseable")
  if [ "$after_status" = "ok" ]; then
    log "RESTART OK: $SERVICE healthy again (restart $restarts_today/$RESTART_MAX_PER_DAY today)"
    exit 0
  fi
  log "RESTART DID NOT RECOVER: status=$after_status: ${AFTER:-<no response>}"
  exit 1
fi

log "RESTART FAILED: docker compose restart $SERVICE returned non-zero"
save_state "$streak" "$last_restart" "$today" "$restarts_today"
exit 1
