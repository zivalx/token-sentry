"""
Example Usage of Token Health Pipeline

Demonstrates various ways to use the comprehensive token health analysis system.
"""

import os
import sys
import logging
from token_health_pipeline import TokenHealthPipeline, analyze_and_print

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_1_basic_analysis():
    """Example 1: Basic token analysis with environment variables"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Analysis")
    print("="*80 + "\n")

    # Analyze USDT on Ethereum
    contract = "0xdac17f958d2ee523a2206206994597c13d831ec7"
    chain = "ethereum"

    health_data = analyze_and_print(contract, chain)

    # Access individual metrics
    if health_data.health_score:
        print(f"\n✓ Analysis complete!")
        print(f"Overall Score: {health_data.health_score.overall_score:.1f}/100")
        print(f"Risk Level: {health_data.health_score.risk_level.value}")


def example_2_custom_api_keys():
    """Example 2: Custom initialization with specific API keys"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Custom API Keys")
    print("="*80 + "\n")

    # Initialize pipeline with custom API keys
    pipeline = TokenHealthPipeline(
        cmc_api_key="your_cmc_api_key",
        etherscan_api_key="your_etherscan_api_key",
        alchemy_api_key="your_alchemy_api_key",
        github_token="your_github_token",
        enable_cache=True,
        cache_ttl=600  # 10 minutes
    )

    # Analyze Chainlink (LINK)
    contract = "0x514910771af9ca656af840dff83e8264ecf986ca"

    health_data = pipeline.analyze_token(
        contract=contract,
        chain="ethereum",
        include_llm_summary=False  # Disable LLM for faster results
    )

    print(f"Health Score: {health_data.health_score.overall_score:.1f}/100")


def example_3_with_llm_summary():
    """Example 3: Analysis with AI-powered summary"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Analysis with LLM Summary")
    print("="*80 + "\n")

    # Make sure ANTHROPIC_API_KEY is set in environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY not set, skipping LLM summary")
        return

    pipeline = TokenHealthPipeline.from_env()

    # Analyze Uniswap (UNI)
    contract = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"

    health_data = pipeline.analyze_token(
        contract=contract,
        chain="ethereum",
        include_llm_summary=True  # Enable AI summary
    )

    # Print full summary including LLM analysis
    print(pipeline.export_summary(health_data))


def example_4_export_results():
    """Example 4: Export results to JSON"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Export Results")
    print("="*80 + "\n")

    pipeline = TokenHealthPipeline.from_env()

    # Analyze multiple tokens
    tokens = [
        ("0x6b175474e89094c44da98b954eedeac495271d0f", "ethereum", "DAI"),
        ("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "ethereum", "USDC"),
    ]

    for contract, chain, name in tokens:
        print(f"\nAnalyzing {name}...")

        health_data = pipeline.analyze_token(contract, chain)

        # Export to JSON
        filename = f"health_report_{name.lower()}.json"
        pipeline.export_json(health_data, filename)

        print(f"✓ Exported to {filename}")
        print(f"  Score: {health_data.health_score.overall_score:.1f}/100")
        print(f"  Risk: {health_data.health_score.risk_level.value}")


def example_5_detailed_breakdown():
    """Example 5: Detailed category breakdown"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Detailed Category Breakdown")
    print("="*80 + "\n")

    pipeline = TokenHealthPipeline.from_env()

    # Analyze Wrapped Bitcoin (WBTC)
    contract = "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599"

    health_data = pipeline.analyze_token(contract, "ethereum")

    if health_data.health_score:
        print(f"\n{'Category':<15} {'Score':<10} {'Weight':<10} {'Weighted':<12}")
        print("-" * 50)

        for cat_score in health_data.health_score.category_scores:
            print(
                f"{cat_score.category.capitalize():<15} "
                f"{cat_score.score:<10.1f} "
                f"{cat_score.weight*100:<10.0f}% "
                f"{cat_score.weighted_score:<12.2f}"
            )

        print("-" * 50)
        print(f"{'TOTAL':<15} {'':<10} {'':<10} {health_data.health_score.overall_score:<12.1f}")

        # Show issues by category
        print("\n\nISSUES BY CATEGORY:")
        for cat_score in health_data.health_score.category_scores:
            if cat_score.issues:
                print(f"\n{cat_score.category.upper()}:")
                for issue in cat_score.issues:
                    print(f"  ⚠️  {issue}")


def example_6_multi_chain():
    """Example 6: Multi-chain analysis"""
    print("\n" + "="*80)
    print("EXAMPLE 6: Multi-Chain Analysis")
    print("="*80 + "\n")

    pipeline = TokenHealthPipeline.from_env()

    # Analyze same token on different chains
    tokens = [
        ("0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d", "bsc", "USDC (BSC)"),
        ("0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "polygon", "USDC (Polygon)"),
    ]

    for contract, chain, name in tokens:
        print(f"\nAnalyzing {name}...")

        health_data = pipeline.analyze_token(contract, chain)

        if health_data.health_score:
            print(f"  Score: {health_data.health_score.overall_score:.1f}/100")
            print(f"  Risk: {health_data.health_score.risk_level.value}")
            print(f"  Confidence: {health_data.health_score.confidence * 100:.0f}%")


def example_7_batch_analysis():
    """Example 7: Batch analysis of multiple tokens"""
    print("\n" + "="*80)
    print("EXAMPLE 7: Batch Analysis")
    print("="*80 + "\n")

    pipeline = TokenHealthPipeline.from_env()

    # Analyze a portfolio of tokens
    portfolio = [
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",  # UNI
        "0x7fc66500c84a76ad7e9c93437bfc5ac33e2ddae9",  # AAVE
        "0xc00e94cb662c3520282e6f5717214004a7f26888",  # COMP
    ]

    results = []

    for contract in portfolio:
        try:
            health_data = pipeline.analyze_token(contract, "ethereum")
            results.append({
                "contract": contract,
                "symbol": health_data.market.symbol if health_data.market else "N/A",
                "score": health_data.health_score.overall_score,
                "risk": health_data.health_score.risk_level.value
            })
        except Exception as e:
            logger.error(f"Failed to analyze {contract}: {e}")

    # Print summary table
    print(f"\n{'Symbol':<10} {'Score':<10} {'Risk Level':<15} {'Contract'}")
    print("-" * 80)

    for result in sorted(results, key=lambda x: x["score"], reverse=True):
        print(
            f"{result['symbol']:<10} "
            f"{result['score']:<10.1f} "
            f"{result['risk']:<15} "
            f"{result['contract']}"
        )


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("TOKEN HEALTH PIPELINE - EXAMPLE USAGE")
    print("="*80)

    # Check for required environment variables
    required_vars = ["CMC_API_KEY", "ETHERSCAN_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"\n⚠️  Warning: Missing environment variables: {', '.join(missing)}")
        print("Some examples may not work properly.")
        print("\nPlease set the following in your .env file:")
        for var in missing:
            print(f"  {var}=your_api_key_here")
        print()

    examples = [
        ("Basic Analysis", example_1_basic_analysis),
        ("Custom API Keys", example_2_custom_api_keys),
        ("LLM Summary", example_3_with_llm_summary),
        ("Export Results", example_4_export_results),
        ("Category Breakdown", example_5_detailed_breakdown),
        ("Multi-Chain", example_6_multi_chain),
        ("Batch Analysis", example_7_batch_analysis),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\n" + "-"*80)

    # Run specific example or all
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            if 1 <= example_num <= len(examples):
                name, func = examples[example_num - 1]
                print(f"\nRunning Example {example_num}: {name}")
                func()
            else:
                print(f"Invalid example number. Choose 1-{len(examples)}")
        except ValueError:
            print("Usage: python example_usage.py [example_number]")
    else:
        # Run first example by default
        print("\nRunning Example 1 (use 'python example_usage.py N' for specific example)")
        example_1_basic_analysis()

    print("\n✓ Examples complete!\n")


if __name__ == "__main__":
    main()
