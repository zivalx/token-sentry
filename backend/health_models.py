"""
Enhanced Token Health Data Models

Comprehensive data structures for holistic token health evaluation.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level classification"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AuditQuality(str, Enum):
    """Security audit quality ratings"""
    NONE = "none"
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    ELITE = "elite"


@dataclass
class MarketMetrics:
    """Market and price-related metrics"""
    symbol: str
    name: Optional[str] = None
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    fdv: Optional[float] = None  # Fully diluted valuation
    volume_24h: Optional[float] = None
    volume_7d: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_7d: Optional[float] = None
    price_change_30d: Optional[float] = None
    price_30d_volatility: Optional[float] = None  # Standard deviation
    ath_price: Optional[float] = None
    ath_date: Optional[str] = None
    ath_change_pct: Optional[float] = None
    exchanges_listed: Optional[int] = None
    cmc_rank: Optional[int] = None
    coingecko_rank: Optional[int] = None


@dataclass
class OnChainMetrics:
    """On-chain and smart contract metrics"""
    contract_address: str
    chain: str = "ethereum"
    contract_age_days: Optional[int] = None
    contract_created_at: Optional[str] = None
    source_verified: Optional[bool] = None
    proxy_contract: Optional[bool] = None
    implementation_address: Optional[str] = None
    owner_address: Optional[str] = None
    owner_renounced: Optional[bool] = None
    owner_has_admin: Optional[bool] = None
    pausable: Optional[bool] = None
    mintable: Optional[bool] = None
    burnable: Optional[bool] = None
    blacklist_function: Optional[bool] = None
    whitelist_function: Optional[bool] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    burned_tokens: Optional[float] = None
    holders_count: Optional[int] = None
    top_1_holder_pct: Optional[float] = None
    top_3_holder_pct: Optional[float] = None
    top_10_holder_pct: Optional[float] = None
    top_50_holder_pct: Optional[float] = None
    unique_wallets_24h: Optional[int] = None
    unique_wallets_7d: Optional[int] = None
    unique_wallets_30d: Optional[int] = None
    tx_count_24h: Optional[int] = None
    tx_count_7d: Optional[int] = None
    tx_count_30d: Optional[int] = None
    transfer_count_total: Optional[int] = None
    recent_large_transfers: Optional[int] = None  # >5% supply
    recent_minting: Optional[float] = None  # % of supply
    compiler_version: Optional[str] = None
    optimization_enabled: Optional[bool] = None


@dataclass
class LiquidityMetrics:
    """Liquidity and trading metrics"""
    main_dex: Optional[str] = None
    main_pool_address: Optional[str] = None
    main_pool_liquidity_usd: Optional[float] = None
    total_liquidity_usd: Optional[float] = None
    liquidity_locked: Optional[bool] = None
    liquidity_locked_pct: Optional[float] = None
    liquidity_lock_until: Optional[str] = None
    lp_holders_count: Optional[int] = None
    lp_top_1_holder_pct: Optional[float] = None
    lp_top_10_holder_pct: Optional[float] = None
    tvl_current: Optional[float] = None
    tvl_7d_delta: Optional[float] = None
    tvl_30d_delta: Optional[float] = None
    liquidity_to_mcap_ratio: Optional[float] = None
    buy_tax: Optional[float] = None
    sell_tax: Optional[float] = None
    transfer_tax: Optional[float] = None
    max_tx_amount: Optional[float] = None
    max_wallet_amount: Optional[float] = None
    slippage_1k: Optional[float] = None  # Slippage for $1k trade
    slippage_10k: Optional[float] = None
    slippage_100k: Optional[float] = None
    honeypot_risk: Optional[bool] = None
    can_buy: Optional[bool] = None
    can_sell: Optional[bool] = None


@dataclass
class SecurityMetrics:
    """Security and audit metrics"""
    audit_exists: Optional[bool] = None
    audit_date: Optional[str] = None
    audit_firm: Optional[str] = None
    audit_quality: Optional[AuditQuality] = None
    audit_score: Optional[float] = None
    audit_url: Optional[str] = None
    exploits_reported: Optional[int] = None
    exploit_history: Optional[List[Dict]] = field(default_factory=list)
    bug_bounty_active: Optional[bool] = None
    bug_bounty_amount: Optional[float] = None
    certik_score: Optional[float] = None
    rugdoc_review: Optional[str] = None
    known_vulnerabilities: Optional[List[str]] = field(default_factory=list)
    security_contacts: Optional[List[str]] = field(default_factory=list)
    multisig_enabled: Optional[bool] = None
    timelock_enabled: Optional[bool] = None
    emergency_pause: Optional[bool] = None


@dataclass
class SocialMetrics:
    """Social media and community metrics"""
    twitter_handle: Optional[str] = None
    twitter_followers: Optional[int] = None
    twitter_following: Optional[int] = None
    twitter_tweets: Optional[int] = None
    twitter_engagement_ratio: Optional[float] = None  # Likes+RT / followers
    twitter_created_at: Optional[str] = None
    twitter_verified: Optional[bool] = None
    telegram_group: Optional[str] = None
    telegram_members: Optional[int] = None
    telegram_active_members_24h: Optional[int] = None
    discord_members: Optional[int] = None
    discord_online_members: Optional[int] = None
    reddit_subscribers: Optional[int] = None
    reddit_active_users: Optional[int] = None
    github_repo: Optional[str] = None
    github_stars: Optional[int] = None
    github_forks: Optional[int] = None
    github_commits_30d: Optional[int] = None
    github_commits_90d: Optional[int] = None
    github_contributors: Optional[int] = None
    github_last_commit: Optional[str] = None
    github_issues_open: Optional[int] = None
    github_issues_closed: Optional[int] = None
    sentiment_score: Optional[float] = None  # -1 to 1
    social_dominance: Optional[float] = None  # % of total crypto social volume


@dataclass
class TeamMetrics:
    """Team and project transparency metrics"""
    team_public: Optional[bool] = None
    team_size: Optional[int] = None
    team_linkedin_profiles: Optional[List[str]] = field(default_factory=list)
    founder_reputation: Optional[str] = None
    previous_projects: Optional[List[str]] = field(default_factory=list)
    previous_exits: Optional[List[Dict]] = field(default_factory=list)
    legal_entity: Optional[bool] = None
    legal_entity_name: Optional[str] = None
    legal_jurisdiction: Optional[str] = None
    whitepaper_exists: Optional[bool] = None
    whitepaper_url: Optional[str] = None
    roadmap_exists: Optional[bool] = None
    roadmap_url: Optional[str] = None
    website_url: Optional[str] = None
    website_ssl: Optional[bool] = None
    website_age_days: Optional[int] = None
    documentation_quality: Optional[str] = None  # poor, basic, good, excellent
    regular_updates: Optional[bool] = None
    last_update_days_ago: Optional[int] = None


@dataclass
class UtilityMetrics:
    """Adoption, utility, and usage metrics"""
    use_case: Optional[str] = None
    use_case_category: Optional[str] = None  # DeFi, Gaming, NFT, etc.
    protocol_usage_score: Optional[float] = None
    active_users_24h: Optional[int] = None
    active_users_7d: Optional[int] = None
    active_users_30d: Optional[int] = None
    transactions_per_user_30d: Optional[float] = None
    revenue_24h: Optional[float] = None
    revenue_7d: Optional[float] = None
    revenue_30d: Optional[float] = None
    revenue_per_user: Optional[float] = None
    fees_generated_24h: Optional[float] = None
    fees_to_holders_pct: Optional[float] = None
    staking_enabled: Optional[bool] = None
    staking_apy: Optional[float] = None
    total_staked: Optional[float] = None
    staking_participation_rate: Optional[float] = None
    governance_enabled: Optional[bool] = None
    proposals_count: Optional[int] = None
    voter_participation_rate: Optional[float] = None
    partnerships: Optional[List[str]] = field(default_factory=list)
    integrations: Optional[List[str]] = field(default_factory=list)
    exchange_listings: Optional[List[str]] = field(default_factory=list)


@dataclass
class CategoryScore:
    """Score for a specific category with breakdown"""
    category: str
    score: float  # 0-100
    weight: float  # 0-1
    weighted_score: float
    factors: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)


@dataclass
class TokenHealthScore:
    """Comprehensive token health score with breakdown"""
    overall_score: float  # 0-100
    risk_level: RiskLevel
    category_scores: List[CategoryScore] = field(default_factory=list)
    confidence: float = 0.0  # 0-1, based on data completeness
    data_completeness: float = 0.0  # 0-1, % of fields populated
    red_flags: List[str] = field(default_factory=list)
    yellow_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TokenHealthData:
    """Complete token health data structure"""
    contract_address: str
    chain: str
    market: Optional[MarketMetrics] = None
    onchain: Optional[OnChainMetrics] = None
    liquidity: Optional[LiquidityMetrics] = None
    security: Optional[SecurityMetrics] = None
    social: Optional[SocialMetrics] = None
    team: Optional[TeamMetrics] = None
    utility: Optional[UtilityMetrics] = None
    health_score: Optional[TokenHealthScore] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, handling nested dataclasses"""
        return asdict(self)

    def get_field_count(self) -> int:
        """Count populated fields across all metrics"""
        count = 0
        total = 0

        for metrics_obj in [self.market, self.onchain, self.liquidity,
                           self.security, self.social, self.team, self.utility]:
            if metrics_obj:
                for key, value in asdict(metrics_obj).items():
                    total += 1
                    if value is not None and value != [] and value != {}:
                        count += 1

        return count, total

    def calculate_completeness(self) -> float:
        """Calculate data completeness ratio"""
        populated, total = self.get_field_count()
        return populated / total if total > 0 else 0.0


# Default scoring weights for each category
DEFAULT_CATEGORY_WEIGHTS = {
    "market": 0.20,         # 20% - Price stability, volume, liquidity
    "onchain": 0.15,        # 15% - Holder distribution, contract age
    "liquidity": 0.15,      # 15% - Pool depth, locked liquidity
    "security": 0.15,       # 15% - Audits, exploits, vulnerabilities
    "social": 0.10,         # 10% - Community engagement
    "team": 0.10,           # 10% - Transparency, track record
    "utility": 0.15,        # 15% - Real usage, revenue, adoption
}


# Risk level thresholds
RISK_THRESHOLDS = {
    (80, 100): RiskLevel.VERY_LOW,
    (60, 80): RiskLevel.LOW,
    (40, 60): RiskLevel.MODERATE,
    (20, 40): RiskLevel.HIGH,
    (0, 20): RiskLevel.CRITICAL,
}


def get_risk_level(score: float) -> RiskLevel:
    """Determine risk level from overall health score"""
    for (min_score, max_score), level in RISK_THRESHOLDS.items():
        if min_score <= score <= max_score:
            return level
    return RiskLevel.CRITICAL
