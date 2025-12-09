import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function TokenExpandedRow({ token, onClose }) {
  const [loading, setLoading] = useState(true)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchAnalysis()
  }, [])

  const fetchAnalysis = async () => {
    try {
      const response = await axios.post(
        `${API_BASE}/health/comprehensive`,
        {
          contract: token.address || token.symbol,
          chain: 'ethereum'
        }
      )
      setAnalysis(response.data)
      setError(null)
    } catch (err) {
      console.error('Analysis error:', err)
      // Don't show error, just show limited data
      setError('Limited data available')
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score) => {
    if (!score) return 'bg-gray-100 text-gray-600'
    if (score >= 80) return 'bg-green-100 text-green-700'
    if (score >= 60) return 'bg-blue-100 text-blue-700'
    if (score >= 40) return 'bg-yellow-100 text-yellow-700'
    if (score >= 20) return 'bg-orange-100 text-orange-700'
    return 'bg-red-100 text-red-700'
  }

  const getScoreBadgeColor = (score) => {
    if (!score) return 'border-gray-300 bg-gray-50'
    if (score >= 80) return 'border-green-400 bg-green-50'
    if (score >= 60) return 'border-blue-400 bg-blue-50'
    if (score >= 40) return 'border-yellow-400 bg-yellow-50'
    if (score >= 20) return 'border-orange-400 bg-orange-50'
    return 'border-red-400 bg-red-50'
  }

  const getRiskBadge = (level) => {
    const badges = {
      'very_low': { color: 'bg-green-500', text: 'Very Low Risk', icon: '🟢' },
      'low': { color: 'bg-blue-500', text: 'Low Risk', icon: '🔵' },
      'moderate': { color: 'bg-yellow-500', text: 'Moderate Risk', icon: '🟡' },
      'high': { color: 'bg-orange-500', text: 'High Risk', icon: '🟠' },
      'critical': { color: 'bg-red-500', text: 'Critical Risk', icon: '🔴' }
    }
    return badges[level] || badges.moderate
  }

  if (loading) {
    return (
      <tr className="border-l-4 border-blue-500">
        <td colSpan="9" className="p-0">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-8">
            <div className="flex items-center justify-center space-x-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <div className="text-gray-700">
                <p className="font-semibold">Analyzing {token.symbol}...</p>
                <p className="text-sm text-gray-600">Fetching data from multiple sources</p>
              </div>
            </div>
          </div>
        </td>
      </tr>
    )
  }

  if (!analysis && error) {
    return (
      <tr className="border-l-4 border-yellow-500">
        <td colSpan="9" className="p-0">
          <div className="bg-yellow-50 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <p className="font-semibold text-yellow-900">Limited Analysis Available</p>
                  <p className="text-sm text-yellow-700">Showing market data only - on-chain data unavailable</p>
                </div>
              </div>
              <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-xl font-bold">
                ×
              </button>
            </div>
            {/* Show basic token info from trending data */}
            <div className="mt-4 grid grid-cols-4 gap-4">
              <div className="bg-white rounded-lg p-4 border border-yellow-200">
                <p className="text-xs text-gray-600">Price</p>
                <p className="text-lg font-bold text-gray-900">${parseFloat(token.priceUsd).toFixed(6)}</p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-yellow-200">
                <p className="text-xs text-gray-600">24h Change</p>
                <p className={`text-lg font-bold ${token.priceChange24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {token.priceChange24h >= 0 ? '+' : ''}{token.priceChange24h}%
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-yellow-200">
                <p className="text-xs text-gray-600">Volume 24h</p>
                <p className="text-lg font-bold text-gray-900">
                  ${(token.volume24h / 1e6).toFixed(2)}M
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-yellow-200">
                <p className="text-xs text-gray-600">Liquidity</p>
                <p className="text-lg font-bold text-gray-900">
                  ${(token.liquidity / 1e6).toFixed(2)}M
                </p>
              </div>
            </div>
          </div>
        </td>
      </tr>
    )
  }

  const riskBadge = getRiskBadge(analysis?.risk_level)

  return (
    <tr className="border-l-4 border-indigo-500">
      <td colSpan="9" className="p-0">
        <div className="bg-gradient-to-br from-gray-50 via-white to-gray-50">
          {/* Header Section */}
          <div className="bg-gradient-to-r from-indigo-600 to-blue-600 text-white p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-4">
                <div className="bg-white/20 rounded-full w-16 h-16 flex items-center justify-center">
                  <span className="text-2xl font-bold">{token.symbol}</span>
                </div>
                <div>
                  <h3 className="text-2xl font-bold">{token.name}</h3>
                  <p className="text-blue-100 text-sm">Comprehensive Health Analysis</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="text-white/80 hover:text-white text-3xl font-bold leading-none"
              >
                ×
              </button>
            </div>
          </div>

          {/* Main Content */}
          <div className="p-6 space-y-6">
            {/* Score Dashboard */}
            <div className="grid grid-cols-4 gap-4">
              {/* Overall Score - Large */}
              <div className={`col-span-1 rounded-xl p-6 border-2 ${getScoreBadgeColor(analysis.overall_score)}`}>
                <div className="text-center">
                  <p className="text-sm font-medium text-gray-600 mb-2">Health Score</p>
                  <div className={`text-5xl font-bold ${getScoreColor(analysis.overall_score).split(' ')[1]}`}>
                    {analysis.overall_score?.toFixed(0) || 'N/A'}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">out of 100</p>

                  {/* Mini gauge */}
                  <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        analysis.overall_score >= 80 ? 'bg-green-500' :
                        analysis.overall_score >= 60 ? 'bg-blue-500' :
                        analysis.overall_score >= 40 ? 'bg-yellow-500' :
                        analysis.overall_score >= 20 ? 'bg-orange-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${analysis.overall_score}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Risk Level */}
              <div className="col-span-1 bg-white rounded-xl p-6 border-2 border-gray-200 shadow-sm">
                <p className="text-sm font-medium text-gray-600 mb-3">Risk Level</p>
                <div className="flex flex-col items-center">
                  <span className="text-4xl mb-2">{riskBadge.icon}</span>
                  <span className={`${riskBadge.color} text-white px-4 py-2 rounded-full text-sm font-semibold`}>
                    {riskBadge.text}
                  </span>
                </div>
              </div>

              {/* Confidence */}
              <div className="col-span-1 bg-white rounded-xl p-6 border-2 border-gray-200 shadow-sm">
                <p className="text-sm font-medium text-gray-600 mb-2">Analysis Confidence</p>
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-900">
                    {(analysis.confidence * 100).toFixed(0)}%
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {analysis.category_scores?.length || 0} of 7 categories
                  </p>
                  <div className="mt-3 flex justify-center space-x-1">
                    {[...Array(7)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-2 h-2 rounded-full ${
                          i < (analysis.category_scores?.length || 0) ? 'bg-blue-500' : 'bg-gray-300'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Data Completeness */}
              <div className="col-span-1 bg-white rounded-xl p-6 border-2 border-gray-200 shadow-sm">
                <p className="text-sm font-medium text-gray-600 mb-2">Data Completeness</p>
                <div className="text-center">
                  <div className="text-4xl font-bold text-gray-900">
                    {(analysis.data_completeness * 100).toFixed(0)}%
                  </div>
                  <p className="text-xs text-gray-500 mt-2">fields populated</p>
                  <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{ width: `${analysis.data_completeness * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Category Scores - Compact Grid */}
            {analysis.category_scores && analysis.category_scores.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <span className="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm mr-2">
                    Category Breakdown
                  </span>
                </h4>
                <div className="grid grid-cols-7 gap-3">
                  {analysis.category_scores.map((cat, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-4 border-2 border-gray-200 hover:border-indigo-300 transition-all">
                      <div className="text-center">
                        <p className="text-xs font-medium text-gray-600 uppercase mb-2">
                          {cat.category}
                        </p>
                        <div className={`text-3xl font-bold ${getScoreColor(cat.score).split(' ')[1]} mb-2`}>
                          {cat.score.toFixed(0)}
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5 mb-2">
                          <div
                            className={`h-1.5 rounded-full ${
                              cat.score >= 70 ? 'bg-green-500' :
                              cat.score >= 50 ? 'bg-blue-500' :
                              cat.score >= 30 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${cat.score}%` }}
                          />
                        </div>
                        <p className="text-xs text-gray-500">{(cat.weight * 100).toFixed(0)}% weight</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Flags Section - Compact */}
            <div className="grid grid-cols-3 gap-4">
              {/* Red Flags */}
              {analysis.red_flags && analysis.red_flags.length > 0 && (
                <div className="bg-red-50 rounded-lg p-4 border-l-4 border-red-500">
                  <h5 className="font-semibold text-red-900 text-sm mb-2 flex items-center">
                    <span className="mr-2">🚨</span> Critical Issues
                  </h5>
                  <ul className="space-y-1">
                    {analysis.red_flags.slice(0, 3).map((flag, idx) => (
                      <li key={idx} className="text-xs text-red-800 flex items-start">
                        <span className="mr-1">•</span>
                        <span>{flag.replace(/\[.*?\]\s*/, '')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Yellow Flags */}
              {analysis.yellow_flags && analysis.yellow_flags.length > 0 && (
                <div className="bg-yellow-50 rounded-lg p-4 border-l-4 border-yellow-500">
                  <h5 className="font-semibold text-yellow-900 text-sm mb-2 flex items-center">
                    <span className="mr-2">⚠️</span> Warnings
                  </h5>
                  <ul className="space-y-1">
                    {analysis.yellow_flags.slice(0, 3).map((flag, idx) => (
                      <li key={idx} className="text-xs text-yellow-800 flex items-start">
                        <span className="mr-1">•</span>
                        <span>{flag.replace(/\[.*?\]\s*/, '')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Green Flags */}
              {analysis.green_flags && analysis.green_flags.length > 0 && (
                <div className="bg-green-50 rounded-lg p-4 border-l-4 border-green-500">
                  <h5 className="font-semibold text-green-900 text-sm mb-2 flex items-center">
                    <span className="mr-2">✅</span> Strengths
                  </h5>
                  <ul className="space-y-1">
                    {analysis.green_flags.slice(0, 3).map((flag, idx) => (
                      <li key={idx} className="text-xs text-green-800 flex items-start">
                        <span className="mr-1">•</span>
                        <span>{flag.replace(/\[.*?\]\s*/, '')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Recommendations */}
            {analysis.recommendations && analysis.recommendations.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 border-l-4 border-blue-500">
                <h5 className="font-semibold text-blue-900 text-sm mb-3 flex items-center">
                  <span className="mr-2">💡</span> Recommendations
                </h5>
                <div className="grid grid-cols-2 gap-2">
                  {analysis.recommendations.slice(0, 4).map((rec, idx) => (
                    <div key={idx} className="flex items-start text-xs text-blue-900">
                      <span className="font-semibold mr-2">{idx + 1}.</span>
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </td>
    </tr>
  )
}

export default TokenExpandedRow
