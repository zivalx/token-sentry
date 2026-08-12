"""
token-sentry backend - FastAPI application
"""
import logging
import os
import re
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from ticker_resolver import get_resolver
from db import get_db
from token_health_pipeline import TokenHealthPipeline

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("token_sentry")

app = FastAPI(title="token-sentry API", version="2.0.0")

# CORS: origins are configurable; wildcard is only valid WITHOUT credentials.
_cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:4000,http://localhost:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ETH_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

class HealthRequest(BaseModel):
    contract: Optional[str] = Field(None, description="Token contract address or ticker symbol")
    ticker: Optional[str] = Field(None, description="Token ticker symbol (alternative to contract)")
    chain: str = Field(default="ethereum", description="Blockchain network")


class ComprehensiveHealthResponse(BaseModel):
    """Enhanced health response with category scores"""
    overall_score: float
    risk_level: str
    confidence: float
    data_completeness: float
    category_scores: List[Dict[str, Any]]
    red_flags: List[str]
    yellow_flags: List[str]
    green_flags: List[str]
    recommendations: List[str]
    summary: Optional[str] = None
    metrics: Dict[str, Any]
    graph: Optional[Dict[str, Any]] = None  # Enhanced graph visualization


@app.get("/")
async def root():
    return {"service": "token-sentry", "version": "2.0.0"}


@app.get("/health/status")
async def health_status():
    """Service health check and available data sources"""
    db = get_db()
    cache_stats = db.get_stats()

    return {
        "status": "healthy",
        "data_sources": {
            "coinmarketcap": bool(os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY")),
            "etherscan": bool(os.getenv("ETHERSCAN_API_KEY")),
            "alchemy": bool(os.getenv("ALCHEMY_API_KEY")),
        },
        "features": ["risk_scoring", "graph_visualization", "llm_summary"],
        "cache": cache_stats
    }


@app.post("/health")
async def health_analyze(
    request: HealthRequest,
    include_llm: bool = False,
    github_repo: Optional[str] = None
) -> ComprehensiveHealthResponse:
    """Analyze a token. Alias for /health/comprehensive."""
    return await run_comprehensive_analysis(request, include_llm, github_repo)


@app.post("/health/comprehensive")
async def comprehensive_health_analyze(
    request: HealthRequest,
    include_llm: bool = False,
    github_repo: Optional[str] = None
) -> ComprehensiveHealthResponse:
    """
    Comprehensive token health analysis with 7-category scoring

    Returns detailed health metrics across:
    - Market (20%): Price, volume, market cap
    - On-Chain (15%): Holder distribution, contract verification
    - Liquidity (15%): Pool depth, locked liquidity
    - Security (15%): Audits, vulnerabilities, exploits
    - Social (10%): Community engagement, development
    - Team (10%): Transparency, documentation
    - Utility (15%): Real usage, revenue, adoption

    Params:
    - include_llm: Generate AI summary (requires ANTHROPIC_API_KEY)
    - github_repo: GitHub repo URL for development metrics
    """
    return await run_comprehensive_analysis(request, include_llm, github_repo)


async def run_comprehensive_analysis(
    request: HealthRequest,
    include_llm: bool = False,
    github_repo: Optional[str] = None
) -> ComprehensiveHealthResponse:
    """Shared implementation behind /health and /health/comprehensive."""
    # Resolve contract address
    contract = await resolve_contract_address(request)

    try:
        # Initialize pipeline
        pipeline = TokenHealthPipeline.from_env()

        # Run comprehensive analysis
        health_data = pipeline.analyze_token(
            contract=contract,
            chain=request.chain,
            include_llm_summary=include_llm,
            github_repo=github_repo,
            fetch_social=True,
            fetch_security=True
        )

        # Build enhanced graph for visualization
        graph = build_health_graph(health_data)

        # Extract metrics for response
        metrics = {
            "market": health_data.market.__dict__ if health_data.market else {},
            "onchain": health_data.onchain.__dict__ if health_data.onchain else {},
            "liquidity": health_data.liquidity.__dict__ if health_data.liquidity else {},
            "security": health_data.security.__dict__ if health_data.security else {},
            "social": health_data.social.__dict__ if health_data.social else {},
            "team": health_data.team.__dict__ if health_data.team else {},
            "utility": health_data.utility.__dict__ if health_data.utility else {},
        }

        # Format category scores
        category_scores = [
            {
                "category": cs.category,
                "score": cs.score,
                "weight": cs.weight,
                "weighted_score": cs.weighted_score,
                "factors": cs.factors,
                "issues": cs.issues,
                "strengths": cs.strengths
            }
            for cs in health_data.health_score.category_scores
        ]

        # Snapshot for score-over-time tracking — never blocks the response
        try:
            get_db().save_score(
                address=contract,
                chain=request.chain,
                score=health_data.health_score.overall_score,
                risk_level=health_data.health_score.risk_level.value,
                confidence=health_data.health_score.confidence,
            )
        except Exception:
            logger.warning(f"Failed to record score history for {contract}", exc_info=True)

        return ComprehensiveHealthResponse(
            overall_score=health_data.health_score.overall_score,
            risk_level=health_data.health_score.risk_level.value,
            confidence=health_data.health_score.confidence,
            data_completeness=health_data.health_score.data_completeness,
            category_scores=category_scores,
            red_flags=health_data.health_score.red_flags,
            yellow_flags=health_data.health_score.yellow_flags,
            green_flags=health_data.health_score.green_flags,
            recommendations=health_data.health_score.recommendations,
            summary=health_data.health_score.summary,
            metrics=metrics,
            graph=graph
        )

    except HTTPException:
        raise
    except Exception:
        # Full detail to the server log; a generic message to the client —
        # internal errors must never leak to the browser
        logger.exception(f"Analysis failed for {contract}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@app.get("/health/history/{address}")
async def score_history(address: str, chain: str = "ethereum", limit: int = 30):
    """
    Score snapshots recorded on each completed analysis, newest first.
    History accrues on demand — a token has entries only if it was analyzed.
    """
    address = sanitize_address(address)
    history = get_db().get_score_history(address, chain, limit)
    return {"address": address, "chain": chain, "count": len(history), "history": history}


@app.get("/tokens/search")
async def search_tokens(query: str, chain: str = "ethereum", limit: int = 10):
    """
    Search for tokens by name or ticker
    Returns list of matching tokens with addresses
    """
    resolver = get_resolver()
    results = resolver.search(query, chain, limit)
    return {"results": results, "count": len(results)}


@app.get("/tokens/trending")
async def trending_tokens(chain: str = "ethereum", limit: int = 20):
    """
    Get trending tokens from CoinMarketCap with database caching
    Returns list of hot tokens with price, volume, liquidity, exchanges, risk
    Cache: 10 minutes in SQLite database
    """
    # Fetch data (will use database cache automatically)
    resolver = get_resolver()
    results = resolver.get_trending(chain, limit)

    return {
        "trending": results,
        "count": len(results),
        "chain": chain,
        "source": "coinmarketcap"
    }


@app.get("/tokens/newest")
async def newest_tokens(chain: str = "ethereum", limit: int = 20):
    """
    Get newest/recently added tokens from CoinMarketCap with database caching
    Sorted by date_added (newest first)
    Cache: 10 minutes in SQLite database
    """
    resolver = get_resolver()
    results = resolver.get_newest(chain, limit)

    return {
        "newest": results,
        "count": len(results),
        "chain": chain,
        "source": "coinmarketcap"
    }


@app.get("/tokens/gainers")
async def top_gainers(chain: str = "ethereum", limit: int = 20):
    """
    Get top gaining tokens (24h % change) from CoinMarketCap with database caching
    Sorted by percent_change_24h (biggest gains first)
    Cache: 10 minutes in SQLite database
    """
    resolver = get_resolver()
    results = resolver.get_top_gainers(chain, limit)

    return {
        "gainers": results,
        "count": len(results),
        "chain": chain,
        "source": "coinmarketcap"
    }


@app.post("/tokens/resolve")
async def resolve_ticker(ticker: str, chain: str = "ethereum"):
    """
    Resolve ticker symbol to contract address
    """
    resolver = get_resolver()
    address = resolver.resolve(ticker, chain)

    if not address:
        raise HTTPException(status_code=404, detail=f"Token '{ticker}' not found on {chain}")

    return {"ticker": ticker, "address": address, "chain": chain}


async def resolve_contract_address(request: HealthRequest) -> str:
    """
    Resolve contract address from request (supports both address and ticker)
    """
    # If ticker provided, resolve it first
    if request.ticker:
        return _resolve_ticker_or_404(request.ticker, request.chain)

    if request.contract:
        contract = request.contract.strip()
        # A ticker pasted into the contract field gets resolved, not rejected
        if not contract.startswith(("0x", "cmc_")) and _looks_like_ticker(contract):
            return _resolve_ticker_or_404(contract, request.chain)
        return sanitize_address(contract)

    raise HTTPException(
        status_code=400,
        detail="Either 'contract' address or 'ticker' symbol is required"
    )


def _looks_like_ticker(value: str) -> bool:
    return 1 <= len(value) <= 10 and value.isalnum()


def _resolve_ticker_or_404(ticker: str, chain: str) -> str:
    resolver = get_resolver()
    address = resolver.resolve(ticker, chain)
    if not address:
        raise HTTPException(
            status_code=404,
            detail=f"Token ticker '{ticker}' not found on {chain}"
        )
    return sanitize_address(address)


def sanitize_address(address: str) -> str:
    """Validate an Ethereum contract address (or a cmc_ placeholder).

    Anything else is a 400 — passing garbage downstream produced confusing
    500s and wasted API calls.
    """
    if not address:
        raise HTTPException(status_code=400, detail="Contract address is required")

    address = address.strip()

    # cmc_<id> placeholders identify CMC-listed tokens without a contract
    # address on the requested chain (market-only analysis)
    if address.startswith("cmc_") and address[4:].isdigit():
        return address

    if ETH_ADDRESS_RE.match(address):
        return address

    raise HTTPException(
        status_code=400,
        detail="Invalid contract address: expected 0x followed by 40 hex characters"
    )


def build_health_graph(health_data) -> Dict[str, Any]:
    """
    Build enhanced graph visualization for token health

    Graph shows:
    - Central token node
    - Category score nodes (7 categories)
    - Factor nodes (issues and strengths)
    - Edges showing relationships and impact
    """
    from health_models import TokenHealthData

    nodes = []
    edges = []

    # Central token node
    token_id = "token_center"
    symbol = health_data.market.symbol if health_data.market else "TOKEN"
    overall_score = health_data.health_score.overall_score if health_data.health_score else 50

    # Color based on score
    if overall_score >= 80:
        token_color = "#10b981"  # green
    elif overall_score >= 60:
        token_color = "#3b82f6"  # blue
    elif overall_score >= 40:
        token_color = "#f59e0b"  # orange
    else:
        token_color = "#ef4444"  # red

    nodes.append({
        "id": token_id,
        "label": f"{symbol}\n{overall_score:.1f}/100",
        "type": "token",
        "shape": "hexagon",
        "color": token_color,
        "size": 60,
        "score": overall_score
    })

    if not health_data.health_score:
        return {"nodes": nodes, "edges": edges}

    # Category nodes
    for cat_score in health_data.health_score.category_scores:
        cat_id = f"cat_{cat_score.category}"

        # Color based on category score
        if cat_score.score >= 70:
            cat_color = "#10b981"  # green
        elif cat_score.score >= 50:
            cat_color = "#3b82f6"  # blue
        elif cat_score.score >= 30:
            cat_color = "#f59e0b"  # orange
        else:
            cat_color = "#ef4444"  # red

        nodes.append({
            "id": cat_id,
            "label": f"{cat_score.category.upper()}\n{cat_score.score:.0f}",
            "type": "category",
            "shape": "circle",
            "color": cat_color,
            "size": 40,
            "score": cat_score.score,
            "weight": cat_score.weight
        })

        # Edge from token to category (weighted)
        edge_width = cat_score.weight * 10  # Scale weight for visibility
        edges.append({
            "source": token_id,
            "target": cat_id,
            "label": f"{cat_score.weight*100:.0f}%",
            "type": "category_weight",
            "width": edge_width,
            "color": "#94a3b8"
        })

        # Factor nodes (top 3 issues or strengths per category)
        factor_count = 0
        max_factors = 3  # Limit to keep graph readable

        # Add issue nodes (red)
        for issue in cat_score.issues[:max_factors]:
            if factor_count >= max_factors:
                break
            factor_id = f"issue_{cat_score.category}_{factor_count}"
            nodes.append({
                "id": factor_id,
                "label": issue[:40] + "..." if len(issue) > 40 else issue,
                "type": "issue",
                "shape": "rectangle",
                "color": "#fca5a5",
                "size": 20
            })
            edges.append({
                "source": cat_id,
                "target": factor_id,
                "type": "issue",
                "color": "#ef4444",
                "width": 2
            })
            factor_count += 1

        # Add strength nodes (green) if no issues
        if factor_count == 0:
            for strength in cat_score.strengths[:max_factors]:
                if factor_count >= max_factors:
                    break
                factor_id = f"strength_{cat_score.category}_{factor_count}"
                nodes.append({
                    "id": factor_id,
                    "label": strength[:40] + "..." if len(strength) > 40 else strength,
                    "type": "strength",
                    "shape": "rectangle",
                    "color": "#86efac",
                    "size": 20
                })
                edges.append({
                    "source": cat_id,
                    "target": factor_id,
                    "type": "strength",
                    "color": "#10b981",
                    "width": 2
                })
                factor_count += 1

    return {
        "nodes": nodes,
        "edges": edges,
        "layout": "radial",  # Suggest radial layout with token at center
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "categories": len(health_data.health_score.category_scores)
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
