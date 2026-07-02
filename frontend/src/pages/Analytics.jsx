import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, CartesianGrid } from 'recharts'

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
    { name: 'Draft', value: data.status_breakdown.draft, color: 'var(--saffron)' },
    { name: 'In Review', value: data.status_breakdown.review, color: '#4F46E5' },
    { name: 'Filed', value: data.status_breakdown.filed, color: 'var(--green-ok)' },
    { name: 'Closed', value: data.status_breakdown.closed || 0, color: 'var(--text-muted)' }
  ].filter(d => d.value > 0)

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
      
      {/* Panel 1: FIRs Per Month (Full Width) */}
      <div className="card" style={{ padding: '24px', marginBottom: '24px', display: 'flex', flexDirection: 'column' }}>
        <h3 style={{ fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', marginBottom: '24px' }}>FIRs Per Month</h3>
        <div style={{ minHeight: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.firs_per_month} margin={{top: 10, right: 10, left: -20, bottom: 0}}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
              <XAxis dataKey="month" tick={{fontSize: 12, fill: 'var(--text-secondary)', fontFamily: 'var(--sans)'}} axisLine={false} tickLine={false} />
              <YAxis tick={{fontSize: 12, fill: 'var(--text-secondary)', fontFamily: 'var(--sans)'}} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip cursor={{fill: 'var(--india-blue-light)'}} contentStyle={{borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface)', boxShadow: '0 4px 12px rgba(0,0,0,0.05)', fontFamily: 'var(--sans)'}} />
              <Bar dataKey="count" fill="var(--saffron)" radius={[4, 4, 0, 0]} activeBar={{ fill: 'var(--saffron-dark)' }} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {/* Panel 2: Top Sections */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', marginBottom: '24px' }}>Top 5 Invoked Sections</h3>
          <div style={{ flex: 1, minHeight: '250px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart layout="vertical" data={data.top_sections} margin={{top: 10, right: 30, left: 10, bottom: 0}}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--border)" />
                <XAxis type="number" tick={{fontSize: 12, fill: 'var(--text-secondary)'}} axisLine={false} tickLine={false} allowDecimals={false} />
                <YAxis dataKey="section" type="category" tick={{fontSize: 11, fill: 'var(--text-secondary)', fontFamily: 'var(--mono)'}} axisLine={false} tickLine={false} width={80} />
                <Tooltip cursor={{fill: 'var(--india-blue-light)'}} contentStyle={{borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface)'}} formatter={(value, name, props) => [value, props.payload.label]} />
                <Bar dataKey="count" fill="var(--india-blue-mid)" radius={[0, 4, 4, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Panel 3: Status Breakdown */}
        <div className="card" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', marginBottom: '24px' }}>Status Breakdown</h3>
          <div style={{ flex: 1, minHeight: '250px', position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={80} stroke="none">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--surface)'}} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center Label */}
            <div style={{
              position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              pointerEvents: 'none'
            }}>
              <span style={{ fontFamily: 'var(--serif)', fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                {pieData.reduce((a, b) => a + b.value, 0)}
              </span>
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap', marginTop: '16px' }}>
            {pieData.map(d => (
              <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', background: d.color }}></span>
                {d.name}: {d.value}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Panel 4: Average Draft Time (Full Width Bottom) */}
      <div className="card" style={{ padding: '40px 24px', textAlign: 'center' }}>
        <h3 style={{ fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', marginBottom: '16px' }}>Pipeline Performance</h3>
        <div style={{ fontFamily: 'var(--serif)', fontSize: '48px', fontWeight: 700, color: 'var(--saffron)', lineHeight: 1, marginBottom: '8px' }}>
          {data.avg_draft_time_seconds}
        </div>
        <div style={{ fontFamily: 'var(--sans)', fontSize: '16px', color: 'var(--text-muted)' }}>
          seconds average
        </div>
        
        {/* Subtle Horizontal Timeline */}
        <div style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', 
          marginTop: '32px', maxWidth: '600px', margin: '32px auto 0' 
        }}>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--india-blue)', margin: '0 auto 8px' }}></div>
            <div style={{ fontSize: '12px', fontWeight: 600 }}>Intake</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>~20s</div>
          </div>
          <div style={{ height: '2px', background: 'var(--border)', flex: 1 }}></div>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--warning)', margin: '0 auto 8px' }}></div>
            <div style={{ fontSize: '12px', fontWeight: 600 }}>Legal Check</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>~15s</div>
          </div>
          <div style={{ height: '2px', background: 'var(--border)', flex: 1 }}></div>
          <div style={{ flex: 1, textAlign: 'center' }}>
            <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--green-ok)', margin: '0 auto 8px' }}></div>
            <div style={{ fontSize: '12px', fontWeight: 600 }}>Drafting</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>~107s</div>
          </div>
        </div>
      </div>
    </div>
  )
}
