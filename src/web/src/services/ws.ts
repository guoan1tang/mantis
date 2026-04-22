export type WSEvent =
  | { type: 'flow_added'; flow: any }
  | { type: 'flow_updated'; flow: any }
  | { type: 'domain_added'; domain: string }
  | { type: 'rule_added'; rule: any }
  | { type: 'error'; message: string };

export class WSService {
  private ws: WebSocket | null = null;
  private listeners: ((event: WSEvent) => void)[] = [];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;

  connect(url?: string) {
    const backendUrl = import.meta.env.VITE_API_URL || '';
    const defaultWsUrl = url || `${backendUrl || `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.hostname}:9080`}/ws/events`;
    this.ws = new WebSocket(defaultWsUrl);
    this.ws.onmessage = (e) => {
      try {
        const event: WSEvent = JSON.parse(e.data);
        this.listeners.forEach(fn => fn(event));
      } catch {}
    };
    this.ws.onclose = () => {
      this.reconnectAttempts++;
      if (this.reconnectAttempts <= this.maxReconnectAttempts) {
        setTimeout(() => this.connect(url), 5000);
      }
    };
  }

  onEvent(fn: (event: WSEvent) => void) {
    this.listeners.push(fn);
    return () => { this.listeners = this.listeners.filter(l => l !== fn); };
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
