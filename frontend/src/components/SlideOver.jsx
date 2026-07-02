import { X, Download } from 'lucide-react'

export default function SlideOver({ isOpen, onClose, title, subtitle, content }) {
  if (!isOpen) return null

  return (
    <>
      <div 
        className="fade-in"
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.3)',
          zIndex: 999
        }}
      ></div>
      <div 
        className="slide-in-right"
        style={{
          position: 'fixed',
          top: 0, right: 0, bottom: 0,
          width: '520px',
          maxWidth: '100vw',
          background: 'var(--surface)',
          zIndex: 1000,
          boxShadow: '-4px 0 24px rgba(0,0,0,0.1)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start'
        }}>
          <div>
            <div style={{fontFamily: 'var(--mono)', fontSize: '13px', color: 'var(--india-blue-mid)', marginBottom: '4px'}}>
              {title}
            </div>
            <h2 style={{fontFamily: 'var(--serif)', fontSize: '18px', color: 'var(--text-primary)', margin: 0}}>
              {subtitle}
            </h2>
          </div>
          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-muted)',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '24px',
          background: '#FAFAF8'
        }}>
          <div style={{
            fontFamily: 'var(--serif)',
            fontSize: '13px',
            lineHeight: 1.9,
            color: 'var(--text-primary)',
            whiteSpace: 'pre-wrap'
          }}>
            {content}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px',
          background: 'var(--surface)'
        }}>
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
          <button className="btn btn-primary" onClick={() => {}}>
            <Download size={16} />
            Download PDF
          </button>
        </div>
      </div>
    </>
  )
}
