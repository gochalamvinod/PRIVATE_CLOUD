"""
Streaming client-side encryption module using AES-256-GCM and Scrypt key derivation.
Chunked streaming: 1 MiB plaintext chunks, unique nonce per chunk (8-byte random prefix + 4-byte counter),
authenticated chunk index, salt in header. Never writes passphrase or key to disk.
"""

import os
import sys
import struct
import getpass
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"PCENC\x01"  # 6-byte magic identifier and version
SALT_LEN = 16
NONCE_PREFIX_LEN = 8
CHUNK_SIZE = 1024 * 1024  # 1 MiB plaintext per chunk


def get_passphrase(provided_passphrase=None):
    """Retrieves passphrase from argument, environment variable, or prompt."""
    if provided_passphrase:
        return provided_passphrase
    env_pass = os.environ.get("PRIVATE_CLOUD_PASSPHRASE")
    if env_pass:
        return env_pass
    return getpass.getpass("Enter encryption/decryption passphrase: ")


def derive_key(passphrase: str, salt: bytes) -> bytes:
    """Derives a 256-bit key using Scrypt."""
    if not isinstance(passphrase, bytes):
        passphrase_bytes = passphrase.encode("utf-8")
    else:
        passphrase_bytes = passphrase

    kdf = Scrypt(
        salt=salt,
        length=32,
        n=16384,
        r=8,
        p=1
    )
    return kdf.derive(passphrase_bytes)


def encrypt_file(input_path: str, output_path: str, passphrase: str = None) -> str:
    """
    Encrypts a file in 1 MiB chunks with AES-256-GCM.
    Header format: [MAGIC: 6 bytes][SALT: 16 bytes][NONCE_PREFIX: 8 bytes]
    Chunk format: [LENGTH: 4 bytes big-endian][CIPHERTEXT + 16-byte TAG]
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    secret = get_passphrase(passphrase)
    if not secret:
        raise ValueError("Passphrase cannot be empty.")

    salt = os.urandom(SALT_LEN)
    nonce_prefix = os.urandom(NONCE_PREFIX_LEN)
    key = derive_key(secret, salt)
    aesgcm = AESGCM(key)

    with open(input_path, "rb") as infile, open(output_path, "wb") as outfile:
        # Write header
        outfile.write(MAGIC)
        outfile.write(salt)
        outfile.write(nonce_prefix)

        chunk_index = 0
        while True:
            plaintext = infile.read(CHUNK_SIZE)
            if not plaintext:
                break

            # 12-byte nonce = 8-byte prefix + 4-byte counter
            nonce = nonce_prefix + struct.pack(">I", chunk_index)
            # Associated data authenticates the chunk sequence
            aad = struct.pack(">I", chunk_index)

            ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
            # Write 4-byte chunk length followed by ciphertext
            outfile.write(struct.pack(">I", len(ciphertext)))
            outfile.write(ciphertext)
            chunk_index += 1

    return output_path


def decrypt_file(input_path: str, output_path: str, passphrase: str = None) -> str:
    """
    Decrypts an AES-256-GCM encrypted file in streaming chunks.
    Validates authentication tag and chunk indices.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Encrypted file not found: {input_path}")

    secret = get_passphrase(passphrase)
    if not secret:
        raise ValueError("Passphrase cannot be empty.")

    with open(input_path, "rb") as infile:
        magic = infile.read(len(MAGIC))
        if magic != MAGIC:
            raise ValueError("Invalid file format or header magic mismatch.")

        salt = infile.read(SALT_LEN)
        nonce_prefix = infile.read(NONCE_PREFIX_LEN)
        if len(salt) != SALT_LEN or len(nonce_prefix) != NONCE_PREFIX_LEN:
            raise ValueError("Corrupted file header: unexpected end of file.")

        key = derive_key(secret, salt)
        aesgcm = AESGCM(key)

        with open(output_path, "wb") as outfile:
            chunk_index = 0
            while True:
                length_bytes = infile.read(4)
                if not length_bytes:
                    break  # Clean EOF

                if len(length_bytes) < 4:
                    raise ValueError("Truncated encrypted chunk header.")

                chunk_len = struct.unpack(">I", length_bytes)[0]
                ciphertext = infile.read(chunk_len)
                if len(ciphertext) != chunk_len:
                    raise ValueError("Truncated ciphertext: unexpected end of file.")

                nonce = nonce_prefix + struct.pack(">I", chunk_index)
                aad = struct.pack(">I", chunk_index)

                try:
                    plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
                except Exception as err:
                    raise ValueError(
                        f"Decryption failed at chunk {chunk_index}: wrong passphrase or tampered ciphertext."
                    ) from err

                outfile.write(plaintext)
                chunk_index += 1

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m crypto.encrypt (--encrypt|--decrypt) <input_file> [-o <output_file>]")
        sys.exit(1)

    mode = sys.argv[1]
    in_file = sys.argv[2]
    out_file = None
    if "-o" in sys.argv:
        out_idx = sys.argv.index("-o")
        if out_idx + 1 < len(sys.argv):
            out_file = sys.argv[out_idx + 1]

    if mode == "--encrypt":
        out_file = out_file or f"{in_file}.enc"
        encrypt_file(in_file, out_file)
        print(f"File encrypted successfully: {out_file}")
    elif mode == "--decrypt":
        out_file = out_file or (in_file[:-4] if in_file.endswith(".enc") else f"{in_file}.dec")
        decrypt_file(in_file, out_file)
        print(f"File decrypted successfully: {out_file}")
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)
