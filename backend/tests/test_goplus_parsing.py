"""GoPlus response parsing must route trading-safety flags to LiquidityMetrics.

Bug: honeypot/can-sell signals were stuffed into SecurityMetrics.known_vulnerabilities
as strings, so the scorer's -50 honeypot penalty never fired.
"""
from data_fetchers import GoPlusSecurityFetcher


HONEYPOT_RESULT = {
    "is_honeypot": "1",
    "cannot_sell_all": "1",
    "buy_tax": "0.05",
    "sell_tax": "0.12",
    "is_proxy": "0",
    "is_mintable": "1",
    "hidden_owner": "1",
    "selfdestruct": "0",
    "can_take_back_ownership": "0",
    "is_open_source": "1",
    "owner_address": "0x" + "a" * 40,
    "holder_count": "1523",
    "is_blacklisted": "0",
}

CLEAN_RESULT = {
    "is_honeypot": "0",
    "cannot_sell_all": "0",
    "buy_tax": "0",
    "sell_tax": "0",
    "is_proxy": "0",
    "is_mintable": "0",
    "hidden_owner": "0",
    "selfdestruct": "0",
    "can_take_back_ownership": "0",
    "is_open_source": "1",
}


class TestGoPlusParsing:
    def test_honeypot_flag_lands_on_liquidity_metrics(self):
        parsed = GoPlusSecurityFetcher().parse_result(HONEYPOT_RESULT)
        assert parsed.liquidity.honeypot_risk is True
        assert parsed.liquidity.can_sell is False

    def test_taxes_are_parsed_as_percentages(self):
        parsed = GoPlusSecurityFetcher().parse_result(HONEYPOT_RESULT)
        assert parsed.liquidity.buy_tax == 5.0
        assert parsed.liquidity.sell_tax == 12.0

    def test_contract_flags_land_on_onchain_metrics(self):
        parsed = GoPlusSecurityFetcher().parse_result(HONEYPOT_RESULT)
        assert parsed.onchain.mintable is True
        assert parsed.onchain.source_verified is True

    def test_security_vulnerabilities_still_collected(self):
        parsed = GoPlusSecurityFetcher().parse_result(HONEYPOT_RESULT)
        assert any("hidden owner" in v.lower() for v in parsed.security.known_vulnerabilities)

    def test_clean_token_has_no_honeypot_risk(self):
        parsed = GoPlusSecurityFetcher().parse_result(CLEAN_RESULT)
        assert parsed.liquidity.honeypot_risk is False
        assert parsed.security.known_vulnerabilities == []


class TestGoPlusRequestFormat:
    def test_chain_id_is_a_path_segment(self):
        """Found in live verification: GoPlus expects
        /token_security/{chain_id}?contract_addresses=... — passing chain_id
        as a query param 404s, so the fetcher never returned data."""
        fetcher = GoPlusSecurityFetcher()
        captured = {}

        def fake_request(url, params=None, **kwargs):
            captured["url"] = url
            captured["params"] = params or {}
            return {"result": {}}

        fetcher._request_with_retry = fake_request
        fetcher.fetch("0x" + "a" * 40, "ethereum")

        assert captured["url"].rstrip("/").endswith("/token_security/1")
        assert "chain_id" not in captured["params"]
        assert captured["params"]["contract_addresses"] == "0x" + "a" * 40


HOLDERS_RESULT = {
    "is_honeypot": "0",
    "holder_count": "5000",
    "holders": [
        {"address": "0x" + "1" * 40, "percent": "0.32", "is_locked": 0},
        {"address": "0x" + "2" * 40, "percent": "0.10", "is_locked": 0},
        {"address": "0x" + "3" * 40, "percent": "0.05", "is_locked": 0},
        {"address": "0x" + "4" * 40, "percent": "0.02", "is_locked": 0},
    ],
    "lp_holders": [
        {"address": "0x" + "a" * 40, "percent": "0.70", "is_locked": 1},
        {"address": "0x" + "b" * 40, "percent": "0.25", "is_locked": 0},
        {"address": "0x" + "c" * 40, "percent": "0.05", "is_locked": 1},
    ],
}


class TestGoPlusHolderConcentration:
    """GoPlus's token_security response includes top holders — the strongest
    rug signal after honeypot, previously dropped on the floor."""

    def test_top_holder_percentages(self):
        parsed = GoPlusSecurityFetcher().parse_result(HOLDERS_RESULT)
        assert parsed.onchain.top_1_holder_pct == 32.0
        assert parsed.onchain.top_3_holder_pct == 47.0
        assert parsed.onchain.top_10_holder_pct == 49.0

    def test_no_holder_data_means_none_not_zero(self):
        parsed = GoPlusSecurityFetcher().parse_result(CLEAN_RESULT)
        assert parsed.onchain.top_1_holder_pct is None
        assert parsed.onchain.top_10_holder_pct is None


class TestGoPlusLiquidityLock:
    """lp_holders carry is_locked flags (lockers and burn addresses)."""

    def test_locked_percentage_summed_from_locked_lp_holders(self):
        parsed = GoPlusSecurityFetcher().parse_result(HOLDERS_RESULT)
        assert parsed.liquidity.liquidity_locked_pct == 75.0
        assert parsed.liquidity.liquidity_locked is True

    def test_zero_locked_is_false(self):
        result = dict(HOLDERS_RESULT, lp_holders=[
            {"address": "0x" + "a" * 40, "percent": "1.0", "is_locked": 0},
        ])
        parsed = GoPlusSecurityFetcher().parse_result(result)
        assert parsed.liquidity.liquidity_locked is False
        assert parsed.liquidity.liquidity_locked_pct == 0.0

    def test_no_lp_data_means_unknown(self):
        parsed = GoPlusSecurityFetcher().parse_result(CLEAN_RESULT)
        assert parsed.liquidity.liquidity_locked is None
        assert parsed.liquidity.liquidity_locked_pct is None

    def test_lp_top_holder_concentration(self):
        parsed = GoPlusSecurityFetcher().parse_result(HOLDERS_RESULT)
        assert parsed.liquidity.lp_top_1_holder_pct == 70.0
