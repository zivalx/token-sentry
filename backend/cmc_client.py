"""
CoinMarketCap API Client with Database Caching
Free tier: 333 calls/day
"""
import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from db import get_db

# Load environment variables
load_dotenv()


class CMCClient:
    """CoinMarketCap API client with persistent caching"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY", "")
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.db = get_db()

    def get_trending(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top trending/latest cryptocurrencies
        Uses database cache to minimize API calls
        """
        # Try cache first (10 min TTL)
        cached = self.db.get_trending(chain)
        if cached:
            print(f"✅ Using cached trending data ({len(cached)} tokens)")
            return cached[:limit]

        # No cache or expired - fetch from API
        if not self.api_key:
            print("⚠️  No CMC API key, using fallback data")
            return self._get_fallback_data(chain, limit)

        try:
            print("🔄 Fetching fresh data from CoinMarketCap...")
            # Use listings but sort by volume and percent change for "trending" effect
            url = f"{self.base_url}/cryptocurrency/listings/latest"
            headers = {
                "X-CMC_PRO_API_KEY": self.api_key,
                "Accept": "application/json"
            }
            params = {
                "start": 1,
                "limit": 200,  # Fetch many more to filter from
                "convert": "USD",
                "sort": "volume_24h",  # Sort by volume for liquid/tradeable tokens
                "sort_dir": "desc",
                "price_min": 0.000001,  # Exclude very low priced
                "volume_24h_min": 50000  # Minimum volume for tradeability
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                coins = data.get("data", [])
                print(f"✅ Received {len(coins)} coins from CoinMarketCap")

                # Process coins
                results = self._process_coins(coins, chain, limit, require_positive_change=True)

                # Save to cache
                self.db.save_trending(chain, results, ttl_minutes=10)
                print(f"💾 Cached {len(results)} tokens to database")

                return results[:limit]

            elif response.status_code == 401:
                print("❌ Invalid CMC API key")
                return self._get_fallback_data(chain, limit)
            elif response.status_code == 429:
                print("⚠️  CMC rate limit reached, using fallback")
                return self._get_fallback_data(chain, limit)
            else:
                print(f"❌ CMC API error: {response.status_code}")
                return self._get_fallback_data(chain, limit)

        except Exception as e:
            print(f"❌ CMC API exception: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_data(chain, limit)

    def _get_contract_address(self, coin: Dict[str, Any], chain: str) -> str:
        """Extract contract address for specific chain"""
        # CMC includes platform info
        platform = coin.get("platform")
        if platform:
            chain_map = {
                "ethereum": "Ethereum",
                "bsc": "BNB Smart Chain (BEP20)",
                "polygon": "Polygon",
                "arbitrum": "Arbitrum"
            }
            if platform.get("name") == chain_map.get(chain.lower()):
                return platform.get("token_address", "")
        return ""

    def _estimate_exchanges(self, coin: Dict[str, Any], market_cap: float, volume: float) -> tuple:
        """
        Estimate exchange presence based on market cap and volume
        Returns: (list of exchanges, count)
        """
        exchanges = []

        # Top tier coins (market cap > $10B) - on all major exchanges
        if market_cap > 10_000_000_000:
            exchanges = ["Binance", "Coinbase", "Kraken", "OKX", "Bybit", "KuCoin"]
            # Check if it's an ETH token - also on DEXes
            platform = coin.get("platform")
            if platform and "Ethereum" in platform.get("name", ""):
                exchanges.extend(["Uniswap", "SushiSwap"])

        # Large caps ($1B - $10B) - major CEXes + some DEXes
        elif market_cap > 1_000_000_000:
            exchanges = ["Binance", "Coinbase", "OKX", "Bybit"]
            platform = coin.get("platform")
            if platform and "Ethereum" in platform.get("name", ""):
                exchanges.extend(["Uniswap"])

        # Mid caps ($100M - $1B) - multiple CEXes + DEXes
        elif market_cap > 100_000_000:
            exchanges = ["Binance", "OKX", "KuCoin"]
            platform = coin.get("platform")
            if platform:
                if "Ethereum" in platform.get("name", ""):
                    exchanges.extend(["Uniswap", "SushiSwap"])
                elif "BNB" in platform.get("name", ""):
                    exchanges.extend(["PancakeSwap"])

        # Small caps ($10M - $100M) - few CEXes, mostly DEXes
        elif market_cap > 10_000_000:
            platform = coin.get("platform")
            if platform:
                if "Ethereum" in platform.get("name", ""):
                    exchanges = ["Uniswap", "SushiSwap", "KuCoin"]
                elif "BNB" in platform.get("name", ""):
                    exchanges = ["PancakeSwap", "Gate.io"]
                else:
                    exchanges = ["Gate.io", "MEXC"]
            else:
                exchanges = ["Gate.io", "MEXC"]

        # Micro caps (< $10M) - mostly DEXes only
        else:
            platform = coin.get("platform")
            if platform:
                if "Ethereum" in platform.get("name", ""):
                    exchanges = ["Uniswap"]
                elif "BNB" in platform.get("name", ""):
                    exchanges = ["PancakeSwap"]
                else:
                    exchanges = ["DEX"]
            else:
                exchanges = ["Minor CEX"]

        return (exchanges, len(exchanges))

    def _calculate_risk(self, coin: Dict[str, Any], quote: Dict[str, Any]) -> int:
        """Calculate risk score based on CMC data"""
        risk = 0

        # Market cap check
        market_cap = quote.get("market_cap", 0)
        if market_cap < 1000000:  # < $1M
            risk += 40
        elif market_cap < 10000000:  # < $10M
            risk += 20
        elif market_cap > 1000000000:  # > $1B
            risk -= 10

        # Volume check
        volume = quote.get("volume_24h", 0)
        if volume < 100000:  # < $100K
            risk += 20
        elif volume < 1000000:  # < $1M
            risk += 10

        # Volatility check
        change_24h = abs(quote.get("percent_change_24h", 0))
        if change_24h > 50:
            risk += 20
        elif change_24h > 20:
            risk += 10

        # CMC rank check (lower rank = more established)
        rank = coin.get("cmc_rank", 999)
        if rank <= 10:
            risk -= 15
        elif rank <= 50:
            risk -= 5
        elif rank > 500:
            risk += 15

        return max(0, min(100, risk))

    def get_newest(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get newest/recently added cryptocurrencies
        Uses database cache to minimize API calls
        """
        # Try cache first (10 min TTL)
        cached = self.db.get_newest(chain)
        if cached:
            print(f"✅ Using cached newest data ({len(cached)} tokens)")
            return cached[:limit]

        # No cache or expired - fetch from API
        if not self.api_key:
            print("⚠️  No CMC API key, using fallback data")
            return self._get_fallback_data(chain, limit, "newest")

        try:
            print("🔄 Fetching newest tokens from CoinMarketCap...")
            url = f"{self.base_url}/cryptocurrency/listings/latest"
            headers = {
                "X-CMC_PRO_API_KEY": self.api_key,
                "Accept": "application/json"
            }
            params = {
                "start": 1,
                "limit": 100,  # Fetch recent additions
                "convert": "USD",
                "sort": "date_added",  # Sort by date added
                "sort_dir": "desc",  # Newest first
                "volume_24h_min": 10000  # Minimum volume for visibility
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                coins = data.get("data", [])
                print(f"✅ Received {len(coins)} newest coins from CoinMarketCap")

                results = self._process_coins(coins, chain, limit)

                # Save to cache
                self.db.save_newest(chain, results, ttl_minutes=10)
                print(f"💾 Cached {len(results)} newest tokens to database")

                return results[:limit]

            elif response.status_code == 401:
                print("❌ Invalid CMC API key")
                return self._get_fallback_data(chain, limit, "newest")
            elif response.status_code == 429:
                print("⚠️  CMC rate limit reached, using fallback")
                return self._get_fallback_data(chain, limit, "newest")
            else:
                print(f"❌ CMC API error: {response.status_code}")
                return self._get_fallback_data(chain, limit, "newest")

        except Exception as e:
            print(f"❌ CMC API exception: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_data(chain, limit, "newest")

    def get_top_gainers(self, chain: str = "ethereum", limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top gaining cryptocurrencies (24h % change)
        Uses database cache to minimize API calls
        """
        # Try cache first (10 min TTL)
        cached = self.db.get_gainers(chain)
        if cached:
            print(f"✅ Using cached gainers data ({len(cached)} tokens)")
            return cached[:limit]

        # No cache or expired - fetch from API
        if not self.api_key:
            print("⚠️  No CMC API key, using fallback data")
            return self._get_fallback_data(chain, limit, "gainers")

        try:
            print("🔄 Fetching top gainers from CoinMarketCap...")

            # Try the trending/gainers-losers endpoint first (may require higher tier)
            url = f"{self.base_url}/cryptocurrency/trending/gainers-losers"
            headers = {
                "X-CMC_PRO_API_KEY": self.api_key,
                "Accept": "application/json"
            }
            params = {
                "limit": limit,
                "convert": "USD"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                gainers = data.get("data", {}).get("gainers", [])
                if gainers:
                    print(f"✅ Received {len(gainers)} top gainers from CoinMarketCap")
                    results = self._process_coins(gainers, chain, limit)
                    self.db.save_gainers(chain, results, ttl_minutes=10)
                    return results[:limit]

            # Fallback: Use listings endpoint sorted by percent_change_24h
            print("🔄 Using listings endpoint for top gainers...")
            url = f"{self.base_url}/cryptocurrency/listings/latest"
            params = {
                "start": 1,
                "limit": 200,
                "convert": "USD",
                "sort": "percent_change_24h",  # Sort by 24h change
                "sort_dir": "desc",  # Biggest gains first
                "volume_24h_min": 50000,  # Minimum volume
                "percent_change_24h_min": 5  # At least 5% gain
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                coins = data.get("data", [])
                print(f"✅ Received {len(coins)} coins, filtering top gainers")

                results = self._process_coins(coins, chain, limit, require_positive_change=True)

                # Save to cache
                self.db.save_gainers(chain, results, ttl_minutes=10)
                print(f"💾 Cached {len(results)} top gainers to database")

                return results[:limit]

            elif response.status_code == 401:
                print("❌ Invalid CMC API key")
                return self._get_fallback_data(chain, limit, "gainers")
            elif response.status_code == 429:
                print("⚠️  CMC rate limit reached, using fallback")
                return self._get_fallback_data(chain, limit, "gainers")
            else:
                print(f"❌ CMC API error: {response.status_code}")
                return self._get_fallback_data(chain, limit, "gainers")

        except Exception as e:
            print(f"❌ CMC API exception: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_data(chain, limit, "gainers")

    def _process_coins(self, coins: List[Dict[str, Any]], chain: str, limit: int, require_positive_change: bool = False) -> List[Dict[str, Any]]:
        """
        Process coin data into our standard format
        """
        results = []
        for coin in coins:
            quote = coin.get("quote", {}).get("USD", {})

            # Get metrics
            volume = quote.get("volume_24h", 0)
            market_cap = quote.get("market_cap", 0)
            price_change = quote.get("percent_change_24h", 0)

            # Filter by positive change if required
            if require_positive_change and price_change <= 0:
                continue

            # Stop once we have enough
            if len(results) >= limit:
                break

            # Get contract address
            address = self._get_contract_address(coin, chain)
            if not address:
                address = f"cmc_{coin.get('id')}"

            # Get exchange info
            exchanges, exchange_count = self._estimate_exchanges(coin, market_cap, volume)

            results.append({
                "symbol": coin.get("symbol", ""),
                "name": coin.get("name", ""),
                "address": address,
                "priceUsd": str(quote.get("price", 0)),
                "priceChange24h": round(price_change, 2),
                "volume24h": int(volume),
                "liquidity": int(volume * 0.2),  # Estimate
                "totalSupply": int(coin.get("total_supply", 0)) if coin.get("total_supply") else None,
                "circulatingSupply": int(coin.get("circulating_supply", 0)) if coin.get("circulating_supply") else None,
                "marketCap": int(market_cap),
                "fdv": int(quote.get("fully_diluted_market_cap", 0)),
                "exchanges": exchanges,
                "exchangeCount": exchange_count,
                "pairCount": exchange_count,
                "chain": chain,
                "riskScore": self._calculate_risk(coin, quote),
                "cmcRank": coin.get("cmc_rank", 999)
            })

        return results

    def _get_fallback_data(self, chain: str, limit: int, data_type: str = "trending") -> List[Dict[str, Any]]:
        """
        Fallback: Try to get ANY cached data, even if expired
        Better to show old data than no data
        """
        print(f"🔍 Looking for any cached {data_type} data as fallback...")

        # Try to get even expired cache
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).parent / "tokens.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Choose the right table based on data type
        table_map = {
            "trending": "trending_cache",
            "newest": "newest_cache",
            "gainers": "gainers_cache"
        }
        table = table_map.get(data_type, "trending_cache")

        cursor.execute(f"""
            SELECT data FROM {table}
            WHERE chain = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (chain,))

        row = cursor.fetchone()
        conn.close()

        if row:
            import json
            data = json.loads(row[0])
            print(f"⚠️  Using stale cache data ({len(data)} tokens)")
            return data[:limit]

        print(f"❌ No {data_type} cache data available")
        return []


# Singleton instance
_cmc_client = None

def get_cmc_client() -> CMCClient:
    """Get global CMC client instance"""
    global _cmc_client
    if _cmc_client is None:
        _cmc_client = CMCClient()
    return _cmc_client
