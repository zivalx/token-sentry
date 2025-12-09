# API Keys Setup Guide

Complete guide to getting free API keys for TokenHealth.

## Required vs Optional APIs

### ✅ Completely Free (No Keys Needed)

| Service | Purpose | Rate Limit | Cost |
|---------|---------|------------|------|
| **DEXScreener** | Trending tokens, pair data | Unlimited | FREE |
| **CoinGecko** | Token search, basic data | 10-50 calls/min | FREE |

These work out-of-the-box without any registration!

### 🔑 Free Tier (Requires Registration)

| Service | Purpose | Free Tier | Sign Up Time |
|---------|---------|-----------|--------------|
| **Etherscan** | Contract verification | 5 calls/sec | ~2 minutes |
| **Alchemy** | RPC blockchain calls | 300M compute units/month | ~3 minutes |
| **CoinMarketCap** | Market data (optional) | 333 calls/day | ~2 minutes |

**Total setup time: ~10 minutes**

---

## Step-by-Step Setup

### 1. Etherscan API Key (Required)

**What it does**: Verifies contract source code, gets transaction history

**Free tier**: 5 calls/second (enough for ~400K calls/day)

**Steps**:
1. Go to https://etherscan.io/register
2. Create account (email + password)
3. Verify email
4. Go to https://etherscan.io/myapikey
5. Click "Add" to create new API key
6. Copy your API key

**Time**: ~2 minutes

**Example key**: `ABC123XYZ789EXAMPLE`

---

### 2. Alchemy API Key (Required)

**What it does**: Connects to Ethereum blockchain, reads contract data

**Free tier**: 300 million compute units/month (plenty for prototypes)

**Steps**:
1. Go to https://alchemy.com
2. Click "Get started for free"
3. Sign up with email or GitHub
4. Create a new app:
   - Name: TokenHealth
   - Chain: Ethereum
   - Network: Mainnet
5. Click on your app
6. Click "API Keys" tab
7. Copy your API key

**Time**: ~3 minutes

**Example key**: `abc123xyz789example`

---

### 3. CoinMarketCap API Key (Optional)

**What it does**: Gets market cap, volume, and ranking data

**Free tier**: 333 calls/day (10K calls/month)

**Steps**:
1. Go to https://coinmarketcap.com/api
2. Click "Get Your Free API Key Now"
3. Fill out registration form
4. Verify email
5. Go to https://pro.coinmarketcap.com/account
6. Copy your API key from dashboard

**Time**: ~2 minutes

**Example key**: `abcd1234-ef56-7890-ghij-klmnopqrstuv`

---

## Configuration

### Create `.env` file

Create a file named `.env` in the `backend/` directory:

```bash
# Required for contract verification and transaction data
ETHERSCAN_API_KEY=your_etherscan_key_here

# Required for blockchain RPC calls
ALCHEMY_API_KEY=your_alchemy_key_here

# Optional for market data
COINMARKETCAP_API_KEY=your_cmc_key_here

# Set to false to use live APIs
DEMO_MODE=false
```

**Windows**:
```cmd
cd backend
notepad .env
```

**Mac/Linux**:
```bash
cd backend
nano .env
```

### Example `.env` file

```bash
ETHERSCAN_API_KEY=ABC123XYZ789EXAMPLE
ALCHEMY_API_KEY=abc123xyz789example
COINMARKETCAP_API_KEY=abcd1234-ef56-7890-ghij-klmnopqrstuv
DEMO_MODE=false
```

---

## Testing Your API Keys

### Test Etherscan

```bash
curl "https://api.etherscan.io/api?module=stats&action=ethsupply&apikey=YOUR_KEY"
```

Should return JSON with ETH supply.

### Test Alchemy

```bash
curl -X POST https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

Should return current block number.

### Test in TokenHealth

```bash
# Start backend
cd backend
python app.py

# Test ticker resolution
curl http://localhost:8000/tokens/resolve?ticker=PEPE

# Test trending tokens
curl http://localhost:8000/tokens/trending?limit=10

# Test search
curl http://localhost:8000/tokens/search?query=shiba
```

---

## Rate Limits Summary

| Service | Free Tier Limit | Enough For |
|---------|----------------|------------|
| Etherscan | 5 calls/sec | ~400K calls/day |
| Alchemy | 300M compute/month | ~1M requests |
| CoinMarketCap | 333 calls/day | Small projects |
| DEXScreener | Unlimited | ∞ |
| CoinGecko | 10-50 calls/min | ~15K calls/day |

**For a prototype or small app**: These limits are MORE than enough!

---

## Cost Breakdown

### Current Setup (Free Forever)

| Service | Monthly Cost | Annual Cost |
|---------|--------------|-------------|
| Etherscan | **$0** | **$0** |
| Alchemy | **$0** | **$0** |
| DEXScreener | **$0** | **$0** |
| CoinGecko | **$0** | **$0** |
| **TOTAL** | **$0** | **$0** |

### If You Exceed Free Tiers

| Service | Paid Tier | When You Need It |
|---------|-----------|------------------|
| Etherscan | $99-$199/month | >5 calls/sec sustained |
| Alchemy | $49-$499/month | >300M compute units |
| CoinMarketCap | $29-$499/month | >333 calls/day |

**For 99% of users**: Free tier is sufficient!

---

## New Features Enabled

### 1. Ticker Support

**Before** (address only):
```bash
curl -X POST http://localhost:8000/health \
  -d '{"contract": "0x1234567890..."}'
```

**After** (ticker support):
```bash
# Using ticker
curl -X POST http://localhost:8000/health \
  -d '{"ticker": "PEPE"}'

# Still supports address
curl -X POST http://localhost:8000/health \
  -d '{"contract": "0x1234567890..."}'
```

### 2. Token Search

Search by name or ticker:

```bash
curl http://localhost:8000/tokens/search?query=shiba&limit=10
```

**Response**:
```json
{
  "results": [
    {
      "symbol": "SHIB",
      "name": "SHIBA INU",
      "address": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
      "chain": "ethereum"
    }
  ],
  "count": 1
}
```

### 3. Trending Tokens

Get hot tokens/memecoins:

```bash
curl http://localhost:8000/tokens/trending?limit=20
```

**Response**:
```json
{
  "trending": [
    {
      "symbol": "PEPE",
      "name": "Pepe",
      "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
      "priceUsd": "0.00000123",
      "volume24h": 12500000,
      "priceChange24h": 15.5,
      "liquidity": 5000000
    }
  ],
  "count": 20
}
```

### 4. Ticker Resolution

Resolve ticker to address:

```bash
curl -X POST http://localhost:8000/tokens/resolve?ticker=PEPE
```

**Response**:
```json
{
  "ticker": "PEPE",
  "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
  "chain": "ethereum"
}
```

---

## Frontend Integration

The frontend now supports ticker input. Users can enter either:
- Contract address: `0x1234567890...`
- Ticker symbol: `PEPE`, `SHIB`, `UNI`, etc.

The backend automatically resolves tickers to addresses.

---

## Multi-Chain Support

TokenHealth supports multiple chains:

```bash
# Ethereum (default)
curl http://localhost:8000/tokens/trending?chain=ethereum

# Binance Smart Chain
curl http://localhost:8000/tokens/trending?chain=bsc

# Polygon
curl http://localhost:8000/tokens/trending?chain=polygon

# Arbitrum
curl http://localhost:8000/tokens/trending?chain=arbitrum
```

**Note**: For non-Ethereum chains, you'll need API keys for those networks too (e.g., BSCScan for BSC).

---

## Troubleshooting

### "Token not found" error

**Problem**: Ticker doesn't resolve to address

**Solutions**:
1. Try the full name instead of ticker
2. Use contract address directly
3. Token might not be listed on CoinGecko/DEXScreener yet
4. Check spelling

### Rate limit exceeded

**Problem**: Too many API calls

**Solutions**:
1. Add caching (Redis recommended)
2. Implement request queuing
3. Upgrade to paid tier
4. Use demo mode for development

### Invalid API key

**Problem**: API returns 401/403 error

**Solutions**:
1. Check `.env` file exists in `backend/` directory
2. Verify API key is copied correctly (no spaces)
3. Restart backend after updating `.env`
4. Check if key is activated on provider's dashboard

---

## Security Best Practices

### ✅ DO

- Keep `.env` file in `.gitignore`
- Use environment variables
- Rotate keys periodically
- Monitor usage on provider dashboards
- Use separate keys for dev/prod

### ❌ DON'T

- Commit API keys to GitHub
- Share keys publicly
- Use production keys in development
- Hardcode keys in source code
- Use same key across multiple projects

---

## Alternative Free APIs

If you want more options:

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **Infura** | Ethereum RPC | 100K requests/day |
| **QuickNode** | Blockchain RPC | 1M credits |
| **Moralis** | NFT/token data | 40K compute/day |
| **Ankr** | Multi-chain RPC | 500M credits |
| **Covalent** | Token data | 100K credits |

All have generous free tiers!

---

## Summary

### Minimal Setup (5 minutes)

1. Get **Etherscan** key
2. Get **Alchemy** key
3. Create `.env` file
4. Set `DEMO_MODE=false`
5. Done!

### Full Setup (10 minutes)

Add CoinMarketCap for enhanced market data.

### No Setup (0 minutes)

Use `DEMO_MODE=true` (default) - no keys needed!

---

**Questions?** Open an issue on GitHub or check the [README](README.md) for more details.
