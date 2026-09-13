import psutil
import platform
import os
import sys

def evaluate_hardware():
    print("=== Hardware Evaluation for AI Models ===")
    
    # OS
    print(f"OS: {platform.system()} {platform.release()}")
    
    # CPU
    cpu_count = psutil.cpu_count(logical=True)
    print(f"CPU Logical Cores: {cpu_count}")
    
    # RAM
    ram = psutil.virtual_memory()
    total_ram_gb = ram.total / (1024 ** 3)
    available_ram_gb = ram.available / (1024 ** 3)
    print(f"Total RAM: {total_ram_gb:.2f} GB")
    print(f"Available RAM: {available_ram_gb:.2f} GB")
    
    # GPU
    has_gpu = False
    try:
        # Try to detect CUDA if torch is installed
        import torch
        if torch.cuda.is_available():
            has_gpu = True
            print(f"GPU Detected: {torch.cuda.get_device_name(0)}")
        else:
            print("GPU Detected: None (CUDA not available)")
    except ImportError:
        print("GPU Detected: None (torch not installed, assuming CPU only)")

    print("\n=== Model Feasibility Analysis ===")
    
    # ColPali / Saul-7B
    print("1. ColPali / Saul-7B (Large Vision-Language Models)")
    if has_gpu:
        print("   -> Feasible if GPU VRAM > 16GB. Local execution recommended.")
    elif total_ram_gb >= 32:
        print("   -> WARNING: CPU-only execution will be extremely slow (minutes per query). NOT RECOMMENDED for synchronous APIs.")
    else:
        print("   -> INFEASIBLE: Insufficient RAM. Will cause OOM.")

    # Surya OCR
    print("\n2. Surya OCR (Line detection & text recognition transformers)")
    if has_gpu:
        print("   -> Feasible. Fast execution.")
    elif cpu_count >= 8 and available_ram_gb > 8:
        print("   -> FEASIBLE ON CPU: Will be slow (10-30s per page). Can be used in background RQ workers. Ensure timeout is generous.")
    else:
        print("   -> WARNING: Marginal for CPU execution. Risk of high latency.")

    # Lightweight NLI (DeBERTa-v3-small)
    print("\n3. Lightweight NLI (e.g. cross-encoder/nli-deberta-v3-small)")
    if cpu_count >= 4 and available_ram_gb > 2:
        print("   -> FEASIBLE ON CPU: Fast enough for CPU inference (1-3s per check). Highly recommended for logical verification fallback.")
    else:
        print("   -> WARNING: Marginal.")

if __name__ == "__main__":
    evaluate_hardware()
