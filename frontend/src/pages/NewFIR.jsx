import { useState } from 'react'
import { useProfile } from '../context/ProfileContext'

export default function NewFIR() {
  const [formData, setFormData] = useState({
    // Complainant Details (Required)
    complainant_name: '',
    address: '',
    district: '',
    phone_number: '',
    // Complainant Details (Optional)
    dob: '',
    gender: '',
    id_proof_type: '',
    id_proof_number: '',
    
    // Incident Details
    incident_date: '',
    incident_time: '',
    incident_location: '',
    landmark: '',
    complaint_text: '',
    
    // Accused Details (Optional)
    accused_name: '',
    accused_description: '',
    accused_vehicle: '',
    
    // Witnesses
    witnesses: []
  })
  
  const { profile } = useProfile()
  
  const [logs, setLogs] = useState([])
  const [finalRecord, setFinalRecord] = useState(null)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [step, setStep] = useState(0) // 0: Form, 1: Intake, 2: Legal, 3: Drafting, 4: Finalized

  const handleAddWitness = () => {
    setFormData({ ...formData, witnesses: [...formData.witnesses, { name: '', contact: '' }] })
  }

  const handleRemoveWitness = (index) => {
    const newWitnesses = [...formData.witnesses]
    newWitnesses.splice(index, 1)
    setFormData({ ...formData, witnesses: newWitnesses })
  }

  const handleWitnessChange = (index, field, value) => {
    const newWitnesses = [...formData.witnesses]
    newWitnesses[index][field] = value
    setFormData({ ...formData, witnesses: newWitnesses })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setLogs([])
    setFinalRecord(null)
    setStep(1)

    // Add officer details from context into the payload
    const payload = {
      ...formData,
      officer_name: profile.officerName,
      officer_rank: profile.rank,
      officer_station: `${profile.stationName}, ${profile.district}`
    }

    try {
      const response = await fetch('http://localhost:5000/api/firs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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
        <form onSubmit={handleSubmit} className="panel" style={{padding: '24px', maxWidth: '850px', margin: '0 auto'}}>
          {/* Officer Details (Readonly from Context) */}
          <div style={{background: 'var(--paper-dim)', padding: '16px', borderRadius: '8px', marginBottom: '24px', border: '1px solid var(--line)'}}>
            <h4 style={{fontFamily: 'var(--sans)', fontSize: '12px', textTransform: 'uppercase', color: 'var(--slate)', marginBottom: '12px', letterSpacing: '0.5px'}}>Filing Officer (Auto-filled)</h4>
            <div style={{display: 'flex', gap: '15px'}}>
              <input type="text" value={profile.officerName} readOnly style={{background: 'var(--paper)', color: 'var(--slate)', marginBottom: 0}} title="Officer Name" />
              <input type="text" value={profile.rank} readOnly style={{background: 'var(--paper)', color: 'var(--slate)', marginBottom: 0}} title="Rank" />
              <input type="text" value={profile.badgeNumber} readOnly style={{background: 'var(--paper)', color: 'var(--slate)', marginBottom: 0}} title="Badge Number" />
              <input type="text" value={profile.stationName} readOnly style={{background: 'var(--paper)', color: 'var(--slate)', marginBottom: 0}} title="Station" />
            </div>
          </div>

          <h3 style={{fontFamily: 'var(--serif)', marginBottom: '16px'}}>1. Complainant Details</h3>
          <div style={{display: 'flex', gap: '15px', marginBottom: '10px'}}>
            <input type="text" placeholder="Full Name *" required onChange={e => setFormData({...formData, complainant_name: e.target.value})} style={{flex: 1}} />
            <input type="text" placeholder="Phone Number (10 digits) *" required pattern="\d{10}" minLength="10" maxLength="10" onChange={e => setFormData({...formData, phone_number: e.target.value})} style={{flex: 1}} />
          </div>
          <div style={{display: 'flex', gap: '15px'}}>
            <input type="text" placeholder="Address *" required onChange={e => setFormData({...formData, address: e.target.value})} style={{flex: 2}} />
            <input type="text" placeholder="District/City *" required onChange={e => setFormData({...formData, district: e.target.value})} style={{flex: 1}} />
          </div>
          
          <div style={{display: 'flex', gap: '15px'}}>
            <input type="date" placeholder="Date of Birth" onChange={e => setFormData({...formData, dob: e.target.value})} />
            <select onChange={e => setFormData({...formData, gender: e.target.value})} style={{width: '100%', border: '1px solid var(--line)', borderRadius: '8px', padding: '16px', fontFamily: 'var(--sans)', fontSize: '14px', marginBottom: '10px'}}>
              <option value="">Select Gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div style={{display: 'flex', gap: '15px'}}>
            <select onChange={e => setFormData({...formData, id_proof_type: e.target.value})} style={{width: '100%', border: '1px solid var(--line)', borderRadius: '8px', padding: '16px', fontFamily: 'var(--sans)', fontSize: '14px', marginBottom: '10px'}}>
              <option value="">ID Proof Type</option>
              <option value="Aadhaar">Aadhaar</option>
              <option value="PAN">PAN</option>
              <option value="Voter ID">Voter ID</option>
              <option value="Passport">Passport</option>
              <option value="Driving License">Driving License</option>
            </select>
            <input type="text" placeholder="ID Proof Number" onChange={e => setFormData({...formData, id_proof_number: e.target.value})} />
          </div>

          <hr style={{border: 'none', borderTop: '1px solid var(--line)', margin: '24px 0'}} />

          <h3 style={{fontFamily: 'var(--serif)', marginBottom: '16px'}}>2. Incident Details</h3>
          <div style={{display: 'flex', gap: '15px', marginBottom: '10px'}}>
            <input type="date" required onChange={e => setFormData({...formData, incident_date: e.target.value})} style={{flex: 1}} title="Date of Incident *" />
            <input type="time" required onChange={e => setFormData({...formData, incident_time: e.target.value})} style={{flex: 1}} title="Time of Incident *" />
          </div>
          <div style={{display: 'flex', gap: '15px', marginBottom: '10px'}}>
            <input type="text" placeholder="Exact Incident Location / Address *" required onChange={e => setFormData({...formData, incident_location: e.target.value})} style={{flex: 2}} />
            <input type="text" placeholder="Landmark (Optional)" onChange={e => setFormData({...formData, landmark: e.target.value})} style={{flex: 1}} />
          </div>
          <textarea placeholder="Full Narrative Complaint *" required onChange={e => setFormData({...formData, complaint_text: e.target.value})} style={{minHeight: '140px'}} />

          <hr style={{border: 'none', borderTop: '1px solid var(--line)', margin: '24px 0'}} />

          <h3 style={{fontFamily: 'var(--serif)', marginBottom: '16px'}}>3. Accused / Perpetrator (Optional)</h3>
          <div style={{display: 'flex', gap: '15px', marginBottom: '10px'}}>
            <input type="text" placeholder="Name of Accused (or 'Unknown')" onChange={e => setFormData({...formData, accused_name: e.target.value})} style={{flex: 1}} />
            <input type="text" placeholder="Vehicle Details (e.g. 'Black motorcycle')" onChange={e => setFormData({...formData, accused_vehicle: e.target.value})} style={{flex: 1}} />
          </div>
          <textarea placeholder="Physical description of accused" onChange={e => setFormData({...formData, accused_description: e.target.value})} style={{minHeight: '80px', marginBottom: '10px'}} />

          <hr style={{border: 'none', borderTop: '1px solid var(--line)', margin: '24px 0'}} />

          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px'}}>
            <h3 style={{fontFamily: 'var(--serif)', margin: 0}}>4. Witnesses (Optional)</h3>
            <button type="button" className="btn btn-ghost" style={{padding: '6px 12px', fontSize: '12px'}} onClick={handleAddWitness}>+ Add Witness</button>
          </div>
          
          {formData.witnesses.map((witness, index) => (
            <div key={index} style={{display: 'flex', gap: '15px', alignItems: 'center'}}>
              <input type="text" placeholder="Witness Name" value={witness.name} onChange={e => handleWitnessChange(index, 'name', e.target.value)} />
              <input type="text" placeholder="Contact Number/Address" value={witness.contact} onChange={e => handleWitnessChange(index, 'contact', e.target.value)} />
              <button type="button" onClick={() => handleRemoveWitness(index)} style={{background: 'none', border: 'none', color: 'var(--seal)', cursor: 'pointer', fontSize: '18px', padding: '0 10px', marginBottom: '10px'}}>×</button>
            </div>
          ))}
          {formData.witnesses.length === 0 && <p style={{fontSize: '13px', color: 'var(--slate-light)', fontStyle: 'italic', marginBottom: '10px'}}>No witnesses added.</p>}

          <hr style={{border: 'none', borderTop: '1px solid var(--line)', margin: '24px 0'}} />
          
          <div className="input-foot" style={{justifyContent: 'flex-end'}}>
            <button type="submit" className="btn btn-primary" disabled={loading} style={{padding: '12px 24px', fontSize: '14px'}}>
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
