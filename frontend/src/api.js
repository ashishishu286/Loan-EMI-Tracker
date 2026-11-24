const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function getToken() {
  return localStorage.getItem('emi_token');
}

export function setToken(token) {
  localStorage.setItem('emi_token', token);
}

export function clearToken() {
  localStorage.removeItem('emi_token');
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (res.status === 401 && path !== '/api/login') {
    clearToken();
    window.location.reload();
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Request failed');
  }

  return res.json();
}

export const api = {
  login: (username, password) =>
    request('/api/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),
  getDashboard: () => request('/api/dashboard'),
  getMembers: () => request('/api/members'),
  createMember: (data) =>
    request('/api/members', { method: 'POST', body: JSON.stringify(data) }),
  getLoans: () => request('/api/loans'),
  createLoan: (data) =>
    request('/api/loans', { method: 'POST', body: JSON.stringify(data) }),
  getLoanDetail: (id) => request(`/api/loans/${id}`),
  payNextEmi: (id) => request(`/api/loans/${id}/pay-next`, { method: 'POST' }),
  forecloseLoan: (id) => request(`/api/loans/${id}/foreclose`, { method: 'POST' }),
  getMemberOutstandingReport: () => request('/api/reports/member-outstanding'),
  downloadReportCsv: async () => {
    const res = await fetch(`${API_BASE}/api/reports/member-outstanding/csv`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) throw new Error('Failed to export CSV');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'member-outstanding-report.csv';
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
};