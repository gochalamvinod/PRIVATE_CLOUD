"""
Test suite for split_large_file and join_parts.
Splits a 5 MB random file with a 512 KB chunk size, rejoins it, and verifies SHA-256 hash identity.
Run with: python -m unittest tests/test_split_join.py
"""

import os
import hashlib
import unittest
import tempfile
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from FINAL_SINGLE_SERVER import split_large_file, join_parts


class TestSplitJoin(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_split_join_")
        self.file_size = 5 * 1024 * 1024  # 5 MB
        self.chunk_size = 512 * 1024       # 512 KB (splits into 10 parts)
        self.original_path = os.path.join(self.test_dir, "original_5mb.bin")
        self.reassembled_path = os.path.join(self.test_dir, "reassembled.bin")

        # Generate 5 MB of pseudorandom data
        self.original_data = os.urandom(self.file_size)
        with open(self.original_path, "wb") as f:
            f.write(self.original_data)

        self.original_sha256 = hashlib.sha256(self.original_data).hexdigest()

    def tearDown(self):
        # Clean up temporary test files
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(self.test_dir)

    def test_split_and_join_roundtrip(self):
        """Splits 5 MB file into chunks, rejoins with join_parts, and validates SHA-256."""
        # 1. Split
        parts = split_large_file(self.original_path, chunk_size=self.chunk_size)
        expected_part_count = (self.file_size + self.chunk_size - 1) // self.chunk_size
        self.assertEqual(len(parts), expected_part_count)

        for part in parts:
            self.assertTrue(os.path.exists(part))

        # 2. Join (pass parts in intentionally unsorted order to verify numeric sorting)
        shuffled_parts = list(reversed(parts))
        join_parts(shuffled_parts, self.reassembled_path)
        self.assertTrue(os.path.exists(self.reassembled_path))

        # 3. Hash verification
        hasher = hashlib.sha256()
        with open(self.reassembled_path, "rb") as f:
            while chunk := f.read(1024 * 1024):
                hasher.update(chunk)
        reassembled_sha256 = hasher.hexdigest()

        self.assertEqual(self.original_sha256, reassembled_sha256, "Reassembled file SHA-256 does not match original!")
        self.assertEqual(os.path.getsize(self.reassembled_path), self.file_size)


if __name__ == "__main__":
    unittest.main()
