# Token Sentry

**Token Sentry** is a token due-diligence tool for ERC-20 tokens (Ethereum, BSC, Polygon). It aggregates market, on-chain, liquidity, security, and development data from public APIs and produces an explainable 0-100 health score across weighted categories — plus a trending/newest/gainers dashboard.

## Disclaimer

**IMPORTANT:** This tool is for research and educational purposes only. It is NOT financial advice. Scores are heuristics computed from public API data, which may be incomplete or stale. Always verify on-chain data independently before making any decisions.

## What it does

- **Health scoring** — weighted 0-100 score across up to 7 categories (market, on-chain, liquidity, security, social, team, utility). Categories with no fetched data are excluded from the score and reported through a `confidence` / `data_completeness` pair — missing data is never scored as "neutral".
- **Honeypot & contract-safety checks** — GoPlus security flags (honeypot, can't-sell, hidden owner, taxes) feed directly into the scoring.
- **Token discovery** — trending / newest / top-gainer lists from CoinMarketCap, with a keyless CoinGecko fallback for trending; SQLite caching (10-min TTL, stale-cache fallback).
- **Ticker resolution** — analyze by ticker (`PEPE`) or contract address; resolution via CoinGecko with DexScreener fallback.
- **AI summaries (optional)** — Claude-generated analyst summary when an `ANTHROPIC_API_KEY` is configured.

### Data honesty

Every number shown is fetched from a source, never inferred. Fields no source provides (e.g. per-token liquidity in list views) are shown as `N/A` — earlier versions estimated them, which is exactly what a due-diligence tool must not do.

## Data sources

| Source | Used for | Key required |
|---|---|---|
| CoinGecko | Market data, ticker resolution, trending fallback | No (free tier) |
| DexScreener | Liquidity/pairs, ticker fallback | No |
| GoPlus Security | Honeypot, taxes, contract flags | No |
| CoinMarketCap | Trending/newest/gainers lists (richer than the fallback) | Yes (free tier, 333 calls/day) |
| Etherscan V2 (ETH/BSC/Polygon) | Contract verification, creation date | Yes (free tier) |
| Alchemy | Supplementary on-chain data | Yes (free tier) |
| GitHub | Development activity | Optional (higher rate limits) |
| Anthropic | AI summaries | Yes (only for `include_llm`) |

All keys are optional — the app degrades gracefully to the keyless sources. See [API_SETUP.md](API_SETUP.md) for step-by-step key setup.

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/zivalx/token-sentry.git
cd token-sentry
cp backend/.env.example backend/.env   # optional: add your API keys
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

### Local development

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
uvicorn app:app --reload          # http://localhost:8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000, proxies /api to :8000
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Service info |
| `/health/status` | GET | Health check, configured data sources, cache stats |
| `/health` | POST | Analyze a token (alias for `/health/comprehensive`) |
| `/health/comprehensive` | POST | Full 7-category analysis. Query params: `include_llm`, `github_repo` |
| `/tokens/trending` | GET | Trending tokens (`?chain=ethereum&limit=20`) |
| `/tokens/newest` | GET | Recently added tokens |
| `/tokens/gainers` | GET | Top 24h gainers |
| `/tokens/search` | GET | Search tokens by name/ticker (`?query=...`) |
| `/tokens/resolve` | POST | Resolve ticker to contract address |

**Analysis request body** (`/health`, `/health/comprehensive`):

```json
{
  "contract": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
  "chain": "ethereum"
}
```

`contract` accepts a `0x` address or a ticker symbol; `ticker` may be used instead. Invalid addresses return `400`.

**Response** (abridged):

```json
{
  "overall_score": 72.4,
  "risk_level": "low",
  "confidence": 0.61,
  "data_completeness": 0.55,
  "category_scores": [
    {"category": "market", "score": 85.0, "weight": 0.2, "issues": [], "strengths": ["Large market cap ($1B+)"]}
  ],
  "red_flags": [],
  "yellow_flags": ["[ONCHAIN] Owner has admin privileges"],
  "green_flags": ["[LIQUIDITY] Strong liquidity ($4,200,000)"],
  "recommendations": ["..."],
  "metrics": {"market": {}, "onchain": {}, "liquidity": {}, "security": {}}
}
```

`overall_score` is a **health** score: higher = healthier. `risk_level` maps 80-100 → very_low … 0-20 → critical.

## Scoring model

Weights: market 20% · on-chain 15% · liquidity 15% · security 15% · utility 15% · social 10% · team 10%.

Each category starts at 50 and moves with evidence (e.g. verified source +20, honeypot −50, unverified contract −25, locked liquidity up to +30). Categories with **no fetched data are skipped** and the remaining weights are renormalized; `confidence` reflects how much data backed the score. The full factor breakdown is returned in `category_scores[].factors` so every score is auditable.

## Testing

```bash
cd backend
venv/bin/pytest tests -v        # or: ./run.sh test
```

The suite covers the scoring engine (branch reachability, honeypot wiring, empty-category handling), address validation, API error hygiene, GoPlus response parsing, cache behavior, and the no-fabricated-data guarantees.

## Project structure

```
token-sentry/
├── backend/
│   ├── app.py                    # FastAPI app: endpoints, validation, CORS
│   ├── token_health_pipeline.py  # Orchestration: fetch → merge → score → summarize
│   ├── health_scorer.py          # 7-category weighted scoring engine
│   ├── health_models.py          # Dataclasses for all metrics + score types
│   ├── data_fetchers.py          # Per-source fetchers (CoinGecko, Etherscan, GoPlus, ...)
│   ├── cmc_client.py             # CoinMarketCap client for list endpoints
│   ├── ticker_resolver.py        # Ticker → contract address resolution
│   ├── db.py                     # SQLite cache for list endpoints
│   ├── tests/                    # pytest suite
│   └── requirements.txt          # runtime deps (requirements-dev.txt for tests)
├── frontend/
│   └── src/
│       ├── TrendingApp.jsx       # Main app: token lists + analyze search
│       ├── TokenExpandedRow.jsx  # Inline risk/market details
│       └── TokenDetailModal.jsx  # Detail modal
├── docker-compose.yml            # backend :8000, frontend :3000
└── CLAUDE.md                     # Context for AI-assisted development
```

## Roadmap

- [ ] Holder-concentration data (requires a paid explorer tier or Transfer-event indexing — currently reported as unavailable, not guessed)
- [ ] Liquidity-lock detection (locker contracts)
- [ ] Multi-chain expansion (Arbitrum, Base)
- [ ] Historical score tracking
- [ ] Social metrics (Twitter/Telegram APIs)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). TDD is the house rule: a bug fix starts with a failing test.

## License

MIT — see [LICENSE](LICENSE).
