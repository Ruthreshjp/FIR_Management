import { useState, useEffect } from 'react'
import { Save, Download, Trash2, Plus, AlertCircle } from 'lucide-react'

export default function DraftEditor({ initialRecord, onSave, onDownload }) {
  const [record, setRecord] = useState(initialRecord)
  const [draftJson, setDraftJson] = useState({ narrative: '', prayer: '', witnesses: '' })
  const [isSaving, setIsSaving] = useState(false)
  const [newBnsSection, setNewBnsSection] = useState('')
  const [newIpcSection, setNewIpcSection] = useState('')

  useEffect(() => {
    try {
      const parsed = JSON.parse(initialRecord.draft || '{}')
      setDraftJson({
        narrative: parsed.narrative || '',
        prayer: parsed.prayer || '',
        witnesses: parsed.witnesses || ''
      })
    } catch (e) {
      setDraftJson({ narrative: initialRecord.draft || '', prayer: '', witnesses: '' })
    }
  }, [initialRecord])

  const handleChange = (e) => {
    const { name, value } = e.target
    setRecord(prev => ({ ...prev, [name]: value }))
  }

  const handleDraftChange = (e) => {
    const { name, value } = e.target
    setDraftJson(prev => ({ ...prev, [name]: value }))
  }

  const removeSection = (type, index) => {
    const key = type === 'bns' ? 'bns_sections' : 'ipc_sections'
    setRecord(prev => ({
      ...prev,
      [key]: prev[key].filter((_, i) => i !== index)
    }))
  }

  const addSection = (type) => {
    const key = type === 'bns' ? 'bns_sections' : 'ipc_sections'
    const value = type === 'bns' ? newBnsSection : newIpcSection
    if (!value.trim()) return

    // parse basic input like "103 - Murder"
    const parts = value.split('-').map(s => s.trim())
    const newSec = {
      act: type.toUpperCase(),
      section_number: parts[0] || value,
      offense: parts[1] || 'Added Manually',
      justification: 'Added by officer during review',
      confidence: 1.0
    }

    setRecord(prev => ({
      ...prev,
      [key]: [...(prev[key] || []), newSec]
    }))

    if (type === 'bns') setNewBnsSection('')
    else setNewIpcSection('')
  }

  const handleSave = async () => {
    setIsSaving(true)
    const finalRecord = {
      ...record,
      draft: JSON.stringify(draftJson)
    }
    
    try {
      const safeFirNum = finalRecord.fir_number.replace(/\//g, '_')
      const response = await fetch(`http://localhost:5000/api/firs/${safeFirNum}/finalize`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalRecord)
      })
      if (!response.ok) throw new Error('Failed to save')
      if (onSave) onSave(finalRecord)
    } catch (err) {
      alert("Error saving FIR: " + err.message)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div style={{ padding: '0 20px' }}>
      {/* Warning Banner */}
      <div style={{ padding: '16px', background: '#FFF9F5', borderLeft: '4px solid #F59E0B', borderRadius: '4px', marginBottom: '24px', display: 'flex', gap: '12px' }}>
        <AlertCircle size={20} color="#F59E0B" />
        <div>
          <h4 style={{ margin: '0 0 4px 0', fontSize: '15px' }}>Draft Preview - Review Required</h4>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-secondary)' }}>
            Please carefully review and edit the sections below before finalizing. You can manually add or remove sections.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* COMPLAINANT CARD */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Complainant Details</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label>Name</label>
              <input type="text" name="complainant_name" value={record.complainant_name || ''} onChange={handleChange} />
            </div>
            <div>
              <label>Phone Number</label>
              <input type="text" name="complainant_phone" value={record.complainant_phone || ''} onChange={handleChange} />
            </div>
            <div>
              <label>Father/Husband Name</label>
              <input type="text" name="complainant_father_name" value={record.complainant_father_name || ''} onChange={handleChange} />
            </div>
            <div>
              <label>Occupation</label>
              <input type="text" name="complainant_occupation" value={record.complainant_occupation || ''} onChange={handleChange} />
            </div>
            <div style={{ gridColumn: 'span 2' }}>
              <label>Address</label>
              <input type="text" name="complainant_address" value={record.complainant_address || ''} onChange={handleChange} />
            </div>
          </div>
        </div>

        {/* INCIDENT CARD */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Incident Details</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label>Date & Time</label>
              <input type="text" value={`${record.incident_date || ''} ${record.incident_time || ''}`} disabled style={{ background: '#f5f5f5' }} />
            </div>
            <div>
              <label>Location</label>
              <input type="text" name="incident_location" value={record.incident_location || ''} onChange={handleChange} />
            </div>
          </div>
        </div>

        {/* ACCUSED LIST */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Accused Details</h3>
          {(record.accused_list || []).map((accused, index) => (
            <div key={index} style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px dashed var(--border)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                <div><label>Name</label><input type="text" value={accused.name || ''} onChange={(e) => {
                  const arr = [...record.accused_list]; arr[index].name = e.target.value; setRecord({...record, accused_list: arr});
                }} /></div>
                <div><label>Age/Gender</label><input type="text" value={`${accused.age || ''} ${accused.gender || ''}`} onChange={(e) => {
                  const arr = [...record.accused_list]; arr[index].age = e.target.value; setRecord({...record, accused_list: arr});
                }} /></div>
                <div><label>Relation</label><input type="text" value={accused.relation || ''} onChange={(e) => {
                  const arr = [...record.accused_list]; arr[index].relation = e.target.value; setRecord({...record, accused_list: arr});
                }} /></div>
              </div>
            </div>
          ))}
          <button type="button" className="btn btn-outline" onClick={() => setRecord({...record, accused_list: [...(record.accused_list || []), {}]})} style={{ height: '32px', padding: '0 12px' }}>
            <Plus size={14} /> Add Accused
          </button>
        </div>

        {/* WITNESSES LIST */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Witnesses</h3>
          {(record.witnesses_list || []).map((witness, index) => (
            <div key={index} style={{ marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px dashed var(--border)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 2fr', gap: '12px' }}>
                <div><label>Name</label><input type="text" value={witness.name || ''} onChange={(e) => {
                  const arr = [...record.witnesses_list]; arr[index].name = e.target.value; setRecord({...record, witnesses_list: arr});
                }} /></div>
                <div><label>Phone</label><input type="text" value={witness.phone || ''} onChange={(e) => {
                  const arr = [...record.witnesses_list]; arr[index].phone = e.target.value; setRecord({...record, witnesses_list: arr});
                }} /></div>
                <div><label>Address</label><input type="text" value={witness.address || ''} onChange={(e) => {
                  const arr = [...record.witnesses_list]; arr[index].address = e.target.value; setRecord({...record, witnesses_list: arr});
                }} /></div>
              </div>
            </div>
          ))}
          <button type="button" className="btn btn-outline" onClick={() => setRecord({...record, witnesses_list: [...(record.witnesses_list || []), {}]})} style={{ height: '32px', padding: '0 12px' }}>
            <Plus size={14} /> Add Witness
          </button>
        </div>

        {/* LEGAL SECTIONS */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Applicable Legal Sections</h3>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
            
            {/* BNS List */}
            <div>
              <h4 style={{ color: 'var(--india-blue)', fontSize: '14px', marginBottom: '12px' }}>BNS Sections</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {(record.bns_sections || []).map((sec, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFC', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>BNS {sec.section_number}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{sec.offense}</div>
                    </div>
                    <button type="button" onClick={() => removeSection('bns', i)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '4px' }}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="text" placeholder="e.g. 103 - Murder" value={newBnsSection} onChange={(e) => setNewBnsSection(e.target.value)} style={{ flex: 1, padding: '8px', fontSize: '13px' }} />
                <button type="button" onClick={() => addSection('bns')} className="btn btn-outline" style={{ height: '36px', padding: '0 12px' }}>
                  <Plus size={16} /> Add
                </button>
              </div>
            </div>

            {/* IPC List */}
            <div>
              <h4 style={{ color: 'var(--india-blue)', fontSize: '14px', marginBottom: '12px' }}>IPC Sections</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '12px' }}>
                {(record.ipc_sections || []).map((sec, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFC', padding: '10px', borderRadius: '6px', border: '1px solid var(--border)' }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '13px' }}>IPC {sec.section_number}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{sec.offense}</div>
                    </div>
                    <button type="button" onClick={() => removeSection('ipc', i)} style={{ background: 'none', border: 'none', color: 'var(--danger)', cursor: 'pointer', padding: '4px' }}>
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input type="text" placeholder="e.g. 302 - Murder" value={newIpcSection} onChange={(e) => setNewIpcSection(e.target.value)} style={{ flex: 1, padding: '8px', fontSize: '13px' }} />
                <button type="button" onClick={() => addSection('ipc')} className="btn btn-outline" style={{ height: '36px', padding: '0 12px' }}>
                  <Plus size={16} /> Add
                </button>
              </div>
            </div>
            
          </div>
        </div>

        {/* NARRATIVE & PRAYER */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '12px', marginBottom: '16px' }}>Narrative & Details</h3>
          
          <div style={{ marginBottom: '16px' }}>
            <label>Narrative of Events</label>
            <textarea name="narrative" value={draftJson.narrative} onChange={handleDraftChange} rows={6} style={{ width: '100%', padding: '12px' }} />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label>Action Requested / Prayer</label>
            <input type="text" name="prayer" value={draftJson.prayer} onChange={handleDraftChange} />
          </div>
        </div>
      </div>

      {/* ACTIONS */}
      <div style={{ display: 'flex', justifyContent: 'center', marginTop: '32px', gap: '16px' }}>
        <button onClick={handleSave} className="btn btn-primary" disabled={isSaving} style={{ minWidth: '220px', height: '48px' }}>
          <Save size={18} /> {isSaving ? 'Saving...' : 'Save & Update FIR'}
        </button>
        <button onClick={() => onDownload(record)} className="btn btn-outline" style={{ minWidth: '220px', height: '48px', color: 'var(--india-blue)', borderColor: 'var(--india-blue)' }}>
          <Download size={18} /> Download PDF
        </button>
      </div>

    </div>
  )
}
