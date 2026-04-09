import { useState, useEffect } from 'react'

// Simple syntax highlighter for JSON
const formatJSON = (obj) => {
  if (!obj) return 'null';
  const jsonStr = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
  
  // Basic regex to highlight JSON
  return jsonStr.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
    let cls = 'json-number';
    if (/^"/.test(match)) {
      if (/:$/.test(match)) {
        cls = 'json-key';
      } else {
        cls = 'json-string';
      }
    } else if (/true|false/.test(match)) {
      cls = 'json-boolean';
    } else if (/null/.test(match)) {
      cls = 'json-boolean';
    }
    return `<span class="${cls}">${match}</span>`;
  });
}

const TraceVisualization = ({ trace }) => {
  if (!trace || !trace.tool_calls || trace.tool_calls.length === 0) return null;

  // Synthesize timeline logic for rendering waterfall
  const calls = trace.tool_calls;
  let runningTime = 0;
  
  const processedCalls = calls.map(call => {
    const duration = call.duration_ms || Math.random() * 500 + 100;
    const item = {
      ...call,
      startMs: runningTime,
      durationMs: duration
    };
    runningTime += duration + (Math.random() * 100); // add small synthetic delay between calls
    return item;
  });

  const totalMs = runningTime;

  return (
    <div className="trace-graph">
      <div className="graph-title">Execution Latency Visualization</div>
      
      <div className="graph-labels">
        <span>0ms</span>
        <span>{Math.round(totalMs / 2)}ms</span>
        <span>{Math.round(totalMs)}ms</span>
      </div>

      <div className="graph-grid">
        <div className="graph-axis" style={{ left: '0%' }}></div>
        <div className="graph-axis" style={{ left: '50%' }}></div>
        <div className="graph-axis" style={{ left: '100%' }}></div>
      </div>

      <div className="graph-content">
        {processedCalls.map((call, idx) => {
          const leftPercent = (call.startMs / totalMs) * 100;
          const widthPercent = (call.durationMs / totalMs) * 100;
          
          return (
            <div key={idx} className="graph-row">
              <div 
                className="graph-bar-container" 
                style={{ 
                  left: `${leftPercent}%`, 
                  width: `${Math.max(widthPercent, 1)}%` 
                }}
              >
                <div className="graph-call-name">
                  {call.name}
                </div>
                <div className="graph-bar" style={{ width: '100%' }}></div>
                <div className="graph-tooltip">
                  {call.name}: {call.durationMs.toFixed(1)}ms
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};


function App() {
  const [snapshots, setSnapshots] = useState([])
  const [selectedSnapshot, setSelectedSnapshot] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // In production this will be served by the same host, so /api/snapshots works.
    // For local dev without the python server running, we add a fallback.
    const fetchSnapshots = async () => {
      try {
        const response = await fetch('/api/snapshots')
        if (response.ok) {
          const data = await response.json()
          setSnapshots(data)
          if (data.length > 0) {
            setSelectedSnapshot(data[0])
          }
        } else {
          // Dummy data fallback for UI testing
          fallbackData()
        }
      } catch (e) {
        fallbackData()
      } finally {
        setLoading(false)
      }
    }
    
    fetchSnapshots()
  }, [])

  const fallbackData = () => {
    const dummy = [
      {
        id: "flight_booking_flow",
        name: "test_books_correct_flight",
        filename: "flight_booking_flow.json",
        path: ".agentcontract/snapshots/flight_booking_flow.json",
        trace: {
          start_time: Date.now() / 1000 - 10,
          end_time: Date.now() / 1000,
          tool_calls: [
            { name: "search_flights", args: { destination: "NYC" }, step: 0, duration_ms: 1200, agent_id: "travel_agent" },
            { name: "verify_availability", args: { date: "10-22-2027" }, step: 1, duration_ms: 2500, agent_id: "data_agent" },
            { name: "book_flight", args: { id: "FL001", passenger: "John" }, step: 2, duration_ms: 300, agent_id: "travel_agent" }
          ]
        }
      },
      {
        id: "multi_agent_flow",
        name: "test_complex_mult_agent_workflow",
        filename: "multi_agent_flow.json",
        path: ".agentcontract/snapshots/multi_agent_flow.json",
        trace: {
          start_time: Date.now() / 1000 - 5,
          end_time: Date.now() / 1000,
          tool_calls: [
            { name: "auth_user", args: { token: "abc" }, step: 0, duration_ms: 50, agent_id: "auth_agent" },
            { name: "db_query", args: { query: "SELECT * FROM users" }, step: 1, duration_ms: 500, agent_id: "data_agent" },
            { name: "update_logs", args: { status: "success" }, step: 2, duration_ms: 150, agent_id: "audit_agent" }
          ]
        }
      }
    ]
    setSnapshots(dummy)
    setSelectedSnapshot(dummy[0])
  }

  const formatTime = (epochSeconds) => {
    return new Date(epochSeconds * 1000).toLocaleString()
  }

  const getDurationString = (start, end) => {
    if (!start || !end) return 'Unknown'
    const ms = (end - start) * 1000
    if (ms > 1000) return `${(ms / 1000).toFixed(2)}s`
    return `${Math.round(ms)}ms`
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="nav-brand">
          <img src="/logo.png" alt="AgentSpec Logo" className="nav-logo" />
          <div className="nav-title">AgentSpec Trace Visualizer</div>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <span className="badge badge-blue">Local Engine Active</span>
        </div>
      </nav>

      <main className="main-content">
        <div className="dashboard-grid">
          
          {/* Sidebar ListView */}
          <div className="snapshot-list">
            <h2 style={{ marginBottom: '1rem', fontSize: '1.25rem', fontWeight: 600 }}>Snapshots</h2>
            {loading ? (
              <div style={{ color: 'var(--text-muted)' }}>Loading traces...</div>
            ) : snapshots.length === 0 ? (
              <div className="empty-state">No snapshots found in .agentcontract/snapshots</div>
            ) : (
              snapshots.map(snap => (
                <div 
                  key={snap.id} 
                  className={`glass-panel glow-hover snapshot-card ${selectedSnapshot?.id === snap.id ? 'active' : ''}`}
                  onClick={() => setSelectedSnapshot(snap)}
                >
                  <div className="snapshot-header">
                    <div className="snapshot-name" title={snap.name}>
                      {snap.id}
                    </div>
                  </div>
                  <div className="snapshot-meta">
                    <div>{snap.trace?.tool_calls?.length || 0} tools called</div>
                    <div>{formatTime(snap.trace?.start_time)}</div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Main Trace Viewer */}
          <div className="glass-panel" style={{ padding: '2rem', height: '100%', display: 'flex', flexDirection: 'column' }}>
            {!selectedSnapshot ? (
              <div className="empty-state">
                <div>Select a snapshot to view the trace trajectory</div>
              </div>
            ) : (
              <div className="snapshot-detail">
                <div className="detail-header">
                  <div className="detail-title">{selectedSnapshot.id}</div>
                  <div className="stat-row">
                    <div className="stat-item">
                      <span className="stat-label">File</span>
                      <span className="stat-value">{selectedSnapshot.filename}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Total Latency</span>
                      <span className="stat-value">
                        {getDurationString(selectedSnapshot.trace?.start_time, selectedSnapshot.trace?.end_time)}
                      </span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Operations</span>
                      <span className="stat-value">{selectedSnapshot.trace?.tool_calls?.length || 0}</span>
                    </div>
                  </div>
                </div>

                <TraceVisualization trace={selectedSnapshot.trace} />

                <div className="trace-timeline">
                  {selectedSnapshot.trace?.tool_calls?.map((call, idx) => (
                    <div key={idx} className="tool-call-item">
                      <div className="tool-marker">{call.step}</div>
                      <div className="glass-panel tool-content">
                        <div className="tool-header">
                          <div className="tool-name-container">
                            <span className="tool-name">{call.name}</span>
                            {call.agent_id && (
                              <span className="badge badge-purple" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#a78bfa', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
                                {call.agent_id}
                              </span>
                            )}
                          </div>
                          <div className="tool-duration">
                            {call.duration_ms ? `${call.duration_ms.toFixed(1)}ms` : ''}
                          </div>
                        </div>
                        
                        <div style={{ marginTop: '0.5rem' }}>
                          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Arguments</div>
                          <pre 
                            className="json-block"
                            dangerouslySetInnerHTML={{ __html: formatJSON(call.args) }}
                          />
                        </div>

                        {call.response && (
                          <div style={{ marginTop: '1rem' }}>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Response</div>
                            <pre 
                              className="json-block"
                              dangerouslySetInnerHTML={{ __html: formatJSON(call.response) }}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  
                  {(!selectedSnapshot.trace?.tool_calls || selectedSnapshot.trace.tool_calls.length === 0) && (
                    <div className="empty-state" style={{ marginTop: '2rem' }}>
                      No tool calls recorded in this trace.
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

        </div>
      </main>
    </div>
  )
}

export default App
