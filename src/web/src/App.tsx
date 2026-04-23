import { useState, useEffect, useCallback } from 'react';
import type { FlowList } from './types/flow';
import type { WSEvent } from './services/ws';
import { fetchFlows } from './services/api';
import { WSService } from './services/ws';
import FlowListTable from './components/FlowList';
import FlowDetail from './components/FlowDetail';
import DomainTree from './components/DomainTree';
import AIPanel from './components/AIPanel';
import StatusBar from './components/StatusBar';

const ws = new WSService();

export default function App() {
  const [flows, setFlows] = useState<FlowList[]>([]);
  const [selectedFlow, setSelectedFlow] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);
  const [proxyHost, setProxyHost] = useState<string>('');
  const [proxyPort, setProxyPort] = useState<number>(0);
  const [certUrl, setCertUrl] = useState<string>('');
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    fetchFlows().then(setFlows).catch(console.error);

    ws.connect();
    ws.onEvent((event: WSEvent) => {
      if (event.type === 'connected') {
        setConnected(true);
        // Fetch proxy info from health endpoint
        fetch('/api/health').then(r => r.json()).then(data => {
          setProxyHost(data.proxy_host);
          setProxyPort(data.proxy_port);
          // Construct cert URL via Vite dev server (proxied to Python)
          setCertUrl(`${window.location.origin}/cert/setup`);
          // Fetch pause state
          fetch('/api/control').then(r2 => r2.json()).then(d => setPaused(d.paused)).catch(console.error);
        }).catch(console.error);
        return;
      }
      setConnected(true);
      if (event.type === 'flow_added') {
        setFlows(prev => [...prev, event.flow]);
      }
    });

    return () => ws.disconnect();
  }, []);

  const handleSelect = useCallback((id: string) => setSelectedFlow(id), []);
  const handleClear = useCallback(() => setFlows([]), []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <StatusBar connected={connected} flowCount={flows.length} proxyHost={proxyHost} proxyPort={proxyPort} certUrl={certUrl} />
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        <div style={{ width: 200, borderRight: '1px solid #333', overflowY: 'auto' }}>
          <DomainTree />
        </div>
        <div style={{ width: '40%', borderRight: '1px solid #333', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <FlowListTable flows={flows} selectedId={selectedFlow} onSelect={handleSelect} onClear={handleClear} paused={paused} onPauseChange={setPaused} />
        </div>
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <FlowDetail flowId={selectedFlow} />
        </div>
      </div>
      <div style={{ height: 200, borderTop: '1px solid #333' }}>
        <AIPanel />
      </div>
    </div>
  );
}
