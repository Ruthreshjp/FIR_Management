import { useState, useEffect } from 'react'
import { Search, Eye, Download } from 'lucide-react'
import StatusPill from '../components/StatusPill'
import SectionChip from '../components/SectionChip'
import SlideOver from '../components/SlideOver'
import EmptyState from '../components/EmptyState'

export default function CaseHistory() {
  const [firs, setFirs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('All')
  
  const [slideOpen, setSlideOpen] = useState(false)
  const [activeFir, setActiveFir] = useState(null)

  useEffect(() => {
    fetch('http://localhost:5000/api/firs')
      .then(r => r.json())
      .then(data => {
        setFirs(data.firs || data)
        setLoading(false)
      })
      .catch(console.error)
  }, [])

  const filteredFirs = firs.filter(f => {
    const s = search.toLowerCase()
    const matchesSearch = !search || 
      (f.fir_number || '').toLowerCase().includes(s) || 
      (f.complainant_name || '').toLowerCase().includes(s)
      
    const matchesStatus = statusFilter === 'All' || 
      (f.status || 'Draft').toLowerCase().includes(statusFilter.toLowerCase())
      
    return matchesSearch && matchesStatus
  })

  const handleView = (fir) => {
    setActiveFir(fir)
    setSlideOpen(true)
  }

  const handleDownload = (fir_num) => {
    const encoded = fir_num.replace(/\//g, '_')
    window.open(`http://localhost:5000/api/firs/${encoded}/pdf`, '_blank')
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* SEARCH & FILTER BAR */}
      <div className="card" style={{ padding: '16px 24px', marginBottom: '24px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '16px', top: '14px', color: 'var(--text-muted)' }} />
          <input 
            type="text" 
            placeholder="Search by name or case number..." 
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: '44px', marginBottom: 0 }}
          />
        </div>
        <div style={{ width: '200px' }}>
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ marginBottom: 0 }}>
            <option value="All">All Statuses</option>
            <option value="Draft">Draft</option>
            <option value="Review">In Review</option>
            <option value="Finalized">Filed</option>
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <input type="date" style={{ marginBottom: 0, width: '140px' }} />
          <span style={{ color: 'var(--text-muted)' }}>—</span>
          <input type="date" style={{ marginBottom: 0, width: '140px' }} />
        </div>
      </div>

      {/* TABLE */}
      <div className="card">
        {loading ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading records...</div>
        ) : filteredFirs.length === 0 ? (
          <EmptyState 
            heading="No records found" 
            subtext="Try adjusting your search or filters." 
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--ash)', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.6px', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Case No.</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Complainant</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Incident Type</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Sections</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Filed On</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '16px 24px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredFirs.map((fir, i) => {
                  const dateStr = fir.created_at ? new Date(fir.created_at).toLocaleDateString('en-IN') : '-'
                  const type = fir.sections?.[0]?.title || 'Unknown'
                  
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)', transition: 'background 150ms ease' }} onMouseOver={e => e.currentTarget.style.background = 'var(--india-blue-light)'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '16px 24px', fontFamily: 'var(--mono)', fontSize: '13px', color: 'var(--india-blue-mid)' }}>
                        {fir.fir_number}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fir.complainant_name || 'Unknown'}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{fir.incident_location || '-'}</div>
                      </td>
                      <td style={{ padding: '16px 24px', color: 'var(--text-secondary)' }}>
                        {type.length > 25 ? type.substring(0, 25) + '...' : type}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {(fir.sections || []).slice(0, 2).map((sec, idx) => (
                            <SectionChip key={idx} act={sec.section.includes('BNS') ? 'BNS' : 'IPC'} sectionNumber={sec.section.replace(/IPC|BNS/i, '').trim()} />
                          ))}
                        </div>
                      </td>
                      <td style={{ padding: '16px 24px', fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {dateStr}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <StatusPill status={fir.status} />
                      </td>
                      <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                        <button className="btn btn-ghost" onClick={() => handleView(fir)} style={{ padding: '8px', height: 'auto', minWidth: 'auto' }} title="View Details">
                          <Eye size={18} />
                        </button>
                        <button className="btn btn-ghost" onClick={() => handleDownload(fir.fir_number)} style={{ padding: '8px', height: 'auto', minWidth: 'auto' }} title="Download PDF">
                          <Download size={18} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <SlideOver 
        isOpen={slideOpen} 
        onClose={() => setSlideOpen(false)}
        title={activeFir?.fir_number}
        subtitle={`Complaint by ${activeFir?.complainant_name}`}
        content={activeFir?.draft || 'No draft generated yet.'}
      />
    </div>
  )
}
