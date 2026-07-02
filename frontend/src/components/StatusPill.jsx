export default function StatusPill({ status }) {
  const normStatus = (status || 'draft').toLowerCase()
  
  let type = 'draft'
  let label = 'Draft'
  
  if (normStatus.includes('review')) {
    type = 'review'
    label = 'In Review'
  } else if (normStatus.includes('file') || normStatus.includes('investigation') || normStatus.includes('finalized')) {
    type = 'filed'
    label = 'Filed'
  } else if (normStatus.includes('close')) {
    type = 'closed'
    label = 'Closed'
  }
  
  return (
    <span className={`status-pill ${type}`}>
      <span className="dot"></span>
      {label}
    </span>
  )
}
