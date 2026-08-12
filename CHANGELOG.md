# Changelog

All notable changes to token-sentry will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-12

Rebuild after a full code review. Theme: the tool must never lie — no fabricated data, no silently dead scoring branches, no docs describing features that don't exist.

### Fixed
- **Honeypot signal now scores.** GoPlus honeypot/can't-sell/tax flags were stored as strings in `SecurityMetrics.known_vulnerabilities`, so the scorer's -50 honeypot penalty never fired. `GoPlusSecurityFetcher.parse_result()` now routes each signal to the metrics category where scoring reads it.
- **No more fabricated data.** Removed `_estimate_exchanges` (exchange names invented from market cap) and the `volume * 0.2` liquidity estimate. List endpoints report CMC's real `num_market_pairs`; unavailable fields are `null` and render as `N/A`.
- **Missing data no longer scores as neutral.** Empty metric categories (e.g. team/utility, which have no automated source) are excluded from scoring and confidence instead of contributing a free 50/100 at 25% combined weight.
- **Unreachable scoring branches.** The `<7 days` contract-age penalty was shadowed by the `<30 days` branch; the `>50 commits` GitHub branch was unreachable because the API returns max 30 items/page (now `per_page=100`).
- **Manipulation signal rewarded points.** Volume/mcap > 1.0 flagged "possible manipulation" while *adding* +10 to the score; it now subtracts.
- **Docker actually starts.** `python-dotenv` and `anthropic` were missing from `requirements.txt`, crashing the container on import; the compose healthcheck used `curl`, which doesn't exist in `python:slim`.
- **Address validation validates.** `sanitize_address` returned every invalid input unchanged (even prepending `0x` to garbage); invalid addresses are now 400s, and tickers pasted into the contract field get resolved.
- **Failed ticker resolutions are no longer cached forever** (`lru_cache` cached `None` for the process lifetime).
- **Error hygiene.** Exception details and tracebacks no longer leak into HTTP 500 responses; CORS no longer combines wildcard origins with credentials.
- Deprecated APIs: `datetime.utcnow()`, sqlite3's implicit datetime adapter, and an outdated Claude model ID.

### Changed
- `POST /health` is implemented (alias for `/health/comprehensive`) instead of returning 501.
- Ports standardized: backend :8000, frontend :3000 — compose, docs, and UI error messages now agree.
- One name everywhere: **token-sentry** (was TokenHealth in docs, token_dd in clone instructions).
- README rewritten to describe the actual product; added `CLAUDE.md` (AI-assist context) and `backend/.env.example`.

### Added
- Real pytest suite (`backend/tests/`, 34 tests): scoring-engine branch reachability, honeypot wiring, empty-category handling, address validation, API error hygiene, GoPlus parsing, cache behavior, and no-fabricated-data guarantees.
- Configurable CORS origins (`CORS_ORIGINS`), `requirements-dev.txt`, optional `env_file` in compose.

### Removed
- Dead v1 code: `heuristics.py`, `graph_builder.py`, `llm_agent.py` (an "LLM agent" that never called an LLM), `example_usage.py`, `App.jsx`, `ComprehensiveHealth.jsx`, demo/seed-data scaffolding, `requirements_health.txt`.
- CHANGELOG claims that were never true (the 1.0.0 entry below described a test suite and seed data that did not exist in the repository).

## [1.0.0] - 2025-12-08

### Added
- Initial release of TokenHealth prototype
- **Backend (FastAPI)**
  - REST API with 5 endpoints: `/`, `/health/status`, `/health/sample`, `/health/demo`, `/health`
  - 11 risk heuristics for token analysis
  - Knowledge graph builder using NetworkX
  - LLM agent with deterministic fallback
  - Demo mode using seed data
  - Address validation and sanitization
  - Comprehensive test suite (pytest)

- **Frontend (React + Vite)**
  - Single-page application
  - Interactive graph visualization using Cytoscape.js
  - Real-time risk score calculation and display
  - Responsive design with gradient UI
  - Summary, risks, and recommended checks display
  - Detailed metrics and reasons breakdown

- **Heuristics**
  - `unverified_source_code`: +25 risk
  - `admin_privileges`: +20 risk
  - `top_holder_concentration`: +10 to +55 risk
  - `recent_large_transfers`: +15 risk
  - `minted_recently`: +30 risk
  - `suspicious_tx_pattern`: +15 risk
  - `low_liquidity`: +20 risk
  - `low_holder_count`: +10 risk
  - `honeypot_check`: +50 risk (placeholder)
  - `liquidity_locked`: -30 risk (safety factor)
  - `audit_present`: -20 risk (safety factor)

- **Infrastructure**
  - Docker support for backend and frontend
  - Docker Compose for orchestration
  - Nginx configuration for production frontend
  - Multi-stage builds for optimized images
  - Health checks for services

- **Seed Data**
  - `demo.json`: High-risk token example
  - `sample.json`: Low-risk safe token example
  - Custom contract-specific seed data support

- **Documentation**
  - Comprehensive README with architecture and usage
  - Quick start guide for 5-minute setup
  - Contributing guidelines
  - Project structure documentation
  - Changelog (this file)
  - MIT License

- **Developer Tools**
  - Makefile with common commands
  - Windows batch script (run.bat)
  - Unix shell script (run.sh)
  - .gitignore for Python and Node
  - .dockerignore for optimized builds

- **Testing**
  - Unit tests for address validation
  - Unit tests for all heuristics
  - Integration tests for API endpoints
  - Graph builder tests
  - Test coverage for risk score bounds

### Technical Stack
- **Backend**: Python 3.11, FastAPI 0.104, NetworkX 3.2, Pytest 7.4
- **Frontend**: React 18, Vite 5, Cytoscape.js 3.27, Axios 1.6
- **DevOps**: Docker, Docker Compose, Nginx
- **Graph**: NetworkX (backend), Cytoscape.js (frontend)
- **Layout**: cose-bilkent algorithm for graph visualization

### Architecture
- RESTful API design
- Modular backend structure
- Separation of concerns (heuristics, graph, LLM agent)
- Deterministic fallback for demo mode
- Extensible design for API integration
- Responsive frontend with mobile support

### Known Limitations (v1.0)
- Demo mode only (no live blockchain data fetching)
- No user authentication or API keys
- Single-worker backend (no horizontal scaling)
- In-memory graph storage (no persistence)
- LLM agent uses deterministic fallback only
- Honeypot detection is placeholder only
- No social sentiment analysis
- Ethereum mainnet only (no multi-chain support)

## [Unreleased]

### Planned Features
- [ ] Live API integration (Etherscan, Covalent, The Graph)
- [ ] Multi-chain support (BSC, Polygon, Arbitrum)
- [ ] Real LLM integration (Claude API)
- [ ] User authentication and API keys
- [ ] Historical risk score tracking
- [ ] Social sentiment analysis
- [ ] Honeypot detection integration
- [ ] WebSocket support for live updates
- [ ] Export reports as PDF
- [ ] Advanced graph analytics
- [ ] Rate limiting and caching
- [ ] PostgreSQL persistence
- [ ] Multi-token comparison
- [ ] Mobile app (React Native)

### Bug Fixes
- None yet (v1.0 initial release)

---

## Version History Summary

- **v1.0.0** (2025-12-08): Initial prototype release with demo mode

---

For detailed changes, see the [commit history](https://github.com/yourusername/tokenhealth/commits/).

To upgrade, see [UPGRADE.md](UPGRADE.md) (to be created for future versions).
