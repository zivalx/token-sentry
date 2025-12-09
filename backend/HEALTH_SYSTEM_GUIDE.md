# Comprehensive Token Health Scoring System

## Overview

The Token Health Scoring System provides holistic evaluation of cryptocurrency tokens across **7 major categories**:

1. **Market (20%)** - Price stability, volume, market cap
2. **On-Chain (15%)** - Holder distribution, contract age, supply
3. **Liquidity (15%)** - Pool depth, locked liquidity, slippage
4. **Security (15%)** - Audits, vulnerabilities, exploits
5. **Social (10%)** - Community engagement, development activity
6. **Team (10%)** - Transparency, track record, documentation
7. **Utility (15%)** - Real usage, revenue, adoption

**Overall Score**: 0-100 (weighted aggregate)
**Risk Levels**: Very Low, Low, Moderate, High, Critical

---

## Architecture

### Modular Components

```
token_health_pipeline.py       # Main orchestration
├── health_models.py           # Data structures (40+ metrics)
├── data_fetchers.py           # API integrations
├── health_scorer.py           # Scoring engine
└── example_usage.py           # Usage examples
```

### Data Flow

```
1. FETCH     → Gather data from multiple APIs
2. TRANSFORM → Normalize and enrich data
3. SCORE     → Calculate weighted health scores
4. LLM       → Generate AI-powered summary (optional)
5. EXPORT    → JSON/Text output
```

---

## Data Model

### 7 Metrics Categories

#### 1. MarketMetrics (20+ fields)
```python
- price_usd, market_cap, fdv
- volume_24h, volume_7d
- price_change_24h/7d/30d
- price_30d_volatility
- exchanges_listed
- cmc_rank, coingecko_rank
```

#### 2. OnChainMetrics (30+ fields)
```python
- contract_age_days, source_verified
- proxy_contract, owner_address
- owner_renounced, owner_has_admin
- total_supply, circulating_supply
- holders_count
- top_1/3/10/50_holder_pct
- unique_wallets_24h/7d/30d
- tx_count_24h/7d/30d
```

#### 3. LiquidityMetrics (20+ fields)
```python
- main_dex, main_pool_liquidity_usd
- total_liquidity_usd
- liquidity_locked, liquidity_locked_pct
- buy_tax, sell_tax
- slippage_1k/10k/100k
- honeypot_risk, can_buy, can_sell
```

#### 4. SecurityMetrics (15+ fields)
```python
- audit_exists, audit_firm, audit_quality
- exploits_reported
- known_vulnerabilities
- bug_bounty_active, bug_bounty_amount
- certik_score
- multisig_enabled, timelock_enabled
```

#### 5. SocialMetrics (20+ fields)
```python
- twitter_followers, twitter_engagement_ratio
- telegram_members, discord_members
- github_stars, github_commits_30d
- github_contributors
- sentiment_score
```

#### 6. TeamMetrics (15+ fields)
```python
- team_public, legal_entity
- whitepaper_exists, roadmap_exists
- previous_projects, previous_exits
- documentation_quality
- regular_updates
```

#### 7. UtilityMetrics (20+ fields)
```python
- active_users_24h/7d/30d
- revenue_24h/7d/30d
- revenue_per_user
- staking_enabled, staking_apy
- governance_enabled
- partnerships, integrations
```

---

## Data Sources

### Currently Integrated

| Source | Category | Free Tier | Status |
|--------|----------|-----------|--------|
| **CoinMarketCap** | Market | 333 calls/day | ✅ Working |
| **CoinGecko** | Market | 50 calls/min | ✅ Working |
| **Etherscan** | On-Chain | 5 calls/sec | ✅ Working |
| **Alchemy** | On-Chain | 300M CU/month | ✅ Working |
| **DexScreener** | Liquidity | Unlimited | ✅ Working |
| **GoPlus Security** | Security | Free | ✅ Working |
| **GitHub** | Social | 60 calls/hour | ✅ Working |

### Available for Integration

| Source | Category | Notes |
|--------|----------|-------|
| Twitter API v2 | Social | Requires approval |
| Telegram Bot API | Social | Requires bot + group access |
| Discord API | Social | Requires bot token |
| CertiK API | Security | Paid tier only |
| Messari API | Market | Free tier available |
| The Graph | On-Chain | Subgraph queries |

---

## Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements_health.txt
```

Create `requirements_health.txt`:
```
requests>=2.31.0
anthropic>=0.18.0  # For LLM summaries
python-dotenv>=1.0.0
```

### 2. Configure API Keys

Edit `.env` file:
```bash
# Required
ETHERSCAN_API_KEY='your_key_here'
CMC_API_KEY='your_key_here'
ALCHEMY_API_KEY='your_key_here'

# Optional
GITHUB_TOKEN='your_token_here'
ANTHROPIC_API_KEY='your_key_here'
```

### 3. Test Installation

```bash
python example_usage.py 1
```

---

## Usage Examples

### Basic Usage

```python
from token_health_pipeline import TokenHealthPipeline

# Initialize from environment variables
pipeline = TokenHealthPipeline.from_env()

# Analyze a token
health_data = pipeline.analyze_token(
    contract="0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI
    chain="ethereum"
)

# Print results
print(f"Score: {health_data.health_score.overall_score}/100")
print(f"Risk: {health_data.health_score.risk_level}")
```

### Quick Analysis

```python
from token_health_pipeline import analyze_and_print

# One-line analysis with console output
analyze_and_print(
    contract="0x6b175474e89094c44da98b954eedeac495271d0f",  # DAI
    chain="ethereum"
)
```

### With LLM Summary

```python
health_data = pipeline.analyze_token(
    contract="0x...",
    chain="ethereum",
    include_llm_summary=True  # Requires ANTHROPIC_API_KEY
)

print(health_data.health_score.summary)
```

### Export Results

```python
# Export to JSON
pipeline.export_json(health_data, "report.json")

# Export human-readable summary
summary = pipeline.export_summary(health_data)
print(summary)
```

### Batch Analysis

```python
tokens = [
    "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI
    "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",  # AAVE
    "0xc00e94cb662c3520282e6f5717214004a7f26888",  # COMP
]

for contract in tokens:
    health_data = pipeline.analyze_token(contract, "ethereum")
    print(f"{health_data.market.symbol}: {health_data.health_score.overall_score:.1f}")
```

---

## Scoring Methodology

### Category Weighting

```python
DEFAULT_CATEGORY_WEIGHTS = {
    "market": 0.20,      # 20%
    "onchain": 0.15,     # 15%
    "liquidity": 0.15,   # 15%
    "security": 0.15,    # 15%
    "social": 0.10,      # 10%
    "team": 0.10,        # 10%
    "utility": 0.15,     # 15%
}
```

### Scoring Logic Examples

#### Market Score (0-100)
- **Market Cap** (30 pts max)
  - >$1B: +30 pts
  - >$100M: +20 pts
  - >$10M: +10 pts
  - <$1M: -10 pts

- **Volume/MCap Ratio** (20 pts max)
  - 5-50% (healthy): +20 pts
  - >100% (suspicious): +10 pts
  - <1% (illiquid): -15 pts

- **Volatility** (20 pts max)
  - <20% (stable): +20 pts
  - <50% (moderate): +10 pts
  - >100% (extreme): -15 pts

#### On-Chain Score (0-100)
- **Contract Age** (25 pts max)
  - >1 year: +25 pts
  - >6 months: +15 pts
  - <30 days: -15 pts
  - <7 days: -25 pts

- **Source Verified** (20 pts)
  - Yes: +20 pts
  - No: -25 pts (major red flag)

- **Holder Concentration** (30 pts max)
  - Top 10 <30%: +30 pts
  - Top 10 <50%: +20 pts
  - Top 10 >85%: -25 pts

#### Security Score (0-100)
- **Audit** (50 pts max)
  - Elite audit: +50 pts
  - Comprehensive: +40 pts
  - Standard: +30 pts
  - None: -20 pts

- **Exploits** (critical)
  - Each exploit: -15 pts (max -40)

- **Bug Bounty** (20 pts max)
  - >$100k bounty: +20 pts
  - Active: +15 pts

### Risk Levels

| Score Range | Risk Level | Description |
|-------------|-----------|-------------|
| 80-100 | Very Low | Excellent fundamentals |
| 60-80 | Low | Good overall health |
| 40-60 | Moderate | Some concerns |
| 20-40 | High | Multiple red flags |
| 0-20 | Critical | Severe issues |

---

## Flags & Recommendations

### Red Flags (Critical)
- Honeypot detected
- Cannot sell tokens
- Contract not verified
- Exploits reported
- Extremely new contract (<7 days)

### Yellow Flags (Warning)
- High holder concentration
- Low liquidity (<$10k)
- No audit
- Anonymous team
- Low trading volume

### Green Flags (Positive)
- Verified contract
- Liquidity locked
- Professional audit
- Public team
- Active development

### Auto-Generated Recommendations
- Based on lowest 3 scoring categories
- Actionable suggestions
- Risk-appropriate advice

---

## API Integration Guide

### Adding New Data Fetchers

1. **Create Fetcher Class**
```python
from data_fetchers import DataFetcher
from health_models import SocialMetrics

class TwitterFetcher(DataFetcher):
    def fetch(self, handle: str) -> Optional[SocialMetrics]:
        # Implementation
        pass
```

2. **Register Fetcher**
```python
# In DataFetcherRegistry
def register_social_fetchers(self, twitter_token: str):
    self.fetchers["twitter"] = TwitterFetcher(twitter_token)
```

3. **Use in Pipeline**
```python
# In TokenHealthPipeline._fetch_social_data
if "twitter" in self.registry.list_fetchers():
    fetcher = self.registry.get_fetcher("twitter")
    twitter_metrics = fetcher.fetch(twitter_handle)
```

### Rate Limiting Best Practices

- Use built-in caching (`cache_ttl` parameter)
- Implement exponential backoff (see `_request_with_retry`)
- Respect API rate limits
- Cache responses in SQLite for production

---

## Advanced Features

### Custom Scoring Weights

```python
custom_weights = {
    "market": 0.10,
    "onchain": 0.15,
    "liquidity": 0.20,  # Emphasize liquidity
    "security": 0.30,   # Emphasize security
    "social": 0.05,
    "team": 0.10,
    "utility": 0.10,
}

scorer = HealthScorer(category_weights=custom_weights)
pipeline = TokenHealthPipeline.from_env()
pipeline.scorer = scorer
```

### Multi-Chain Analysis

```python
chains = ["ethereum", "bsc", "polygon"]

for chain in chains:
    health_data = pipeline.analyze_token(contract, chain)
    print(f"{chain}: {health_data.health_score.overall_score:.1f}")
```

### Confidence Scoring

The system calculates confidence based on:
- **Data completeness** (70% weight): % of fields populated
- **Category coverage** (30% weight): # of categories analyzed

```python
confidence = health_data.health_score.confidence
print(f"Confidence: {confidence * 100:.0f}%")
```

---

## Integration with Existing System

### Update FastAPI Endpoints

```python
from token_health_pipeline import TokenHealthPipeline

@app.post("/health/comprehensive")
async def comprehensive_health(request: HealthRequest):
    pipeline = TokenHealthPipeline.from_env()

    health_data = pipeline.analyze_token(
        contract=request.contract,
        chain=request.chain,
        include_llm_summary=True
    )

    return {
        "score": health_data.health_score.overall_score,
        "risk_level": health_data.health_score.risk_level,
        "category_scores": [
            {
                "category": cs.category,
                "score": cs.score,
                "weight": cs.weight
            }
            for cs in health_data.health_score.category_scores
        ],
        "red_flags": health_data.health_score.red_flags,
        "recommendations": health_data.health_score.recommendations,
        "summary": health_data.health_score.summary,
        "confidence": health_data.health_score.confidence
    }
```

### Frontend Visualization

Use the category scores for charts:
```javascript
// In React component
const categoryData = response.category_scores.map(cat => ({
  category: cat.category,
  score: cat.score,
  weight: cat.weight * 100
}));

// Render radar chart, bar chart, etc.
```

---

## Performance Optimization

### Caching Strategy

1. **In-memory cache** (current)
   - 10-minute TTL
   - Per-fetcher caching

2. **SQLite cache** (recommended)
   - Persistent across restarts
   - Shared across instances

3. **Redis cache** (production)
   - Distributed caching
   - Sub-second response times

### Parallel Fetching

```python
import concurrent.futures

def fetch_all_parallel(self, contract, chain):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(self._fetch_market_data, contract, chain): "market",
            executor.submit(self._fetch_onchain_data, contract, chain): "onchain",
            executor.submit(self._fetch_liquidity_data, contract, chain): "liquidity",
            executor.submit(self._fetch_security_data, contract, chain): "security",
        }

        results = {}
        for future in concurrent.futures.as_completed(futures):
            category = futures[future]
            results[category] = future.result()

        return results
```

---

## Troubleshooting

### Common Issues

**1. "All market data fetchers failed"**
- Check CMC_API_KEY is valid
- Verify API rate limits not exceeded
- Try CoinGecko as fallback (no key needed)

**2. "Some on-chain fetchers failed"**
- Etherscan free tier: 5 calls/sec limit
- Add delay between requests
- Enable caching to reduce calls

**3. "LLM summary generation failed"**
- Check ANTHROPIC_API_KEY is set
- Verify API credits available
- LLM summary is optional, score still calculated

**4. Low confidence score**
- Not all API keys configured
- Token too new (missing historical data)
- DEX not supported by data sources

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

pipeline = TokenHealthPipeline.from_env()
health_data = pipeline.analyze_token(contract, chain)

# Check what data was fetched
print(f"Data completeness: {health_data.calculate_completeness():.2%}")
print(f"Populated fields: {health_data.get_field_count()}")
print(f"Errors: {health_data.errors}")
```

---

## Roadmap

### Phase 1: Core Enhancement ✅
- [x] Enhanced data model (40+ metrics)
- [x] Modular fetchers
- [x] Weighted scoring system
- [x] LLM integration

### Phase 2: Data Expansion
- [ ] Twitter sentiment analysis
- [ ] Telegram metrics
- [ ] Discord metrics
- [ ] Historical price patterns
- [ ] Whale wallet tracking

### Phase 3: Advanced Analytics
- [ ] Machine learning risk models
- [ ] Anomaly detection
- [ ] Predictive scoring
- [ ] Comparative analysis
- [ ] Portfolio risk assessment

### Phase 4: Production Features
- [ ] PostgreSQL backend
- [ ] Redis caching
- [ ] Background job queue
- [ ] WebSocket real-time updates
- [ ] API rate limiter

---

## API Reference

### TokenHealthPipeline

**Constructor**
```python
TokenHealthPipeline(
    cmc_api_key: Optional[str] = None,
    etherscan_api_key: Optional[str] = None,
    alchemy_api_key: Optional[str] = None,
    github_token: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    enable_cache: bool = True,
    cache_ttl: int = 600
)
```

**Methods**
- `from_env()` → Create from environment variables
- `analyze_token(contract, chain, **kwargs)` → Run analysis
- `export_json(health_data, filepath)` → Export to JSON
- `export_summary(health_data)` → Human-readable report

### HealthScorer

**Constructor**
```python
HealthScorer(category_weights: Optional[Dict[str, float]] = None)
```

**Methods**
- `score_token(health_data)` → Calculate scores

### DataFetcherRegistry

**Methods**
- `register_market_fetchers(**keys)`
- `register_onchain_fetchers(**keys)`
- `register_liquidity_fetchers()`
- `register_security_fetchers()`
- `register_social_fetchers(**tokens)`
- `get_fetcher(name)` → Retrieve fetcher
- `list_fetchers()` → List all registered

---

## Contributing

### Adding New Metrics

1. Update `health_models.py` dataclass
2. Add fetcher logic to `data_fetchers.py`
3. Add scoring logic to `health_scorer.py`
4. Update documentation

### Testing

```bash
# Unit tests (to be implemented)
pytest tests/test_health_scorer.py
pytest tests/test_data_fetchers.py

# Integration tests
python example_usage.py 7  # Batch analysis
```

---

## License

Same as parent project.

## Support

- GitHub Issues: https://github.com/anthropics/claude-code/issues
- Documentation: This file
- Examples: `example_usage.py`
