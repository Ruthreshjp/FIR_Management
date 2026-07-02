import { Check } from 'lucide-react'

export default function StepperBar({ steps, currentStep }) {
  // Steps: array of labels e.g. ["Details", "Incident", "Accused", "Witness"]
  const total = steps.length
  // Progress width
  const progressPercent = Math.min(100, Math.max(0, (currentStep / (total - 1)) * 100))
  
  return (
    <div style={{ padding: '32px 0', width: '100%', maxWidth: '700px', margin: '0 auto' }}>
      <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        
        {/* Background line */}
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '0',
          right: '0',
          height: '2px',
          background: 'var(--border)',
          zIndex: 1
        }}></div>

        {/* Active progress line */}
        <div style={{
          position: 'absolute',
          top: '16px',
          left: '0',
          height: '2px',
          background: 'var(--green-ok)',
          zIndex: 2,
          width: `${progressPercent}%`,
          transition: 'width 600ms ease'
        }}></div>

        {steps.map((label, index) => {
          const isCompleted = index < currentStep
          const isActive = index === currentStep
          const isPending = index > currentStep

          let bgColor = 'var(--ash)'
          let border = '2px solid var(--border)'
          let color = 'var(--text-muted)'
          
          if (isCompleted) {
            bgColor = 'var(--green-ok)'
            border = 'none'
            color = 'white'
          } else if (isActive) {
            bgColor = 'var(--saffron)'
            border = 'none'
            color = 'white'
          }

          return (
            <div key={index} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', zIndex: 3 }}>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                background: bgColor,
                border: border,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: color,
                fontFamily: 'var(--sans)',
                fontSize: '13px',
                fontWeight: 600,
                boxShadow: isActive ? '0 0 0 4px rgba(255,107,0,0.2)' : 'none',
                transition: 'all 300ms ease'
              }}>
                {isCompleted ? <Check size={16} strokeWidth={3} /> : (index + 1)}
              </div>
              <div style={{
                marginTop: '12px',
                fontFamily: 'var(--sans)',
                fontSize: '12px',
                fontWeight: 600,
                color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {label}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
