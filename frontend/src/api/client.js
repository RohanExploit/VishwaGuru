const API_URL = import.meta.env.VITE_API_URL || '';

/**
 * The API is deployed on an instance that suspends when idle and takes up to
 * ~2 minutes to serve its first request again. Every call in this file
 * previously used a bare fetch with no timeout and no retry, so during that
 * window requests hung indefinitely, the UI showed a spinner with no
 * explanation, and a detector polling every 2 seconds stacked up dozens of
 * pending requests against a server that was still starting.
 *
 * So: each attempt gets a bounded timeout, failures retry with backoff inside a
 * total budget long enough to cover a cold start, and callers can subscribe to
 * find out that the server is waking rather than broken.
 */
/**
 * Mutable so tests can shrink the delays. Retrying through real backoff in a
 * unit test spends a minute of CI time proving arithmetic.
 */
export const retryConfig = {
  attemptTimeoutMs: 20000,
  // Long enough to cover a cold start on a suspended instance.
  totalBudgetMs: 150000,
  backoffMs: [1000, 3000, 6000, 10000, 15000],
};

const wakeListeners = new Set();

/**
 * Subscribe to server-waking notifications. The callback receives true when a
 * request has failed at least once and is being retried, and false once a
 * request succeeds. Returns an unsubscribe function.
 */
export const onServerWaking = (listener) => {
  wakeListeners.add(listener);
  return () => wakeListeners.delete(listener);
};

const notifyWaking = (waking) => {
  for (const listener of wakeListeners) {
    try {
      listener(waking);
    } catch (err) {
      console.error('Server-waking listener failed', err);
    }
  }
};

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** A 4xx means the request itself is wrong; retrying only wastes the budget. */
const isRetriable = (error, response) => {
  if (response) return response.status >= 500 || response.status === 429;
  return true; // network error, abort, DNS failure
};

const fetchWithTimeout = async (url, options, timeoutMs) => {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
};

/**
 * Perform a request, retrying transient failures within the total budget.
 *
 * `retry: false` opts out for calls where a stale answer is worse than none --
 * a live detector frame is pointless 30 seconds later.
 */
export const request = async (endpoint, options = {}, { retry = true } = {}) => {
  const url = `${API_URL}${endpoint}`;
  const deadline = Date.now() + retryConfig.totalBudgetMs;
  let attempt = 0;
  let lastError;

  for (;;) {
    try {
      const response = await fetchWithTimeout(url, options, retryConfig.attemptTimeoutMs);

      if (!response.ok) {
        const error = new Error(`HTTP error! status: ${response.status}`);
        error.status = response.status;
        if (!retry || !isRetriable(error, response) || Date.now() >= deadline) {
          // Flagged so the catch below re-throws instead of treating this as a
          // transient failure. Throwing here without the flag meant a 422 was
          // caught by this function's own handler and retried until the budget
          // ran out -- 28 requests for a payload the server had already
          // rejected, which on the AI endpoints costs real money.
          error.noRetry = true;
          throw error;
        }
        lastError = error;
      } else {
        notifyWaking(false);
        return response;
      }
    } catch (error) {
      // A caller-supplied abort is intentional and must not be retried.
      if (error.noRetry) throw error;
      if (options.signal?.aborted) throw error;
      if (!retry || Date.now() >= deadline) throw error;
      lastError = error;
    }

    const { backoffMs } = retryConfig;
    const delay = backoffMs[Math.min(attempt, backoffMs.length - 1)];
    if (Date.now() + delay >= deadline) throw lastError;

    // Only announce after the first failure: a single slow request is normal,
    // a retry means the server is very likely still starting.
    notifyWaking(true);
    await sleep(delay);
    attempt += 1;
  }
};

export const apiClient = {
  get: async (endpoint, opts) => {
    const response = await request(endpoint, {}, opts);
    return response.json();
  },

  post: async (endpoint, data, opts) => {
    const response = await request(
      endpoint,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      },
      opts,
    );
    return response.json();
  },

  // For file uploads (FormData). fetch sets the multipart Content-Type and
  // boundary itself, so it must not be set here.
  postForm: async (endpoint, formData, opts) => {
    const response = await request(endpoint, { method: 'POST', body: formData }, opts);
    return response.json();
  },
};

export const getApiUrl = () => API_URL;
