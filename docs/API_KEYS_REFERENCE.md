# 🔑 API Keys & Credentials Reference

## ✅ All API Keys Securely Stored

Your API keys and credentials have been securely added to the `.env` file, which is **gitignored** and will never be committed to GitHub.

---

## 📋 Current Configuration

### 🤖 **AI & ML Services**

| Service | Variable Name | Status |
|---------|---------------|--------|
| **Jules AI** | `JULES_API_KEY` | ✅ Configured (Pro) |
| **Hugging Face** | `HF_TOKEN` | ✅ Configured |
| **Google Gemini** | `GEMINI_API_KEY` | ⚠️ Needs update |
| **Telegram Bot** | `TELEGRAM_BOT_TOKEN` | ⚠️ Needs update |

### 🌐 **Deployment Services**

| Service | Variable Name | Status |
|---------|---------------|--------|
| **Render** | `RENDER_API_KEY` | ✅ Configured |

### 💾 **Database Services**

| Service | Variable Name | Status |
|---------|---------------|--------|
| **Supabase URL** | `VITE_SUPABASE_URL` | ✅ Configured |
| **Supabase Anon Key** | `VITE_SUPABASE_ANON_KEY` | ✅ Configured |
| **Supabase DB Password** | `SUPABASE_DB_PASSWORD` | ✅ Secured (commented) |

---

## 🔐 Security Status

✅ **All secrets are protected in `.env`**  
✅ **`.env` is gitignored** (line 14 of `.gitignore`)  
✅ **Multiple `.env*` patterns** excluded from Git  
✅ **`.env.example` contains safe placeholders** for team members  

**Verification:**
```bash
git check-ignore -v .env
# Result: .gitignore:14:.env ✅
```

---

## 🚀 Where These Keys Are Used

### **Hugging Face Token** (`HF_TOKEN`)
- **Purpose**: Access Hugging Face models and API
- **Used in**: Backend ML inference, model downloads
- **Fallback**: Enabled via `ENABLE_HF_FALLBACK=true`
- **Scope**: Server-side only (backend)

### **Jules API Key** (`JULES_API_KEY`)
- **Purpose**: AI-powered autonomous development assistance
- **Subscription**: Pro tier (enhanced capabilities)
- **Used in**: Development automation, code generation, autonomous decision-making
- **Features**:
  - 🤖 Autonomous development when user is away
  - 🚀 Auto-approve best practices and safe operations
  - 📝 Intelligent code generation and refactoring
  - 🔍 Advanced code analysis and optimization
  - ⚡ Reduced human interaction during development
- **Scope**: Development environment
- **Pro Benefits**: Enhanced AI models, faster responses, priority access

### **Render API Key** (`RENDER_API_KEY`)
- **Purpose**: Automated deployments, service management
- **Used in**: Deployment scripts, CI/CD pipelines
- **Scope**: Deployment automation scripts
- **Documentation**: See `RENDER_DEPLOYMENT.md`

### **Supabase Credentials**
- **Purpose**: Database, authentication, storage, real-time
- **Used in**: Frontend application
- **Scope**: 
  - `VITE_SUPABASE_URL` & `VITE_SUPABASE_ANON_KEY`: ✅ Safe for frontend
  - `SUPABASE_DB_PASSWORD`: ❌ Backend only (commented out)
- **Documentation**: See `SUPABASE_SETUP.md` and `docs/SUPABASE_INTEGRATION.md`

---

## 📖 Using API Keys in Code

### Backend (Python)
```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access API keys
hf_token = os.getenv('HF_TOKEN')
render_key = os.getenv('RENDER_API_KEY')
```

### Frontend (Vite/React)
```javascript
// Vite automatically loads VITE_* prefixed variables
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// Note: Only VITE_* prefixed vars are exposed to frontend
```

---

## ⚠️ Important Security Rules

### ✅ **DO**
- ✅ Keep the `.env` file in your local directory
- ✅ Use `VITE_*` prefix for frontend environment variables
- ✅ Use `.env.example` to share configuration structure
- ✅ Rotate keys immediately if compromised
- ✅ Use different keys for development and production

### ❌ **DON'T**
- ❌ Never commit the `.env` file to Git
- ❌ Never share API keys in chat, email, or screenshots
- ❌ Never hardcode API keys in source code
- ❌ Never expose backend-only keys in frontend code
- ❌ Never use production keys in development

---

## 🔄 Key Rotation Guide

If any key is compromised:

### **1. Hugging Face Token**
1. Go to [Hugging Face Settings](https://huggingface.co/settings/tokens)
2. Revoke the compromised token
3. Generate a new token
4. Update `HF_TOKEN` in `.env`

### **2. Render API Key**
1. Go to [Render Account Settings](https://dashboard.render.com/account)
2. Revoke the old key
3. Generate a new API key
4. Update `RENDER_API_KEY` in `.env`

### **3. Supabase Credentials**
1. Go to [Supabase Dashboard](https://supabase.com/dashboard/project/espcjwpddzibctsvtvtz/settings/api)
2. For Anon Key: Reset project keys (affects all users)
3. For Database Password: Update in Database Settings
4. Update `.env` with new credentials

---

## 📊 Environment File Structure

```
VishwaGuru/
├── .env                    # ✅ Real secrets (GITIGNORED)
├── .env.example            # ✅ Safe template (committed to Git)
└── .gitignore              # ✅ Protects .env files
```

---

## 🎯 Quick Commands

```bash
# Verify .env is gitignored
git check-ignore -v .env

# Check what files Git is tracking
git ls-files | grep .env

# View environment variables (without secrets)
cat .env.example
```

---

## 📞 Support & Resources

- **Hugging Face Docs**: https://huggingface.co/docs
- **Render Docs**: https://render.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Your Supabase Dashboard**: https://supabase.com/dashboard/project/espcjwpddzibctsvtvtz

### 📚 Project Documentation
- **MCP Servers Configuration**: See `MCP_SERVERS_CONFIG.md`
- **Supabase Integration**: See `SUPABASE_SETUP.md` and `docs/SUPABASE_INTEGRATION.md`
- **API Keys Reference**: This document

---

## ✅ Configuration Checklist

- [x] Jules AI key configured (Pro subscription)
- [x] Hugging Face token configured
- [x] Render API key configured
- [x] Supabase URL configured
- [x] Supabase Anon Key configured
- [x] All secrets in `.env` (gitignored)
- [x] Template in `.env.example` (safe to commit)
- [ ] Telegram Bot token (update when ready)
- [ ] Google Gemini API key (update when ready)

---

**Last Updated**: 2026-02-16  
**🔒 Security Level**: Protected

Your API keys are secure and ready to use! 🎉
