# Quick Start Guide - Comprehensive Token Health System

## 🚀 Get Running in 3 Steps

### Step 1: Start the Backend

**Option A: Easy Mode (Windows)**
```bash
cd backend
start_backend.bat
```

**Option B: Manual (Any OS)**
```bash
cd backend
pip install -r requirements_health.txt
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

✅ **Backend is now running on http://localhost:8000**

---

### Step 2: Start the Frontend

Open a **new terminal**:

```bash
cd frontend
npm install  # First time only
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

✅ **Frontend is now running on http://localhost:5173**

---

### Step 3: Test It!

1. **Open browser:** http://localhost:5173

2. **Test Trending Tokens:**
   - Click "Trending" tab
   - Should see tokens loading from CoinMarketCap
   - No connection errors

3. **Test Comprehensive Analysis:**
   - Navigate to "Comprehensive Health" (if added to nav)
   - Try example token: `0x1f9840a85d5af5bf1d1762f925bdaddc4201f984` (UNI)
   - Click "Analyze Token"
   - Wait 1-2 seconds
   - See health score, categories, graph!

---

## 🐛 Troubleshooting

### "Connection Refused" Errors

**Problem:** Frontend shows connection errors
**Solution:**
1. Make sure backend is running on port **8000**
2. Check `frontend/vite.config.js` has `target: 'http://localhost:8000'`
3. Restart frontend after changing config

### "Comprehensive health system not available"

**Problem:** Backend logs show this warning
**Solution:**
```bash
cd backend
pip install anthropic
```

**Note:** System works without `anthropic`, you just won't get AI summaries

### "Module not found" Errors

**Problem:** Backend fails to start
**Solution:**
```bash
cd backend
pip install -r requirements_health.txt
```

### Backend Port Already in Use

**Problem:** `Address already in use`
**Solution:**

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

Or change port:
```bash
python -m uvicorn app:app --port 8001
```

And update `frontend/vite.config.js` to `target: 'http://localhost:8001'`

---

## ✅ Verify Everything Works

### 1. Check Backend Health
```bash
curl http://localhost:8000/health/status
```

Should return:
```json
{
  "status": "healthy",
  "data_sources": {
    "coinmarketcap": true,
    "etherscan": true,
    "alchemy": true
  },
  "features": ["risk_scoring", "graph_visualization", "llm_summary"]
}
```

### 2. Test Comprehensive Analysis
```bash
curl -X POST http://localhost:8000/health/comprehensive \
  -H "Content-Type: application/json" \
  -d '{"contract":"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"}'
```

Should return JSON with:
- `overall_score`
- `risk_level`
- `category_scores`
- `red_flags`, `green_flags`
- `recommendations`
- `graph` (with nodes and edges)

### 3. Test Trending Tokens
```bash
curl http://localhost:8000/tokens/trending?limit=5
```

Should return list of trending tokens.

---

## 📝 What to Test

### Basic Analysis (Works Now):
1. **UNI Token** (Uniswap)
   ```
   Contract: 0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
   Expected: 75-85 score, LOW risk
   ```

2. **LINK Token** (Chainlink)
   ```
   Contract: 0x514910771af9ca656af840dff83e8264ecf986ca
   Expected: 80-90 score, VERY_LOW risk
   ```

3. **DAI Token** (Stablecoin)
   ```
   Contract: 0x6b175474e89094c44da98b954eedeac495271d0f
   Expected: 85-95 score, VERY_LOW risk
   ```

### What You'll See:

- ✅ Overall health score (0-100)
- ✅ Risk level (very_low, low, moderate, high, critical)
- ✅ 4 category scores (market, onchain, liquidity, security)
- ✅ Red flags (issues found)
- ✅ Green flags (strengths)
- ✅ Recommendations (what to improve)
- ✅ Graph visualization (interactive network)

### What You Won't See Yet (Need Optional APIs):

- ⚠️ Social category (needs GITHUB_TOKEN)
- ⚠️ Team category (needs manual input)
- ⚠️ Utility category (needs manual input)
- ⚠️ AI summary (needs ANTHROPIC_API_KEY)
- ⚠️ Holder distribution (needs paid Etherscan Pro)

**Current confidence: 50-65%** (4 of 7 categories)

---

## 🎯 Next Steps After It's Working

### Quick Wins (Free):

1. **Add GitHub Token** (2 minutes)
   - Go to https://github.com/settings/tokens
   - Create token with `public_repo` scope
   - Add to `backend/.env`: `GITHUB_TOKEN=your_token`
   - Restart backend
   - Now get development metrics for tokens with GitHub repos

2. **Test Example Usage Script**
   ```bash
   cd backend
   python example_usage.py 1  # Basic analysis
   python example_usage.py 7  # Batch analysis
   ```

3. **Try Different Tokens**
   - Test with scam tokens (low scores)
   - Test with blue chips (high scores)
   - Compare scores

### Optional ($):

4. **Add AI Summaries** ($5/month)
   - Get API key: https://console.anthropic.com/
   - Add to `backend/.env`: `ANTHROPIC_API_KEY=your_key`
   - Enable "Include AI Summary" checkbox

5. **Add Holder Analysis** ($99/month)
   - Upgrade to Etherscan Pro
   - Get comprehensive holder distribution
   - Boost confidence to 85-95%

---

## 📚 Documentation Quick Links

- **Full Guide:** `backend/HEALTH_SYSTEM_GUIDE.md`
- **What Works Now:** `backend/CURRENT_STATUS.md`
- **Graph Design:** `GRAPH_VISUALIZATION_CONCEPT.md`
- **Complete Summary:** `IMPLEMENTATION_SUMMARY.md`
- **API Examples:** `backend/example_usage.py`

---

## 🆘 Still Having Issues?

### Check:
1. ✅ Python 3.8+ installed
2. ✅ Node.js 16+ installed
3. ✅ Backend on port 8000
4. ✅ Frontend on port 5173
5. ✅ No firewall blocking ports
6. ✅ All dependencies installed
7. ✅ `.env` file exists with API keys

### Debug Mode:
```bash
# Backend with verbose logging
cd backend
uvicorn app:app --log-level debug --port 8000

# Frontend with debug
cd frontend
npm run dev -- --debug
```

### Check API Keys:
```bash
# In backend directory
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('CMC:', bool(os.getenv('CMC_API_KEY'))); print('Etherscan:', bool(os.getenv('ETHERSCAN_API_KEY'))); print('Alchemy:', bool(os.getenv('ALCHEMY_API_KEY')))"
```

Should show:
```
CMC: True
Etherscan: True
Alchemy: True
```

---

## ✨ Success Checklist

After following this guide, you should have:

- ✅ Backend running on http://localhost:8000
- ✅ Frontend running on http://localhost:5173
- ✅ No connection errors in browser console
- ✅ Trending tokens loading successfully
- ✅ Comprehensive analysis working for test tokens
- ✅ Graph visualization rendering
- ✅ Overall health scores calculated
- ✅ Red/green flags displayed
- ✅ Recommendations shown

**If all checked, you're ready to analyze tokens! 🎉**
