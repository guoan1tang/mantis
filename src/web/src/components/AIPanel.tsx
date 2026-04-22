import { useState } from 'react';
import { SSEService } from '../services/sse';
import type { AIEvent } from '../types/api';
import QuickActions from './QuickActions';

const sse = new SSEService();

export default function AIPanel() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (query?: string) => {
    const text = query || input.trim();
    if (!text || loading) return;
    if (!query) setInput('');

    setMessages(prev => [...prev, { role: 'user', text }]);
    setLoading(true);

    let aiText = '';
    try {
      await sse.query('/api/ai/query', text, (event: AIEvent) => {
        if (event.type === 'analysis' || event.type === 'result') {
          aiText += event.type === 'analysis' ? event.chunk : event.content;
          setMessages(prev => {
            const updated = [...prev];
            const last = updated[updated.length - 1];
            if (last && last.role === 'assistant') {
              last.text = aiText;
            } else {
              updated.push({ role: 'assistant', text: aiText });
            }
            return updated;
          });
        } else if (event.type === 'error') {
          setMessages(prev => [...prev, { role: 'error', text: event.message }]);
        }
      });
    } catch (e) {
      setMessages(prev => [...prev, { role: 'error', text: String(e) }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ marginBottom: 4, fontSize: 12 }}>
            {m.role === 'user' && <strong style={{ color: '#87CEEB' }}>You:</strong>}
            {m.role === 'assistant' && <strong style={{ color: '#90EE90' }}>AI:</strong>}
            {m.role === 'error' && <strong style={{ color: '#FF6B6B' }}>Error:</strong>}
            {' '}{m.text}
          </div>
        ))}
        {loading && <div style={{ color: '#ff9800', fontSize: 12 }}>Analyzing...</div>}
      </div>
      <QuickActions onAction={handleSubmit} />
      <div style={{ display: 'flex', borderTop: '1px solid #333' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSubmit()}
          placeholder="Ask AI about captured traffic..."
          disabled={loading}
          style={{ flex: 1, padding: 8, background: '#1a1a2e', color: '#e0e0e0', border: 'none', outline: 'none' }}
        />
      </div>
    </div>
  );
}
