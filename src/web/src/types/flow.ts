export interface Flow {
  id: string;
  timestamp: string;
  method: string;
  url: string;
  host: string;
  path: string;
  status_code: number | null;
  request_headers: Record<string, string>;
  response_headers: Record<string, string>;
  content_type: string;
  size: number;
  duration_ms: number;
  intercepted: boolean;
  modified: boolean;
  tags: string[];
  security_issues: string[];
  request_body_base64: string | null;
  response_body_base64: string | null;
}

export interface FlowList {
  id: string;
  method: string;
  url: string;
  host: string;
  path: string;
  status_code: number | null;
  duration_ms: number;
  size: number;
}
