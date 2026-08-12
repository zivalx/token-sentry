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
