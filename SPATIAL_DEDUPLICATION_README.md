# Spatial Deduplication Implementation

## Overview

This implementation adds geospatial clustering and deduplication to prevent duplicate issue reports for the same real-world problems. When users report issues with location data, the system automatically checks for nearby existing "open" issues within a 50-meter radius and either links the new report to an existing issue or prompts the user to upvote/verify existing reports.

## Key Features

### 1. **Automatic Deduplication**
- When a new issue is reported with coordinates, the system searches for existing open issues within 50 meters
- If nearby issues are found, the new report is automatically linked to the closest existing issue
- The existing issue receives an upvote, increasing its priority

### 2. **Nearby Issues API**
- `GET /api/issues/nearby?latitude={lat}&longitude={lon}&radius={meters}&limit={n}`
- Returns issues near a location, sorted by distance
- Useful for frontend to show nearby issues before creating a new report

### 3. **Manual Verification**
- `POST /api/issues/{issue_id}/verify`
- Allows users to manually verify existing issues (counts as 2 upvotes)
- Issues with 5+ upvotes automatically get "verified" status

### 4. **Enhanced Response Schema**
- Issue creation now returns deduplication information
- Includes nearby issues, recommended actions, and linked issue IDs

## Technical Implementation

### Spatial Utilities (`backend/spatial_utils.py`)
- `haversine_distance()`: Calculate distance between coordinates
- `find_nearby_issues()`: Find issues within radius, sorted by distance
- `cluster_issues_dbscan()`: Cluster issues using DBSCAN algorithm
- `get_cluster_representative()`: Get most representative issue from cluster

### API Changes
- **Issue Creation**: Now includes deduplication check before saving
- **Response Format**: Returns `IssueCreateWithDeduplicationResponse` with deduplication info
- **New Endpoints**:
  - `/api/issues/nearby` - Get nearby issues
  - `/api/issues/{issue_id}/verify` - Manual verification

### Database Considerations
- Uses existing `latitude`/`longitude` fields in Issue model
- No additional spatial indexes (SQLite limitation)
- For production PostgreSQL, consider PostGIS for better performance

## Usage Examples

### Creating an Issue with Deduplication
```python
response = requests.post("/api/issues", data={
    "description": "Pothole on Main St",
    "category": "Road",
    "latitude": 19.0760,
    "longitude": 72.8777
})

if response.json()["deduplication_info"]["has_nearby_issues"]:
    print("Linked to existing issue:", response.json()["linked_issue_id"])
```

### Finding Nearby Issues
```python
response = requests.get("/api/issues/nearby", params={
    "latitude": 19.0760,
    "longitude": 72.8777,
    "radius": 50
})
nearby_issues = response.json()
```

## Configuration

- **Search Radius**: Currently set to 50 meters (configurable in code)
- **Auto-upvote**: Deduplication automatically upvotes the closest existing issue
- **Verification Threshold**: Issues with 5+ upvotes get "verified" status

## Testing

Run the spatial deduplication tests:
```bash
PYTHONPATH=. python tests/test_spatial_deduplication.py
```

Tests cover:
- Spatial utility functions
- Deduplication API behavior
- Manual verification endpoint

## Future Enhancements

1. **H3 Indexing**: Implement Uber's H3 geospatial indexing for faster queries
2. **Clustering Analysis**: Use DBSCAN for identifying issue clusters
3. **Frontend Integration**: Add UI prompts for manual deduplication choices
4. **Admin Controls**: Allow adjusting deduplication radius and thresholds
5. **Performance**: Add spatial indexes for production databases

## Impact

- **Data Quality**: Eliminates duplicate reports, providing cleaner data to government
- **User Experience**: Users can see existing issues and contribute to community consensus
- **Resource Efficiency**: Reduces database clutter and processing overhead
- **Community Engagement**: Encourages upvoting and verification of existing issues