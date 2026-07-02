import { useState } from 'react'
import { Plus, X, ArrowRight, Save, User } from 'lucide-react'
import { useProfile } from '../context/ProfileContext'
import StepperBar from '../components/StepperBar'
import AgentPipeline from '../components/AgentPipeline'

export default function NewFIR() {
  const { profile } = useProfile()
  const [step, setStep] = useState(0)
  
  const [formData, setFormData] = useState({
    // Section A
    complainant_name: '',
    complainant_phone: '',
    complainant_gender: '',
    complainant_id_type: '',
    complainant_id_number: '',
    complainant_address: '',
    complainant_city: '',
    complainant_state: '',
    // Section B
    incident_date: '',
    incident_time: '',
    incident_location: '',
    incident_landmark: '',
    // Section C
    accused_name: '',
    accused_description: '',
    accused_vehicle: '',
    // Section D
    witnesses: [],
    // Section E
    complaint_text: ''
  })

  const [showAccused, setShowAccused] = useState(false)
  
  // Pipeline state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeAgent, setActiveAgent] = useState('intake') // intake -> legal -> drafting
  const [isComplete, setIsComplete] = useState(false)
  const [draftContent, setDraftContent] = useState('')

  const handleChange = (e) => setFormData({...formData, [e.target.name]: e.target.value})

  const addWitness = () => setFormData({...formData, witnesses: [...formData.witnesses, {name: '', phone: ''}]})
  const removeWitness = (index) => {
    const w = [...formData.witnesses]
    w.splice(index, 1)
    setFormData({...formData, witnesses: w})
  }
  const handleWitnessChange = (index, field, value) => {
    const w = [...formData.witnesses]
    w[index][field] = value
    setFormData({...formData, witnesses: w})
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    setStep(4)
    setActiveAgent('intake')
    setIsComplete(false)
    setDraftContent('')

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
      const decoder = new TextDecoder()
      
      let fullDraft = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim()
            if (!dataStr) continue
            
            try {
              const data = JSON.parse(dataStr)
              
              if (data.agent === 'System') {
                if (data.type === 'error') {
                  alert("Error: " + data.message)
                  setIsSubmitting(false)
                } else if (data.type === 'pipeline_complete') {
                  setIsComplete(true)
                  if (data.fir_record && data.fir_record.draft) {
                    setDraftContent(data.fir_record.draft)
                  }
                }
              } else if (data.agent === 'Intake Agent') {
                setActiveAgent('intake')
              } else if (data.agent === 'Legal Agent') {
                setActiveAgent('legal')
              } else if (data.agent === 'Drafting Agent') {
                setActiveAgent('drafting')
                if (data.type === 'thought' && data.message) {
                  setDraftContent(data.message)
                }
              }
              
            } catch (err) {
              console.error("Parse error", err)
            }
          }
        }
      }
    } catch (e) {
      console.error(e)
    }
  }

  if (isSubmitting) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ textAlign: 'right', marginBottom: '24px', fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
          <User size={14} />
          Filing Officer: {profile.officerName} · {profile.rank} · {profile.stationName}
        </div>
        <AgentPipeline activeAgent={activeAgent} isComplete={isComplete} draftContent={draftContent} />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', paddingBottom: '60px' }}>
      
      <StepperBar 
        steps={["Complainant", "Incident", "Parties", "Narrative"]} 
        currentStep={step} 
      />

      <form onSubmit={handleSubmit}>
        
        {/* Section A: Complainant Details */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '4px', height: '24px', background: 'var(--saffron)' }}></div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>Section A: Complainant Details</h2>
          </div>
          
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label>Full Name</label>
                <input type="text" name="complainant_name" value={formData.complainant_name} onChange={handleChange} required />
              </div>
              <div>
                <label>Phone Number</label>
                <input type="text" name="complainant_phone" value={formData.complainant_phone} onChange={handleChange} required />
              </div>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label>Gender</label>
                <select name="complainant_gender" value={formData.complainant_gender} onChange={handleChange}>
                  <option value="">Select...</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label>ID Proof Type</label>
                <select name="complainant_id_type" value={formData.complainant_id_type} onChange={handleChange}>
                  <option value="">Select...</option>
                  <option value="Aadhaar">Aadhaar</option>
                  <option value="Voter ID">Voter ID</option>
                  <option value="Driving License">Driving License</option>
                  <option value="Passport">Passport</option>
                </select>
              </div>
              <div>
                <label>ID Proof Number</label>
                <input type="text" name="complainant_id_number" value={formData.complainant_id_number} onChange={handleChange} />
              </div>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label>Residential Address</label>
              <textarea name="complainant_address" rows="2" value={formData.complainant_address} onChange={handleChange} required></textarea>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div>
                <label>City / District</label>
                <input type="text" name="complainant_city" value={formData.complainant_city} onChange={handleChange} required />
              </div>
              <div>
                <label>State</label>
                <input type="text" name="complainant_state" value={formData.complainant_state} onChange={handleChange} required />
              </div>
            </div>
          </div>
        </div>

        {/* Section B: Incident Details */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '4px', height: '24px', background: 'var(--saffron)' }}></div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>Section B: Incident Details</h2>
          </div>
          
          <div className="card" style={{ padding: '24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
              <div>
                <label>Date of Incident</label>
                <input type="date" name="incident_date" value={formData.incident_date} onChange={handleChange} required />
              </div>
              <div>
                <label>Time of Incident</label>
                <input type="time" name="incident_time" value={formData.incident_time} onChange={handleChange} />
              </div>
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label>Incident Location</label>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Enter the location where the incident occurred, not your home address.
              </div>
              <input type="text" name="incident_location" value={formData.incident_location} onChange={handleChange} required />
            </div>
            
            <div>
              <label>Landmark / Nearby Reference</label>
              <input type="text" name="incident_landmark" value={formData.incident_landmark} onChange={handleChange} />
            </div>
          </div>
        </div>

        {/* Section C: Accused / Perpetrator */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '4px', height: '24px', background: 'var(--saffron)' }}></div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>Section C: Accused / Perpetrator (Optional)</h2>
          </div>
          
          <div className="card" style={{ padding: '24px' }}>
            {!showAccused ? (
              <button type="button" className="btn btn-ghost" onClick={() => setShowAccused(true)}>
                <Plus size={16} /> Add Accused Details
              </button>
            ) : (
              <div>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '8px' }}>
                  <button type="button" className="btn btn-ghost" onClick={() => setShowAccused(false)} style={{ height: '32px', color: 'var(--danger)' }}>
                    <X size={14} /> Remove Accused
                  </button>
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label>Name or "Unknown"</label>
                  <input type="text" name="accused_name" value={formData.accused_name} onChange={handleChange} placeholder="e.g. Unknown male, approx 30 yrs" />
                </div>
                <div style={{ marginBottom: '20px' }}>
                  <label>Physical Description</label>
                  <textarea name="accused_description" rows="2" value={formData.accused_description} onChange={handleChange} placeholder="Height, build, clothing, distinguishing features..."></textarea>
                </div>
                <div>
                  <label>Vehicle Details (if any)</label>
                  <input type="text" name="accused_vehicle" value={formData.accused_vehicle} onChange={handleChange} placeholder="Make, model, color, license plate..." />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Section D: Witnesses */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '4px', height: '24px', background: 'var(--saffron)' }}></div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>Section D: Witnesses (Optional)</h2>
          </div>
          
          <div className="card" style={{ padding: '24px' }}>
            {formData.witnesses.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '14px', marginBottom: '16px' }}>
                No witnesses added.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
                {formData.witnesses.map((w, index) => (
                  <div key={index} style={{ display: 'flex', gap: '12px', alignItems: 'flex-end', background: '#FFF9F5', padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                    <div style={{ flex: 2 }}>
                      <label>Witness Name</label>
                      <input type="text" value={w.name} onChange={(e) => handleWitnessChange(index, 'name', e.target.value)} required />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label>Phone Number</label>
                      <input type="text" value={w.phone} onChange={(e) => handleWitnessChange(index, 'phone', e.target.value)} />
                    </div>
                    <button type="button" className="btn btn-ghost" onClick={() => removeWitness(index)} style={{ height: '44px', color: 'var(--danger)', padding: '0 12px' }}>
                      <X size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
            <button type="button" className="btn btn-ghost" onClick={addWitness}>
              <Plus size={16} /> Add Witness
            </button>
          </div>
        </div>

        {/* Section E: Narrative */}
        <div style={{ marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
            <div style={{ width: '4px', height: '24px', background: 'var(--saffron)' }}></div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>Section E: Complaint Narrative</h2>
          </div>
          
          <div className="card" style={{ padding: '24px' }}>
            <textarea 
              name="complaint_text" 
              value={formData.complaint_text} 
              onChange={handleChange}
              placeholder="Describe the incident in your own words. Include what happened, when, where, who was involved, and any other relevant details you remember."
              style={{ minHeight: '140px' }}
              required
            ></textarea>
            <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px', fontFamily: 'var(--mono)' }}>
              {formData.complaint_text.length} / 2000
            </div>
          </div>
        </div>

        {/* SUBMIT BUTTON ROW */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '16px', marginTop: '40px' }}>
          <button type="button" className="btn btn-ghost" style={{ padding: '0 24px' }}>
            <Save size={16} /> Save Draft
          </button>
          <button type="submit" className="btn btn-primary" style={{ height: '48px', fontSize: '15px', minWidth: '200px' }} onClick={() => setStep(3)}>
            Generate FIR Draft <ArrowRight size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}
