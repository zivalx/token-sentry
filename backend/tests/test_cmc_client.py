"""CMC client tests: no fabricated data in trending results."""
from cmc_client import CMCClient


def make_coin(num_market_pairs=7, market_cap=50_000_000_000):
    return {
        "id": 1,
        "symbol": "TEST",
        "name": "Test Token",
        "cmc_rank": 42,
        "num_market_pairs": num_market_pairs,
        "total_supply": 1_000_000,
        "circulating_supply": 900_000,
        "platform": {"name": "Ethereum", "token_address": "0x" + "2" * 40},
        "quote": {
            "USD": {
                "price": 1.23,
                "volume_24h": 5_000_000,
                "market_cap": market_cap,
                "percent_change_24h": 3.5,
                "fully_diluted_market_cap": 60_000_000_000,
            }
        },
    }


class TestNoFabricatedData:
    """A due-diligence tool must never present invented data as observed data.

    Bug: exchange names were guessed from market cap and liquidity was
    invented as volume * 0.2.
    """

    def test_exchange_count_comes_from_cmc_not_market_cap_guess(self):
        client = CMCClient(api_key="unused")
        result = client._process_coins([make_coin(num_market_pairs=7)], "ethereum", 10)[0]
        assert result["exchangeCount"] == 7

    def test_no_invented_exchange_names(self):
        client = CMCClient(api_key="unused")
        result = client._process_coins([make_coin(market_cap=50_000_000_000)], "ethereum", 10)[0]
        assert result.get("exchanges") in (None, [])

    def test_no_invented_liquidity(self):
        client = CMCClient(api_key="unused")
        result = client._process_coins([make_coin()], "ethereum", 10)[0]
        assert result.get("liquidity") is None
