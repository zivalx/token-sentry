import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'

// Register layout
cytoscape.use(coseBilkent)

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function ComprehensiveHealth() {
  const [contract, setContract] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [includeLLM, setIncludeLLM] = useState(false)
  const cyRef = useRef(null)
  const cyInstance = useRef(null)

  const analyzeToken = async () => {
    if (!contract.trim()) {
      setError('Please enter a contract address or ticker')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(
        `${API_BASE}/health/comprehensive?include_llm=${includeLLM}`,
        {
          contract: contract,
          chain: 'ethereum'
        }
      )
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    analyzeToken()
  }

  // Example tokens for quick testing
  const exampleTokens = [
    { name: 'UNI', address: '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984' },
    { name: 'LINK', address: '0x514910771af9ca656af840dff83e8264ecf986ca' },
    { name: 'DAI', address: '0x6b175474e89094c44da98b954eedeac495271d0f' },
  ]

  const loadExample = (address) => {
    setContract(address)
    setError(null)
  }

  // Render graph when result changes
  useEffect(() => {
    if (result && result.graph && cyRef.current) {
      renderGraph(result.graph)
    }
  }, [result])

  const renderGraph = (graph) => {
    if (cyInstance.current) {
      cyInstance.current.destroy()
    }

    const elements = []

    // Add nodes
    graph.nodes.forEach(node => {
      elements.push({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          ...node
        }
      })
    })

    // Add edges
    graph.edges.forEach(edge => {
      elements.push({
        data: {
          id: `${edge.source}-${edge.target}-${Math.random()}`,
          source: edge.source,
          target: edge.target,
          label: edge.label,
          type: edge.type,
          width: edge.width || 2,
          ...edge
        }
      })
    })

    cyInstance.current = cytoscape({
      container: cyRef.current,
      elements: elements,
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'text-wrap': 'wrap',
            'text-max-width': '80px',
            'color': '#fff',
            'text-outline-color': '#000',
            'text-outline-width': 1
          }
        },
        {
          selector: 'node[type="token"]',
          style: {
            'shape': 'hexagon',
            'font-size': '14px',
            'font-weight': 'bold'
          }
        },
        {
          selector: 'node[type="category"]',
          style: {
            'shape': 'ellipse',
            'font-size': '11px',
            'font-weight': 'bold'
          }
        },
        {
          selector: 'node[type="issue"]',
          style: {
            'shape': 'rectangle',
            'font-size': '8px'
          }
        },
        {
          selector: 'node[type="strength"]',
          style: {
            'shape': 'rectangle',
            'font-size': '8px'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': 'data(color)',
            'target-arrow-color': 'data(color)',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'text-rotation': 'autorotate'
          }
        }
      ],
      layout: {
        name: 'cose-bilkent',
        animate: true,
        randomize: false,
        nodeRepulsion: 4500,
        idealEdgeLength: 100,
        edgeElasticity: 0.45,
        nestingFactor: 0.1,
        gravity: 0.25,
        numIter: 2500,
        tile: true
      }
    })

    // Fit to view
    cyInstance.current.fit()
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

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-blue-600'
    if (score >= 40) return 'text-yellow-600'
    if (score >= 20) return 'text-orange-600'
    return 'text-red-600'
  }

  const getScoreBarColor = (score) => {
    if (score >= 80) return 'bg-green-500'
    if (score >= 60) return 'bg-blue-500'
    if (score >= 40) return 'bg-yellow-500'
    if (score >= 20) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Comprehensive Token Health Analysis
          </h1>
          <p className="text-gray-600">
            Multi-source analysis across 7 categories: Market, On-Chain, Liquidity, Security, Social, Team, Utility
          </p>
        </div>

        {/* Input Form */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Contract Address or Ticker Symbol
              </label>
              <input
                type="text"
                value={contract}
                onChange={(e) => setContract(e.target.value)}
                placeholder="0x... or UNI"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="includeLLM"
                checked={includeLLM}
                onChange={(e) => setIncludeLLM(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="includeLLM" className="text-sm text-gray-700">
                Include AI Summary (requires ANTHROPIC_API_KEY)
              </label>
            </div>

            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {loading ? 'Analyzing...' : 'Analyze Token'}
              </button>

              {exampleTokens.map(token => (
                <button
                  key={token.address}
                  type="button"
                  onClick={() => loadExample(token.address)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                >
                  Try {token.name}
                </button>
              ))}
            </div>
          </form>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mb-6">
            <p className="font-medium">Error:</p>
            <p>{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Overall Score Card */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Overall Health Score</p>
                  <p className={`text-5xl font-bold ${getScoreColor(result.overall_score)}`}>
                    {result.overall_score.toFixed(1)}
                  </p>
                  <p className="text-gray-500 text-sm mt-1">out of 100</p>
                </div>

                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Risk Level</p>
                  <span className={`inline-block px-4 py-2 rounded-full font-semibold text-sm border ${getRiskLevelColor(result.risk_level)}`}>
                    {result.risk_level.replace('_', ' ').toUpperCase()}
                  </span>
                </div>

                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Confidence</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {(result.confidence * 100).toFixed(0)}%
                  </p>
                  <p className="text-gray-500 text-sm mt-1">data quality</p>
                </div>

                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Data Completeness</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {(result.data_completeness * 100).toFixed(0)}%
                  </p>
                  <p className="text-gray-500 text-sm mt-1">fields populated</p>
                </div>
              </div>
            </div>

            {/* Category Scores */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Category Breakdown</h2>
              <div className="space-y-4">
                {result.category_scores.map((cat, idx) => (
                  <div key={idx} className="border-b border-gray-200 pb-4 last:border-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <span className="font-semibold text-gray-900 capitalize">
                          {cat.category}
                        </span>
                        <span className="text-sm text-gray-500">
                          (weight: {(cat.weight * 100).toFixed(0)}%)
                        </span>
                      </div>
                      <span className={`text-xl font-bold ${getScoreColor(cat.score)}`}>
                        {cat.score.toFixed(1)}
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className={`h-2 rounded-full ${getScoreBarColor(cat.score)}`}
                        style={{ width: `${cat.score}%` }}
                      />
                    </div>

                    {/* Issues and Strengths */}
                    {cat.issues && cat.issues.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-red-600 mb-1">Issues:</p>
                        <ul className="text-xs text-red-700 space-y-1">
                          {cat.issues.map((issue, i) => (
                            <li key={i}>⚠️ {issue}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {cat.strengths && cat.strengths.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-green-600 mb-1">Strengths:</p>
                        <ul className="text-xs text-green-700 space-y-1">
                          {cat.strengths.map((strength, i) => (
                            <li key={i}>✓ {strength}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Flags Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Red Flags */}
              {result.red_flags && result.red_flags.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <h3 className="font-bold text-red-900 mb-3">🚨 Red Flags</h3>
                  <ul className="space-y-2 text-sm text-red-800">
                    {result.red_flags.map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-red-600 mt-0.5">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Yellow Flags */}
              {result.yellow_flags && result.yellow_flags.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-bold text-yellow-900 mb-3">⚠️ Warnings</h3>
                  <ul className="space-y-2 text-sm text-yellow-800">
                    {result.yellow_flags.map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-yellow-600 mt-0.5">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Green Flags */}
              {result.green_flags && result.green_flags.length > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h3 className="font-bold text-green-900 mb-3">✅ Strengths</h3>
                  <ul className="space-y-2 text-sm text-green-800">
                    {result.green_flags.slice(0, 5).map((flag, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-green-600 mt-0.5">•</span>
                        <span>{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-bold text-blue-900 mb-3">📋 Recommendations</h3>
                <ol className="space-y-2 text-sm text-blue-900">
                  {result.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="font-semibold">{idx + 1}.</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* AI Summary */}
            {result.summary && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
                <h3 className="font-bold text-purple-900 mb-3">🤖 AI Analysis</h3>
                <p className="text-sm text-purple-900 whitespace-pre-line">
                  {result.summary}
                </p>
              </div>
            )}

            {/* Graph Visualization */}
            {result.graph && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Health Factor Network
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  Visualizing category scores, issues, and strengths.
                  Token at center → Categories → Contributing factors.
                </p>
                <div
                  ref={cyRef}
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg"
                  style={{ height: '600px' }}
                />
                {result.graph.metadata && (
                  <p className="text-xs text-gray-500 mt-2">
                    Graph: {result.graph.metadata.total_nodes} nodes,
                    {result.graph.metadata.total_edges} edges,
                    {result.graph.metadata.categories} categories
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ComprehensiveHealth
