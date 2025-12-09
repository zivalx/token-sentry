# Token Health System - Current Status & Capabilities

## 🟢 WORKING NOW (With Your Existing API Keys)

### Data Sources - Currently Active

| Source | Category | Data Retrieved | Rate Limit | Status |
|--------|----------|----------------|------------|--------|
| **CoinMarketCap** | Market Data | ✅ Price, market cap, volume, 24h change | 333 calls/day | 🟢 ACTIVE |
| **CoinGecko** | Market Data (fallback) | ✅ Price, market cap, ATH, rank | 50 calls/min | 🟢 ACTIVE |
| **Etherscan** | On-Chain Data | ✅ Contract verification, source code, creator | 5 calls/sec | 🟢 ACTIVE |
| **Alchemy** | On-Chain RPC | ✅ Token metadata, supply data | 300M CU/month | 🟢 ACTIVE |
| **DexScreener** | Liquidity | ✅ Pool data, liquidity USD, DEX info | Unlimited | 🟢 ACTIVE |
| **GoPlus Security** | Security | ✅ Honeypot check, contract flags | Free tier | 🟢 ACTIVE |

### Metrics Currently Calculated

#### ✅ Market Metrics (Working)
- `price_usd` - Current price from CMC/CoinGecko
- `market_cap` - Market capitalization
- `fdv` - Fully diluted valuation
- `volume_24h` - 24-hour trading volume
- `price_change_24h` - 24-hour % change
- `price_change_7d` - 7-day % change
- `price_change_30d` - 30-day % change
- `exchanges_listed` - Number of exchanges
- `cmc_rank` - CoinMarketCap rank
- `coingecko_rank` - CoinGecko rank
- `ath_price` - All-time high price
- `ath_date` - Date of ATH

**Score Calculation:**
```python
Market Score =
  + 30 pts if market_cap > $1B
  + 20 pts if market_cap > $100M
  - 10 pts if market_cap < $1M
  + 20 pts if volatility < 20%
  + 15 pts if price_trend stable (-10% to +30%)
  + 15 pts if listed on 10+ exchanges
  = 0-100 score
```

#### ✅ On-Chain Metrics (Working)
- `contract_address` - Token contract
- `source_verified` - Is source code verified? (Etherscan)
- `contract_age_days` - Age since deployment
- `contract_created_at` - Creation timestamp
- `compiler_version` - Solidity compiler version
- `optimization_enabled` - Optimizer used?
- `total_supply` - Total token supply (Alchemy)
- `proxy_contract` - Is it upgradeable?
- `implementation_address` - If proxy, implementation contract

**Score Calculation:**
```python
On-Chain Score =
  + 25 pts if age > 1 year
  + 20 pts if source verified
  - 25 pts if NOT verified (critical)
  + 20 pts if ownership renounced
  - 15 pts if owner has admin privileges
  - 10 pts if proxy contract (upgradeable)
  = 0-100 score
```

#### ✅ Liquidity Metrics (Working)
- `main_dex` - Primary DEX (Uniswap, Sushi, etc.)
- `main_pool_address` - Largest pool address
- `main_pool_liquidity_usd` - Liquidity in largest pool
- `total_liquidity_usd` - Total across all pools
- `tvl_current` - Total value locked

**Score Calculation:**
```python
Liquidity Score =
  + 40 pts if liquidity > $1M
  + 25 pts if liquidity > $100k
  - 20 pts if liquidity < $5k
  + 30 pts if liquidity locked
  - 25 pts if liquidity NOT locked
  + 20 pts if no buy/sell taxes
  - 50 pts if honeypot detected
  = 0-100 score
```

#### ✅ Security Metrics (Working)
- `honeypot_risk` - Honeypot detection (GoPlus)
- `known_vulnerabilities` - List of issues (GoPlus)
  - Is proxy contract?
  - Is mintable?
  - Can take back ownership?
  - Has hidden owner?
  - Has selfdestruct?

**Score Calculation:**
```python
Security Score =
  + 50 pts if professionally audited
  - 50 pts if honeypot detected
  - 15 pts per known vulnerability
  + 20 pts if bug bounty active
  + 15 pts if multisig + timelock
  = 0-100 score
```

#### ⚠️ Social Metrics (Partial - Needs GitHub Token)
Currently available WITHOUT extra API keys:
- None (requires GITHUB_TOKEN)

With GITHUB_TOKEN configured:
- `github_repo` - Repository name
- `github_stars` - Star count
- `github_commits_30d` - Recent commits
- `github_contributors` - Contributor count
- `github_issues_open` - Open issues

**Score Calculation:**
```python
Social Score =
  + 30 pts if 100k+ Twitter followers
  + 20 pts if Telegram > 10k members
  + 15 pts if 50+ GitHub commits/month
  + 15 pts if 1000+ GitHub stars
  = 0-100 score
```

#### ⚠️ Team Metrics (Manual Input Required)
These require manual data entry or web scraping:
- `team_public` - Are team members public?
- `legal_entity` - Is there a legal entity?
- `whitepaper_exists` - Is there a whitepaper?
- `roadmap_exists` - Is there a roadmap?
- `documentation_quality` - Quality rating

**Score Calculation:**
```python
Team Score =
  + 30 pts if team is public
  + 20 pts if legal entity exists
  + 10 pts if whitepaper exists
  + 10 pts if roadmap exists
  + 25 pts if successful previous projects
  = 0-100 score
```

#### ⚠️ Utility Metrics (Manual Input Required)
These require protocol-specific APIs or manual entry:
- `active_users_30d` - Monthly active users
- `revenue_30d` - Monthly revenue
- `staking_enabled` - Staking available?
- `governance_enabled` - DAO governance?
- `partnerships` - List of partnerships

**Score Calculation:**
```python
Utility Score =
  + 35 pts if 10k+ active users
  + 30 pts if $100k+ monthly revenue
  + 15 pts if 50%+ staking participation
  + 20 pts if partnerships/integrations
  = 0-100 score
```

---

## 🟡 PARTIALLY WORKING (Needs Optional API Keys)

### GitHub Development Activity
**Requires:** `GITHUB_TOKEN` (free, but needs registration)
**Get it:** https://github.com/settings/tokens

**Provides:**
- Commit activity (30d, 90d)
- Contributor count
- Stars, forks, issues
- Last commit date

### LLM Summary Generation
**Requires:** `ANTHROPIC_API_KEY` (paid, $3-15/million tokens)
**Get it:** https://console.anthropic.com/

**Provides:**
- AI-generated health summary
- Natural language risk explanation
- Contextual recommendations

---

## 🔴 NOT YET IMPLEMENTED (Requires Additional APIs)

### Holder Distribution Analysis
**Blocker:** Etherscan free tier doesn't provide holder lists
**Solutions:**
1. Etherscan Pro API ($99/month) - provides holder data
2. The Graph subgraphs - query Transfer events
3. Moralis API - holder endpoint
4. Covalent API - balances endpoint

**Would Provide:**
- `holders_count` - Total unique holders
- `top_1_holder_pct` - % held by largest wallet
- `top_10_holder_pct` - % held by top 10
- `unique_wallets_30d` - Active wallets

### Twitter Sentiment
**Blocker:** Twitter API v2 requires approval + elevated access
**Get it:** https://developer.twitter.com/

**Would Provide:**
- `twitter_followers` - Follower count
- `twitter_engagement_ratio` - Engagement rate
- `sentiment_score` - Sentiment analysis

### Telegram Metrics
**Blocker:** Requires bot + group admin access
**Setup:** Create Telegram Bot, add to group as admin

**Would Provide:**
- `telegram_members` - Member count
- `telegram_active_members_24h` - Active users

### Advanced Security Audits
**Blocker:** CertiK, Hacken, etc. require paid enterprise API
**Alternative:** Manual audit database lookup

**Would Provide:**
- `audit_firm` - Auditor name
- `audit_quality` - Quality rating
- `audit_score` - Numerical score
- `certik_score` - CertiK security score

### Liquidity Lock Verification
**Blocker:** Requires querying specific locker contracts
**Solutions:**
1. Query known lockers (Unicrypt, TeamFinance, etc.)
2. Parse contract events for lock transactions

**Would Provide:**
- `liquidity_locked` - Is liquidity locked?
- `liquidity_locked_pct` - % of liquidity locked
- `liquidity_lock_until` - Lock expiration date

### Buy/Sell Tax & Slippage
**Blocker:** Requires simulated transactions
**Solutions:**
1. Honeypot.is API (free but rate limited)
2. BSCheck API (for BSC)
3. Custom simulation via Tenderly

**Would Provide:**
- `buy_tax` - Buy tax %
- `sell_tax` - Sell tax %
- `slippage_1k` - Slippage for $1k trade
- `can_buy` - Can buy successfully?
- `can_sell` - Can sell successfully?

---

## 📊 Overall Health Score - How It Works NOW

### With Current API Keys (CMC, Etherscan, Alchemy)

**Categories Available:**
1. ✅ **Market (20%)** - Full data from CMC/CoinGecko
2. ✅ **On-Chain (15%)** - Basic data from Etherscan/Alchemy
3. ✅ **Liquidity (15%)** - Basic data from DexScreener
4. ✅ **Security (15%)** - Basic checks from GoPlus
5. ❌ **Social (10%)** - Needs GITHUB_TOKEN
6. ❌ **Team (10%)** - Manual input required
7. ❌ **Utility (15%)** - Manual input required

**Example Score Breakdown:**

```
Token: UNI (Uniswap)
Contract: 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984

CATEGORY SCORES (4 of 7 available):
├─ Market:     85.0/100  (weight: 20%)  → weighted: 17.0
├─ On-Chain:   75.0/100  (weight: 15%)  → weighted: 11.25
├─ Liquidity:  82.0/100  (weight: 15%)  → weighted: 12.3
└─ Security:   70.0/100  (weight: 15%)  → weighted: 10.5

Total Weighted: 51.05
Available Weight: 65% (4 categories)

NORMALIZED SCORE: 51.05 / 0.65 = 78.5/100
RISK LEVEL: LOW
CONFIDENCE: 65% (4 of 7 categories available)
```

### With All API Keys Configured

**Categories Available:**
1. ✅ **Market (20%)** - CMC/CoinGecko
2. ✅ **On-Chain (15%)** - Etherscan/Alchemy
3. ✅ **Liquidity (15%)** - DexScreener
4. ✅ **Security (15%)** - GoPlus + Audits
5. ✅ **Social (10%)** - GitHub + Twitter
6. ✅ **Team (10%)** - Manual + Web scraping
7. ✅ **Utility (15%)** - Protocol APIs

**Confidence: 100%** (all categories)

---

## 🎯 What You Can Analyze RIGHT NOW

### Fully Supported
- ✅ Market health (price, volume, cap)
- ✅ Contract verification status
- ✅ Contract age and creator
- ✅ Basic liquidity metrics
- ✅ Honeypot detection
- ✅ Known vulnerabilities

### Example Tokens That Work Well
```python
# Major tokens (full CMC + Etherscan data)
analyze("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984")  # UNI
analyze("0x6b175474e89094c44da98b954eedeac495271d0f")  # DAI
analyze("0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9")  # AAVE

# New/small tokens (may have limited data)
analyze("0x...")  # Will work, but lower confidence
```

### What You'll Get
```json
{
  "overall_score": 78.5,
  "risk_level": "low",
  "confidence": 0.65,
  "category_scores": [
    {"category": "market", "score": 85.0, "weight": 0.20},
    {"category": "onchain", "score": 75.0, "weight": 0.15},
    {"category": "liquidity", "score": 82.0, "weight": 0.15},
    {"category": "security", "score": 70.0, "weight": 0.15}
  ],
  "red_flags": [
    "[SECURITY] No recent security audit"
  ],
  "green_flags": [
    "[MARKET] Large market cap ($1B+)",
    "[ONCHAIN] Verified contract source code",
    "[LIQUIDITY] Strong liquidity ($10M+)"
  ],
  "recommendations": [
    "Get a professional security audit from a reputable firm",
    "Build community presence on Twitter and Telegram"
  ]
}
```

---

## 🚀 Quick Upgrade Path

### Level 1: Basic (Current)
**What works:** Market + On-Chain + Basic Liquidity + Basic Security
**Confidence:** 50-65%
**Cost:** FREE (using your existing keys)

### Level 2: Development Tracking (+GITHUB_TOKEN)
**Add:** GitHub development activity
**Confidence:** 60-75%
**Cost:** FREE (requires GitHub account)
**Time:** 2 minutes to create token

### Level 3: AI Summaries (+ANTHROPIC_API_KEY)
**Add:** LLM-powered summaries and insights
**Confidence:** Same as Level 2
**Cost:** ~$0.01-0.05 per analysis
**Time:** 5 minutes to set up account

### Level 4: Social Sentiment (+TWITTER_API)
**Add:** Twitter metrics and sentiment
**Confidence:** 70-85%
**Cost:** FREE (if approved) or $100/month
**Time:** 1-2 weeks for API approval

### Level 5: Complete Data (+Paid APIs)
**Add:** Holder analysis, detailed liquidity, advanced audits
**Confidence:** 90-100%
**Cost:** $100-500/month
**Time:** Varies by API

---

## 📈 Recommended Next Steps

### Immediate (Do Now)
1. ✅ Test current system: `python example_usage.py 1`
2. ✅ Analyze a few tokens to see what data comes back
3. ✅ Integrate into FastAPI endpoint (I'll do this next)
4. ✅ Create frontend visualizations (I'll do this next)

### Short Term (This Week)
1. Add `GITHUB_TOKEN` to `.env` for development metrics
2. Test with tokens that have GitHub repos
3. Add `ANTHROPIC_API_KEY` for AI summaries (optional)

### Medium Term (This Month)
1. Decide which paid APIs are worth it for your use case
2. Implement holder distribution (if needed)
3. Add Twitter integration (if approved)
4. Build historical tracking (store scores over time)

### Long Term (Next Quarter)
1. Machine learning risk models
2. Comparative portfolio analysis
3. Real-time alerts
4. Predictive scoring
