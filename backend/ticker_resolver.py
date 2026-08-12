"""
Token Ticker Resolver
Converts ticker symbols to contract addresses using multiple APIs
"""
import logging
import requests
from typing import Optional, Dict, List, Any
from cmc_client import get_cmc_client

logger = logging.getLogger(__name__)


class TickerResolver:
    """Resolves token tickers to contract addresses"""

    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"
        self._resolve_cache = {}

    def resolve(self, ticker: str, chain: str = "ethereum") -> Optional[str]:
        """
        Resolve ticker to contract address
        Returns: contract address or None

        Successful resolutions are cached; failures are NOT — a transient
        API error must not blacklist a ticker for the process lifetime.
        """
        ticker = ticker.upper()
        cache_key = (ticker, chain)
        if cache_key in self._resolve_cache:
            return self._resolve_cache[cache_key]

        # Try CoinGecko first (more comprehensive), then DEXScreener
        address = self._resolve_coingecko(ticker, chain) or self._resolve_dexscreener(ticker, chain)

        if address:
            if len(self._resolve_cache) >= 1000:
                self._resolve_cache.pop(next(iter(self._resolve_cache)))
            self._resolve_cache[cache_key] = address
        return address

    def search(self, query: str, chain: str = "ethereum", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tokens by name or ticker
        Returns: list of {symbol, name, address, chain}
        """
        results = []

        # CoinGecko search
        cg_results = self._search_coingecko(query, chain)
        results.extend(cg_results[:limit])

        # Deduplicate by address
        seen = set()
        unique_results = []
        for r in results:
            if r['address'] not in seen:
                seen.add(r['address'])
                unique_results.append(r)

        return unique_results[:limit]

    def _resolve_coingecko(self, ticker: str, chain: str) -> Optional[str]:
        """Resolve using CoinGecko API"""
        try:
            # Search for token
            url = f"{self.coingecko_base}/search"
            params = {"query": ticker}
            response = requests.get(url, params=params, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()
            coins = data.get("coins", [])

            # Filter by symbol match
            for coin in coins:
                if coin.get("symbol", "").upper() == ticker:
                    coin_id = coin.get("id")
                    if coin_id:
                        # Get contract address
                        return self._get_coingecko_contract(coin_id, chain)

        except Exception as e:
            print(f"CoinGecko error: {e}")
            return None

    def _get_coingecko_contract(self, coin_id: str, chain: str) -> Optional[str]:
        """Get contract address from CoinGecko coin ID"""
        try:
            url = f"{self.coingecko_base}/coins/{coin_id}"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()
            platforms = data.get("platforms", {})

            # Map chain names
            chain_map = {
                "ethereum": "ethereum",
                "bsc": "binance-smart-chain",
                "polygon": "polygon-pos",
                "arbitrum": "arbitrum-one",
                "base": "base",
            }

            platform_key = chain_map.get(chain.lower(), "ethereum")
            address = platforms.get(platform_key, "")

            return address if address else None

        except Exception as e:
            print(f"CoinGecko contract fetch error: {e}")
            return None

    def _resolve_dexscreener(self, ticker: str, chain: str) -> Optional[str]:
        """Resolve using DEXScreener API"""
        try:
            # Search for token
            url = f"{self.dexscreener_base}/search"
            params = {"q": ticker}
            response = requests.get(url, params=params, timeout=5)

            if response.status_code != 200:
                return None

            data = response.json()
            pairs = data.get("pairs", [])

            # Filter by chain and symbol match
            chain_map = {
                "ethereum": "ethereum",
                "bsc": "bsc",
                "polygon": "polygon",
                "arbitrum": "arbitrum",
                "base": "base",
            }

            chain_id = chain_map.get(chain.lower(), "ethereum")

            for pair in pairs:
                if pair.get("chainId") == chain_id:
                    base_token = pair.get("baseToken", {})
                    if base_token.get("symbol", "").upper() == ticker:
                        return base_token.get("address")

            return None

        except Exception as e:
            print(f"DEXScreener error: {e}")
            return None

    def _search_coingecko(self, query: str, chain: str) -> List[Dict[str, Any]]:
        """Search tokens using CoinGecko"""
        results = []
        try:
            url = f"{self.coingecko_base}/search"
            params = {"query": query}
            response = requests.get(url, params=params, timeout=5)

            if response.status_code != 200:
                return results

            data = response.json()
            coins = data.get("coins", [])

            for coin in coins[:10]:
                coin_id = coin.get("id")
                if coin_id:
                    address = self._get_coingecko_contract(coin_id, chain)
                    if address:
                        results.append({
                            "symbol": coin.get("symbol", "").upper(),
                            "name": coin.get("name", ""),
                            "address": address,
                            "chain": chain,
                            "source": "coingecko"
                        })

        except Exception as e:
            print(f"CoinGecko search error: {e}")

        return results

    def get_trending(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get trending tokens with comprehensive data using CoinMarketCap
        Uses database caching to minimize API calls
        Returns: list with symbol, name, address, price, volume, liquidity, supply, exchanges, risk
        """
        cmc_client = get_cmc_client()
        results = cmc_client.get_trending(chain, limit)
        if results:
            return results

        # No CMC key (or CMC empty): fall back to CoinGecko trending
        return self._get_trending_coingecko(chain, limit)

    def get_newest(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get newest/recently added tokens using CoinMarketCap
        Sorted by date_added (newest first)
        Uses database caching to minimize API calls
        """
        print(f"🔍 Getting newest tokens for {chain} (limit: {limit})")

        # Use CoinMarketCap client with database caching
        cmc_client = get_cmc_client()
        return cmc_client.get_newest(chain, limit)

    def get_top_gainers(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top gaining tokens (24h % change) using CoinMarketCap
        Sorted by percent_change_24h (biggest gains first)
        Uses database caching to minimize API calls
        """
        print(f"🔍 Getting top gainers for {chain} (limit: {limit})")

        # Use CoinMarketCap client with database caching
        cmc_client = get_cmc_client()
        return cmc_client.get_top_gainers(chain, limit)

    def _get_trending_coingecko(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """Fallback trending list from CoinGecko (keyless).

        One /coins/{id} call per trending coin (~15), so results are cached
        in SQLite for 10 minutes like the CMC path.
        """
        from db import get_db

        try:
            data = self._cg_get(f"{self.coingecko_base}/search/trending")
            if not data:
                return []

            results = []
            for item in data.get("coins", [])[:limit]:
                coin_id = item.get("item", {}).get("id")
                if not coin_id:
                    continue
                coin_data = self._cg_get(f"{self.coingecko_base}/coins/{coin_id}")
                if not coin_data:
                    continue
                token = self._cg_trending_token(coin_data, chain)
                if token:
                    results.append(token)

            if results:
                get_db().save_trending(chain, results, ttl_minutes=10)
            return results

        except Exception as e:
            logger.error(f"CoinGecko trending error: {e}")
            return []

    def _cg_get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """GET a CoinGecko endpoint, returning None on any failure."""
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                logger.warning(f"CoinGecko {url} returned {response.status_code}")
                return None
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"CoinGecko request failed: {e}")
            return None

    def _cg_trending_token(self, coin_data: Dict[str, Any], chain: str) -> Optional[Dict[str, Any]]:
        """Build a trending-list row from a CoinGecko /coins/{id} payload.

        Only real fields: no invented liquidity, exchange names, or default
        risk scores. Returns None when the coin has no address on the chain.
        """
        chain_map = {
            "ethereum": "ethereum",
            "bsc": "binance-smart-chain",
            "polygon": "polygon-pos",
            "arbitrum": "arbitrum-one",
            "base": "base",
        }
        platform_key = chain_map.get(chain.lower(), "ethereum")
        address = (coin_data.get("platforms") or {}).get(platform_key)
        if not address:
            return None

        market_data = coin_data.get("market_data", {})
        market_cap = market_data.get("market_cap", {}).get("usd")
        volume = market_data.get("total_volume", {}).get("usd")
        price_change = market_data.get("price_change_percentage_24h")

        token = {
            "symbol": coin_data.get("symbol", "").upper(),
            "name": coin_data.get("name", ""),
            "address": address,
            "priceUsd": str(market_data.get("current_price", {}).get("usd", 0)),
            "priceChange24h": round(price_change, 2) if price_change is not None else 0,
            "volume24h": int(volume) if volume else None,
            "liquidity": None,  # CoinGecko does not provide pool liquidity
            "totalSupply": int(market_data["total_supply"]) if market_data.get("total_supply") else None,
            "circulatingSupply": int(market_data["circulating_supply"]) if market_data.get("circulating_supply") else None,
            "marketCap": int(market_cap) if market_cap else None,
            "fdv": int(market_data["fully_diluted_valuation"]["usd"]) if market_data.get("fully_diluted_valuation", {}).get("usd") else None,
            "chain": chain,
            "source": "coingecko",
        }
        token["riskScore"] = self._calculate_quick_risk(token)
        return token

    def _calculate_quick_risk(self, token: Dict[str, Any]) -> int:
        """
        Quick risk assessment for trending-list rows
        Returns: 0-100 (higher = riskier)

        Only fields that are actually present move the score — unknown data
        is unknown, not bad.
        """
        risk = 0

        liquidity = token.get("liquidity")
        if liquidity is not None:
            if liquidity < 10000:
                risk += 30
            elif liquidity < 50000:
                risk += 15
            elif liquidity > 500000:
                risk -= 10

        volume = token.get("volume24h")
        if volume is not None:
            if volume < 5000:
                risk += 20
            elif volume < 20000:
                risk += 10

        price_change = token.get("priceChange24h")
        if price_change is not None:
            if abs(price_change) > 100:
                risk += 20  # Extreme volatility
            elif abs(price_change) > 50:
                risk += 10

        market_cap = token.get("marketCap")
        if market_cap is not None:
            if market_cap < 100000:
                risk += 15  # Very low market cap
            elif market_cap > 1_000_000_000:
                risk -= 10

        return max(0, min(100, 30 + risk))  # 30 = baseline for a trending small token

# Singleton instance
_resolver = None

def get_resolver() -> TickerResolver:
    """Get global ticker resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = TickerResolver()
    return _resolver
