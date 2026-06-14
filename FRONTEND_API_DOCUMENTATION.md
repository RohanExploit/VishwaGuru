# Frontend API Documentation

This document provides comprehensive documentation for the API endpoints used by the VishwaGuru frontend application. All endpoints are RESTful and return JSON responses.

## API Base URL

The frontend uses the `VITE_API_URL` environment variable to determine the API base URL. If not set, it defaults to a relative URL (same origin).

```javascript
const API_URL = import.meta.env.VITE_API_URL || '';
```

## Authentication & Headers

Currently, the API does not require authentication for public endpoints. All requests use standard HTTP methods with JSON payloads.

**Common Headers:**
- `Content-Type: application/json` (for JSON requests)
- `Content-Type: multipart/form-data` (for file uploads)

## Error Handling

All API endpoints follow consistent error handling patterns:

### HTTP Status Codes

- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `413` - Payload Too Large (file uploads)
- `422` - Unprocessable Entity (validation errors)
- `500` - Internal Server Error

### Error Response Format

```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "specific error details"
  },
  "timestamp": "2026-01-24T10:30:00Z"
}
```

### Frontend Error Handling Pattern

```javascript
try {
  const response = await apiClient.get('/api/endpoint');
  // Handle success
} catch (error) {
  console.error('API Error:', error.message);
  // Handle error - show user-friendly message
}
```

---

## API Endpoints

### Health & Status

#### GET /
**Health check endpoint**

**Response:**
```json
{
  "message": "VishwaGuru API is running",
  "data": null,
  "timestamp": "2026-01-24T10:30:00Z"
}
```

#### GET /health
**Detailed health check**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-24T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "ai_services": "healthy"
  }
}
```

**Error Responses:**
- `503` - Service Unavailable (degraded services)

#### GET /api/ml-status
**Machine learning services status**

**Response:**
```json
{
  "status": "ready",
  "models_loaded": ["pothole_detector", "garbage_detector"],
  "memory_usage": {
    "total": "512MB",
    "available": "256MB"
  }
}
```

---

### Issue Management

#### POST /api/issues
**Create a new issue**

**Content-Type:** `multipart/form-data`

**Form Data:**
- `file` (File) - Image file (optional, max 10MB)
- `description` (string) - Issue description (10-1000 chars)
- `category` (string) - Issue category (Road, Water, Streetlight, Garbage, College Infra, Women Safety)
- `user_email` (string) - User's email (optional)
- `latitude` (number) - Latitude coordinate (-90 to 90, optional)
- `longitude` (number) - Longitude coordinate (-180 to 180, optional)
- `location` (string) - Location description (optional, max 200 chars)

**Example Request:**
```javascript
const formData = new FormData();
formData.append('file', imageFile);
formData.append('description', 'Large pothole on Main Street');
formData.append('category', 'Road');
formData.append('latitude', 19.0760);
formData.append('longitude', 72.8777);
formData.append('location', 'Near Bandra Station');

const response = await apiClient.postForm('/api/issues', formData);
```

**Success Response (201):**
```json
{
  "id": 123,
  "message": "Issue created successfully",
  "action_plan": {
    "whatsapp": "Hello, I would like to report a pothole issue...",
    "email_subject": "Urgent: Pothole Repair Needed",
    "email_body": "Dear authorities, there is a dangerous pothole...",
    "x_post": "🚨 Pothole hazard on Main Street! @MumbaiPolice please fix ASAP #RoadSafety"
  }
}
```

**Error Responses:**
- `400` - Invalid form data or missing required fields
- `413` - File too large (>10MB)
- `422` - Validation error (invalid coordinates, category, etc.)

#### GET /api/issues/recent
**Get recent issues**

**Response:**
```json
[
  {
    "id": 123,
    "category": "Road",
    "description": "Large pothole causing traffic issues",
    "created_at": "2026-01-24T09:15:30Z",
    "image_path": "/uploads/issues/123.jpg",
    "status": "open",
    "upvotes": 5,
    "location": "Main Street, Mumbai",
    "latitude": 19.0760,
    "longitude": 72.8777,
    "action_plan": {
      "whatsapp": "...",
      "email_subject": "...",
      "email_body": "...",
      "x_post": "..."
    }
  }
]
```

**Error Responses:**
- `500` - Database error (falls back to fake data in frontend)

#### POST /api/issues/{issue_id}/vote
**Vote on an issue**

**Request Body:**
```json
{}
```
*(Empty body - upvote by default)*

**Success Response:**
```json
{
  "id": 123,
  "upvotes": 6,
  "message": "Vote recorded successfully"
}
```

**Error Responses:**
- `404` - Issue not found
- `400` - Invalid vote type

#### PUT /api/issues/status
**Update issue status (Admin/Government use)**

**Request Body:**
```json
{
  "reference_id": "SECURE_REF_123",
  "status": "in_progress",
  "assigned_to": "Mumbai Municipal Corporation",
  "notes": "Issue assigned to road maintenance team"
}
```

**Success Response:**
```json
{
  "id": 123,
  "reference_id": "SECURE_REF_123",
  "status": "in_progress",
  "message": "Issue status updated successfully"
}
```

---

### AI & Chat

#### POST /api/chat
**Chat with civic assistant**

**Request Body:**
```json
{
  "query": "How do I report a streetlight issue?"
}
```

**Success Response:**
```json
{
  "response": "To report a streetlight issue in Mumbai, you can use the VishwaGuru app or contact your local municipal corporation..."
}
```

**Error Responses:**
- `400` - Empty or invalid query
- `500` - AI service unavailable

#### POST /api/analyze-urgency
**Analyze issue urgency**

**Request Body:**
```json
{
  "description": "Water pipeline burst flooding the street",
  "category": "Water"
}
```

**Success Response:**
```json
{
  "urgency_level": "critical",
  "reasoning": "Water pipeline bursts can cause significant property damage and safety hazards",
  "recommended_actions": [
    "Contact emergency services immediately",
    "Evacuate affected area",
    "Contact municipal water department"
  ]
}
```

---

### Detection Services

All detection endpoints accept `multipart/form-data` with an `image` file.

#### POST /api/detect-pothole
**Detect potholes in image**

**Form Data:**
- `image` (File) - Image file

**Success Response:**
```json
{
  "detections": [
    {
      "class": "pothole",
      "confidence": 0.95,
      "bbox": [100, 200, 150, 250]
    }
  ],
  "severity": "high",
  "description": "Large pothole detected with high confidence"
}
```

#### POST /api/detect-garbage
**Detect garbage in image**

#### POST /api/detect-vandalism
**Detect vandalism/damage**

#### POST /api/detect-flooding
**Detect flooding/water damage**

#### POST /api/detect-infrastructure
**Detect infrastructure issues**

#### POST /api/detect-illegal-parking
**Detect illegal parking**

#### POST /api/detect-street-light
**Detect street light issues**

#### POST /api/detect-fire
**Detect fire hazards**

#### POST /api/detect-stray-animal
**Detect stray animals**

#### POST /api/detect-blocked-road
**Detect blocked roads**

#### POST /api/detect-tree-hazard
**Detect tree hazards**

#### POST /api/detect-pest
**Detect pest infestations**

**Common Detection Response:**
```json
{
  "detections": [
    {
      "class": "detected_object",
      "confidence": 0.87,
      "bbox": [x1, y1, x2, y2]
    }
  ],
  "severity": "medium",
  "description": "Detection results with confidence scores"
}
```

**Error Responses for Detection:**
- `400` - Invalid image file
- `413` - Image too large
- `422` - Unsupported image format
- `500` - ML model unavailable

---

### Location & Government

#### GET /api/responsibility-map
**Get government responsibility mapping**

**Response:**
```json
{
  "data": {
    "roads": "Municipal Corporation",
    "water": "Water Supply Department",
    "streetlights": "Electricity Department",
    "garbage": "Municipal Corporation"
  }
}
```

#### GET /api/mh/rep-contacts?pincode={pincode}
**Get Maharashtra representative contacts by pincode**

**Query Parameters:**
- `pincode` (string) - 6-digit pincode

**Example:** `/api/mh/rep-contacts?pincode=400001`

**Success Response:**
```json
{
  "pincode": "400001",
  "district": "Mumbai",
  "constituency": "Mahalaxmi",
  "mla_name": "Shiv Sena MLA",
  "mla_contact": "+91-22-12345678",
  "mla_email": "mla@example.com",
  "mp_name": "BJP MP",
  "mp_contact": "+91-22-87654321",
  "description": "Contact information for your local representatives"
}
```

**Error Responses:**
- `400` - Invalid pincode format
- `404` - Pincode not found

---

### Push Notifications

#### POST /api/push-subscription
**Subscribe to push notifications**

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh": "base64-encoded-key",
  "auth": "base64-encoded-auth",
  "issue_id": 123
}
```

**Success Response:**
```json
{
  "id": 456,
  "message": "Push subscription created successfully"
}
```

---

## Frontend Integration Examples

### Creating an Issue with Image

```javascript
import { issuesApi } from '../api/issues';

async function createIssue(imageFile, description, category) {
  try {
    const formData = new FormData();
    formData.append('file', imageFile);
    formData.append('description', description);
    formData.append('category', category);

    const result = await issuesApi.create(formData);
    console.log('Issue created:', result);
    return result;
  } catch (error) {
    console.error('Failed to create issue:', error);
    throw error;
  }
}
```

### Using Detection Services

```javascript
import { detectorsApi } from '../api/detectors';

async function detectIssue(imageFile, detectorType) {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);

    const result = await detectorsApi[detectorType](formData);
    console.log('Detection result:', result);
    return result;
  } catch (error) {
    console.error('Detection failed:', error);
    throw error;
  }
}
```

### Error Handling Pattern

```javascript
import { apiClient } from '../api/client';

async function safeApiCall(endpoint, options = {}) {
  try {
    const response = await apiClient.get(endpoint);
    return { success: true, data: response };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      status: error.status || 500
    };
  }
}
```

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- Issue creation: 10 requests per hour per IP
- Detection services: 50 requests per hour per IP
- Chat: 100 requests per hour per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

## File Upload Limits

- Maximum file size: 10MB
- Supported formats: JPEG, PNG, GIF, WebP, BMP, TIFF
- Images are validated for corruption and malware

## Offline Support

The frontend implements offline queuing for API requests:
- Failed requests are stored locally
- Automatic retry when connection is restored
- User notification of queued requests

---

**Last Updated:** 2026-01-24
**API Version:** v1.0
**Contact:** For API support, check the backend logs or create an issue</content>
<parameter name="filePath">c:\Users\Gupta\Downloads\VishwaGuru\FRONTEND_API_DOCUMENTATION.md