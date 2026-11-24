import { useState } from 'react';
import { clearToken, getToken } from './api';
import Dashboard from './components/Dashboard';
import LoanDetail from './components/LoanDetail';
import Loans from './components/Loans';
import Login from './components/Login';
import Members from './components/Members';
import Report from './components/Report';

export default function App() {
  const [isAuthed, setIsAuthed] = useState(Boolean(getToken()));
  const [page, setPage] = useState('dashboard');
  const [selectedLoanId, setSelectedLoanId] = useState(null);

  if (!isAuthed) {
    return <Login onSuccess={() => setIsAuthed(true)} />;
  }

  const navigate = (nextPage) => {
    setSelectedLoanId(null);
    setPage(nextPage);
  };

  const handleLogout = () => {
    clearToken();
    setIsAuthed(false);
    setPage('dashboard');
    setSelectedLoanId(null);
  };

  return (
    <div>
      <nav className="navbar">
        <div className="brand">Loan EMI Tracker</div>
        <div className="nav-links">
          <button
            className={`nav-btn ${page === 'dashboard' ? 'active' : ''}`}
            onClick={() => navigate('dashboard')}
          >
            Dashboard
          </button>
          <button
            className={`nav-btn ${page === 'members' ? 'active' : ''}`}
            onClick={() => navigate('members')}
          >
            Members
          </button>
          <button
            className={`nav-btn ${page === 'loans' ? 'active' : ''}`}
            onClick={() => navigate('loans')}
          >
            Loans
          </button>
          <button
            className={`nav-btn ${page === 'report' ? 'active' : ''}`}
            onClick={() => navigate('report')}
          >
            Report
          </button>
          <button className="nav-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <main className="container">
        {page === 'dashboard' && <Dashboard onNavigate={navigate} />}
        {page === 'members' && <Members />}
        {page === 'loans' && !selectedLoanId && (
          <Loans onSelectLoan={(id) => setSelectedLoanId(id)} />
        )}
        {page === 'loans' && selectedLoanId && (
          <LoanDetail
            loanId={selectedLoanId}
            onBack={() => setSelectedLoanId(null)}
          />
        )}
        {page === 'report' && <Report />}
      </main>
    </div>
  );
}