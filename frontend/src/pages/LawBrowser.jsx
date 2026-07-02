import { useState, useEffect, useRef } from 'react'
import { Search, Loader2 } from 'lucide-react'
import SectionChip from '../components/SectionChip'

function ExpandableDescription({ text }) {
  const [expanded, setExpanded] = useState(false)
  if (!text) return null
  
  return (
    <div>
      <div style={{
        fontFamily: 'var(--sans)',
        fontSize: '13px',
        lineHeight: 1.6,
        color: 'var(--text-secondary)',
        display: '-webkit-box',
        WebkitLineClamp: expanded ? 'unset' : 3,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden'
      }}>
        {text}
      </div>
      {text.length > 120 && (
        <span 
          onClick={() => setExpanded(!expanded)}
          style={{color: 'var(--saffron)', cursor: 'pointer', fontSize: '13px', fontWeight: '500', display: 'inline-block', marginTop: '4px'}}
        >
          {expanded ? 'Show less' : 'Show more'}
        </span>
      )}
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
  
  const searchTimeoutRef = useRef(null)

  const fetchLaws = async (currentFilter, currentPage, currentSearch) => {
    setLoading(true)
    try {
      const query = new URLSearchParams({
        act: currentFilter,
        page: currentPage,
        limit: 25,
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

  const totalPages = Math.ceil(data.total / 25) || 1
  const hasSearch = search.trim().length > 0

  const FilterPill = ({ label, act, count }) => {
    const active = filter === act
    return (
      <button 
        onClick={() => {setFilter(act); setPage(1)}}
        style={{
          height: '40px',
          minWidth: '100px',
          borderRadius: '20px',
          border: active ? '1px solid var(--india-blue)' : '1px solid var(--border)',
          background: active ? 'var(--india-blue)' : 'var(--surface)',
          color: active ? 'white' : 'var(--text-secondary)',
          fontFamily: 'var(--sans)',
          fontSize: '14px',
          fontWeight: 600,
          cursor: 'pointer',
          padding: '0 20px',
          transition: 'all 150ms ease'
        }}
      >
        {label} &nbsp;·&nbsp; {count}
      </button>
    )
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', paddingBottom: '40px' }}>
      
      {/* TOP FILTER ROW */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', gap: '12px' }}>
          <FilterPill label="All" act="ALL" count={data.counts.all} />
          <FilterPill label="IPC" act="IPC" count={data.counts.ipc} />
          <FilterPill label="BNS" act="BNS" count={data.counts.bns} />
        </div>
        
        <div style={{ position: 'relative', width: '320px' }}>
          <input 
            type="text" 
            placeholder="Search sections, offenses..." 
            value={search}
            onChange={handleSearchChange}
            style={{ paddingLeft: '40px', borderRadius: '20px', marginBottom: 0 }}
          />
          {isSearching ? (
            <Loader2 size={18} className="spin" style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
          ) : (
            <Search size={18} style={{ position: 'absolute', left: '14px', top: '13px', color: 'var(--text-muted)' }} />
          )}
        </div>
      </div>

      {hasSearch && (
        <div style={{ marginBottom: '24px', fontSize: '14px', color: 'var(--text-muted)' }}>
          {data.results.length} results for "{search}"
        </div>
      )}

      {/* SECTION CARDS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(500px, 1fr))', gap: '24px', marginBottom: '40px' }}>
        {data.results.map((item, index) => (
          <div key={index} className="card" style={{ padding: '24px' }}>
            
            {/* Top Row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
              <div>
                <SectionChip act={item.act} sectionNumber={item.section_number.replace(/IPC|BNS/i, '').trim()} />
                <div style={{ fontFamily: 'var(--serif)', fontSize: '20px', fontWeight: 700, color: 'var(--india-blue)', marginTop: '8px' }}>
                  § {item.section_number.replace(/IPC|BNS/i, '').trim()}
                </div>
              </div>
              {item.cognizable && item.cognizable !== 'N/A' && (
                <div style={{
                  background: item.cognizable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                  color: 'white',
                  padding: '4px 10px',
                  borderRadius: '20px',
                  fontSize: '11px',
                  fontFamily: 'var(--sans)',
                  fontWeight: 600,
                  textTransform: 'uppercase'
                }}>
                  {item.cognizable}
                </div>
              )}
            </div>
            
            {/* Middle */}
            <div style={{ fontFamily: 'var(--sans)', fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>
              {item.section_name}
            </div>
            
            <ExpandableDescription text={item.description} />
            
            {/* Bottom Row */}
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px', alignItems: 'center' }}>
              {item.bailable && item.bailable !== 'N/A' && (
                <div style={{
                  background: item.bailable.toLowerCase().includes('non') ? '#FEE2E2' : 'var(--green-light)',
                  color: item.bailable.toLowerCase().includes('non') ? 'var(--danger)' : 'var(--green-ok)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase'
                }}>
                  {item.bailable}
                </div>
              )}
              {item.corresponding_section && item.corresponding_section !== 'N/A' && (
                <div style={{
                  background: 'var(--india-blue-light)',
                  color: 'var(--india-blue-mid)',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '11px',
                  fontFamily: 'var(--mono)',
                  fontWeight: 500
                }}>
                  ↔ {item.act === 'IPC' ? 'BNS' : 'IPC'} {item.corresponding_section}
                </div>
              )}
            </div>

          </div>
        ))}
      </div>

      {/* PAGINATION */}
      {!hasSearch && totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px' }}>
          <button 
            className="btn btn-ghost" 
            onClick={() => setPage(p => Math.max(1, p - 1))} 
            disabled={page === 1}
          >
            Prev
          </button>
          
          <div style={{ fontFamily: 'var(--sans)', fontSize: '14px', color: 'var(--text-muted)', display: 'flex', gap: '8px' }}>
            {Array.from({length: Math.min(5, totalPages)}).map((_, i) => {
              // Simple pagination display logic
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
                    width: '32px', height: '32px', borderRadius: '4px', border: 'none',
                    background: p === page ? 'var(--saffron)' : 'transparent',
                    color: p === page ? 'white' : 'var(--text-secondary)',
                    fontWeight: p === page ? 600 : 400,
                    cursor: 'pointer'
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
    </div>
  )
}
