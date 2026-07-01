import { useState, useEffect } from 'react'

export default function CaseHistory() {
  const [firs, setFirs] = useState([])

  useEffect(() => {
    fetch('http://localhost:5000/api/firs')
      .then(res => res.json())
      .then(data => setFirs(data))
      .catch(console.error)
  }, [])

  const handleDownload = (fir_number) => {
    const encodedId = encodeURIComponent(fir_number.replace('/', '_'))
    window.open(`http://localhost:5000/api/firs/${encodedId}/pdf`, '_blank')
  }

  return (
    <div className="page-container">
      <h1 className="page-title">Case History</h1>
      <table className="history-table">
        <thead>
          <tr>
            <th>FIR Number</th>
            <th>Date</th>
            <th>Complainant</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {firs.map(fir => (
            <tr key={fir.fir_number}>
              <td>{fir.fir_number}</td>
              <td>{fir.created_at.substring(0, 10)}</td>
              <td>{fir.complainant_name}</td>
              <td><span className={`status-pill ${fir.status.toLowerCase()}`}>{fir.status}</span></td>
              <td>
                <button onClick={() => handleDownload(fir.fir_number)}>PDF</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
