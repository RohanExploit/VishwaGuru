# Maharashtra MLA Integration Guide

This document describes the implementation of Maharashtra pincode-wise MLA lookup feature integrated with Gemini API.

## Overview

This feature allows users to find their Maharashtra MLA (Member of Legislative Assembly) by entering their 6-digit pincode. The system provides:
- MLA contact information (name, party, phone, email)
- District and constituency details
- Links to grievance portals (CPGRAMS and Maharashtra Aaple Sarkar)
- AI-generated description of MLA's role and responsibilities using Gemini

## Architecture

### Backend Components

#### 1. Data Files (`backend/data/`)

- **`mh_pincode_sample.json`**: Maps pincodes to constituencies
  ```json
  {
    "pincode": "411001",
    "district": "Pune",
    "state": "Maharashtra",
    "assembly_constituency": "Kasba Peth"
  }
  ```

- **`mh_mla_sample.json`**: Contains MLA information
  ```json
  {
    "state": "Maharashtra",
    "assembly_constituency": "Kasba Peth",
    "mla_name": "Sample MLA Pune",
    "party": "Sample Party",
    "phone": "98XXXXXXXX",
    "email": "pune.mla@example.com"
  }
  ```

#### 2. Service Layer

- **`backend/maharashtra_locator.py`**: Pure functions for data lookup
  - `load_maharashtra_pincode_data()`: Loads and caches pincode mapping
  - `load_maharashtra_mla_data()`: Loads and caches MLA data
  - `find_constituency_by_pincode(pincode)`: Returns constituency info for a pincode
  - `find_mla_by_constituency(constituency_name)`: Returns MLA details for a constituency

- **`backend/gemini_summary.py`**: AI-powered MLA description generation
  - `generate_mla_summary()`: Uses Gemini to create human-readable MLA role descriptions
  - Does NOT hallucinate contact details, only describes roles and responsibilities

#### 3. API Endpoint

**Route**: `GET /api/mh/rep-contacts?pincode=XXXXXX`

**Request Parameters**:
- `pincode` (required): 6-digit Maharashtra pincode

**Response** (Success - 200):
```json
{
  "pincode": "411001",
  "state": "Maharashtra",
  "district": "Pune",
  "assembly_constituency": "Kasba Peth",
  "mla": {
    "name": "Sample MLA Pune",
    "party": "Sample Party",
    "phone": "98XXXXXXXX",
    "email": "pune.mla@example.com"
  },
  "description": "AI-generated description of MLA's role...",
  "grievance_links": {
    "central_cpgrams": "https://pgportal.gov.in/",
    "maharashtra_portal": "https://aaplesarkar.mahaonline.gov.in/en",
    "note": "This is an MVP; data may not be fully accurate."
  }
}
```

**Error Responses**:
- 400: Invalid pincode format
- 404: Pincode not found in database
- 422: Missing or invalid parameters

### Frontend Components

#### 1. API Helper (`frontend/src/api/location.js`)

```javascript
export async function getMaharashtraRepContacts(pincode) {
  const res = await fetch(`${API_URL}/api/mh/rep-contacts?pincode=${pincode}`);
  if (!res.ok) {
    throw new Error('Failed to fetch contact information');
  }
  return res.json();
}
```

#### 2. UI Component (in `frontend/src/App.jsx`)

- New "Find My MLA (Maharashtra)" button on home screen
- Pincode input form with validation
- Results display showing:
  - Location details (pincode, district, constituency)
  - MLA information (name, party, contacts)
  - AI-generated description
  - Grievance portal links (CPGRAMS, Maharashtra Aaple Sarkar)

## Testing

### Unit Tests

**File**: `tests/test_maharashtra_locator.py`

Tests include:
- Data loading functions
- Pincode validation and lookup
- MLA lookup by constituency
- Complete lookup flow (pincode → constituency → MLA)
- Error handling for invalid inputs

**Run tests**:
```bash
cd /home/runner/work/VishwaGuru/VishwaGuru
python -m pytest tests/test_maharashtra_locator.py -v
```

### Endpoint Tests

**File**: `tests/test_mh_endpoint.py`

Tests the complete API endpoint with:
- Valid pincodes (Pune, Mumbai, Nagpur)
- Invalid pincodes
- Invalid formats
- Missing parameters

**Run tests**:
```bash
cd /home/runner/work/VishwaGuru/VishwaGuru
PYTHONPATH=backend python tests/test_mh_endpoint.py
```

## Deployment

### Backend (Render)

The backend is deployed on Render. Environment variables required:
- `GEMINI_API_KEY`: Your Google Gemini API key (reuses existing key)
- `FRONTEND_URL`: Netlify frontend URL for CORS
- `TELEGRAM_BOT_TOKEN`: Telegram bot token (existing)

### Frontend (Netlify)

The frontend is deployed on Netlify. Environment variable required:
- `VITE_API_URL`: Backend API URL from Render

### Database (Neon)

Currently uses static JSON files. Future enhancement can migrate to Neon PostgreSQL for:
- Larger pincode datasets
- Dynamic updates
- Better scalability

## Current Limitations (MVP)

1. **Limited Coverage**: Only 5 sample pincodes are included
2. **Sample Data**: MLA information is placeholder/dummy data
3. **No Real-time Updates**: Static JSON files, not connected to live sources
4. **Maharashtra Only**: Feature is state-specific

## Future Enhancements

1. **Expand Coverage**:
   - Add all Maharashtra pincodes
   - Fetch real MLA data from PRS Legislative Research or state sources
   - Add other states

2. **Database Migration**:
   - Move from JSON files to Neon PostgreSQL
   - Enable admin panel for data updates
   - Add data versioning

3. **Enhanced Features**:
   - Add MP (Member of Parliament) lookup
   - Include ward/municipal councillor information
   - Show MLA's recent activities/bills
   - Add constituency boundaries on map

4. **Geocoding**:
   - Add GPS-based location detection
   - Reverse geocoding to auto-fill pincode
   - Display constituency on a map

## API Usage Examples

### cURL

```bash
# Valid pincode
curl "https://your-backend.onrender.com/api/mh/rep-contacts?pincode=411001"

# Invalid pincode
curl "https://your-backend.onrender.com/api/mh/rep-contacts?pincode=999999"
```

### JavaScript

```javascript
const response = await fetch(
  'https://your-backend.onrender.com/api/mh/rep-contacts?pincode=411001'
);
const data = await response.json();
console.log(data.mla.name);
```

### Python

```python
import requests

response = requests.get(
    'https://your-backend.onrender.com/api/mh/rep-contacts',
    params={'pincode': '411001'}
)
data = response.json()
print(f"Your MLA: {data['mla']['name']}")
```

## Sample Pincodes for Testing

- `411001` - Pune (Kasba Peth)
- `411002` - Pune (Shivajinagar)
- `400001` - Mumbai (Colaba)
- `400020` - Mumbai (Mumbadevi)
- `440001` - Nagpur (Nagpur Central)

## Security Considerations

1. **Input Validation**: Pincode format is validated (6 digits)
2. **Rate Limiting**: Consider adding rate limiting in production
3. **Data Privacy**: Sample data used; ensure real data complies with privacy laws
4. **Gemini Usage**: AI summaries do not include contact info to prevent hallucination

## Maintenance

### Updating Data

To add new pincodes and MLAs:

1. Edit `backend/data/mh_pincode_sample.json`:
   ```json
   {
     "pincode": "NEW_PINCODE",
     "district": "District Name",
     "state": "Maharashtra",
     "assembly_constituency": "Constituency Name"
   }
   ```

2. Edit `backend/data/mh_mla_sample.json`:
   ```json
   {
     "state": "Maharashtra",
     "assembly_constituency": "Constituency Name",
     "mla_name": "MLA Full Name",
     "party": "Party Name",
     "phone": "Contact Number",
     "email": "email@example.com"
   }
   ```

3. Restart the backend service (Render auto-deploys on git push)

### Monitoring

- Check Render logs for errors
- Monitor Gemini API usage
- Track 404 errors to identify missing pincodes

## Contributing

When adding data:
1. Verify MLA information from official sources
2. Ensure pincode-constituency mappings are accurate
3. Add test cases for new pincodes
4. Update this documentation

## Support

For issues or questions:
- Check backend logs on Render dashboard
- Review frontend console for API errors
- Verify environment variables are set correctly
- Ensure CORS is configured properly

---

**Version**: 1.0.0 (MVP)  
**Last Updated**: December 2024
