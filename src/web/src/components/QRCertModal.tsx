import { QRCodeSVG } from 'qrcode.react';

interface Props {
  certUrl: string;
  onClose: () => void;
}

export default function QRCertModal({ certUrl, onClose }: Props) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000,
      }}
    >
      <div
        onClick={e => e.stopPropagation()}
        style={{
          background: '#16213e', borderRadius: 12, padding: 24,
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 16, maxWidth: 320, width: '90%',
        }}
      >
        <h3 style={{ margin: 0, color: '#e0e0e0' }}>手机抓包 - 扫码设置</h3>
        <p style={{ margin: 0, color: '#aaa', fontSize: 13, textAlign: 'center' }}>
          手机连同一 Wi-Fi 后，用浏览器扫码此二维码
        </p>
        <div style={{ background: '#fff', borderRadius: 8, padding: 12 }}>
          <QRCodeSVG value={certUrl} size={200} />
        </div>
        <p style={{ margin: 0, color: '#87CEEB', fontSize: 12, userSelect: 'text', wordBreak: 'break-all', textAlign: 'center' }}>
          {certUrl}
        </p>
        <p style={{ margin: 0, color: '#aaa', fontSize: 12 }}>
          扫码后页面将显示证书下载和代理设置指南
        </p>
        <button
          onClick={onClose}
          style={{
            padding: '6px 24px', background: '#4caf50', color: '#fff',
            border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 14,
          }}
        >
          关闭
        </button>
      </div>
    </div>
  );
}
