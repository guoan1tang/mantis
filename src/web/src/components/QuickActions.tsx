interface Props {
  onAction: (query: string) => void;
}

const actions = [
  { label: '\u5206\u6790\u6d41\u91cf', query: '\u5206\u6790\u6d41\u91cf' },
  { label: '\u68c0\u67e5\u5b89\u5168', query: '\u68c0\u67e5\u5b89\u5168\u95ee\u9898' },
  { label: '\u7edf\u8ba1\u63a5\u53e3', query: '\u7edf\u8ba1\u6240\u6709\u63a5\u53e3' },
];

export default function QuickActions({ onAction }: Props) {
  return (
    <div style={{ display: 'flex', gap: 4, padding: '4px 8px' }}>
      {actions.map(a => (
        <button
          key={a.label}
          onClick={() => onAction(a.query)}
          style={{ padding: '2px 8px', fontSize: 12, cursor: 'pointer', background: '#16213e', color: '#e0e0e0', border: '1px solid #333', borderRadius: 2 }}
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}
