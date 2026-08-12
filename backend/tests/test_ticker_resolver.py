"""Ticker resolver caching: transient failures must not be cached forever."""
from ticker_resolver import TickerResolver


class TestResolveCaching:
    def test_failed_resolution_is_not_cached(self):
        """Bug: @lru_cache on resolve() cached None (API hiccup, rate limit)
        for the process lifetime, permanently blacklisting the ticker."""
        resolver = TickerResolver()
        attempts = {"n": 0}

        def flaky_coingecko(ticker, chain):
            attempts["n"] += 1
            return None if attempts["n"] == 1 else "0x" + "3" * 40

        resolver._resolve_coingecko = flaky_coingecko
        resolver._resolve_dexscreener = lambda ticker, chain: None

        assert resolver.resolve("UNI", "ethereum") is None
        assert resolver.resolve("UNI", "ethereum") == "0x" + "3" * 40

    def test_successful_resolution_is_cached(self):
        resolver = TickerResolver()
        attempts = {"n": 0}

        def counting_coingecko(ticker, chain):
            attempts["n"] += 1
            return "0x" + "3" * 40

        resolver._resolve_coingecko = counting_coingecko
        resolver._resolve_dexscreener = lambda ticker, chain: None

        resolver.resolve("UNI", "ethereum")
        resolver.resolve("UNI", "ethereum")
        assert attempts["n"] == 1
