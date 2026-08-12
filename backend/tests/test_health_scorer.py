"""Tests for the health scoring engine — targets bugs found in the 2026-08 review."""
import dataclasses

from health_models import (
    TokenHealthData, MarketMetrics, OnChainMetrics, LiquidityMetrics,
    TeamMetrics, UtilityMetrics,
)
from health_scorer import HealthScorer


def onchain(**kwargs) -> OnChainMetrics:
    return OnChainMetrics(contract_address="0x" + "1" * 40, **kwargs)


class TestContractAgeScoring:
    def test_extremely_new_contract_scores_lower_than_month_old(self):
        """A <7-day contract must be penalized harder than a <30-day one.

        Bug: the `< 30` branch shadowed the `< 7` branch, so the extreme-new
        penalty was unreachable.
        """
        scorer = HealthScorer()
        three_days = scorer._score_onchain(onchain(contract_age_days=3))
        twenty_days = scorer._score_onchain(onchain(contract_age_days=20))
        assert three_days.score < twenty_days.score

    def test_extremely_new_contract_flagged_as_extreme(self):
        scorer = HealthScorer()
        result = scorer._score_onchain(onchain(contract_age_days=3))
        assert any("7 days" in issue for issue in result.issues)


class TestVolumeScoring:
    def test_manipulation_signal_does_not_add_points(self):
        """Volume/mcap > 1.0 is flagged as possible manipulation — it must not
        simultaneously INCREASE the score."""
        scorer = HealthScorer()
        result = scorer._score_market(
            MarketMetrics(symbol="X", market_cap=1_000_000, volume_24h=2_000_000)
        )
        assert any("manipulation" in issue.lower() for issue in result.issues)
        assert result.factors["volume"] <= 0

    def test_suspicious_volume_scores_below_healthy_volume(self):
        scorer = HealthScorer()
        suspicious = scorer._score_market(
            MarketMetrics(symbol="X", market_cap=1_000_000, volume_24h=2_000_000)
        )
        healthy = scorer._score_market(
            MarketMetrics(symbol="X", market_cap=1_000_000, volume_24h=200_000)
        )
        assert suspicious.score < healthy.score


class TestEmptyCategories:
    """Empty metrics objects (all fields None) must not be scored as neutral-50.

    Bug: the pipeline always attached empty TeamMetrics()/UtilityMetrics(), which
    scored 50/100 at 25% combined weight and inflated confidence.
    """

    def _data_with_empty_categories(self) -> TokenHealthData:
        return TokenHealthData(
            contract_address="0x" + "1" * 40,
            chain="ethereum",
            market=MarketMetrics(symbol="X", market_cap=500_000_000, volume_24h=50_000_000),
            team=TeamMetrics(),        # nothing fetched
            utility=UtilityMetrics(),  # nothing fetched
        )

    def test_empty_categories_are_not_scored(self):
        score = HealthScorer().score_token(self._data_with_empty_categories())
        scored = {cs.category for cs in score.category_scores}
        assert "team" not in scored
        assert "utility" not in scored

    def test_empty_categories_do_not_inflate_confidence(self):
        with_empty = HealthScorer().score_token(self._data_with_empty_categories())
        without = HealthScorer().score_token(
            TokenHealthData(
                contract_address="0x" + "1" * 40,
                chain="ethereum",
                market=MarketMetrics(symbol="X", market_cap=500_000_000, volume_24h=50_000_000),
            )
        )
        assert with_empty.confidence == without.confidence


class TestHoneypotScoring:
    def test_honeypot_tanks_liquidity_score(self):
        scorer = HealthScorer()
        clean = scorer._score_liquidity(
            LiquidityMetrics(total_liquidity_usd=200_000, can_buy=True, can_sell=True)
        )
        honeypot = scorer._score_liquidity(
            LiquidityMetrics(total_liquidity_usd=200_000, honeypot_risk=True)
        )
        assert honeypot.score <= clean.score - 40
        assert any("honeypot" in issue.lower() for issue in honeypot.issues)


class TestScoreClamping:
    """Found in live verification: a category can accumulate a raw score >100
    (e.g. mega-cap with healthy volume and stable trend = 115). The weighted
    score and the risk level must be computed from CLAMPED values, otherwise
    overall_score=100 is reported as risk_level=critical (no threshold matches
    values above 100)."""

    def _mega_cap_data(self) -> TokenHealthData:
        return TokenHealthData(
            contract_address="0x" + "1" * 40,
            chain="ethereum",
            market=MarketMetrics(
                symbol="X",
                market_cap=2_000_000_000,
                volume_24h=200_000_000,
                price_change_7d=5.0,
            ),
            liquidity=LiquidityMetrics(total_liquidity_usd=20_000_000),
        )

    def test_weighted_score_uses_clamped_category_score(self):
        score = HealthScorer().score_token(self._mega_cap_data())
        for cs in score.category_scores:
            assert cs.weighted_score <= cs.weight * 100 + 1e-9

    def test_risk_level_matches_clamped_overall_score(self):
        score = HealthScorer().score_token(self._mega_cap_data())
        assert 80 <= score.overall_score <= 100
        assert score.risk_level.value == "very_low"


class TestLiquidityLockGrading:
    """With real locked percentages available (GoPlus lp_holders), grade by
    percentage: a 5%-locked pool must not earn the 'partially locked' bonus
    that was designed for meaningful locks."""

    def _score(self, locked, pct):
        return HealthScorer()._score_liquidity(
            LiquidityMetrics(
                total_liquidity_usd=200_000,
                liquidity_locked=locked,
                liquidity_locked_pct=pct,
            )
        )

    def test_tiny_lock_scores_no_better_than_unlocked_plus_epsilon(self):
        tiny = self._score(True, 5.0)
        mostly = self._score(True, 90.0)
        assert mostly.score - tiny.score >= 25

    def test_tiny_lock_is_flagged_not_praised(self):
        tiny = self._score(True, 5.0)
        assert not any("locked" in s.lower() for s in tiny.strengths)
        assert any("unlocked" in i.lower() or "locked" in i.lower() for i in tiny.issues)

    def test_unknown_taxes_are_not_rewarded_as_zero_taxes(self):
        """buy_tax/sell_tax of None means 'not fetched', not 'tax-free'."""
        unknown = HealthScorer()._score_liquidity(
            LiquidityMetrics(total_liquidity_usd=200_000)
        )
        assert "taxes" not in unknown.factors
        assert not any("tax" in s.lower() for s in unknown.strengths)
