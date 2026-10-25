/**
 * Server-Sent Events (SSE) Client (SPEC §10.8 / Stream R3 / R3.4).
 *
 * Connects to /v1/stream with auth (session cookies), tracks Last-Event-ID,
 * manages exponential backoff on disconnects, invalidates TanStack Query cache
 * on realtime domain events, and surfaces a visible live indicator state.
 */

import { useState, useEffect, useRef } from 'react';
import { queryClient } from './queryClient';

export type SSEConnectionStatus = 'connecting' | 'live' | 'disconnected';

export interface SSEClientOptions {
  onEvent?: (eventType: string, payload: unknown, id?: string) => void;
  enabled?: boolean;
}

export function useRealtimeStream(options: SSEClientOptions = {}) {
  const { enabled = true, onEvent } = options;
  const [status, setStatus] = useState<SSEConnectionStatus>('disconnected');
  const [lastEventId, setLastEventId] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const backoffRef = useRef<number>(1000);
  const lastIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setStatus('disconnected');
      return;
    }

    let isCancelled = false;

    function connect() {
      if (isCancelled) return;
      setStatus('connecting');

      const url = new URL('/v1/stream', window.location.origin);
      if (lastIdRef.current) {
        url.searchParams.set('last_event_id', lastIdRef.current);
      }

      try {
        const es = new EventSource(url.toString(), { withCredentials: true });
        eventSourceRef.current = es;

        es.onopen = () => {
          if (isCancelled) {
            es.close();
            return;
          }
          setStatus('live');
          backoffRef.current = 1000; // Reset backoff on successful connection
        };

        es.onerror = () => {
          if (isCancelled) return;
          setStatus('disconnected');
          es.close();
          eventSourceRef.current = null;

          // Exponential backoff up to 30s + jitter
          const jitter = Math.floor(Math.random() * 500);
          const delay = Math.min(backoffRef.current, 30000) + jitter;
          backoffRef.current = Math.min(backoffRef.current * 2, 30000);

          reconnectTimeoutRef.current = setTimeout(() => {
            if (!isCancelled) {
              connect();
            }
          }, delay);
        };

        // Generic event listener
        es.onmessage = (e) => {
          if (e.lastEventId) {
            lastIdRef.current = e.lastEventId;
            setLastEventId(e.lastEventId);
          }
        };

        // Domain-specific event handlers for cache invalidation
        const registerEventHandler = (type: string, queryKeysToInvalidate: string[][]) => {
          es.addEventListener(type, (e: MessageEvent) => {
            if (e.lastEventId) {
              lastIdRef.current = e.lastEventId;
              setLastEventId(e.lastEventId);
            }
            let payload: unknown = null;
            try {
              payload = JSON.parse(e.data);
            } catch {
              payload = e.data;
            }

            onEvent?.(type, payload, e.lastEventId);

            // Invalidate TanStack query cache keys
            for (const key of queryKeysToInvalidate) {
              queryClient.invalidateQueries({ queryKey: key });
            }
          });
        };

        registerEventHandler('instrument.created', [['instruments'], ['dashboard']]);
        registerEventHandler('instrument.submitted', [['instruments'], ['dashboard']]);
        registerEventHandler('instrument.transitioned', [['instruments'], ['dashboard']]);
        registerEventHandler('observation.opened', [['observations'], ['instruments'], ['dashboard']]);
        registerEventHandler('observation.resolved', [['observations'], ['instruments'], ['dashboard']]);
        registerEventHandler('notification.created', [['notifications']]);
        registerEventHandler('notification.queued', [['notifications']]);
        registerEventHandler('session.revoked', [['sessions']]);
      } catch {
        setStatus('disconnected');
      }
    }

    connect();

    return () => {
      isCancelled = true;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      setStatus('disconnected');
    };
  }, [enabled, onEvent]);

  return { status, lastEventId };
}
