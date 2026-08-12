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


class TestKeylessTrending:
    """Without a CMC key the dashboard must fall back to CoinGecko's trending
    list instead of showing nothing."""

    def test_falls_back_to_coingecko_when_cmc_returns_nothing(self, monkeypatch):
        import ticker_resolver as tr

        class EmptyCMC:
            def get_trending(self, chain, limit):
                return []

        monkeypatch.setattr(tr, "get_cmc_client", lambda: EmptyCMC())

        resolver = TickerResolver()
        sentinel = [{"symbol": "AAA", "address": "0x" + "1" * 40}]
        resolver._get_trending_coingecko = lambda chain, limit: sentinel

        assert resolver.get_trending("ethereum", 5) == sentinel

    def test_cmc_results_win_when_present(self, monkeypatch):
        import ticker_resolver as tr

        cmc_tokens = [{"symbol": "BBB", "address": "0x" + "2" * 40}]

        class FullCMC:
            def get_trending(self, chain, limit):
                return cmc_tokens

        monkeypatch.setattr(tr, "get_cmc_client", lambda: FullCMC())

        resolver = TickerResolver()
        resolver._get_trending_coingecko = lambda chain, limit: [{"symbol": "WRONG"}]

        assert resolver.get_trending("ethereum", 5) == cmc_tokens


class TestCoinGeckoTrendingHonesty:
    """The CoinGecko fallback must not fabricate fields (v1 invented
    liquidity as volume*0.1 and a hardcoded riskScore of 50)."""

    COIN_DATA = {
        "symbol": "abc",
        "name": "ABC Token",
        "platforms": {"ethereum": "0x" + "3" * 40},
        "market_data": {
            "current_price": {"usd": 1.5},
            "price_change_percentage_24h": 4.2,
            "total_volume": {"usd": 9_000_000},
            "market_cap": {"usd": 120_000_000},
            "fully_diluted_valuation": {"usd": 150_000_000},
            "total_supply": 1_000_000,
            "circulating_supply": 900_000,
        },
    }

    def test_no_fabricated_liquidity_or_exchanges(self):
        token = TickerResolver()._cg_trending_token(self.COIN_DATA, "ethereum")
        assert token.get("liquidity") is None
        assert "exchanges" not in token

    def test_risk_score_computed_from_real_fields(self):
        token = TickerResolver()._cg_trending_token(self.COIN_DATA, "ethereum")
        assert token["riskScore"] is not None
        assert 0 <= token["riskScore"] <= 100

    def test_returns_none_without_address_on_chain(self):
        coin = dict(self.COIN_DATA, platforms={})
        assert TickerResolver()._cg_trending_token(coin, "ethereum") is None


class TestMultiChainTrendingToken:
    def test_base_and_arbitrum_platform_mapping(self):
        resolver = TickerResolver()
        for chain, platform_key in (("base", "base"), ("arbitrum", "arbitrum-one")):
            coin = {
                "symbol": "abc",
                "name": "ABC",
                "platforms": {platform_key: "0x" + "5" * 40},
                "market_data": {
                    "current_price": {"usd": 1.0},
                    "total_volume": {"usd": 1_000_000},
                    "market_cap": {"usd": 10_000_000},
                },
            }
            token = resolver._cg_trending_token(coin, chain)
            assert token is not None, chain
            assert token["address"] == "0x" + "5" * 40
