import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export default function Analytics() {
  const [data, setData] = useState({
    firs_per_month: [],
    top_sections: [],
    status_breakdown: { draft: 0, review: 0, filed: 0 },
    avg_draft_time_seconds: 0
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:5000/api/analytics')
      .then(res => res.json())
      .then(d => {
        setData(d)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="page-container"><p>Loading analytics...</p></div>

  const pieData = [
    { name: 'Draft', value: data.status_breakdown.draft, color: '#f59e0b' },
    { name: 'In Review', value: data.status_breakdown.review, color: '#3b82f6' },
    { name: 'Filed', value: data.status_breakdown.filed, color: '#10b981' }
  ].filter(d => d.value > 0)

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins} min ${secs} sec`
  }

  return (
    <div className="page-container" style={{maxWidth: '1000px', margin: '0 auto'}}>
      <div className="topbar" style={{marginBottom: '24px'}}>
        <div className="topbar-left">
          <h1 style={{fontFamily: 'var(--serif)', fontSize: '28px', margin: 0, color: 'var(--foreground)'}}>Analytics Dashboard</h1>
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px'}}>
        
        {/* Panel 1: FIRs Per Month */}
        <div className="panel" style={{padding: '20px', display: 'flex', flexDirection: 'column'}}>
          <h3 style={{fontFamily: 'var(--sans)', fontSize: '14px', textTransform: 'uppercase', color: 'var(--slate)', letterSpacing: '0.5px', marginBottom: '20px'}}>FIRs Per Month</h3>
          <div style={{flex: 1, minHeight: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.firs_per_month} margin={{top: 10, right: 10, left: -20, bottom: 0}}>
                <XAxis dataKey="month" tick={{fontSize: 12, fill: 'var(--slate)'}} axisLine={false} tickLine={false} />
                <YAxis tick={{fontSize: 12, fill: 'var(--slate)'}} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip cursor={{fill: 'var(--paper-dim)'}} contentStyle={{borderRadius: '8px', border: '1px solid var(--line)', background: 'var(--paper)', boxShadow: '0 4px 12px rgba(0,0,0,0.05)'}} />
                <Bar dataKey="count" fill="#A8362B" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 2: Average Draft Time */}
        <div className="panel" style={{padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
          <h3 style={{fontFamily: 'var(--sans)', fontSize: '14px', textTransform: 'uppercase', color: 'var(--slate)', letterSpacing: '0.5px', marginBottom: '24px'}}>Average Draft Time</h3>
          <div style={{fontSize: '42px', fontWeight: 'bold', color: 'var(--foreground)', fontFamily: 'var(--serif)'}}>
            {formatTime(data.avg_draft_time_seconds)}
          </div>
          <div style={{color: 'var(--slate)', fontSize: '14px', marginTop: '12px'}}>
            Average time from complaint to draft completion
          </div>
        </div>

        {/* Panel 3: Status Breakdown */}
        <div className="panel" style={{padding: '20px', display: 'flex', flexDirection: 'column'}}>
          <h3 style={{fontFamily: 'var(--sans)', fontSize: '14px', textTransform: 'uppercase', color: 'var(--slate)', letterSpacing: '0.5px', marginBottom: '20px'}}>Status Breakdown</h3>
          <div style={{flex: 1, minHeight: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} stroke="none">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{borderRadius: '8px', border: '1px solid var(--line)', background: 'var(--paper)'}} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap'}}>
            {pieData.map(d => (
              <div key={d.name} style={{display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--slate)'}}>
                <span style={{display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: d.color}}></span>
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>

        {/* Panel 4: Top Sections */}
        <div className="panel" style={{padding: '20px', display: 'flex', flexDirection: 'column'}}>
          <h3 style={{fontFamily: 'var(--sans)', fontSize: '14px', textTransform: 'uppercase', color: 'var(--slate)', letterSpacing: '0.5px', marginBottom: '20px'}}>Top 5 Invoked Sections</h3>
          <div style={{flex: 1, minHeight: '250px'}}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={data.top_sections} margin={{top: 10, right: 30, left: 10, bottom: 0}}>
                <XAxis type="number" tick={{fontSize: 12, fill: 'var(--slate)'}} axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis dataKey="section" type="category" tick={{fontSize: 12, fill: 'var(--slate)'}} axisLine={false} tickLine={false} width={80} />
                <Tooltip cursor={{fill: 'var(--paper-dim)'}} contentStyle={{borderRadius: '8px', border: '1px solid var(--line)', background: 'var(--paper)'}} formatter={(value, name, props) => [value, props.payload.label]} />
                <Bar dataKey="count" fill="#A8362B" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  )
}
