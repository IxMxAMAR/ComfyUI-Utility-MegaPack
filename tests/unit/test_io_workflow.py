"""Tests for IOWorkflowNode."""

import json
import os
from unittest.mock import patch, MagicMock

import pytest
import torch
from PIL import Image

from mp_nodes.io_workflow import IOWorkflowNode


def run(mode, **kwargs):
    return IOWorkflowNode().process(mode=mode, theme="(use pack default)", **kwargs)


@pytest.fixture(autouse=True)
def _allow_tmp_paths(monkeypatch):
    """Tests use pytest's tmp_path which is outside the allow-listed roots.
    Opt out of fs confinement for tests; one targeted test below verifies
    the confinement actually blocks paths when the env var is unset."""
    monkeypatch.setenv("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS", "1")


# -----------------------
# Filesystem
# -----------------------
class TestFilesystem:
    def test_mkdir(self, tmp_path):
        out = run("fs_mkdir", path=str(tmp_path / "newdir"))
        assert os.path.isdir(out[0])

    def test_exists_file(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("hi")
        info = run("fs_exists", path=str(f))[1]
        assert info["exists"] is True
        assert info["is_file"] is True
        assert info["size_bytes"] == 2

    def test_exists_missing(self):
        info = run("fs_exists", path="/no/such/path")[1]
        assert info["exists"] is False

    def test_glob(self, tmp_path):
        for n in ("a.txt", "b.txt", "c.md"):
            (tmp_path / n).write_text("")
        info = run("fs_glob", pattern=str(tmp_path / "*.txt"))[1]
        assert info["count"] == 2

    def test_copy(self, tmp_path):
        src = tmp_path / "src.txt"
        src.write_text("hello")
        dst = tmp_path / "dst.txt"
        out = run("fs_copy", src=str(src), dst=str(dst), overwrite=False)[0]
        assert os.path.isfile(out)
        assert dst.read_text() == "hello"

    def test_copy_existing_no_overwrite_raises(self, tmp_path):
        src = tmp_path / "s.txt"; src.write_text("x")
        dst = tmp_path / "d.txt"; dst.write_text("y")
        with pytest.raises(RuntimeError, match="exists"):
            run("fs_copy", src=str(src), dst=str(dst), overwrite=False)

    def test_move(self, tmp_path):
        src = tmp_path / "src.txt"; src.write_text("hi")
        dst = tmp_path / "dst.txt"
        run("fs_move", src=str(src), dst=str(dst), overwrite=False)
        assert not src.exists()
        assert dst.read_text() == "hi"

    def test_delete(self, tmp_path):
        f = tmp_path / "del.txt"; f.write_text("x")
        run("fs_delete", path=str(f), missing_ok=False)
        assert not f.exists()

    def test_delete_dir_refuses(self, tmp_path):
        with pytest.raises(RuntimeError):
            run("fs_delete", path=str(tmp_path), missing_ok=False)

    def test_path_join(self):
        out = run("path_join", a="a", b="b", c="c.txt")[0]
        assert out == os.path.join("a", "b", "c.txt")

    def test_path_basename(self):
        assert run("path_basename", path="/foo/bar/baz.txt")[0] == "baz.txt"

    def test_path_dirname(self):
        assert run("path_dirname", path="/foo/bar/baz.txt")[0] == "/foo/bar"

    def test_sanitize_filename(self):
        assert run("path_sanitize_filename", filename='bad:name?<file>.txt', replacement="_")[0] == "bad_name__file_.txt"


class TestFilesystemConfinement:
    """When UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS is unset, fs ops reject
    paths outside the allow-list (ComfyUI input/output/temp + user home).
    This blocks the v0.1.0/0.1.1 vulnerability where a network-exposed
    ComfyUI could touch arbitrary files (Gemini review #7).

    These tests pin the allow-list to a known-narrow directory via monkeypatch
    so we can test against paths that are definitely outside it, independent
    of where the test runner's tmp_path or HOME actually live.
    """

    @pytest.fixture(autouse=True)
    def _isolated_confinement(self, monkeypatch, tmp_path):
        from mp_nodes.io_workflow.operations import filesystem as fs_mod
        # Allow only this temp dir — everything else is outside
        allowed = str(tmp_path / "allowed")
        os.makedirs(allowed, exist_ok=True)
        monkeypatch.setattr(fs_mod, "_confined_roots", lambda: [allowed])
        monkeypatch.delenv("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS", raising=False)
        self._allowed = allowed
        self._outside = str(tmp_path / "outside" / "should_fail")

    def test_mkdir_outside_allow_list_rejected(self):
        with pytest.raises(RuntimeError, match="outside the allow-listed roots"):
            run("fs_mkdir", path=self._outside)

    def test_delete_outside_allow_list_rejected(self):
        with pytest.raises(RuntimeError, match="outside the allow-listed roots"):
            run("fs_delete", path=self._outside, missing_ok=True)

    def test_inside_allowed_root_succeeds(self):
        out = run("fs_mkdir", path=os.path.join(self._allowed, "subdir"))
        assert os.path.isdir(out[0])

    def test_env_var_override_disables_confinement(self, monkeypatch):
        monkeypatch.setenv("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS", "1")
        out = run("fs_mkdir", path=self._outside)
        assert os.path.isdir(out[0])


# -----------------------
# Network (mocked)
# -----------------------
class TestNetwork:
    def test_http_get_returns_text_and_status(self):
        mock_resp = MagicMock()
        mock_resp.iter_content = lambda chunk_size: [b'{"hello": "world"}']
        mock_resp.encoding = "utf-8"
        mock_resp.status_code = 200
        with patch("mp_nodes.io_workflow.operations.network.requests.get", return_value=mock_resp):
            out = run("http_get", url="http://example.com")
        # RETURN_TYPES is (STRING, DICT, IMAGE, INT)
        assert out[0] == '{"hello": "world"}'
        assert out[1] == {"hello": "world"}
        assert out[3] == 200

    def test_http_post_with_body(self):
        mock_resp = MagicMock()
        mock_resp.iter_content = lambda chunk_size: [b'{"ok": true}']
        mock_resp.encoding = "utf-8"
        mock_resp.status_code = 201
        with patch("mp_nodes.io_workflow.operations.network.requests.post", return_value=mock_resp):
            out = run("http_post", url="http://example.com",
                      body_json='{"a": 1}', timeout_seconds=5)
        assert out[3] == 201
        assert out[1] == {"ok": True}

    def test_http_post_enforces_size_cap(self):
        """Verify streaming enforcement: a giant response must error before fully buffering."""
        from mp_nodes.io_workflow.operations.network import _MAX_RESPONSE_BYTES
        big_chunk = b"x" * (_MAX_RESPONSE_BYTES + 1)
        mock_resp = MagicMock()
        mock_resp.iter_content = lambda chunk_size: [big_chunk]
        mock_resp.encoding = "utf-8"
        mock_resp.status_code = 200
        with patch("mp_nodes.io_workflow.operations.network.requests.post", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="exceeded"):
                run("http_post", url="http://example.com", body_json="{}", timeout_seconds=5)


# -----------------------
# Workflow
# -----------------------
class TestWorkflow:
    def test_filename_format(self):
        out = run("filename_format",
                  template="{seed}_{prompt_slug}.{ext}",
                  seed=42, prompt="A red car", extension="png")[0]
        assert out == "42_a-red-car.png"

    def test_save_image_with_manifest(self, tmp_path):
        img = torch.zeros((1, 4, 4, 3))
        path = run("save_image_with_manifest",
                   image=img, output_dir=str(tmp_path),
                   filename="test.png", manifest_json='{"seed": 7}')[0]
        assert os.path.isfile(path)
        sidecar = os.path.splitext(path)[0] + ".json"
        assert os.path.isfile(sidecar)
        manifest = json.loads(open(sidecar).read())
        assert manifest["seed"] == 7

    def test_notify_console_writes_to_stderr(self, capsys):
        run("notify_console", label="TEST", message="hello")
        captured = capsys.readouterr()
        assert "[TEST] hello" in captured.err

    def test_workflow_stop_when_true_raises(self):
        with pytest.raises(RuntimeError, match="bad"):
            run("workflow_stop", condition=True, message="bad")

    def test_workflow_stop_when_false_passes(self):
        out = run("workflow_stop", condition=False, message="not raised")[0]
        assert out == ""

    def test_workflow_assert_passes(self):
        assert run("workflow_assert", condition=True, message="ok")[0] == "ok"

    def test_workflow_assert_fails(self):
        with pytest.raises(RuntimeError, match="boom"):
            run("workflow_assert", condition=False, message="boom")

    def test_sweep_param(self):
        out = run("sweep_param", start=0.0, stop=1.0, step=0.25)[1]
        assert out["values"] == [0.0, 0.25, 0.5, 0.75, 1.0]
        assert out["count"] == 5

    def test_watch_folder_returns_newest(self, tmp_path):
        import time
        for i, name in enumerate(["a.png", "b.png"]):
            Image.new("RGB", (4, 4)).save(tmp_path / name)
            time.sleep(0.02)
        out = run("watch_folder_next", folder=str(tmp_path), wait_seconds=0.0)[0]
        assert out.endswith("b.png")

    def test_watch_folder_empty_returns_empty(self, tmp_path):
        out = run("watch_folder_next", folder=str(tmp_path), wait_seconds=0.0)[0]
        assert out == ""


# -----------------------
# System
# -----------------------
class TestSystem:
    def test_system_stats_returns_dict(self, tmp_path):
        info = run("system_stats", disk_path=str(tmp_path))[1]
        assert isinstance(info, dict)
        # Disk should always be reported on a real path
        assert "disk_total_gb" in info
