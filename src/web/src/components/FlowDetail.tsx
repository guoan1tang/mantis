import { useEffect, useState } from 'react';
import { fetchFlow } from '../services/api';
import type { Flow } from '../types/flow';

export default function FlowDetail({ flowId }: { flowId: string | null }) {
  const [flow, setFlow] = useState<Flow | null>(null);

  useEffect(() => {
    if (!flowId) { setFlow(null); return; }
    fetchFlow(flowId).then(setFlow).catch(console.error);
  }, [flowId]);

  if (!flow) return <div style={{ padding: 20, color: '#666' }}>No flow selected</div>;

  const decodeBody = (b64: string | null) => {
    if (!b64) return '(empty)';
    try {
      const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
      const text = new TextDecoder('utf-8').decode(bytes);
      if (text.startsWith('{') || text.startsWith('[')) {
        return JSON.stringify(JSON.parse(text), null, 2);
      }
      return text;
    } catch {
      return '(binary data)';
    }
  };

  return (
    <div style={{ padding: 12, overflowY: 'auto', flex: 1, fontSize: 13 }}>
      <div style={{ marginBottom: 12 }}>
        <strong>{flow.method}</strong> {flow.url}
      </div>

      <h4 style={{ margin: '8px 0 4px' }}>Request Headers</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#aaa' }}>
        {Object.entries(flow.request_headers).map(([k, v]) => `${k}: ${v}`).join('\n') || '(none)'}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Request Body</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#ccc', maxHeight: 200, overflow: 'auto' }}>
        {decodeBody(flow.request_body_base64)}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>
        Response <span style={{ color: (flow.status_code ?? 0) < 400 ? '#4caf50' : '#f44336' }}>{flow.status_code ?? '(pending)'}</span>
      </h4>

      <h4 style={{ margin: '8px 0 4px' }}>Response Headers</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#aaa' }}>
        {Object.entries(flow.response_headers).map(([k, v]) => `${k}: ${v}`).join('\n') || '(none)'}
      </pre>

      <h4 style={{ margin: '8px 0 4px' }}>Response Body</h4>
      <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', color: '#ccc', maxHeight: 300, overflow: 'auto' }}>
        {decodeBody(flow.response_body_base64)}
      </pre>
    </div>
  );
}
