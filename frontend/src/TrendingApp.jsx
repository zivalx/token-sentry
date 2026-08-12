import React, { useState, useEffect } from 'react'
import axios from 'axios'
import TokenExpandedRow from './TokenExpandedRow'
import TokenDetailModal from './TokenDetailModal'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function TrendingApp() {
  const [trending, setTrending] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [filter, setFilter] = useState('trending')
  const [contract, setContract] = useState('')
  const [searchLoading, setSearchLoading] = useState(false)
  const [expandedToken, setExpandedToken] = useState(null)
  const [selectedToken, setSelectedToken] = useState(null)
  const [cmcAvailable, setCmcAvailable] = useState(null)

  useEffect(() => {
    loadTokens()
  }, [filter])

  useEffect(() => {
    // Newest/gainers need a CoinMarketCap key; trending has a keyless fallback.
    axios.get(`${API_BASE}/health/status`)
      .then(res => setCmcAvailable(Boolean(res.data?.data_sources?.coinmarketcap)))
      .catch(() => setCmcAvailable(null))
  }, [])

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
      setError(`Failed to load ${filter} tokens: ${err.message}. Make sure backend is running on port 8000.`)
      console.error(`${filter} error:`, err)
    } finally {
      setLoading(false)
    }
  }

  const loadTrending = () => {
    setFilter('trending')
  }

  const isTokenAnalyzable = (token) => {
    return token?.address && token.address !== 'N/A'
  }

  const handleRowClick = (token) => {
    // Only allow click if token is analyzable
    if (!isTokenAnalyzable(token)) return

    // Toggle expansion - if same token clicked, collapse it
    if (expandedToken?.address === token.address) {
      setExpandedToken(null)
    } else {
      setExpandedToken(token)
    }
  }

  const handleAnalyze = async () => {
    if (!contract.trim()) {
      setError('Please enter a contract address or ticker')
      return
    }

    const searchTerm = contract.trim().toUpperCase()

    // First, search for token in existing list
    const foundToken = trending.find(token =>
      token.symbol?.toUpperCase() === searchTerm ||
      token.name?.toUpperCase().includes(searchTerm) ||
      token.address?.toLowerCase() === contract.trim().toLowerCase()
    )

    if (foundToken) {
      // Token found in list - expand it!
      setExpandedToken(foundToken)
      setContract('')

      // Scroll to the token row
      setTimeout(() => {
        const row = document.querySelector(`tr[data-address="${foundToken.address}"]`)
        if (row) {
          row.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }, 100)
      return
    }

    // Token not in current list - analyze it via API
    setSearchLoading(true)
    setError(null)

    try {
      console.log('Analyzing token via API:', contract.trim())
      const response = await axios.post(`${API_BASE}/health/comprehensive`, {
        contract: contract.trim(),
        chain: 'ethereum'
      })

      console.log('Analysis response:', response.data)

      // Map the comprehensive-health response (metrics grouped by category).
      // overall_score is a HEALTH score (high = good); the table shows RISK
      // (high = bad), so invert it.
      const market = response.data.metrics?.market || {}
      const liquidity = response.data.metrics?.liquidity || {}
      const onchain = response.data.metrics?.onchain || {}
      const analyzedToken = {
        symbol: market.symbol || contract.trim(),
        name: market.name || 'Unknown Token',
        address: contract.trim(),
        priceUsd: market.price_usd || 0,
        priceChange24h: market.price_change_24h ?? 0,
        volume24h: market.volume_24h || 0,
        liquidity: liquidity.total_liquidity_usd ?? null,
        circulatingSupply: onchain.circulating_supply || 0,
        totalSupply: onchain.total_supply || 0,
        pairCount: market.exchanges_listed ?? null,
        riskScore: response.data.overall_score != null
          ? Math.round(100 - response.data.overall_score)
          : null
      }

      // Add to trending list temporarily at the top
      setTrending([analyzedToken, ...trending])

      // Expand it
      setExpandedToken(analyzedToken)
      setContract('')

      // Scroll to top
      window.scrollTo({ top: 0, behavior: 'smooth' })

    } catch (err) {
      console.error('Analysis error:', err)
      setError(`Could not analyze "${contract}". Please check the contract address or symbol and try again. Error: ${err.response?.data?.detail || err.message}`)
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
            <h1>Token Sentry</h1>
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
            filter !== 'trending' && cmcAvailable === false ? (
              <div className="empty-state">
                <div className="empty-icon">🔑</div>
                <h3>Requires a CoinMarketCap API key</h3>
                <p>
                  The {filter} list comes from CoinMarketCap, which needs a (free) API key —
                  the trending tab works without one.
                </p>
                <p>
                  Get a key at coinmarketcap.com/api, set <code>CMC_API_KEY</code> in{' '}
                  <code>backend/.env</code> (see <code>backend/.env.example</code>), and restart the backend.
                </p>
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📊</div>
                <h3>No {filter.charAt(0).toUpperCase() + filter.slice(1)} Tokens Available</h3>
                <p>Unable to fetch {filter} data right now. This could be due to:</p>
                <ul>
                  <li>API rate limiting</li>
                  <li>Network connectivity issues</li>
                  <li>Backend not running (check port 8000)</li>
                </ul>
                <button className="btn btn-secondary" onClick={loadTokens}>
                  Retry
                </button>
              </div>
            )
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
                      <th className="right">Markets</th>
                      <th className="right">Risk</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trending.map((token, index) => {
                      const analyzable = isTokenAnalyzable(token)
                      const isExpanded = expandedToken?.address === token.address
                      return (
                      <React.Fragment key={token.address}>
                      <tr
                        data-address={token.address}
                        onClick={() => handleRowClick(token)}
                        className={analyzable ? 'cursor-pointer hover:bg-gray-50' : 'cursor-not-allowed opacity-60'}
                        title={analyzable ? 'Click to analyze' : 'No contract address available'}
                      >
                        <td>
                          <span className="token-rank">{index + 1}</span>
                          {!analyzable && <span className="ml-2 text-xs text-gray-400">⚠️</span>}
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
                        <td className="right">
                          <span className="pair-count">
                            {token.pairCount ?? token.exchangeCount ?? '—'}
                          </span>
                        </td>
                        <td className="right">
                          <span className={`risk-badge ${getRiskBadgeClass(token.riskScore)}`}>
                            {getRiskLabel(token.riskScore)}
                          </span>
                        </td>
                      </tr>
                      {isExpanded && (
                        <TokenExpandedRow token={token} onFullReport={setSelectedToken} />
                      )}
                      </React.Fragment>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Token Detail Modal */}
      {selectedToken && (
        <TokenDetailModal
          token={selectedToken}
          onClose={() => setSelectedToken(null)}
        />
      )}
    </>
  )
}

export default TrendingApp
