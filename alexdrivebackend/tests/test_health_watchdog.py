"""Tests for scripts/alexdrive-health-check.sh.

The watchdog restarts production, so its restraint matters more than its eagerness:
it must not restart on a blip, must never restart while the source is rate-limiting
us, and must stop restarting rather than loop against a dead upstream.

Runs the real script with `curl` and `docker` stubbed on PATH.
"""
import os
import shutil
import subprocess
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "alexdrive-health-check.sh"

OK = '{"status":"ok","last_successful_parse_seconds_ago":12,"rate_limited":false}'
DEGRADED = '{"status":"degraded","last_successful_parse_seconds_ago":553697,"rate_limited":false}'
RATE_LIMITED = '{"status":"degraded","last_successful_parse_seconds_ago":1200,"rate_limited":true}'

pytestmark = pytest.mark.skipif(
    not shutil.which("jq"), reason="watchdog needs jq (present on the production host)"
)


@pytest.fixture
def env(tmp_path):
    """A sandbox with stubbed curl/docker and a marker file recording restarts."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    restarts = tmp_path / "restarts.log"
    responses = tmp_path / "responses"  # one JSON body per line; last line repeats

    (bin_dir / "curl").write_text(
        "#!/usr/bin/env bash\n"
        f'f="{responses}"\n'
        'n=$(cat "%s" 2>/dev/null || echo 0)\n' % (tmp_path / "curl_calls")
        + f'total=$(wc -l < "$f")\n'
        'line=$((n + 1)); [ "$line" -gt "$total" ] && line="$total"\n'
        f'echo $((n + 1)) > "{tmp_path / "curl_calls"}"\n'
        'sed -n "${line}p" "$f"\n'
    )
    (bin_dir / "docker").write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$@" >> "{restarts}"\n'
        "exit 0\n"
    )
    for f in ("curl", "docker"):
        os.chmod(bin_dir / f, 0o755)

    def run(bodies, *, state=None, **overrides):
        responses.write_text("\n".join(bodies) + "\n")
        (tmp_path / "curl_calls").unlink(missing_ok=True)
        state_dir = tmp_path / "state"
        state_dir.mkdir(exist_ok=True)
        if state is not None:
            (state_dir / "health-state").write_text(state + "\n")
        e = {
            **os.environ,
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "ALEXDRIVE_HEALTH_URL": "http://stub/health",
            "ALEXDRIVE_STATE_DIR": str(state_dir),
            "ALEXDRIVE_APP_DIR": str(tmp_path),
            "ALEXDRIVE_LOG": str(tmp_path / "health.log"),
            "ALEXDRIVE_VERIFY_WAIT": "0",
            **overrides,
        }
        proc = subprocess.run(["bash", str(SCRIPT)], env=e, capture_output=True, text=True, timeout=60)
        return {
            "code": proc.returncode,
            "restarts": restarts.read_text() if restarts.exists() else "",
            "log": (tmp_path / "health.log").read_text() if (tmp_path / "health.log").exists() else "",
            "state": (state_dir / "health-state").read_text().strip(),
        }

    return run


def test_healthy_does_nothing(env):
    r = env([OK])
    assert r["code"] == 0
    assert r["restarts"] == "", "must not restart a healthy backend"
    assert r["state"].startswith("0|")


def test_single_degraded_check_does_not_restart(env):
    """A blip must never trigger a production restart."""
    r = env([DEGRADED])
    assert r["restarts"] == ""
    assert r["state"].startswith("1|"), "streak should advance to 1"
    assert "streak=1/3" in r["log"]


def test_restarts_after_three_consecutive_degraded_checks(env):
    r = env([DEGRADED, OK], state="2|0||0")  # this run is the 3rd strike
    assert "restart backend" in r["restarts"], "should have restarted"
    assert "RESTART OK" in r["log"]
    assert r["code"] == 0
    assert r["state"].startswith("0|"), "streak resets after a restart"


def test_never_restarts_while_rate_limited(env):
    """Rate limiting is the SOURCE throttling us; restarting risks an IP ban."""
    r = env([RATE_LIMITED], state="9|0||0")
    assert r["restarts"] == "", "must not restart when rate_limited"
    assert "SKIP restart: rate_limited" in r["log"]


def test_respects_the_hourly_cooldown(env):
    recent = str(int(time.time()) - 60)
    r = env([DEGRADED], state=f"2|{recent}||1")
    assert r["restarts"] == ""
    assert "cooldown" in r["log"]


def test_respects_the_daily_cap(env):
    today = time.strftime("%Y-%m-%d")
    old = str(int(time.time()) - 7200)  # outside the cooldown
    r = env([DEGRADED], state=f"2|{old}|{today}|4")
    assert r["restarts"] == "", "must stop restarting rather than loop forever"
    assert "Needs a human" in r["log"]


def test_daily_cap_resets_on_a_new_day(env):
    old = str(int(time.time()) - 7200)
    r = env([DEGRADED, OK], state=f"2|{old}|1999-01-01|4")
    assert "restart backend" in r["restarts"], "yesterday's cap must not block today"


def test_unreachable_backend_counts_as_degraded(env):
    r = env([""], state="2|0||0")
    assert "restart backend" in r["restarts"]
    assert "unreachable" in r["log"]


def test_recovery_is_logged_and_streak_clears(env):
    r = env([OK], state="2|0||0")
    assert "RECOVERED" in r["log"]
    assert r["state"].startswith("0|")


def test_restart_that_does_not_recover_is_reported(env):
    r = env([DEGRADED, DEGRADED], state="2|0||0")
    assert "restart backend" in r["restarts"]
    assert "RESTART DID NOT RECOVER" in r["log"]
    assert r["code"] == 1
