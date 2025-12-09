# TokenHealth Troubleshooting Guide

## Issue: Empty Trending Table

If you see "no error but nothing shows in table", follow these steps:

### Step 1: Check Backend Console Output

When you run the backend, you should see console logs like:
```
Fetching trending from: https://api.dexscreener.com/latest/dex/tokens/trending
Response status: 200
Received X pairs from DEXScreener
Returning X trending tokens for chain ethereum
```

**What to check:**
- Is the status code 200?
- How many pairs were received?
- How many tokens are being returned?

### Step 2: Check Frontend Console (Browser F12)

Open browser console and look for:
```
Fetching from: /api/tokens/trending?limit=20
Trending response: {trending: Array(20), count: 20, ...}
Trending array: [...]
Trending length: 20
Setting trending data with 20 tokens
```

**What to check:**
- Is the API call being made?
- What does the response look like?
- Is the trending array populated?

### Step 3: Test API Directly

Run the test script:
```bash
cd backend
python test_api.py
```

This will test the DEXScreener API directly and show if there are any connectivity issues.

### Step 4: Test Backend Endpoint

Use curl to test the backend:
```bash
curl http://localhost:8000/tokens/trending?limit=5
```

Should return JSON with trending tokens.

### Step 5: Check Backend is Running

Make sure the backend is running:
```bash
cd backend
python app.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Check Frontend Dev Server

Make sure Vite is running:
```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.x.x  ready in XXX ms
➜  Local:   http://localhost:5173/
```

## Common Issues

### Issue: DEXScreener API Returns Empty Data

**Cause:** The `/tokens/trending` endpoint might not exist or be rate-limited

**Solution:** The backend will now show detailed error messages. Check backend console.

### Issue: CORS Error

**Symptoms:** Browser console shows "CORS policy" error

**Solution:**
1. Make sure backend is running with CORS enabled (it should be by default)
2. Check that frontend proxy is configured correctly in vite.config.js

### Issue: Network Error

**Symptoms:** "Failed to load trending tokens: Network Error"

**Solution:**
1. Check backend is running on port 8000
2. Check firewall isn't blocking localhost connections
3. Try accessing http://localhost:8000 directly in browser

### Issue: Rate Limiting

**Symptoms:** Backend shows 429 status code

**Solution:**
- DEXScreener has rate limits
- Backend caches for 5 minutes to avoid this
- Wait a few minutes and try again

## Debug Checklist

- [ ] Backend is running on port 8000
- [ ] Frontend dev server is running on port 5173
- [ ] Browser console shows API call being made
- [ ] Backend console shows receiving API request
- [ ] test_api.py script succeeds
- [ ] curl to backend endpoint returns data
- [ ] No errors in browser console
- [ ] No errors in backend console

## Still Not Working?

Check the improved error messages:
1. Frontend now shows detailed empty state with retry button
2. Backend logs show exactly what's happening with the API
3. Browser console shows detailed logging of API responses

If the issue persists, it's likely the DEXScreener API endpoint has changed or is not available. You may need to:
1. Use a different API endpoint
2. Add API keys for more reliable data sources
3. Use mock data for testing
