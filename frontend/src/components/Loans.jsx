import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatINR } from '../utils';

export default function Loans({ onSelectLoan }) {
  const [loans, setLoans] = useState([]);
  const [members, setMembers] = useState([]);
  const [memberId, setMemberId] = useState('');
  const [principal, setPrincipal] = useState('');
  const [tenureMonths, setTenureMonths] = useState('12');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const [loanData, memberData] = await Promise.all([
        api.getLoans(),
        api.getMembers(),
      ]);
      setLoans(loanData);
      setMembers(memberData);
      if (!memberId && memberData.length > 0) {
        setMemberId(String(memberData[0].id));
      }
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    const p = Number(principal);
    const t = Number(tenureMonths);

    if (!memberId || p <= 0 || t < 1 || t > 360) {
      setError('Select a member, enter a positive principal, and tenure (1–360 months).');
      return;
    }

    setSubmitting(true);
    try {
      const created = await api.createLoan({
        member_id: Number(memberId),
        principal: Math.round(p),
        tenure_months: Math.round(t),
      });
      setPrincipal('');
      await loadData();
      onSelectLoan(created.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const visibleLoans = loans.filter((l) =>
    statusFilter === 'ALL' ? true : l.status === statusFilter
  );

  return (
    <div>
      <div className="card">
        <div className="header-row">
          <h3 style={{ margin: 0 }}>Create New Loan</h3>
          <span className="muted">Fixed Interest: 8% p.a. (Reducing Balance)</span>
        </div>
        {error && <div className="error">{error}</div>}
        <form className="form-grid" onSubmit={handleCreate}>
          <div className="field">
            <label>Member</label>
            <select value={memberId} onChange={(e) => setMemberId(e.target.value)}>
              {members.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.member_code})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Principal (₹)</label>
            <input
              type="number"
              min="1"
              placeholder="e.g. 100000"
              value={principal}
              onChange={(e) => setPrincipal(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Tenure (Months)</label>
            <input
              type="number"
              min="1"
              max="360"
              value={tenureMonths}
              onChange={(e) => setTenureMonths(e.target.value)}
            />
          </div>
          <button className="btn" disabled={submitting || members.length === 0}>
            {submitting ? 'Generating...' : 'Create Loan & Schedule'}
          </button>
        </form>
      </div>

      <div className="card">
        <div className="header-row">
          <h3 style={{ margin: 0 }}>All Loans ({visibleLoans.length})</h3>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="ALL">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Loan #</th>
                <th>Member</th>
                <th className="num">Principal</th>
                <th className="num">Tenure</th>
                <th className="num">Monthly EMI</th>
                <th className="num">Outstanding</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {visibleLoans.length === 0 ? (
                <tr>
                  <td colSpan="8" className="muted">
                    No loans found.
                  </td>
                </tr>
              ) : (
                visibleLoans.map((loan) => (
                  <tr key={loan.id}>
                    <td>#{loan.id}</td>
                    <td>
                      {loan.member_name}{' '}
                      <span className="muted">({loan.member_code})</span>
                    </td>
                    <td className="num">{formatINR(loan.principal)}</td>
                    <td className="num">{loan.tenure_months} mo</td>
                    <td className="num">{formatINR(loan.emi_amount)}</td>
                    <td className="num">{formatINR(loan.outstanding_balance)}</td>
                    <td>
                      <span
                        className={`badge ${
                          loan.status === 'ACTIVE' ? 'badge-active' : 'badge-closed'
                        }`}
                      >
                        {loan.status}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => onSelectLoan(loan.id)}
                      >
                        View Schedule
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}