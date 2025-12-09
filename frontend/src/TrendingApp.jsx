import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function TrendingApp() {
  const [trending, setTrending] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('trending')
  const [contract, setContract] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)

  useEffect(() => {
    loadTokens()
  }, [filter])

  const loadTokens = async () => {
    setLoading(true)
    setError(null)

    // Map filter to API endpoint
    const endpointMap = {
      'trending': 'trending',
      'newest': 'newest',
      'gainers': 'gainers'
    }

    const endpoint = endpointMap[filter] || 'trending'
    const dataKey = filter // Response keys match filter names

    try {
      console.log('Fetching from:', `${API_BASE}/tokens/${endpoint}?limit=20`)
      const response = await axios.get(`${API_BASE}/tokens/${endpoint}?limit=20`)
      console.log(`${filter} response:`, response.data)

      const data = response.data?.[dataKey]

      if (data && Array.isArray(data) && data.length > 0) {
        console.log(`Setting ${filter} data with`, data.length, 'tokens')
        setTrending(data)
      } else {
        console.warn(`${filter} data is empty array`)
        setError(`No ${filter} tokens available right now. The API may be rate-limited or returning no data. Try refreshing in a few minutes.`)
      }
    } catch (err) {
      setError(`Failed to load ${filter} tokens: ${err.message}. Make sure backend is running on port 8001.`)
      console.error(`${filter} error:`, err)
    } finally {
      setLoading(false)
    }
  }

  const loadTrending = () => {
    setFilter('trending')
  }

  const handleRowClick = (token) => {
    // Set contract and scroll to search
    setContract(token.address)
    document.querySelector('.search-section').scrollIntoView({ behavior: 'smooth' })
  }

  const handleAnalyze = async () => {
    if (!contract.trim()) {
      setError('Please enter a contract address or ticker')
      return
    }
    setSearchLoading(true)
    setError(null)
    try {
      // Simulate analysis
      await new Promise(resolve => setTimeout(resolve, 2000))
      alert(`Analysis for ${contract} - Feature coming soon!`)
    } catch (err) {
      setError('Analysis failed')
    } finally {
      setSearchLoading(false)
    }
  }

  const formatNumber = (num) => {
    if (!num || num === 0) return 'N/A'
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`
    return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const formatPrice = (price) => {
    if (!price) return 'N/A'
    const num = parseFloat(price)
    if (num >= 1) {
      return `$${num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })}`
    } else if (num >= 0.0001) {
      return `$${num.toFixed(6)}`
    } else {
      return `$${num.toExponential(2)}`
    }
  }

  const formatSupply = (num) => {
    if (!num) return 'N/A'
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`
    return num.toLocaleString()
  }

  const getRiskBadgeClass = (score) => {
    if (score >= 60) return 'high'
    if (score >= 30) return 'moderate'
    return 'low'
  }

  const getRiskLabel = (score) => {
    if (score >= 60) return 'High'
    if (score >= 30) return 'Moderate'
    return 'Low'
  }

  return (
    <>
      <div className="header">
        <div className="header-content">
          <div>
            <h1>TokenHealth</h1>
            <p>Real-time Token Due Diligence</p>
          </div>
        </div>
      </div>

      <div className="container">
        <div className="disclaimer">
          <strong>DISCLAIMER:</strong> Research/educational purposes only. Not financial advice.
          Always verify on-chain data independently.
        </div>

        {/* Search Section */}
        <div className="search-section">
          <h2>Analyze Token</h2>
          <form onSubmit={(e) => { e.preventDefault(); handleAnalyze(); }}>
            <div className="input-group">
              <input
                type="text"
                placeholder="Enter contract address or ticker (e.g., PEPE, 0x...)"
                value={contract}
                onChange={(e) => setContract(e.target.value)}
                disabled={searchLoading}
              />
              <button type="submit" className="btn btn-primary" disabled={searchLoading}>
                {searchLoading ? (
                  <>
                    <span className="btn-spinner"></span>
                    Analyzing...
                  </>
                ) : 'Analyze'}
              </button>
            </div>
          </form>
        </div>

        {/* Trending Section */}
        <div className="trending-section">
          <div className="trending-header">
            <h2>
              {filter === 'newest' && '🆕 Newest Tokens'}
              {filter === 'gainers' && '📈 Top Gainers'}
              {filter === 'trending' && '🔥 Trending Tokens'}
            </h2>
            <div className="trending-filters">
              <button
                className={`filter-btn ${filter === 'trending' ? 'active' : ''}`}
                onClick={() => setFilter('trending')}
              >
                Trending
              </button>
              <button
                className={`filter-btn ${filter === 'newest' ? 'active' : ''}`}
                onClick={() => setFilter('newest')}
              >
                Newest
              </button>
              <button
                className={`filter-btn ${filter === 'gainers' ? 'active' : ''}`}
                onClick={() => setFilter('gainers')}
              >
                Top Gainers
              </button>
            </div>
          </div>

          {error && <div className="error">{error}</div>}

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading {filter} tokens...</p>
            </div>
          ) : trending.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No {filter.charAt(0).toUpperCase() + filter.slice(1)} Tokens Available</h3>
              <p>Unable to fetch {filter} data right now. This could be due to:</p>
              <ul>
                <li>API rate limiting</li>
                <li>Network connectivity issues</li>
                <li>Backend not running (check port 8001)</li>
              </ul>
              <button className="btn btn-secondary" onClick={loadTokens}>
                Retry
              </button>
            </div>
          ) : (
            <div className="trending-table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Token</th>
                      <th className="right">Price</th>
                      <th className="right">24h %</th>
                      <th className="right">Volume (24h)</th>
                      <th className="right">Liquidity</th>
                      <th className="right">Supply</th>
                      <th>Exchanges</th>
                      <th className="right">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trending.map((token, index) => (
                      <tr key={token.address} onClick={() => handleRowClick(token)}>
                        <td>
                          <span className="token-rank">{index + 1}</span>
                        </td>
                        <td>
                          <div className="token-info">
                            <div>
                              <div className="token-symbol">{token.symbol}</div>
                              <div className="token-name">{token.name}</div>
                            </div>
                          </div>
                        </td>
                        <td className="right">
                          <span className="price">{formatPrice(token.priceUsd)}</span>
                        </td>
                        <td className="right">
                          <span className={token.priceChange24h >= 0 ? 'change-positive' : 'change-negative'}>
                            {token.priceChange24h >= 0 ? '+' : ''}{token.priceChange24h}%
                          </span>
                        </td>
                        <td className="right">
                          <span className="volume">{formatNumber(token.volume24h)}</span>
                        </td>
                        <td className="right">
                          <span className="liquidity">{formatNumber(token.liquidity)}</span>
                        </td>
                        <td className="right">
                          <span className="supply">{formatSupply(token.circulatingSupply || token.totalSupply)}</span>
                        </td>
                        <td>
                          <div className="exchanges">
                            {token.exchanges.slice(0, 3).map((ex, i) => (
                              <span key={i} className="exchange-badge">
                                {ex.replace('_', ' ')}
                              </span>
                            ))}
                            {token.exchanges.length > 3 && (
                              <span className="exchange-badge">+{token.exchanges.length - 3}</span>
                            )}
                          </div>
                        </td>
                        <td className="right">
                          <span className={`risk-badge ${getRiskBadgeClass(token.riskScore)}`}>
                            {getRiskLabel(token.riskScore)}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default TrendingApp
