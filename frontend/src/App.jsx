import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { Grid, PlusCircle, Archive, BarChart3, BookOpen, User } from 'lucide-react'

import Dashboard from './pages/Dashboard'
import NewFIR from './pages/NewFIR'
import CaseHistory from './pages/CaseHistory'
import Analytics from './pages/Analytics'
import LawBrowser from './pages/LawBrowser'
import Profile from './pages/Profile'
import { ProfileProvider } from './context/ProfileContext'

function Sidebar() {
  const location = useLocation()
  
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          {/* Ashoka Chakra inspired SVG */}
          <svg width="40" height="40" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style={{opacity: 0.4}}>
            <circle cx="50" cy="50" r="48" stroke="white" strokeWidth="2"/>
            <circle cx="50" cy="50" r="3" fill="white"/>
            {Array.from({length: 24}).map((_, i) => (
              <line key={i} x1="50" y1="50" x2="50" y2="2" stroke="white" strokeWidth="1" transform={`rotate(${i * 15} 50 50)`} />
            ))}
          </svg>
          <div className="brand-text">
            <h1>AutoFIR</h1>
            <span>e-FIR Drafting System</span>
          </div>
        </div>
      </div>

      <nav className="nav">
        <Link to="/" className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}>
          <Grid size={20} />
          Dashboard
        </Link>
        <Link to="/new" className={`nav-item ${location.pathname === '/new' ? 'active' : ''}`}>
          <PlusCircle size={20} />
          New FIR
        </Link>
        <Link to="/history" className={`nav-item ${location.pathname === '/history' ? 'active' : ''}`}>
          <Archive size={20} />
          Case History
        </Link>
        <Link to="/analytics" className={`nav-item ${location.pathname === '/analytics' ? 'active' : ''}`}>
          <BarChart3 size={20} />
          Analytics
        </Link>

        <div className="nav-label" style={{ borderTop: '1px solid rgba(255,255,255,0.1)', marginTop: '8px' }}>
          REFERENCE
        </div>
        <Link to="/laws" className={`nav-item ${location.pathname === '/laws' ? 'active' : ''}`}>
          <BookOpen size={20} />
          Law Browser
        </Link>
        <Link to="/profile" className={`nav-item ${location.pathname === '/profile' ? 'active' : ''}`}>
          <User size={20} />
          My Profile
        </Link>
      </nav>

      <div className="sidebar-foot">
        <div style={{display: 'flex', alignItems: 'center', marginBottom: '6px'}}>
          <span className="status-dot"></span>
          <span style={{fontFamily: 'var(--sans)', fontSize: '11px', color: 'rgba(255,255,255,0.5)'}}>System Online</span>
        </div>
        <div style={{fontFamily: 'var(--mono)', fontSize: '10px', color: 'rgba(255,255,255,0.35)'}}>
          Groq · gpt-oss-20b
        </div>
      </div>
    </aside>
  )
}

function Topbar() {
  const location = useLocation()
  
  const getPageTitle = (path) => {
    switch(path) {
      case '/': return 'Dashboard'
      case '/new': return 'New FIR Registration'
      case '/history': return 'Case History'
      case '/analytics': return 'Analytics'
      case '/laws': return 'Legal Reference'
      case '/profile': return 'Officer Profile'
      default: return 'AutoFIR'
    }
  }

  const title = getPageTitle(location.pathname)

  const [dateStr, setDateStr] = useState('')
  useEffect(() => {
    const updateTime = () => {
      const now = new Date()
      setDateStr(now.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }))
    }
    updateTime()
    const int = setInterval(updateTime, 60000)
    return () => clearInterval(int)
  }, [])

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="breadcrumb">AutoFIR / {title}</div>
        <h2>{title}</h2>
      </div>
      <div className="topbar-right">
        <span className="datetime">{dateStr}</span>
        <Link to="/new" className="btn btn-primary" style={{height: '36px', fontSize: '13px', padding: '0 16px'}}>
          New FIR
        </Link>
      </div>
    </header>
  )
}

function App() {
  return (
    <ProfileProvider>
      <Router>
        <div className="app">
          <Sidebar />
          <main className="main">
            <Topbar />
            <div className="page-content">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/new" element={<NewFIR />} />
                <Route path="/history" element={<CaseHistory />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/laws" element={<LawBrowser />} />
                <Route path="/profile" element={<Profile />} />
              </Routes>
            </div>
          </main>
        </div>
      </Router>
    </ProfileProvider>
  )
}

export default App
