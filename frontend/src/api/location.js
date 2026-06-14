/**
 * Location API Helper for Maharashtra Representative Lookup
 * 
 * Provides functions to interact with the Maharashtra representative
 * contact information endpoint.
 */

import { fakeRepInfo } from '../fakeData';

// Get API URL from environment variable, fallback to relative URL for local dev
const API_URL = import.meta.env.VITE_API_URL || '';

/**
 * Get Maharashtra representative contact information by pincode
 * 
 * @param {string} pincode - 6-digit pincode
 * @returns {Promise<Object>} Representative contact information
 * @throws {Error} If the request fails or pincode is invalid
 */
export async function getMaharashtraRepContacts(pincode) {
  try {
    const res = await fetch(`${API_URL}/api/mh/rep-contacts?pincode=${pincode}`);

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: 'Failed to fetch contact information' }));
      throw new Error(errorData.detail || 'Failed to fetch contact information');
    }

    return await res.json();
  } catch (error) {
    console.error("Failed to fetch representative info, using fake data", error);
    // Return fake data enriched with the requested pincode
    return { ...fakeRepInfo, pincode: pincode };
  }
}
