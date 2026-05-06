"""System-level operations: monitor RAM/disk, GPU info."""

import os
import shutil

from .. import op


@op(
    op_id="system_stats",
    display_name="System Stats (RAM, disk, GPU)",
    category="System",
    input_schema={"required": {
        "disk_path": ("STRING", {"default": "."}),
    }},
    output_indices=(1,),
    description="Returns DICT with `ram_total_mb`, `ram_avail_mb`, `disk_total_gb`, `disk_free_gb`, `gpu_*` if torch.cuda available.",
)
def system_stats(self, disk_path="."):
    info = {}

    # RAM via psutil if available, else best-effort via os.sysconf or skip.
    try:
        import psutil
        vm = psutil.virtual_memory()
        info["ram_total_mb"] = round(vm.total / (1024 * 1024), 1)
        info["ram_avail_mb"] = round(vm.available / (1024 * 1024), 1)
        info["ram_percent_used"] = vm.percent
    except ImportError:
        info["ram"] = "psutil not installed"

    # Disk
    try:
        usage = shutil.disk_usage(disk_path)
        info["disk_total_gb"] = round(usage.total / (1024 ** 3), 2)
        info["disk_free_gb"] = round(usage.free / (1024 ** 3), 2)
    except OSError as e:
        info["disk_error"] = str(e)

    # GPU via torch
    try:
        import torch
        if torch.cuda.is_available():
            dev = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(dev)
            info["gpu_name"] = props.name
            info["gpu_total_mb"] = round(props.total_memory / (1024 * 1024), 1)
            info["gpu_alloc_mb"] = round(torch.cuda.memory_allocated(dev) / (1024 * 1024), 1)
            info["gpu_reserved_mb"] = round(torch.cuda.memory_reserved(dev) / (1024 * 1024), 1)
        else:
            info["gpu"] = "CUDA not available"
    except (ImportError, RuntimeError) as e:
        info["gpu_error"] = str(e)

    return (info,)
