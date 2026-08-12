"""
Modular Data Fetchers for Token Health Analysis

Each fetcher is responsible for retrieving data from a specific source
and populating the corresponding metrics dataclass.
"""

import logging
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time
import os

from health_models import (
    MarketMetrics, OnChainMetrics, LiquidityMetrics,
    SecurityMetrics, SocialMetrics, TeamMetrics, UtilityMetrics
)

logger = logging.getLogger(__name__)


class DataFetcher(ABC):
    """Base class for all data fetchers"""

    def __init__(self, api_key: Optional[str] = None, cache_ttl: int = 600):
        self.api_key = api_key
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """Retrieve cached data if still valid"""
        if key in self._cache and key in self._cache_timestamps:
            age = datetime.now() - self._cache_timestamps[key]
            if age.total_seconds() < self.cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return self._cache[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """Store data in cache"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()

    def _request_with_retry(
        self,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        max_retries: int = 3,
        backoff: float = 1.0
    ) -> Optional[Dict]:
        """Make HTTP request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    sleep_time = backoff * (2 ** attempt)
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Request failed after {max_retries} attempts")
                    return None

    @abstractmethod
    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[Any]:
        """Fetch data for the given contract"""
        pass


# ============================================================================
# MARKET DATA FETCHERS
# ============================================================================

class CoinMarketCapFetcher(DataFetcher):
    """Fetch market data from CoinMarketCap"""

    BASE_URL = "https://pro-api.coinmarketcap.com/v2/cryptocurrency"

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.headers = {
            "X-CMC_PRO_API_KEY": api_key,
            "Accept": "application/json"
        }

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[MarketMetrics]:
        """Fetch market metrics from CMC"""
        cache_key = f"cmc_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Map chain to CMC platform ID
        platform_map = {
            "ethereum": "1027",
            "bsc": "1839",
            "polygon": "3890"
        }
        platform_id = platform_map.get(chain.lower())

        if not platform_id:
            logger.warning(f"Unsupported chain for CMC: {chain}")
            return None

        # Get token info by contract address
        url = f"{self.BASE_URL}/quotes/latest"
        params = {
            "address": contract,
            "aux": "num_market_pairs,market_cap_by_total_supply"
        }

        data = self._request_with_retry(url, params=params, headers=self.headers)
        if not data or "data" not in data:
            return None

        try:
            # CMC returns data with contract address as key
            token_data = list(data["data"].values())[0]
            quote = token_data.get("quote", {}).get("USD", {})

            metrics = MarketMetrics(
                symbol=token_data.get("symbol", ""),
                name=token_data.get("name"),
                price_usd=quote.get("price"),
                market_cap=quote.get("market_cap"),
                fdv=quote.get("fully_diluted_market_cap"),
                volume_24h=quote.get("volume_24h"),
                price_change_24h=quote.get("percent_change_24h"),
                price_change_7d=quote.get("percent_change_7d"),
                price_change_30d=quote.get("percent_change_30d"),
                cmc_rank=token_data.get("cmc_rank"),
                exchanges_listed=token_data.get("num_market_pairs")
            )

            self._set_cache(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error parsing CMC data: {e}")
            return None


class CoinGeckoFetcher(DataFetcher):
    """Fetch market data from CoinGecko (free tier)"""

    BASE_URL = "https://api.coingecko.com/api/v3"

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[MarketMetrics]:
        """Fetch market metrics from CoinGecko"""
        cache_key = f"cg_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Map chain to CoinGecko platform
        platform_map = {
            "ethereum": "ethereum",
            "bsc": "binance-smart-chain",
            "polygon": "polygon-pos",
            "arbitrum": "arbitrum-one",
            "base": "base"
        }
        platform = platform_map.get(chain.lower())

        if not platform:
            logger.warning(f"Unsupported chain for CoinGecko: {chain}")
            return None

        url = f"{self.BASE_URL}/coins/{platform}/contract/{contract}"

        data = self._request_with_retry(url)
        if not data:
            return None

        try:
            market_data = data.get("market_data", {})

            metrics = MarketMetrics(
                symbol=data.get("symbol", "").upper(),
                name=data.get("name"),
                price_usd=market_data.get("current_price", {}).get("usd"),
                market_cap=market_data.get("market_cap", {}).get("usd"),
                fdv=market_data.get("fully_diluted_valuation", {}).get("usd"),
                volume_24h=market_data.get("total_volume", {}).get("usd"),
                price_change_24h=market_data.get("price_change_percentage_24h"),
                price_change_7d=market_data.get("price_change_percentage_7d"),
                price_change_30d=market_data.get("price_change_percentage_30d"),
                ath_price=market_data.get("ath", {}).get("usd"),
                ath_date=market_data.get("ath_date", {}).get("usd"),
                ath_change_pct=market_data.get("ath_change_percentage", {}).get("usd"),
                coingecko_rank=data.get("market_cap_rank")
            )

            self._set_cache(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error parsing CoinGecko data: {e}")
            return None


# ============================================================================
# ON-CHAIN DATA FETCHERS
# ============================================================================

class EtherscanFetcher(DataFetcher):
    """Fetch on-chain data from the Etherscan V2 API.

    V2 is one host for every chain, selected by a `chainid` param — the V1
    per-chain hosts (api.bscscan.com, api.polygonscan.com) are retired."""

    BASE_URL = "https://api.etherscan.io/v2/api"

    CHAIN_IDS = {
        "ethereum": "1",
        "bsc": "56",
        "polygon": "137",
        "arbitrum": "42161",
        "base": "8453"
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[OnChainMetrics]:
        """Fetch on-chain metrics from block explorer"""
        chain_id = self.CHAIN_IDS.get(chain.lower())
        if not chain_id:
            logger.warning(f"Unsupported chain for Etherscan: {chain}")
            return None

        cache_key = f"etherscan_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        metrics = OnChainMetrics(contract_address=contract, chain=chain)

        # Fetch contract source code (includes verification, proxy, etc.)
        source_data = self._get_contract_source(chain_id, contract)
        if source_data:
            metrics.source_verified = source_data.get("SourceCode") != ""
            metrics.proxy_contract = source_data.get("Proxy") == "1"
            metrics.implementation_address = source_data.get("Implementation")
            metrics.compiler_version = source_data.get("CompilerVersion")
            metrics.optimization_enabled = source_data.get("OptimizationUsed") == "1"

        # Fetch token holder statistics
        holder_data = self._get_token_holders(chain_id, contract)
        if holder_data:
            metrics.holders_count = len(holder_data)
            metrics.top_1_holder_pct = self._calculate_holder_concentration(holder_data, 1)
            metrics.top_3_holder_pct = self._calculate_holder_concentration(holder_data, 3)
            metrics.top_10_holder_pct = self._calculate_holder_concentration(holder_data, 10)
            metrics.top_50_holder_pct = self._calculate_holder_concentration(holder_data, 50)

        # Fetch contract creation transaction
        creation_data = self._get_contract_creation(chain_id, contract)
        if creation_data:
            metrics.owner_address = creation_data.get("contractCreator")
            if creation_data.get("timestamp"):
                created_ts = int(creation_data["timestamp"])
                created_dt = datetime.fromtimestamp(created_ts)
                metrics.contract_created_at = created_dt.isoformat()
                metrics.contract_age_days = (datetime.now() - created_dt).days

        # Fetch token supply info
        supply_data = self._get_token_supply(chain_id, contract)
        if supply_data:
            metrics.total_supply = supply_data.get("totalSupply")
            metrics.circulating_supply = supply_data.get("circulatingSupply")

        # Fetch transaction count
        tx_data = self._get_transaction_stats(chain_id, contract)
        if tx_data:
            metrics.tx_count_24h = tx_data.get("tx_24h")
            metrics.tx_count_7d = tx_data.get("tx_7d")
            metrics.tx_count_30d = tx_data.get("tx_30d")
            metrics.transfer_count_total = tx_data.get("tx_total")

        self._set_cache(cache_key, metrics)
        return metrics

    def _get_contract_source(self, chain_id: str, contract: str) -> Optional[Dict]:
        """Get contract source code and metadata"""
        params = {
            "chainid": chain_id,
            "module": "contract",
            "action": "getsourcecode",
            "address": contract,
            "apikey": self.api_key
        }
        data = self._request_with_retry(self.BASE_URL, params=params)
        if data and data.get("status") == "1" and data.get("result"):
            return data["result"][0]
        return None

    def _get_token_holders(self, chain_id: str, contract: str, limit: int = 100) -> Optional[List[Dict]]:
        """Get top token holders (Note: This requires pro API on some explorers)"""
        # Note: This endpoint is not available on free tier for most block explorers
        # You may need to use alternative methods like querying Transfer events
        # For now, returning None - implement when pro API is available
        logger.info("Token holder data requires pro API tier on most block explorers")
        return None

    def _get_contract_creation(self, chain_id: str, contract: str) -> Optional[Dict]:
        """Get contract creation transaction"""
        params = {
            "chainid": chain_id,
            "module": "contract",
            "action": "getcontractcreation",
            "contractaddresses": contract,
            "apikey": self.api_key
        }
        data = self._request_with_retry(self.BASE_URL, params=params)
        if data and data.get("status") == "1" and data.get("result"):
            return data["result"][0]
        return None

    def _get_token_supply(self, chain_id: str, contract: str) -> Optional[Dict]:
        """Get token supply information"""
        params = {
            "chainid": chain_id,
            "module": "stats",
            "action": "tokensupply",
            "contractaddress": contract,
            "apikey": self.api_key
        }
        data = self._request_with_retry(self.BASE_URL, params=params)
        if data and data.get("status") == "1":
            try:
                return {"totalSupply": float(data.get("result", 0)) / 1e18}
            except:
                return None
        return None

    def _get_transaction_stats(self, chain_id: str, contract: str) -> Optional[Dict]:
        """Get transaction statistics (approximation via recent transfers)"""
        # This is a simplified version - you'd need to query Transfer events
        # and aggregate by time period for accurate stats
        return None

    def _calculate_holder_concentration(self, holders: List[Dict], top_n: int) -> Optional[float]:
        """Calculate percentage held by top N holders"""
        if not holders or len(holders) < top_n:
            return None

        total_supply = sum(h.get("balance", 0) for h in holders)
        if total_supply == 0:
            return None

        top_n_balance = sum(h.get("balance", 0) for h in holders[:top_n])
        return (top_n_balance / total_supply) * 100


class AlchemyFetcher(DataFetcher):
    """Fetch on-chain data using Alchemy RPC"""

    CHAIN_URLS = {
        "ethereum": "https://eth-mainnet.g.alchemy.com/v2/",
        "polygon": "https://polygon-mainnet.g.alchemy.com/v2/",
        "arbitrum": "https://arb-mainnet.g.alchemy.com/v2/",
        "base": "https://base-mainnet.g.alchemy.com/v2/",
        "optimism": "https://opt-mainnet.g.alchemy.com/v2/"
    }

    def __init__(self, api_key: str):
        super().__init__(api_key)

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[OnChainMetrics]:
        """Fetch on-chain data via Alchemy RPC"""
        base_url = self.CHAIN_URLS.get(chain.lower())
        if not base_url:
            logger.warning(f"Unsupported chain for Alchemy: {chain}")
            return None

        rpc_url = f"{base_url}{self.api_key}"
        cache_key = f"alchemy_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        metrics = OnChainMetrics(contract_address=contract, chain=chain)

        # Get token metadata using Alchemy's enhanced API
        token_metadata = self._get_token_metadata(rpc_url, contract)
        if token_metadata:
            metrics.total_supply = token_metadata.get("totalSupply")

        # Get owner/admin using alchemy_getTokenAllowance or bytecode analysis
        # This is complex and requires contract-specific logic
        # For now, we'll leave it for Etherscan to handle

        self._set_cache(cache_key, metrics)
        return metrics

    def _get_token_metadata(self, rpc_url: str, contract: str) -> Optional[Dict]:
        """Get token metadata via Alchemy enhanced API"""
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenMetadata",
            "params": [contract],
            "id": 1
        }

        try:
            response = requests.post(rpc_url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            return result.get("result")
        except Exception as e:
            logger.error(f"Error fetching Alchemy token metadata: {e}")
            return None


# ============================================================================
# LIQUIDITY DATA FETCHERS
# ============================================================================

class DexScreenerFetcher(DataFetcher):
    """Fetch liquidity data from DexScreener"""

    BASE_URL = "https://api.dexscreener.com/latest/dex"

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[LiquidityMetrics]:
        """Fetch liquidity metrics from DexScreener"""
        cache_key = f"dexscreener_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        url = f"{self.BASE_URL}/tokens/{contract}"
        data = self._request_with_retry(url)

        if not data or "pairs" not in data:
            return None

        try:
            pairs = data["pairs"]
            if not pairs:
                return None

            # Sort by liquidity to get main pair
            pairs.sort(key=lambda x: x.get("liquidity", {}).get("usd", 0), reverse=True)
            main_pair = pairs[0]

            metrics = LiquidityMetrics(
                main_dex=main_pair.get("dexId"),
                main_pool_address=main_pair.get("pairAddress"),
                main_pool_liquidity_usd=main_pair.get("liquidity", {}).get("usd"),
                total_liquidity_usd=sum(p.get("liquidity", {}).get("usd", 0) for p in pairs),
                tvl_current=main_pair.get("liquidity", {}).get("usd"),
            )

            # Calculate liquidity changes if historical data available
            price_change = main_pair.get("priceChange", {})
            if "h24" in price_change:
                # Approximate TVL change from volume and price change
                pass

            self._set_cache(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error parsing DexScreener data: {e}")
            return None


# ============================================================================
# SECURITY DATA FETCHERS
# ============================================================================

@dataclass
class GoPlusData:
    """Parsed GoPlus token_security response, routed to the metrics each
    signal belongs to. Trading-safety flags (honeypot, taxes) live on
    LiquidityMetrics so the scorer's honeypot penalty actually fires."""
    security: SecurityMetrics
    liquidity: LiquidityMetrics
    onchain: OnChainMetrics


class GoPlusSecurityFetcher(DataFetcher):
    """Fetch contract security data from GoPlus Security API (free)"""

    BASE_URL = "https://api.gopluslabs.io/api/v1/token_security"

    CHAIN_IDS = {
        "ethereum": "1",
        "bsc": "56",
        "polygon": "137",
        "arbitrum": "42161",
        "base": "8453"
    }

    def fetch(self, contract: str, chain: str = "ethereum") -> Optional[GoPlusData]:
        """Fetch and parse token security data from GoPlus"""
        cache_key = f"goplus_{contract}_{chain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        chain_id = self.CHAIN_IDS.get(chain.lower())
        if not chain_id:
            logger.warning(f"Unsupported chain for GoPlus: {chain}")
            return None

        # GoPlus takes the chain id as a path segment; as a query param it 404s
        params = {"contract_addresses": contract}

        data = self._request_with_retry(f"{self.BASE_URL}/{chain_id}", params=params)
        if not data or "result" not in data:
            return None

        result = data["result"].get(contract.lower())
        if not result:
            return None

        try:
            parsed = self.parse_result(result, contract=contract, chain=chain)
            self._set_cache(cache_key, parsed)
            return parsed
        except Exception as e:
            logger.error(f"Error parsing GoPlus data: {e}")
            return None

    def parse_result(
        self,
        result: Dict[str, Any],
        contract: str = "",
        chain: str = "ethereum"
    ) -> GoPlusData:
        """Parse a GoPlus token_security result dict (values are "0"/"1" strings)."""

        def flag(key: str) -> Optional[bool]:
            value = result.get(key)
            if value is None or value == "":
                return None
            return value == "1"

        def pct(key: str) -> Optional[float]:
            """GoPlus taxes are 0-1 fractions; convert to percent."""
            value = result.get(key)
            if value in (None, ""):
                return None
            try:
                return float(value) * 100
            except (TypeError, ValueError):
                return None

        def holder_pct(holders: Optional[List[Dict]], top_n: int) -> Optional[float]:
            """Sum the supply share of the top N holders (GoPlus sorts desc;
            `percent` is a 0-1 fraction string)."""
            if not holders:
                return None
            total = 0.0
            for holder in holders[:top_n]:
                try:
                    total += float(holder.get("percent", 0))
                except (TypeError, ValueError):
                    continue
            return round(total * 100, 4)

        honeypot = flag("is_honeypot")
        cannot_sell_all = flag("cannot_sell_all")

        liquidity = LiquidityMetrics(
            honeypot_risk=honeypot,
            can_sell=(not (honeypot or cannot_sell_all))
            if (honeypot is not None or cannot_sell_all is not None) else None,
            buy_tax=pct("buy_tax"),
            sell_tax=pct("sell_tax"),
        )

        # LP lock status: sum the share held by lockers/burn addresses
        lp_holders = result.get("lp_holders")
        if lp_holders:
            locked = 0.0
            for lp in lp_holders:
                try:
                    if lp.get("is_locked") in (1, "1", True):
                        locked += float(lp.get("percent", 0))
                except (TypeError, ValueError):
                    continue
            liquidity.liquidity_locked_pct = round(locked * 100, 4)
            liquidity.liquidity_locked = liquidity.liquidity_locked_pct > 0
            liquidity.lp_holders_count = len(lp_holders)
            liquidity.lp_top_1_holder_pct = holder_pct(lp_holders, 1)

        onchain = OnChainMetrics(
            contract_address=contract,
            chain=chain,
            source_verified=flag("is_open_source"),
            proxy_contract=flag("is_proxy"),
            mintable=flag("is_mintable"),
            blacklist_function=flag("is_blacklisted"),
            owner_address=result.get("owner_address") or None,
        )
        holder_count = result.get("holder_count")
        if holder_count:
            try:
                onchain.holders_count = int(holder_count)
            except (TypeError, ValueError):
                pass

        # Top-holder concentration — the strongest rug signal after honeypot
        holders = result.get("holders")
        onchain.top_1_holder_pct = holder_pct(holders, 1)
        onchain.top_3_holder_pct = holder_pct(holders, 3)
        onchain.top_10_holder_pct = holder_pct(holders, 10)

        vulnerabilities = []
        if flag("can_take_back_ownership"):
            vulnerabilities.append("Owner can take back ownership")
        if flag("hidden_owner"):
            vulnerabilities.append("Hidden owner")
        if flag("selfdestruct"):
            vulnerabilities.append("Self-destruct function present")
        if flag("external_call"):
            vulnerabilities.append("External call risk")

        security = SecurityMetrics(known_vulnerabilities=vulnerabilities)

        return GoPlusData(security=security, liquidity=liquidity, onchain=onchain)


# ============================================================================
# SOCIAL DATA FETCHERS
# ============================================================================

class GitHubFetcher(DataFetcher):
    """Fetch project data from GitHub"""

    BASE_URL = "https://api.github.com"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.headers = {}
        if api_key:
            self.headers["Authorization"] = f"token {api_key}"

    def fetch(self, repo_url: str) -> Optional[SocialMetrics]:
        """Fetch GitHub metrics for a repository"""
        # Parse owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            return None

        owner, repo = parts[-2], parts[-1]
        cache_key = f"github_{owner}_{repo}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Get repository info
        repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        repo_data = self._request_with_retry(repo_url, headers=self.headers)

        if not repo_data:
            return None

        try:
            # Get commit activity
            commits_url = f"{repo_url}/commits"
            since_30d = (datetime.now() - timedelta(days=30)).isoformat()
            since_90d = (datetime.now() - timedelta(days=90)).isoformat()

            # per_page=100 — the default page size of 30 silently capped the
            # commit counts and made the ">50 commits" scoring branch unreachable
            commits_30d = self._request_with_retry(
                commits_url,
                params={"since": since_30d, "per_page": 100},
                headers=self.headers
            )
            commits_90d = self._request_with_retry(
                commits_url,
                params={"since": since_90d, "per_page": 100},
                headers=self.headers
            )

            # Get contributors
            contributors_url = f"{repo_url}/contributors"
            contributors = self._request_with_retry(contributors_url, headers=self.headers)

            # Get issues
            issues_open = repo_data.get("open_issues_count", 0)

            metrics = SocialMetrics(
                github_repo=f"{owner}/{repo}",
                github_stars=repo_data.get("stargazers_count"),
                github_forks=repo_data.get("forks_count"),
                github_commits_30d=len(commits_30d) if commits_30d else 0,
                github_commits_90d=len(commits_90d) if commits_90d else 0,
                github_contributors=len(contributors) if contributors else 0,
                github_last_commit=repo_data.get("pushed_at"),
                github_issues_open=issues_open,
            )

            self._set_cache(cache_key, metrics)
            return metrics

        except Exception as e:
            logger.error(f"Error parsing GitHub data: {e}")
            return None


# ============================================================================
# DATA FETCHER REGISTRY
# ============================================================================

class DataFetcherRegistry:
    """Central registry for all data fetchers"""

    def __init__(self):
        self.fetchers = {}

    def register_market_fetchers(
        self,
        cmc_api_key: Optional[str] = None,
        coingecko_api_key: Optional[str] = None
    ):
        """Register market data fetchers"""
        if cmc_api_key:
            self.fetchers["coinmarketcap"] = CoinMarketCapFetcher(cmc_api_key)
        self.fetchers["coingecko"] = CoinGeckoFetcher()

    def register_onchain_fetchers(
        self,
        etherscan_api_key: Optional[str] = None,
        alchemy_api_key: Optional[str] = None
    ):
        """Register on-chain data fetchers"""
        if etherscan_api_key:
            self.fetchers["etherscan"] = EtherscanFetcher(etherscan_api_key)
        if alchemy_api_key:
            self.fetchers["alchemy"] = AlchemyFetcher(alchemy_api_key)

    def register_liquidity_fetchers(self):
        """Register liquidity data fetchers"""
        self.fetchers["dexscreener"] = DexScreenerFetcher()

    def register_security_fetchers(self):
        """Register security data fetchers"""
        self.fetchers["goplus"] = GoPlusSecurityFetcher()

    def register_social_fetchers(self, github_token: Optional[str] = None):
        """Register social media fetchers"""
        self.fetchers["github"] = GitHubFetcher(github_token)

    def get_fetcher(self, name: str) -> Optional[DataFetcher]:
        """Get a registered fetcher by name"""
        return self.fetchers.get(name)

    def list_fetchers(self) -> List[str]:
        """List all registered fetchers"""
        return list(self.fetchers.keys())
