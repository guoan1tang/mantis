import { useState, useEffect } from 'react';
import { fetchDomains, addDomain, deleteDomain } from '../services/api';

export default function DomainTree() {
  const [domains, setDomains] = useState<string[]>([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    fetchDomains().then(setDomains).catch(console.error);
  }, []);

  const handleAdd = async () => {
    if (!input.trim()) return;
    try {
      await addDomain(input.trim());
      setDomains(prev => [...prev, input.trim()]);
      setInput('');
    } catch (e) {
      console.error('Failed to add domain', e);
    }
  };

  const handleDelete = async (domain: string) => {
    try {
      await deleteDomain(domain);
      setDomains(prev => prev.filter(d => d !== domain));
    } catch (e) {
      console.error('Failed to delete domain', e);
    }
  };

  return (
    <div style={{ padding: 8 }}>
      <h4 style={{ marginBottom: 8, fontSize: 13 }}>Domains</h4>
      <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAdd()}
          placeholder="Add domain..."
          style={{ flex: 1, padding: 4, fontSize: 12, background: '#1a1a2e', color: '#e0e0e0', border: '1px solid #333', borderRadius: 2 }}
        />
        <button onClick={handleAdd} style={{ fontSize: 12, padding: '4px 8px', cursor: 'pointer' }}>+</button>
      </div>
      <div style={{ maxHeight: 200, overflowY: 'auto' }}>
        {domains.map(domain => (
          <div key={domain} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '2px 4px', fontSize: 12 }}>
            <span>{domain}</span>
            <button onClick={() => handleDelete(domain)} style={{ background: 'none', border: 'none', color: '#f44336', cursor: 'pointer', fontSize: 12 }}>x</button>
          </div>
        ))}
      </div>
    </div>
  );
}
