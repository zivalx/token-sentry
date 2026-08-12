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
