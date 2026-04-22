import { useState } from 'react';
import type { FlowList } from '../types/flow';

interface Props {
  flows: FlowList[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export default function FlowListTable({ flows, selectedId, onSelect }: Props) {
  const [filter, setFilter] = useState('');
  const filtered = flows.filter(f =>
    !filter || f.path.toLowerCase().includes(filter) || f.host.toLowerCase().includes(filter)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <input
        placeholder="Filter by path or host..."
        value={filter}
        onChange={e => setFilter(e.target.value)}
        style={{ padding: 8, border: 'none', borderBottom: '1px solid #333', background: '#1a1a2e', color: '#e0e0e0', outline: 'none' }}
      />
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>
              <th style={{ padding: '4px 8px' }}>Method</th>
              <th style={{ padding: '4px 8px' }}>Path</th>
              <th style={{ padding: '4px 8px' }}>Status</th>
              <th style={{ padding: '4px 8px' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(f => (
              <tr
                key={f.id}
                onClick={() => onSelect(f.id)}
                style={{
                  background: f.id === selectedId ? '#16213e' : 'transparent',
                  cursor: 'pointer',
                  borderBottom: '1px solid #222',
                }}
              >
                <td style={{ padding: '4px 8px' }}>
                  <span style={{ color: f.method === 'GET' ? '#4caf50' : f.method === 'POST' ? '#2196f3' : '#ff9800' }}>
                    {f.method}
                  </span>
                </td>
                <td style={{ padding: '4px 8px', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {f.path}
                </td>
                <td style={{ padding: '4px 8px', color: (f.status_code ?? 0) < 400 ? '#4caf50' : '#f44336' }}>
                  {f.status_code ?? '...'}
                </td>
                <td style={{ padding: '4px 8px', color: '#888' }}>
                  {f.duration_ms > 0 ? `${f.duration_ms.toFixed(0)}ms` : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
