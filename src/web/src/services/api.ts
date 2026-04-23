const BASE_URL = import.meta.env.VITE_API_URL || '';

export async function fetchFlows(limit = 100, offset = 0): Promise<import('../types/flow').FlowList[]> {
  const resp = await fetch(`${BASE_URL}/api/flows?limit=${limit}&offset=${offset}`);
  if (!resp.ok) throw new Error(`Failed to fetch flows: ${resp.statusText}`);
  return resp.json();
}

export async function fetchFlow(id: string): Promise<import('../types/flow').Flow> {
  const resp = await fetch(`${BASE_URL}/api/flows/${id}`);
  if (!resp.ok) throw new Error(`Flow not found`);
  return resp.json();
}

export async function clearFlows(): Promise<{ cleared: number }> {
  const resp = await fetch(`${BASE_URL}/api/flows`, { method: 'DELETE' });
  return resp.json();
}

export async function exportCurl(id: string): Promise<{ curl: string }> {
  const resp = await fetch(`${BASE_URL}/api/flows/${id}/curl`);
  if (!resp.ok) throw new Error(`Flow not found`);
  return resp.json();
}

export async function fetchControl(): Promise<{ paused: boolean }> {
  const resp = await fetch(`${BASE_URL}/api/control`);
  return resp.json();
}

export async function togglePause(): Promise<{ paused: boolean }> {
  const resp = await fetch(`${BASE_URL}/api/control/pause`, { method: 'POST' });
  return resp.json();
}

export async function fetchDomains(): Promise<string[]> {
  const resp = await fetch(`${BASE_URL}/api/domains`);
  return resp.json();
}

export async function addDomain(domain: string): Promise<void> {
  const resp = await fetch(`${BASE_URL}/api/domains`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain }),
  });
  if (!resp.ok) throw new Error(`Failed to add domain`);
}

export async function deleteDomain(domain: string): Promise<void> {
  const resp = await fetch(`${BASE_URL}/api/domains/${domain}`, { method: 'DELETE' });
  if (!resp.ok) throw new Error(`Failed to delete domain`);
}

export async function postAIAnalyze(query: string, flowIds?: string[]): Promise<ReadableStream<Uint8Array>> {
  const resp = await fetch(`${BASE_URL}/api/ai/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, flow_ids: flowIds }),
  });
  if (!resp.ok) throw new Error(`AI request failed: ${resp.statusText}`);
  return resp.body!;
}
