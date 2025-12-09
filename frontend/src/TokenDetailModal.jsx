import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function TokenDetailModal({ token, onClose }) {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (token) {
      fetchAnalysis()
    }
  }, [token])

  const fetchAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      // Get contract address from token (handles both 'address' and 'contract' fields)
      const contractAddress = token.address || token.contract

      if (!contractAddress) {
        setError('No contract address available for this token')
        setLoading(false)
        return
      }

      console.log('Fetching analysis for:', contractAddress)

      const response = await axios.post(
        `${API_BASE}/health/comprehensive`,
        {
          contract: contractAddress,
          chain: 'ethereum'
        }
      )
      setAnalysis(response.data)
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (!token) return null

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-50'
    if (score >= 60) return 'text-blue-600 bg-blue-50'
    if (score >= 40) return 'text-yellow-600 bg-yellow-50'
    if (score >= 20) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }

  const getRiskLevelColor = (level) => {
    const colors = {
      'very_low': 'bg-green-100 text-green-800 border-green-300',
      'low': 'bg-blue-100 text-blue-800 border-blue-300',
      'moderate': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'high': 'bg-orange-100 text-orange-800 border-orange-300',
      'critical': 'bg-red-100 text-red-800 border-red-300'
    }
    return colors[level] || colors['moderate']
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6 flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold">{token.symbol || token.name}</h2>
            <p className="text-blue-100 text-sm mt-1">{token.name}</p>
            <p className="text-blue-200 text-xs mt-2 font-mono">
              {token.address || token.contract}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-blue-200 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 bg-gray-50">
          <div className="flex space-x-8 px-6">
            {['overview', 'categories', 'metrics', 'flags'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Analyzing token...</p>
                <p className="mt-2 text-sm text-gray-500">Fetching data from 6+ sources</p>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4">
              <p className="font-medium">Analysis Error:</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          )}

          {analysis && activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Score Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className={`rounded-lg p-4 ${getScoreColor(analysis.overall_score)} border-2`}>
                  <p className="text-sm font-medium opacity-75">Overall Score</p>
                  <p className="text-3xl font-bold mt-1">{analysis.overall_score.toFixed(1)}</p>
                  <p className="text-xs mt-1">out of 100</p>
                </div>

                <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-600">Risk Level</p>
                  <span className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold border ${getRiskLevelColor(analysis.risk_level)}`}>
                    {analysis.risk_level.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-600">Confidence</p>
                  <p className="text-3xl font-bold mt-1 text-gray-900">
                    {(analysis.confidence * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs mt-1 text-gray-500">data quality</p>
                </div>

                <div className="bg-white border-2 border-gray-200 rounded-lg p-4">
                  <p className="text-sm font-medium text-gray-600">Completeness</p>
                  <p className="text-3xl font-bold mt-1 text-gray-900">
                    {(analysis.data_completeness * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs mt-1 text-gray-500">fields populated</p>
                </div>
              </div>

              {/* Quick Stats */}
              {analysis.metrics.market && (
                <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                  <h3 className="font-semibold text-gray-900 mb-3">Market Data</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-gray-600">Price</p>
                      <p className="text-lg font-bold text-gray-900">
                        ${analysis.metrics.market.price_usd?.toFixed(4) || 'N/A'}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Market Cap</p>
                      <p className="text-lg font-bold text-gray-900">
                        ${(analysis.metrics.market.market_cap / 1e6).toFixed(2)}M
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">Volume 24h</p>
                      <p className="text-lg font-bold text-gray-900">
                        ${(analysis.metrics.market.volume_24h / 1e6).toFixed(2)}M
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600">24h Change</p>
                      <p className={`text-lg font-bold ${analysis.metrics.market.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {analysis.metrics.market.price_change_24h?.toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {analysis.recommendations && analysis.recommendations.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-semibold text-blue-900 mb-3">💡 Recommendations</h3>
                  <ul className="space-y-2">
                    {analysis.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-blue-900">
                        <span className="font-semibold">{idx + 1}.</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {analysis && activeTab === 'categories' && (
            <div className="space-y-4">
              {analysis.category_scores.map((cat, idx) => (
                <div key={idx} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="font-semibold text-lg capitalize">{cat.category}</span>
                      <span className="text-sm text-gray-500">
                        (weight: {(cat.weight * 100).toFixed(0)}%)
                      </span>
                    </div>
                    <span className={`text-2xl font-bold ${getScoreColor(cat.score).split(' ')[0]}`}>
                      {cat.score.toFixed(1)}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                    <div
                      className={`h-3 rounded-full ${cat.score >= 70 ? 'bg-green-500' : cat.score >= 50 ? 'bg-blue-500' : cat.score >= 30 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>

                  {/* Issues */}
                  {cat.issues && cat.issues.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs font-medium text-red-600 mb-2">⚠️ Issues:</p>
                      <ul className="space-y-1">
                        {cat.issues.map((issue, i) => (
                          <li key={i} className="text-sm text-red-700 pl-4">• {issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Strengths */}
                  {cat.strengths && cat.strengths.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs font-medium text-green-600 mb-2">✓ Strengths:</p>
                      <ul className="space-y-1">
                        {cat.strengths.map((strength, i) => (
                          <li key={i} className="text-sm text-green-700 pl-4">• {strength}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {analysis && activeTab === 'metrics' && (
            <div className="space-y-6">
              {Object.entries(analysis.metrics).map(([category, data]) => {
                if (!data || Object.keys(data).length === 0) return null
                return (
                  <div key={category} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-lg capitalize mb-3 text-gray-900">
                      {category} Metrics
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {Object.entries(data).map(([key, value]) => {
                        if (value === null || value === undefined) return null
                        return (
                          <div key={key} className="bg-gray-50 p-3 rounded border border-gray-200">
                            <p className="text-xs text-gray-600 capitalize">
                              {key.replace(/_/g, ' ')}
                            </p>
                            <p className="text-sm font-medium text-gray-900 mt-1 break-all">
                              {typeof value === 'boolean'
                                ? (value ? '✓ Yes' : '✗ No')
                                : typeof value === 'number'
                                ? value.toLocaleString()
                                : value}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {analysis && activeTab === 'flags' && (
            <div className="space-y-6">
              {/* Red Flags */}
              {analysis.red_flags && analysis.red_flags.length > 0 && (
                <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4">
                  <h3 className="font-bold text-red-900 text-lg mb-3">🚨 Critical Issues</h3>
                  <ul className="space-y-2">
                    {analysis.red_flags.map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-red-800">
                        <span className="text-red-600 font-bold">•</span>
                        <span className="text-sm">{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Yellow Flags */}
              {analysis.yellow_flags && analysis.yellow_flags.length > 0 && (
                <div className="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
                  <h3 className="font-bold text-yellow-900 text-lg mb-3">⚠️ Warnings</h3>
                  <ul className="space-y-2">
                    {analysis.yellow_flags.map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-yellow-800">
                        <span className="text-yellow-600 font-bold">•</span>
                        <span className="text-sm">{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Green Flags */}
              {analysis.green_flags && analysis.green_flags.length > 0 && (
                <div className="bg-green-50 border-2 border-green-200 rounded-lg p-4">
                  <h3 className="font-bold text-green-900 text-lg mb-3">✅ Strengths</h3>
                  <ul className="space-y-2">
                    {analysis.green_flags.slice(0, 10).map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-green-800">
                        <span className="text-green-600 font-bold">•</span>
                        <span className="text-sm">{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {!analysis.red_flags?.length && !analysis.yellow_flags?.length && !analysis.green_flags?.length && (
                <div className="text-center py-8 text-gray-500">
                  <p>No flags available for this token.</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 p-4 flex justify-between items-center">
          <div className="text-xs text-gray-500">
            Analysis completed • {analysis?.category_scores?.length || 0} of 7 categories analyzed
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default TokenDetailModal
