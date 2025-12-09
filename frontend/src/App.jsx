import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import cytoscape from 'cytoscape'
import coseBilkent from 'cytoscape-cose-bilkent'

// Register layout
cytoscape.use(coseBilkent)

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

function App() {
  const [contract, setContract] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const cyRef = useRef(null)
  const cyInstance = useRef(null)

  const analyzeToken = async (useSample = false) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      let response
      if (useSample) {
        response = await axios.get(`${API_BASE}/health/sample`)
      } else {
        response = await axios.post(`${API_BASE}/health/demo`, {
          contract: contract,
          chain: 'ethereum'
        })
      }
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const loadSample = () => {
    analyzeToken(true)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!contract.trim()) {
      setError('Please enter a contract address')
      return
    }
    analyzeToken(false)
  }

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
          id: `${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          label: edge.label,
          type: edge.type,
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
            'background-color': '#667eea',
            'label': 'data(label)',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'width': '60px',
            'height': '60px',
            'text-wrap': 'wrap',
            'text-max-width': '80px'
          }
        },
        {
          selector: 'node[type="token"]',
          style: {
            'background-color': '#4caf50',
            'width': '80px',
            'height': '80px',
            'font-size': '14px',
            'font-weight': 'bold'
          }
        },
        {
          selector: 'node[type="owner"]',
          style: {
            'background-color': '#ff9800',
            'shape': 'diamond'
          }
        },
        {
          selector: 'node[type="holder"]',
          style: {
            'background-color': '#2196f3'
          }
        },
        {
          selector: 'node[type="liquidity_pool"]',
          style: {
            'background-color': '#9c27b0',
            'shape': 'hexagon'
          }
        },
        {
          selector: 'node[type="locker"]',
          style: {
            'background-color': '#f44336',
            'shape': 'rectangle'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 3,
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10
          }
        }
      ],
      layout: {
        name: 'cose-bilkent',
        animate: true,
        animationDuration: 1000,
        randomize: false,
        nodeRepulsion: 8000,
        idealEdgeLength: 100,
        edgeElasticity: 0.45,
        nestingFactor: 0.1,
        gravity: 0.25,
        numIter: 2500,
        tile: true
      }
    })

    // Add click handler for nodes
    cyInstance.current.on('tap', 'node', (evt) => {
      const node = evt.target
      console.log('Node clicked:', node.data())
    })
  }

  const getRiskLevel = (score) => {
    if (score >= 70) return { level: 'HIGH RISK', class: 'risk-high' }
    if (score >= 40) return { level: 'MODERATE RISK', class: 'risk-moderate' }
    return { level: 'LOW RISK', class: 'risk-low' }
  }

  const formatMetricValue = (key, value) => {
    if (typeof value === 'boolean') return value ? 'Yes' : 'No'
    if (key.includes('pct')) return `${value.toFixed(2)}%`
    if (key.includes('usd') || key.includes('cap')) return `$${value.toLocaleString()}`
    if (typeof value === 'number' && value > 1000) return value.toLocaleString()
    return value
  }

  const formatMetricKey = (key) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
  }

  return (
    <div className="container">
      <header className="header">
        <h1>TokenHealth</h1>
        <p>On-chain Token Due Diligence System</p>
      </header>

      <div className="disclaimer">
        <strong>DISCLAIMER:</strong> This tool is for research and educational purposes only.
        Not financial advice. Always verify on-chain data independently before making decisions.
      </div>

      <div className="input-section">
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <input
              type="text"
              placeholder="Enter token contract address (0x...)"
              value={contract}
              onChange={(e) => setContract(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Analyzing...' : 'Analyze Token'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={loadSample}
              disabled={loading}
            >
              Load Sample
            </button>
          </div>
        </form>
      </div>

      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="loading">
          <p>Analyzing token... Building knowledge graph and computing risk score...</p>
        </div>
      )}

      {result && (
        <>
          <div className="results-grid">
            <div className="card">
              <h2>Risk Score</h2>
              <div className={`risk-score ${getRiskLevel(result.risk_score).class}`}>
                {result.risk_score.toFixed(0)}
              </div>
              <div className={`risk-label ${getRiskLevel(result.risk_score).class}`}>
                {getRiskLevel(result.risk_score).level}
              </div>
            </div>

            <div className="card">
              <h2>Summary</h2>
              <ul className="summary-list">
                {result.summary.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="results-grid">
            <div className="card">
              <h2>Top Risks</h2>
              <ul className="risk-list">
                {result.top_risks.map((risk, idx) => (
                  <li key={idx}>{risk}</li>
                ))}
              </ul>
            </div>

            <div className="card">
              <h2>Next Checks</h2>
              <ul className="checks-list">
                {result.next_checks.map((check, idx) => (
                  <li key={idx}>{check}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card" style={{ marginBottom: '2rem' }}>
            <h2>Knowledge Graph</h2>
            <div ref={cyRef} id="cy"></div>
          </div>

          <div className="card" style={{ marginBottom: '2rem' }}>
            <h2>Risk Factors</h2>
            <ul className="reasons-list">
              {result.reasons.map((reason, idx) => (
                <li key={idx} className={reason.contribution > 0 ? 'negative' : 'positive'}>
                  <div className="reason-header">
                    <span className="reason-id">
                      {reason.id.replace(/_/g, ' ')}
                    </span>
                    <span className={`reason-contribution ${reason.contribution > 0 ? 'risk-high' : 'risk-low'}`}>
                      {reason.contribution > 0 ? '+' : ''}{reason.contribution}
                    </span>
                  </div>
                  <div className="reason-note">{reason.note}</div>
                </li>
              ))}
            </ul>
          </div>

          <div className="card">
            <h2>Metrics</h2>
            <div className="metrics-grid">
              {Object.entries(result.metrics)
                .filter(([key]) => !['contract', 'symbol', 'name', 'owner'].includes(key))
                .map(([key, value]) => (
                  <div key={key} className="metric-item">
                    <div className="metric-label">{formatMetricKey(key)}</div>
                    <div className="metric-value">{formatMetricValue(key, value)}</div>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default App
