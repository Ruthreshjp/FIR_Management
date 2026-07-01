import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FileText } from 'lucide-react'

export default function Dashboard() {
  const [firs, setFirs] = useState([])

  useEffect(() => {
    fetch('http://localhost:5000/api/firs')
      .then(res => res.json())
      .then(data => setFirs(data))
      .catch(console.error)
  }, [])

  return (
    <>
      <div className="topbar">
        <div className="topbar-left">
          <div className="eyebrow">28 JUN 2026 · STATION DESK 04</div>
          <h2>Dashboard</h2>
        </div>
        <div className="topbar-right">
          <button className="btn btn-ghost">Export Log</button>
          <Link to="/new" className="btn btn-primary">
            <FileText size={16} />
            New Complaint
          </Link>
        </div>
      </div>

      <div className="content">
        {/* STATS */}
        <div className="stat-row">
          <div className="stat">
            <div className="label">Open This Month</div>
            <div className="value">{firs.length} <span className="delta">+12%</span></div>
          </div>
          <div className="stat">
            <div className="label">Pending Review</div>
            <div className="value">{firs.filter(f => f.status === 'Draft').length} <span className="delta warn">needs action</span></div>
          </div>
          <div className="stat">
            <div className="label">Avg. Draft Time</div>
            <div className="value">2.4<span style={{fontSize: '15px', fontWeight: 500, color: 'var(--slate-light)'}}>min</span></div>
          </div>
          <div className="stat">
            <div className="label">Sections Indexed</div>
            <div className="value">800</div>
          </div>
        </div>

        {/* RECENT DOCKET */}
        <div className="section-head">
          <h3>Recent Case Docket</h3>
          <span className="see-all">View full history →</span>
        </div>
        <div className="docket">
          <div className="docket-row head">
            <span>Case No.</span>
            <span>Complainant / Summary</span>
            <span>Sections</span>
            <span>Filed</span>
            <span>Status</span>
            <span></span>
          </div>

          {firs.slice(0, 5).map(fir => (
            <Link to={`/history`} key={fir.fir_number} className="docket-row">
              <span className="case-no">{fir.fir_number}</span>
              <div className="case-info">
                <div className="title">{fir.complainant_name}</div>
                <div className="sub">{fir.police_station}, {fir.district}</div>
              </div>
              <div className="act-tags">
                <span className="tag bns">BNS</span>
                <span className="tag ipc">IPC</span>
              </div>
              <span className="timestamp">{fir.created_at?.substring(0, 10)}</span>
              <span className={`pill ${fir.status.toLowerCase().replace(' ', '.')}`}>{fir.status}</span>
              <span className="row-arrow">→</span>
            </Link>
          ))}
        </div>

        {/* TWO COLUMN */}
        <div className="grid-2">
          <div className="panel">
            <h4>Most Invoked Sections — Last 30 Days</h4>
            <div className="bar-row">
              <div className="bar-top"><span className="name">BNS 303 — Theft</span><span className="count">41</span></div>
              <div className="bar-track"><div className="bar-fill" style={{width: '88%'}}></div></div>
            </div>
            <div className="bar-row">
              <div className="bar-top"><span className="name">BNS 115 — Voluntarily causing hurt</span><span className="count">29</span></div>
              <div className="bar-track"><div className="bar-fill" style={{width: '63%'}}></div></div>
            </div>
            <div className="bar-row">
              <div className="bar-top"><span className="name">BNS 305 — Burglary</span><span className="count">22</span></div>
              <div className="bar-track"><div className="bar-fill" style={{width: '48%'}}></div></div>
            </div>
            <div className="bar-row">
              <div className="bar-top"><span className="name">IPC 354 — Assault on woman</span><span className="count">14</span></div>
              <div className="bar-track"><div className="bar-fill" style={{width: '30%'}}></div></div>
            </div>
            <div className="bar-row">
              <div className="bar-top"><span className="name">POCSO 12 — Sexual harassment of child</span><span className="count">8</span></div>
              <div className="bar-track"><div className="bar-fill" style={{width: '17%'}}></div></div>
            </div>
          </div>

          <div className="panel">
            <h4>Pipeline Activity</h4>
            <div className="feed-item">
              <div className="feed-dot"></div>
              <div>
                <div className="feed-text"><b>Legal Agent</b> matched FIR–0142 to BNS §303 and corresponding IPC §379</div>
                <div className="feed-time">12 min ago</div>
              </div>
            </div>
            <div className="feed-item">
              <div className="feed-dot"></div>
              <div>
                <div className="feed-text"><b>Drafting Agent</b> generated narrative for FIR–0141, awaiting officer review</div>
                <div className="feed-time">1 hr ago</div>
              </div>
            </div>
            <div className="feed-item">
              <div className="feed-dot"></div>
              <div>
                <div className="feed-text"><b>Intake Agent</b> flagged minor victim in FIR–0140 — routed to POCSO check</div>
                <div className="feed-time">Yesterday, 6:48 PM</div>
              </div>
            </div>
            <div className="feed-item">
              <div className="feed-dot"></div>
              <div>
                <div className="feed-text">PDF exported for <b>FIR–0139</b> by Desk Officer</div>
                <div className="feed-time">2 days ago</div>
              </div>
            </div>
          </div>
        </div>

        <div className="watermark">AutoFIR · Generated drafts require officer verification before filing</div>
      </div>
    </>
  )
}
