export default function StatCard({ label, value, trendText, trendType, leftBorderColor }) {
  // trendType: 'positive' (green), 'warning' (orange), 'neutral' (blue)
  let trendClass = ''
  let trendColor = 'var(--text-muted)'
  
  if (trendType === 'positive') {
    trendColor = 'var(--green-ok)'
  } else if (trendType === 'warning') {
    trendColor = 'var(--warning)'
  }

  return (
    <div className="card" style={{
      padding: '20px',
      borderLeft: `3px solid ${leftBorderColor}`,
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{
        fontFamily: 'var(--sans)',
        fontSize: '11px',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        color: 'var(--text-muted)',
        marginBottom: '12px'
      }}>
        {label}
      </div>
      
      <div style={{
        fontFamily: 'var(--serif)',
        fontSize: '36px',
        fontWeight: 700,
        color: 'var(--text-primary)',
        lineHeight: 1,
        marginBottom: '12px'
      }}>
        {value}
      </div>
      
      {trendText && (
        <div style={{
          fontFamily: 'var(--sans)',
          fontSize: '12px',
          fontWeight: 500,
          color: trendColor
        }}>
          {trendText}
        </div>
      )}
    </div>
  )
}
