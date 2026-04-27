const API_BASE = 'http://localhost:8000';

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/api/health`);
  return res.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload`, { method: 'POST', body: formData });
  if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Upload failed'); }
  return res.json();
}

export async function analyzeData(context = '') {
  const formData = new FormData();
  formData.append('context', context);
  const res = await fetch(`${API_BASE}/api/analyze`, { method: 'POST', body: formData });
  if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Analysis failed'); }
  return res.json();
}

export async function getVisualizationData(datasetType = null) {
  const url = datasetType
    ? `${API_BASE}/api/visualizations?dataset_type=${datasetType}`
    : `${API_BASE}/api/visualizations`;
  const res = await fetch(url);
  if (!res.ok) { const err = await res.json(); throw new Error(err.detail || 'Failed to load visualizations'); }
  return res.json();
}

export function getExportUrl(type) {
  return `${API_BASE}/api/export/${type}`;
}
