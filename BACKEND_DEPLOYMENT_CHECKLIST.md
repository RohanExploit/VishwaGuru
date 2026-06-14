# Backend Deployment, API Integrity & System Integration - #246

## Deployment Checklist

### Pre-Deployment Setup
- [ ] Create Render account at https://render.com
- [ ] Fork/clone VishwaGuru repository
- [ ] Set up environment variables in Render dashboard
- [ ] Configure PostgreSQL database (Neon, Supabase, etc.)
- [ ] Deploy frontend to Netlify and get the URL

### Environment Variables Configuration
Set the following in Render dashboard:

```bash
GEMINI_API_KEY=your_google_gemini_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
FRONTEND_URL=https://your-netlify-app.netlify.app
DATABASE_URL=postgresql://user:pass@host:port/dbname
CORS_ORIGINS=https://your-netlify-app.netlify.app
ENVIRONMENT=production
DEBUG=false
```

### API Endpoints to Test

#### Core Endpoints
- [ ] `GET /` - Should return service info
- [ ] `GET /health` - Should return healthy status
- [ ] `GET /api/stats` - Should return application statistics

#### Issues Management
- [ ] `GET /api/issues/recent` - Should return recent issues
- [ ] `POST /api/issues` - Should create new issue (test with form data)
- [ ] `GET /api/issues/{id}` - Should return specific issue
- [ ] `PUT /api/issues/{id}/vote` - Should update vote count
- [ ] `PUT /api/issues/{id}/status` - Should update issue status

#### AI Services
- [ ] `POST /api/chat` - Should respond to chat messages
- [ ] `POST /api/detect/pothole` - Should detect potholes in images
- [ ] `POST /api/detect/garbage` - Should detect garbage in images
- [ ] `POST /api/analyze-urgency` - Should analyze issue urgency

#### Utility Endpoints
- [ ] `GET /api/responsibility-map` - Should return responsibility mapping
- [ ] `GET /api/mh/rep-contacts?pincode=400001` - Should return rep contacts
- [ ] `POST /api/push/subscribe` - Should handle push subscriptions

### Frontend-Backend Integration Tests

#### CORS Configuration
- [ ] Frontend can make requests to backend without CORS errors
- [ ] All API calls from frontend succeed
- [ ] Error responses are handled properly

#### Data Flow
- [ ] Issue creation from frontend works
- [ ] Image uploads are processed correctly
- [ ] Chat functionality works
- [ ] ML detections return valid results

### Security & Performance Checks

#### Security
- [ ] No sensitive data exposed in API responses
- [ ] API keys are not logged or exposed
- [ ] CORS is properly configured
- [ ] Rate limiting is working

#### Performance
- [ ] API responses are reasonably fast (< 5 seconds)
- [ ] Large file uploads are handled properly
- [ ] Database queries are optimized
- [ ] Memory usage is reasonable

### Error Handling
- [ ] Invalid requests return appropriate error codes
- [ ] Missing required fields are validated
- [ ] File upload limits are enforced
- [ ] Network timeouts are handled gracefully

### Database Integrity
- [ ] Database migrations run successfully
- [ ] Data is persisted correctly
- [ ] Concurrent requests don't cause issues
- [ ] Backup/restore procedures work

## Testing Commands

### Local Testing
```bash
# Test backend startup
python start-backend.py

# Test API endpoints
python test-api.py

# Run unit tests
cd backend && python -m pytest tests/
```

### Production Testing
```bash
# Test health endpoint
curl https://your-backend.onrender.com/health

# Test with Postman/Thunder Client
# Import the API collection and test all endpoints
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check FRONTEND_URL and CORS_ORIGINS environment variables
   - Ensure frontend URL is correct and includes protocol

2. **Database Connection Issues**
   - Verify DATABASE_URL format
   - Check database credentials and permissions
   - Ensure database server allows connections

3. **API Key Issues**
   - Verify GEMINI_API_KEY and TELEGRAM_BOT_TOKEN are set
   - Check API key validity and permissions

4. **File Upload Issues**
   - Check MAX_UPLOAD_SIZE_MB setting
   - Verify ALLOWED_FILE_TYPES configuration
   - Check server disk space

### Logs and Monitoring
- Check Render logs for startup errors
- Monitor API response times
- Watch for database connection issues
- Check for memory leaks

## Video Demo Requirements

Create a 4-7 minute video covering:

1. **Backend Local Testing** (2 min)
   - Show backend starting locally
   - Demonstrate API testing with curl/Postman
   - Show database operations

2. **Deployment Process** (1 min)
   - Render dashboard setup
   - Environment variable configuration
   - Deployment logs

3. **Production API Testing** (2 min)
   - Test all endpoints on deployed backend
   - Show API documentation at `/docs`
   - Demonstrate error handling

4. **Frontend-Backend Integration** (2 min)
   - Show frontend connecting to deployed backend
   - Demonstrate full user workflow
   - Show real-time data flow

## Success Criteria

- [ ] Backend deploys successfully on Render
- [ ] All API endpoints return correct responses
- [ ] Frontend can consume all backend APIs
- [ ] No security vulnerabilities exposed
- [ ] Performance meets requirements
- [ ] Error handling is robust
- [ ] Database operations work correctly
- [ ] Video demo shows complete functionality