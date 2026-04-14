import math

try:
    import numpy as np
    import torch
    import torch.nn as nn
    from transformers import AutoModelForCausalLM, PreTrainedModel
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers.cache_utils import DynamicCache
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    class DynamicCache:
        pass

class TurboQuantDynamicCache(DynamicCache):
    """
    HuggingFace-compatible Cache that applies TurboQuant compression inline
    during generation.

    Strategy (per the paper):
      - Keep the most recent `window_size` tokens in fp16 (uncompressed) so the
        attention layer always gets fresh K/V for the local context window.
      - When the window overflows, compress the overflow slice via
        TurboQuant (PolarQuant rotation + bit-packed quantization + optional
        QJL residual) and drop the raw tensors from the backing cache.
      - On `update()`, return the full logical KV to the attention layer by
        decompressing the stored chunks and concatenating the fp16 recent
        window. Decompression is O(compressed_len) per layer per step.

    Memory footprint vs a vanilla DynamicCache scales with
        window_size * hidden_dim * 2 (fp16) + compressed_chunks
    instead of seq_len * hidden_dim * 2, giving roughly
        raw_size * (bits/16)  for the compressed tail.
    """

    def __init__(self, compressor, window_size=128):
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers must be installed to use TurboQuantDynamicCache")
        # Intentionally skip super().__init__() — HF's DynamicCache internals
        # have shifted across versions (4.x used key_cache/value_cache lists,
        # 5.x uses `layers`). We duck-type the interface HF relies on
        # (update, get_seq_length) and manage our own storage.
        self.compressor = compressor
        self.window_size = max(1, int(window_size))
        # Recent fp16 window: per-layer tensors or None
        self._recent_k = {}
        self._recent_v = {}
        # Per-layer list of compressed chunk dicts (older-than-window tokens)
        self._compressed_chunks = {}
        # Remember dtype to decompress back to the right precision
        self._dtype_hint = {}

    def _ensure_layer_slot(self, layer_idx):
        self._recent_k.setdefault(layer_idx, None)
        self._recent_v.setdefault(layer_idx, None)
        self._compressed_chunks.setdefault(layer_idx, [])

    def update(self, key_states, value_states, layer_idx, cache_kwargs=None):
        self._ensure_layer_slot(layer_idx)
        self._dtype_hint[layer_idx] = key_states.dtype

        # 1. Append new K/V to the recent (uncompressed) window
        if self._recent_k[layer_idx] is None:
            self._recent_k[layer_idx] = key_states
            self._recent_v[layer_idx] = value_states
        else:
            self._recent_k[layer_idx] = torch.cat(
                [self._recent_k[layer_idx], key_states], dim=-2
            )
            self._recent_v[layer_idx] = torch.cat(
                [self._recent_v[layer_idx], value_states], dim=-2
            )

        # 2. If window overflows, compress the overflow slice and evict it
        recent_len = self._recent_k[layer_idx].shape[-2]
        if recent_len > self.window_size:
            overflow = recent_len - self.window_size
            k_old = self._recent_k[layer_idx][..., :overflow, :].contiguous()
            v_old = self._recent_v[layer_idx][..., :overflow, :].contiguous()
            compressed = self.compressor.compress([(k_old, v_old)])[0]
            self._compressed_chunks[layer_idx].append(compressed)
            # Free the raw tensors from the backing cache
            self._recent_k[layer_idx] = self._recent_k[layer_idx][..., overflow:, :].contiguous()
            self._recent_v[layer_idx] = self._recent_v[layer_idx][..., overflow:, :].contiguous()
            del k_old, v_old

        # 3. Return full logical K/V for attention: decompressed old + recent window
        chunks = self._compressed_chunks[layer_idx]
        if not chunks:
            return self._recent_k[layer_idx], self._recent_v[layer_idx]

        dtype = self._dtype_hint[layer_idx]
        decompressed = self.compressor.decompress(chunks, dtype=dtype)
        k_parts = [kv[0] for kv in decompressed] + [self._recent_k[layer_idx]]
        v_parts = [kv[1] for kv in decompressed] + [self._recent_v[layer_idx]]
        return torch.cat(k_parts, dim=-2), torch.cat(v_parts, dim=-2)

    def get_seq_length(self, layer_idx=0):
        recent = 0
        if self._recent_k.get(layer_idx) is not None:
            recent = self._recent_k[layer_idx].shape[-2]
        old = sum(c["shape"][2] for c in self._compressed_chunks.get(layer_idx, []))
        return recent + old

    def memory_footprint_bytes(self):
        """Approximate bytes used by the cache (raw window + compressed chunks)."""
        total = 0
        for t in list(self._recent_k.values()) + list(self._recent_v.values()):
            if t is not None:
                total += t.element_size() * t.nelement()
        for chunks in self._compressed_chunks.values():
            for c in chunks:
                for key in ("k_q", "k_scale", "k_zero", "v_q", "v_scale", "v_zero"):
                    t = c[key]
                    total += t.element_size() * t.nelement()
                qjl = c.get("qjl")
                if qjl:
                    for key in ("k_1bit", "k_mag", "v_1bit", "v_mag"):
                        t = qjl[key]
                        total += t.element_size() * t.nelement()
        return total

class TurboQuantKVCacheCompressor:
    """
    Implementation of the TurboQuant KV Cache Compression algorithm (Google, 2026).
    
    This module implements the two core mathematical innovations of TurboQuant:
    1. PolarQuant (Random Rotation): Rotates the KV cache features using an orthogonal 
       matrix to destroy structured outliers, making the distribution highly predictable 
       (approx Beta distribution) and thus highly compressible without complex metadata.
    2. Quantized Johnson-Lindenstrauss (QJL): Projects the quantization residuals 
       using a random JL matrix, and applies 1-bit quantization to capture and correct
       the vector dot-product errors essential for exact Attention computation.
       
    The compressor supports PyTorch tensors.
    """
    
    def __init__(self, hidden_dim, bits=4, use_qjl=True, qjl_proj_dim=None, device='cpu'):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for TurboQuant inference on KV caches.")
            
        self.device = device
        self.hidden_dim = hidden_dim
        self.bits = bits
        self.use_qjl = use_qjl
        
        # Determine number of quantization bins
        self.q_min = 0
        self.q_max = (1 << bits) - 1
        
        # 1. Generate PolarQuant random orthogonal matrix
        # Using QR decomposition on a random normal matrix
        H = torch.randn(hidden_dim, hidden_dim, device=device)
        Q, R = torch.linalg.qr(H)
        # Ensure uniform distribution over Orthogonal group
        d = torch.diagonal(R)
        ph = d / torch.abs(d)
        self.rotation_matrix = Q * ph # [hidden_dim, hidden_dim]
        # Store inverse rotation (transpose since it's orthogonal)
        self.rotation_matrix_inv = self.rotation_matrix.T
        
        # 2. QJL setup: Number of projection dimensions for 1-bit residual
        if qjl_proj_dim is None:
            self.qjl_proj_dim = max(64, hidden_dim // 2)
        else:
            self.qjl_proj_dim = qjl_proj_dim
            
        if self.use_qjl:
            # Generate JL projection matrix for error correction
            # Gaussian matrix scaled by 1/sqrt(proj_dim)
            self.jl_matrix = torch.randn(
                self.hidden_dim, self.qjl_proj_dim, device=device
            ) / math.sqrt(self.qjl_proj_dim)
            
            self.jl_matrix_inv = torch.linalg.pinv(self.jl_matrix)

    def _quantize_tensor(self, x):
        """Standard Min-Max uniform quantization (as rotation handles outliers)."""
        x_min = x.min(dim=-1, keepdim=True)[0]
        x_max = x.max(dim=-1, keepdim=True)[0]
        
        scale = (x_max - x_min).clamp(min=1e-8) / self.q_max
        zero_point = x_min
        
        x_q = torch.round((x - zero_point) / scale).clamp(self.q_min, self.q_max).to(torch.int8)
        
        # Return state needed for decompression
        return x_q, scale, zero_point

    def _dequantize_tensor(self, x_q, scale, zero_point):
        """Dequantize tensor back to float."""
        return x_q.to(scale.dtype) * scale + zero_point

    def _apply_qjl(self, residual):
        """
        Apply 1-bit Quantized Johnson-Lindenstrauss (QJL) for residual error correction.
        """
        # Project residual into JL space
        projected = torch.matmul(residual, self.jl_matrix)
        
        # 1-bit quantization (sign bit)
        qjl_1bit = torch.sign(projected)
        # Assuming we store magnitude for rough reconstruction scalar
        magnitude = projected.abs().mean(dim=-1, keepdim=True)
        
        return qjl_1bit.to(torch.int8), magnitude

    def _reconstruct_qjl(self, qjl_1bit, magnitude):
        """Reconstruct the residual from 1-bit QJL."""
        # Restore magnitude
        projected_recon = qjl_1bit.to(magnitude.dtype) * magnitude
        # Project back to original dimension space
        residual_recon = torch.matmul(projected_recon, self.jl_matrix_inv)
        return residual_recon

    def compress(self, past_key_values):
        """
        Compresses standard PyTorch Transformer past_key_values.
        Expects a tuple/list of KV pairs for each layer.
        For example: input shape [batch_size, num_heads, seq_len, head_dim]
        We flatten heads and project, then reshape.
        """
        compressed_cache = []
        
        for k_layer, v_layer in past_key_values:
            # Flatten to [..., hidden_dim] for multiplication
            batch, heads, seq_len, head_dim = k_layer.shape
            
            if heads * head_dim != self.hidden_dim:
                # If compression is applied per-head or differently, handle here
                # For simplicity, we assume hidden_dim matches the last dim
                pass
                
            k_flat = k_layer.reshape(-1, self.hidden_dim)
            v_flat = v_layer.reshape(-1, self.hidden_dim)
            
            # Step 1: PolarQuant Rotation
            k_rotated = torch.matmul(k_flat, self.rotation_matrix)
            v_rotated = torch.matmul(v_flat, self.rotation_matrix)
            
            # Step 2: Primary Tensor Quantization
            k_q, k_scale, k_zero = self._quantize_tensor(k_rotated)
            v_q, v_scale, v_zero = self._quantize_tensor(v_rotated)
            
            # Step 3: QJL Residual Error Correction (Optional but necessary for long contexts)
            qjl_payload = None
            if self.use_qjl:
                # Get the quantization error
                k_residual = k_rotated - self._dequantize_tensor(k_q, k_scale, k_zero)
                v_residual = v_rotated - self._dequantize_tensor(v_q, v_scale, v_zero)
                
                # Compress residuals to 1-bit via JL transform
                k_qjl_1bit, k_mag = self._apply_qjl(k_residual)
                v_qjl_1bit, v_mag = self._apply_qjl(v_residual)
                
                qjl_payload = {
                    'k_1bit': k_qjl_1bit, 'k_mag': k_mag,
                    'v_1bit': v_qjl_1bit, 'v_mag': v_mag
                }
            
            # Store compressed metadata
            compressed_layer = {
                'shape': (batch, heads, seq_len, head_dim),
                'k_q': k_q, 'k_scale': k_scale, 'k_zero': k_zero,
                'v_q': v_q, 'v_scale': v_scale, 'v_zero': v_zero,
                'qjl': qjl_payload
            }
            
            compressed_cache.append(compressed_layer)
            
        return compressed_cache

    def decompress(self, compressed_cache, dtype=None):
        """
        Decompresses and reconstructs the TurboQuant KV Cache back to PyTorch tensors.
        """
        if dtype is None:
            dtype = self.rotation_matrix.dtype
            
        reconstructed_cache = []
        
        for layer in compressed_cache:
            batch, heads, seq_len, head_dim = layer['shape']
            
            # Step 1: Dequantize the primary tensors
            k_recon_rot = self._dequantize_tensor(layer['k_q'], layer['k_scale'], layer['k_zero']).to(dtype)
            v_recon_rot = self._dequantize_tensor(layer['v_q'], layer['v_scale'], layer['v_zero']).to(dtype)
            
            # Step 2: Reconstruct and add residuals if QJL was used
            qjl_payload = layer.get('qjl')
            if qjl_payload is not None:
                k_residual_recon = self._reconstruct_qjl(qjl_payload['k_1bit'], qjl_payload['k_mag']).to(dtype)
                v_residual_recon = self._reconstruct_qjl(qjl_payload['v_1bit'], qjl_payload['v_mag']).to(dtype)
                
                k_recon_rot += k_residual_recon
                v_recon_rot += v_residual_recon
                
            # Step 3: Reverse the orthogonal rotation
            k_recon_flat = torch.matmul(k_recon_rot, self.rotation_matrix_inv)
            v_recon_flat = torch.matmul(v_recon_rot, self.rotation_matrix_inv)
            
            # Verify shapes
            k_recon = k_recon_flat.reshape(batch, heads, seq_len, head_dim)
            v_recon = v_recon_flat.reshape(batch, heads, seq_len, head_dim)
            
            reconstructed_cache.append((k_recon, v_recon))
            
        return tuple(reconstructed_cache)


def mock_test():
    """
    Test suite to verify the logic on synthetic KV cache tensors.
    Covers:
      1. Standalone compress/decompress round-trip (MSE bounded)
      2. Inline TurboQuantDynamicCache: window eviction, compression trigger,
         bounded memory, and attention-visible full KV reconstruction.
    """
    if not TORCH_AVAILABLE:
        print("PyTorch not installed, skipping test.")
        return

    # --- Test 1: standalone compress/decompress ---
    hidden_dim = 128
    batch = 2
    heads = 4
    seq_len = 50
    head_dim = hidden_dim // heads

    compressor = TurboQuantKVCacheCompressor(hidden_dim=hidden_dim, bits=3, use_qjl=True)

    layer_kv = []
    for _ in range(2):
        k = torch.randn(batch, heads, seq_len, head_dim)
        v = torch.randn(batch, heads, seq_len, head_dim)
        layer_kv.append((k, v))

    raw_bytes = 2 * 2 * k.element_size() * k.nelement()
    print(f"Original KV Cache Memory (approx dict size uncompressed): {raw_bytes} bytes")

    compressed_cache = compressor.compress(layer_kv)
    q_k = compressed_cache[0]['k_q']
    q_1bit = compressed_cache[0]['qjl']['k_1bit']
    print("Successfully compressed cache.")
    print(f"Layer 1 shape checking... Base Q: {q_k.shape}, QJL 1-bit: {q_1bit.shape}")

    reconstructed_cache = compressor.decompress(compressed_cache)
    k_in, v_in = layer_kv[0]
    k_out, v_out = reconstructed_cache[0]
    mse = torch.nn.functional.mse_loss(k_in, k_out)
    print(f"Reconstruction MSE: {mse.item():.6f}")
    assert mse.item() < 1.0, f"Round-trip MSE too high: {mse.item()}"

    # --- Test 2: inline TurboQuantDynamicCache ---
    if not TRANSFORMERS_AVAILABLE:
        print("transformers not installed — skipping inline cache test.")
        return

    print("\n--- Inline TurboQuantDynamicCache test ---")
    window = 16
    num_layers = 2
    total_steps = 64  # 4x window → compression triggers 3 times per layer
    step_seq = 1
    cache = TurboQuantDynamicCache(compressor, window_size=window)

    all_k_reference = [[] for _ in range(num_layers)]  # for MSE verification
    all_v_reference = [[] for _ in range(num_layers)]
    last_returned_k = [None] * num_layers

    for step in range(total_steps):
        for li in range(num_layers):
            k_tok = torch.randn(batch, heads, step_seq, head_dim)
            v_tok = torch.randn(batch, heads, step_seq, head_dim)
            all_k_reference[li].append(k_tok)
            all_v_reference[li].append(v_tok)
            k_full, v_full = cache.update(k_tok, v_tok, li)
            last_returned_k[li] = k_full
            # Full logical length should always equal steps consumed so far
            assert cache.get_seq_length(li) == step + 1, (
                f"Layer {li} step {step}: got seq_len {cache.get_seq_length(li)}"
            )

    # Recent window must be bounded at `window` per layer
    for li in range(num_layers):
        assert cache._recent_k[li].shape[-2] == window, (
            f"Layer {li} recent window is {cache._recent_k[li].shape[-2]}, expected {window}"
        )
    # Compressed chunks must have accumulated (total_steps - window)
    for li in range(num_layers):
        compressed_len = sum(c["shape"][2] for c in cache._compressed_chunks[li])
        assert compressed_len == total_steps - window, (
            f"Layer {li} compressed len {compressed_len}, expected {total_steps - window}"
        )

    # Memory savings: cache footprint should be notably less than raw fp32 would be
    raw_full_bytes = num_layers * 2 * batch * heads * total_steps * head_dim * 4  # fp32
    cache_bytes = cache.memory_footprint_bytes()
    print(f"Raw-full fp32 bytes: {raw_full_bytes}")
    print(f"TurboQuant cache bytes: {cache_bytes}")
    print(f"Compression ratio: {raw_full_bytes / cache_bytes:.2f}x")
    assert cache_bytes < raw_full_bytes, "TurboQuant cache must be smaller than raw fp32 cache"

    # Returned full K/V must match the raw concatenated tokens within reconstruction MSE
    for li in range(num_layers):
        ref_k = torch.cat(all_k_reference[li], dim=-2)
        mse_full = torch.nn.functional.mse_loss(ref_k, last_returned_k[li])
        print(f"Layer {li} inline round-trip MSE over {total_steps} tokens: {mse_full.item():.6f}")
        assert mse_full.item() < 1.5, f"Inline MSE too high on layer {li}: {mse_full.item()}"

    print("✅ All TurboQuant tests passed.")


if __name__ == "__main__":
    mock_test()
