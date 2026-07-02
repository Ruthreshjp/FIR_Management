import { Link } from 'react-router-dom'

export default function EmptyState({ icon: Icon, heading, subtext, buttonLabel, buttonHref }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 20px',
      textAlign: 'center'
    }}>
      <div style={{
        width: '64px',
        height: '64px',
        borderRadius: '50%',
        background: 'var(--ash)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: '16px'
      }}>
        {Icon ? <Icon size={32} color="var(--text-muted)" /> : (
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            <circle cx="12" cy="13" r="2"></circle>
            <path d="M12 15v2"></path>
          </svg>
        )}
      </div>
      <h3 style={{fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', marginBottom: '8px', fontWeight: 600}}>
        {heading}
      </h3>
      <p style={{fontFamily: 'var(--sans)', fontSize: '14px', color: 'var(--text-muted)', maxWidth: '300px', marginBottom: '24px'}}>
        {subtext}
      </p>
      {buttonLabel && buttonHref && (
        <Link to={buttonHref} className="btn btn-primary">
          {buttonLabel}
        </Link>
      )}
    </div>
  )
}
