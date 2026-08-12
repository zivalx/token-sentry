import { useState, useEffect } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function TokenDetailModal({ token, onClose }) {
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [history, setHistory] = useState([])

  useEffect(() => {
    if (token) {
      fetchAnalysis()
    }
  }, [token])

  const fetchAnalysis = async () => {
    setLoading(true)
    setError(null)

    try {
      const contractAddress = token.address || token.contract
      if (!contractAddress) {
        setError('No contract address available for this token')
        setLoading(false)
        return
      }

      const response = await axios.post(`${API_BASE}/health/comprehensive`, {
        contract: contractAddress,
        chain: token.chain || 'ethereum'
      })
      setAnalysis(response.data)

      try {
        const hist = await axios.get(
          `${API_BASE}/health/history/${contractAddress}?chain=${token.chain || 'ethereum'}&limit=6`
        )
        setHistory(hist.data.history || [])
      } catch {
        setHistory([])
      }
    } catch (err) {
      console.error('Analysis error:', err)
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (!token) return null

  const scoreColor = (score) => {
    if (score >= 70) return 'var(--green)'
    if (score >= 40) return 'var(--orange)'
    return 'var(--red)'
  }

  const formatMetricValue = (value) => {
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    if (typeof value === 'number') return value.toLocaleString()
    return String(value)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div>
            <h2>{token.symbol || token.name}</h2>
            <p className="modal-subtitle">{token.name}</p>
            <p className="modal-address">{token.address || token.contract}</p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        {/* Tabs */}
        <div className="modal-tabs">
          {['overview', 'categories', 'metrics', 'flags'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`modal-tab ${activeTab === tab ? 'active' : ''}`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="modal-body">
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Analyzing token…</p>
            </div>
          )}

          {error && <div className="error">{error}</div>}

          {analysis && activeTab === 'overview' && (
            <div className="modal-section">
              <div className="score-cards">
                <div className="score-card">
                  <div className="score-card-label">Health Score</div>
                  <div className="score-card-value" style={{ color: scoreColor(analysis.overall_score) }}>
                    {analysis.overall_score.toFixed(1)}
                  </div>
                  <div className="score-card-hint">out of 100 (higher is healthier)</div>
                </div>
                <div className="score-card">
                  <div className="score-card-label">Risk Level</div>
                  <div className="score-card-value" style={{ color: scoreColor(analysis.overall_score), fontSize: '1.3rem' }}>
                    {analysis.risk_level.replace('_', ' ').toUpperCase()}
                  </div>
                </div>
                <div className="score-card">
                  <div className="score-card-label">Confidence</div>
                  <div className="score-card-value">{(analysis.confidence * 100).toFixed(0)}%</div>
                  <div className="score-card-hint">how much data backed this score</div>
                </div>
                <div className="score-card">
                  <div className="score-card-label">Data Completeness</div>
                  <div className="score-card-value">{(analysis.data_completeness * 100).toFixed(0)}%</div>
                  <div className="score-card-hint">fields populated</div>
                </div>
              </div>

              {analysis.recommendations?.length > 0 && (
                <div className="modal-panel">
                  <h3>Recommendations</h3>
                  <ol className="modal-list">
                    {analysis.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ol>
                </div>
              )}

              {analysis.summary && (
                <div className="modal-panel">
                  <h3>AI Summary</h3>
                  <p className="modal-summary">{analysis.summary}</p>
                </div>
              )}

              {history.length > 1 && (
                <div className="modal-panel">
                  <h3>Score history</h3>
                  {(() => {
                    const prev = history[1]  // history[0] is this analysis
                    const delta = analysis.overall_score - prev.score
                    return (
                      <p className="history-delta">
                        {delta === 0 ? 'Unchanged' : `${delta > 0 ? '+' : ''}${delta.toFixed(1)} points`} since
                        the previous analysis ({prev.created_at})
                      </p>
                    )
                  })()}
                  <ul className="history-list">
                    {history.map((row, idx) => (
                      <li key={idx}>
                        <span className="history-date">{row.created_at}</span>
                        <span className="history-score" style={{ color: scoreColor(row.score) }}>
                          {row.score.toFixed(1)}
                        </span>
                        <span className="history-risk">{row.risk_level.replace('_', ' ')}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {analysis && activeTab === 'categories' && (
            <div className="modal-section">
              {analysis.category_scores.map((cat, idx) => (
                <div key={idx} className="category-card">
                  <div className="category-header">
                    <span className="category-name">
                      {cat.category}
                      <span className="category-weight"> · weight {(cat.weight * 100).toFixed(0)}%</span>
                    </span>
                    <span className="category-score" style={{ color: scoreColor(cat.score) }}>
                      {cat.score.toFixed(1)}
                    </span>
                  </div>
                  <div className="category-bar">
                    <div
                      className="category-bar-fill"
                      style={{ width: `${cat.score}%`, background: scoreColor(cat.score) }}
                    />
                  </div>
                  {cat.issues?.length > 0 && (
                    <ul className="modal-list issues">
                      {cat.issues.map((issue, i) => <li key={i}>{issue}</li>)}
                    </ul>
                  )}
                  {cat.strengths?.length > 0 && (
                    <ul className="modal-list strengths">
                      {cat.strengths.map((strength, i) => <li key={i}>{strength}</li>)}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          )}

          {analysis && activeTab === 'metrics' && (
            <div className="modal-section">
              {Object.entries(analysis.metrics).map(([category, data]) => {
                const entries = Object.entries(data || {}).filter(
                  ([, value]) => value !== null && value !== undefined && value !== '' &&
                    !(Array.isArray(value) && value.length === 0)
                )
                if (entries.length === 0) return null
                return (
                  <div key={category} className="modal-panel">
                    <h3>{category} metrics</h3>
                    <div className="metrics-grid">
                      {entries.map(([key, value]) => (
                        <div key={key} className="metric-cell">
                          <div className="metric-key">{key.replace(/_/g, ' ')}</div>
                          <div className="metric-value">{formatMetricValue(value)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          )}

          {analysis && activeTab === 'flags' && (
            <div className="modal-section">
              {analysis.red_flags?.length > 0 && (
                <div className="modal-panel flag-red">
                  <h3>Critical issues</h3>
                  <ul className="modal-list">
                    {analysis.red_flags.map((flag, idx) => <li key={idx}>{flag}</li>)}
                  </ul>
                </div>
              )}
              {analysis.yellow_flags?.length > 0 && (
                <div className="modal-panel flag-yellow">
                  <h3>Warnings</h3>
                  <ul className="modal-list">
                    {analysis.yellow_flags.map((flag, idx) => <li key={idx}>{flag}</li>)}
                  </ul>
                </div>
              )}
              {analysis.green_flags?.length > 0 && (
                <div className="modal-panel flag-green">
                  <h3>Strengths</h3>
                  <ul className="modal-list">
                    {analysis.green_flags.slice(0, 10).map((flag, idx) => <li key={idx}>{flag}</li>)}
                  </ul>
                </div>
              )}
              {!analysis.red_flags?.length && !analysis.yellow_flags?.length && !analysis.green_flags?.length && (
                <p className="modal-empty">No flags available for this token.</p>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <span className="modal-footer-note">
            {analysis ? `${analysis.category_scores?.length || 0} of 7 categories had data` : ''}
          </span>
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}

export default TokenDetailModal
