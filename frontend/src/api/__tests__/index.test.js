import * as api from '../index';

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
    // client: apiClient, getApiUrl (2)
    // issues: issuesApi (1)
    // detectors: detectorsApi (1)
    // misc: miscApi (1)
    // Total: 5 top-level exports
    const exportKeys = Object.keys(api);
    expect(exportKeys.length).toBe(5);

    const expectedKeys = ['apiClient', 'getApiUrl', 'issuesApi', 'detectorsApi', 'miscApi'];
    expectedKeys.forEach(key => {
      expect(exportKeys).toContain(key);
    });
  });
});