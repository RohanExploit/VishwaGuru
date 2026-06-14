# 💾 Supabase Integration Guide

## 📋 Overview

This project is integrated with **Supabase** - an open-source Firebase alternative that provides:
- PostgreSQL database
- Authentication & authorization
- Real-time subscriptions
- Storage
- Edge functions

## 🔐 Security & Environment Variables

### Environment Setup

All Supabase credentials are stored in `.env` file (which is **gitignored** and never committed):

```env
VITE_SUPABASE_URL=https://espcjwpddzibctsvtvtz.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### ⚠️ Important Security Notes

1. **NEVER commit the `.env` file** - it's protected by `.gitignore`
2. **Anon Key is SAFE for frontend** - it's designed for client-side use
3. **Database password should ONLY be used on backend/server** - never in frontend code
4. **Use Row Level Security (RLS)** in Supabase to protect your data
5. When sharing code, use `.env.example` with placeholder values

## 🚀 Quick Start

### 1. Import the Supabase Client

```javascript
import { supabase } from './lib/supabase';
```

### 2. Use React Hooks (Recommended)

```javascript
import { useAuth, useSupabaseQuery } from './lib/supabaseHooks';

function MyComponent() {
  // Get current user
  const { user, loading } = useAuth();
  
  // Fetch data from a table
  const { data: reports, loading: reportsLoading } = useSupabaseQuery('reports', {
    filter: { status: 'pending' },
    order: { column: 'created_at', ascending: false },
    limit: 10
  });
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      {user ? `Welcome ${user.email}` : 'Not logged in'}
      {reports && reports.map(report => (
        <div key={report.id}>{report.title}</div>
      ))}
    </div>
  );
}
```

## 📚 Usage Examples

### Authentication

#### Sign Up
```javascript
import { signUp } from './lib/supabase';

const handleSignUp = async (email, password) => {
  const { data, error } = await signUp(email, password, {
    full_name: 'John Doe',
    avatar_url: 'https://example.com/avatar.jpg'
  });
  
  if (error) {
    console.error('Sign up error:', error);
  } else {
    console.log('User created:', data.user);
  }
};
```

#### Sign In
```javascript
import { signIn } from './lib/supabase';

const handleSignIn = async (email, password) => {
  const { data, error } = await signIn(email, password);
  
  if (error) {
    console.error('Sign in error:', error);
  } else {
    console.log('Logged in:', data.user);
  }
};
```

#### Sign Out
```javascript
import { signOut } from './lib/supabase';

const handleSignOut = async () => {
  const { error } = await signOut();
  if (error) console.error('Sign out error:', error);
};
```

### Database Operations

#### Fetch Data
```javascript
const { data, loading, error, refetch } = useSupabaseQuery('civic_reports', {
  select: 'id, title, description, status, created_at',
  filter: { user_id: user.id },
  order: { column: 'created_at', ascending: false }
});
```

#### Insert Data
```javascript
import { useSupabaseInsert } from './lib/supabaseHooks';

const { insert, loading } = useSupabaseInsert('civic_reports');

const handleSubmit = async (reportData) => {
  const { data, error } = await insert({
    title: reportData.title,
    description: reportData.description,
    latitude: reportData.lat,
    longitude: reportData.lng,
    category: reportData.category,
    user_id: user.id
  });
  
  if (error) {
    console.error('Insert error:', error);
  } else {
    console.log('Report created:', data);
  }
};
```

#### Update Data
```javascript
import { useSupabaseUpdate } from './lib/supabaseHooks';

const { update, loading } = useSupabaseUpdate('civic_reports');

const updateStatus = async (reportId, newStatus) => {
  const { data, error } = await update(reportId, {
    status: newStatus,
    updated_at: new Date().toISOString()
  });
  
  if (error) {
    console.error('Update error:', error);
  }
};
```

#### Delete Data
```javascript
import { useSupabaseDelete } from './lib/supabaseHooks';

const { deleteRecord, loading } = useSupabaseDelete('civic_reports');

const handleDelete = async (reportId) => {
  const { error } = await deleteRecord(reportId);
  
  if (error) {
    console.error('Delete error:', error);
  } else {
    console.log('Report deleted');
  }
};
```

### Real-time Subscriptions

```javascript
import { useSupabaseSubscription } from './lib/supabaseHooks';

function LiveReports() {
  const [reports, setReports] = useState([]);
  
  useSupabaseSubscription('civic_reports', (payload) => {
    console.log('Change received!', payload);
    
    if (payload.eventType === 'INSERT') {
      setReports(prev => [payload.new, ...prev]);
    } else if (payload.eventType === 'UPDATE') {
      setReports(prev => prev.map(r => 
        r.id === payload.new.id ? payload.new : r
      ));
    } else if (payload.eventType === 'DELETE') {
      setReports(prev => prev.filter(r => r.id !== payload.old.id));
    }
  });
  
  return (
    <div>
      {reports.map(report => (
        <div key={report.id}>{report.title}</div>
      ))}
    </div>
  );
}
```

### File Storage

```javascript
import { supabase } from './lib/supabase';

// Upload image
const uploadImage = async (file) => {
  const fileExt = file.name.split('.').pop();
  const fileName = `${Math.random()}.${fileExt}`;
  const filePath = `${user.id}/${fileName}`;

  const { data, error } = await supabase.storage
    .from('report-images')
    .upload(filePath, file);

  if (error) {
    console.error('Upload error:', error);
    return null;
  }

  // Get public URL
  const { data: { publicUrl } } = supabase.storage
    .from('report-images')
    .getPublicUrl(filePath);

  return publicUrl;
};
```

## 🗄️ Database Schema Example

Here's an example table schema for civic reports:

```sql
CREATE TABLE civic_reports (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id),
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  image_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE civic_reports ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view all reports
CREATE POLICY "Anyone can view reports" ON civic_reports
  FOR SELECT USING (true);

-- Policy: Users can insert their own reports
CREATE POLICY "Users can insert their own reports" ON civic_reports
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own reports
CREATE POLICY "Users can update their own reports" ON civic_reports
  FOR UPDATE USING (auth.uid() = user_id);

-- Policy: Users can delete their own reports
CREATE POLICY "Users can delete their own reports" ON civic_reports
  FOR DELETE USING (auth.uid() = user_id);
```

## 🔗 Project Configuration

- **Project URL**: https://espcjwpddzibctsvtvtz.supabase.co
- **MCP Server**: https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz

## 📖 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
- [Real-time Subscriptions](https://supabase.com/docs/guides/realtime)

## 🛡️ Best Practices

1. **Always use Row Level Security (RLS)** on your tables
2. **Validate data on both client and server side**
3. **Use prepared statements** (Supabase does this automatically)
4. **Handle errors gracefully** in your UI
5. **Use environment variables** for all configuration
6. **Never expose service_role key** in frontend code
7. **Implement proper authentication** before allowing data access
8. **Use indexes** on frequently queried columns
9. **Implement rate limiting** for sensitive operations
10. **Monitor usage** via Supabase dashboard

## 🎯 VishwaGuru Integration

For this civic intelligence platform, you can use Supabase to:

1. **Store civic reports** (potholes, garbage, streetlights, etc.)
2. **User authentication** for report submission
3. **Real-time updates** for live report tracking
4. **Image storage** for photo evidence
5. **Geospatial queries** for location-based reports
6. **Vote/comment system** for community engagement
7. **Dashboard analytics** for government officials

## 🚨 Emergency Contact

If credentials are compromised:
1. Immediately rotate keys in Supabase dashboard
2. Update `.env` file with new keys
3. Contact team members
4. Review Supabase logs for suspicious activity
