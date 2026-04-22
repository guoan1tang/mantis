export interface HealthResponse {
  status: string;
  flows: number;
  domains: string[];
  rules: number;
}

export interface StatsEvent {
  type: 'stats';
  total: number;
  methods: Record<string, number>;
  endpoints: string[];
  avg_size: number;
}

export interface AnalysisEvent {
  type: 'analysis';
  chunk: string;
}

export interface ResultEvent {
  type: 'result';
  content: string;
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export interface DoneEvent {
  type: 'done';
}

export type AIEvent = StatsEvent | AnalysisEvent | ResultEvent | ErrorEvent | DoneEvent;
