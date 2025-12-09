"""
Token Health ETL Pipeline

Main orchestration pipeline that:
1. Fetches data from multiple sources
2. Transforms and normalizes data
3. Calculates health scores
4. Optionally generates LLM summaries
"""

import logging
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from health_models import (
    TokenHealthData, MarketMetrics, OnChainMetrics,
    LiquidityMetrics, SecurityMetrics, SocialMetrics,
    TeamMetrics, UtilityMetrics
)
from data_fetchers import DataFetcherRegistry
from health_scorer import HealthScorer

logger = logging.getLogger(__name__)


class TokenHealthPipeline:
    """
    Main ETL pipeline for comprehensive token health analysis

    Example usage:
        pipeline = TokenHealthPipeline.from_env()
        health_data = pipeline.analyze_token(
            contract="0x1234...",
            chain="ethereum",
            include_llm_summary=True
        )
        print(f"Health Score: {health_data.health_score.overall_score}")
    """

    def __init__(
        self,
        cmc_api_key: Optional[str] = None,
        etherscan_api_key: Optional[str] = None,
        alchemy_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        enable_cache: bool = True,
        cache_ttl: int = 600
    ):
        """
        Initialize the pipeline with API keys

        Args:
            cmc_api_key: CoinMarketCap API key
            etherscan_api_key: Etherscan API key
            alchemy_api_key: Alchemy API key
            github_token: GitHub personal access token
            anthropic_api_key: Anthropic API key for LLM summaries
            enable_cache: Enable caching of API responses
            cache_ttl: Cache time-to-live in seconds
        """
        self.enable_cache = enable_cache
        self.cache_ttl = cache_ttl
        self.anthropic_api_key = anthropic_api_key

        # Initialize fetcher registry
        self.registry = DataFetcherRegistry()

        # Register fetchers with available API keys
        if cmc_api_key:
            self.registry.register_market_fetchers(cmc_api_key=cmc_api_key)
        else:
            self.registry.register_market_fetchers()  # CoinGecko only

        if etherscan_api_key or alchemy_api_key:
            self.registry.register_onchain_fetchers(
                etherscan_api_key=etherscan_api_key,
                alchemy_api_key=alchemy_api_key
            )

        self.registry.register_liquidity_fetchers()
        self.registry.register_security_fetchers()

        if github_token:
            self.registry.register_social_fetchers(github_token=github_token)

        # Initialize scorer
        self.scorer = HealthScorer()

        logger.info(f"Pipeline initialized with fetchers: {self.registry.list_fetchers()}")

    @classmethod
    def from_env(cls) -> "TokenHealthPipeline":
        """Create pipeline from environment variables"""
        return cls(
            cmc_api_key=os.getenv("CMC_API_KEY"),
            etherscan_api_key=os.getenv("ETHERSCAN_API_KEY"),
            alchemy_api_key=os.getenv("ALCHEMY_API_KEY"),
            github_token=os.getenv("GITHUB_TOKEN"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    def analyze_token(
        self,
        contract: str,
        chain: str = "ethereum",
        include_llm_summary: bool = False,
        github_repo: Optional[str] = None,
        fetch_social: bool = True,
        fetch_security: bool = True
    ) -> TokenHealthData:
        """
        Run complete analysis pipeline for a token

        Args:
            contract: Token contract address
            chain: Blockchain network (ethereum, bsc, polygon, etc.)
            include_llm_summary: Generate AI-powered summary
            github_repo: GitHub repository URL (if known)
            fetch_social: Fetch social media metrics
            fetch_security: Fetch security metrics

        Returns:
            TokenHealthData with all metrics and scores
        """
        logger.info(f"Starting analysis for {contract} on {chain}")

        health_data = TokenHealthData(
            contract_address=contract,
            chain=chain
        )

        # ====================================================================
        # FETCH PHASE: Gather data from all sources
        # ====================================================================

        # 1. Market Data
        health_data.market = self._fetch_market_data(contract, chain)

        # 2. On-Chain Data
        health_data.onchain = self._fetch_onchain_data(contract, chain)

        # 3. Liquidity Data
        health_data.liquidity = self._fetch_liquidity_data(contract, chain)

        # 4. Security Data
        if fetch_security:
            health_data.security = self._fetch_security_data(contract, chain)

        # 5. Social Data
        if fetch_social and github_repo:
            health_data.social = self._fetch_social_data(github_repo)

        # 6. Team & Utility Data
        # These typically require manual input or web scraping
        # For now, we'll leave them as optional/manual
        health_data.team = TeamMetrics()
        health_data.utility = UtilityMetrics()

        # ====================================================================
        # TRANSFORM PHASE: Enrich and normalize data
        # ====================================================================

        # Cross-reference and enrich data
        self._enrich_data(health_data)

        # ====================================================================
        # SCORE PHASE: Calculate health scores
        # ====================================================================

        health_data.health_score = self.scorer.score_token(health_data)

        # ====================================================================
        # LLM PHASE: Generate AI summary (optional)
        # ====================================================================

        if include_llm_summary:
            health_data.health_score.summary = self._generate_llm_summary(health_data)

        logger.info(
            f"Analysis complete: Score={health_data.health_score.overall_score:.1f}, "
            f"Risk={health_data.health_score.risk_level.value}"
        )

        return health_data

    # ========================================================================
    # DATA FETCHING METHODS
    # ========================================================================

    def _fetch_market_data(
        self,
        contract: str,
        chain: str
    ) -> Optional[MarketMetrics]:
        """Fetch market data from available sources"""
        errors = []

        # Try CoinMarketCap first (if available)
        if "coinmarketcap" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("coinmarketcap")
            try:
                metrics = fetcher.fetch(contract, chain)
                if metrics:
                    logger.info("Market data fetched from CoinMarketCap")
                    return metrics
            except Exception as e:
                logger.warning(f"CoinMarketCap fetch failed: {e}")
                errors.append(f"CMC: {str(e)}")

        # Fallback to CoinGecko
        if "coingecko" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("coingecko")
            try:
                metrics = fetcher.fetch(contract, chain)
                if metrics:
                    logger.info("Market data fetched from CoinGecko")
                    return metrics
            except Exception as e:
                logger.warning(f"CoinGecko fetch failed: {e}")
                errors.append(f"CG: {str(e)}")

        if errors:
            logger.error(f"All market data fetchers failed: {errors}")

        return None

    def _fetch_onchain_data(
        self,
        contract: str,
        chain: str
    ) -> Optional[OnChainMetrics]:
        """Fetch on-chain data from available sources"""
        metrics = OnChainMetrics(contract_address=contract, chain=chain)
        errors = []

        # Etherscan data (comprehensive)
        if "etherscan" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("etherscan")
            try:
                etherscan_metrics = fetcher.fetch(contract, chain)
                if etherscan_metrics:
                    # Merge metrics
                    for key, value in vars(etherscan_metrics).items():
                        if value is not None:
                            setattr(metrics, key, value)
                    logger.info("On-chain data fetched from Etherscan")
            except Exception as e:
                logger.warning(f"Etherscan fetch failed: {e}")
                errors.append(f"Etherscan: {str(e)}")

        # Alchemy data (supplementary)
        if "alchemy" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("alchemy")
            try:
                alchemy_metrics = fetcher.fetch(contract, chain)
                if alchemy_metrics:
                    # Merge non-null values
                    for key, value in vars(alchemy_metrics).items():
                        if value is not None and getattr(metrics, key) is None:
                            setattr(metrics, key, value)
                    logger.info("On-chain data supplemented from Alchemy")
            except Exception as e:
                logger.warning(f"Alchemy fetch failed: {e}")
                errors.append(f"Alchemy: {str(e)}")

        if errors:
            logger.error(f"Some on-chain fetchers failed: {errors}")

        return metrics if any(vars(metrics).values()) else None

    def _fetch_liquidity_data(
        self,
        contract: str,
        chain: str
    ) -> Optional[LiquidityMetrics]:
        """Fetch liquidity data from DEX aggregators"""
        if "dexscreener" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("dexscreener")
            try:
                metrics = fetcher.fetch(contract, chain)
                if metrics:
                    logger.info("Liquidity data fetched from DexScreener")
                    return metrics
            except Exception as e:
                logger.warning(f"DexScreener fetch failed: {e}")

        return None

    def _fetch_security_data(
        self,
        contract: str,
        chain: str
    ) -> Optional[SecurityMetrics]:
        """Fetch security data from available sources"""
        metrics = SecurityMetrics()

        # GoPlus Security (free API)
        if "goplus" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("goplus")
            try:
                goplus_metrics = fetcher.fetch(contract, chain)
                if goplus_metrics:
                    # Merge metrics
                    for key, value in vars(goplus_metrics).items():
                        if value is not None:
                            setattr(metrics, key, value)
                    logger.info("Security data fetched from GoPlus")
            except Exception as e:
                logger.warning(f"GoPlus fetch failed: {e}")

        # Additional security sources could be added here:
        # - CertiK API (requires paid plan)
        # - Hacken API
        # - Manual audit database lookup

        return metrics if any(vars(metrics).values()) else None

    def _fetch_social_data(
        self,
        github_repo: Optional[str]
    ) -> Optional[SocialMetrics]:
        """Fetch social media and community data"""
        metrics = SocialMetrics()

        # GitHub data
        if github_repo and "github" in self.registry.list_fetchers():
            fetcher = self.registry.get_fetcher("github")
            try:
                github_metrics = fetcher.fetch(github_repo)
                if github_metrics:
                    # Merge metrics
                    for key, value in vars(github_metrics).items():
                        if value is not None:
                            setattr(metrics, key, value)
                    logger.info("Social data fetched from GitHub")
            except Exception as e:
                logger.warning(f"GitHub fetch failed: {e}")

        # Twitter, Telegram, Discord would go here
        # These typically require:
        # - Twitter API v2 (requires approval)
        # - Telegram Bot API (requires bot token + group access)
        # - Discord API (requires bot token + server access)

        return metrics if any(vars(metrics).values()) else None

    # ========================================================================
    # DATA ENRICHMENT
    # ========================================================================

    def _enrich_data(self, health_data: TokenHealthData):
        """Cross-reference and enrich data across categories"""

        # Calculate derived metrics
        if health_data.market and health_data.liquidity:
            # Liquidity to market cap ratio
            if health_data.market.market_cap and health_data.liquidity.total_liquidity_usd:
                ratio = health_data.liquidity.total_liquidity_usd / health_data.market.market_cap
                health_data.liquidity.liquidity_to_mcap_ratio = ratio

        # Populate symbol across categories
        if health_data.market and health_data.market.symbol:
            symbol = health_data.market.symbol
            if health_data.onchain:
                health_data.raw_data["symbol"] = symbol

        # Add enrichment timestamp
        health_data.raw_data["enriched_at"] = datetime.utcnow().isoformat()

    # ========================================================================
    # LLM INTEGRATION
    # ========================================================================

    def _generate_llm_summary(self, health_data: TokenHealthData) -> Optional[str]:
        """Generate AI-powered summary using LLM"""
        if not self.anthropic_api_key:
            logger.warning("No Anthropic API key provided, skipping LLM summary")
            return None

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.anthropic_api_key)

            # Prepare context for LLM
            context = self._prepare_llm_context(health_data)

            prompt = f"""You are a crypto token analyst. Analyze this token's health data and provide a concise summary.

TOKEN DATA:
{json.dumps(context, indent=2)}

HEALTH SCORE: {health_data.health_score.overall_score:.1f}/100
RISK LEVEL: {health_data.health_score.risk_level.value}

Provide:
1. A 3-5 sentence summary of the token's overall health
2. Top 2-3 red flags (if any)
3. 1-2 key strengths
4. 1-2 actionable recommendations for investors

Keep it concise and factual. Focus on the most critical information."""

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = message.content[0].text
            logger.info("LLM summary generated successfully")
            return summary

        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return None

    def _prepare_llm_context(self, health_data: TokenHealthData) -> Dict[str, Any]:
        """Prepare summarized context for LLM"""
        context = {
            "contract": health_data.contract_address,
            "chain": health_data.chain,
        }

        if health_data.market:
            context["market"] = {
                "symbol": health_data.market.symbol,
                "price": health_data.market.price_usd,
                "market_cap": health_data.market.market_cap,
                "volume_24h": health_data.market.volume_24h,
                "price_change_7d": health_data.market.price_change_7d,
            }

        if health_data.onchain:
            context["onchain"] = {
                "age_days": health_data.onchain.contract_age_days,
                "verified": health_data.onchain.source_verified,
                "holders": health_data.onchain.holders_count,
                "top_10_pct": health_data.onchain.top_10_holder_pct,
            }

        if health_data.liquidity:
            context["liquidity"] = {
                "total_usd": health_data.liquidity.total_liquidity_usd,
                "locked": health_data.liquidity.liquidity_locked,
                "honeypot": health_data.liquidity.honeypot_risk,
            }

        if health_data.security:
            context["security"] = {
                "audited": health_data.security.audit_exists,
                "exploits": health_data.security.exploits_reported,
                "vulnerabilities": health_data.security.known_vulnerabilities,
            }

        if health_data.health_score:
            context["category_scores"] = {
                cs.category: cs.score
                for cs in health_data.health_score.category_scores
            }

        return context

    # ========================================================================
    # EXPORT & SERIALIZATION
    # ========================================================================

    def export_json(self, health_data: TokenHealthData, filepath: str):
        """Export health data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(health_data.to_dict(), f, indent=2, default=str)
        logger.info(f"Exported health data to {filepath}")

    def export_summary(self, health_data: TokenHealthData) -> str:
        """Export human-readable summary"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"TOKEN HEALTH REPORT")
        lines.append("=" * 80)
        lines.append(f"Contract: {health_data.contract_address}")
        lines.append(f"Chain: {health_data.chain}")
        lines.append(f"Analyzed: {health_data.fetched_at}")
        lines.append("")

        if health_data.market:
            lines.append(f"Symbol: {health_data.market.symbol}")
            lines.append(f"Price: ${health_data.market.price_usd:,.4f}" if health_data.market.price_usd else "Price: N/A")

        if health_data.health_score:
            lines.append("")
            lines.append(f"OVERALL HEALTH SCORE: {health_data.health_score.overall_score:.1f}/100")
            lines.append(f"Risk Level: {health_data.health_score.risk_level.value.upper()}")
            lines.append(f"Confidence: {health_data.health_score.confidence * 100:.1f}%")
            lines.append("")

            lines.append("CATEGORY SCORES:")
            for cs in health_data.health_score.category_scores:
                lines.append(f"  {cs.category.capitalize()}: {cs.score:.1f}/100 (weight: {cs.weight*100:.0f}%)")

            if health_data.health_score.red_flags:
                lines.append("")
                lines.append("RED FLAGS:")
                for flag in health_data.health_score.red_flags:
                    lines.append(f"  ⚠️  {flag}")

            if health_data.health_score.green_flags:
                lines.append("")
                lines.append("STRENGTHS:")
                for flag in health_data.health_score.green_flags[:5]:
                    lines.append(f"  ✓ {flag}")

            if health_data.health_score.recommendations:
                lines.append("")
                lines.append("RECOMMENDATIONS:")
                for i, rec in enumerate(health_data.health_score.recommendations, 1):
                    lines.append(f"  {i}. {rec}")

            if health_data.health_score.summary:
                lines.append("")
                lines.append("AI SUMMARY:")
                lines.append(health_data.health_score.summary)

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_token_quick(
    contract: str,
    chain: str = "ethereum",
    **kwargs
) -> TokenHealthData:
    """Quick analysis using environment variables"""
    pipeline = TokenHealthPipeline.from_env()
    return pipeline.analyze_token(contract, chain, **kwargs)


def analyze_and_print(
    contract: str,
    chain: str = "ethereum",
    include_llm: bool = False
):
    """Analyze token and print summary to console"""
    pipeline = TokenHealthPipeline.from_env()
    health_data = pipeline.analyze_token(
        contract,
        chain,
        include_llm_summary=include_llm
    )
    print(pipeline.export_summary(health_data))
    return health_data
