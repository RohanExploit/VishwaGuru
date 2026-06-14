# 🔌 MCP Servers Configuration

## Overview

This document contains **MCP (Model Context Protocol)** server configurations for various services used in the VishwaGuru project.

MCP servers provide standardized interfaces to interact with external services and AI models.

---

## 📋 Available MCP Servers

### 1. **Hugging Face MCP Server**

**Configuration:**
```json
{
  "mcpServers": {
    "hf-mcp-server": {
      "url": "https://huggingface.co/mcp?login"
    }
  }
}
```

**Purpose:**
- Access Hugging Face models via MCP protocol
- Unified interface for model inference
- Authentication via login flow

**Authentication:**
- Uses your `HF_TOKEN` from `.env` file
- Token: Configured in `.env` (see `.env.example` for setup)

**Use Cases:**
- Model inference and generation
- Access to Hugging Face Hub models
- Fine-tuned model deployment
- Model discovery and metadata

---

### 2. **Supabase MCP Server**

**Configuration:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz"
    }
  }
}
```

**Purpose:**
- Database operations via MCP
- Real-time subscriptions
- Authentication management
- Storage operations

**Project Details:**
- Project Reference: `espcjwpddzibctsvtvtz`
- Project URL: `https://espcjwpddzibctsvtvtz.supabase.co`
- Anon Key: Configured in `.env`

**Use Cases:**
- Database CRUD operations
- User authentication
- File storage management
- Real-time data synchronization

---

## 🔧 Combined MCP Configuration

For tools that support multiple MCP servers, use this combined configuration:

```json
{
  "mcpServers": {
    "hf-mcp-server": {
      "url": "https://huggingface.co/mcp?login"
    },
    "supabase": {
      "url": "https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz"
    }
  }
}
```

---

## 📖 Usage Examples

### Hugging Face MCP Server

```javascript
// Example: Using HF MCP server for text generation
const response = await mcpClient.request('hf-mcp-server', {
  model: 'meta-llama/Llama-2-7b-chat-hf',
  prompt: 'Explain quantum computing',
  max_tokens: 500
});
```

### Supabase MCP Server

```javascript
// Example: Using Supabase MCP server for database query
const response = await mcpClient.request('supabase', {
  table: 'civic_reports',
  operation: 'select',
  filter: { status: 'pending' }
});
```

---

## 🔐 Security Considerations

### ✅ **Safe to Use**
- MCP server URLs are public endpoints
- Authentication happens via API keys stored in `.env`
- MCP protocol handles secure token transmission

### ⚠️ **Important**
- Never hardcode API keys in MCP configurations
- Always use environment variables for authentication
- MCP servers should validate tokens server-side

---

## 🚀 Integration with VishwaGuru

### Backend (Python)
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Hugging Face via MCP
hf_mcp_config = {
    "url": "https://huggingface.co/mcp?login",
    "token": os.getenv('HF_TOKEN')
}

# Supabase via MCP
supabase_mcp_config = {
    "url": f"https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz",
    "anon_key": os.getenv('VITE_SUPABASE_ANON_KEY')
}
```

### Frontend (JavaScript)
```javascript
// Supabase MCP is primarily for server-side tools
// Frontend should use the regular Supabase JS client
import { supabase } from './lib/supabase';
```

---

## 🔗 Related Documentation

- **API Keys**: See `API_KEYS_REFERENCE.md`
- **Supabase Setup**: See `SUPABASE_SETUP.md`
- **Supabase Integration**: See `docs/SUPABASE_INTEGRATION.md`
- **Environment Setup**: See `.env.example`

---

## 📚 External Resources

### Hugging Face
- [Hugging Face Hub](https://huggingface.co)
- [HF Models Documentation](https://huggingface.co/docs/hub/models)
- [HF Inference API](https://huggingface.co/docs/api-inference)

### Supabase
- [Supabase Dashboard](https://supabase.com/dashboard/project/espcjwpddzibctsvtvtz)
- [Supabase MCP Documentation](https://supabase.com/docs/guides/mcp)
- [MCP Protocol Spec](https://modelcontextprotocol.io)

---

## 🛠️ Configuration File Locations

Different tools may require MCP configurations in different locations:

### VS Code / IDEs
```json
// settings.json or workspace configuration
{
  "mcp": {
    "servers": {
      "hf-mcp-server": {
        "url": "https://huggingface.co/mcp?login"
      },
      "supabase": {
        "url": "https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz"
      }
    }
  }
}
```

### AI Development Tools
```json
// .mcprc or mcp.json
{
  "mcpServers": {
    "hf-mcp-server": {
      "url": "https://huggingface.co/mcp?login"
    },
    "supabase": {
      "url": "https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz"
    }
  }
}
```

---

## ✅ MCP Server Status

| Server | Status | Purpose | Authentication |
|--------|--------|---------|----------------|
| **Hugging Face** | ✅ Configured | AI Models | HF_TOKEN |
| **Supabase** | ✅ Configured | Database | Anon Key |

---

## 🎯 Quick Reference

**Hugging Face MCP:**
- URL: `https://huggingface.co/mcp?login`
- Token: In `.env` as `HF_TOKEN`
- Use for: Model inference, training, deployments

**Supabase MCP:**
- URL: `https://mcp.supabase.com/mcp?project_ref=espcjwpddzibctsvtvtz`
- Keys: In `.env` as `VITE_SUPABASE_*`
- Use for: Database, auth, storage, real-time

---

**Last Updated**: 2026-02-16  
**MCP Protocol Version**: Latest

Your MCP servers are configured and ready to use! 🚀
