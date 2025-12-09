"""
Token Ticker Resolver
Converts ticker symbols to contract addresses using multiple APIs
"""
import requests
from typing import Optional, Dict, List, Any
from functools import lru_cache
from cmc_client import get_cmc_client


class TickerResolver:
    """Resolves token tickers to contract addresses"""

    def __init__(self):
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.dexscreener_base = "https://api.dexscreener.com/latest/dex"

    @lru_cache(maxsize=1000)
    def resolve(self, ticker: str, chain: str = "ethereum") -> Optional[str]:
        """
        Resolve ticker to contract address
        Returns: contract address or None
        """
        ticker = ticker.upper()

        # Try CoinGecko first (more comprehensive)
        address = self._resolve_coingecko(ticker, chain)
        if address:
            return address

        # Fallback to DEXScreener
        address = self._resolve_dexscreener(ticker, chain)
        if address:
            return address

        return None

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
        print(f"🔍 Getting trending tokens for {chain} (limit: {limit})")

        # Use CoinMarketCap client with database caching
        cmc_client = get_cmc_client()
        return cmc_client.get_trending(chain, limit)

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
        """
        Fallback: Get trending tokens from CoinGecko
        """
        try:
            print("Using CoinGecko trending as fallback")
            url = f"{self.coingecko_base}/search/trending"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                print(f"CoinGecko trending failed: {response.status_code}")
                return []

            data = response.json()
            coins = data.get("coins", [])
            print(f"Received {len(coins)} trending coins from CoinGecko")

            results = []
            chain_map = {
                "ethereum": "ethereum",
                "bsc": "binance-smart-chain",
                "polygon": "polygon-pos",
                "arbitrum": "arbitrum-one",
            }
            platform_key = chain_map.get(chain.lower(), "ethereum")

            for item in coins[:limit]:
                coin = item.get("item", {})
                coin_id = coin.get("id")

                if not coin_id:
                    continue

                # Get full coin data to extract contract address
                try:
                    coin_url = f"{self.coingecko_base}/coins/{coin_id}"
                    coin_response = requests.get(coin_url, timeout=5)

                    if coin_response.status_code == 200:
                        coin_data = coin_response.json()
                        platforms = coin_data.get("platforms", {})
                        address = platforms.get(platform_key, "")

                        if address:
                            market_data = coin_data.get("market_data", {})
                            results.append({
                                "symbol": coin.get("symbol", "").upper(),
                                "name": coin.get("name", ""),
                                "address": address,
                                "priceUsd": str(market_data.get("current_price", {}).get("usd", 0)),
                                "priceChange24h": float(market_data.get("price_change_percentage_24h", 0)),
                                "volume24h": int(market_data.get("total_volume", {}).get("usd", 0)),
                                "liquidity": int(market_data.get("total_volume", {}).get("usd", 0) * 0.1),  # Estimate
                                "totalSupply": int(market_data.get("total_supply", 0)) if market_data.get("total_supply") else None,
                                "circulatingSupply": int(market_data.get("circulating_supply", 0)) if market_data.get("circulating_supply") else None,
                                "marketCap": int(market_data.get("market_cap", {}).get("usd", 0)),
                                "fdv": int(market_data.get("fully_diluted_valuation", {}).get("usd", 0)),
                                "exchanges": ["coingecko"],
                                "exchangeCount": 1,
                                "pairCount": 1,
                                "chain": chain,
                                "riskScore": 50  # Default moderate risk for CoinGecko trending
                            })
                except Exception as e:
                    print(f"Error fetching coin {coin_id}: {e}")
                    continue

            print(f"Returning {len(results)} tokens from CoinGecko")
            return results

        except Exception as e:
            print(f"CoinGecko trending error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _calculate_quick_risk(self, token: Dict[str, Any]) -> int:
        """
        Quick risk assessment for trending tokens
        Returns: 0-100 (higher = riskier)
        """
        risk = 0

        # Liquidity check
        liquidity = token.get("liquidity", 0)
        if liquidity < 10000:
            risk += 30
        elif liquidity < 50000:
            risk += 15
        elif liquidity > 500000:
            risk -= 10  # Good liquidity

        # Volume check
        volume = token.get("volume24h", 0)
        if volume < 5000:
            risk += 20
        elif volume < 20000:
            risk += 10

        # Exchange diversity
        exchange_count = len(token.get("exchanges", set()))
        if exchange_count <= 1:
            risk += 15
        elif exchange_count >= 5:
            risk -= 10
        elif exchange_count >= 3:
            risk -= 5

        # Price volatility
        price_change = abs(token.get("priceChange24h", 0))
        if price_change > 100:
            risk += 20  # Extreme volatility
        elif price_change > 50:
            risk += 10

        # Market cap check
        market_cap = token.get("marketCap", 0)
        if market_cap > 0 and market_cap < 100000:
            risk += 15  # Very low market cap

        return max(0, min(100, risk))


# Singleton instance
_resolver = None

def get_resolver() -> TickerResolver:
    """Get global ticker resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = TickerResolver()
    return _resolver
