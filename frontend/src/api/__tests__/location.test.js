import { getMaharashtraRepContacts } from '../location';
import { fakeRepInfo } from '../../fakeData';

// Mock fetch globally
global.fetch = jest.fn();

// Mock fakeData
jest.mock('../../fakeData', () => ({
  fakeRepInfo: {
    mla: 'Fake MLA',
    mp: 'Fake MP',
    contact: 'fake@example.com',
    pincode: '000000'
  }
}));

describe('getMaharashtraRepContacts', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset environment variable
    delete process.env.VITE_API_URL;
  });

  it('should return representative data from API on success', async () => {
    const pincode = '400001';
    const mockApiResponse = {
      mla: 'John Doe',
      mp: 'Jane Smith',
      contact: '+91-9876543210',
      district: 'Mumbai',
      assembly: 'South Mumbai'
    };

    const mockFetchResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockApiResponse)
    };

    global.fetch.mockResolvedValue(mockFetchResponse);

    const result = await getMaharashtraRepContacts(pincode);

    expect(global.fetch).toHaveBeenCalledWith('/api/mh/rep-contacts?pincode=400001');
    expect(result).toEqual(mockApiResponse);
  });

  it('should use API URL prefix when VITE_API_URL is set', async () => {
    process.env.VITE_API_URL = 'https://api.example.com';
    const pincode = '411001';
    const mockApiResponse = { mla: 'Test MLA' };

    const mockFetchResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockApiResponse)
    };

    global.fetch.mockResolvedValue(mockFetchResponse);

    await getMaharashtraRepContacts(pincode);

    expect(global.fetch).toHaveBeenCalledWith('https://api.example.com/api/mh/rep-contacts?pincode=411001');
  });

  it('should return fake data when API call fails', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const pincode = '400001';
    const error = new Error('Network error');

    global.fetch.mockRejectedValue(error);

    const result = await getMaharashtraRepContacts(pincode);

    expect(result).toEqual({ ...fakeRepInfo, pincode: '400001' });
    expect(consoleErrorSpy).toHaveBeenCalledWith("Failed to fetch representative info, using fake data", error);

    consoleErrorSpy.mockRestore();
  });

  it('should handle HTTP error responses', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const pincode = '999999';
    const errorResponse = { detail: 'Invalid pincode' };

    const mockFetchResponse = {
      ok: false,
      json: jest.fn().mockResolvedValue(errorResponse)
    };

    global.fetch.mockResolvedValue(mockFetchResponse);

    const result = await getMaharashtraRepContacts(pincode);

    expect(result).toEqual({ ...fakeRepInfo, pincode: '999999' });
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should handle different pincode formats', async () => {
    const testPincodes = ['400001', '411001', '500001', '600001'];

    for (const pincode of testPincodes) {
      const mockApiResponse = { mla: 'Test MLA' };
      const mockFetchResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue(mockApiResponse)
      };

      global.fetch.mockResolvedValue(mockFetchResponse);

      const result = await getMaharashtraRepContacts(pincode);

      expect(global.fetch).toHaveBeenCalledWith(`/api/mh/rep-contacts?pincode=${pincode}`);
      expect(result).toEqual(mockApiResponse);
    }
  });

  it('should handle JSON parsing errors in error responses', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const pincode = '400001';

    const mockFetchResponse = {
      ok: false,
      json: jest.fn().mockRejectedValue(new Error('Invalid JSON'))
    };

    global.fetch.mockResolvedValue(mockFetchResponse);

    const result = await getMaharashtraRepContacts(pincode);

    expect(result).toEqual({ ...fakeRepInfo, pincode: '400001' });
    expect(consoleErrorSpy).toHaveBeenCalled();

    consoleErrorSpy.mockRestore();
  });

  it('should handle network timeouts', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const pincode = '400001';
    const timeoutError = new Error('Request timeout');

    global.fetch.mockRejectedValue(timeoutError);

    const result = await getMaharashtraRepContacts(pincode);

    expect(result).toEqual({ ...fakeRepInfo, pincode: '400001' });
    expect(consoleErrorSpy).toHaveBeenCalledWith("Failed to fetch representative info, using fake data", timeoutError);

    consoleErrorSpy.mockRestore();
  });

  it('should enrich fake data with requested pincode', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    const pincode = '123456';

    global.fetch.mockRejectedValue(new Error('API down'));

    const result = await getMaharashtraRepContacts(pincode);

    expect(result.pincode).toBe('123456');
    expect(result.mla).toBe(fakeRepInfo.mla);
    expect(result.mp).toBe(fakeRepInfo.mp);

    consoleErrorSpy.mockRestore();
  });

  it('should handle empty pincode', async () => {
    const pincode = '';
    const mockApiResponse = { mla: 'Test MLA' };

    const mockFetchResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockApiResponse)
    };

    global.fetch.mockResolvedValue(mockFetchResponse);

    const result = await getMaharashtraRepContacts(pincode);

    expect(global.fetch).toHaveBeenCalledWith('/api/mh/rep-contacts?pincode=');
    expect(result).toEqual(mockApiResponse);
  });
});