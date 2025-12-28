# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod serverless worker that runs Automatic1111 Stable Diffusion WebUI and exposes its API endpoints (txt2img, img2img, LoRA management, options). The project is containerized and designed to run on RunPod's serverless infrastructure.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  RunPod Serverless Event                                │
│  {"input": {"api": "txt2img", "prompt": "..."}}         │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  src/handler.py (RunPod Handler)                        │
│  - Routes requests by 'api' field                       │
│  - Proxies to Automatic1111 WebUI API                   │
│  - Retry logic with exponential backoff                 │
└─────────────────────┬───────────────────────────────────┘
                      │ http://127.0.0.1:3000/sdapi/v1/*
┌─────────────────────▼───────────────────────────────────┐
│  Automatic1111 WebUI (API mode, no web interface)       │
│  - Launched by src/start.sh                             │
│  - Uses tcmalloc for memory optimization                │
└─────────────────────────────────────────────────────────┘
```

## Development Commands

### Build (local development with custom models)
```bash
# Build with default model (sdxl)
docker buildx bake

# Build with specific model
docker buildx bake --set default.args.MODEL_NAME=awportrait_v14

# Available models: awportrait_v14, dreamshaper, dreamshaper_xl, sd15, sdxl
```

### Run Container Locally
```bash
# Run the built image (requires NVIDIA GPU)
docker run --gpus all -p 8000:8000 <image_tag>
```

### Testing
```bash
# Test txt2img endpoint
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input.json

# Test img2img endpoint  
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input_img2img.json

# Test get available LoRAs
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input_loras.json

# Test get/set options
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input_options.json

# Test with LCM LoRA (fast generation)
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input_lora.json

# Test LCM LoRA with img2img
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d @test_input_lora_img2img.json
```

## Configuration

### Docker Build Arguments
- `MODEL_NAME`: Specifies which model directory to use (default: `awportrait_v14`)
- `GIT_VERSION`: Automatic1111 version to use (default: `v1.9.3`)
- `APP_NAME`: Application name for container metadata
- `GIT_REPO_URL`: Automatic1111 repository URL

### Environment Variables
The container sets several environment variables for optimal performance:
- `LD_PRELOAD`: Uses tcmalloc for better memory management
- `PYTHONUNBUFFERED`: Ensures Python output is not buffered
- `DEBIAN_FRONTEND=noninteractive`: Prevents interactive prompts during package installation

## Model Management

Models are organized in the `models/` directory by model name:
```
models/<MODEL_NAME>/
├── ControlNet/       → /stable-diffusion-webui/models/ControlNet/
├── Lora/             → /stable-diffusion-webui/models/Lora/
├── VAE/              → /stable-diffusion-webui/models/VAE/
├── embeddings/       → /stable-diffusion-webui/models/embeddings/
└── model.safetensors → /model.safetensors
```

To add a new model, create a directory under `models/` with the required subdirectories and files.

## API Interface

The service accepts RunPod serverless event format with an `api` field to specify the endpoint:

### Text-to-Image (txt2img)
```json
{
  "input": {
    "api": "txt2img",
    "prompt": "image description, <lora:lcm:1.0>",
    "negative_prompt": "unwanted elements", 
    "width": 512,
    "height": 512,
    "steps": 8,
    "cfg_scale": 2.0,
    "sampler_name": "LCM"
  }
}
```

#### Using LoRA Models
LoRA models can be applied by including them in the prompt with the syntax `<lora:model_name:weight>`:
- `<lora:lcm:1.0>` - Apply LCM LoRA with full strength
- `<lora:lcm:0.8>` - Apply LCM LoRA with 80% strength
- Multiple LoRAs: `<lora:lcm:0.8>, <lora:style:0.6>`

When using LCM LoRA, recommended settings:
- Steps: 4-8 (much faster generation)
- CFG Scale: 1.0-2.0 (lower values work better)
- Sampler: "LCM" for optimal results

### Image-to-Image (img2img)
```json
{
  "input": {
    "api": "img2img",
    "prompt": "modify this image",
    "init_images": ["base64_encoded_image"],
    "denoising_strength": 0.7,
    "width": 512,
    "height": 512,
    "steps": 20,
    "cfg_scale": 7
  }
}
```

### Get Available LoRAs
```json
{
  "input": {
    "api": "getLoras"
  }
}
```

### Get Current Options
```json
{
  "input": {
    "api": "getOptions"
  }
}
```

### Set Options
```json
{
  "input": {
    "api": "setOptions",
    "sd_model_checkpoint": "model.safetensors",
    "CLIP_stop_at_last_layers": 2
  }
}
```

If no `api` field is provided, it defaults to `txt2img` for backward compatibility.