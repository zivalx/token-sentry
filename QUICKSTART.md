# TokenHealth - Quick Start Guide

Get TokenHealth running in under 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Git (optional, for cloning)

## Step 1: Get the Code

```bash
git clone <repository-url>
cd token_dd
```

Or download and extract the ZIP file.

## Step 2: Start the Services

### Option A: Using Docker Compose (Recommended)

```bash
# Windows
run.bat up-build

# Mac/Linux
chmod +x run.sh
./run.sh up-build

# Or directly with docker-compose
DEMO_MODE=true docker-compose up --build
```

Wait for the build to complete (first time takes 2-3 minutes).

## Step 3: Access the Application

Open your browser:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Step 4: Try It Out

### Option 1: Load Sample Data
Click the **"Load Sample"** button to see a pre-computed analysis of a safe token.

### Option 2: Enter a Contract Address
1. Enter any Ethereum contract address in the input field (e.g., `0x1234567890123456789012345678901234567890`)
2. Click **"Analyze Token"**
3. View the risk score, knowledge graph, and detailed analysis

**Note**: In demo mode, the system uses seed data regardless of the actual contract address.

## What You'll See

### 1. Risk Score (0-100)
- **0-20**: Low Risk 🟢
- **20-40**: Low-Moderate Risk 🟡
- **40-70**: Moderate Risk 🟠
- **70-100**: High Risk 🔴

### 2. Knowledge Graph
Interactive visualization showing:
- Token (green circle)
- Owner (orange diamond)
- Top holders (blue circles)
- Liquidity pool (purple hexagon)
- Locker (red rectangle)

### 3. Analysis Details
- **Summary**: 4-line verdict and key findings
- **Top Risks**: 3 most critical risk factors
- **Next Checks**: Recommended verification steps
- **Risk Factors**: Detailed breakdown of heuristics
- **Metrics**: All computed metrics

## Common Commands

```bash
# Stop services
run.bat down          # Windows
./run.sh down         # Mac/Linux

# View logs
run.bat logs          # Windows
./run.sh logs         # Mac/Linux

# Run tests
run.bat test          # Windows
./run.sh test         # Mac/Linux

# Clean up everything
run.bat clean         # Windows
./run.sh clean        # Mac/Linux
```

## API Usage Examples

### Using cURL

```bash
# Get sample analysis
curl http://localhost:8000/health/sample

# Analyze a token
curl -X POST http://localhost:8000/health/demo \
  -H "Content-Type: application/json" \
  -d '{"contract": "0x1234567890123456789012345678901234567890"}'

# Check service status
curl http://localhost:8000/health/status
```

### Using Python

```python
import requests

# Analyze token
response = requests.post(
    'http://localhost:8000/health/demo',
    json={'contract': '0x1234567890123456789012345678901234567890'}
)

result = response.json()
print(f"Risk Score: {result['risk_score']}")
print(f"Summary: {result['summary']}")
```

### Using JavaScript

```javascript
// Analyze token
const response = await fetch('http://localhost:8000/health/demo', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    contract: '0x1234567890123456789012345678901234567890'
  })
})

const result = await response.json()
console.log('Risk Score:', result.risk_score)
console.log('Summary:', result.summary)
```

## Development Mode

### Run Backend Only

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on http://localhost:8000

### Run Frontend Only

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Use different ports (edit docker-compose.yml)
ports:
  - "8001:8000"  # backend
  - "3001:80"    # frontend
```

### Docker Build Fails

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

### Frontend Can't Connect to Backend

1. Check both containers are running:
   ```bash
   docker-compose ps
   ```

2. Check backend logs:
   ```bash
   docker-compose logs backend
   ```

3. Verify backend is accessible:
   ```bash
   curl http://localhost:8000/health/status
   ```

## Next Steps

1. **Read the Full README**: [README.md](README.md)
2. **Explore the API**: Visit http://localhost:8000/docs
3. **Customize Seed Data**: Edit files in `backend/seed_data/`
4. **Add New Heuristics**: See [CONTRIBUTING.md](CONTRIBUTING.md)
5. **Deploy to Production**: See deployment section in README

## Need Help?

- Check [README.md](README.md) for detailed documentation
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Open an issue on GitHub for bugs or questions
- Review API documentation at `/docs` endpoint

---

**Remember**: This is for educational purposes only. Not financial advice!
