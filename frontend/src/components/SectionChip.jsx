export default function SectionChip({ act, sectionNumber }) {
  const isIPC = act === 'IPC'
  const bgColor = isIPC ? '#FFF3E8' : '#E8EEF8'
  const borderColor = isIPC ? '#FFBA80' : '#A0B4D6'
  const textColor = isIPC ? 'var(--saffron-dark)' : 'var(--india-blue)'
  
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      background: bgColor,
      border: `1px solid ${borderColor}`,
      color: textColor,
      fontFamily: 'var(--mono)',
      fontSize: '11px',
      fontWeight: 700,
      padding: '2px 8px',
      borderRadius: '4px',
      textTransform: 'uppercase'
    }}>
      {act} {sectionNumber}
    </span>
  )
}
