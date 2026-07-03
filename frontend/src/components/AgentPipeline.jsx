import { Loader2, CheckCircle2, FileText, Bot, Scale } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

export default function AgentPipeline({ activeAgent, isComplete, draftContent }) {
  // activeAgent: 'intake' | 'legal' | 'drafting'
  
  const agents = [
    { id: 'intake', name: 'Intake Agent', desc: 'Extracting structured facts...', icon: Bot, color: 'var(--india-blue)' },
    { id: 'legal', name: 'Legal Agent', desc: 'Querying ChromaDB · matches found', icon: Scale, color: 'var(--saffron)' },
    { id: 'drafting', name: 'Drafting Agent', desc: 'Composing FIR narrative...', icon: FileText, color: 'var(--green-ok)' }
  ]
  
  const activeIndex = agents.findIndex(a => a.id === activeAgent)

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '32px 0' }}>
      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <h2 style={{ fontFamily: 'var(--serif)', fontSize: '20px', margin: 0, color: 'var(--text-primary)' }}>
          {isComplete ? 'FIR Draft Generated Successfully' : 'Generating FIR Draft'}
        </h2>
      </div>

      <div className="card" style={{ padding: '32px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {agents.map((agent, i) => {
            const isDone = isComplete || i < activeIndex
            const isActive = !isComplete && i === activeIndex
            const isPending = !isComplete && i > activeIndex
            
            return (
              <div key={agent.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', opacity: isPending ? 0.4 : 1 }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: isActive ? 'var(--ash)' : (isDone ? agent.color : 'var(--ash)'),
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: isDone ? 'white' : agent.color,
                  border: `2px solid ${isDone ? 'transparent' : agent.color}`
                }}>
                  {isDone ? <CheckCircle2 size={20} /> : <agent.icon size={20} className={isActive ? 'spin' : ''} />}
                </div>
                <div>
                  <div style={{ fontFamily: 'var(--sans)', fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {agent.name}
                  </div>
                  <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                    {isDone ? 'Complete' : (isActive ? agent.desc : 'Waiting...')}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {draftContent && (
        <div className="card" style={{ background: '#FAFAF8', padding: '24px' }}>
          <div style={{ fontFamily: 'var(--sans)', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '16px' }}>
            Draft Preview
          </div>
          <div className="draft-preview">
            <ReactMarkdown>{draftContent}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
