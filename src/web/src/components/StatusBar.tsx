export default function StatusBar({ connected, flowCount }: { connected: boolean; flowCount: number }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 16, padding: '4px 12px',
      background: '#16213e', fontSize: 13,
    }}>
      <span style={{ color: connected ? '#4caf50' : '#f44336' }}>
        {connected ? '\u25cf' : '\u2717'} {connected ? 'Connected' : 'Disconnected'}
      </span>
      <span>Flows: {flowCount}</span>
    </div>
  );
}
