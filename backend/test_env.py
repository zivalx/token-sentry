"""
Quick test to verify environment variables are loading
Run this to check if your API keys are being detected
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("=" * 60)
print("Environment Variable Test")
print("=" * 60)

# Check each API key
api_keys = {
    "CoinMarketCap": os.getenv("CMC_API_KEY") or os.getenv("COINMARKETCAP_API_KEY"),
    "Etherscan": os.getenv("ETHERSCAN_API_KEY"),
    "Alchemy": os.getenv("ALCHEMY_API_KEY"),
    "GitHub": os.getenv("GITHUB_TOKEN"),
    "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
}

all_good = True

for name, value in api_keys.items():
    if value:
        # Show first 8 chars and last 4 chars
        if len(value) > 12:
            masked = f"{value[:8]}...{value[-4:]}"
        else:
            masked = value[:4] + "..." if len(value) > 4 else "***"
        print(f"✅ {name:15} : {masked}")
    else:
        print(f"❌ {name:15} : NOT SET")
        if name in ["CoinMarketCap", "Etherscan", "Alchemy"]:
            all_good = False

print("=" * 60)

if all_good:
    print("✅ All required API keys are loaded!")
    print("   You can now start the backend.")
else:
    print("❌ Missing required API keys!")
    print("   Check backend/.env file")

print("=" * 60)
