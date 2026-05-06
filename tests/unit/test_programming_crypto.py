"""Tests for the Crypto category."""

import hashlib
import hmac as _hmac

import pytest

from nodes.programming import ProgrammingNode


def run(mode, **kwargs):
    return ProgrammingNode().process(mode=mode, theme="(use pack default)", **kwargs)


class TestHashes:
    def test_sha256_known(self):
        # echo -n "hello" | sha256sum
        assert run("hash_sha256", text="hello")[0] == \
            "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_sha512_known(self):
        expected = hashlib.sha512(b"hello").hexdigest()
        assert run("hash_sha512", text="hello")[0] == expected

    def test_md5_known(self):
        # echo -n "abc" | md5sum
        assert run("hash_md5", text="abc")[0] == "900150983cd24fb0d6963f7d28e17f72"

    def test_blake2b_known(self):
        expected = hashlib.blake2b(b"hello").hexdigest()
        assert run("hash_blake2b", text="hello")[0] == expected

    def test_empty_input(self):
        # Empty SHA-256
        assert run("hash_sha256", text="")[0] == \
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class TestHmac:
    def test_hmac_sign_matches_stdlib(self):
        sig = run("hmac_sign", text="message", key="secret")[0]
        expected = _hmac.new(b"secret", b"message", hashlib.sha256).hexdigest()
        assert sig == expected

    def test_hmac_verify_correct(self):
        sig = run("hmac_sign", text="hello", key="key")[0]
        assert run("hmac_verify", text="hello", key="key", expected_hex=sig)[3] is True

    def test_hmac_verify_wrong_key(self):
        sig = run("hmac_sign", text="hello", key="key1")[0]
        assert run("hmac_verify", text="hello", key="key2", expected_hex=sig)[3] is False

    def test_hmac_verify_wrong_text(self):
        sig = run("hmac_sign", text="hello", key="key")[0]
        assert run("hmac_verify", text="goodbye", key="key", expected_hex=sig)[3] is False

    def test_hmac_verify_handles_garbage_expected(self):
        # constant-time compare with a non-hex string returns False, no crash
        assert run("hmac_verify", text="x", key="k", expected_hex="not-hex")[3] is False


class TestAES:
    def test_aes_round_trip(self):
        ct = run("aes_encrypt", plaintext="hello world", key="my-passphrase")[0]
        pt = run("aes_decrypt", ciphertext_b64=ct, key="my-passphrase")[0]
        assert pt == "hello world"

    def test_aes_round_trip_unicode(self):
        ct = run("aes_encrypt", plaintext="café 🎉", key="k")[0]
        pt = run("aes_decrypt", ciphertext_b64=ct, key="k")[0]
        assert pt == "café 🎉"

    def test_aes_decrypt_wrong_key_raises(self):
        ct = run("aes_encrypt", plaintext="secret", key="key1")[0]
        with pytest.raises(RuntimeError):
            run("aes_decrypt", ciphertext_b64=ct, key="key2")

    def test_aes_decrypt_short_blob_raises(self):
        with pytest.raises(RuntimeError, match="too short"):
            run("aes_decrypt", ciphertext_b64="dGlueQ==", key="anything")

    def test_aes_two_encrypts_differ_due_to_random_nonce(self):
        a = run("aes_encrypt", plaintext="same input", key="same key")[0]
        b = run("aes_encrypt", plaintext="same input", key="same key")[0]
        assert a != b
