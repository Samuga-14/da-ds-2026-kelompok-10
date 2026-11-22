/**
 * FE service boundary. Components call these domain methods instead of
 * constructing endpoint URLs throughout the dashboard.
 */
const TobaKostApi = {
  capabilities() {
    return fetch('/api/capabilities');
  },

  analytics() {
    return fetch('/api/data');
  },

  summary(filters = {}) {
    const params = new URLSearchParams();
    [
      'kecamatan',
      'kategori_penghuni',
      'sewa_tahunan_bulanan',
      'tahun_mulai_sewa',
      'harga_min',
      'harga_max',
      'fasilitas'
    ]
      .forEach((key) => {
        const value = filters[key];
        if (value !== undefined && value !== null && value !== '' && value !== 'ALL') {
          params.append(key, value);
        }
      });

    const query = params.toString();
    return fetch(query ? `/api/summary?${query}` : '/api/summary');
  },

  predict(payload) {
    return fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  },

  warehouse(table) {
    return fetch(`/api/warehouse?table=${encodeURIComponent(table)}`);
  },

  createKos(payload) {
    return fetch('/api/kos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  }
};
