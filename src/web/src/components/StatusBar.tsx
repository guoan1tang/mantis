import { useState } from 'react';
import QRCertModal from './QRCertModal';

export default function StatusBar({ connected, flowCount, proxyHost, proxyPort, certUrl }: { connected: boolean; flowCount: number; proxyHost: string; proxyPort: number; certUrl: string }) {
  const [showQR, setShowQR] = useState(false);

  return (
    <>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 16, padding: '4px 12px',
        background: '#16213e', fontSize: 13,
      }}>
        <span style={{ color: connected ? '#4caf50' : '#f44336' }}>
          {connected ? '\u25cf' : '\u2717'} {connected ? 'Connected' : 'Disconnected'}
        </span>
        <span>Flows: {flowCount}</span>
        {proxyHost && (
          <span style={{ color: '#aaa' }}>
            手机抓包:{' '}
            <a
              href="#"
              onClick={e => { e.preventDefault(); setShowQR(true); }}
              style={{ color: '#87CEEB', textDecoration: 'none' }}
            >
              {proxyHost}:{proxyPort}
            </a>
            {' '}(扫码下载证书)
          </span>
        )}
      </div>
      {showQR && certUrl && <QRCertModal certUrl={certUrl} onClose={() => setShowQR(false)} />}
    </>
  );
}
