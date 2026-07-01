import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom'
import { FileText, LayoutDashboard, History, BarChart3, Scale, ShieldCheck, CheckCircle2 } from 'lucide-react'

import Dashboard from './pages/Dashboard'
import NewFIR from './pages/NewFIR'
import CaseHistory from './pages/CaseHistory'
import Analytics from './pages/Analytics'

function Sidebar() {
  const location = useLocation()
  
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <div className="brand-seal">FIR</div>
          <div className="brand-text">
            <h1>AutoFIR</h1>
            <span>Case Drafting System</span>
          </div>
        </div>
      </div>

      <nav className="nav">
        <div className="nav-label">Workspace</div>
        <Link to="/" className={`nav-item ${location.pathname === '/' ? 'active' : ''}`}>
          <LayoutDashboard size={17} />
          Dashboard
        </Link>
        <Link to="/new" className={`nav-item ${location.pathname === '/new' ? 'active' : ''}`}>
          <FileText size={17} />
          New Complaint
        </Link>
        <Link to="/history" className={`nav-item ${location.pathname === '/history' ? 'active' : ''}`}>
          <History size={17} />
          Case History
          <span className="nav-badge">128</span>
        </Link>
        <Link to="/analytics" className={`nav-item ${location.pathname === '/analytics' ? 'active' : ''}`}>
          <BarChart3 size={17} />
          Analytics
        </Link>

        <div className="nav-label">Legal Reference</div>
        <Link to="/reference" className={`nav-item ${location.pathname === '/reference' ? 'active' : ''}`}>
          <Scale size={17} />
          IPC & BNS Browser
        </Link>
        <Link to="/pocso" className={`nav-item ${location.pathname === '/pocso' ? 'active' : ''}`}>
          <ShieldCheck size={17} />
          POCSO Reference
        </Link>
      </nav>

      <div className="sidebar-foot">
        <div><span className="status-dot"></span>Groq · Llama3-8b connected</div>
        <div style={{marginTop: '4px'}}>MongoDB Atlas · synced</div>
      </div>
    </aside>
  )
}

function App() {
  return (
    <Router>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/new" element={<NewFIR />} />
            <Route path="/history" element={<CaseHistory />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
