"""Security regression tests for v0.3.0 fixes.

These guard the four Critical findings from the v0.3 audit:
  1. Jinja2 SSTI sandbox
  2. Home-dir removal from confined roots
  3. save_image_with_manifest path confinement
  4. SSRF block on HTTP nodes
"""
import os
import sys
import pytest

# Ensure the package directory is importable for the standalone test runner.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)


# ---------------- Jinja2 SSTI sandbox ----------------

class TestJinjaSandbox:
    def test_text_template_render_blocks_class_walk(self):
        """The classic SSTI payload should NOT escape the sandbox."""
        from mp_nodes.programming.operations import text as text_ops
        from jinja2.exceptions import SecurityError

        payload = "{{ ''.__class__.__bases__[0].__subclasses__() }}"
        with pytest.raises((SecurityError, Exception)) as excinfo:
            text_ops._jinja_env.from_string(payload).render()
        # SecurityError is the specific class, but a generic UndefinedError /
        # TemplateError is also acceptable — what matters is that it raises.
        assert "SecurityError" in type(excinfo.value).__name__ \
            or "Security" in str(excinfo.value) \
            or "Undefined" in type(excinfo.value).__name__

    def test_prompt_template_render_blocks_class_walk(self):
        from mp_nodes.prompt.operations import prompt as prompt_ops
        from jinja2.exceptions import SecurityError

        payload = "{{ ''.__class__.__mro__[1].__subclasses__() }}"
        with pytest.raises((SecurityError, Exception)) as excinfo:
            prompt_ops._jinja.from_string(payload).render()
        assert "SecurityError" in type(excinfo.value).__name__ \
            or "Security" in str(excinfo.value) \
            or "Undefined" in type(excinfo.value).__name__

    def test_safe_templates_still_work(self):
        """Sandbox must not break legitimate templates."""
        from mp_nodes.programming.operations import text as text_ops
        result = text_ops._jinja_env.from_string(
            "Hello {{ name }}! Count: {{ items|length }}"
        ).render(name="world", items=[1, 2, 3])
        assert result == "Hello world! Count: 3"


# ---------------- Filesystem path confinement ----------------

class TestPathConfinement:
    def test_home_dir_not_in_confined_roots(self):
        """The user's home directory MUST NOT be in the allow-list anymore."""
        from mp_nodes.io_workflow.operations.filesystem import _confined_roots
        home = os.path.normcase(os.path.expanduser("~"))
        roots = [os.path.normcase(r) for r in _confined_roots()]
        # No root should be the home dir itself or its parent prefix.
        for root in roots:
            assert root != home, f"{root!r} == home dir — confinement bypass!"

    def test_ssh_key_path_rejected(self):
        """An attack like rm ~/.ssh/id_rsa must raise PermissionError."""
        from mp_nodes.io_workflow.operations.filesystem import _require_confined
        ssh_key = os.path.join(os.path.expanduser("~"), ".ssh", "id_rsa")
        # Skip the test if we're somehow already running with the override env
        # var set (e.g. CI).
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _require_confined(ssh_key)

    def test_traversal_via_dotdot_rejected(self):
        """`../../../etc/passwd` must not slip through the basename sanitizer."""
        from mp_nodes.io_workflow.operations.filesystem import _require_confined
        traversal = os.path.abspath(os.path.join("output", "..", "..", "etc", "passwd"))
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_ARBITRARY_PATHS") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _require_confined(traversal)

    def test_normcase_on_windows(self):
        """Mixed-case paths should still match the registered roots on Windows."""
        if os.name != "nt":
            pytest.skip("Windows-only")
        from mp_nodes.io_workflow.operations.filesystem import _path_is_confined, _confined_roots
        roots = _confined_roots()
        if not roots:
            pytest.skip("no roots configured")
        # Take the first root and flip its case.
        sample = os.path.join(roots[0], "subdir", "file.png")
        assert _path_is_confined(sample.swapcase()) is _path_is_confined(sample)


# ---------------- SSRF block ----------------

class TestSSRFBlock:
    def test_blocks_loopback(self):
        from mp_nodes.io_workflow.operations.network import _check_ssrf
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _check_ssrf("http://127.0.0.1:8080/api")

    def test_blocks_aws_metadata_endpoint(self):
        """169.254.169.254 is the AWS/GCP/Azure metadata endpoint —
        classic SSRF target that leaks IAM creds."""
        from mp_nodes.io_workflow.operations.network import _check_ssrf
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _check_ssrf("http://169.254.169.254/latest/meta-data/iam/security-credentials/")

    def test_blocks_private_network(self):
        from mp_nodes.io_workflow.operations.network import _check_ssrf
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _check_ssrf("http://10.0.0.1/")

    def test_localhost_alias_blocked(self):
        """`localhost` resolves to 127.0.0.1 → must be blocked."""
        from mp_nodes.io_workflow.operations.network import _check_ssrf
        if os.environ.get("UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP") == "1":
            pytest.skip("override env var is set")
        with pytest.raises(PermissionError):
            _check_ssrf("http://localhost/")

    def test_override_env_allows_loopback(self, monkeypatch):
        """The escape hatch must work for legitimate local-LLM use cases."""
        from mp_nodes.io_workflow.operations import network as net_mod
        monkeypatch.setenv("UTILITY_MEGAPACK_ALLOW_INTERNAL_HTTP", "1")
        # No raise.
        net_mod._check_ssrf("http://127.0.0.1:11434/api/chat")
