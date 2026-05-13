"""Filesystem and path operations."""

import glob as _glob
import os
import re
import shutil

from .. import op


# Path confinement for write/delete ops. Gemini review #7: previous version
# accepted any absolute path → host-wide read/write if ComfyUI was exposed.
# Default allow-list: ComfyUI input/output/temp + user home. Override with
# the env var UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS=1 for power users.
def _confined_roots() -> list[str]:
    roots: list[str] = []
    try:
        import folder_paths  # type: ignore
        roots.extend([
            folder_paths.get_input_directory(),
            folder_paths.get_output_directory(),
            folder_paths.get_temp_directory(),
        ])
    except Exception:
        # Fallback for non-ComfyUI environments (tests, doc gen)
        roots.extend([
            os.path.abspath("input"),
            os.path.abspath("output"),
            os.path.abspath("temp"),
        ])
    roots.append(os.path.expanduser("~"))
    return [os.path.abspath(r) for r in roots if r]


def _path_is_confined(target: str) -> bool:
    abs_target = os.path.abspath(target)
    for root in _confined_roots():
        try:
            if os.path.commonpath([abs_target, root]) == root:
                return True
        except ValueError:
            continue
    return False


def _require_confined(path: str) -> None:
    if os.environ.get("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS") == "1":
        return
    if not _path_is_confined(path):
        raise PermissionError(
            f"path {path!r} is outside the allow-listed roots "
            f"(ComfyUI input/output/temp, user home). "
            f"Set UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS=1 to override (use with care)."
        )


@op(
    op_id="fs_mkdir",
    display_name="FS Mkdir",
    category="Filesystem",
    input_schema={"required": {
        "path": ("STRING", {"default": ""}),
        "exist_ok": ("BOOLEAN", {"default": True}),
    }},
    output_indices=(0,),
    description="Create directory (recursive). Returns the created path.",
)
def fs_mkdir(self, path, exist_ok=True):
    if not path:
        raise ValueError("path is required")
    _require_confined(path)
    os.makedirs(path, exist_ok=bool(exist_ok))
    return (path,)


@op(
    op_id="fs_exists",
    display_name="FS Exists",
    category="Filesystem",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(1,),
    description="Returns DICT with `is_file`, `is_dir`, `exists`, `size_bytes`.",
)
def fs_exists(self, path):
    info = {"path": path, "exists": False, "is_file": False, "is_dir": False, "size_bytes": 0}
    if path and os.path.exists(path):
        info["exists"] = True
        info["is_file"] = os.path.isfile(path)
        info["is_dir"] = os.path.isdir(path)
        if info["is_file"]:
            info["size_bytes"] = os.path.getsize(path)
    return (info,)


@op(
    op_id="fs_glob",
    display_name="FS Glob",
    category="Filesystem",
    input_schema={"required": {
        "pattern": ("STRING", {"default": ""}),
        "recursive": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(1,),
    description="Returns DICT with `matches` (list) and `count`.",
)
def fs_glob(self, pattern, recursive=False):
    matches = sorted(_glob.glob(pattern, recursive=bool(recursive)))
    return ({"matches": matches, "count": len(matches)},)


@op(
    op_id="fs_copy",
    display_name="FS Copy",
    category="Filesystem",
    input_schema={"required": {
        "src": ("STRING", {"default": ""}),
        "dst": ("STRING", {"default": ""}),
        "overwrite": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(0,),
)
def fs_copy(self, src, dst, overwrite=False):
    if not os.path.isfile(src):
        raise FileNotFoundError(f"source file not found: {src!r}")
    _require_confined(src)
    _require_confined(dst)
    if os.path.exists(dst) and not overwrite:
        raise FileExistsError(f"destination exists and overwrite=False: {dst!r}")
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    shutil.copy2(src, dst)
    return (dst,)


@op(
    op_id="fs_move",
    display_name="FS Move",
    category="Filesystem",
    input_schema={"required": {
        "src": ("STRING", {"default": ""}),
        "dst": ("STRING", {"default": ""}),
        "overwrite": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(0,),
)
def fs_move(self, src, dst, overwrite=False):
    if not os.path.isfile(src):
        raise FileNotFoundError(f"source file not found: {src!r}")
    _require_confined(src)
    _require_confined(dst)
    if os.path.exists(dst) and not overwrite:
        raise FileExistsError(f"destination exists and overwrite=False: {dst!r}")
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    if os.path.exists(dst) and overwrite:
        os.remove(dst)
    shutil.move(src, dst)
    return (dst,)


@op(
    op_id="fs_delete",
    display_name="FS Delete (file)",
    category="Filesystem",
    input_schema={"required": {
        "path": ("STRING", {"default": ""}),
        "missing_ok": ("BOOLEAN", {"default": False}),
    }},
    output_indices=(0,),
    description="Delete a file (not a directory). Use with care.",
)
def fs_delete(self, path, missing_ok=False):
    _require_confined(path)
    if not os.path.exists(path):
        if missing_ok:
            return (path,)
        raise FileNotFoundError(f"path not found: {path!r}")
    if os.path.isdir(path):
        raise IsADirectoryError(f"refusing to delete directory: {path!r} (use a dedicated tool)")
    os.remove(path)
    return (path,)


@op(
    op_id="path_join",
    display_name="Path Join",
    category="Filesystem",
    input_schema={"required": {
        "a": ("STRING", {"default": ""}),
        "b": ("STRING", {"default": ""}),
        "c": ("STRING", {"default": ""}),
    }},
    output_indices=(0,),
)
def path_join(self, a, b, c=""):
    parts = [p for p in (a, b, c) if p]
    return (os.path.join(*parts) if parts else "",)


@op(
    op_id="path_basename",
    display_name="Path Basename",
    category="Filesystem",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def path_basename(self, path):
    return (os.path.basename(path),)


@op(
    op_id="path_dirname",
    display_name="Path Dirname",
    category="Filesystem",
    input_schema={"required": {"path": ("STRING", {"default": ""})}},
    output_indices=(0,),
)
def path_dirname(self, path):
    return (os.path.dirname(path),)


_FILENAME_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@op(
    op_id="path_sanitize_filename",
    display_name="Sanitize Filename",
    category="Filesystem",
    input_schema={"required": {
        "filename": ("STRING", {"default": ""}),
        "replacement": ("STRING", {"default": "_"}),
    }},
    output_indices=(0,),
    description="Replace OS-forbidden filename chars (<>:\"/\\|?*, control chars).",
)
def path_sanitize_filename(self, filename, replacement="_"):
    return (_FILENAME_FORBIDDEN.sub(replacement, filename).strip(" .") or "untitled",)
