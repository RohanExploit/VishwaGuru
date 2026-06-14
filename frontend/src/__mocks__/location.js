// Mock version of location.js for testing
import { fakeRepInfo } from '../fakeData';

const getApiUrl = () => {
  return process.env.VITE_API_URL || '';
};

export async function getMaharashtraRepContacts(pincode) {
  try {
    const apiUrl = getApiUrl();
    const fullUrl = `${apiUrl}/api/mh/rep-contacts?pincode=${pincode}`;
    const res = await fetch(fullUrl);

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