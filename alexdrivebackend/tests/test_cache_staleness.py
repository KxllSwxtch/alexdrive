"""Regression tests for the 'immortal stale cache' that concealed the 2026-08 outage.

Freshness used to be derived as `now - (expiry - TTL)`. Every failure path extended
`expiry`, so a FAILED refresh reset the apparent age to zero and the entry looked brand
new again -- forever. Production served 6.4-day-old listings while the scraper was
completely dead, and /api/health was the only thing that noticed.
"""
import time

import pytest

from app.services import scraper as sc


class TestEntryAge:
    def test_age_is_measured_from_fetched_at_not_expiry(self):
        entry = sc._new_cache_entry({"listings": [1]}, sc.LISTING_TTL)
        entry["fetched_at"] = time.time() - 300
        entry["expiry"] = time.time() + sc.LISTING_TTL
        assert 295 < sc._entry_age(entry, sc.LISTING_TTL) < 305

    def test_failed_refresh_does_not_reset_age(self):
        """The core bug: marking an entry stale-served must not make it look fresh."""
        entry = sc._new_cache_entry({"listings": [1]}, sc.LISTING_TTL)
        entry["fetched_at"] = time.time() - 6 * 24 * 3600  # 6 days old, as in production

        sc._mark_stale_served(entry, sc.LISTING_TTL)

        age = sc._entry_age(entry, sc.LISTING_TTL)
        assert age > 5 * 24 * 3600, "age must keep growing across failed refreshes"
        assert age >= sc.LISTING_TTL, "a 6-day-old entry must never count as fresh"

    def test_mark_stale_served_keeps_entry_servable_and_backs_off(self):
        entry = sc._new_cache_entry({"listings": [1]}, sc.LISTING_TTL)
        entry["fetched_at"] = time.time() - 10_000
        sc._mark_stale_served(entry, sc.LISTING_TTL)
        # still servable (survives eviction) ...
        assert entry["expiry"] > time.time()
        # ... but a retry is scheduled rather than attempted on every request
        assert entry["next_retry_at"] > time.time()

    def test_legacy_entry_without_fetched_at_still_works(self):
        """Entries restored from disk predate `fetched_at`."""
        legacy = {"data": {}, "expiry": time.time() + sc.LISTING_TTL - 100}
        age = sc._entry_age(legacy, sc.LISTING_TTL)
        assert 95 < age < 105


class TestIsDegraded:
    def test_never_parsed_becomes_degraded_after_threshold(self, monkeypatch):
        """A container that has NEVER parsed (dead proxy after restart) must report
        degraded, not look permanently healthy."""
        monkeypatch.setattr(sc, "_last_successful_parse", 0.0)
        monkeypatch.setattr(sc, "_process_start", time.time() - sc.DEGRADED_AFTER_SECONDS - 10)
        assert sc.is_degraded() is True

    def test_recent_success_is_not_degraded(self, monkeypatch):
        monkeypatch.setattr(sc, "_last_successful_parse", time.time() - 10)
        assert sc.is_degraded() is False

    def test_stale_success_is_degraded(self, monkeypatch):
        monkeypatch.setattr(sc, "_last_successful_parse", time.time() - sc.DEGRADED_AFTER_SECONDS - 10)
        assert sc.is_degraded() is True


class TestWarmingGuards:
    @pytest.mark.asyncio
    async def test_warming_skipped_while_degraded(self, monkeypatch):
        """The warm storm is what exhausted the connection pool."""
        monkeypatch.setattr(sc, "_last_successful_parse", 0.0)
        monkeypatch.setattr(sc, "_process_start", time.time() - sc.DEGRADED_AFTER_SECONDS - 10)
        called = []

        async def _boom(cid, **kw):
            called.append(cid)
            return {}

        monkeypatch.setattr(sc, "get_car_detail", _boom)
        await sc.warm_detail_cache_for_listings([{"id": "123"}, {"id": "456"}])
        assert called == [], "must not warm details while the scraper is degraded"

    @pytest.mark.asyncio
    async def test_failed_warm_is_backed_off_not_retried_every_request(self, monkeypatch):
        monkeypatch.setattr(sc, "_last_successful_parse", time.time())
        monkeypatch.setattr(sc, "_warm_failures", {})
        monkeypatch.setattr(sc, "_warming_in_flight", set())
        attempts = []

        async def _fail(cid, **kw):
            attempts.append(cid)
            raise RuntimeError("upstream down")

        monkeypatch.setattr(sc, "get_car_detail", _fail)
        listings = [{"id": "car-1"}]
        await sc.warm_detail_cache_for_listings(listings)
        await sc.warm_detail_cache_for_listings(listings)
        await sc.warm_detail_cache_for_listings(listings)

        assert attempts == ["car-1"], "a failing id must be backed off, not re-queued every request"
