import { useState, useEffect, useRef } from 'react'
import { Plus, X, ArrowRight, Save, User, Mic, Keyboard, Camera, Download } from 'lucide-react'
import { useProfile } from '../context/ProfileContext'
import AgentPipeline from '../components/AgentPipeline'
import SpeechFormFiller from '../components/SpeechFormFiller'
import DraftEditor from '../components/DraftEditor'

const initialFormState = {
  complainant_name: '',
  complainant_father_name: '',
  complainant_occupation: '',
  complainant_email: '',
  complainant_phone: '',
  complainant_age: '',
  complainant_gender: '',
  complainant_id_type: '',
  complainant_id_number: '',
  complainant_address: '',
  incident_date: '',
  incident_time: '',
  incident_location: '',
  incident_station: '',
  incident_district: '',
  accused_list: [],
  witnesses_list: [],
  complaint_text: ''
}

export default function NewFIR() {
  const { profile } = useProfile()
  const [inputMode, setInputMode] = useState('speech') // 'speech' | 'manual'

  const [formData, setFormData] = useState(initialFormState)

  const [fillStatus, setFillStatus] = useState('idle')
  const [missingRequiredFields, setMissingRequiredFields] = useState([])

  // Pipeline state
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeAgent, setActiveAgent] = useState('intake')
  const [isComplete, setIsComplete] = useState(false)
  const [draftContent, setDraftContent] = useState('')
  const [verifierStats, setVerifierStats] = useState(null)
  const [firNumber, setFirNumber] = useState(null)
  const [firRecord, setFirRecord] = useState(null)

  useEffect(() => {
    resetForm()
  }, [])

  const resetForm = () => {
    setFormData(initialFormState)
    setIsSubmitting(false)
    setActiveAgent('intake')
    setIsComplete(false)
    setDraftContent('')
    setVerifierStats(null)
    setFirNumber(null)
    setFirRecord(null)
    setFillStatus('idle')
    setMissingRequiredFields([])
  }

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (value.trim() !== '') {
      setMissingRequiredFields(prev => {
        const updated = prev.filter(f => f !== name);
        if (updated.length === 0 && fillStatus === 'partial') {
          setFillStatus('success');
        }
        return updated;
      });
    }
  }

  const handleArrayChange = (arrayName, index, field, value) => {
    setFormData(prev => {
      const arr = [...prev[arrayName]];
      arr[index] = { ...arr[index], [field]: value };
      return { ...prev, [arrayName]: arr };
    });
  }

  const addArrayItem = (arrayName, emptyObj) => {
    setFormData(prev => ({
      ...prev,
      [arrayName]: [...prev[arrayName], emptyObj]
    }));
  }

  const removeArrayItem = (arrayName, index) => {
    setFormData(prev => {
      const arr = [...prev[arrayName]];
      arr.splice(index, 1);
      return { ...prev, [arrayName]: arr };
    });
  }

  const handleFieldsExtracted = (fields) => {
    setFormData(prev => {
      const updated = { ...prev };

      // Complainant fields
      if (fields.complainant?.name) updated.complainant_name = fields.complainant.name;
      if (fields.complainant?.email) updated.complainant_email = fields.complainant.email;
      if (fields.complainant?.phone) updated.complainant_phone = fields.complainant.phone;
      if (fields.complainant?.age) updated.complainant_age = fields.complainant.age;
      if (fields.complainant?.address) updated.complainant_address = fields.complainant.address;
      if (fields.complainant?.gender) updated.complainant_gender = fields.complainant.gender;
      if (fields.complainant?.id_type) updated.complainant_id_type = fields.complainant.id_type;
      if (fields.complainant?.id_number) updated.complainant_id_number = fields.complainant.id_number;

      if (fields.complainant?.father_name) updated.complainant_father_name = fields.complainant.father_name;
      if (fields.complainant?.occupation) updated.complainant_occupation = fields.complainant.occupation;

      // Incident fields
      if (fields.incident?.date) updated.incident_date = fields.incident.date;
      if (fields.incident?.time) updated.incident_time = fields.incident.time;
      if (fields.incident?.location) updated.incident_location = fields.incident.location;
      if (fields.incident?.station) updated.incident_station = fields.incident.station;
      if (fields.incident?.district) updated.incident_district = fields.incident.district;

      // Accused
      if (fields.accused_list && Array.isArray(fields.accused_list)) {
        updated.accused_list = fields.accused_list;
      }

      // Witnesses
      if (fields.witnesses_list && Array.isArray(fields.witnesses_list)) {
        updated.witnesses_list = fields.witnesses_list;
      }

      // Complaint narrative
      if (fields.complaint_narrative) updated.complaint_text = fields.complaint_narrative;

      const requiredFields = ['complainant_name', 'complainant_email', 'complaint_text'];
      const missing = requiredFields.filter(f => !updated[f] || updated[f].trim() === '');
      setMissingRequiredFields(missing);
      setFillStatus(missing.length > 0 ? 'partial' : 'success');

      return updated;
    });
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    const requiredFields = ['complainant_name', 'complainant_email', 'complaint_text'];
    const missing = requiredFields.filter(f => !formData[f] || formData[f].trim() === '');

    if (missing.length > 0) {
      setMissingRequiredFields(missing);
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setIsSubmitting(true)
    setActiveAgent('intake')
    setIsComplete(false)
    setDraftContent('')
    setVerifierStats(null)

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

      if (!response.ok) {
        const errorData = await response.json()
        alert(`Validation Error: ${errorData.error || 'Request failed'}`)
        setIsSubmitting(false)
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

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
                  if (data.fir_record) {
                    setFirRecord(data.fir_record)
                    if (data.fir_record.draft) setDraftContent(data.fir_record.draft)
                    if (data.fir_record.fir_number) setFirNumber(data.fir_record.fir_number)
                  }
                }
              } else if (data.agent === 'Intake Agent') {
                setActiveAgent('intake')
              } else if (data.agent === 'Legal Agent') {
                setActiveAgent('legal')
              } else if (data.agent === 'Verifier') {
                setActiveAgent('verifier')
                if (data.stage === 'verifier') {
                  setVerifierStats({ kept: data.kept, total: data.total })
                }
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

  const downloadPDF = () => {
    if (!firNumber) return;
    const safeFirNum = firNumber.replace(/\//g, '_');
    window.open(`http://localhost:5000/api/firs/${safeFirNum}/pdf`, '_blank');
  }

  if (isSubmitting) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div style={{ textAlign: 'right', marginBottom: '24px', fontSize: '13px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
          <User size={14} />
          Filing Officer: {profile.officerName} · {profile.rank} · {profile.stationName}
        </div>

        <AgentPipeline activeAgent={activeAgent} isComplete={isComplete} draftContent={draftContent} verifierStats={verifierStats} />

        {isComplete && firRecord && (
          <div style={{ marginTop: '40px', marginBottom: '60px' }}>
            <DraftEditor 
              initialRecord={firRecord} 
              onSave={(updatedRecord) => {
                setFirRecord(updatedRecord);
                alert("FIR updated successfully!");
              }}
              onDownload={() => downloadPDF()}
            />
            
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '32px' }}>
              <button className="btn btn-outline" onClick={resetForm} style={{ minWidth: '220px', height: '48px' }}>
                <Plus size={18} /> File Another FIR
              </button>
            </div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', paddingBottom: '60px' }}>

      {/* HEADER */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '32px', color: 'var(--india-blue)', marginBottom: '12px' }}>New FIR Registration</h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', margin: 0 }}>
          Speak your complaint or type it manually — AI will generate the FIR
        </p>
      </div>

      {/* INPUT METHOD SELECTOR */}
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '32px' }}>
        <div style={{ display: 'inline-flex', background: 'var(--border)', borderRadius: '10px', padding: '6px' }}>
          <button
            type="button"
            onClick={() => setInputMode('speech')}
            style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '12px 28px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              background: inputMode === 'speech' ? 'var(--surface)' : 'transparent',
              color: inputMode === 'speech' ? 'var(--india-blue)' : 'var(--text-muted)',
              fontWeight: inputMode === 'speech' ? 700 : 500,
              fontSize: '15px',
              boxShadow: inputMode === 'speech' ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.2s'
            }}
          >
            <Mic size={20} /> Speech Mode
          </button>
          <button
            type="button"
            onClick={() => setInputMode('manual')}
            style={{
              display: 'flex', alignItems: 'center', gap: '10px',
              padding: '12px 28px', borderRadius: '8px', border: 'none', cursor: 'pointer',
              background: inputMode === 'manual' ? 'var(--surface)' : 'transparent',
              color: inputMode === 'manual' ? 'var(--india-blue)' : 'var(--text-muted)',
              fontWeight: inputMode === 'manual' ? 700 : 500,
              fontSize: '15px',
              boxShadow: inputMode === 'manual' ? '0 2px 8px rgba(0,0,0,0.08)' : 'none',
              transition: 'all 0.2s'
            }}
          >
            <Keyboard size={20} /> Manual Mode
          </button>
        </div>
      </div>

      {/* SPEECH SECTION */}
      {inputMode === 'speech' && (
        <SpeechFormFiller
          onFieldsExtracted={handleFieldsExtracted}
          onSwitchToManual={() => setInputMode('manual')}
        />
      )}

      {/* STATUS BANNERS */}
      {fillStatus === 'success' && (
        <div style={{ padding: '14px 18px', background: '#F0FFF4', border: '1.5px solid #3D6B4F', borderRadius: '8px', marginBottom: '32px', color: '#3D6B4F', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
          ✅ Form auto-filled from speech successfully!
        </div>
      )}

      {fillStatus === 'partial' && (
        <div style={{ padding: '14px 18px', background: '#FFF9F5', border: '1.5px solid #E67E22', borderRadius: '8px', marginBottom: '32px', color: '#E67E22', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
          ⚠️ Form auto-filled from speech. Some details are missing. Please fill the required fields.
        </div>
      )}

      {/* MISSING FIELDS VALIDATION ERROR */}
      {missingRequiredFields.length > 0 && fillStatus === 'idle' && (
        <div style={{ padding: '14px 18px', background: '#FFF5F5', border: '1.5px solid var(--danger)', borderRadius: '8px', marginBottom: '32px', color: 'var(--danger)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '10px' }}>
          ❌ Some required details are missing. Please fill the highlighted fields.
        </div>
      )}

      {inputMode === 'manual' && (
        <form onSubmit={handleSubmit}>

          {/* Section A: Complainant Details */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '5px', height: '24px', background: 'var(--saffron)' }}></div>
              <h2 style={{ margin: 0, fontSize: '20px' }}>Section A: Complainant Details</h2>
            </div>

            <div className="card" style={{ padding: '28px' }}>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr 1fr', gap: '20px', marginBottom: '24px' }}>
                <div>
                  <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                    Full Name
                    {missingRequiredFields.includes('complainant_name') && <span style={{ color: 'var(--danger)', fontSize: '11px' }}>Required</span>}
                  </label>
                  <input type="text" name="complainant_name" value={formData.complainant_name} onChange={handleChange} style={missingRequiredFields.includes('complainant_name') ? { borderColor: 'var(--danger)', backgroundColor: '#FFF5F5' } : {}} />
                </div>
                <div>
                  <label>Father/Husband Name</label>
                  <input type="text" name="complainant_father_name" value={formData.complainant_father_name} onChange={handleChange} />
                </div>
                <div>
                  <label>Age</label>
                  <input type="number" name="complainant_age" value={formData.complainant_age} onChange={handleChange} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '20px', marginBottom: '24px' }}>
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
                  <label>Contact Number</label>
                  <input type="text" name="complainant_phone" value={formData.complainant_phone} onChange={handleChange} />
                </div>
                <div>
                  <label>Occupation</label>
                  <input type="text" name="complainant_occupation" value={formData.complainant_occupation} onChange={handleChange} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 2fr', gap: '20px', marginBottom: '24px' }}>
                <div>
                  <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                    Email Address
                    {missingRequiredFields.includes('complainant_email') && <span style={{ color: 'var(--danger)', fontSize: '11px' }}>Required</span>}
                  </label>
                  <input type="email" name="complainant_email" value={formData.complainant_email} onChange={handleChange} style={missingRequiredFields.includes('complainant_email') ? { borderColor: 'var(--danger)', backgroundColor: '#FFF5F5' } : {}} />
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ flex: 1 }}>
                    <label>ID Proof Type</label>
                    <select name="complainant_id_type" value={formData.complainant_id_type} onChange={handleChange}>
                      <option value="">Select...</option>
                      <option value="Aadhaar">Aadhaar</option>
                      <option value="Voter ID">Voter ID</option>
                      <option value="Driving License">Driving License</option>
                      <option value="Passport">Passport</option>
                    </select>
                  </div>
                  <div style={{ flex: 1.5 }}>
                    <label>ID Proof Number</label>
                    <input type="text" name="complainant_id_number" value={formData.complainant_id_number} onChange={handleChange} />
                  </div>
                </div>
              </div>

              <div>
                <label>Residential Address</label>
                <textarea name="complainant_address" rows="2" value={formData.complainant_address} onChange={handleChange}></textarea>
              </div>
            </div>
          </div>

          {/* Section B: Incident Details */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '5px', height: '24px', background: 'var(--saffron)' }}></div>
              <h2 style={{ margin: 0, fontSize: '20px' }}>Section B: Incident Details</h2>
            </div>

            <div className="card" style={{ padding: '28px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
                <div>
                  <label>Date of Incident</label>
                  <input type="date" name="incident_date" value={formData.incident_date} onChange={handleChange} />
                </div>
                <div>
                  <label>Time of Incident</label>
                  <input type="time" name="incident_time" value={formData.incident_time} onChange={handleChange} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '20px' }}>
                <div>
                  <label>Place of Occurrence / Location</label>
                  <input type="text" name="incident_location" value={formData.incident_location} onChange={handleChange} />
                </div>
                <div>
                  <label>Police Station</label>
                  <input type="text" name="incident_station" value={formData.incident_station} onChange={handleChange} />
                </div>
                <div>
                  <label>District</label>
                  <input type="text" name="incident_district" value={formData.incident_district} onChange={handleChange} />
                </div>
              </div>
            </div>
          </div>

          {/* Section C: Accused / Perpetrator */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '5px', height: '24px', background: 'var(--saffron)' }}></div>
              <h2 style={{ margin: 0, fontSize: '20px' }}>Section C: Accused / Perpetrator (Optional)</h2>
            </div>

            <div className="card" style={{ padding: '28px' }}>
              {formData.accused_list.map((accused, index) => (
                <div key={index} style={{ marginBottom: '24px', paddingBottom: '24px', borderBottom: index < formData.accused_list.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h4 style={{ margin: 0, color: 'var(--india-blue)' }}>Accused #{index + 1}</h4>
                    <button type="button" onClick={() => removeArrayItem('accused_list', index)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>
                      <X size={16} />
                    </button>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label>Name</label>
                      <input type="text" value={accused.name} onChange={(e) => handleArrayChange('accused_list', index, 'name', e.target.value)} />
                    </div>
                    <div>
                      <label>Age</label>
                      <input type="text" value={accused.age} onChange={(e) => handleArrayChange('accused_list', index, 'age', e.target.value)} />
                    </div>
                    <div>
                      <label>Gender</label>
                      <select value={accused.gender} onChange={(e) => handleArrayChange('accused_list', index, 'gender', e.target.value)}>
                        <option value="">Select...</option>
                        <option value="Male">Male</option>
                        <option value="Female">Female</option>
                        <option value="Other">Other</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '16px' }}>
                    <div>
                      <label>Relation to Complainant</label>
                      <input type="text" value={accused.relation} onChange={(e) => handleArrayChange('accused_list', index, 'relation', e.target.value)} />
                    </div>
                    <div>
                      <label>Address / Additional Info</label>
                      <input type="text" value={accused.address} onChange={(e) => handleArrayChange('accused_list', index, 'address', e.target.value)} />
                    </div>
                  </div>
                </div>
              ))}
              <button type="button" className="btn btn-outline" onClick={() => addArrayItem('accused_list', { name: '', age: '', gender: '', relation: '', address: '' })} style={{ marginTop: formData.accused_list.length > 0 ? '0' : '0' }}>
                <Plus size={16} /> Add Accused
              </button>
            </div>
          </div>

          {/* Section D: Witnesses */}
          <div style={{ marginBottom: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '5px', height: '24px', background: 'var(--saffron)' }}></div>
              <h2 style={{ margin: 0, fontSize: '20px' }}>Section D: Witnesses (Optional)</h2>
            </div>
            <div className="card" style={{ padding: '28px' }}>
              {formData.witnesses_list.map((witness, index) => (
                <div key={index} style={{ marginBottom: '24px', paddingBottom: '24px', borderBottom: index < formData.witnesses_list.length - 1 ? '1px solid var(--border)' : 'none' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <h4 style={{ margin: 0, color: 'var(--india-blue)' }}>Witness #{index + 1}</h4>
                    <button type="button" onClick={() => removeArrayItem('witnesses_list', index)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>
                      <X size={16} />
                    </button>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label>Name</label>
                      <input type="text" value={witness.name} onChange={(e) => handleArrayChange('witnesses_list', index, 'name', e.target.value)} />
                    </div>
                    <div>
                      <label>Phone</label>
                      <input type="text" value={witness.phone} onChange={(e) => handleArrayChange('witnesses_list', index, 'phone', e.target.value)} />
                    </div>
                  </div>
                  <div>
                    <label>Address</label>
                    <input type="text" value={witness.address} onChange={(e) => handleArrayChange('witnesses_list', index, 'address', e.target.value)} />
                  </div>
                </div>
              ))}
              <button type="button" className="btn btn-outline" onClick={() => addArrayItem('witnesses_list', { name: '', phone: '', address: '' })}>
                <Plus size={16} /> Add Witness
              </button>
            </div>
          </div>

          {/* Section E: Narrative */}
          <div style={{ marginBottom: '40px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <div style={{ width: '5px', height: '24px', background: 'var(--saffron)' }}></div>
              <h2 style={{ margin: 0, fontSize: '20px' }}>Section E: Detailed Complaint Description</h2>
            </div>

            <div className="card" style={{ padding: '28px' }}>

              <label style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                Complaint Narrative
                {missingRequiredFields.includes('complaint_text') && <span style={{ color: 'var(--danger)', fontSize: '11px' }}>Required</span>}
              </label>
              <textarea
                name="complaint_text"
                value={formData.complaint_text}
                onChange={handleChange}
                placeholder="Provide a detailed description of the incident..."
                style={{ minHeight: '180px', width: '100%', padding: '16px', borderRadius: '8px', border: missingRequiredFields.includes('complaint_text') ? '2px solid var(--danger)' : '1.5px solid var(--border)', backgroundColor: missingRequiredFields.includes('complaint_text') ? '#FFF5F5' : 'transparent', fontSize: '15px', lineHeight: '1.6' }}
              ></textarea>
              <div style={{ textAlign: 'right', fontSize: '12px', color: 'var(--text-muted)', marginTop: '10px', fontFamily: 'var(--mono)' }}>
                {formData.complaint_text.length} / 2000
              </div>
            </div>
          </div>

          {/* SUBMIT BUTTON */}
          <div style={{ display: 'flex', justifyContent: 'center', paddingBottom: '20px' }}>
            <button type="submit" className="btn btn-primary" style={{ height: '64px', fontSize: '18px', fontWeight: '700', minWidth: '320px', borderRadius: '12px', display: 'flex', gap: '12px', boxShadow: '0 8px 24px rgba(255, 107, 0, 0.3)' }}>
              🚀 Generate FIR <ArrowRight size={20} />
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
