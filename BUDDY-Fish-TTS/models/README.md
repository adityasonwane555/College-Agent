# 📦 Fish Audio S2 Pro Model Assets

This directory houses the quantized GGUF weights and tokenizer required for running **Fish Audio S2 Pro** locally via `s2.cpp`.

---

## 🔍 Model Information

- **Base Architecture**: Fish Audio S2-Pro (Dual-AR Text-to-Speech & Voice Clone architecture, ~4.56 Billion parameters).
- **Quantization Variant**: `s2-pro-q5_k_m.gguf`
- **File Size**: ~3.8 GB (4,031,183,968 bytes)
- **Hugging Face Repository**: [`rodrigomt/s2-pro-gguf`](https://huggingface.co/rodrigomt/s2-pro-gguf)
- **Inference Runtime**: [`rodrigomatta/s2.cpp`](https://github.com/rodrigomatta/s2.cpp) (Native C++ / GGML engine)
- **Tokenizer**: `tokenizer.json` (~13 MB)

---

## ⚡ Hardware Footprint & Compatibility

- **Target GPU**: NVIDIA GeForce RTX 4060 (8 GB Dedicated VRAM)
- **Target RAM**: 16 GB System Memory
- **Memory Overhead**:
  - Model weights: ~3.8 GB
  - Codec & KV context buffers: ~1.5 - 2.0 GB
  - Total runtime memory: ~5.3 - 5.8 GB
  - **Result**: Fits comfortably within the 8 GB VRAM buffer, leaving safety headroom for Windows desktop compositor and concurrent tasks.

---

## 📜 Licensing & Usage Restrictions

- **Base Model License**: **Fish Audio Research License**
  - **Permitted**: Non-commercial use, research, local evaluation, academic experimentation.
  - **Restricted**: Commercial deployment or monetization requires a commercial agreement from Fish Audio.
- **Inference Engine (`s2.cpp`)**: Apache 2.0 / MIT.
- **Voice Cloning Ethics**: Do not synthesize or clone real individuals' voices without explicit authorization.

---

## 📥 Manual Download Instructions

If you need to download or replace the model manually:

```powershell
# Using Python script
python scripts/download_model.py

# Or directly with curl
curl.exe -L -C - -o models/s2-pro-q5_k_m.gguf "https://huggingface.co/rodrigomt/s2-pro-gguf/resolve/main/s2-pro-q5_k_m.gguf"
```
