import { useState } from 'react'

export default function NewFIR() {
  const [formData, setFormData] = useState({
    complainant_name: '',
    complainant_email: '',
    police_station: '',
    district: '',
    complaint_text: ''
  })
  
  const [logs, setLogs] = useState([])
  const [finalRecord, setFinalRecord] = useState(null)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0) // 0: Form, 1: Intake, 2: Legal, 3: Drafting, 4: Finalized

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setLogs([])
    setFinalRecord(null)
    setStep(1)

    try {
      const response = await fetch('http://localhost:5000/api/firs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder("utf-8")

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.substring(6))
            if (data.type === 'pipeline_complete') {
              setFinalRecord(data.fir_record)
              setDraft(data.fir_record.draft)
              setStep(3)
              setLoading(false)
            } else {
              setLogs(prev => [...prev, data])
              if (data.agent === 'Legal Agent') setStep(2)
              if (data.agent === 'Drafting Agent') setStep(3)
            }
          }
        }
      }
    } catch (error) {
      console.error(error)
      setLoading(false)
      setStep(0)
    }
  }

  const handleFinalize = async () => {
    try {
      const encodedId = encodeURIComponent(finalRecord.fir_number.replace('/', '_'))
      const response = await fetch(`http://localhost:5000/api/firs/${encodedId}/finalize`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ draft })
      })
      const result = await response.json()
      if (result.status === 'success') {
        alert('FIR Finalized and Issued! TX Hash: ' + result.tx_hash)
        setStep(4)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const handleDownload = () => {
    const encodedId = encodeURIComponent(finalRecord.fir_number.replace('/', '_'))
    window.open(`http://localhost:5000/api/firs/${encodedId}/pdf`, '_blank')
  }

  return (
    <div className="wrap">
      <div className="page-head">
        <div>
          <div className="eyebrow">NEW COMPLAINT INTAKE</div>
          <h1>Draft a First Information Report</h1>
        </div>
        {finalRecord && <div className="draft-id">{finalRecord.fir_number} · auto-saved</div>}
      </div>

      {step === 0 && (
        <form onSubmit={handleSubmit} className="panel" style={{padding: '24px', maxWidth: '800px', margin: '0 auto'}}>
          <h3 style={{fontFamily: 'var(--serif)', marginBottom: '20px'}}>Initial Complaint Details</h3>
          <div style={{display: 'flex', gap: '15px'}}>
            <input type="text" placeholder="Complainant Name" required onChange={e => setFormData({...formData, complainant_name: e.target.value})} />
            <input type="email" placeholder="Complainant Email" required onChange={e => setFormData({...formData, complainant_email: e.target.value})} />
          </div>
          <div style={{display: 'flex', gap: '15px'}}>
            <input type="text" placeholder="Police Station" required onChange={e => setFormData({...formData, police_station: e.target.value})} />
            <input type="text" placeholder="District" required onChange={e => setFormData({...formData, district: e.target.value})} />
          </div>
          <textarea placeholder="Complaint Text" required onChange={e => setFormData({...formData, complaint_text: e.target.value})} />
          
          <div className="input-foot" style={{justifyContent: 'flex-end'}}>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Processing Pipeline...' : 'Generate FIR →'}
            </button>
          </div>
        </form>
      )}

      {step > 0 && (
        <>
          <div className="stepper">
            <div className={`step ${step > 1 ? 'done' : 'active'}`}>
              <div className="step-circle">{step > 1 ? '✓' : '1'}</div>
              <div className="step-label"><span className="name">Intake</span><span className="desc">Facts extracted</span></div>
            </div>
            <div className={`step-line ${step > 1 ? 'done' : ''}`}></div>
            <div className={`step ${step > 2 ? 'done' : step === 2 ? 'active' : 'pending'}`}>
              <div className="step-circle">{step > 2 ? '✓' : '2'}</div>
              <div className="step-label"><span className="name">Legal Matching</span><span className="desc">Reviewing sections</span></div>
            </div>
            <div className={`step-line ${step > 2 ? 'done' : ''}`}></div>
            <div className={`step ${step > 3 ? 'done' : step === 3 ? 'active' : 'pending'}`}>
              <div className="step-circle">{step > 3 ? '✓' : '3'}</div>
              <div className="step-label"><span className="name">Drafting</span><span className="desc">Awaiting approval</span></div>
            </div>
            <div className={`step-line ${step > 3 ? 'done' : ''}`}></div>
            <div className={`step ${step === 4 ? 'done' : 'pending'}`}>
              <div className="step-circle">{step === 4 ? '✓' : '4'}</div>
              <div className="step-label"><span className="name">Finalize</span><span className="desc">Export PDF</span></div>
            </div>
          </div>

          <div className="grid">
            {/* LEFT WORK AREA */}
            <div>
              <div className="panel" style={{marginBottom: '24px'}}>
                <div className="panel-head">
                  <h3>Complainant's Account</h3>
                  <span className="hint">Plain language, any detail level</span>
                </div>
                <div className="panel-body">
                  <textarea readOnly value={formData.complaint_text} style={{minHeight: '120px'}}></textarea>
                  <div className="input-foot">
                    <span className="char-count">{formData.complaint_text.length} characters</span>
                  </div>
                  
                  {finalRecord?.facts && (
                    <div className="fact-grid">
                      {finalRecord.facts.split('\n').filter(Boolean).map((factLine, i) => {
                        const parts = factLine.replace('- **', '').split('**: ')
                        if (parts.length === 2) {
                          return (
                            <div className="fact" key={i}>
                              <div className="k">{parts[0]}</div>
                              <div className="v">{parts[1]}</div>
                            </div>
                          )
                        }
                        return null
                      })}
                    </div>
                  )}
                </div>
              </div>

              {finalRecord?.sections && (
                <div className="panel">
                  <div className="panel-head">
                    <h3>Matched Legal Sections</h3>
                    <span className="hint">Ranked by semantic + reasoning match</span>
                  </div>
                  <div className="panel-body">
                    {finalRecord.sections.split('\n\n').filter(Boolean).map((sectionStr, i) => {
                      const lines = sectionStr.split('\n')
                      const title = lines[0].replace('### ', '')
                      const reason = lines.find(l => l.startsWith('**Reasoning:**'))?.replace('**Reasoning:** ', '') || ''
                      return (
                        <div className="match-card" key={i}>
                          <div className="match-top">
                            <div className="match-act">
                              <span className={`act-chip ${title.includes('BNS') ? 'bns' : 'ipc'}`}>
                                {title.includes('BNS') ? 'BNS' : 'IPC'}
                              </span>
                              <span className="sec-num">{title}</span>
                            </div>
                            <span className="confidence">Matched</span>
                          </div>
                          <div className="match-reason">{reason}</div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT RAIL */}
            <div>
              <div className="panel" style={{marginBottom: '20px'}}>
                <div className="panel-head"><h3>Pipeline Status</h3></div>
                <div className="panel-body">
                  {logs.slice(-3).map((log, i) => (
                    <div className="agent-status" key={i}>
                      <div className="agent-dot active"></div>
                      <div className="agent-info">
                        <div className="name">{log.agent}</div>
                        <div className="task">{log.message.substring(0, 45)}...</div>
                      </div>
                    </div>
                  ))}
                  {finalRecord && (
                    <div className="agent-status">
                      <div className="agent-dot done"></div>
                      <div className="agent-info">
                        <div className="name">Drafting Agent</div>
                        <div className="task">Awaiting officer verification</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {finalRecord && (
                <div className="panel">
                  <div className="panel-head"><h3>Live Draft Preview</h3></div>
                  <div className="panel-body">
                    <textarea 
                      className="preview-box" 
                      style={{width: '100%', minHeight: '350px', border: '1px solid var(--line)'}} 
                      value={draft}
                      onChange={e => setDraft(e.target.value)}
                    />
                    <div style={{display: 'flex', gap: '10px', marginTop: '15px', flexDirection: 'column'}}>
                      {step !== 4 ? (
                        <button className="btn btn-primary" style={{width: '100%', justifyContent: 'center'}} onClick={handleFinalize}>
                          Finalize & Issue FIR →
                        </button>
                      ) : (
                        <button className="btn btn-ghost" style={{width: '100%', justifyContent: 'center'}} onClick={handleDownload}>
                          Download Official PDF
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
