"""
TokenHealth Backend - FastAPI application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import json
from pathlib import Path
from time import time

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from heuristics import HeuristicsEngine
from graph_builder import GraphBuilder
from llm_agent import LLMAgent
from ticker_resolver import get_resolver
from db import get_db

# Import new comprehensive health system
try:
    from token_health_pipeline import TokenHealthPipeline
    COMPREHENSIVE_HEALTH_AVAILABLE = True
except ImportError:
    COMPREHENSIVE_HEALTH_AVAILABLE = False
    print("⚠️  Comprehensive health system not available. Run: pip install anthropic")

app = FastAPI(title="TokenHealth API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthRequest(BaseModel):
    contract: Optional[str] = Field(None, description="Token contract address or ticker symbol")
    ticker: Optional[str] = Field(None, description="Token ticker symbol (alternative to contract)")
    chain: str = Field(default="ethereum", description="Blockchain network")


class HealthResponse(BaseModel):
    risk_score: float
    summary: List[str]
    top_risks: List[str]
    next_checks: List[str]
    reasons: List[Dict[str, Any]]
    graph: Dict[str, Any]
    metrics: Dict[str, Any]


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
    return {"service": "TokenHealth", "version": "1.0.0"}


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
async def health_analyze(request: HealthRequest):
    """Analyze token with live blockchain data"""
    # Resolve contract address (from ticker if provided)
    contract = await resolve_contract_address(request)

    # TODO: Implement live blockchain data fetching
    # This will require integration with:
    # - Etherscan/block explorer for contract verification and holder data
    # - Alchemy/Infura for blockchain queries
    # - DEX APIs for liquidity data

    raise HTTPException(
        status_code=501,
        detail="Live analysis coming soon. Use /health/comprehensive instead."
    )


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
    if not COMPREHENSIVE_HEALTH_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Comprehensive health system not available. Install: pip install anthropic"
        )

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

        return ComprehensiveHealthResponse(
            overall_score=health_data.health_score.overall_score,
            risk_level=health_data.health_score.risk_level.value,
            confidence=health_data.health_score.confidence,
            data_completeness=health_data.data_completeness,
            category_scores=category_scores,
            red_flags=health_data.health_score.red_flags,
            yellow_flags=health_data.health_score.yellow_flags,
            green_flags=health_data.health_score.green_flags,
            recommendations=health_data.health_score.recommendations,
            summary=health_data.health_score.summary,
            metrics=metrics,
            graph=graph
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )


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
        resolver = get_resolver()
        address = resolver.resolve(request.ticker, request.chain)
        if not address:
            raise HTTPException(
                status_code=404,
                detail=f"Token ticker '{request.ticker}' not found on {request.chain}"
            )
        return sanitize_address(address)

    # Otherwise use contract address
    if request.contract:
        return sanitize_address(request.contract)

    raise HTTPException(
        status_code=400,
        detail="Either 'contract' address or 'ticker' symbol is required"
    )


def sanitize_address(address: str) -> str:
    """Validate and sanitize Ethereum address - lenient mode for best-effort analysis"""
    if not address:
        raise HTTPException(status_code=400, detail="Contract address is required")

    # Remove whitespace
    address = address.strip()

    # If it's a placeholder (cmc_xxx), return as-is for market-only analysis
    if address.startswith("cmc_"):
        return address

    # Check if starts with 0x
    if not address.startswith("0x"):
        # Could be a ticker symbol - return as-is
        if len(address) <= 10 and address.isalnum():
            return address
        address = "0x" + address

    # Check length (42 chars: 0x + 40 hex chars)
    if len(address) != 42:
        # Not a valid Ethereum address, but return it anyway for market analysis
        return address

    # Check if valid hex
    try:
        int(address, 16)
        return address
    except ValueError:
        # Invalid hex, but return for market-only analysis
        return address


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


def analyze_token(seed_data: Dict[str, Any]) -> HealthResponse:
    """Core analysis logic"""

    # 1. Build graph
    graph_builder = GraphBuilder()
    graph = graph_builder.build_from_seed(seed_data)

    # 2. Compute heuristics
    heuristics_engine = HeuristicsEngine()
    heuristics_result = heuristics_engine.compute(seed_data, graph)

    risk_score = heuristics_result["risk_score"]
    reasons = heuristics_result["reasons"]
    metrics = heuristics_result["metrics"]

    # 3. LLM agent summary
    llm_agent = LLMAgent()
    agent_result = llm_agent.generate_summary(
        symbol=seed_data.get("symbol", "UNKNOWN"),
        contract=seed_data.get("contract", "0x0"),
        metrics=metrics,
        graph_summary=graph_builder.get_summary(graph),
        reasons=reasons
    )

    # 4. Format response
    return HealthResponse(
        risk_score=risk_score,
        summary=agent_result.get("summary", []),
        top_risks=agent_result.get("top_risks", []),
        next_checks=agent_result.get("next_checks", []),
        reasons=reasons,
        graph={
            "nodes": graph["nodes"],
            "edges": graph["edges"]
        },
        metrics=metrics
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
