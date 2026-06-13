import * as api from '../index';

jest.mock('../grievances', () => ({
  grievancesApi: {}
}));
jest.mock('../resolutionProof', () => ({
  resolutionProofApi: {}
}));
jest.mock('../auth', () => ({
  authApi: {}
}));
jest.mock('../admin', () => ({
  adminApi: {}
}));

// Mock all the API modules
jest.mock('../client', () => ({
  apiClient: { get: jest.fn(), post: jest.fn(), postForm: jest.fn() },
  getApiUrl: jest.fn()
}));

jest.mock('../issues', () => ({
  issuesApi: { getRecent: jest.fn(), create: jest.fn(), vote: jest.fn() }
}));

jest.mock('../detectors', () => ({
  detectorsApi: {
    pothole: jest.fn(),
    garbage: jest.fn(),
    vandalism: jest.fn(),
    flooding: jest.fn(),
    infrastructure: jest.fn(),
    illegalParking: jest.fn(),
    streetLight: jest.fn(),
    fire: jest.fn(),
    strayAnimal: jest.fn(),
    blockedRoad: jest.fn(),
    treeHazard: jest.fn(),
    pest: jest.fn()
  }
}));

jest.mock('../misc', () => ({
  miscApi: {
    getResponsibilityMap: jest.fn(),
    chat: jest.fn(),
    getRepContact: jest.fn(),
    getStats: jest.fn()
  }
}));

describe('API Index Exports', () => {
  it('should export all client functions', () => {
    expect(api.apiClient).toBeDefined();
    expect(typeof api.apiClient.get).toBe('function');
    expect(typeof api.apiClient.post).toBe('function');
    expect(typeof api.apiClient.postForm).toBe('function');
    expect(typeof api.getApiUrl).toBe('function');
  });

  it('should export all issues API functions', () => {
    expect(api.issuesApi).toBeDefined();
    expect(typeof api.issuesApi.getRecent).toBe('function');
    expect(typeof api.issuesApi.create).toBe('function');
    expect(typeof api.issuesApi.vote).toBe('function');
  });

  it('should export all detector API functions', () => {
    expect(api.detectorsApi).toBeDefined();

    const expectedDetectors = [
      'pothole', 'garbage', 'vandalism', 'flooding', 'infrastructure',
      'illegalParking', 'streetLight', 'fire', 'strayAnimal',
      'blockedRoad', 'treeHazard', 'pest'
    ];

    expectedDetectors.forEach(detector => {
      expect(typeof api.detectorsApi[detector]).toBe('function');
    });
  });

  it('should export all misc API functions', () => {
    expect(api.miscApi).toBeDefined();
    expect(typeof api.miscApi.getResponsibilityMap).toBe('function');
    expect(typeof api.miscApi.chat).toBe('function');
    expect(typeof api.miscApi.getRepContact).toBe('function');
    expect(typeof api.miscApi.getStats).toBe('function');
  });

  it('should not export any undefined values', () => {
    // Check that all exports are properly defined
    Object.keys(api).forEach(key => {
      expect(api[key]).toBeDefined();
      expect(api[key]).not.toBeNull();
    });
  });

  it('should have the correct number of exports', () => {
    const exportKeys = Object.keys(api);
    // client: apiClient (1) (assuming getApiUrl isn't exported if we check the index.js actually exports everything from client, wait index.js exports *, so if client exports getApiUrl it'll be here)
    expect(exportKeys.length).toBeGreaterThanOrEqual(5);

    const expectedKeys = ['apiClient', 'issuesApi', 'detectorsApi', 'miscApi', 'grievancesApi', 'resolutionProofApi', 'authApi', 'adminApi'];
    expectedKeys.forEach(key => {
      expect(exportKeys).toContain(key);
    });
  });
});