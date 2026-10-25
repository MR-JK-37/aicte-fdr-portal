/**
 * apiFetch wrapper for apps/web (Stream R3.2 / MASTER_PROMPT_V2 §6).
 *
 * Provides:
 * 1. Automatic Correlation-ID header injection (RFC 9457 traceability).
 * 2. Same-origin credentials (httponly cookies for session and refresh).
 * 3. CSRF token header (X-CSRF-Token) for mutating requests.
 * 4. Mapping of RFC 9457 application/problem+json errors into typed ProblemError.
 */

export interface ProblemDetails {
  type?: string;
  title?: string;
  status: number;
  detail?: string;
  instance?: string;
  correlation_id?: string;
  code?: string;
  errors?: Record<string, string[]>;
  [key: string]: unknown;
}

export class ProblemError extends Error {
  public readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title || `API error ${problem.status}`);
    this.name = 'ProblemError';
    this.problem = problem;
  }

  get status(): number {
    return this.problem.status;
  }

  get correlationId(): string | undefined {
    return this.problem.correlation_id;
  }

  get isStaleVersion(): boolean {
    return this.problem.status === 409 || this.problem.code === 'STALE_VERSION';
  }

  get isStepUpRequired(): boolean {
    return this.problem.status === 403 && this.problem.code === 'step_up_required';
  }

  get isForbidden(): boolean {
    return this.problem.status === 403;
  }

  get isNotFound(): boolean {
    return this.problem.status === 404;
  }
}

function generateCorrelationId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'corr-' + Math.random().toString(36).substring(2, 15);
}

function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)fdr_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function apiFetch<T>(
  url: string,
  init?: RequestInit
): Promise<T> {
  const headers = new Headers(init?.headers);

  // Correlation ID header
  if (!headers.has('X-Correlation-ID')) {
    headers.set('X-Correlation-ID', generateCorrelationId());
  }

  // CSRF protection on mutating requests
  const method = (init?.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken && !headers.has('X-CSRF-Token')) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }

  // Ensure JSON content-type if body is a stringified JSON object
  if (init?.body && typeof init.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...init,
    headers,
    credentials: init?.credentials || 'include',
  });

  if (!response.ok) {
    let problem: ProblemDetails;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/problem+json') || contentType.includes('application/json')) {
      try {
        const json = await response.json();
        problem = {
          status: response.status,
          title: json.title || response.statusText,
          detail: json.detail,
          type: json.type,
          correlation_id: json.correlation_id || headers.get('X-Correlation-ID') || undefined,
          code: json.code,
          errors: json.errors,
          ...json,
        };
      } catch {
        problem = {
          status: response.status,
          title: response.statusText,
          correlation_id: headers.get('X-Correlation-ID') || undefined,
        };
      }
    } else {
      const text = await response.text();
      problem = {
        status: response.status,
        title: response.statusText,
        detail: text || undefined,
        correlation_id: headers.get('X-Correlation-ID') || undefined,
      };
    }
    throw new ProblemError(problem);
  }

  // 204 No Content
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return (await response.json()) as T;
  }

  return (await response.text()) as unknown as T;
}
