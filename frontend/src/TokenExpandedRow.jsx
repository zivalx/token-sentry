function TokenExpandedRow({ token }) {
  const formatNumber = (num) => {
    if (!num) return 'N/A'
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`
    return `$${num.toFixed(2)}`
  }

  const getRiskColor = (score) => {
    if (!score && score !== 0) return '#6c6c6c'
    if (score < 30) return '#16c784'  // Green - Low risk
    if (score < 60) return '#f6b87a'  // Orange - Moderate
    return '#ea3943'                   // Red - High risk
  }

  const getRiskLabel = (score) => {
    if (!score && score !== 0) return 'Unknown Risk'
    if (score < 30) return 'Low Risk'
    if (score < 60) return 'Moderate Risk'
    return 'High Risk'
  }

  const getRiskDescription = (score) => {
    if (!score && score !== 0) return 'Risk data unavailable'
    if (score < 30) return 'Positive indicators detected'
    if (score < 60) return 'Monitor recommended'
    return 'Exercise caution'
  }

  const riskColor = getRiskColor(token.riskScore)

  return (
    <tr className="expanded-row-wrapper">
      <td colSpan="9" className="p-0">
        <div className="expanded-row-container">
          {/* Main Content - Two Column Layout */}
          <div className="expanded-row-content">

            {/* LEFT COLUMN - Risk Analysis (Hero) */}
            <div className="risk-hero-section">
              {/* Large Risk Score */}
              <div className="risk-score-display">
                <div className="risk-score-label">RISK SCORE</div>
                <div className="risk-score-value" style={{ color: riskColor }}>
                  {token.riskScore || token.riskScore === 0 ? token.riskScore : '--'}
                  <span className="risk-score-max">/100</span>
                </div>
                <div className="risk-score-bar">
                  <div
                    className="risk-score-fill"
                    style={{
                      width: `${token.riskScore || 0}%`,
                      background: riskColor
                    }}
                  />
                </div>
                <div className="risk-label" style={{ color: riskColor }}>
                  {getRiskLabel(token.riskScore)}
                </div>
                <div className="risk-description">
                  {getRiskDescription(token.riskScore)}
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN - Market Details */}
            <div className="market-details-section">
              <div className="details-header">Market Details</div>

              {/* Compact Stats Grid */}
              <div className="stats-grid">
                <div className="stat-item">
                  <div className="stat-label">Price</div>
                  <div className="stat-value">
                    {token.priceUsd ? `$${parseFloat(token.priceUsd).toFixed(6)}` : 'N/A'}
                  </div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">24h Change</div>
                  <div className={`stat-value ${token.priceChange24h >= 0 ? 'positive' : 'negative'}`}>
                    {token.priceChange24h >= 0 ? '+' : ''}{token.priceChange24h}%
                  </div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Volume</div>
                  <div className="stat-value">{formatNumber(token.volume24h)}</div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Liquidity</div>
                  <div className="stat-value">{formatNumber(token.liquidity)}</div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Supply</div>
                  <div className="stat-value">
                    {token.circulatingSupply ? `${(token.circulatingSupply / 1e6).toFixed(0)}M` :
                     token.totalSupply ? `${(token.totalSupply / 1e6).toFixed(0)}M` : 'N/A'}
                  </div>
                </div>

                <div className="stat-item">
                  <div className="stat-label">Markets</div>
                  <div className="stat-value">{token.pairCount ?? token.exchangeCount ?? 'N/A'}</div>
                </div>
              </div>

              {/* Token Info */}
              {token.address && token.address !== 'N/A' && (
                <div className="token-info">
                  <div className="info-label">Contract Address</div>
                  <div className="contract-address" title={token.address}>
                    {token.address.slice(0, 6)}...{token.address.slice(-4)}
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      </td>
    </tr>
  )
}

export default TokenExpandedRow
