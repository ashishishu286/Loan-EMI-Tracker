import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatINR } from '../utils';

const actions = [
  { page: 'members', label: 'Manage members' },
  { page: 'loans', label: 'Create / view loans' },
  { page: 'report', label: 'Outstanding report & CSV', secondary: true },
];

export default function Dashboard({ onNavigate }) {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getDashboard().then(setStats).catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="error">{error}</div>;
  if (!stats) return <div className="card">Loading dashboard...</div>;

  const cards = [
    ['Total members', stats.total_members],
    ['Active / total loans', `${stats.active_loans} / ${stats.total_loans}`],
    ['Total disbursed', formatINR(stats.total_disbursed)],
    ['Total outstanding', formatINR(stats.total_outstanding)],
  ];

  return (
    <div>
      <div className="stats-grid">
        {cards.map(([label, value]) => (
          <div className="stat-card" key={label}>
            <div className="stat-label">{label}</div>
            <div className="stat-value">{value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Quick actions</h3>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {actions.map(({ page, label, secondary }) => (
            <button
              key={page}
              className={secondary ? 'btn btn-secondary' : 'btn'}
              onClick={() => onNavigate(page)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
