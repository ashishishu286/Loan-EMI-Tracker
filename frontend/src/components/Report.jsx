import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatINR } from '../utils';

export default function Report() {
  const [rows, setRows] = useState([]);
  const [error, setError] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    api
      .getMemberOutstandingReport()
      .then(setRows)
      .catch((err) => setError(err.message));
  }, []);

  const handleExport = async () => {
    setExporting(true);
    setError('');
    try {
      await api.downloadReportCsv();
    } catch (err) {
      setError(err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="card">
      <div className="header-row">
        <div>
          <h3 style={{ margin: 0 }}>Member-wise Outstanding Report</h3>
          <span className="muted">Total outstanding balance across all loans per member</span>
        </div>
        <button className="btn" onClick={handleExport} disabled={exporting}>
          {exporting ? 'Exporting...' : 'Export to CSV'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Member ID</th>
              <th>Member Name</th>
              <th className="num">Monthly Salary</th>
              <th className="num">Active / Total Loans</th>
              <th className="num">Total Principal</th>
              <th className="num">Total Outstanding</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan="6" className="muted">
                  No report data available.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.member_id}>
                  <td>{r.member_code}</td>
                  <td>{r.member_name}</td>
                  <td className="num">{formatINR(r.monthly_salary)}</td>
                  <td className="num">
                    {r.active_loans || 0} / {r.total_loans}
                  </td>
                  <td className="num">{formatINR(r.total_principal)}</td>
                  <td className="num">
                    <strong>{formatINR(r.total_outstanding)}</strong>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}