import type { AIEvent } from '../types/api';

export class SSEService {
  private abortController: AbortController | null = null;

  async query(url: string, query: string, onEvent: (event: AIEvent) => void, flowIds?: string[]): Promise<void> {
    this.abortController?.abort();
    this.abortController = new AbortController();

    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, flow_ids: flowIds }),
      signal: this.abortController.signal,
    });

    if (!resp.ok) throw new Error(`AI request failed: ${resp.statusText}`);

    const reader = resp.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event: AIEvent = JSON.parse(line.slice(6));
              onEvent(event);
            } catch {}
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      throw e;
    }
  }

  abort() {
    this.abortController?.abort();
  }
}
