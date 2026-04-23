import { useState, useMemo } from 'react';
import type { FlowList } from '../types/flow';
import { clearFlows, togglePause, exportCurl } from '../services/api';

interface Props {
  flows: FlowList[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  onClear: () => void;
  paused: boolean;
  onPauseChange: (paused: boolean) => void;
}

export default function FlowListTable({ flows, selectedId, onSelect, onClear, paused, onPauseChange }: Props) {
  const [filter, setFilter] = useState('');
  const [expandedDomains, setExpandedDomains] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState('');

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(''), 1500);
  };

  const filtered = flows.filter(f =>
    !filter || f.path.toLowerCase().includes(filter) || f.host.toLowerCase().includes(filter)
  );

  const grouped = useMemo(() => {
    const map = new Map<string, FlowList[]>();
    for (const f of filtered) {
      if (!map.has(f.host)) map.set(f.host, []);
      map.get(f.host)!.push(f);
    }
    return map;
  }, [filtered]);

  const toggleDomain = (domain: string) => {
    setExpandedDomains(prev => {
      const next = new Set(prev);
      if (next.has(domain)) next.delete(domain);
      else next.add(domain);
      return next;
    });
  };

  const handleClear = async () => {
    try {
      const { cleared } = await clearFlows();
      if (cleared > 0) onClear();
    } catch (e) {
      console.error('Failed to clear flows', e);
    }
  };

  const handlePause = async () => {
    try {
      const { paused: p } = await togglePause();
      onPauseChange(p);
    } catch (e) {
      console.error('Failed to toggle pause', e);
    }
  };

  const handleExportCurl = async (flowId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const { curl } = await exportCurl(flowId);
      try {
        await navigator.clipboard.writeText(curl);
      } catch {
        // Fallback for non-secure contexts
        const ta = document.createElement('textarea');
        ta.value = curl;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
      }
      showToast('cURL 已复制');
    } catch (e) {
      showToast('复制失败: ' + (e as Error).message);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
          background: '#16213e', color: '#4caf50', padding: '8px 20px', borderRadius: 6,
          fontSize: 13, fontWeight: 600, zIndex: 100, border: '1px solid #4caf50',
        }}>
          {toast}
        </div>
      )}
      {/* Filter + Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, padding: '6px 8px', borderBottom: '1px solid #333', background: '#1a1a2e' }}>
        <input
          placeholder="Filter by path or host..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{ flex: 1, padding: '4px 8px', border: 'none', background: '#1a1a2e', color: '#e0e0e0', outline: 'none', fontSize: 13 }}
        />
        <ActionButton onClick={handleClear} label="清空" title="清空所有请求" />
        <ActionButton onClick={handlePause} label={paused ? '已暂停' : '暂停'} title={paused ? '恢复跟踪' : '暂停跟踪'} active={paused} />
      </div>
      <div style={{ flex: 1, overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>
              <th style={{ padding: '4px 8px' }}>Method</th>
              <th style={{ padding: '4px 8px' }}>Path</th>
              <th style={{ padding: '4px 8px' }}>Status</th>
              <th style={{ padding: '4px 8px' }}>Time</th>
              <th style={{ padding: '4px 8px', width: 28 }}></th>
            </tr>
          </thead>
          <tbody>
            {Array.from(grouped.entries()).map(([domain, items]) => (
              <Fragment key={domain}>
                <tr
                  onClick={() => toggleDomain(domain)}
                  style={{
                    background: '#0f0f23',
                    cursor: 'pointer',
                    borderBottom: '1px solid #333',
                  }}
                >
                  <td colSpan={5} style={{ padding: '4px 8px', fontWeight: 600, fontSize: 12, color: '#7c8aff' }}>
                    {expandedDomains.has(domain) ? '▾' : '▸'} {domain} ({items.length})
                  </td>
                </tr>
                {expandedDomains.has(domain) && items.map(f => (
                  <tr
                    key={f.id}
                    onClick={() => onSelect(f.id)}
                    style={{
                      background: f.id === selectedId ? '#16213e' : 'transparent',
                      cursor: 'pointer',
                      borderBottom: '1px solid #222',
                    }}
                  >
                    <td style={{ padding: '4px 8px', paddingLeft: 20 }}>
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
                    <td style={{ padding: '4px 4px' }}>
                      <button
                        onClick={e => handleExportCurl(f.id, e)}
                        title="复制 curl 命令到剪贴板"
                        style={{
                          background: 'none', border: 'none', color: '#888', cursor: 'pointer',
                          fontSize: 12, padding: '2px 4px', borderRadius: 2,
                        }}
                      >
                        cURL
                      </button>
                    </td>
                  </tr>
                ))}
              </Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Fragment({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

function ActionButton({ onClick, label, active, title }: { onClick: () => void; label: string; active?: boolean; title: string }) {
  return (
    <button
      onClick={onClick}
      title={title}
      style={{
        padding: '3px 10px', fontSize: 12, cursor: 'pointer',
        background: active ? '#ff9800' : '#16213e',
        color: active ? '#fff' : '#aaa',
        border: '1px solid #333', borderRadius: 3,
      }}
    >
      {label}
    </button>
  );
}
