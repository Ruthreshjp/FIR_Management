import { useState } from 'react'
import { useProfile } from '../context/ProfileContext'
import { Check, Plus, X } from 'lucide-react'

export default function Profile() {
  const { profile, saveProfile } = useProfile()
  const [officerData, setOfficerData] = useState({
    officerName: profile.officerName || '',
    rank: profile.rank || '',
    badgeNumber: profile.badgeNumber || '',
    phone: profile.phone || '',
    email: profile.email || ''
  })
  
  const [stationData, setStationData] = useState({
    stationName: profile.stationName || '',
    stationCode: profile.stationCode || '',
    district: profile.district || '',
    state: profile.state || '',
    address: profile.address || ''
  })
  
  const [roster, setRoster] = useState(profile.roster || [])
  
  const [toast, setToast] = useState(null)

  const showToast = (msg) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleSaveOfficer = (e) => {
    e.preventDefault()
    saveProfile({ ...profile, ...officerData })
    showToast('Officer details saved')
  }

  const handleSaveStation = (e) => {
    e.preventDefault()
    saveProfile({ ...profile, ...stationData })
    showToast('Station details saved')
  }
  
  const handleSaveRoster = () => {
    saveProfile({ ...profile, roster })
    showToast('Roster saved')
  }

  // Get Initials for Avatar
  const getInitials = (name) => {
    if (!name) return 'O'
    const parts = name.split(' ')
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return name.substring(0, 2).toUpperCase()
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '60px' }}>
      
      {toast && (
        <div className="fade-in" style={{
          position: 'fixed', bottom: '24px', right: '24px', 
          background: 'var(--surface)', padding: '16px 24px', 
          borderRadius: '8px', boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
          borderLeft: '4px solid var(--green-ok)', zIndex: 1000,
          display: 'flex', alignItems: 'center', gap: '12px',
          fontWeight: 600, color: 'var(--text-primary)'
        }}>
          <Check size={18} color="var(--green-ok)" />
          {toast}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '3fr 2fr', gap: '32px' }}>
        
        {/* LEFT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Card 1: Officer Details */}
          <form onSubmit={handleSaveOfficer} className="card" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px' }}>Officer Details</h3>
            
            <div style={{ display: 'flex', gap: '24px', marginBottom: '32px', alignItems: 'center' }}>
              <div style={{
                width: '60px', height: '60px', borderRadius: '50%', 
                background: 'var(--india-blue)', color: 'white',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontFamily: 'var(--serif)', fontSize: '24px'
              }}>
                {getInitials(officerData.officerName)}
              </div>
              <div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: '13px', color: 'var(--text-muted)' }}>Avatar is auto-generated</div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label>Full Name</label>
                <input type="text" value={officerData.officerName} onChange={e => setOfficerData({...officerData, officerName: e.target.value})} required />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label>Rank / Designation</label>
                  <input type="text" value={officerData.rank} onChange={e => setOfficerData({...officerData, rank: e.target.value})} required />
                </div>
                <div>
                  <label>Badge / ID Number</label>
                  <input type="text" value={officerData.badgeNumber} onChange={e => setOfficerData({...officerData, badgeNumber: e.target.value})} required />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label>Contact Number</label>
                  <input type="text" value={officerData.phone} onChange={e => setOfficerData({...officerData, phone: e.target.value})} />
                </div>
                <div>
                  <label>Email Address</label>
                  <input type="email" value={officerData.email} onChange={e => setOfficerData({...officerData, email: e.target.value})} />
                </div>
              </div>
            </div>
            
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '32px' }}>
              Save Officer Details
            </button>
          </form>

          {/* Card 2: Station Details */}
          <form onSubmit={handleSaveStation} className="card" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px' }}>Station Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
                <div>
                  <label>Station Name</label>
                  <input type="text" value={stationData.stationName} onChange={e => setStationData({...stationData, stationName: e.target.value})} required />
                </div>
                <div>
                  <label>Station Code</label>
                  <input type="text" value={stationData.stationCode} onChange={e => setStationData({...stationData, stationCode: e.target.value})} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label>District</label>
                  <input type="text" value={stationData.district} onChange={e => setStationData({...stationData, district: e.target.value})} required />
                </div>
                <div>
                  <label>State</label>
                  <input type="text" value={stationData.state} onChange={e => setStationData({...stationData, state: e.target.value})} required />
                </div>
              </div>
              <div>
                <label>Full Address</label>
                <textarea rows="3" value={stationData.address} onChange={e => setStationData({...stationData, address: e.target.value})}></textarea>
              </div>
            </div>
            
            <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '32px' }}>
              Save Station Details
            </button>
          </form>
        </div>

        {/* RIGHT COLUMN */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          
          {/* Card 3: Performance (Read Only) */}
          <div className="card" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px' }}>Performance</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Mini Stat Card */}
              <div style={{ padding: '16px', borderLeft: '3px solid var(--saffron)', background: '#FAFAF8', borderRadius: '4px' }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, marginBottom: '8px' }}>12</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>Cases Open</div>
              </div>
              <div style={{ padding: '16px', borderLeft: '3px solid var(--green-ok)', background: '#FAFAF8', borderRadius: '4px' }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, marginBottom: '8px' }}>148</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>Cases Filed</div>
              </div>
              <div style={{ padding: '16px', borderLeft: '3px solid var(--border)', background: '#FAFAF8', borderRadius: '4px' }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, marginBottom: '8px' }}>84</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>Cases Closed</div>
              </div>
              <div style={{ padding: '16px', borderLeft: '3px solid var(--india-blue)', background: '#FAFAF8', borderRadius: '4px' }}>
                <div style={{ fontFamily: 'var(--serif)', fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1, marginBottom: '8px' }}>244</div>
                <div style={{ fontFamily: 'var(--sans)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.5px', color: 'var(--text-muted)' }}>Total FIRs</div>
              </div>
            </div>
          </div>

          {/* Card 4: Personnel Roster */}
          <div className="card" style={{ padding: '32px' }}>
            <h3 style={{ marginBottom: '24px' }}>Personnel Roster</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
              {roster.map((person, i) => (
                <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  <input type="text" placeholder="Name" value={person.name} onChange={e => {
                    const r = [...roster]; r[i].name = e.target.value; setRoster(r)
                  }} style={{ flex: 2, height: '36px' }} />
                  <input type="text" placeholder="Rank" value={person.rank} onChange={e => {
                    const r = [...roster]; r[i].rank = e.target.value; setRoster(r)
                  }} style={{ flex: 1, height: '36px' }} />
                  <input type="text" placeholder="Badge No." value={person.badge} onChange={e => {
                    const r = [...roster]; r[i].badge = e.target.value; setRoster(r)
                  }} style={{ flex: 1, height: '36px' }} />
                  <button type="button" className="btn btn-ghost" onClick={() => {
                    const r = [...roster]; r.splice(i, 1); setRoster(r)
                  }} style={{ padding: '0 8px', color: 'var(--danger)' }}>
                    <X size={16} />
                  </button>
                </div>
              ))}
              {roster.length === 0 && (
                <div style={{ color: 'var(--text-muted)', fontSize: '14px', fontStyle: 'italic', marginBottom: '8px' }}>No personnel added to this station.</div>
              )}
              <button 
                type="button" 
                className="btn btn-ghost" 
                style={{ alignSelf: 'flex-start', padding: '0' }}
                onClick={() => setRoster([...roster, {name:'', rank:'', badge:''}])}
              >
                <Plus size={16} /> Add Personnel
              </button>
            </div>

            <button type="button" className="btn btn-primary" onClick={handleSaveRoster} style={{ width: '100%' }}>
              Save Roster
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}
