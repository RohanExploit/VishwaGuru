# Local Machine Learning Model Implementation

## Issue #76: Create a Local Machine Learning model

This document describes the implementation of a local ML model to replace the Hugging Face API dependency for image classification tasks.

## Overview

VishwaGuru now supports **local machine learning inference** for civic issue detection, eliminating the dependency on Hugging Face's external API. This provides:

- ✅ **Offline Capability**: Detection works without internet connectivity
- ✅ **Reduced Latency**: No network round-trips to external APIs
- ✅ **No Rate Limits**: Unlimited local inference
- ✅ **Privacy**: Images are processed locally
- ✅ **Cost Savings**: No API usage fees

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Unified Detection Service                       │
│  ┌─────────────────┐              ┌─────────────────┐           │
│  │  Local ML Model │  ◄─ AUTO ─►  │  HF API Fallback │           │
│  │  (CLIP-based)   │              │  (Original impl) │           │
│  └─────────────────┘              └─────────────────┘           │
│         ▲                                  ▲                     │
│         │                                  │                     │
│  ┌──────┴──────────────────────────────────┴──────┐             │
│  │           Detection Endpoints                   │             │
│  │  • /api/detect-vandalism                       │             │
│  │  • /api/detect-infrastructure                  │             │
│  │  • /api/detect-flooding                        │             │
│  └─────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. `local_ml_service.py`

Core local ML service with:

- **LocalCLIPModel**: Thread-safe singleton wrapper for CLIP model
- **Lazy Loading**: Model loads on first use, not at startup
- **Optional Quantization**: INT8 quantization for reduced memory
- **Detection Functions**:
  - `detect_vandalism_local()` - Graffiti, spray paint, vandalism
  - `detect_infrastructure_local()` - Broken streetlights, damaged signs
  - `detect_flooding_local()` - Flooded streets, waterlogging

### 2. `unified_detection_service.py`

Smart routing layer that:

- Uses local model by default
- Falls back to HF API on failure (configurable)
- Provides consistent interface for all detection types
- Includes health check and status endpoints

### 3. Updated `main.py`

- New endpoint: `GET /api/ml-status` - Check ML service status
- Updated detection endpoints to use unified service

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_LOCAL_ML` | `true` | Enable local ML model |
| `ENABLE_HF_FALLBACK` | `true` | Fall back to HF API on local failure |
| `LOCAL_ML_DEVICE` | `cpu` | Device for inference (`cpu` or `cuda`) |
| `LOCAL_ML_QUANTIZE` | `false` | Enable INT8 quantization |
| `LOCAL_CLIP_MODEL` | `openai/clip-vit-base-patch32` | CLIP model to use |

### Example `.env`

```bash
# Local ML Configuration
USE_LOCAL_ML=true
ENABLE_HF_FALLBACK=true
LOCAL_ML_DEVICE=cpu
LOCAL_ML_QUANTIZE=false
LOCAL_CLIP_MODEL=openai/clip-vit-base-patch32
```

## Installation

### New Dependencies

```txt
torch
transformers
Pillow
```

### Install Command

```bash
cd backend
pip install -r requirements.txt
```

## API Reference

### Check ML Status

```bash
GET /api/ml-status
```

**Response:**
```json
{
  "status": "ok",
  "ml_service": {
    "use_local_model": true,
    "enable_hf_fallback": true,
    "local_backend": {
      "available": true,
      "status": "ready",
      "details": {
        "model_name": "openai/clip-vit-base-patch32",
        "is_available": true,
        "device": "cpu",
        "quantization_enabled": false,
        "error": null
      }
    },
    "huggingface_backend": {
      "available": true,
      "status": "ready"
    },
    "active_backend": "local"
  }
}
```

### Detection Endpoints

All detection endpoints work the same way:

```bash
POST /api/detect-vandalism
POST /api/detect-infrastructure
POST /api/detect-flooding
```

**Request:** Multipart form with `image` file

**Response:**
```json
{
  "detections": [
    {
      "label": "graffiti",
      "confidence": 0.85,
      "box": []
    }
  ]
}
```

## Model Details

### CLIP (Contrastive Language-Image Pre-training)

We use OpenAI's CLIP model for zero-shot image classification:

- **Model**: `openai/clip-vit-base-patch32`
- **Vision Encoder**: ViT-B/32 (Vision Transformer)
- **Text Encoder**: 63M parameter Transformer
- **Image Size**: 224x224 pixels
- **Inference**: ~50-100ms on CPU, ~10-20ms on GPU

### Classification Labels

**Vandalism Detection:**
- graffiti, vandalism, spray paint, street art
- clean wall, public property, normal street

**Infrastructure Detection:**
- broken streetlight, damaged traffic sign
- fallen tree, damaged fence, pothole
- clean street, normal infrastructure

**Flooding Detection:**
- flooded street, waterlogging
- blocked drain, heavy rain
- dry street, normal road

## Performance Optimization

### 1. Lazy Loading
Model loads on first request, not at startup:
```python
def get_model():
    global _model
    if _model is None:
        _model = load_model()  # First call loads model
    return _model
```

### 2. INT8 Quantization (Optional)
Enable for 2-4x memory reduction:
```bash
LOCAL_ML_QUANTIZE=true
```

### 3. GPU Acceleration
Enable CUDA for faster inference:
```bash
LOCAL_ML_DEVICE=cuda
```

### 4. Model Caching
Models are cached locally after first download:
- Location: `~/.cache/huggingface/hub/`
- Size: ~350MB for CLIP ViT-B/32

## Testing

```bash
cd tests
pytest test_local_ml_service.py -v
```

### Test Coverage

- Singleton pattern verification
- Model loading and initialization
- Detection function outputs
- Environment configuration
- API endpoint integration

## Migration Guide

### From HF API to Local Model

1. **Update dependencies:**
   ```bash
   pip install torch transformers
   ```

2. **Set environment variables:**
   ```bash
   export USE_LOCAL_ML=true
   ```

3. **Restart the server:**
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. **Verify status:**
   ```bash
   curl http://localhost:8000/api/ml-status
   ```

### Rollback to HF API

```bash
export USE_LOCAL_ML=false
export ENABLE_HF_FALLBACK=true
```

## Troubleshooting

### Common Issues

1. **"Missing dependency" error**
   ```bash
   pip install torch transformers
   ```

2. **Out of memory**
   - Enable quantization: `LOCAL_ML_QUANTIZE=true`
   - Use smaller model: `LOCAL_CLIP_MODEL=openai/clip-vit-base-patch16`

3. **Slow first request**
   - Normal behavior - model downloads and loads on first use
   - Subsequent requests are fast

4. **Model not available**
   - Check `/api/ml-status` for error details
   - Falls back to HF API if `ENABLE_HF_FALLBACK=true`

## Future Improvements

- [ ] Add batch inference support
- [ ] Implement model warm-up at startup
- [ ] Add ONNX runtime for faster CPU inference
- [ ] Support custom fine-tuned models
- [ ] Add model versioning and updates

## Contributors

- Implementation: Issue #76
- Local ML Model Development
- Model Optimization & Integration
