"""
Database for caching trending tokens
Uses SQLite for persistence
"""
import sqlite3
import json
from datetime import datetime, timedelta


def _now_str() -> str:
    """Current time as an ISO string — sqlite3's implicit datetime adapter is
    deprecated since Python 3.12, so timestamps are stored/compared as text."""
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def _expiry_str(ttl_minutes: int) -> str:
    return (datetime.now() + timedelta(minutes=ttl_minutes)).isoformat(sep=" ", timespec="seconds")
from typing import List, Dict, Any, Optional
from pathlib import Path


class TokenDatabase:
    """SQLite database for token caching"""

    def __init__(self, db_path: str = "tokens.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Trending tokens cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trending_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Newest tokens cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newest_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Top gainers cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gainers_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Token details cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_cache (
                address TEXT PRIMARY KEY,
                chain TEXT NOT NULL,
                symbol TEXT,
                name TEXT,
                data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # Score history — one row per completed analysis (on-demand snapshots)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS score_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                chain TEXT NOT NULL,
                score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                confidence REAL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_score_history_token
            ON score_history(address, chain, id)
        """)

        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_trending_chain_expires
            ON trending_cache(chain, expires_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_newest_chain_expires
            ON newest_cache(chain, expires_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gainers_chain_expires
            ON gainers_cache(chain, expires_at)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_token_expires
            ON token_cache(expires_at)
        """)

        conn.commit()
        conn.close()

    def save_trending(self, chain: str, tokens: List[Dict[str, Any]], ttl_minutes: int = 10):
        """
        Save trending tokens to cache
        TTL: 10 minutes default (much longer than in-memory)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete old cache for this chain
        cursor.execute("DELETE FROM trending_cache WHERE chain = ?", (chain,))

        # Insert new cache
        expires_at = _expiry_str(ttl_minutes)
        data_json = json.dumps(tokens)

        cursor.execute("""
            INSERT INTO trending_cache (chain, data, expires_at)
            VALUES (?, ?, ?)
        """, (chain, data_json, expires_at))

        conn.commit()
        conn.close()

    def get_trending(self, chain: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached trending tokens if not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, expires_at FROM trending_cache
            WHERE chain = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (chain, _now_str()))

        row = cursor.fetchone()
        conn.close()

        if row:
            data_json, expires_at = row
            print(f"Cache HIT: Found trending data for {chain}, expires at {expires_at}")
            return json.loads(data_json)

        print(f"Cache MISS: No valid trending data for {chain}")
        return None

    def save_newest(self, chain: str, tokens: List[Dict[str, Any]], ttl_minutes: int = 10):
        """Save newest tokens to cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete old cache for this chain
        cursor.execute("DELETE FROM newest_cache WHERE chain = ?", (chain,))

        # Insert new cache
        expires_at = _expiry_str(ttl_minutes)
        data_json = json.dumps(tokens)

        cursor.execute("""
            INSERT INTO newest_cache (chain, data, expires_at)
            VALUES (?, ?, ?)
        """, (chain, data_json, expires_at))

        conn.commit()
        conn.close()

    def get_newest(self, chain: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached newest tokens if not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, expires_at FROM newest_cache
            WHERE chain = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (chain, _now_str()))

        row = cursor.fetchone()
        conn.close()

        if row:
            data_json, expires_at = row
            print(f"Cache HIT: Found newest data for {chain}, expires at {expires_at}")
            return json.loads(data_json)

        print(f"Cache MISS: No valid newest data for {chain}")
        return None

    def save_gainers(self, chain: str, tokens: List[Dict[str, Any]], ttl_minutes: int = 10):
        """Save top gainers to cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Delete old cache for this chain
        cursor.execute("DELETE FROM gainers_cache WHERE chain = ?", (chain,))

        # Insert new cache
        expires_at = _expiry_str(ttl_minutes)
        data_json = json.dumps(tokens)

        cursor.execute("""
            INSERT INTO gainers_cache (chain, data, expires_at)
            VALUES (?, ?, ?)
        """, (chain, data_json, expires_at))

        conn.commit()
        conn.close()

    def get_gainers(self, chain: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached top gainers if not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data, expires_at FROM gainers_cache
            WHERE chain = ? AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (chain, _now_str()))

        row = cursor.fetchone()
        conn.close()

        if row:
            data_json, expires_at = row
            print(f"Cache HIT: Found gainers data for {chain}, expires at {expires_at}")
            return json.loads(data_json)

        print(f"Cache MISS: No valid gainers data for {chain}")
        return None

    def save_token(self, address: str, chain: str, data: Dict[str, Any], ttl_minutes: int = 30):
        """Save individual token data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        expires_at = _expiry_str(ttl_minutes)
        data_json = json.dumps(data)

        cursor.execute("""
            INSERT OR REPLACE INTO token_cache
            (address, chain, symbol, name, data, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            address,
            chain,
            data.get("symbol", ""),
            data.get("name", ""),
            data_json,
            expires_at
        ))

        conn.commit()
        conn.close()

    def get_token(self, address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Get cached token data if not expired"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data FROM token_cache
            WHERE address = ? AND chain = ? AND expires_at > ?
        """, (address, chain, _now_str()))

        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def save_score(self, address: str, chain: str, score: float,
                   risk_level: str, confidence: Optional[float] = None):
        """Record one analysis snapshot for score-over-time tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO score_history (address, chain, score, risk_level, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (address.lower(), chain, score, risk_level, confidence, _now_str()))
        conn.commit()
        conn.close()

    def get_score_history(self, address: str, chain: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Return snapshots for a token, newest first"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, risk_level, confidence, created_at
            FROM score_history
            WHERE address = ? AND chain = ?
            ORDER BY id DESC
            LIMIT ?
        """, (address.lower(), chain, limit))
        rows = cursor.fetchall()
        conn.close()
        return [
            {"score": r[0], "risk_level": r[1], "confidence": r[2], "created_at": r[3]}
            for r in rows
        ]

    def cleanup_expired(self):
        """Remove expired cache entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM trending_cache WHERE expires_at < ?", (_now_str(),))
        cursor.execute("DELETE FROM newest_cache WHERE expires_at < ?", (_now_str(),))
        cursor.execute("DELETE FROM gainers_cache WHERE expires_at < ?", (_now_str(),))
        cursor.execute("DELETE FROM token_cache WHERE expires_at < ?", (_now_str(),))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        if deleted > 0:
            print(f"Cleaned up {deleted} expired cache entries")

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM trending_cache WHERE expires_at > ?", (_now_str(),))
        trending_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM newest_cache WHERE expires_at > ?", (_now_str(),))
        newest_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM gainers_cache WHERE expires_at > ?", (_now_str(),))
        gainers_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM token_cache WHERE expires_at > ?", (_now_str(),))
        token_count = cursor.fetchone()[0]

        conn.close()

        return {
            "trending_cached": trending_count,
            "newest_cached": newest_count,
            "gainers_cached": gainers_count,
            "tokens_cached": token_count
        }


# Singleton instance
_db = None

def get_db() -> TokenDatabase:
    """Get global database instance"""
    global _db
    if _db is None:
        db_path = Path(__file__).parent / "tokens.db"
        _db = TokenDatabase(str(db_path))
    return _db
