"""
Token Health Scoring Engine

Implements weighted scoring across 7 categories:
- Market (20%): Price stability, volume, market cap
- On-chain (15%): Holder distribution, contract age, supply
- Liquidity (15%): Pool depth, locked liquidity, slippage
- Security (15%): Audits, vulnerabilities, exploits
- Social (10%): Community engagement, followers
- Team (10%): Transparency, track record
- Utility (15%): Real usage, revenue, adoption
"""

import logging
import math
from typing import Optional, List, Dict, Tuple
from datetime import datetime

from health_models import (
    TokenHealthData, TokenHealthScore, CategoryScore,
    MarketMetrics, OnChainMetrics, LiquidityMetrics,
    SecurityMetrics, SocialMetrics, TeamMetrics, UtilityMetrics,
    DEFAULT_CATEGORY_WEIGHTS, get_risk_level, has_data
)

logger = logging.getLogger(__name__)


class HealthScorer:
    """Calculate comprehensive token health scores"""

    def __init__(self, category_weights: Optional[Dict[str, float]] = None):
        self.weights = category_weights or DEFAULT_CATEGORY_WEIGHTS

    def score_token(self, health_data: TokenHealthData) -> TokenHealthScore:
        """Calculate overall health score from token data"""

        category_scores = []

        # Score each category — a metrics object with no populated fields means
        # "nothing fetched" and must not be scored as neutral-50
        if has_data(health_data.market, ignore={"symbol", "name"}):
            category_scores.append(self._score_market(health_data.market))

        if has_data(health_data.onchain, ignore={"contract_address", "chain"}):
            category_scores.append(self._score_onchain(health_data.onchain))

        if has_data(health_data.liquidity):
            category_scores.append(self._score_liquidity(health_data.liquidity))

        if has_data(health_data.security):
            category_scores.append(self._score_security(health_data.security))

        if has_data(health_data.social):
            category_scores.append(self._score_social(health_data.social))

        if has_data(health_data.team):
            category_scores.append(self._score_team(health_data.team))

        if has_data(health_data.utility):
            category_scores.append(self._score_utility(health_data.utility))

        # Calculate weighted overall score
        overall_score = sum(cs.weighted_score for cs in category_scores)

        # Normalize if not all categories are present
        total_weight = sum(cs.weight for cs in category_scores)
        if total_weight > 0 and total_weight < 1.0:
            overall_score = overall_score / total_weight

        # Clamp before ANY derived value — an unclamped 104 maps to no risk
        # threshold and used to fall through to CRITICAL
        overall_score = min(100.0, max(0.0, overall_score))

        # Collect flags
        red_flags, yellow_flags, green_flags = self._collect_flags(category_scores)

        # Generate recommendations
        recommendations = self._generate_recommendations(category_scores, overall_score)

        # Calculate confidence based on data completeness
        data_completeness = health_data.calculate_completeness()
        confidence = self._calculate_confidence(data_completeness, len(category_scores))

        health_score = TokenHealthScore(
            overall_score=overall_score,
            risk_level=get_risk_level(overall_score),
            category_scores=category_scores,
            confidence=confidence,
            data_completeness=data_completeness,
            red_flags=red_flags,
            yellow_flags=yellow_flags,
            green_flags=green_flags,
            recommendations=recommendations
        )

        return health_score

    # ========================================================================
    # CATEGORY SCORING METHODS
    # ========================================================================

    def _score_market(self, metrics: MarketMetrics) -> CategoryScore:
        """Score market and price metrics (20% of total)"""
        score = 50.0  # Start neutral
        factors = {}
        issues = []
        strengths = []

        # Market cap scoring (30 points max)
        if metrics.market_cap:
            if metrics.market_cap > 1_000_000_000:  # >$1B
                score += 30
                factors["market_cap"] = 30
                strengths.append("Large market cap ($1B+)")
            elif metrics.market_cap > 100_000_000:  # >$100M
                score += 20
                factors["market_cap"] = 20
                strengths.append("Significant market cap ($100M+)")
            elif metrics.market_cap > 10_000_000:  # >$10M
                score += 10
                factors["market_cap"] = 10
            elif metrics.market_cap < 1_000_000:  # <$1M
                score -= 10
                factors["market_cap"] = -10
                issues.append("Very low market cap (<$1M)")
            else:
                factors["market_cap"] = 0

        # Volume scoring (20 points max)
        if metrics.volume_24h and metrics.market_cap:
            volume_to_mcap = metrics.volume_24h / metrics.market_cap
            if 0.05 <= volume_to_mcap <= 0.5:  # Healthy 5-50%
                score += 20
                factors["volume"] = 20
                strengths.append("Healthy trading volume")
            elif volume_to_mcap > 1.0:  # Very high volume — a risk signal, not a strength
                score -= 10
                factors["volume"] = -10
                issues.append("Unusually high volume (possible manipulation)")
            elif volume_to_mcap < 0.01:  # Very low volume
                score -= 15
                factors["volume"] = -15
                issues.append("Very low trading volume")
            else:
                factors["volume"] = 5

        # Price volatility scoring (20 points max)
        if metrics.price_30d_volatility is not None:
            if metrics.price_30d_volatility < 20:  # Low volatility
                score += 20
                factors["volatility"] = 20
                strengths.append("Low price volatility")
            elif metrics.price_30d_volatility < 50:  # Moderate
                score += 10
                factors["volatility"] = 10
            elif metrics.price_30d_volatility > 100:  # Very high
                score -= 15
                factors["volatility"] = -15
                issues.append("Extreme price volatility")
            else:
                factors["volatility"] = 0

        # Price trend scoring (15 points max)
        if metrics.price_change_7d is not None:
            if -10 <= metrics.price_change_7d <= 30:  # Stable/modest growth
                score += 15
                factors["price_trend"] = 15
                strengths.append("Stable price trend")
            elif metrics.price_change_7d < -30:  # Sharp decline
                score -= 10
                factors["price_trend"] = -10
                issues.append("Sharp recent price decline")
            elif metrics.price_change_7d > 100:  # Parabolic pump
                score -= 5
                factors["price_trend"] = -5
                issues.append("Parabolic price pump (unsustainable)")
            else:
                factors["price_trend"] = 5

        # Exchange listings (15 points max)
        if metrics.exchanges_listed:
            if metrics.exchanges_listed >= 10:
                score += 15
                factors["listings"] = 15
                strengths.append(f"Listed on {metrics.exchanges_listed} exchanges")
            elif metrics.exchanges_listed >= 5:
                score += 10
                factors["listings"] = 10
            elif metrics.exchanges_listed == 1:
                score -= 5
                factors["listings"] = -5
                issues.append("Only listed on 1 exchange")
            else:
                factors["listings"] = 5

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["market"]

        return CategoryScore(
            category="market",
            score=score,
            weight=self.weights["market"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_onchain(self, metrics: OnChainMetrics) -> CategoryScore:
        """Score on-chain metrics (15% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Contract age (25 points max)
        if metrics.contract_age_days:
            if metrics.contract_age_days > 365:  # >1 year
                score += 25
                factors["age"] = 25
                strengths.append(f"Mature contract ({metrics.contract_age_days} days)")
            elif metrics.contract_age_days > 180:  # >6 months
                score += 15
                factors["age"] = 15
            elif metrics.contract_age_days < 7:  # <1 week — narrowest bucket first
                score -= 25
                factors["age"] = -25
                issues.append("Extremely new contract (<7 days)")
            elif metrics.contract_age_days < 30:  # <1 month
                score -= 15
                factors["age"] = -15
                issues.append("Very new contract (<30 days)")
            else:
                factors["age"] = 5

        # Source verification (20 points max)
        if metrics.source_verified is True:
            score += 20
            factors["verified"] = 20
            strengths.append("Contract source code verified")
        elif metrics.source_verified is False:
            score -= 25
            factors["verified"] = -25
            issues.append("Contract NOT verified (major red flag)")

        # Holder concentration (30 points max)
        concentration_score = 0
        if metrics.top_10_holder_pct:
            if metrics.top_10_holder_pct < 30:  # Very distributed
                concentration_score = 30
                strengths.append("Excellent holder distribution")
            elif metrics.top_10_holder_pct < 50:  # Good
                concentration_score = 20
                strengths.append("Good holder distribution")
            elif metrics.top_10_holder_pct < 70:  # Moderate
                concentration_score = 5
            elif metrics.top_10_holder_pct < 85:  # High
                concentration_score = -15
                issues.append("High holder concentration")
            else:  # Very high
                concentration_score = -25
                issues.append("Extreme holder concentration (>85%)")

            score += concentration_score
            factors["concentration"] = concentration_score

        # Top 1 holder check
        if metrics.top_1_holder_pct and metrics.top_1_holder_pct > 40:
            score -= 15
            factors["top_holder"] = -15
            issues.append(f"Single wallet holds {metrics.top_1_holder_pct:.1f}%")

        # Holder count (15 points max)
        if metrics.holders_count:
            if metrics.holders_count > 10000:
                score += 15
                factors["holders"] = 15
                strengths.append(f"{metrics.holders_count:,} holders")
            elif metrics.holders_count > 1000:
                score += 10
                factors["holders"] = 10
            elif metrics.holders_count < 100:
                score -= 10
                factors["holders"] = -10
                issues.append(f"Very few holders ({metrics.holders_count})")
            else:
                factors["holders"] = 0

        # Owner/admin privileges (20 points)
        if metrics.owner_renounced is True:
            score += 20
            factors["ownership"] = 20
            strengths.append("Ownership renounced")
        elif metrics.owner_has_admin is True:
            score -= 15
            factors["ownership"] = -15
            issues.append("Owner has admin privileges")

        # Proxy contract (cautionary)
        if metrics.proxy_contract is True:
            score -= 10
            factors["proxy"] = -10
            issues.append("Proxy contract (upgradeable)")

        # Suspicious features
        if metrics.blacklist_function is True:
            score -= 15
            factors["blacklist"] = -15
            issues.append("Blacklist function present")

        if metrics.mintable is True and metrics.owner_has_admin is True:
            score -= 10
            factors["mintable"] = -10
            issues.append("Mintable with admin control")

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["onchain"]

        return CategoryScore(
            category="onchain",
            score=score,
            weight=self.weights["onchain"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_liquidity(self, metrics: LiquidityMetrics) -> CategoryScore:
        """Score liquidity metrics (15% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Total liquidity (40 points max)
        if metrics.total_liquidity_usd:
            if metrics.total_liquidity_usd > 1_000_000:  # >$1M
                score += 40
                factors["liquidity"] = 40
                strengths.append(f"Strong liquidity (${metrics.total_liquidity_usd:,.0f})")
            elif metrics.total_liquidity_usd > 100_000:  # >$100k
                score += 25
                factors["liquidity"] = 25
                strengths.append("Good liquidity")
            elif metrics.total_liquidity_usd > 10_000:  # >$10k
                score += 10
                factors["liquidity"] = 10
            elif metrics.total_liquidity_usd < 5_000:  # <$5k
                score -= 20
                factors["liquidity"] = -20
                issues.append("Very low liquidity (<$5k)")
            else:
                factors["liquidity"] = 0

        # Liquidity locked (30 points max)
        if metrics.liquidity_locked is True:
            lock_score = 30
            if metrics.liquidity_locked_pct and metrics.liquidity_locked_pct > 80:
                lock_score = 30
                strengths.append(f"Liquidity {metrics.liquidity_locked_pct:.0f}% locked")
            elif metrics.liquidity_locked_pct and metrics.liquidity_locked_pct > 50:
                lock_score = 20
                strengths.append("Majority liquidity locked")
            else:
                lock_score = 15
                strengths.append("Liquidity partially locked")
            score += lock_score
            factors["locked"] = lock_score
        elif metrics.liquidity_locked is False:
            score -= 25
            factors["locked"] = -25
            issues.append("Liquidity NOT locked (rug risk)")

        # Buy/sell taxes (20 points)
        total_tax = (metrics.buy_tax or 0) + (metrics.sell_tax or 0)
        if total_tax == 0:
            score += 20
            factors["taxes"] = 20
            strengths.append("No buy/sell taxes")
        elif total_tax < 10:
            score += 10
            factors["taxes"] = 10
        elif total_tax > 20:
            score -= 15
            factors["taxes"] = -15
            issues.append(f"High taxes ({total_tax}%)")
        else:
            factors["taxes"] = 0

        # Honeypot check (critical)
        if metrics.honeypot_risk is True or metrics.can_sell is False:
            score -= 50
            factors["honeypot"] = -50
            issues.append("HONEYPOT DETECTED - Cannot sell!")
        elif metrics.can_buy is True and metrics.can_sell is True:
            score += 10
            factors["tradeable"] = 10
            strengths.append("Verified tradeable")

        # Slippage check
        if metrics.slippage_10k and metrics.slippage_10k > 20:
            score -= 15
            factors["slippage"] = -15
            issues.append(f"High slippage ({metrics.slippage_10k}%)")
        elif metrics.slippage_10k and metrics.slippage_10k < 5:
            score += 10
            factors["slippage"] = 10
            strengths.append("Low slippage")

        # LP holder concentration
        if metrics.lp_top_1_holder_pct and metrics.lp_top_1_holder_pct > 50:
            score -= 10
            factors["lp_concentration"] = -10
            issues.append("LP highly concentrated")

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["liquidity"]

        return CategoryScore(
            category="liquidity",
            score=score,
            weight=self.weights["liquidity"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_security(self, metrics: SecurityMetrics) -> CategoryScore:
        """Score security metrics (15% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Audit presence and quality (50 points max)
        if metrics.audit_exists is True:
            if metrics.audit_quality == "elite":
                score += 50
                factors["audit"] = 50
                strengths.append(f"Elite audit by {metrics.audit_firm}")
            elif metrics.audit_quality == "comprehensive":
                score += 40
                factors["audit"] = 40
                strengths.append(f"Comprehensive audit by {metrics.audit_firm}")
            elif metrics.audit_quality == "standard":
                score += 30
                factors["audit"] = 30
                strengths.append(f"Standard audit by {metrics.audit_firm}")
            elif metrics.audit_quality == "basic":
                score += 20
                factors["audit"] = 20
                strengths.append("Basic audit completed")
            else:
                score += 15
                factors["audit"] = 15
                strengths.append("Audited")
        elif metrics.audit_exists is False:
            score -= 20
            factors["audit"] = -20
            issues.append("No security audit")

        # Exploit history (critical)
        if metrics.exploits_reported and metrics.exploits_reported > 0:
            exploit_penalty = min(40, metrics.exploits_reported * 15)
            score -= exploit_penalty
            factors["exploits"] = -exploit_penalty
            issues.append(f"{metrics.exploits_reported} exploit(s) reported")

        # Known vulnerabilities
        if metrics.known_vulnerabilities and len(metrics.known_vulnerabilities) > 0:
            vuln_count = len(metrics.known_vulnerabilities)
            vuln_penalty = min(30, vuln_count * 10)
            score -= vuln_penalty
            factors["vulnerabilities"] = -vuln_penalty
            issues.append(f"{vuln_count} known vulnerability(ies)")

        # Bug bounty program (20 points max)
        if metrics.bug_bounty_active is True:
            if metrics.bug_bounty_amount and metrics.bug_bounty_amount > 100000:
                score += 20
                factors["bug_bounty"] = 20
                strengths.append(f"Bug bounty: ${metrics.bug_bounty_amount:,.0f}")
            else:
                score += 15
                factors["bug_bounty"] = 15
                strengths.append("Bug bounty program active")

        # Security features (15 points max)
        security_features = 0
        if metrics.multisig_enabled is True:
            security_features += 5
            strengths.append("Multisig enabled")
        if metrics.timelock_enabled is True:
            security_features += 5
            strengths.append("Timelock enabled")
        if metrics.emergency_pause is True:
            security_features += 5
            strengths.append("Emergency pause available")

        score += security_features
        factors["security_features"] = security_features

        # CertiK score
        if metrics.certik_score:
            if metrics.certik_score > 80:
                score += 15
                factors["certik"] = 15
                strengths.append(f"CertiK score: {metrics.certik_score}")
            elif metrics.certik_score < 50:
                score -= 10
                factors["certik"] = -10
                issues.append(f"Low CertiK score: {metrics.certik_score}")

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["security"]

        return CategoryScore(
            category="security",
            score=score,
            weight=self.weights["security"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_social(self, metrics: SocialMetrics) -> CategoryScore:
        """Score social and community metrics (10% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Twitter following (30 points max)
        if metrics.twitter_followers:
            if metrics.twitter_followers > 100000:
                score += 30
                factors["twitter"] = 30
                strengths.append(f"{metrics.twitter_followers:,} Twitter followers")
            elif metrics.twitter_followers > 10000:
                score += 20
                factors["twitter"] = 20
            elif metrics.twitter_followers > 1000:
                score += 10
                factors["twitter"] = 10
            elif metrics.twitter_followers < 100:
                score -= 10
                factors["twitter"] = -10
                issues.append("Very few Twitter followers")
            else:
                factors["twitter"] = 0

        # Twitter engagement (20 points max)
        if metrics.twitter_engagement_ratio:
            if metrics.twitter_engagement_ratio > 0.05:  # >5%
                score += 20
                factors["engagement"] = 20
                strengths.append("High Twitter engagement")
            elif metrics.twitter_engagement_ratio > 0.02:  # >2%
                score += 10
                factors["engagement"] = 10
            elif metrics.twitter_engagement_ratio < 0.005:  # <0.5%
                score -= 10
                factors["engagement"] = -10
                issues.append("Low Twitter engagement")

        # Telegram community (20 points max)
        if metrics.telegram_members:
            if metrics.telegram_members > 10000:
                score += 20
                factors["telegram"] = 20
                strengths.append(f"{metrics.telegram_members:,} Telegram members")
            elif metrics.telegram_members > 1000:
                score += 10
                factors["telegram"] = 10
            elif metrics.telegram_members < 100:
                score -= 5
                factors["telegram"] = -5

        # GitHub activity (30 points max)
        github_score = 0
        if metrics.github_commits_30d:
            if metrics.github_commits_30d > 50:
                github_score += 15
                strengths.append("Very active development")
            elif metrics.github_commits_30d > 10:
                github_score += 10
                strengths.append("Active development")
            elif metrics.github_commits_30d == 0:
                github_score -= 10
                issues.append("No recent development activity")
            else:
                github_score += 5

        if metrics.github_stars:
            if metrics.github_stars > 1000:
                github_score += 15
            elif metrics.github_stars > 100:
                github_score += 10
            else:
                github_score += 5

        score += github_score
        factors["github"] = github_score

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["social"]

        return CategoryScore(
            category="social",
            score=score,
            weight=self.weights["social"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_team(self, metrics: TeamMetrics) -> CategoryScore:
        """Score team and transparency metrics (10% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Team public (30 points max)
        if metrics.team_public is True:
            score += 30
            factors["public_team"] = 30
            strengths.append("Public team identity")
        elif metrics.team_public is False:
            score -= 20
            factors["public_team"] = -20
            issues.append("Anonymous team")

        # Legal entity (20 points max)
        if metrics.legal_entity is True:
            score += 20
            factors["legal"] = 20
            strengths.append(f"Legal entity: {metrics.legal_entity_name}")
        elif metrics.legal_entity is False:
            score -= 10
            factors["legal"] = -10

        # Documentation (25 points max)
        doc_score = 0
        if metrics.whitepaper_exists is True:
            doc_score += 10
            strengths.append("Whitepaper available")
        else:
            doc_score -= 5
            issues.append("No whitepaper")

        if metrics.roadmap_exists is True:
            doc_score += 10
            strengths.append("Roadmap available")

        if metrics.documentation_quality == "excellent":
            doc_score += 15
        elif metrics.documentation_quality == "good":
            doc_score += 10
        elif metrics.documentation_quality == "poor":
            doc_score -= 5

        score += doc_score
        factors["documentation"] = doc_score

        # Team track record (25 points max)
        if metrics.previous_exits and len(metrics.previous_exits) > 0:
            successful_exits = sum(1 for e in metrics.previous_exits if e.get("success"))
            if successful_exits > 0:
                score += 25
                factors["track_record"] = 25
                strengths.append(f"{successful_exits} successful previous project(s)")
            else:
                score -= 15
                factors["track_record"] = -15
                issues.append("Previous failed projects")

        # Regular updates
        if metrics.regular_updates is True:
            score += 10
            factors["updates"] = 10
            strengths.append("Regular project updates")
        elif metrics.last_update_days_ago and metrics.last_update_days_ago > 90:
            score -= 10
            factors["updates"] = -10
            issues.append("No updates in 90+ days")

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["team"]

        return CategoryScore(
            category="team",
            score=score,
            weight=self.weights["team"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    def _score_utility(self, metrics: UtilityMetrics) -> CategoryScore:
        """Score utility and adoption metrics (15% of total)"""
        score = 50.0
        factors = {}
        issues = []
        strengths = []

        # Active users (35 points max)
        if metrics.active_users_30d:
            if metrics.active_users_30d > 10000:
                score += 35
                factors["users"] = 35
                strengths.append(f"{metrics.active_users_30d:,} active users")
            elif metrics.active_users_30d > 1000:
                score += 25
                factors["users"] = 25
                strengths.append("Strong user base")
            elif metrics.active_users_30d > 100:
                score += 15
                factors["users"] = 15
            elif metrics.active_users_30d < 10:
                score -= 15
                factors["users"] = -15
                issues.append("Very few active users")
            else:
                factors["users"] = 5

        # Revenue generation (30 points max)
        if metrics.revenue_30d:
            if metrics.revenue_30d > 100000:
                score += 30
                factors["revenue"] = 30
                strengths.append(f"${metrics.revenue_30d:,.0f} monthly revenue")
            elif metrics.revenue_30d > 10000:
                score += 20
                factors["revenue"] = 20
            elif metrics.revenue_30d > 1000:
                score += 10
                factors["revenue"] = 10
            elif metrics.revenue_30d < 100:
                score -= 10
                factors["revenue"] = -10
                issues.append("Minimal revenue generation")

        # Revenue per user (efficiency metric)
        if metrics.revenue_per_user and metrics.revenue_per_user > 10:
            score += 10
            factors["efficiency"] = 10
            strengths.append("High revenue per user")

        # Staking participation (15 points max)
        if metrics.staking_enabled is True:
            if metrics.staking_participation_rate and metrics.staking_participation_rate > 50:
                score += 15
                factors["staking"] = 15
                strengths.append(f"{metrics.staking_participation_rate}% staking rate")
            elif metrics.staking_participation_rate and metrics.staking_participation_rate > 20:
                score += 10
                factors["staking"] = 10
            else:
                score += 5
                factors["staking"] = 5

        # Governance participation (10 points max)
        if metrics.governance_enabled is True and metrics.voter_participation_rate:
            if metrics.voter_participation_rate > 30:
                score += 10
                factors["governance"] = 10
                strengths.append("Active governance participation")
            elif metrics.voter_participation_rate > 10:
                score += 5
                factors["governance"] = 5

        # Partnerships and integrations (20 points max)
        partnership_score = 0
        if metrics.partnerships:
            partnership_score += min(10, len(metrics.partnerships) * 2)
        if metrics.integrations:
            partnership_score += min(10, len(metrics.integrations) * 2)

        if partnership_score > 0:
            strengths.append(f"{len(metrics.partnerships or [])} partnerships")
            factors["partnerships"] = partnership_score
            score += partnership_score

        score = min(100.0, max(0.0, score))
        weighted_score = score * self.weights["utility"]

        return CategoryScore(
            category="utility",
            score=score,
            weight=self.weights["utility"],
            weighted_score=weighted_score,
            factors=factors,
            issues=issues,
            strengths=strengths
        )

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _collect_flags(
        self,
        category_scores: List[CategoryScore]
    ) -> Tuple[List[str], List[str], List[str]]:
        """Collect red, yellow, and green flags from category scores"""
        red_flags = []
        yellow_flags = []
        green_flags = []

        for cat_score in category_scores:
            # Red flags: critical issues
            for issue in cat_score.issues:
                if any(keyword in issue.lower() for keyword in [
                    "honeypot", "exploit", "not verified", "cannot sell",
                    "extremely", "major red flag"
                ]):
                    red_flags.append(f"[{cat_score.category.upper()}] {issue}")
                else:
                    yellow_flags.append(f"[{cat_score.category.upper()}] {issue}")

            # Green flags: significant strengths
            for strength in cat_score.strengths:
                if any(keyword in strength.lower() for keyword in [
                    "excellent", "strong", "elite", "verified", "locked",
                    "audit", "public team"
                ]):
                    green_flags.append(f"[{cat_score.category.upper()}] {strength}")

        return red_flags, yellow_flags, green_flags

    def _generate_recommendations(
        self,
        category_scores: List[CategoryScore],
        overall_score: float
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Find lowest scoring categories
        sorted_scores = sorted(category_scores, key=lambda x: x.score)

        for cat_score in sorted_scores[:3]:  # Top 3 improvement areas
            if cat_score.score < 50:
                if cat_score.category == "security":
                    recommendations.append("Get a professional security audit from a reputable firm")
                elif cat_score.category == "liquidity":
                    recommendations.append("Lock liquidity in a verified locker for at least 6 months")
                elif cat_score.category == "onchain":
                    recommendations.append("Improve holder distribution and verify contract source code")
                elif cat_score.category == "team":
                    recommendations.append("Increase transparency: reveal team, publish whitepaper and roadmap")
                elif cat_score.category == "social":
                    recommendations.append("Build community presence on Twitter, Telegram, and Discord")
                elif cat_score.category == "utility":
                    recommendations.append("Focus on real-world utility and user adoption")
                elif cat_score.category == "market":
                    recommendations.append("Build sustainable trading volume on multiple exchanges")

        # Overall score recommendations
        if overall_score < 40:
            recommendations.insert(0, "CAUTION: Multiple red flags detected. Avoid investing until issues are resolved.")
        elif overall_score < 60:
            recommendations.insert(0, "Exercise caution: Several areas need improvement before investment.")

        return recommendations[:5]  # Limit to top 5

    def _calculate_confidence(self, data_completeness: float, categories_present: int) -> float:
        """Calculate confidence score based on data availability"""
        # Base confidence from data completeness (70% weight)
        base_confidence = data_completeness * 0.7

        # Category coverage (30% weight) - ideal is all 7 categories
        category_confidence = (categories_present / 7) * 0.3

        return base_confidence + category_confidence
