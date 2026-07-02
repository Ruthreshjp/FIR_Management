import { useState } from 'react'
import { useProfile } from '../context/ProfileContext'
import { ShieldCheck } from 'lucide-react'

export default function Profile() {
  const { profile, saveProfile } = useProfile()
  const [formData, setFormData] = useState(profile)
  const [saved, setSaved] = useState(false)

  const handleSubmit = (e) => {
    e.preventDefault()
    saveProfile(formData)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  return (
    <div className="page-container" style={{maxWidth: '600px', margin: '0 auto'}}>
      <div className="topbar" style={{marginBottom: '24px'}}>
        <div className="topbar-left">
          <h1 style={{fontFamily: 'var(--serif)', fontSize: '28px', margin: 0, color: 'var(--foreground)'}}>Officer Profile</h1>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="panel" style={{padding: '24px'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px', paddingBottom: '24px', borderBottom: '1px solid var(--line)'}}>
          <div style={{width: '64px', height: '64px', borderRadius: '50%', background: 'var(--paper-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
            <ShieldCheck size={32} color="var(--slate)" />
          </div>
          <div>
            <h2 style={{margin: 0, fontSize: '18px', fontWeight: '600'}}>{profile.officerName}</h2>
            <div style={{color: 'var(--slate)', fontSize: '14px'}}>{profile.rank} · {profile.stationName}</div>
          </div>
        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
          <div>
            <label style={{display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: '500', color: 'var(--slate)'}}>Full Name</label>
            <input type="text" value={formData.officerName} onChange={e => setFormData({...formData, officerName: e.target.value})} required style={{width: '100%', marginBottom: 0}} />
          </div>
          <div style={{display: 'flex', gap: '16px'}}>
            <div style={{flex: 1}}>
              <label style={{display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: '500', color: 'var(--slate)'}}>Rank</label>
              <input type="text" value={formData.rank} onChange={e => setFormData({...formData, rank: e.target.value})} required style={{width: '100%', marginBottom: 0}} />
            </div>
            <div style={{flex: 1}}>
              <label style={{display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: '500', color: 'var(--slate)'}}>Badge / ID Number</label>
              <input type="text" value={formData.badgeNumber} onChange={e => setFormData({...formData, badgeNumber: e.target.value})} required style={{width: '100%', marginBottom: 0}} />
            </div>
          </div>
          <div>
            <label style={{display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: '500', color: 'var(--slate)'}}>Station Name</label>
            <input type="text" value={formData.stationName} onChange={e => setFormData({...formData, stationName: e.target.value})} required style={{width: '100%', marginBottom: 0}} />
          </div>
          <div>
            <label style={{display: 'block', marginBottom: '8px', fontSize: '13px', fontWeight: '500', color: 'var(--slate)'}}>District</label>
            <input type="text" value={formData.district} onChange={e => setFormData({...formData, district: e.target.value})} required style={{width: '100%', marginBottom: 0}} />
          </div>
        </div>

        <div style={{marginTop: '32px', display: 'flex', alignItems: 'center', gap: '16px'}}>
          <button type="submit" className="btn btn-primary">Save Profile</button>
          {saved && <span style={{color: '#10b981', fontSize: '14px', fontWeight: '500'}}>Profile saved successfully!</span>}
        </div>
      </form>
    </div>
  )
}
