# TokenHealth

**TokenHealth** is a token due-diligence system that builds an on-chain knowledge graph, computes risk heuristics, and produces an explainable health score with a short report for ERC-20/ERC-721 tokens.

## Disclaimer

**IMPORTANT:** This tool is for research and educational purposes only. It is NOT financial advice. Always verify on-chain data independently and conduct your own due diligence before making any investment decisions.

## Features

- **Risk Scoring**: Computes a 0-100 risk score based on multiple on-chain heuristics
- **Knowledge Graph**: Visualizes relationships between token, holders, liquidity pools, and owner
- **Explainable Results**: Shows which heuristics contributed to the score with detailed reasons
- **LLM-Powered Summary**: Generates human-readable summaries, top risks, and next verification steps
- **Demo Mode**: Run without API keys using seed data for testing and demonstrations
- **Docker Support**: Fully containerized for easy deployment

## Architecture

### Backend (FastAPI)
- **Framework**: Python FastAPI
- **Graph**: NetworkX for building knowledge graphs
- **Persistence**: SQLite-ready (currently in-memory for prototype)
- **LLM Agent**: Deterministic fallback for demo mode, extensible for Claude/GPT integration

### Frontend (React + Vite)
- **Framework**: React 18 with Vite
- **Graph Visualization**: Cytoscape.js with cose-bilkent layout
- **Styling**: Custom CSS with gradient backgrounds
- **API Communication**: Axios

### Data Sources (Planned)
- Etherscan API: Contract verification, token transactions
- Covalent: Token balances, top holders
- The Graph: DEX liquidity pairs
- Alchemy/Infura: RPC calls for on-chain data
- CoinGecko: Market data (optional)

**Note**: Current prototype uses seed data in demo mode. Live API integration requires API keys.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Run with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd token_dd
   ```

2. **Start the services**
   ```bash
   DEMO_MODE=true docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Try it out**
   - Click "Load Sample" to see a pre-computed analysis
   - Or enter any contract address (will use demo data in demo mode)

### Run Locally (Development)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend will run on http://localhost:8000

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on http://localhost:3000

## API Endpoints

### `GET /`
Health check and service information

### `GET /health/status`
Returns service status and available data sources

### `GET /health/sample`
Returns pre-computed sample analysis with safe token profile

### `POST /health/demo`
Analyzes token using seed data

**Request Body:**
```json
{
  "contract": "0x1234567890123456789012345678901234567890",
  "chain": "ethereum"
}
```

**Response:**
```json
{
  "risk_score": 65.0,
  "summary": [
    "DEMO shows MODERATE RISK signals (65/100)",
    "Primary concerns: top holder concentration, admin privileges.",
    "Top holder owns 35.0% of supply",
    "Verify on-chain data independently before making decisions."
  ],
  "top_risks": [
    "Top holder owns 35.0% of supply",
    "Owner has privileged functions (mint, pause, upgrade, or setFee).",
    "Low liquidity pool ($8,500)."
  ],
  "next_checks": [
    "Check if owner address is a multisig or DAO contract.",
    "Verify liquidity lock status and expiration date.",
    "Investigate top holder addresses (exchange, team, or whale)."
  ],
  "reasons": [...],
  "graph": {
    "nodes": [...],
    "edges": [...]
  },
  "metrics": {...}
}
```

### `POST /health`
Analyze token (requires API keys in production, uses demo data if `demo=true` or `DEMO_MODE=true`)

## Risk Heuristics

TokenHealth evaluates tokens using the following heuristics:

| Heuristic | Risk Impact | Description |
|-----------|-------------|-------------|
| `unverified_source_code` | +25 | Contract source code not verified on block explorer |
| `admin_privileges` | +20 | Owner has mint, pause, upgrade, or setFee functions |
| `top_holder_concentration` | +10 to +55 | High percentage held by top holders (1/3/10) |
| `recent_large_transfers` | +15 | Large transfer (>5% supply) in last 30 days |
| `minted_recently` | +30 | Significant minting (>5% supply) in last 30 days |
| `suspicious_tx_pattern` | +15 | Unusual transaction patterns (many small transfers) |
| `low_liquidity` | +20 | Liquidity pool < $10,000 |
| `low_holder_count` | +10 | Fewer than 100 token holders |
| `honeypot_check` | +50 | Failed buy/sell simulation (placeholder) |
| `liquidity_locked` | -30 | Liquidity locked in verified locker (safety factor) |
| `audit_present` | -20 | Audited by known auditor (safety factor) |

**Risk Score Interpretation:**
- **0-20**: Low Risk
- **20-40**: Low-Moderate Risk
- **40-70**: Moderate Risk
- **70-100**: High Risk

## Testing

### Run Backend Tests

```bash
cd backend
pytest test_app.py -v
```

**Test Coverage:**
- Address validation and sanitization
- Heuristics calculations (edge cases)
- Graph builder node/edge counts
- API endpoints (sample, demo, analyze)
- Risk score bounds (0-100)

## Project Structure

```
token_dd/
├── backend/
│   ├── app.py                 # FastAPI application
│   ├── heuristics.py          # Risk scoring engine
│   ├── graph_builder.py       # Knowledge graph builder
│   ├── llm_agent.py           # LLM agent (with fallback)
│   ├── test_app.py            # Unit & integration tests
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Backend container
│   └── seed_data/
│       ├── demo.json          # Demo token data
│       └── sample.json        # Sample safe token
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main React component
│   │   ├── main.jsx           # Entry point
│   │   └── index.css          # Styles
│   ├── index.html             # HTML template
│   ├── package.json           # Node dependencies
│   ├── vite.config.js         # Vite configuration
│   ├── nginx.conf             # Nginx config for production
│   └── Dockerfile             # Frontend container
├── docker-compose.yml         # Docker orchestration
├── .gitignore
└── README.md                  # This file
```

## Seed Data Format

Create custom seed data files in `backend/seed_data/` for testing:

```json
{
  "contract": "0x...",
  "symbol": "TOKEN",
  "name": "Token Name",
  "total_supply": 1000000000,
  "market_cap_usd": 500000,
  "contract_verified": true,
  "owner": "0x...",
  "owner_has_admin": false,
  "audited": true,
  "honeypot_risk": false,
  "holders": [
    {
      "address": "0x...",
      "balance": 100000000
    }
  ],
  "transfers": [
    {
      "from": "0x...",
      "to": "0x...",
      "value": 1000000,
      "timestamp": 1700000000
    }
  ],
  "liquidity": {
    "pair": "0x...",
    "liquidity_usd": 100000,
    "locked": true,
    "locker": "0x..."
  }
}
```

## LLM Agent Prompt Template

The system uses this template for generating summaries (currently uses deterministic fallback in demo mode):

```
[SYSTEM]
You are TokenHealth AGENT. Your job: given concise token metrics + graph summary,
produce a 4-line human summary, top-3 risks, and 3 immediate checks.

[USER]
Token: {symbol} ({contract})
Metrics:
  total_supply: {total_supply}
  top1_pct: {top1_pct}%
  liquidity_usd: ${liquidity_usd}
  ...

Graph summary: {graph_summary}

Instructions: produce JSON with fields:
  - "summary" (array of 4 strings)
  - "top_risks" (array of 3 strings)
  - "next_checks" (array of 3 strings)
```

## Extending for Production

### Add Live API Integration

1. **Etherscan API**
   ```python
   import requests

   def fetch_contract_info(address, api_key):
       url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}"
       response = requests.get(url)
       return response.json()
   ```

2. **Environment Variables**
   Create `.env` file:
   ```
   ETHERSCAN_API_KEY=your_key
   COVALENT_API_KEY=your_key
   ALCHEMY_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key  # For Claude LLM
   DEMO_MODE=false
   ```

3. **Update `app.py`**
   Replace seed data loading with live API calls when `DEMO_MODE=false`

### Add LLM Integration

Update `llm_agent.py`:

```python
import anthropic

def _generate_llm_summary(self, ...):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4.5-20250929",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": self._build_prompt(...)
        }]
    )

    return self._parse_llm_response(message.content[0].text)
```

## Deployment

### Deploy Backend (Cloud Run / Render)

1. Push code to GitHub
2. Connect to Cloud Run or Render
3. Set environment variables
4. Deploy from `backend/` directory

### Deploy Frontend (Vercel / Netlify)

1. Push code to GitHub
2. Connect to Vercel or Netlify
3. Set build command: `npm run build`
4. Set output directory: `dist`
5. Add environment variable: `VITE_API_BASE=https://your-backend-url.com`

## Troubleshooting

### Docker Issues

**Problem**: Backend not starting
```bash
docker-compose logs backend
```

**Solution**: Check if port 8000 is already in use

**Problem**: Frontend can't connect to backend
```bash
# Check network connectivity
docker-compose exec frontend ping backend
```

**Solution**: Ensure both services are on the same Docker network

### Development Issues

**Problem**: CORS errors
- Ensure backend CORS middleware allows frontend origin
- Check `allow_origins` in `app.py`

**Problem**: Graph not rendering
- Check browser console for errors
- Ensure cytoscape and layout libraries are loaded
- Verify graph data structure matches expected format

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest backend/test_app.py`
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Future Enhancements

- [ ] Real-time on-chain data fetching
- [ ] Support for multiple chains (BSC, Polygon, Arbitrum)
- [ ] Social sentiment analysis (Twitter, Reddit)
- [ ] Historical risk score tracking
- [ ] Honeypot detection integration
- [ ] Multi-token comparison
- [ ] Export reports as PDF
- [ ] WebSocket support for live updates
- [ ] Advanced graph analysis (centrality, clustering)
- [ ] Machine learning risk model

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation
- Review API docs at `/docs` endpoint

---

Built with FastAPI, React, NetworkX, and Cytoscape.js
