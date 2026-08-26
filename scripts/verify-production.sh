#!/usr/bin/env bash
# Verify the production site is genuinely healthy -- not merely serving stale cache.
# Exits non-zero on the first hard failure. Usage: ./scripts/verify-production.sh
set -uo pipefail

SITE="${ALEXDRIVE_SITE:-https://alexdrive.kr}"
CANON='PageNow=1&PageSize=24&PageSort=ModDt&PageAscDesc=DESC'
FAIL=0
note() { printf '%s\n' "$*"; }
bad()  { printf 'FAIL  %s\n' "$*"; FAIL=1; }
ok()   { printf 'ok    %s\n' "$*"; }

note "== 1. backend health =="
HEALTH="$(curl -fsS --max-time 20 "${SITE}/api/health" 2>/dev/null || true)"
if [ -z "$HEALTH" ]; then
  bad "/api/health unreachable"
else
  note "      $HEALTH"
  case "$HEALTH" in
    *'"status":"ok"'*) ok "status=ok" ;;
    *) bad "status is not ok (scraper still cannot reach the source)" ;;
  esac
  AGE="$(printf '%s' "$HEALTH" | sed -n 's/.*"last_successful_parse_seconds_ago":\([0-9]*\).*/\1/p')"
  if [ -n "$AGE" ]; then
    if [ "$AGE" -lt 900 ]; then ok "last successful parse ${AGE}s ago"
    else bad "last successful parse ${AGE}s ago (>900s = stale)"; fi
  else
    bad "no last_successful_parse_seconds_ago (never parsed)"
  fi
fi

note "== 2. canonical catalog query (the one the homepage issues) =="
read -r CODE TIME <<<"$(curl -s -o /dev/null --compressed --max-time 70 \
  -w '%{http_code} %{time_total}' "${SITE}/api/cars?${CANON}")"
note "      code=${CODE} time=${TIME}s"
[ "$CODE" = "200" ] && ok "/api/cars 200" || bad "/api/cars returned ${CODE} (503@30s=pool timeout, 504@60s=nginx)"
awk -v t="$TIME" 'BEGIN{exit !(t<15)}' && ok "responded in ${TIME}s" || bad "took ${TIME}s (>15s)"

note "== 3. filters endpoint =="
read -r FCODE FTIME <<<"$(curl -s -o /dev/null --compressed --max-time 70 \
  -w '%{http_code} %{time_total}' "${SITE}/api/filters?carnation=1")"
note "      code=${FCODE} time=${FTIME}s"
[ "$FCODE" = "200" ] && ok "/api/filters 200" || bad "/api/filters returned ${FCODE}"

note "== 4. homepage renders cars =="
TMP="$(mktemp)"
read -r HCODE HTTFB <<<"$(curl -s --compressed --max-time 70 -o "$TMP" \
  -w '%{http_code} %{time_starttransfer}' "${SITE}/")"
CARS="$(grep -oE '/car/[^"\\]{5,60}' "$TMP" | sort -u | wc -l | tr -d ' ')"
note "      code=${HCODE} ttfb=${HTTFB}s car_links=${CARS}"
[ "$HCODE" = "200" ] && ok "homepage 200" || bad "homepage returned ${HCODE}"
[ "$CARS" -gt 0 ] && ok "${CARS} car links rendered" || bad "homepage rendered ZERO cars"
awk -v t="$HTTFB" 'BEGIN{exit !(t<15)}' && ok "ttfb ${HTTFB}s" || bad "ttfb ${HTTFB}s (>15s)"

note "== 5. a car detail page =="
SLUG="$(grep -oE '/car/[^"\\]{5,60}' "$TMP" | head -1)"
if [ -n "$SLUG" ]; then
  read -r DCODE DTIME <<<"$(curl -s -o /dev/null --compressed --max-time 70 \
    -w '%{http_code} %{time_starttransfer}' "${SITE}${SLUG}")"
  note "      ${SLUG} code=${DCODE} ttfb=${DTIME}s"
  [ "$DCODE" = "200" ] && ok "detail page 200" || bad "detail page returned ${DCODE}"
else
  bad "no car link to test a detail page with"
fi
rm -f "$TMP"

note "== 6. concurrency burst (pool exhaustion check) =="
BURST="$(for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null --compressed --max-time 70 -w '%{http_code} ' "${SITE}/api/cars?${CANON}&PageNow=${i}" &
done; wait)"
note "      codes: ${BURST}"
case "$BURST" in
  *503*|*504*|*000*) bad "5xx/timeout under concurrency -- pool still exhausting" ;;
  *) ok "no 5xx under 6 concurrent requests" ;;
esac

echo
if [ "$FAIL" = "0" ]; then echo "RESULT: PASS"; else echo "RESULT: FAIL"; fi
exit "$FAIL"
