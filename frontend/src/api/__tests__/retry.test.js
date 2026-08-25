/**
 * Cold-start resilience for the API client.
 *
 * The backend is deployed on an instance that suspends when idle. Its first
 * request after a quiet period took 117 seconds when measured against the live
 * service; subsequent requests took 0.5s. Every call used a bare fetch with no
 * timeout and no retry, so during that window requests hung indefinitely, the
 * UI showed an unexplained spinner, and detectors polling every two seconds
 * stacked up dozens of pending requests against a server that was still
 * starting.
 */
import { apiClient, onServerWaking, request, retryConfig } from '../client';

const original = { ...retryConfig };

beforeEach(() => {
  jest.clearAllMocks();
  // Shrink the delays; retrying through real backoff would spend a minute of
  // CI time proving arithmetic.
  retryConfig.attemptTimeoutMs = 50;
  retryConfig.totalBudgetMs = 400;
  retryConfig.backoffMs = [1];
});

afterEach(() => {
  Object.assign(retryConfig, original);
});

const ok = (body = {}) => ({ ok: true, status: 200, json: async () => body });
const serverError = () => ({ ok: false, status: 500, json: async () => ({}) });
const clientError = (status = 422) => ({ ok: false, status, json: async () => ({}) });

describe('transient failures', () => {
  it('retries and succeeds once the server finishes waking', async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error('Network request failed'))
      .mockRejectedValueOnce(new Error('Network request failed'))
      .mockResolvedValueOnce(ok({ status: 'healthy' }));

    await expect(apiClient.get('/health')).resolves.toEqual({ status: 'healthy' });
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });

  it('retries a 500, which is what a starting server returns', async () => {
    global.fetch = jest
      .fn()
      .mockResolvedValueOnce(serverError())
      .mockResolvedValueOnce(ok({ ready: true }));

    await expect(apiClient.get('/api/stats')).resolves.toEqual({ ready: true });
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('gives up once the budget is spent instead of hanging forever', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network request failed'));

    await expect(apiClient.get('/health')).rejects.toThrow();
    // The point is that it terminates at all; the old client had no bound.
    expect(global.fetch).toHaveBeenCalled();
  });
});

describe('failures that must not be retried', () => {
  it('does not retry a 4xx', async () => {
    // A 422 means the request itself is wrong. Retrying it burns the budget
    // and, on the AI endpoints, real money.
    global.fetch = jest.fn().mockResolvedValue(clientError(422));

    await expect(apiClient.post('/api/chat', { query: 'hi' })).rejects.toThrow();
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('honours retry: false for calls where a stale answer is useless', async () => {
    // A live detector frame is pointless thirty seconds later.
    global.fetch = jest.fn().mockRejectedValue(new Error('Network request failed'));

    await expect(
      request('/api/detect-pothole', { method: 'POST' }, { retry: false }),
    ).rejects.toThrow();
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });
});

describe('timeout', () => {
  it('aborts an attempt that never settles rather than waiting forever', async () => {
    global.fetch = jest.fn((_url, options) => {
      return new Promise((_resolve, reject) => {
        options.signal.addEventListener('abort', () =>
          reject(Object.assign(new Error('Aborted'), { name: 'AbortError' })),
        );
      });
    });

    await expect(apiClient.get('/health')).rejects.toThrow();
    expect(global.fetch).toHaveBeenCalled();
  });
});

describe('server-waking notifications', () => {
  it('tells subscribers the server is waking, then that it is up', async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error('Network request failed'))
      .mockResolvedValueOnce(ok({}));

    const seen = [];
    const unsubscribe = onServerWaking((waking) => seen.push(waking));

    await apiClient.get('/health');
    unsubscribe();

    // Without this the UI cannot distinguish "starting" from "broken".
    expect(seen).toContain(true);
    expect(seen[seen.length - 1]).toBe(false);
  });

  it('stays quiet when the first attempt succeeds', async () => {
    global.fetch = jest.fn().mockResolvedValue(ok({}));

    const seen = [];
    const unsubscribe = onServerWaking((waking) => seen.push(waking));

    await apiClient.get('/health');
    unsubscribe();

    expect(seen).not.toContain(true);
  });

  it('unsubscribes cleanly', async () => {
    global.fetch = jest.fn().mockResolvedValue(ok({}));

    const listener = jest.fn();
    onServerWaking(listener)();

    await apiClient.get('/health');
    expect(listener).not.toHaveBeenCalled();
  });
});
