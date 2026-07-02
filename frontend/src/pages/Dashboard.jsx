import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, Activity, Cpu, FileText, CheckCircle2 } from 'lucide-react'
import StatCard from '../components/StatCard'
import StatusPill from '../components/StatusPill'
import SectionChip from '../components/SectionChip'
import EmptyState from '../components/EmptyState'

export default function Dashboard() {
  const [firs, setFirs] = useState([])
  const [summary, setSummary] = useState({ open_this_month: 0, pending_review: 0, total_sections_indexed: 0 })
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetch('http://localhost:5000/api/firs').then(r => r.json()),
      fetch('http://localhost:5000/api/analytics').then(r => r.json())
    ])
    .then(([firData, analyticsData]) => {
      if (firData.firs) {
        setFirs(firData.firs)
        setSummary(firData.summary)
      }
      setAnalytics(analyticsData)
      setLoading(false)
    })
    .catch(err => {
      console.error(err)
      setLoading(false)
    })
  }, [])

  if (loading) return <div>Loading dashboard...</div>

  // Generate fake pipeline activity feed
  const feed = [
    { type: 'intake', agent: 'Intake Agent', action: 'extracted facts for FIR-0143', time: '10 mins ago', color: 'var(--india-blue)' },
    { type: 'legal', agent: 'Legal Agent', action: 'matched 3 sections for FIR-0143', time: '11 mins ago', color: 'var(--saffron)' },
    { type: 'drafting', agent: 'Drafting Agent', action: 'completed draft for FIR-0142', time: '1 hour ago', color: 'var(--green-ok)' },
    { type: 'intake', agent: 'Intake Agent', action: 'extracted facts for FIR-0142', time: '1 hour ago', color: 'var(--india-blue)' }
  ]

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}m ${s}s`
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* STAT ROW */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <StatCard 
          label="Open This Month" 
          value={summary.open_this_month} 
          trendText="from this station" 
          trendType="neutral" 
          leftBorderColor="var(--saffron)" 
        />
        <StatCard 
          label="Pending Review" 
          value={summary.pending_review} 
          trendText="needs action" 
          trendType="warning" 
          leftBorderColor="var(--warning)" 
        />
        <StatCard 
          label="Avg. Draft Time" 
          value={analytics ? formatTime(analytics.avg_draft_time_seconds) : '-'} 
          trendText="from intake to draft" 
          trendType="neutral" 
          leftBorderColor="var(--india-blue)" 
        />
        <StatCard 
          label="Sections Indexed" 
          value={summary.total_sections_indexed} 
          trendText="IPC & BNS" 
          trendType="positive" 
          leftBorderColor="var(--green-ok)" 
        />
      </div>

      {/* DOCKET TABLE */}
      <div className="card" style={{ marginBottom: '32px' }}>
        <div style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0 }}>Recent Case Docket</h3>
          <Link to="/history" style={{ color: 'var(--saffron)', fontSize: '14px', fontWeight: 600 }}>View All</Link>
        </div>
        
        {firs.length === 0 ? (
          <EmptyState 
            heading="No FIRs on record" 
            subtext="Cases will appear here once a complaint is drafted." 
            buttonLabel="+ Draft First FIR" 
            buttonHref="/new" 
          />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ background: 'var(--ash)', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.6px', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Case No.</th>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Complainant</th>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Sections</th>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Date Filed</th>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Status</th>
                  <th style={{ padding: '12px 24px', fontWeight: 600 }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {firs.slice(0, 5).map((fir, i) => {
                  const dateStr = fir.created_at ? new Date(fir.created_at).toLocaleDateString('en-IN') : '-'
                  return (
                    <tr key={i} style={{ borderBottom: '1px solid var(--border)', transition: 'background 150ms ease' }} onMouseOver={e => e.currentTarget.style.background = 'var(--india-blue-light)'} onMouseOut={e => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '16px 24px', fontFamily: 'var(--mono)', fontSize: '13px', color: 'var(--india-blue-mid)' }}>
                        {fir.fir_number}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fir.complainant_name || 'Unknown'}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{fir.incident_location || '-'}</div>
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {(fir.sections || []).slice(0, 2).map((sec, idx) => (
                            <SectionChip key={idx} act={sec.section.includes('BNS') ? 'BNS' : 'IPC'} sectionNumber={sec.section.replace(/IPC|BNS/i, '').trim()} />
                          ))}
                          {fir.sections?.length > 2 && <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>+{fir.sections.length - 2} more</span>}
                        </div>
                      </td>
                      <td style={{ padding: '16px 24px', fontFamily: 'var(--mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
                        {dateStr}
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <StatusPill status={fir.status} />
                      </td>
                      <td style={{ padding: '16px 24px' }}>
                        <button className="btn btn-ghost" style={{ padding: '4px 12px', height: '32px', fontSize: '12px' }}>
                          View <ArrowRight size={14} style={{ marginLeft: '4px' }} />
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

      {/* BOTTOM PANELS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '32px', alignItems: 'start' }}>
        
        {/* Most Invoked Sections */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ marginBottom: '24px' }}>Most Invoked Sections</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {analytics?.top_sections?.map((item, i) => {
              // Calculate width relative to the max count (let's say 50 for placeholder if missing)
              const max = Math.max(...(analytics.top_sections.map(s => s.count)), 10)
              const width = Math.max(5, (item.count / max) * 100)
              return (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '13px' }}>
                    <div style={{ color: 'var(--text-primary)' }}>
                      <span style={{ fontFamily: 'var(--mono)', color: 'var(--india-blue-mid)', marginRight: '8px' }}>{item.section}</span>
                      {item.label}
                    </div>
                    <div style={{ fontWeight: 600 }}>{item.count}</div>
                  </div>
                  <div style={{ background: '#F1F5F9', height: '8px', borderRadius: '4px', width: '100%' }}>
                    <div style={{ 
                      background: 'linear-gradient(90deg, var(--saffron), var(--saffron-dark))', 
                      height: '100%', 
                      borderRadius: '4px',
                      width: `${width}%`
                    }}></div>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Pipeline Activity */}
        <div className="card" style={{ padding: '24px' }}>
          <h3 style={{ marginBottom: '24px' }}>Pipeline Activity</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
            {feed.map((item, i) => (
              <div key={i} style={{ display: 'flex', gap: '16px', padding: '16px 0', borderBottom: i < feed.length - 1 ? '1px solid var(--border)' : 'none' }}>
                <div style={{ marginTop: '4px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: item.color }}></div>
                </div>
                <div>
                  <div style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.4 }}>
                    <span style={{ fontWeight: 600 }}>{item.agent}</span> {item.action}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    {item.time}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
