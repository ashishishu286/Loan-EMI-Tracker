import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatDate, formatINR } from '../utils';

export default function LoanDetail({ loanId, onBack }) {
  const [loan, setLoan] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const loadLoan = () => {
    api
      .getLoanDetail(loanId)
      .then(setLoan)
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadLoan();
  }, [loanId]);

  const handlePayNext = async () => {
    setError('');
    setBusy(true);
    try {
      await api.payNextEmi(loanId);
      loadLoan();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleForeclose = async () => {
    const settlement = loan.foreclosure_preview?.settlement_amount || 0;
    const confirmed = window.confirm(
      `Foreclose this loan now?\nSettlement = Outstanding Principal + Current Month Interest = ${formatINR(
        settlement
      )}.\nAll future interest will be waived.`
    );
    if (!confirmed) return;

    setError('');
    setBusy(true);
    try {
      await api.forecloseLoan(loanId);
      loadLoan();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (error && !loan) return <div className="error">{error}</div>;
  if (!loan) return <div className="card">Loading loan schedule...</div>;

  return (
    <div>
      <div className="header-row">
        <button className="btn btn-secondary" onClick={onBack}>
          ← Back to Loans
        </button>
        {loan.status === 'ACTIVE' && (
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button className="btn" disabled={busy} onClick={handlePayNext}>
              Record Next EMI Payment
            </button>
            <button
              className="btn btn-danger"
              disabled={busy}
              onClick={handleForeclose}
            >
              Foreclose Loan ({formatINR(loan.foreclosure_preview.settlement_amount)})
            </button>
          </div>
        )}
      </div>

      {error && <div className="error">{error}</div>}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Member</div>
          <div className="stat-value" style={{ fontSize: 18 }}>
            {loan.member_name} ({loan.member_code})
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Original Principal</div>
          <div className="stat-value">{formatINR(loan.principal)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Current Outstanding Principal</div>
          <div className="stat-value">{formatINR(loan.outstanding_balance)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Status / Monthly EMI</div>
          <div className="stat-value" style={{ fontSize: 20 }}>
            {loan.status} · {formatINR(loan.emi_amount)}
          </div>
        </div>
      </div>

      {loan.foreclosed_amount != null && (
        <div className="card">
          <strong>Foreclosed:</strong> Settled for{' '}
          {formatINR(loan.foreclosed_amount)} (future interest waived).
        </div>
      )}

      <div className="card">
        <div className="header-row">
          <h3 style={{ margin: 0 }}>
            EMI Repayment Schedule ({loan.tenure_months} months @ 8% p.a. reducing)
          </h3>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>EMI #</th>
                <th>Due Date</th>
                <th className="num">EMI Amount</th>
                <th className="num">Principal</th>
                <th className="num">Interest</th>
                <th className="num">Outstanding Balance</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {loan.schedule.map((row) => (
                <tr key={row.id}>
                  <td>{row.emi_number}</td>
                  <td>{formatDate(row.due_date)}</td>
                  <td className="num">{formatINR(row.emi_amount)}</td>
                  <td className="num">{formatINR(row.principal_component)}</td>
                  <td className="num">{formatINR(row.interest_component)}</td>
                  <td className="num">{formatINR(row.closing_balance)}</td>
                  <td>
                    <span
                      className={`badge badge-${row.status.toLowerCase()}`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}