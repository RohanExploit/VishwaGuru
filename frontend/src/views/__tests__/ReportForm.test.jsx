/**
 * Tests for the report submission flow.
 *
 * ReportForm is 635 lines and is the reason the application exists -- a citizen
 * describing a civic problem and sending it to the right authority. It had no
 * tests at all, so the field names it posts, its offline fallback and its error
 * handling were only ever verified by hand.
 *
 * These cover the submit contract rather than the styling: what actually goes
 * into the request, and what the component does when it cannot send.
 */
import { fireEvent, render, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import ReportForm from '../ReportForm';

jest.mock('../../offlineQueue', () => ({
  saveReportOffline: jest.fn().mockResolvedValue(undefined),
  registerBackgroundSync: jest.fn(),
}));

jest.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k) => k, i18n: { language: 'en' } }),
}));

import { registerBackgroundSync, saveReportOffline } from '../../offlineQueue';

const defaultProps = () => ({
  setView: jest.fn(),
  setLoading: jest.fn(),
  setError: jest.fn(),
  setActionPlan: jest.fn(),
  fetchRecentIssues: jest.fn(),
  loading: false,
});

const renderForm = (props = {}, { route } = {}) => {
  const merged = { ...defaultProps(), ...props };
  const ui = render(
    <MemoryRouter initialEntries={[route || '/report']}>
      <ReportForm {...merged} />
    </MemoryRouter>,
  );
  return { ...ui, props: merged };
};

/** Read a fetch call's FormData into a plain object. */
const formDataFrom = (call) => {
  const body = call[1].body;
  return Object.fromEntries(body.entries());
};

const setOnline = (value) => {
  Object.defineProperty(window.navigator, 'onLine', {
    value,
    configurable: true,
    writable: true,
  });
};

beforeEach(() => {
  jest.clearAllMocks();
  setOnline(true);
  global.fetch = jest.fn().mockResolvedValue({
    ok: true,
    status: 201,
    json: async () => ({ id: 1, action_plan: null, deduplication_info: {} }),
  });
});

describe('ReportForm rendering', () => {
  it('renders a description field and a submit control', () => {
    renderForm();
    expect(document.querySelector('textarea, input[type="text"]')).toBeInTheDocument();
    expect(document.querySelector('form')).toBeInTheDocument();
  });

  it('prefills description and category from router state', () => {
    // SmartScanner navigates here with a detected category and description.
    const { container } = render(
      <MemoryRouter
        initialEntries={[
          { pathname: '/report', state: { description: 'Detected pothole', category: 'road' } },
        ]}
      >
        <ReportForm {...defaultProps()} />
      </MemoryRouter>,
    );
    expect(container.innerHTML).toContain('Detected pothole');
  });
});

describe('ReportForm submission', () => {
  it('posts to /api/issues with the fields the backend declares', async () => {
    const { container } = renderForm();

    const description = container.querySelector('textarea, input[type="text"]');
    fireEvent.change(description, { target: { value: 'Deep pothole outside the school gate' } });
    fireEvent.submit(container.querySelector('form'));

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/api/issues'));
    expect(call).toBeDefined();
    expect(call[1].method).toBe('POST');

    const sent = formDataFrom(call);
    // These names must match create_issue's Form(...) parameters in
    // backend/main.py. A mismatch is a 422 the UI swallows into a console
    // error, which is how /api/chat and /api/analyze-urgency stayed broken.
    expect(sent).toHaveProperty('description', 'Deep pothole outside the school gate');
    expect(sent).toHaveProperty('category');
  });

  it('does not send latitude or longitude when no location was captured', async () => {
    const { container } = renderForm();

    fireEvent.change(container.querySelector('textarea, input[type="text"]'), {
      target: { value: 'Streetlight out on the corner' },
    });
    fireEvent.submit(container.querySelector('form'));

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());

    const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/api/issues'));
    const sent = formDataFrom(call);
    // Posting empty strings would fail float coercion on the backend.
    expect(sent.latitude).toBeUndefined();
    expect(sent.longitude).toBeUndefined();
  });

  it('reports a failed submission instead of failing silently', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network down'));
    const { container, props } = renderForm();

    fireEvent.change(container.querySelector('textarea, input[type="text"]'), {
      target: { value: 'Overflowing bin near the market' },
    });
    fireEvent.submit(container.querySelector('form'));

    await waitFor(() => expect(props.setLoading).toHaveBeenCalledWith(false));
  });
});

describe('ReportForm offline behaviour', () => {
  it('queues the report locally instead of posting when offline', async () => {
    setOnline(false);
    const { container } = renderForm();

    fireEvent.change(container.querySelector('textarea, input[type="text"]'), {
      target: { value: 'Water leak flooding the lane' },
    });
    fireEvent.submit(container.querySelector('form'));

    await waitFor(() => expect(saveReportOffline).toHaveBeenCalled());

    // The whole point of the offline path: nothing is sent, nothing is lost.
    expect(global.fetch).not.toHaveBeenCalledWith(
      expect.stringContaining('/api/issues'),
      expect.anything(),
    );

    const queued = saveReportOffline.mock.calls[0][0];
    expect(queued).toHaveProperty('description', 'Water leak flooding the lane');
    expect(queued).toHaveProperty('category');
  });

  it('registers a background sync so the queued report is sent later', async () => {
    setOnline(false);
    const { container } = renderForm();

    fireEvent.change(container.querySelector('textarea, input[type="text"]'), {
      target: { value: 'Blocked drain on the main road' },
    });
    fireEvent.submit(container.querySelector('form'));

    // Without this the report sits in IndexedDB until the user reopens the app.
    await waitFor(() => expect(registerBackgroundSync).toHaveBeenCalled());
  });

  it('still takes the user to the action view when offline', async () => {
    setOnline(false);
    const { container, props } = renderForm();

    fireEvent.change(container.querySelector('textarea, input[type="text"]'), {
      target: { value: 'Fallen tree blocking the footpath' },
    });
    fireEvent.submit(container.querySelector('form'));

    await waitFor(() => expect(props.setView).toHaveBeenCalledWith('action'));
  });
});
