# CLAUDE.md

Context for AI-assisted development on **token-sentry** — a token due-diligence tool (FastAPI backend + React frontend) that scores ERC-20 tokens from public API data.

## Cardinal rule: no fabricated data

This is a due-diligence tool. **Never present inferred, estimated, or invented values as observed data.** If a source doesn't provide a field, return `None` and let the UI show `N/A`. The v1 codebase estimated exchange listings from market cap and liquidity as `volume * 0.2`; both were removed in v2 and tests in `backend/tests/test_cmc_client.py` guard against regressions. Any new "estimate" must be labeled as such in the field name and the UI.

## Architecture

```
frontend (React/Vite, :3000) ──/api──▶ app.py (FastAPI, :8000)
                                        │
                        ┌───────────────┼──────────────────┐
                        ▼               ▼                  ▼
              token_health_pipeline   ticker_resolver    cmc_client + db.py
              (fetch→merge→score)     (ticker→address)   (list endpoints, SQLite cache)
                        │
              data_fetchers.py (CoinGecko, CMC, Etherscan, Alchemy, DexScreener, GoPlus, GitHub)
              health_scorer.py (7-category weighted score)
              health_models.py (dataclasses)
```

- **Two data paths**: list endpoints (`/tokens/*`) go through `cmc_client` + SQLite cache; per-token analysis (`/health*`) goes through `token_health_pipeline`.
- **Score semantics**: `overall_score` is HEALTH (high = good). The trending list's `riskScore` is RISK (high = bad). The frontend converts with `100 - overall_score` when merging an analysis into the list. Don't mix them up.
- **Signal routing**: GoPlus returns one blob; `GoPlusSecurityFetcher.parse_result()` routes each signal to the category where scoring reads it — honeypot/taxes → `LiquidityMetrics`, contract flags → `OnChainMetrics`, vulnerabilities → `SecurityMetrics`. A signal on the wrong dataclass silently never scores (this was v1's worst bug).
- **Missing data is absent, not neutral**: the scorer skips metrics objects with no populated fields (`has_data()` in `health_models.py`); weights renormalize; `confidence`/`data_completeness` tell the user how much data backed the score. Never attach empty metrics objects "for shape".

## Development rules

- **TDD**: bug fixes and features start with a failing test in `backend/tests/`. Run: `cd backend && venv/bin/pytest tests -v`.
- **Error hygiene**: exception details go to the server log (`logger.exception`), never into HTTP responses. Validation failures are 400s raised in `sanitize_address` / `resolve_contract_address` before any fetching.
- **Caching**: cache successes, never failures (`ticker_resolver` learned this the hard way). SQLite timestamps are ISO strings — sqlite3's implicit datetime adapter is deprecated (Python 3.12+).
- **Datetimes**: timezone-aware only (`datetime.now(timezone.utc)`), never `datetime.utcnow()`.
- **Free-tier awareness**: CMC free tier is 333 calls/day — that's why list results are cached in SQLite for 10 min with stale-cache fallback. Don't add per-row API calls to list endpoints.
- **Known limitation**: holder-concentration data needs a paid explorer tier; `EtherscanFetcher._get_token_holders` returns `None` on purpose. Concentration heuristics only run when data exists — don't fake it.

## Commands

```bash
docker-compose up --build          # full stack (backend :8000, frontend :3000)
cd backend && uvicorn app:app --reload    # backend dev
cd frontend && npm run dev                # frontend dev (proxies /api → :8000)
cd backend && venv/bin/pytest tests -v    # test suite
```

## Configuration

All via `backend/.env` (see `backend/.env.example`). Every API key is optional; the pipeline registers only the fetchers whose keys exist. `CORS_ORIGINS` is a comma-separated allowlist (wildcard+credentials is forbidden and tested against).

## Naming

The project is **token-sentry** ("Token Sentry" in UI copy). Historical names (TokenHealth, token_dd) must not reappear in docs or code.
