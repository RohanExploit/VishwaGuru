/**
 * Tests for the real API client.
 *
 * This file previously imported '../client', which jest.config.js redirected to
 * src/__mocks__/client.js. Every assertion here described a hand-written
 * fixture rather than the client the application ships, so the suite could not
 * have failed if the client broke -- and it encoded the fixture's behaviour
 * (reading process.env, sending a JSON Content-Type on GET) rather than the
 * client's. The redirect is gone; these now exercise the real module.
 *
 * Retry, timeout and cold-start behaviour live in retry.test.js.
 */
import { apiClient, getApiUrl, retryConfig } from '../client';

// babel-plugin-transform-vite-meta-env replaces import.meta.env at transform
// time, so the base URL is fixed for the whole run rather than read from the
// environment. Assertions therefore go through getApiUrl() instead of assuming
// a value.
const BASE = getApiUrl();

const original = { ...retryConfig };

beforeEach(() => {
  jest.clearAllMocks();
  global.fetch = jest.fn();
  // Keep failure cases from spending real backoff time.
  retryConfig.totalBudgetMs = 200;
  retryConfig.backoffMs = [1];
});

afterEach(() => {
  Object.assign(retryConfig, original);
});

const jsonResponse = (body, { ok = true, status = 200 } = {}) => ({
  ok,
  status,
  json: jest.fn().mockResolvedValue(body),
});

/** The URL and options fetch was actually called with. */
const lastCall = () => global.fetch.mock.calls[global.fetch.mock.calls.length - 1];

describe('getApiUrl', () => {
  it('returns the configured base URL', () => {
    expect(typeof getApiUrl()).toBe('string');
  });
});

describe('get', () => {
  it('returns the decoded body on success', async () => {
    global.fetch.mockResolvedValue(jsonResponse({ data: 'test' }));

    await expect(apiClient.get('/test-endpoint')).resolves.toEqual({ data: 'test' });
  });

  it('requests the endpoint under the configured base URL', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}));

    await apiClient.get('/api/stats');

    expect(lastCall()[0]).toBe(`${BASE}/api/stats`);
  });

  it('does not send a JSON Content-Type on a request with no body', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}));

    await apiClient.get('/api/stats');

    expect(lastCall()[1].headers).toBeUndefined();
  });

  it('attaches an abort signal so a request cannot hang forever', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}));

    await apiClient.get('/api/stats');

    // The absence of this is what let cold-start requests hang indefinitely.
    expect(lastCall()[1].signal).toBeDefined();
  });

  it('throws when the response is not ok', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 404 }));

    await expect(apiClient.get('/missing')).rejects.toThrow('404');
  });
});

describe('post', () => {
  it('sends JSON and returns the decoded body', async () => {
    global.fetch.mockResolvedValue(jsonResponse({ id: 1 }));

    await expect(apiClient.post('/api/chat', { query: 'hello' })).resolves.toEqual({ id: 1 });

    const [, options] = lastCall();
    expect(options.method).toBe('POST');
    expect(options.headers['Content-Type']).toBe('application/json');
    expect(JSON.parse(options.body)).toEqual({ query: 'hello' });
  });

  it('posts to the endpoint under the configured base URL', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}));

    await apiClient.post('/api/issues', {});

    expect(lastCall()[0]).toBe(`${BASE}/api/issues`);
  });

  it('throws when the response is not ok', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 422 }));

    await expect(apiClient.post('/api/chat', {})).rejects.toThrow('422');
  });
});

describe('postForm', () => {
  it('sends the FormData unchanged and returns the decoded body', async () => {
    global.fetch.mockResolvedValue(jsonResponse({ detections: [] }));
    const form = new FormData();
    form.append('image', 'blob');

    await expect(apiClient.postForm('/api/detect-pothole', form)).resolves.toEqual({
      detections: [],
    });

    const [, options] = lastCall();
    expect(options.method).toBe('POST');
    expect(options.body).toBe(form);
  });

  it('does not set Content-Type, so fetch can add the multipart boundary', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}));

    await apiClient.postForm('/api/detect-pothole', new FormData());

    // Setting it by hand omits the boundary and the server rejects the upload.
    expect(lastCall()[1].headers).toBeUndefined();
  });

  it('throws when the response is not ok', async () => {
    global.fetch.mockResolvedValue(jsonResponse({}, { ok: false, status: 413 }));

    await expect(apiClient.postForm('/api/detect-pothole', new FormData())).rejects.toThrow('413');
  });
});
