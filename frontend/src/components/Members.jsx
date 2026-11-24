import { useEffect, useState } from 'react';
import { api } from '../api';
import { formatINR } from '../utils';

export default function Members() {
  const [members, setMembers] = useState([]);
  const [search, setSearch] = useState('');
  const [memberCode, setMemberCode] = useState('');
  const [name, setName] = useState('');
  const [monthlySalary, setMonthlySalary] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadMembers = () => {
    api
      .getMembers()
      .then(setMembers)
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadMembers();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    setError('');

    if (!memberCode.trim() || !name.trim() || Number(monthlySalary) <= 0) {
      setError('Member ID, Name, and a positive Monthly Salary are required.');
      return;
    }

    setSubmitting(true);
    try {
      await api.createMember({
        member_code: memberCode.trim(),
        name: name.trim(),
        monthly_salary: Math.round(Number(monthlySalary)),
      });
      setMemberCode('');
      setName('');
      setMonthlySalary('');
      loadMembers();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const filtered = members.filter(
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      m.member_code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Add New Member</h3>
        {error && <div className="error">{error}</div>}
        <form className="form-grid" onSubmit={handleAdd}>
          <div className="field">
            <label>Member / Employee ID</label>
            <input
              placeholder="e.g. EMP-104"
              value={memberCode}
              onChange={(e) => setMemberCode(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Full Name</label>
            <input
              placeholder="e.g. Sneha Kulkarni"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="field">
            <label>Monthly Salary (₹)</label>
            <input
              type="number"
              min="1"
              placeholder="e.g. 60000"
              value={monthlySalary}
              onChange={(e) => setMonthlySalary(e.target.value)}
            />
          </div>
          <button className="btn" disabled={submitting}>
            {submitting ? 'Adding...' : 'Add Member'}
          </button>
        </form>
      </div>

      <div className="card">
        <div className="header-row">
          <h3 style={{ margin: 0 }}>Members ({filtered.length})</h3>
          <input
            placeholder="Search by name or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Member ID</th>
                <th>Name</th>
                <th className="num">Monthly Salary</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan="3" className="muted">
                    No members found.
                  </td>
                </tr>
              ) : (
                filtered.map((m) => (
                  <tr key={m.id}>
                    <td>{m.member_code}</td>
                    <td>{m.name}</td>
                    <td className="num">{formatINR(m.monthly_salary)}</td>
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