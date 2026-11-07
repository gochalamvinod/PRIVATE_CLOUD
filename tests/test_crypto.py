"""
Test suite for opt-in client-side AES-256-GCM encryption.
Verifies:
  1. Plaintext -> Encrypt -> Decrypt -> identical Plaintext round-trip
  2. Wrong passphrase raises decryption error
  3. Tampered ciphertext / tag detection raises decryption error
Run with: python -m unittest tests/test_crypto.py
"""

import os
import unittest
import tempfile
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crypto.encrypt import encrypt_file, decrypt_file


class TestCrypto(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_crypto_")
        self.passphrase = "SecretPassphrase123!#$"
        self.plain_path = os.path.join(self.test_dir, "sample.txt")
        self.enc_path = os.path.join(self.test_dir, "sample.txt.enc")
        self.dec_path = os.path.join(self.test_dir, "sample_decrypted.txt")

        # Create multi-chunk test file (2.5 MiB to test multi-chunk streaming)
        self.plain_data = os.urandom(int(2.5 * 1024 * 1024))
        with open(self.plain_path, "wb") as f:
            f.write(self.plain_data)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(self.test_dir)

    def test_roundtrip_encryption_decryption(self):
        """Verifies encrypt -> decrypt reproduces exact plaintext."""
        encrypt_file(self.plain_path, self.enc_path, passphrase=self.passphrase)
        self.assertTrue(os.path.exists(self.enc_path))
        self.assertNotEqual(os.path.getsize(self.enc_path), 0)

        decrypt_file(self.enc_path, self.dec_path, passphrase=self.passphrase)
        self.assertTrue(os.path.exists(self.dec_path))

        with open(self.dec_path, "rb") as f:
            decrypted_data = f.read()

        self.assertEqual(self.plain_data, decrypted_data)

    def test_wrong_passphrase_failure(self):
        """Verifies decryption fails when an incorrect passphrase is provided."""
        encrypt_file(self.plain_path, self.enc_path, passphrase=self.passphrase)
        wrong_pass = "CompletelyWrongPassword999"

        with self.assertRaises(ValueError):
            decrypt_file(self.enc_path, self.dec_path, passphrase=wrong_pass)

    def test_tamper_detection(self):
        """Verifies AES-256-GCM detects ciphertext tampering and fails integrity verification."""
        encrypt_file(self.plain_path, self.enc_path, passphrase=self.passphrase)

        # Tamper with a byte inside the encrypted file (after header)
        with open(self.enc_path, "r+b") as f:
            f.seek(50)  # Seek past the 30-byte header into first chunk
            byte = f.read(1)
            tampered_byte = bytes([byte[0] ^ 0xFF])
            f.seek(50)
            f.write(tampered_byte)

        with self.assertRaises(ValueError):
            decrypt_file(self.enc_path, self.dec_path, passphrase=self.passphrase)


if __name__ == "__main__":
    unittest.main()
