const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const error = new Error(`API error: ${res.status} ${res.statusText}`);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export function fetchVehicles(params = {}) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, value);
    }
  }
  const qs = searchParams.toString();
  return request(`/api/vehicles${qs ? `?${qs}` : ''}`);
}

export function fetchVehicle(id) {
  return request(`/api/vehicles/${id}`);
}

export function fetchFilters(params = {}) {
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.set(key, value);
    }
  }
  const qs = searchParams.toString();
  return request(`/api/filters${qs ? `?${qs}` : ''}`);
}

export function fetchStats() {
  return request('/api/stats');
}

export function submitLead(data) {
  return request('/api/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}
