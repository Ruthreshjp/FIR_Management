import { useState, useEffect, useRef } from 'react'
import { Search, Loader2 } from 'lucide-react'

function ExpandableDescription({ text }) {
  const [expanded, setExpanded] = useState(false)
  if (!text) return null
  
  const isLong = text.length > 150
  const displayText = expanded ? text : text.substring(0, 150) + (isLong ? '...' : '')
  
  return (
    <div style={{fontSize: '13px', lineHeight: '1.6', color: 'var(--slate)', marginTop: '8px'}}>
      {displayText}
      {isLong && (
        <span 
          onClick={() => setExpanded(!expanded)}
          style={{color: 'var(--brand)', cursor: 'pointer', marginLeft: '8px', fontWeight: '500'}}
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

  const clearSearch = () => {
    setSearch('')
    setPage(1)
    fetchLaws(filter, 1, '')
  }

  const totalPages = Math.ceil(data.total / 25) || 1
  const hasSearch = search.trim().length > 0

  return (
    <div className="page-container" style={{maxWidth: '1000px', margin: '0 auto'}}>
      <div className="topbar" style={{marginBottom: '24px'}}>
        <div className="topbar-left">
          <h1 style={{fontFamily: 'var(--serif)', fontSize: '28px', margin: 0, color: 'var(--foreground)'}}>Legal Reference</h1>
        </div>
      </div>

      <div className="panel" style={{marginBottom: '24px', overflow: 'hidden'}}>
        <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: 'var(--paper)', borderBottom: '1px solid var(--line)'}}>
          
          <div style={{display: 'flex', gap: '8px'}}>
            <button 
              className={`btn ${filter === 'ALL' ? 'btn-primary' : 'btn-ghost'}`} 
              onClick={() => {setFilter('ALL'); setPage(1)}}
              style={{padding: '6px 12px', fontSize: '13px'}}
            >
              All ({data.counts.all})
            </button>
            <button 
              className={`btn ${filter === 'IPC' ? 'btn-primary' : 'btn-ghost'}`} 
              onClick={() => {setFilter('IPC'); setPage(1)}}
              style={{padding: '6px 12px', fontSize: '13px'}}
            >
              IPC ({data.counts.ipc})
            </button>
            <button 
              className={`btn ${filter === 'BNS' ? 'btn-primary' : 'btn-ghost'}`} 
              onClick={() => {setFilter('BNS'); setPage(1)}}
              style={{padding: '6px 12px', fontSize: '13px'}}
            >
              BNS ({data.counts.bns})
            </button>
          </div>

          <div style={{position: 'relative', width: '300px'}}>
            <input 
              type="text" 
              placeholder="Search sections, offenses..." 
              value={search}
              onChange={handleSearchChange}
              style={{paddingLeft: '36px', marginBottom: 0, width: '100%', height: '36px', borderRadius: '18px'}}
            />
            {isSearching ? (
              <Loader2 size={16} className="spin" style={{position: 'absolute', left: '12px', top: '10px', color: 'var(--slate)'}} />
            ) : (
              <Search size={16} style={{position: 'absolute', left: '12px', top: '10px', color: 'var(--slate)'}} />
            )}
          </div>
        </div>

        <div className="panel-body" style={{padding: '20px', background: 'var(--body)'}}>
          
          {hasSearch && (
            <div style={{marginBottom: '16px', fontSize: '14px', color: 'var(--slate)'}}>
              {data.results.length} results for "{search}"
            </div>
          )}

          {!loading && data.results.length === 0 ? (
            <div style={{textAlign: 'center', padding: '60px 20px'}}>
              <h3 style={{color: 'var(--slate)', marginBottom: '12px'}}>No sections matched your search</h3>
              {hasSearch && (
                <button className="btn btn-ghost" onClick={clearSearch}>Clear search</button>
              )}
            </div>
          ) : (
            <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
              {data.results.map((item, index) => (
                <div key={index} className="panel" style={{padding: '20px'}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px'}}>
                    <div>
                      <span className={`act-chip ${item.act === 'BNS' ? 'bns' : 'ipc'}`} style={{marginBottom: '8px', display: 'inline-block'}}>
                        {item.act}
                      </span>
                      <h2 style={{fontFamily: 'var(--serif)', fontSize: '22px', margin: '0 0 4px 0', color: 'var(--foreground)'}}>
                        {item.section_number}
                      </h2>
                      <div style={{fontWeight: '600', color: 'var(--foreground)', fontSize: '15px'}}>{item.section_name}</div>
                    </div>
                    {item.corresponding_section && item.corresponding_section !== 'N/A' && (
                      <div style={{fontSize: '12px', padding: '4px 8px', background: 'var(--paper-dim)', border: '1px solid var(--line)', borderRadius: '4px', color: 'var(--slate)'}}>
                        ↔ {item.act === 'IPC' ? 'BNS' : 'IPC'} {item.corresponding_section}
                      </div>
                    )}
                  </div>
                  
                  <ExpandableDescription text={item.description} />
                  
                  {(item.cognizable || item.bailable) && (
                    <div style={{display: 'flex', gap: '8px', marginTop: '16px'}}>
                      {item.cognizable && item.cognizable !== 'N/A' && (
                        <span style={{
                          fontSize: '11px', 
                          fontWeight: '600',
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          textTransform: 'uppercase',
                          background: item.cognizable.toLowerCase().includes('non') ? 'var(--paper-dim)' : '#e6f4ea',
                          color: item.cognizable.toLowerCase().includes('non') ? 'var(--slate)' : '#1e8e3e'
                        }}>
                          {item.cognizable}
                        </span>
                      )}
                      {item.bailable && item.bailable !== 'N/A' && (
                        <span style={{
                          fontSize: '11px', 
                          fontWeight: '600',
                          padding: '4px 8px', 
                          borderRadius: '4px', 
                          textTransform: 'uppercase',
                          background: 'var(--paper-dim)',
                          color: 'var(--slate)'
                        }}>
                          {item.bailable}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pagination (Hide during search) */}
        {!hasSearch && totalPages > 1 && (
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: 'var(--paper)', borderTop: '1px solid var(--line)'}}>
            <button 
              className="btn btn-ghost" 
              onClick={() => setPage(p => Math.max(1, p - 1))} 
              disabled={page === 1}
            >
              ← Previous
            </button>
            <div style={{fontSize: '14px', color: 'var(--slate)', display: 'flex', alignItems: 'center', gap: '8px'}}>
              Showing {(page - 1) * 25 + 1}–{Math.min(page * 25, data.total)} of {data.total}
              <span style={{margin: '0 8px', color: 'var(--line)'}}>|</span>
              Page 
              <input 
                type="number" 
                value={page}
                onChange={(e) => {
                  let p = parseInt(e.target.value)
                  if (!isNaN(p) && p >= 1 && p <= totalPages) {
                    setPage(p)
                  }
                }}
                style={{width: '60px', height: '28px', padding: '4px', margin: 0, textAlign: 'center'}}
                min={1}
                max={totalPages}
              />
              of {totalPages}
            </div>
            <button 
              className="btn btn-ghost" 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))} 
              disabled={page === totalPages}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
