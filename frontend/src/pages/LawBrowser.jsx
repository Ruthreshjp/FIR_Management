import { useState, useEffect, useRef } from 'react'
import { Search, Loader2, Copy, PlusCircle, ExternalLink, X, BookOpen, AlertCircle, Scale } from 'lucide-react'

// Utility to clean markdown, pipes, and extra spaces
const cleanText = (text) => {
  if (!text) return ''
  return text
    .replace(/[*#|]/g, '') // Remove basic markdown and pipes
    .replace(/\s+/g, ' ')   // Normalize spaces and newlines
    .trim()
}

// Truncate text for the short description
const truncateText = (text, maxLength = 120) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

function SectionModal({ item, onClose }) {
  if (!item) return null

  const handleCopy = () => {
    const copyText = `Act: ${item.act}\nSection: ${item.section_number}\nOffence: ${item.section_name}\nPunishment: ${item.punishment}\nDetails: ${cleanText(item.description)}`
    navigator.clipboard.writeText(copyText)
    alert('Section details copied to clipboard!')
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.6)',
      backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '24px'
    }} onClick={onClose}>
      <div 
        style={{
          background: 'var(--surface)',
          width: '100%', maxWidth: '700px',
          maxHeight: '90vh',
          borderRadius: '12px',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          overflowY: 'auto',
          position: 'relative'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ 
          padding: '24px', 
          borderBottom: '1px solid var(--border)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          background: '#f8fafc', borderTopLeftRadius: '12px', borderTopRightRadius: '12px'
        }}>
          <div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ 
                background: 'var(--india-blue)', color: 'white', 
                padding: '4px 12px', borderRadius: '4px', fontSize: '13px', fontWeight: 700 
              }}>
                {item.act}
              </span>
              <span style={{ fontFamily: 'var(--serif)', fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                Section {item.section_number.replace(/IPC|BNS/i, '').trim()}
              </span>
            </div>
            <h2 style={{ fontSize: '18px', color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0, fontWeight: 600 }}>
              {item.section_name}
            </h2>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}>
            <X size={24} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Status Pills */}
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            {item.cognizable && item.cognizable !== 'N/A' && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: item.cognizable.toLowerCase().includes('non') ? '#FFF5F5' : '#F0FFF4',
                color: item.cognizable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                border: `1px solid ${item.cognizable.toLowerCase().includes('non') ? '#FEB2B2' : '#9AE6B4'}`,
                padding: '6px 16px', borderRadius: '20px', fontSize: '13px', fontWeight: 600
              }}>
                <AlertCircle size={16} />
                {item.cognizable}
              </div>
            )}
            {item.bailable && item.bailable !== 'N/A' && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: item.bailable.toLowerCase().includes('non') ? '#FFF5F5' : '#F0FFF4',
                color: item.bailable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                border: `1px solid ${item.bailable.toLowerCase().includes('non') ? '#FEB2B2' : '#9AE6B4'}`,
                padding: '6px 16px', borderRadius: '20px', fontSize: '13px', fontWeight: 600
              }}>
                <Scale size={16} />
                {item.bailable}
              </div>
            )}
          </div>

          <div>
            <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.5px' }}>
              Description
            </h3>
            <p style={{ fontSize: '15px', color: 'var(--text-primary)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
              {cleanText(item.description)}
            </p>
          </div>

          {item.punishment && item.punishment !== 'N/A' && (
            <div style={{
              background: '#FFF9F5', borderLeft: '4px solid var(--saffron)',
              padding: '16px', borderRadius: '0 8px 8px 0'
            }}>
              <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--saffron-dark)', fontWeight: 700, marginBottom: '8px', letterSpacing: '0.5px' }}>
                Punishment
              </h3>
              <p style={{ fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500, margin: 0 }}>
                {cleanText(item.punishment)}
              </p>
            </div>
          )}

          {item.corresponding_section && item.corresponding_section !== 'N/A' && (
            <div style={{
              background: 'var(--india-blue-light)',
              padding: '16px', borderRadius: '8px',
              display: 'flex', alignItems: 'center', gap: '12px'
            }}>
              <BookOpen size={20} color="var(--india-blue-mid)" />
              <div>
                <div style={{ fontSize: '12px', color: 'var(--india-blue-mid)', fontWeight: 600, textTransform: 'uppercase' }}>Equivalent To</div>
                <div style={{ fontSize: '15px', color: 'var(--india-blue)', fontWeight: 700 }}>
                  {item.act === 'IPC' ? 'BNS' : 'IPC'} {item.corresponding_section}
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div style={{
          padding: '20px 24px', borderTop: '1px solid var(--border)',
          display: 'flex', justifyContent: 'flex-end', gap: '12px',
          background: '#f8fafc', borderBottomLeftRadius: '12px', borderBottomRightRadius: '12px'
        }}>
          <button 
            onClick={handleCopy}
            className="btn btn-secondary" 
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Copy size={16} /> Copy Details
          </button>
          <button 
            onClick={() => {
              alert('Section added to draft! (Mock functionality)')
              onClose()
            }}
            className="btn btn-primary" 
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <PlusCircle size={16} /> Add to FIR
          </button>
        </div>
      </div>
    </div>
  )
}

export default function LawBrowser() {
  const [data, setData] = useState({ results: [], total: 0, counts: { ipc: 0, bns: 0, all: 0 } })
  const [filter, setFilter] = useState('ALL')
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [isSearching, setIsSearching] = useState(false)
  const [selectedSection, setSelectedSection] = useState(null)
  
  const searchTimeoutRef = useRef(null)

  const fetchLaws = async (currentFilter, currentPage, currentSearch) => {
    setLoading(true)
    try {
      const query = new URLSearchParams({
        act: currentFilter,
        page: currentPage,
        limit: 24, // nice grid number
        search: currentSearch
      })
      const response = await fetch(`http://localhost:5000/api/laws?${query}`)
      const json = await response.json()
      setData(json)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
    setIsSearching(false)
  }

  useEffect(() => {
    fetchLaws(filter, page, search)
    // eslint-disable-next-line
  }, [filter, page])

  const handleSearchChange = (e) => {
    const val = e.target.value
    setSearch(val)
    setIsSearching(true)
    
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current)
    }
    
    searchTimeoutRef.current = setTimeout(() => {
      setPage(1)
      fetchLaws(filter, 1, val)
    }, 400)
  }

  const totalPages = Math.ceil(data.total / 24) || 1
  const hasSearch = search.trim().length > 0

  const FILTERS = [
    { id: 'ALL', label: 'All Acts' },
    { id: 'BNS', label: 'BNS (New)' },
    { id: 'IPC', label: 'IPC (Old)' },
    { id: 'IT', label: 'IT Act' },
    { id: 'OTHER', label: 'Others' }
  ]

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '60px' }}>
      
      {/* Header Area */}
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h1 style={{ fontFamily: 'var(--serif)', fontSize: '32px', color: 'var(--text-primary)', marginBottom: '12px' }}>
          Legal Reference Browser
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '16px', maxWidth: '600px', margin: '0 auto' }}>
          Search and browse through the Bharatiya Nyaya Sanhita (BNS), Indian Penal Code (IPC), and other relevant legal frameworks.
        </p>
      </div>

      {/* Control Bar: Search and Filters */}
      <div style={{ 
        background: 'var(--surface)', padding: '20px', borderRadius: '12px', 
        boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border)',
        marginBottom: '32px', display: 'flex', flexDirection: 'column', gap: '20px'
      }}>
        {/* Search */}
        <div style={{ position: 'relative', width: '100%', maxWidth: '600px', margin: '0 auto' }}>
          <input 
            type="text" 
            placeholder="Search by section number, offence name, or keywords..." 
            value={search}
            onChange={handleSearchChange}
            style={{ 
              width: '100%', padding: '14px 20px 14px 48px', 
              borderRadius: '30px', border: '2px solid var(--india-blue-light)',
              fontSize: '16px', outline: 'none', transition: 'border-color 0.2s',
              background: '#f8fafc', fontFamily: 'var(--sans)'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--india-blue)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--india-blue-light)'}
          />
          {isSearching ? (
            <Loader2 size={20} className="spin" style={{ position: 'absolute', left: '18px', top: '16px', color: 'var(--india-blue)' }} />
          ) : (
            <Search size={20} style={{ position: 'absolute', left: '18px', top: '16px', color: 'var(--text-muted)' }} />
          )}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {FILTERS.map(f => {
            const isActive = filter === f.id
            const count = (f.id === 'IPC' || f.id === 'BNS' || f.id === 'ALL') ? data.counts[f.id.toLowerCase()] : 0
            
            return (
              <button 
                key={f.id}
                onClick={() => { setFilter(f.id); setPage(1); }}
                style={{
                  padding: '8px 20px',
                  borderRadius: '20px',
                  border: isActive ? '1px solid var(--india-blue)' : '1px solid var(--border)',
                  background: isActive ? 'var(--india-blue)' : 'var(--surface)',
                  color: isActive ? 'white' : 'var(--text-secondary)',
                  fontFamily: 'var(--sans)',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  display: 'flex', alignItems: 'center', gap: '6px'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'var(--background)'
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = 'var(--surface)'
                }}
              >
                {f.label}
                {(count > 0 || isActive) && (
                  <span style={{ 
                    background: isActive ? 'rgba(255,255,255,0.2)' : 'var(--border)', 
                    padding: '2px 8px', borderRadius: '12px', fontSize: '11px', marginLeft: '4px' 
                  }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      </div>

      {/* Results Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div style={{ fontSize: '15px', color: 'var(--text-secondary)', fontWeight: 500 }}>
          {loading ? 'Loading...' : (
            <>Showing <strong>{data.results.length}</strong> of <strong>{data.total}</strong> results {hasSearch && `for "${search}"`}</>
          )}
        </div>
      </div>

      {/* CARDS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        {data.results.map((item, index) => (
          <div 
            key={index} 
            className="card" 
            onClick={() => setSelectedSection(item)}
            style={{ 
              padding: '0', 
              transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s', 
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',
              border: '1px solid var(--border)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-4px)'
              e.currentTarget.style.boxShadow = '0 12px 24px rgba(0,0,0,0.08)'
              e.currentTarget.style.borderColor = 'var(--india-blue-light)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
              e.currentTarget.style.borderColor = 'var(--border)'
            }}
          >
            {/* Card Header */}
            <div style={{ 
              background: '#f8fafc', padding: '16px 20px', borderBottom: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span style={{ 
                  background: item.act === 'IPC' ? 'var(--text-muted)' : 'var(--india-blue)', 
                  color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 700 
                }}>
                  {item.act}
                </span>
                <span style={{ fontFamily: 'var(--serif)', fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  § {item.section_number.replace(/IPC|BNS/i, '').trim()}
                </span>
              </div>
              <ExternalLink size={16} color="var(--text-muted)" />
            </div>

            {/* Card Body */}
            <div style={{ padding: '20px', flex: 1, display: 'flex', flexDirection: 'column' }}>
              
              <h3 style={{ 
                fontFamily: 'var(--sans)', fontSize: '15px', fontWeight: 600, 
                color: 'var(--text-primary)', marginBottom: '12px', lineHeight: 1.4,
                display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden'
              }}>
                {cleanText(item.section_name)}
              </h3>
              
              <p style={{ 
                fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5, 
                marginBottom: '16px', flex: 1
              }}>
                {truncateText(cleanText(item.description), 140)}
              </p>

              {/* Badges */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: 'auto' }}>
                {item.cognizable && item.cognizable !== 'N/A' && (
                  <span style={{
                    background: item.cognizable.toLowerCase().includes('non') ? '#FFF5F5' : '#F0FFF4',
                    color: item.cognizable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                    padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, border: `1px solid ${item.cognizable.toLowerCase().includes('non') ? '#FEB2B2' : '#9AE6B4'}`
                  }}>
                    {item.cognizable}
                  </span>
                )}
                {item.bailable && item.bailable !== 'N/A' && (
                  <span style={{
                    background: item.bailable.toLowerCase().includes('non') ? '#FFF5F5' : '#F0FFF4',
                    color: item.bailable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                    padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600, border: `1px solid ${item.bailable.toLowerCase().includes('non') ? '#FEB2B2' : '#9AE6B4'}`
                  }}>
                    {item.bailable}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* No Results Empty State */}
      {!loading && data.results.length === 0 && (
        <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--border)' }}>
          <BookOpen size={48} color="var(--border)" style={{ margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: '18px', color: 'var(--text-primary)', marginBottom: '8px' }}>No sections found</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
            Try adjusting your search terms or filters to find what you're looking for.
          </p>
        </div>
      )}

      {/* PAGINATION */}
      {!hasSearch && totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px' }}>
          <button 
            className="btn btn-ghost" 
            onClick={() => setPage(p => Math.max(1, p - 1))} 
            disabled={page === 1}
          >
            Previous
          </button>
          
          <div style={{ fontFamily: 'var(--sans)', fontSize: '14px', color: 'var(--text-muted)', display: 'flex', gap: '4px' }}>
            {Array.from({length: Math.min(5, totalPages)}).map((_, i) => {
              let p = page
              if (page <= 3) p = i + 1
              else if (page >= totalPages - 2) p = totalPages - 4 + i
              else p = page - 2 + i
              
              if (p < 1 || p > totalPages) return null

              return (
                <button 
                  key={p}
                  onClick={() => setPage(p)}
                  style={{
                    width: '36px', height: '36px', borderRadius: '18px', border: 'none',
                    background: p === page ? 'var(--india-blue)' : 'transparent',
                    color: p === page ? 'white' : 'var(--text-secondary)',
                    fontWeight: p === page ? 600 : 500,
                    cursor: 'pointer', transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (p !== page) e.currentTarget.style.background = 'var(--background)'
                  }}
                  onMouseLeave={(e) => {
                    if (p !== page) e.currentTarget.style.background = 'transparent'
                  }}
                >
                  {p}
                </button>
              )
            })}
          </div>

          <button 
            className="btn btn-ghost" 
            onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
            disabled={page === totalPages}
          >
            Next
          </button>
        </div>
      )}

      {/* Modal for detailed view */}
      {selectedSection && (
        <SectionModal item={selectedSection} onClose={() => setSelectedSection(null)} />
      )}
    </div>
  )
}
