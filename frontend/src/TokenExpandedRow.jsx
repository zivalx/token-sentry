function TokenExpandedRow({ token }) {
  const formatNumber = (num) => {
    if (!num) return 'N/A'
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`
    if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`
    return `$${num.toFixed(2)}`
  }

  const getRiskColor = (score) => {
    if (!score && score !== 0) return 'text-gray-400'
    if (score < 30) return 'text-green-400'  // Low risk
    if (score < 60) return 'text-yellow-400' // Moderate risk
    return 'text-red-400'                     // High risk
  }

  const getRiskBg = (score) => {
    if (!score && score !== 0) return 'bg-gray-900'
    if (score < 30) return 'bg-green-900/20'
    if (score < 60) return 'bg-yellow-900/20'
    return 'bg-red-900/20'
  }

  const getRiskLabel = (score) => {
    if (!score && score !== 0) return 'Unknown'
    if (score < 30) return 'Low Risk'
    if (score < 60) return 'Moderate Risk'
    return 'High Risk'
  }

  const getRiskDescription = (score) => {
    if (!score && score !== 0) return 'Risk data not available'
    if (score < 30) return 'This token shows positive indicators and low risk factors'
    if (score < 60) return 'This token has some risk factors that should be monitored'
    return 'This token shows significant risk factors - exercise caution'
  }

  return (
    <tr className="expanded-row">
      <td colSpan="9" className="p-0">
        <div style={{
          background: 'var(--bg-tertiary)',
          borderTop: '1px solid var(--border-color)',
          borderBottom: '1px solid var(--border-color)'
        }}>
          <div className="p-6">
            {/* Market Overview */}
            <div className="grid grid-cols-6 gap-3 mb-6">
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">Price</div>
                <div className="text-lg font-semibold text-white">
                  {token.priceUsd ? `$${parseFloat(token.priceUsd).toFixed(6)}` : 'N/A'}
                </div>
              </div>

              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">24h Change</div>
                <div className={`text-lg font-semibold ${token.priceChange24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {token.priceChange24h >= 0 ? '+' : ''}{token.priceChange24h}%
                </div>
              </div>

              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">Volume 24h</div>
                <div className="text-lg font-semibold text-white">
                  {formatNumber(token.volume24h)}
                </div>
              </div>

              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">Liquidity</div>
                <div className="text-lg font-semibold text-white">
                  {formatNumber(token.liquidity)}
                </div>
              </div>

              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">Supply</div>
                <div className="text-lg font-semibold text-white">
                  {token.circulatingSupply ? `${(token.circulatingSupply / 1e6).toFixed(0)}M` :
                   token.totalSupply ? `${(token.totalSupply / 1e6).toFixed(0)}M` : 'N/A'}
                </div>
              </div>

              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-1">Exchanges</div>
                <div className="text-lg font-semibold text-white">
                  {token.exchanges?.length || 0}
                </div>
              </div>
            </div>

            {/* Risk Analysis - Using existing riskScore from token */}
            <div className="grid grid-cols-3 gap-4">
              {/* Risk Score */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-6">
                <div className="text-xs text-gray-500 mb-3 uppercase tracking-wider">Risk Score</div>
                <div className="flex items-center justify-center mb-3">
                  <div className={`text-5xl font-bold ${getRiskColor(token.riskScore)}`}>
                    {token.riskScore || token.riskScore === 0 ? token.riskScore : 'N/A'}
                  </div>
                  <div className="text-xl text-gray-600 ml-2">/100</div>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden mb-2">
                  <div
                    className={`h-2 rounded-full transition-all ${
                      token.riskScore < 30 ? 'bg-green-500' :
                      token.riskScore < 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${token.riskScore}%` }}
                  />
                </div>
                <div className="text-xs text-gray-500 text-center">{getRiskLabel(token.riskScore)}</div>
              </div>

              {/* Risk Level Badge */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-6">
                <div className="text-xs text-gray-500 mb-3 uppercase tracking-wider">Risk Assessment</div>
                <div className={`${getRiskBg(token.riskScore)} ${getRiskColor(token.riskScore)} px-4 py-4 rounded-lg text-center font-semibold text-xl mb-3`}>
                  {getRiskLabel(token.riskScore)}
                </div>
                <div className="text-xs text-gray-400 text-center">
                  {getRiskDescription(token.riskScore)}
                </div>
              </div>

              {/* Additional Info */}
              <div style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)' }} className="rounded-lg p-6">
                <div className="text-xs text-gray-500 mb-3 uppercase tracking-wider">Token Details</div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Symbol:</span>
                    <span className="text-white font-semibold">{token.symbol}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Name:</span>
                    <span className="text-white font-semibold truncate ml-2">{token.name}</span>
                  </div>
                  {token.address && token.address !== 'N/A' && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Address:</span>
                      <span className="text-blue-400 font-mono text-xs truncate ml-2" title={token.address}>
                        {token.address.slice(0, 6)}...{token.address.slice(-4)}
                      </span>
                    </div>
                  )}
                  {token.exchanges && token.exchanges.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs text-gray-500 mb-2">Listed on:</div>
                      <div className="flex flex-wrap gap-1">
                        {token.exchanges.slice(0, 3).map((ex, i) => (
                          <span key={i} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded">
                            {ex.replace('_', ' ')}
                          </span>
                        ))}
                        {token.exchanges.length > 3 && (
                          <span className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded">
                            +{token.exchanges.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </td>
    </tr>
  )
}

export default TokenExpandedRow
