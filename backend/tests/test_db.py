"""SQLite cache tests: roundtrip correctness and no deprecated datetime adapters."""
import warnings

import pytest

from db import TokenDatabase


@pytest.fixture
def db(tmp_path):
    return TokenDatabase(str(tmp_path / "test.db"))


TOKENS = [{"symbol": "AAA", "name": "Token A"}, {"symbol": "BBB", "name": "Token B"}]


class TestCacheRoundtrip:
    def test_trending_roundtrip(self, db):
        db.save_trending("ethereum", TOKENS)
        assert db.get_trending("ethereum") == TOKENS

    def test_expired_entries_are_not_returned(self, db):
        db.save_trending("ethereum", TOKENS, ttl_minutes=-1)
        assert db.get_trending("ethereum") is None

    def test_no_deprecated_datetime_adapter(self, db):
        """Bug: datetime objects were passed raw to sqlite3, relying on the
        default adapter deprecated since Python 3.12."""
        with warnings.catch_warnings():
            warnings.simplefilter("error", DeprecationWarning)
            db.save_trending("ethereum", TOKENS)
            db.get_trending("ethereum")
            db.save_token("0x" + "1" * 40, "ethereum", {"symbol": "AAA"})
            db.get_token("0x" + "1" * 40, "ethereum")
            db.cleanup_expired()
            db.get_stats()


class TestScoreHistory:
    ADDR = "0x" + "9" * 40

    def test_roundtrip_newest_first(self, db):
        db.save_score(self.ADDR, "ethereum", 72.5, "low", 0.6)
        db.save_score(self.ADDR, "ethereum", 68.0, "moderate", 0.55)
        history = db.get_score_history(self.ADDR, "ethereum")
        assert len(history) == 2
        assert history[0]["score"] == 68.0          # newest first
        assert history[0]["risk_level"] == "moderate"
        assert history[1]["score"] == 72.5
        assert all("created_at" in row for row in history)

    def test_history_is_scoped_to_address_and_chain(self, db):
        db.save_score(self.ADDR, "ethereum", 72.5, "low", 0.6)
        assert db.get_score_history("0x" + "8" * 40, "ethereum") == []
        assert db.get_score_history(self.ADDR, "bsc") == []

    def test_limit(self, db):
        for i in range(5):
            db.save_score(self.ADDR, "ethereum", float(i), "low", 0.5)
        assert len(db.get_score_history(self.ADDR, "ethereum", limit=3)) == 3
